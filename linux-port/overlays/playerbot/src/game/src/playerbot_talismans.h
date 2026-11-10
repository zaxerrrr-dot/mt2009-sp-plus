#ifndef __INC_METIN2_PLAYERBOT_TALISMANS_H__
#define __INC_METIN2_PLAYERBOT_TALISMANS_H__

// MT2009_PLUS_BOT_TALISMANS_V1: the bots and the element talismans (MT2009_PLUS_ELEMENTS_V1,
// Autor: Digi Rasta, server-patches/zywioly, playerbot_elements.cpp). "Naucz boty talizmanow:
// ulepszaja je u Kowala, zakladaja jeden w pole talizmanu i wybieraja ten, ktory na danej mapie
// daje najwiecej obrazen ... i dazy do ulepszenia talizmanu pasujacego do mapy, az go
// przescignie" (the owner, 7 October). Until now a bot wore the talisman with the most element
// power it owned (ScorePlayerBotApply, sixty a point) and never refined one.
//
// Which talisman is worn: the one whose expected bonus on the bot's hunting map is the largest,
// by the engine's own formula (ElementsAttackBonus): a talisman of power P gives min(P/10, 20)%
// against everything, and against a monster of its element min(18 + 0.5*(P-1), 80)% more. The
// map's monsters are counted by their race flag bits 11-16 (the element of a monster - set by
// tools/zywioly/gen_zywioly_moby.py; Metins and every other monster have none), so the expected
// bonus is general + share(element) * element bonus. The map is the one the bot stands on, or -
// in a village - the last field map it hunted on (a town has no monsters to count).
//
// Note on the owner's example: by that formula Fire +100 is +10% everywhere, and Lightning +2 is
// +18.5% against a lightning monster. In Grota Wygnancow, where every monster but the Metins is
// lightning, Lightning +2 wins as soon as more than ~54% of what the bot fights is lightning,
// and Lightning +1 (+18%) already beats Fire +100 there. The rule computes; it does not assume.
//
// What is refined (the project): the worn talisman, the best by the rule above - unless the
// hunting map has a dominant element (PLAYERBOT_TALISMAN_DOMINANT_PERCENT of its monsters) and
// the best talisman is not of that element: then the talisman of the map's element, until its
// bonus there overtakes the other one and the equipment pass puts it on. One step at the
// Blacksmith (refine_proto 20001-21200 through DoRefine, the engine's path): 10 Kwiat Zywiolu
// (95500, Mistrz's shop 9550 - bought there, playerbot_workshop.h), 1 Ornament (30031), a second
// Talisman +0 of the element and the fee; 100%. Never past what the bot's level can wear.
//
// Who refines: PLAYERBOT_TALISMAN_WORKER_PERCENT of the bots from PLAYERBOT_TALISMAN_MIN_LEVEL
// (by player id). The rest wear what they have. Materials: the Ornament and the spare +0 come
// off the counters (playerbot_market.h, playerbot_offline_market.h - the talisman at the owner's
// price, 700 000 at +0 and 650 000 more a grade, GetPlayerBotTalismanPrice), the flowers from Mistrz. The owner, 7 October:
// "mozesz dac niektorym botom przedmioty, zeby ulatwic robienie/ulepszanie ... zeby szybciej
// to uruchomic" - a share of the
// workers (PLAYERBOT_TALISMAN_SEED_PERCENT) is given a Talisman +0 to wear and the materials of
// PLAYERBOT_TALISMAN_SEED_STEPS steps - the spare +0 and the Ornament handed over at the anvil one
// step at a time (a quest flag counts them), so the bag does not carry ten talismans, and the
// flowers of those steps at Mistrz; the fee is the bot's own. Event flag m2_bot_craft_seed_off stops
// the gifts, m2_bot_workshop_off the whole errand.

#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_ELEMENTS_V1)

namespace
{
	const int PLAYERBOT_TALISMAN_ELEMENTS = 6;
	const int PLAYERBOT_TALISMAN_MAX_PLUS = 200;
	const int PLAYERBOT_TALISMAN_MIN_LEVEL = 30;
	const int PLAYERBOT_TALISMAN_WORKER_PERCENT = 60;
	const int PLAYERBOT_TALISMAN_SEED_PERCENT = 35;
	const int PLAYERBOT_TALISMAN_SEED_STEPS = 10;
	const char* const PLAYERBOT_TALISMAN_SEED_FLAG = "playerbot.talisman_seed";
	// A map's element is its own when this share of its monsters has it.
	const int PLAYERBOT_TALISMAN_DOMINANT_PERCENT = 25;
	const DWORD PLAYERBOT_TALISMAN_FLOWER_VNUM = 95500;
	const DWORD PLAYERBOT_TALISMAN_ORNAMENT_VNUM = 30031;
	const int PLAYERBOT_TALISMAN_FLOWERS_A_STEP = 10;
	const DWORD PLAYERBOT_TALISMAN_FLOWER_SHOP = 9550;
	const long long PLAYERBOT_TALISMAN_FLOWER_PRICE = 100000LL;
	// What a worker pays at most for a spare +0: the owner's price of any talisman
	// (PLAYERBOT_TALISMAN_PRICE, 700 000 - playerbot_energy_shards.h) and this share over it.
	const int PLAYERBOT_TALISMAN_BUY_OVER_PERCENT = 130;
	// Spares and ornaments a worker holds for its next steps; the rest are goods.
	const int PLAYERBOT_TALISMAN_SPARE_KEEP = 3;
	const int PLAYERBOT_TALISMAN_SPARE_WANT = 2;
	// Ornaments: a line of up to this many is bought, and this many are kept.
	const int PLAYERBOT_TALISMAN_ORNAMENT_KEEP = 10;
	// Steps at one visit, and the share of the spare purse a visit may spend.
	const int PLAYERBOT_TALISMAN_VISIT_STEPS = 5;
	const int PLAYERBOT_TALISMAN_SPEND_PERCENT = 60;
	const DWORD PLAYERBOT_TALISMAN_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_TALISMAN_PLAN_MS = 20 * 1000;

	struct TPlayerBotTalismanElement
	{
		DWORD raceFlag;
		DWORD baseVnum;
		const char* name;
	};

	// In the order of playerbot_elements.cpp's ELEMENTS (bit 14 is wind in the client).
	const TPlayerBotTalismanElement PLAYERBOT_TALISMAN_ELEMENT[PLAYERBOT_TALISMAN_ELEMENTS] = {
		{ RACE_FLAG_ATT_ELEC,	94250, "Blyskawicy" },
		{ RACE_FLAG_ATT_FIRE,	94000, "Ognia" },
		{ RACE_FLAG_ATT_ICE,	94500, "Lodu" },
		{ RACE_FLAG_ATT_TEMPLE,	94750, "Wiatru" },
		{ RACE_FLAG_ATT_EARTH,	95000, "Ziemi" },
		{ RACE_FLAG_ATT_DARK,	95250, "Mroku" },
	};

	int GetPlayerBotTalismanElementOf(DWORD vnum)
	{
		for (int e = 0; e < PLAYERBOT_TALISMAN_ELEMENTS; ++e)
			if (vnum >= PLAYERBOT_TALISMAN_ELEMENT[e].baseVnum &&
					vnum <= PLAYERBOT_TALISMAN_ELEMENT[e].baseVnum + PLAYERBOT_TALISMAN_MAX_PLUS)
				return e;
		return -1;
	}

	bool IsPlayerBotTalismanVnum(DWORD vnum)
	{
		return GetPlayerBotTalismanElementOf(vnum) >= 0;
	}

	bool IsPlayerBotTalismanItem(LPITEM item)
	{
		return item && item->GetType() == ITEM_ARMOR && IsPlayerBotTalismanVnum(item->GetVnum());
	}

	// The plus from the vnum: the name's "+N" would do too, but GetRefineLevel is a BYTE
	// in places and a talisman goes to +200.
	int GetPlayerBotTalismanPlus(LPITEM item)
	{
		const int e = item ? GetPlayerBotTalismanElementOf(item->GetVnum()) : -1;
		return e < 0 ? 0 : (int)(item->GetVnum() - PLAYERBOT_TALISMAN_ELEMENT[e].baseVnum);
	}

	bool IsPlayerBotTalismanWorker(LPCHARACTER ch)
	{
		return ch && (int)ch->GetLevel() >= PLAYERBOT_TALISMAN_MIN_LEVEL &&
				PlayerBotNavHash(ch->GetPlayerID() ^ 0x54414c49U) % 100U < (DWORD)PLAYERBOT_TALISMAN_WORKER_PERCENT;
	}

	// ---- the map's elements -------------------------------------------------------------

	struct TPlayerBotElementCensus
	{
		DWORD at;
		unsigned total;
		unsigned count[PLAYERBOT_TALISMAN_ELEMENTS];
	};
	std::map<long, TPlayerBotElementCensus> s_mapPlayerBotElementCensus;

	struct FPlayerBotElementCount
	{
		TPlayerBotElementCensus& c;
		explicit FPlayerBotElementCount(TPlayerBotElementCensus& census) : c(census) {}
		void operator()(LPENTITY entity)
		{
			if (!entity || !entity->IsType(ENTITY_CHARACTER))
				return;
			LPCHARACTER mob = static_cast<LPCHARACTER>(entity);
			if (mob->IsPC() || mob->IsDead() || !(mob->IsMonster() || mob->IsStone()))
				return;
			++c.total;
			for (int e = 0; e < PLAYERBOT_TALISMAN_ELEMENTS; ++e)
				if (mob->IsRaceFlag(PLAYERBOT_TALISMAN_ELEMENT[e].raceFlag))
				{
					++c.count[e];
					break;
				}
		}
	};

	// The share of the map's monsters (and Metins, which have no element) of each element, in
	// percent; all zero for a map this core does not host or that has nobody to count. Counted
	// over the whole map at most once in PLAYERBOT_TALISMAN_CENSUS_MS.
	void GetPlayerBotMapElementShares(long mapIndex, int share[PLAYERBOT_TALISMAN_ELEMENTS])
	{
		for (int e = 0; e < PLAYERBOT_TALISMAN_ELEMENTS; ++e)
			share[e] = 0;
		if (mapIndex <= 0)
			return;
		const DWORD now = get_dword_time();
		std::map<long, TPlayerBotElementCensus>::iterator it = s_mapPlayerBotElementCensus.find(mapIndex);
		if (it == s_mapPlayerBotElementCensus.end() || now - it->second.at >= PLAYERBOT_TALISMAN_CENSUS_MS)
		{
			LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(mapIndex);
			if (!pMap)
			{
				if (it == s_mapPlayerBotElementCensus.end())
					return;	// never counted here: nothing known
			}
			else
			{
				TPlayerBotElementCensus fresh;
				memset(&fresh, 0, sizeof(fresh));
				FPlayerBotElementCount counter(fresh);
				pMap->for_each(counter);
				fresh.at = now;
				s_mapPlayerBotElementCensus[mapIndex] = fresh;
				it = s_mapPlayerBotElementCensus.find(mapIndex);
			}
		}
		const TPlayerBotElementCensus& c = it->second;
		if (c.total < 5)
			return;
		for (int e = 0; e < PLAYERBOT_TALISMAN_ELEMENTS; ++e)
			share[e] = (int)(c.count[e] * 100U / c.total);
	}

	// The map a bot's talisman is chosen for: where it stands, or in a village the last field
	// map it hunted on (playerbot_workshop.h keeps it).
	long GetPlayerBotHuntingMap(LPCHARACTER ch);

	// MT2009_PLUS_BOT_YOHARA_ELEMENTS_V1: the shares a bot's talisman is chosen by - its Sung Ma map's from the table
	// (playerbot_yohara_elements.h: fixed, so a map of two near equal elements no longer swaps the talisman with what
	// is alive, and a trade trip home keeps the talisman of the map it goes back to), else the hunting map's count.
	// Returns the map.
	long GetPlayerBotTalismanMapShares(LPCHARACTER ch, int share[PLAYERBOT_TALISMAN_ELEMENTS])
	{
		const long yohara = GetPlayerBotYoharaElementMap(ch);
		if (yohara != 0 && GetPlayerBotYoharaMapShares(yohara, share))
			return yohara;
		const long map = GetPlayerBotHuntingMap(ch);
		GetPlayerBotMapElementShares(map, share);
		return map;
	}

	// ---- the formula ----------------------------------------------------------------------

	// ElementsAttackBonus's numbers for one talisman of power `plus`, in hundredths of a
	// percent: the general bonus, and the bonus against a monster of the element.
	int GetPlayerBotTalismanGeneralBonus(int plus)
	{
		return plus <= 0 ? 0 : std::min(plus / 10, 20) * 100;
	}

	int GetPlayerBotTalismanElementBonus(int plus)
	{
		return plus <= 0 ? 0 : std::min(36 + (plus - 1), 160) * 50;
	}

	// The expected damage bonus of element `e` at `plus` on a map with these shares, in
	// hundredths of a percent.
	int GetPlayerBotTalismanGain(int e, int plus, const int share[PLAYERBOT_TALISMAN_ELEMENTS])
	{
		if (e < 0 || e >= PLAYERBOT_TALISMAN_ELEMENTS)
			return 0;
		return GetPlayerBotTalismanGeneralBonus(plus) + GetPlayerBotTalismanElementBonus(plus) * share[e] / 100;
	}

	// The equipment score of a talisman for this bot now (GetPlayerBotEquipmentScore asks it for
	// every talisman, so the equipment pass and the wear pass below agree): the expected bonus
	// on its hunting map first, the plus as the tie-break.
	long long GetPlayerBotTalismanScore(LPCHARACTER ch, LPITEM item)
	{
		const int e = item ? GetPlayerBotTalismanElementOf(item->GetVnum()) : -1;
		if (!ch || e < 0)
			return 0;
		int share[PLAYERBOT_TALISMAN_ELEMENTS];
		GetPlayerBotTalismanMapShares(ch, share);	// MT2009_PLUS_BOT_YOHARA_ELEMENTS_V1
		const int plus = GetPlayerBotTalismanPlus(item);
		return 1 + (long long)GetPlayerBotTalismanGain(e, plus, share) * 1000 + plus;
	}

	// MT2009_PLUS_BOT_YOHARA_ELEMENTS_V1: the pendant slot's one rule (D15), GetPlayerBotPendantScore, is in
	// playerbot_yohara_elements_late.h (it needs the Will of the Sung Ma maps); a pendant it chooses from:
	bool IsPlayerBotPendantChoice(LPITEM item)
	{
		return item && (IsPlayerBotTalismanItem(item) ||
				(item->GetType() == ITEM_ARMOR && GetPlayerBotWillTalismanKind(item->GetVnum()) >= 0));
	}

	// ---- what the bot owns ----------------------------------------------------------------

	bool IsPlayerBotTalismanWearable(LPCHARACTER ch, LPITEM item)
	{
		return ch && IsPlayerBotTalismanItem(item) && item->GetLevelLimit() <= (int)ch->GetLevel() &&
				item->CanUsedBy(ch);
	}

	// The best talisman the bot could wear now, worn or in the bag.
	LPITEM FindPlayerBotBestTalisman(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return NULL;
		LPITEM best = NULL;
		long long bestScore = 0;
		LPITEM worn = ch->GetWear(WEAR_PENDANT);
		if (IsPlayerBotTalismanWearable(ch, worn))
		{
			best = worn;
			bestScore = GetPlayerBotTalismanScore(ch, worn);
		}
#ifdef MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
		// MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1: the element set's worn talisman stays, its talisman in the bag waits
		if (worn && IsPlayerBotSecondSetWornLocked(ch, worn))
			return worn;
#endif
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || !IsPlayerBotTalismanWearable(ch, item))
				continue;
#ifdef MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
			if (IsPlayerBotSecondSetStored(ch, item))
				continue;
#endif
			const long long score = GetPlayerBotTalismanScore(ch, item);
			if (!best || score > bestScore)
			{
				best = item;
				bestScore = score;
			}
		}
		return best;
	}

	// MT2009_PLUS_BOT_YOHARA_ELEMENTS_V1: the pendant to wear - an element talisman or a Talizman Woli, worn or in the
	// bag - by the equipment score itself (GetPlayerBotPendantScore inside), so the light pass and the equipment pass
	// never disagree; the worn one stays on a tie.
	LPITEM FindPlayerBotBestPendant(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return NULL;
		LPITEM best = NULL;
		long long bestScore = 0;
		LPITEM worn = ch->GetWear(WEAR_PENDANT);
		if (IsPlayerBotPendantChoice(worn) && worn->GetLevelLimit() <= (int)ch->GetLevel() && worn->CanUsedBy(ch))
		{
			best = worn;
			bestScore = GetPlayerBotEquipmentScore(worn, ch);
		}
#ifdef MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
		// MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1: the element set's worn pendant stays, its pendant in the bag waits
		if (worn && IsPlayerBotSecondSetWornLocked(ch, worn))
			return worn;
#endif
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || !IsPlayerBotPendantChoice(item) ||
					item->GetLevelLimit() > (int)ch->GetLevel() || !item->CanUsedBy(ch))
				continue;
#ifdef MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
			if (IsPlayerBotSecondSetStored(ch, item))
				continue;
#endif
			const long long score = GetPlayerBotEquipmentScore(item, ch);
			if (!best || score > bestScore)
			{
				best = item;
				bestScore = score;
			}
		}
		return best;
	}

	// The highest talisman of an element the bot owns (worn or in the bag).
	LPITEM FindPlayerBotTalismanOfElement(LPCHARACTER ch, int e)
	{
		if (!ch || e < 0)
			return NULL;
		LPITEM best = NULL;
		LPITEM worn = ch->GetWear(WEAR_PENDANT);
		if (IsPlayerBotTalismanItem(worn) && GetPlayerBotTalismanElementOf(worn->GetVnum()) == e)
			best = worn;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || !IsPlayerBotTalismanItem(item) ||
					GetPlayerBotTalismanElementOf(item->GetVnum()) != e)
				continue;
			if (!best || GetPlayerBotTalismanPlus(item) > GetPlayerBotTalismanPlus(best))
				best = item;
		}
		return best;
	}

	// The spare Talismans +0 of an element in the bag, leaving the project out.
	int CountPlayerBotTalismanSpares(LPCHARACTER ch, int e, LPITEM project)
	{
		if (!ch || e < 0)
			return 0;
		int spares = 0;
		const DWORD base = PLAYERBOT_TALISMAN_ELEMENT[e].baseVnum;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && item != project && item->GetVnum() == base
#ifdef MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
					&& !IsPlayerBotSecondSetStored(ch, item)	// MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
#endif
					)
				spares += std::max<int>(1, item->GetCount());
		}
		return spares;
	}

	// The seeded steps still owed (none while m2_bot_craft_seed_off is set).
	int GetPlayerBotTalismanSeedLeft(LPCHARACTER ch)
	{
		if (!ch || ArePlayerBotCraftSeedsOff())
			return 0;
		return std::max(0, ch->GetQuestFlag(PLAYERBOT_TALISMAN_SEED_FLAG) - 1);
	}

	// ---- the plan -------------------------------------------------------------------------

	struct TPlayerBotTalismanPlan
	{
		DWORD at;
		int element;		// the project's element, -1 for none
		DWORD projectId;	// 0 while the bot owns none of that element
		int plus;
		int dominant;		// the hunting map's element, -1 for none
		int spares;
		int ornaments;
		int flowers;
		bool stepWearable;	// the next plus is within the bot's level
	};
	std::map<DWORD, TPlayerBotTalismanPlan> s_mapPlayerBotTalismanPlan;

	struct TPlayerBotTalismanStats
	{
		unsigned steps;
		unsigned wears;
		unsigned seeded;
		unsigned seedGifts;
		unsigned flowersBought;
		unsigned bought;
		unsigned long long boughtYang;
		unsigned long long fees;
	};
	TPlayerBotTalismanStats s_kPlayerBotTalismanStats = { 0, 0, 0, 0, 0, 0, 0, 0 };

	const TPlayerBotTalismanPlan& GetPlayerBotTalismanPlan(LPCHARACTER ch, bool fresh = false)
	{
		static TPlayerBotTalismanPlan s_none = { 0, -1, 0, 0, -1, 0, 0, 0, false };
		if (!ch)
			return s_none;
		TPlayerBotTalismanPlan& p = s_mapPlayerBotTalismanPlan[ch->GetPlayerID()];
		const DWORD now = get_dword_time();
		if (!fresh && p.at != 0 && now - p.at < PLAYERBOT_TALISMAN_PLAN_MS)
			return p;
		p.at = now;
		p.element = -1;
		p.projectId = 0;
		p.plus = 0;
		p.dominant = -1;
		p.spares = p.ornaments = p.flowers = 0;
		p.stepWearable = false;
		if (!IsPlayerBotTalismanWorker(ch) || !ch->IsItemLoaded())
			return p;

		int share[PLAYERBOT_TALISMAN_ELEMENTS];
		GetPlayerBotTalismanMapShares(ch, share);	// MT2009_PLUS_BOT_YOHARA_ELEMENTS_V1
		int dominantShare = 0;
		for (int e = 0; e < PLAYERBOT_TALISMAN_ELEMENTS; ++e)
			if (share[e] >= PLAYERBOT_TALISMAN_DOMINANT_PERCENT && share[e] > dominantShare)
			{
				p.dominant = e;
				dominantShare = share[e];
			}

		LPITEM best = FindPlayerBotBestTalisman(ch);
		const int bestElement = best ? GetPlayerBotTalismanElementOf(best->GetVnum()) : -1;
		LPITEM project = best;
		p.element = bestElement;
		// The map's own element, until it overtakes what is worn.
		if (p.dominant >= 0 && p.dominant != bestElement)
		{
			p.element = p.dominant;
			project = FindPlayerBotTalismanOfElement(ch, p.dominant);
		}
		// Nothing at all yet: the seeded element's, else one by player id - the general
		// bonus is the same for every element.
		if (p.element < 0)
			p.element = (int)(PlayerBotNavHash(ch->GetPlayerID() ^ 0x454c454dU) % PLAYERBOT_TALISMAN_ELEMENTS);
		if (project)
		{
			p.projectId = project->GetID();
			p.plus = GetPlayerBotTalismanPlus(project);
			p.stepWearable = p.plus < PLAYERBOT_TALISMAN_MAX_PLUS && project->GetRefinedVnum() != 0 &&
					IsPlayerBotWearableAtLevel(ch, project->GetRefinedVnum());
		}
		p.spares = CountPlayerBotTalismanSpares(ch, p.element, project);
		p.ornaments = (int)ch->CountSpecifyItem(PLAYERBOT_TALISMAN_ORNAMENT_VNUM);
		p.flowers = (int)ch->CountSpecifyItem(PLAYERBOT_TALISMAN_FLOWER_VNUM);
		return p;
	}

	void ForgetPlayerBotTalismanPlan(LPCHARACTER ch)
	{
		if (ch)
			s_mapPlayerBotTalismanPlan.erase(ch->GetPlayerID());
	}

	LPITEM GetPlayerBotTalismanProject(LPCHARACTER ch)
	{
		const TPlayerBotTalismanPlan& p = GetPlayerBotTalismanPlan(ch);
		if (p.projectId == 0)
			return NULL;
		LPITEM item = ITEM_MANAGER::instance().Find(p.projectId);
		return item && item->GetOwner() == ch && IsPlayerBotTalismanItem(item) ? item : NULL;
	}

	// The yang a bot can spend on its talisman: what it holds over its reserve and the
	// shopping floor.
	long long GetPlayerBotTalismanSpare(LPCHARACTER ch)
	{
		return ch ? (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR : 0;
	}

	long long GetPlayerBotTalismanStepFee(LPCHARACTER ch, LPITEM project)
	{
		const TRefineTable* recipe = project ? CRefineManager::instance().GetRefineRecipe(project->GetRefineSet()) : NULL;
		return recipe ? (long long)ch->ComputeRefineFee(recipe->cost) : -1;
	}

	// The price of a flower at Mistrz: the shop's own line, else the item's.
	long long GetPlayerBotTalismanFlowerPrice()
	{
		if (LPSHOP shop = CShopManager::instance().Get(PLAYERBOT_TALISMAN_FLOWER_SHOP))
		{
			const std::vector<CShop::SHOP_ITEM>& offers = shop->GetItemVector();
			for (size_t i = 0; i < offers.size(); ++i)
				if (offers[i].vnum == PLAYERBOT_TALISMAN_FLOWER_VNUM && offers[i].price > 0)
					return (long long)offers[i].price;
		}
		return PLAYERBOT_TALISMAN_FLOWER_PRICE;
	}

	// Can the next step be paid: the fee and the flowers still to buy, out of
	// PLAYERBOT_TALISMAN_SPEND_PERCENT of the spare purse.
	bool CanPlayerBotPayTalismanStep(LPCHARACTER ch, LPITEM project, int flowersHeld)
	{
		const long long fee = GetPlayerBotTalismanStepFee(ch, project);
		if (fee < 0)
			return false;
		// A seeded step's flowers are a gift (BuyPlayerBotTalismanFlowers).
		const int missing = GetPlayerBotTalismanSeedLeft(ch) > 0 ? 0 : std::max(0, PLAYERBOT_TALISMAN_FLOWERS_A_STEP - flowersHeld);
		const long long cost = fee + missing * GetPlayerBotTalismanFlowerPrice();
		return cost <= GetPlayerBotTalismanSpare(ch) * PLAYERBOT_TALISMAN_SPEND_PERCENT / 100;
	}

	// MT2009_PLUS_BOT_TALISMAN_CHEAP_V1 (playerbot_small_fixes.h): the cheap step - a worker whose body armour stands at
	// PLAYERBOT_TALISMAN_CHEAP_ARMOUR_PLUS or more (the gear first), its project under PLAYERBOT_TALISMAN_CHEAP_MAX_PLUS:
	// the Blacksmith hands over the step's spare Talisman +0 and Ornament its bag lacks, for their yang. The flowers, the
	// fee and the roll stay the step's own.
	struct TPlayerBotTalismanCheapStats
	{
		unsigned steps, spares, ornaments;
		unsigned long long yang;
	};
	TPlayerBotTalismanCheapStats s_kPlayerBotTalismanCheapStats = { 0, 0, 0, 0 };

	bool IsPlayerBotTalismanCheapStep(LPCHARACTER ch, const TPlayerBotTalismanPlan& p)
	{
		if (!ch || !IsPlayerBotSmallFixOn(SMALLFIX_TALISMAN) || p.projectId == 0 || !p.stepWearable || p.element < 0)
			return false;
		const TPlayerBotSmallFixCfg& c = GetPlayerBotSmallFixCfg();
		if (p.plus >= c.talismanMaxPlus)
			return false;
		LPITEM body = ch->GetWear(WEAR_BODY);
		return body && (int)body->GetRefineLevel() >= c.talismanArmourPlus;
	}

	// The yang the cheap step adds for what the bag lacks (0 when nothing is lacking or the step is not cheap).
	long long GetPlayerBotTalismanCheapYang(LPCHARACTER ch, const TPlayerBotTalismanPlan& p)
	{
		if (!IsPlayerBotTalismanCheapStep(ch, p))
			return 0;
		const TPlayerBotSmallFixCfg& c = GetPlayerBotSmallFixCfg();
		return (p.spares < 1 ? (long long)c.talismanSpareYang : 0LL) + (p.ornaments < 1 ? (long long)c.talismanOrnamentYang : 0LL);
	}

	// A step to go to the anvil for: the project, a wearable next plus, the fee and flowers
	// paid for, and the spare +0 and the ornament in the bag - or still owed by the seed.
	bool HasPlayerBotTalismanWork(LPCHARACTER ch)
	{
		const TPlayerBotTalismanPlan& p = GetPlayerBotTalismanPlan(ch);
		if (p.projectId == 0 || !p.stepWearable)
			return false;
		LPITEM project = GetPlayerBotTalismanProject(ch);
		if (!project || !CanPlayerBotPayTalismanStep(ch, project, p.flowers))
			return false;
		if (GetPlayerBotTalismanSeedLeft(ch) > 0)
			return true;
		if (p.spares >= 1 && p.ornaments >= 1)
			return true;
		// MT2009_PLUS_BOT_TALISMAN_CHEAP_V1: or the cheap step, its goods' yang within the step's share of the purse too.
		if (!IsPlayerBotTalismanCheapStep(ch, p))
			return false;
		const long long fee = std::max<long long>(0, GetPlayerBotTalismanStepFee(ch, project));
		const int flowersMissing = std::max(0, PLAYERBOT_TALISMAN_FLOWERS_A_STEP - p.flowers);
		return fee + flowersMissing * GetPlayerBotTalismanFlowerPrice() + GetPlayerBotTalismanCheapYang(ch, p) <=
				GetPlayerBotTalismanSpare(ch) * PLAYERBOT_TALISMAN_SPEND_PERCENT / 100;
	}

	// ---- the Yohara spare (MT2009_PLUS_BOT_YOHARA_ELEMENTS_V1, D14) ---------------------------

	// The map the spare is for: the next Sung Ma map up switched on for the bots, else (the top one) the map itself.
	long GetPlayerBotYoharaSpareMap(long map)
	{
		const int slot = GetPlayerBotYoharaElementSlot(map);
		if (slot < 0)
			return 0;
		for (int i = slot + 1; i < PLAYERBOT_YOHARA_ELEMENT_MAP_COUNT; ++i)
			if (IsPlayerBotSungmaMapOn(PLAYERBOT_YOHARA_ELEMENT_MAPS[i].lMap))
				return PLAYERBOT_YOHARA_ELEMENT_MAPS[i].lMap;
		return PLAYERBOT_YOHARA_ELEMENT_MAPS[slot].lMap;
	}

	int GetPlayerBotTalismanItemGain(LPITEM item, const int share[PLAYERBOT_TALISMAN_ELEMENTS])
	{
		return item ? GetPlayerBotTalismanGain(GetPlayerBotTalismanElementOf(item->GetVnum()), GetPlayerBotTalismanPlus(item), share) : 0;
	}

	// The one spare talisman of a bot on Yohara: of those it owns but the best for its map, the best for the spare's
	// map (a real bonus there); NULL off Yohara.
	LPITEM FindPlayerBotYoharaSpareTalisman(LPCHARACTER ch)
	{
		int share[PLAYERBOT_TALISMAN_ELEMENTS];
		if (!ch || !ch->IsItemLoaded() || !GetPlayerBotYoharaMapShares(GetPlayerBotYoharaSpareMap(GetPlayerBotYoharaElementMap(ch)), share))
			return NULL;
		LPITEM main = FindPlayerBotBestTalisman(ch);
		LPITEM best = NULL;
		int bestGain = 0;
		LPITEM worn = ch->GetWear(WEAR_PENDANT);
		if (worn && worn != main && IsPlayerBotTalismanItem(worn) && GetPlayerBotTalismanItemGain(worn, share) > bestGain)
		{
			best = worn;
			bestGain = GetPlayerBotTalismanItemGain(worn, share);
		}
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item == main || item->GetCell() != cell || !IsPlayerBotTalismanItem(item))
				continue;
			const int gain = GetPlayerBotTalismanItemGain(item, share);
			if (gain > bestGain)
			{
				best = item;
				bestGain = gain;
			}
		}
		return best;
	}

	// A talisman on a stand for a bot on Yohara: one it can wear, with a plus, that betters the best it owns for its
	// map, or - of another element than that one - its spare for the next map. The price: the talisman's rules below.
	bool WantsPlayerBotYoharaTalismanOffer(LPCHARACTER ch, LPITEM offer)
	{
		const int e = offer ? GetPlayerBotTalismanElementOf(offer->GetVnum()) : -1;
		if (!ch || e < 0 || GetPlayerBotTalismanPlus(offer) <= 0 || !IsPlayerBotTalismanWearable(ch, offer))
			return false;
		const long map = GetPlayerBotYoharaElementMap(ch);
		int share[PLAYERBOT_TALISMAN_ELEMENTS];
		if (!GetPlayerBotYoharaMapShares(map, share))
			return false;
		LPITEM main = FindPlayerBotBestTalisman(ch);
		if (GetPlayerBotTalismanItemGain(offer, share) > GetPlayerBotTalismanItemGain(main, share))
			return true;
		if (main && GetPlayerBotTalismanElementOf(main->GetVnum()) == e)
			return false;
		int spareShare[PLAYERBOT_TALISMAN_ELEMENTS];
		GetPlayerBotYoharaMapShares(GetPlayerBotYoharaSpareMap(map), spareShare);
		return GetPlayerBotTalismanItemGain(offer, spareShare) > GetPlayerBotTalismanItemGain(FindPlayerBotYoharaSpareTalisman(ch), spareShare);
	}

	// ---- the market -----------------------------------------------------------------------

	// A Talisman +0 of the project's element and the Ornament, for a worker short of them -
	// not while the seed still owes it the step.
	bool WantsPlayerBotTalismanOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (WantsPlayerBotYoharaTalismanOffer(ch, offer))	// MT2009_PLUS_BOT_YOHARA_ELEMENTS_V1
			return true;
		if (!ch || !offer || !IsPlayerBotTalismanWorker(ch) || GetPlayerBotTalismanSeedLeft(ch) > 0)
			return false;
		const TPlayerBotTalismanPlan& p = GetPlayerBotTalismanPlan(ch);
		if (p.element < 0)
			return false;
		if (offer->GetVnum() == PLAYERBOT_TALISMAN_ELEMENT[p.element].baseVnum)
			return p.spares < PLAYERBOT_TALISMAN_SPARE_WANT || p.projectId == 0;
		if (offer->GetVnum() == PLAYERBOT_TALISMAN_ORNAMENT_VNUM)
			return p.projectId != 0 && p.stepWearable && p.ornaments < PLAYERBOT_TALISMAN_SPARE_WANT &&
					(int)offer->GetCount() <= PLAYERBOT_TALISMAN_ORNAMENT_KEEP;
		return false;
	}

	bool CanPlayerBotPayForTalismanOffer(LPCHARACTER ch, LPITEM offer, long long price)
	{
		if (!ch || !offer || price <= 0)
			return false;
		const long long spare = GetPlayerBotTalismanSpare(ch);
		const long long count = std::max<long long>(1, (long long)offer->GetCount());
		if (IsPlayerBotTalismanVnum(offer->GetVnum()))
			// MT2009_PLUS_SHEET_PRICES_ONLY_V1: the grade's price scaled as the
			// counters ask it (ScalePlayerBotIwakuraPrice), not as written.
			return price / count <= (long long)ScalePlayerBotIwakuraPrice(GetPlayerBotTalismanPrice(offer->GetVnum())) *
					PLAYERBOT_TALISMAN_BUY_OVER_PERCENT / 100 &&
					price <= spare * 40 / 100;
		const long long fair = (long long)GetPlayerBotShopAskingPrice(offer);
		const long long cap = std::max<long long>(fair * 2, 150000LL * count);
		return price <= cap && price <= spare * 10 / 100;
	}

	void CollectPlayerBotTalismanMissing(LPCHARACTER ch, std::map<DWORD, int>& missing)
	{
		if (!ch || !IsPlayerBotTalismanWorker(ch) || GetPlayerBotTalismanSeedLeft(ch) > 0)
			return;
		const TPlayerBotTalismanPlan& p = GetPlayerBotTalismanPlan(ch);
		if (p.element < 0)
			return;
		if (p.projectId == 0 || p.spares < PLAYERBOT_TALISMAN_SPARE_WANT)
			missing[PLAYERBOT_TALISMAN_ELEMENT[p.element].baseVnum] +=
					std::max(1, PLAYERBOT_TALISMAN_SPARE_WANT - p.spares);
		if (p.projectId != 0 && p.stepWearable && p.ornaments < PLAYERBOT_TALISMAN_SPARE_WANT)
			missing[PLAYERBOT_TALISMAN_ORNAMENT_VNUM] += PLAYERBOT_TALISMAN_SPARE_WANT - p.ornaments;
	}

	// What a worker keeps of a vnum for its steps (the counter lists the rest).
	int GetPlayerBotTalismanMaterialKeep(LPCHARACTER ch, DWORD vnum)
	{
		if (!ch || !IsPlayerBotTalismanWorker(ch))
			return 0;
		const TPlayerBotTalismanPlan& p = GetPlayerBotTalismanPlan(ch);
		if (p.element < 0)
			return 0;
		if (vnum == PLAYERBOT_TALISMAN_ELEMENT[p.element].baseVnum)
			return PLAYERBOT_TALISMAN_SPARE_KEEP + (p.projectId == 0 ? 1 : 0);
		if (p.projectId == 0 || !p.stepWearable)
			return 0;
		if (vnum == PLAYERBOT_TALISMAN_ORNAMENT_VNUM)
			return PLAYERBOT_TALISMAN_ORNAMENT_KEEP;
		if (vnum == PLAYERBOT_TALISMAN_FLOWER_VNUM)
			return PLAYERBOT_TALISMAN_FLOWERS_A_STEP * PLAYERBOT_TALISMAN_SPARE_KEEP;
		return 0;
	}

	// The talisman items a bot keeps whatever their vnum's keep: the project and the one it
	// wears best.
	bool IsPlayerBotKeptTalisman(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !IsPlayerBotTalismanItem(item))
			return false;
		const TPlayerBotTalismanPlan& p = GetPlayerBotTalismanPlan(ch);
		if (p.projectId != 0 && item->GetID() == p.projectId)
			return true;
#ifdef MT2009_PLUS_BOT_WIND_SET_V1
		// MT2009_PLUS_BOT_WIND_SET_V1: the best lightning and the best wind talisman of a bot with a wind set (each set's)
		if (IsPlayerBotWindSetTalismanKept(ch, item))
			return true;
#endif
		// MT2009_PLUS_BOT_SUNGMA_DEATHS_V1: a talisman of another element at least as strong as the worn one is the
		// talisman of another map (the Yohara maps' cohort carries one an element - tools/yohara_bot_cohort_sungma.py),
		// not goods for the merchant or a counter.
		LPITEM worn = ch->GetWear(WEAR_PENDANT);
		if (worn && worn != item && IsPlayerBotTalismanItem(worn) && GetPlayerBotTalismanPlus(item) > 0 &&
				GetPlayerBotTalismanPlus(item) >= GetPlayerBotTalismanPlus(worn) &&
				GetPlayerBotTalismanElementOf(item->GetVnum()) != GetPlayerBotTalismanElementOf(worn->GetVnum()))
			return true;
		// MT2009_PLUS_BOT_YOHARA_ELEMENTS_V1 (D14): on Yohara the spare for the next map stays in the bag too (a drop or
		// a stand's included).
		if (item == FindPlayerBotYoharaSpareTalisman(ch))
			return true;
		return item == FindPlayerBotBestTalisman(ch);
	}

	void NotePlayerBotTalismanBought(LPCHARACTER ch, DWORD vnum, long long price)
	{
		if (!ch || !(IsPlayerBotTalismanVnum(vnum) || vnum == PLAYERBOT_TALISMAN_ORNAMENT_VNUM))
			return;
		++s_kPlayerBotTalismanStats.bought;
		s_kPlayerBotTalismanStats.boughtYang += (unsigned long long)std::max<long long>(0, price);
		ForgetPlayerBotTalismanPlan(ch);
		// MT2009_PLUS_BOT_YOHARA_ELEMENTS_V1: a Yohara bot's talisman for its map or its spare.
		if (IsPlayerBotTalismanVnum(vnum) && GetPlayerBotYoharaElementMap(ch) != 0)
		{
			const int e = GetPlayerBotTalismanElementOf(vnum);
			sys_log(0, "PLAYERBOT_ELEMENTS: talisman bought pid=%u name=%s map=%ld vnum=%u (%s +%d) price=%lld gold=%lld",
					ch->GetPlayerID(), ch->GetName(), GetPlayerBotYoharaElementMap(ch), vnum, PLAYERBOT_TALISMAN_ELEMENT[e].name,
					(int)(vnum - PLAYERBOT_TALISMAN_ELEMENT[e].baseVnum), price, (long long)ch->GetGold());
		}
	}

	// ---- the gifts --------------------------------------------------------------------------

	// Once a bot qualifies: whether it is in the seeded share, and - with no talisman of its
	// own - the Talisman +0 it wears. The steps' materials come at the anvil.
	void DecidePlayerBotTalismanSeed(LPCHARACTER ch)
	{
		if (!ch || (int)ch->GetLevel() < PLAYERBOT_TALISMAN_MIN_LEVEL || ArePlayerBotCraftSeedsOff() ||
				ch->GetQuestFlag(PLAYERBOT_TALISMAN_SEED_FLAG) != 0)
			return;
		const bool seeded = IsPlayerBotTalismanWorker(ch) &&
				PlayerBotNavHash(ch->GetPlayerID() ^ 0x53454544U) % 100U < (DWORD)PLAYERBOT_TALISMAN_SEED_PERCENT;
		if (seeded && FindPlayerBotBestTalisman(ch) == NULL)
		{
			if (ch->GetEmptyInventory(1) < 0)
				return;	// asked again at the next look
			const TPlayerBotTalismanPlan& p = GetPlayerBotTalismanPlan(ch, true);
			const DWORD vnum = PLAYERBOT_TALISMAN_ELEMENT[p.element >= 0 ? p.element : 1].baseVnum;
			if (!ch->AutoGiveItem(vnum, 1, -1, false))
				return;
		}
		ch->SetQuestFlag(PLAYERBOT_TALISMAN_SEED_FLAG, (seeded ? PLAYERBOT_TALISMAN_SEED_STEPS : 0) + 1);
		if (seeded)
		{
			++s_kPlayerBotTalismanStats.seeded;
			sys_log(0, "PLAYERBOT_TALISMAN: seeded pid=%u name=%s lv=%d steps=%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), PLAYERBOT_TALISMAN_SEED_STEPS);
		}
		ForgetPlayerBotTalismanPlan(ch);
	}

	// MT2009_PLUS_BOT_TALISMAN_FIRST_V1 (the owner, 10 November 2026: "587 of 669 bots of the talisman programme have no
	// talisman - find why and fix it"). Why: the plan's project is the talisman of the hunting map's own element
	// (p.projectId 0 while the bot owns none of it - BOT_TALISMAN_CHEAP's no_talisman), and the only ways to one were the
	// seed (35% of the workers, once, at level 30, of the element of that day's map), a counter's +0 at the owner's price
	// (700 000, at most 40% of the spare purse - the bots 70+ hold 0.4-0.9 M) or the cheap step, which needs a project
	// already AND a body armour at +7 (the bots 70-97 wear +4/+5: the pearls). So a worker never got the talisman of the
	// element it fights. Now a worker of PLAYERBOT_TALISMAN_FIRST_MIN_LEVEL+ with no talisman of its plan's element gets the
	// Talisman +0 of it from the Blacksmith for PLAYERBOT_TALISMAN_FIRST_YANG (its spare purse), at most one in
	// PLAYERBOT_TALISMAN_FIRST_GAP_H hours (quest flag playerbot.talisman_first - a map change of element does not buy one
	// each time), and wears it when it is the best for the map; its steps go on by the old rules. Event flags:
	// m2_bot_talisman_first_off 1 - off; m2_bot_talisman_first_yang N (10 000-5 000 000).
	// MT2009_PLUS_BOT_TALISMAN_DAILY_V1 (the owner, 10 November 2026: 150 000 was too cheap - 500 000, one a day, and with it
	// the talisman goes up one "+" a day): the Blacksmith's daily deal, PLAYERBOT_TALISMAN_FIRST_YANG (now 500 000) at most
	// once in PLAYERBOT_TALISMAN_FIRST_GAP_H hours (the same flag) -
	//   * a worker with no talisman of its plan's element: the Talisman +0 of it, as before;
	//   * a worker that has it (the project, its next plus wearable) with no spare +0 of the element in the bag, no seed
	//     owed and no cheap step (MT2009_PLUS_BOT_TALISMAN_CHEAP_V1 sells the goods for less - its armour +7 rule is not
	//     asked here): the step's goods - the Talisman +0 the recipe eats and the Ornament (30031) when the bag lacks one -
	//     for the same price, and only when the rest of that step is in the purse too, so the anvil's next visit makes the +1.
	// The step stays the recipe's (refine_proto 20001-21200: 10 Kwiat Zywiolu at Mistrz's 100 000, 1 Ornament, 1 Talisman +0
	// of the element, the fee - 280 000 to +49, 3 375 000 from +50 ... 20 950 000 at +199 - and 100%): after the deal the
	// fee and the missing flowers must fit PLAYERBOT_TALISMAN_SPEND_PERCENT of what is left (CanPlayerBotPayTalismanStep),
	// i.e. a +1 under +50 is ~1.8 M a day in all (500 000 + 1 000 000 flowers + 280 000 fee). Event flag
	// m2_bot_talisman_daily_step_off 1 - the first talisman only (as before).
	const int PLAYERBOT_TALISMAN_FIRST_MIN_LEVEL = 60;
	const long long PLAYERBOT_TALISMAN_FIRST_YANG = 500000LL;
	const int PLAYERBOT_TALISMAN_FIRST_GAP_H = 24;
	const char* const PLAYERBOT_TALISMAN_FIRST_FLAG = "playerbot.talisman_first";
	unsigned int s_uPlayerBotTalismanFirst = 0, s_uPlayerBotTalismanFirstPurse = 0;
	unsigned int s_uPlayerBotTalismanDailyStep = 0, s_uPlayerBotTalismanDailyStepPurse = 0;	// MT2009_PLUS_BOT_TALISMAN_DAILY_V1

	bool GivePlayerBotFirstTalisman(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded() || ch->IsDead() || (int)ch->GetLevel() < PLAYERBOT_TALISMAN_FIRST_MIN_LEVEL ||
				!IsPlayerBotTalismanWorker(ch) || IsPlayerBotGearFrozen(ch) || ch->GetExchange() || ch->GetMyShop())
			return false;
		quest::CQuestManager& q = quest::CQuestManager::instance();
		if (q.GetEventFlag("m2_bot_talisman_first_off") != 0)
			return false;
		const int last = ch->GetQuestFlag(PLAYERBOT_TALISMAN_FIRST_FLAG);
		if (last != 0 && get_global_time() - last < PLAYERBOT_TALISMAN_FIRST_GAP_H * 3600)
			return false;
		const TPlayerBotTalismanPlan p = GetPlayerBotTalismanPlan(ch);
		if (p.element < 0 || p.element >= PLAYERBOT_TALISMAN_ELEMENTS || GetPlayerBotTalismanSeedLeft(ch) > 0)
			return false;
		const DWORD vnum = PLAYERBOT_TALISMAN_ELEMENT[p.element].baseVnum;
		const int flag = q.GetEventFlag("m2_bot_talisman_first_yang");
		const long long price = flag >= 10000 && flag <= 5000000 ? (long long)flag : PLAYERBOT_TALISMAN_FIRST_YANG;
		// MT2009_PLUS_BOT_TALISMAN_DAILY_V1: a project already - the day's step goods
		if (p.projectId != 0)
		{
			if (q.GetEventFlag("m2_bot_talisman_daily_step_off") != 0 || !p.stepWearable || p.spares >= 1 ||
					IsPlayerBotTalismanCheapStep(ch, p))
				return false;
			LPITEM project = GetPlayerBotTalismanProject(ch);
			const long long fee = project ? GetPlayerBotTalismanStepFee(ch, project) : -1;
			if (!project || fee < 0 || IsPlayerBotSidekickLockedItem(ch, project))
				return false;
			const int flowersMissing = std::max(0, PLAYERBOT_TALISMAN_FLOWERS_A_STEP - p.flowers);
			const long long rest = fee + flowersMissing * GetPlayerBotTalismanFlowerPrice();
			const long long spare = GetPlayerBotTalismanSpare(ch);
			if (spare < price || (spare - price) * PLAYERBOT_TALISMAN_SPEND_PERCENT / 100 < rest)
			{
				++s_uPlayerBotTalismanDailyStepPurse;
				return false;
			}
			const bool ornament = p.ornaments < 1;
			if (CountPlayerBotFreeInventoryCells(ch) < (ornament ? 2 : 1))
				return false;
			PlayerBotChangeGold(ch, -price);
			if (!ch->AutoGiveItem(vnum, 1, -1, false))
			{
				PlayerBotChangeGold(ch, price);
				return false;
			}
			if (ornament)
				ch->AutoGiveItem(PLAYERBOT_TALISMAN_ORNAMENT_VNUM, 1, -1, false);
			ch->SetQuestFlag(PLAYERBOT_TALISMAN_FIRST_FLAG, get_global_time());
			++s_uPlayerBotTalismanDailyStep;
			ForgetPlayerBotTalismanPlan(ch);
			sys_log(0, "PLAYERBOT_TALISMAN: daily step goods pid=%u name=%s lv=%d element=%s plus=%d vnum=%u ornament=%d price=%lld "
					"step_rest=%lld (fee=%lld flowers_missing=%d) gold=%lld",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), PLAYERBOT_TALISMAN_ELEMENT[p.element].name, p.plus, vnum,
					ornament ? 1 : 0, price, rest, fee, flowersMissing, (long long)ch->GetGold());
			return true;
		}
		if (ch->CountSpecifyItem(vnum) > 0 || !IsPlayerBotWearableAtLevel(ch, vnum))
			return false;
		if (GetPlayerBotTalismanSpare(ch) < price)
		{
			++s_uPlayerBotTalismanFirstPurse;
			return false;
		}
		if (ch->GetEmptyInventory(1) < 0)
			return false;
		PlayerBotChangeGold(ch, -price);
		if (!ch->AutoGiveItem(vnum, 1, -1, false))
		{
			PlayerBotChangeGold(ch, price);
			return false;
		}
		ch->SetQuestFlag(PLAYERBOT_TALISMAN_FIRST_FLAG, get_global_time());
		++s_uPlayerBotTalismanFirst;
		ForgetPlayerBotTalismanPlan(ch);
		sys_log(0, "PLAYERBOT_TALISMAN: first talisman pid=%u name=%s lv=%d element=%s vnum=%u dominant=%d price=%lld gold=%lld",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), PLAYERBOT_TALISMAN_ELEMENT[p.element].name, vnum, p.dominant,
				price, (long long)ch->GetGold());
		return true;
	}

	// ---- wearing --------------------------------------------------------------------------

	// Puts on the best talisman for the hunting map, when it is not on already. The equipment
	// pass would do the same by GetPlayerBotEquipmentScore; this one runs on a short clock, so
	// the change comes with the map.
	bool WearPlayerBotBestTalisman(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded() || ch->IsDead() || ch->GetExchange() || ch->GetMyShop() ||
				IsPlayerBotGearFrozen(ch))
			return false;
		LPITEM best = FindPlayerBotBestPendant(ch);	// MT2009_PLUS_BOT_YOHARA_ELEMENTS_V1: a Talizman Woli too (D15)
		LPITEM worn = ch->GetWear(WEAR_PENDANT);
		if (!best || best == worn)
			return false;
		if (worn && (IsPlayerBotSidekickLockedItem(ch, worn) || !IsPlayerBotPendantChoice(worn)))
			return false;
		const DWORD oldVnum = worn ? worn->GetVnum() : 0;
		if (worn && (ch->GetEmptyInventory(worn->GetSize()) < 0 || !ch->UnequipItem(worn) || worn->IsEquipped()))
			return false;
		if (!ch->EquipItem(best))
		{
			if (worn && !worn->IsEquipped())
				ch->EquipItem(worn);
			return false;
		}
		++s_kPlayerBotTalismanStats.wears;
		int share[PLAYERBOT_TALISMAN_ELEMENTS];
		const long huntMap = GetPlayerBotTalismanMapShares(ch, share);	// MT2009_PLUS_BOT_YOHARA_ELEMENTS_V1
		const int e = GetPlayerBotTalismanElementOf(best->GetVnum());
		sys_log(0, "PLAYERBOT_TALISMAN: wear pid=%u name=%s lv=%d vnum=%u (%s +%d) old=%u map=%ld share=%d gain=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), best->GetVnum(),
				e >= 0 ? PLAYERBOT_TALISMAN_ELEMENT[e].name : "Woli", e >= 0 ? GetPlayerBotTalismanPlus(best) : (int)(best->GetVnum() % 10), oldVnum, huntMap,
				e >= 0 ? share[e] : 0, GetPlayerBotTalismanGain(e, GetPlayerBotTalismanPlus(best), share));
		ForgetPlayerBotTalismanPlan(ch);
		return true;
	}

	// ---- at the shop and the anvil --------------------------------------------------------

	// At Mistrz: the flowers of up to `steps` steps, from his shop 9550, the shop's price.
	int BuyPlayerBotTalismanFlowers(LPCHARACTER ch, int steps)
	{
		const TPlayerBotTalismanPlan p = GetPlayerBotTalismanPlan(ch, true);
		LPITEM project = GetPlayerBotTalismanProject(ch);
		if (!project || !p.stepWearable || steps <= 0)
			return 0;
		const long long price = GetPlayerBotTalismanFlowerPrice();
		const long long fee = std::max<long long>(0, GetPlayerBotTalismanStepFee(ch, project));
		const long long budget = GetPlayerBotTalismanSpare(ch) * PLAYERBOT_TALISMAN_SPEND_PERCENT / 100;
		// Only for steps the materials allow (a spare and an ornament each, or the seed's).
		const int seedLeft = GetPlayerBotTalismanSeedLeft(ch);
		int byMaterials = seedLeft > 0 ? seedLeft : std::min(p.spares, p.ornaments);
		// MT2009_PLUS_BOT_TALISMAN_CHEAP_V1: a cheap step's goods come at the anvil - the flowers of one step.
		if (byMaterials < 1 && IsPlayerBotTalismanCheapStep(ch, p))
			byMaterials = 1;
		steps = std::min(steps, byMaterials);
		int want = steps * PLAYERBOT_TALISMAN_FLOWERS_A_STEP - p.flowers;
		// The seeded steps' flowers are part of the gift: handed over here, free (the step
		// itself is counted off at the anvil, so a visit cut short owes nothing twice - the
		// flowers wait in the bag).
		if (seedLeft > 0)
		{
			if (want <= 0 || ch->GetEmptyInventory(1) < 0)
				return 0;
			ch->AutoGiveItem(PLAYERBOT_TALISMAN_FLOWER_VNUM, (ITEM_COUNT)want, -1, false);
			++s_kPlayerBotTalismanStats.seedGifts;
			sys_log(0, "PLAYERBOT_TALISMAN: seed flowers given pid=%u name=%s count=%d steps=%d",
					ch->GetPlayerID(), ch->GetName(), want, steps);
			ForgetPlayerBotTalismanPlan(ch);
			return want;
		}
		// Each step's fee stays in the purse.
		while (want > 0 && (long long)want * price + fee * steps > budget)
		{
			--steps;
			want = steps * PLAYERBOT_TALISMAN_FLOWERS_A_STEP - p.flowers;
		}
		if (want <= 0 || ch->GetEmptyInventory(1) < 0)
			return 0;
		PlayerBotChangeGold(ch, -(long long)want * price);
		ch->AutoGiveItem(PLAYERBOT_TALISMAN_FLOWER_VNUM, (ITEM_COUNT)want, -1, false);
		s_kPlayerBotTalismanStats.flowersBought += (unsigned)want;
		sys_log(0, "PLAYERBOT_TALISMAN: flowers bought pid=%u name=%s count=%d price=%lld steps=%d gold=%lld",
				ch->GetPlayerID(), ch->GetName(), want, price, steps, (long long)ch->GetGold());
		ForgetPlayerBotTalismanPlan(ch);
		return want;
	}

	// One step at the anvil: the seed's missing piece first, the project off the slot, DoRefine
	// - the engine's fee, materials and roll. Returns whether an attempt was made.
	bool RefinePlayerBotTalismanStep(LPCHARACTER ch)
	{
		// A copy: the plan is forgotten (erased) on the way.
		const TPlayerBotTalismanPlan plan = GetPlayerBotTalismanPlan(ch, true);
		LPITEM project = GetPlayerBotTalismanProject(ch);
		if (!project || !plan.stepWearable || IsPlayerBotGearFrozen(ch) || IsPlayerBotSidekickLockedItem(ch, project))
			return false;
		const int e = plan.element;
		if (e < 0 || !CanPlayerBotPayTalismanStep(ch, project, plan.flowers))
			return false;
		if (plan.flowers < PLAYERBOT_TALISMAN_FLOWERS_A_STEP)
			return false;	// Mistrz's flowers first (playerbot_workshop.h)

		// The seed's step: what the bag lacks of the spare and the ornament.
		int seedLeft = GetPlayerBotTalismanSeedLeft(ch);
		// MT2009_PLUS_BOT_TALISMAN_CHEAP_V1: no seed owed - the cheap step's goods for their yang.
		if ((plan.spares < 1 || plan.ornaments < 1) && seedLeft <= 0 && IsPlayerBotTalismanCheapStep(ch, plan))
		{
			const long long goods = GetPlayerBotTalismanCheapYang(ch, plan);
			const long long fee = std::max<long long>(0, GetPlayerBotTalismanStepFee(ch, project));
			if (CountPlayerBotFreeInventoryCells(ch) < 2 || goods + fee > GetPlayerBotTalismanSpare(ch))
				return false;
			PlayerBotChangeGold(ch, -goods);
			if (plan.spares < 1)
			{
				ch->AutoGiveItem(PLAYERBOT_TALISMAN_ELEMENT[e].baseVnum, 1, -1, false);
				++s_kPlayerBotTalismanCheapStats.spares;
			}
			if (plan.ornaments < 1)
			{
				ch->AutoGiveItem(PLAYERBOT_TALISMAN_ORNAMENT_VNUM, 1, -1, false);
				++s_kPlayerBotTalismanCheapStats.ornaments;
			}
			++s_kPlayerBotTalismanCheapStats.steps;
			s_kPlayerBotTalismanCheapStats.yang += (unsigned long long)goods;
			sys_log(0, "BOT_TALISMAN_CHEAP: step goods pid=%u name=%s lv=%d element=%s plus=%d spare=%d ornament=%d yang=%lld gold=%lld",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), PLAYERBOT_TALISMAN_ELEMENT[e].name, plan.plus,
					plan.spares < 1 ? 1 : 0, plan.ornaments < 1 ? 1 : 0, goods, (long long)ch->GetGold());
		}
		else if (plan.spares < 1 || plan.ornaments < 1)
		{
			if (seedLeft <= 0 || CountPlayerBotFreeInventoryCells(ch) < 2)
				return false;
			if (plan.spares < 1)
				ch->AutoGiveItem(PLAYERBOT_TALISMAN_ELEMENT[e].baseVnum, 1, -1, false);
			if (plan.ornaments < 1)
				ch->AutoGiveItem(PLAYERBOT_TALISMAN_ORNAMENT_VNUM, 1, -1, false);
			ch->SetQuestFlag(PLAYERBOT_TALISMAN_SEED_FLAG, seedLeft);	// left - 1, plus one
			--seedLeft;
			++s_kPlayerBotTalismanStats.seedGifts;
			sys_log(0, "PLAYERBOT_TALISMAN: seed step given pid=%u name=%s element=%s spare=%d ornament=%d left=%d",
					ch->GetPlayerID(), ch->GetName(), PLAYERBOT_TALISMAN_ELEMENT[e].name,
					plan.spares < 1 ? 1 : 0, plan.ornaments < 1 ? 1 : 0, seedLeft);
		}

		if (project->IsEquipped())
		{
			if (ch->GetEmptyInventory(project->GetSize()) < 0 || !ch->UnequipItem(project) || project->IsEquipped())
				return false;
		}
		if (project->GetOwner() != ch || project->GetWindow() != INVENTORY || project->GetCell() >= PLAYERBOT_BAG_CELLS)
			return false;
		const DWORD oldVnum = project->GetVnum();
		const DWORD nextVnum = project->GetRefinedVnum();
		const int before = (int)ch->CountSpecifyItem(nextVnum);
		const long long goldBefore = (long long)ch->GetGold();
		const bool attempted = ch->DoRefine(project, false);
		ForgetPlayerBotTalismanPlan(ch);
		if (!attempted)
		{
			sys_log(0, "PLAYERBOT_TALISMAN: refine refused pid=%u name=%s vnum=%u flowers=%d ornaments=%d spares=%d",
					ch->GetPlayerID(), ch->GetName(), oldVnum, (int)ch->CountSpecifyItem(PLAYERBOT_TALISMAN_FLOWER_VNUM),
					(int)ch->CountSpecifyItem(PLAYERBOT_TALISMAN_ORNAMENT_VNUM),
					CountPlayerBotTalismanSpares(ch, e, NULL));
			return false;
		}
		const bool success = (int)ch->CountSpecifyItem(nextVnum) > before;
		const long long paid = goldBefore - (long long)ch->GetGold();
		++s_kPlayerBotTalismanStats.steps;
		s_kPlayerBotTalismanStats.fees += (unsigned long long)std::max<long long>(0, paid);
		sys_log(0, "PLAYERBOT_TALISMAN: refine %s pid=%u name=%s lv=%d %s +%d -> +%d fee=%lld dominant=%d gold=%lld",
				success ? "SUCCESS" : "FAILED", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(),
				PLAYERBOT_TALISMAN_ELEMENT[e].name, (int)(oldVnum - PLAYERBOT_TALISMAN_ELEMENT[e].baseVnum),
				(int)(nextVnum - PLAYERBOT_TALISMAN_ELEMENT[e].baseVnum), paid, plan.dominant, (long long)ch->GetGold());
		return true;
	}

	void LogPlayerBotTalismanCensus()
	{
		const TPlayerBotTalismanStats& s = s_kPlayerBotTalismanStats;
		sys_log(0, "PLAYERBOT_TALISMAN: census steps=%u wears=%u seeded=%u seed_steps=%u flowers=%u bought=%u bought_yang=%llu fees=%llu maps=%u "
				"first=%u first_short_purse=%u daily_step=%u daily_step_short_purse=%u",
				s.steps, s.wears, s.seeded, s.seedGifts, s.flowersBought, s.bought, s.boughtYang, s.fees,
				(unsigned)s_mapPlayerBotElementCensus.size(), s_uPlayerBotTalismanFirst, s_uPlayerBotTalismanFirstPurse,
				s_uPlayerBotTalismanDailyStep, s_uPlayerBotTalismanDailyStepPurse);	// MT2009_PLUS_BOT_TALISMAN_FIRST_V1
		// MT2009_PLUS_BOT_TALISMAN_CHEAP_V1: the cheap steps since the core started, and the bots' talismans now - the
		// workers, their projects at +0, and what holds the rest of them back.
		unsigned workers = 0, atZero = 0, noProject = 0, cheapReady = 0, shortGear = 0, shortPurse = 0, ready = 0;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !IsPlayerBotTalismanWorker(ch) || !ch->IsItemLoaded())
				continue;
			++workers;
			const TPlayerBotTalismanPlan& p = GetPlayerBotTalismanPlan(ch);
			if (p.projectId == 0)
			{
				++noProject;
				continue;
			}
			if (p.plus == 0)
				++atZero;
			if (HasPlayerBotTalismanWork(ch))
			{
				++ready;
				if (p.spares < 1 || p.ornaments < 1)
					++cheapReady;
			}
			else if (p.stepWearable && (p.spares < 1 || p.ornaments < 1) && !IsPlayerBotTalismanCheapStep(ch, p))
				++shortGear;
			else if (p.stepWearable)
				++shortPurse;
		}
		const TPlayerBotTalismanCheapStats& k = s_kPlayerBotTalismanCheapStats;
		sys_log(0, "BOT_TALISMAN_CHEAP: census on=%d armour_plus=%d max_plus=%d workers=%u no_talisman=%u at_zero=%u ready=%u "
				"ready_cheap=%u waiting_armour_or_goods=%u waiting_purse=%u cheap_steps=%u spares=%u ornaments=%u yang=%llu",
				IsPlayerBotSmallFixOn(SMALLFIX_TALISMAN) ? 1 : 0, GetPlayerBotSmallFixCfg().talismanArmourPlus,
				GetPlayerBotSmallFixCfg().talismanMaxPlus, workers, noProject, atZero, ready, cheapReady, shortGear, shortPurse,
				k.steps, k.spares, k.ornaments, k.yang);
	}
}

#else

namespace
{
	bool IsPlayerBotTalismanItem(LPITEM) { return false; }
	long long GetPlayerBotTalismanScore(LPCHARACTER, LPITEM) { return 0; }
	int GetPlayerBotTalismanElementOf(DWORD) { return -1; }	// MT2009_PLUS_BOT_YOHARA_ELEMENTS_V1
	bool HasPlayerBotTalismanWork(LPCHARACTER) { return false; }
	bool WantsPlayerBotTalismanOffer(LPCHARACTER, LPITEM) { return false; }
	bool CanPlayerBotPayForTalismanOffer(LPCHARACTER, LPITEM, long long) { return false; }
	void CollectPlayerBotTalismanMissing(LPCHARACTER, std::map<DWORD, int>&) {}
	int GetPlayerBotTalismanMaterialKeep(LPCHARACTER, DWORD) { return 0; }
	bool IsPlayerBotKeptTalisman(LPCHARACTER, LPITEM) { return false; }
	void NotePlayerBotTalismanBought(LPCHARACTER, DWORD, long long) {}
	void DecidePlayerBotTalismanSeed(LPCHARACTER) {}
	bool GivePlayerBotFirstTalisman(LPCHARACTER) { return false; }	// MT2009_PLUS_BOT_TALISMAN_FIRST_V1
	bool WearPlayerBotBestTalisman(LPCHARACTER) { return false; }
	int BuyPlayerBotTalismanFlowers(LPCHARACTER, int) { return 0; }
	bool RefinePlayerBotTalismanStep(LPCHARACTER) { return false; }
	void LogPlayerBotTalismanCensus() {}
	long GetPlayerBotHuntingMap(LPCHARACTER ch);
}

#endif

#endif
