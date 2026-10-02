#ifndef __INC_METIN2_PLAYERBOT_HERBALISM_H__
#define __INC_METIN2_PLAYERBOT_HERBALISM_H__

// Herbalism: Baek-Go's crafting board, worked without his window.
//
// The 2.x package ships the whole system and this world has never used a line
// of it. Read off the running server on 17 September: the onboarding quest is
// compiled and hooked to mob 20018 in all three first villages, his special
// shop 14 sells the Herbalist's Knife and the three empty bottles, and
// world.crafting_proto carries 77 rows behind eight levels of recipe knowledge.
// What it produced in game was nothing at all - the recipes that drop from
// Metin stones (29 groups at 12.5-18%) went to the merchant as an unknown
// item, and the herbs went on the counters as bulk goods.
//
// Three engine facts decide the shape of what follows:
//
//   * The board is a CLIENT WINDOW. crafting.open sends `craft_open` down the
//     chat channel and crafting.create refuses anything unless that window
//     reported itself open, so a bot - which has no client - can never press a
//     single button on it. The craft is therefore re-implemented here against
//     CCraftingManager, the way the stable keeper's hand-over and the ore
//     smelting already are. Everything it touches is the quest's own: the same
//     rows, the same odds, the same price, and the same progress flags
//     (`crafting.progress_<recipe>`), so a bot and a player are counted by one
//     ledger and the panel reads both the same way.
//   * A craft SPENDS THE MATERIALS WHETHER IT SUCCEEDS OR NOT - crafting.lua
//     removes them before it rolls - so a 60% row is a real loss and a bot
//     keeps PLAYERBOT_HERBALISM_GOLD_RESERVE rather than grinding its purse.
//   * A potion is ITEM_POTION (type 36), a type of its own on this line, and
//     its use goes through the compiled quest hook `object/36/use_type`, not
//     through any case in char_item.cpp. So a bot drinks one with an ordinary
//     UseItem and the quest does the rest: value0 is the duration, value1 the
//     group (boost 1, offensive 2, defensive 3) and the engine allows 5, 3 and
//     2 affects of those groups at once.
//
// What is deliberately NOT here: picking the plants. The knife wants a growing
// bush to click and this world spawns four of the sixteen - the Alpine Rose in
// the three second villages, the Thistle on Mount Sohan, the Amber Petal and
// the Nettle on the two Trent maps - none of them the Peach Blossom the
// onboarding asks for. That is the mining problem again (no map spawns a vein
// either) and placing plants is a change of its own. The herbs a bot works
// with come from the drop tables, where all of them are: the bags and counters
// of the test world held 2788 of them before a single line of this ran.
//
// An implementation fragment in the sense playerbot_types.h describes: include
// it exactly once, after playerbot_mining.h - it uses the free-cell count and
// the gold reserve - and before playerbot_economy.h, whose junk rule asks it
// what a potion and a recipe are worth keeping.

#if defined(PLAYERBOT_ENGINE_MT2009)
#include "crafting_manager.h"
#endif

namespace
{
#if defined(PLAYERBOT_ENGINE_MT2009)

	// Baek-Go's own rows, read out of the package's crafting_data.lua
	// (CRAFTING_BAEKGO = 102) rather than guessed from the numbering: 58-66 are
	// commented out there as "wszystkie rosy pvp" and are not on his board, so
	// a bot that walked the range would ask for rows the quest refuses.
	const DWORD PLAYERBOT_HERBALISM_ROWS[] = {
		11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27,
		28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44,
		45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57,
		67, 68, 71, 72, 73, 74, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88,
		92, 93, 94, 95
	};
	const size_t PLAYERBOT_HERBALISM_ROW_COUNT =
			sizeof(PLAYERBOT_HERBALISM_ROWS) / sizeof(PLAYERBOT_HERBALISM_ROWS[0]);

	// The herbalist's sixteen, by vnum: the materials of his board.
	bool IsPlayerBotHerbalismHerb(DWORD vnum)
	{
		return vnum >= PLAYERBOT_HERB_VNUM_FIRST && vnum <= PLAYERBOT_HERB_VNUM_LAST;
	}

	int CountPlayerBotHerbKnives(LPCHARACTER ch);

	// MT2009_PLUS_BOT_HERBALIST_ACTIVITY_V1: there is no herbalist by trade
	// any more (the FIX_V1 share of 10% by pid that spent three quarters of
	// its time at the bushes and was the Zielarz throughout). Picking is an
	// activity of any bot (IsPlayerBotHerbalistNow, below) and a bot that has
	// taken it up - it bought the Herbalist's Knife for its first session -
	// is a gatherer: it keeps its herbs for Baek-Go's board, brews them there
	// with its own purse's rules and keeps the knife in the bag between two
	// sessions, the way an angler keeps its rod. Never a dropper (its farm is
	// one thing), nor a player's companion, nor a shouter.
	bool IsPlayerBotHerbGatherer(LPCHARACTER ch)
	{
		if (!ch || ch->GetLevel() < PLAYERBOT_HERBALISM_MIN_LEVEL)
			return false;
		TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotAIStates.end() || IsPlayerBotDropper(it->second.bPersonality) ||
				IsPlayerBotSidekickPID(ch->GetPlayerID()) || IsPlayerBotShouterPID(ch->GetPlayerID()))
			return false;
		return CountPlayerBotHerbKnives(ch) > 0;
	}

	// What a craft leaves in the purse. Two million was the Conqueror's
	// reserve and stays his; for a gatherer it is its own reserve (the
	// teleporter fare, the battle horse, the guild's fund) and a little over,
	// or no bot of a young world ever brewed the cheapest row.
	long long GetPlayerBotHerbalismGoldReserve(LPCHARACTER ch)
	{
		if (IsPlayerBotHerbGatherer(ch))   // MT2009_PLUS_BOT_HERBALIST_ACTIVITY_V1
			return std::max<long long>(PLAYERBOT_HERBALIST_GOLD_RESERVE,
					(long long)GetPlayerBotReservedGold(ch) + PLAYERBOT_HERBALIST_GOLD_RESERVE);
		return PLAYERBOT_HERBALISM_GOLD_RESERVE;
	}

	bool IsPlayerBotCraftedPotion(LPITEM item)
	{
		return item && item->GetType() == ITEM_POTION;
	}

	bool IsPlayerBotCraftRecipeItem(LPITEM item)
	{
		return item && item->GetType() == ITEM_USE &&
				item->GetSubType() == USE_CRAFT_RECIPE;
	}

	// The green and purple potions (Zielona/Fioletowa Mikstura M/S/D, both
	// runs of them) that a counter sells in packs (PLAYERBOT_SHOP_POTION_PACKS).
	bool IsPlayerBotPackedPotion(LPITEM item)
	{
		if (!item || item->GetType() != ITEM_POTION)
			return false;
		const DWORD vnum = item->GetVnum();
		return (vnum >= 27100 && vnum <= 27105) || (vnum >= 27110 && vnum <= 27115);
	}

	// The quest's own ledger: pc.setf("crafting", "progress_<vnum>") in
	// crafting.lua, which is `crafting.progress_<vnum>` to GetQuestFlag.
	int GetPlayerBotCraftProgress(LPCHARACTER ch, DWORD recipeVnum)
	{
		if (!ch || recipeVnum == 0)
			return 0;
		char flag[64];
		snprintf(flag, sizeof(flag), "crafting.progress_%u", recipeVnum);
		return std::max(0, ch->GetQuestFlag(flag));
	}

	void SetPlayerBotCraftProgress(LPCHARACTER ch, DWORD recipeVnum, int value)
	{
		if (!ch || recipeVnum == 0)
			return;
		char flag[64];
		snprintf(flag, sizeof(flag), "crafting.progress_%u", recipeVnum);
		ch->SetQuestFlag(flag, value);
	}

	// herbalism.lua asks for this before it opens the board at all, and before
	// a recipe may be read (herbalism.can_craft). The quest sets it by walking a
	// player through Baek-Go's dialog; a bot has no dialog, so it is given the
	// same thing on the same terms wherever it stands: level fifteen and ten
	// Peach Blossoms in the bag - which drop from 29 monsters on this world -
	// and in return the first recipe and five bottles. The quest only looks at
	// the flowers and never takes them (herbalism_onboarding.quest, the
	// state_progress handler), and neither does this: the first build took
	// them, which was a price no player paid.
	bool IsPlayerBotHerbalismUnlocked(LPCHARACTER ch)
	{
		return ch && ch->GetQuestFlag("herbalism_onboarding.completed") > 0;
	}

	bool EnsurePlayerBotHerbalismStarted(LPCHARACTER ch)
	{
		if (!ch)
			return false;
		if (IsPlayerBotHerbalismUnlocked(ch))
			return true;
		if (ch->GetLevel() < PLAYERBOT_HERBALISM_MIN_LEVEL)
			return false;
		const int flowers = (int) ch->CountSpecifyItem(PLAYERBOT_HERBALISM_ONBOARD_FLOWER);
		if (flowers < PLAYERBOT_HERBALISM_ONBOARD_COUNT)
			return false;
		if (CountPlayerBotFreeInventoryCells(ch) < 2)
			return false;
		ch->AutoGiveItem(PLAYERBOT_HERBALISM_FIRST_RECIPE, 1);
		ch->AutoGiveItem(PLAYERBOT_HERBALISM_BOTTLE_M, PLAYERBOT_HERBALISM_ONBOARD_BOTTLES);
		ch->SetQuestFlag("herbalism_onboarding.completed", 1);
		sys_log(0, "PLAYERBOT_HERB: onboarding done pid=%u name=%s level=%u flowers=%d",
				ch->GetPlayerID(), ch->GetName(), (unsigned int) ch->GetLevel(), flowers);
		return true;
	}

	// The quest's own wait flag, pc.setf("crafting", "learn_delay"..vnum).
	int GetPlayerBotRecipeLearnDelay(LPCHARACTER ch, DWORD recipeVnum)
	{
		char flag[64];
		snprintf(flag, sizeof(flag), "crafting.learn_delay%u", recipeVnum);
		return ch->GetQuestFlag(flag);
	}

	void SetPlayerBotRecipeLearnDelay(LPCHARACTER ch, DWORD recipeVnum, int value)
	{
		char flag[64];
		snprintf(flag, sizeof(flag), "crafting.learn_delay%u", recipeVnum);
		ch->SetQuestFlag(flag, value);
	}

	// Whether a recipe could be read at all, by anybody: crafting.learn_recipe
	// answers false for a row crafting_data does not know, and keeps the item.
	const TCraftingItem* GetPlayerBotRecipeRow(LPITEM item)
	{
		if (!IsPlayerBotCraftRecipeItem(item) || item->GetValue(0) <= 0)
			return NULL;
		const TCraftingItem* row = CCraftingManager::instance().GetCraftingRecipe(item->GetValue(0));
		return row && row->itemVnum != 0 ? row : NULL;
	}

	// One recipe read per call, the way crafting.learn_recipe reads one: the
	// odds and the ceiling are the item's own (value1, value2), the progress is
	// the quest's flag, so a bot's knowledge is a player's knowledge, and the
	// quest's refusals are this one's - no row, the ceiling, the row's level, a
	// wait still running. A read that gets past them costs ONE recipe whether it
	// succeeds or not (the quest's item.remove(1)); the first build removed the
	// whole stack, ten recipes for one roll.
	//
	// There is no wait between reads: the quest's twenty-one hours are gone for
	// players (the Dockerfile's crafting.lua step, upstream 2.2.39) and a bot
	// reads the same way - the bots' book wait used to stand in for it here,
	// and a wait flag written before is ignored as the quest ignores it. A Hermit's
	// Advice waits: the quest takes it off at any recipe read without using it,
	// and the book pass puts it on for the class book it is about to read.
	bool ReadPlayerBotCraftRecipe(LPCHARACTER ch)
	{
		if (!ch || !IsPlayerBotHerbalismUnlocked(ch))
			return false;
		if (ch->FindAffect(AFFECT_SKILL_BOOK_BONUS))
			return false;
		for (int cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			const TCraftingItem* row = GetPlayerBotRecipeRow(item);
			if (!row)
				continue;
			const DWORD recipeVnum = item->GetValue(0);
			const int chance = item->GetValue(1);
			const int maxRead = item->GetValue(2);
			if (maxRead <= 0)
				continue;
			const int progress = GetPlayerBotCraftProgress(ch, recipeVnum);
			if (progress >= maxRead)
				continue;   // known to the ceiling: the stack is goods now
			if (ch->GetLevel() < row->reqLevel)
				continue;
			const int bonus = ch->GetPoint(POINT_LEARN_CHANCE);
			const int rolled = chance * (100 + bonus) / 100;
			// The quest spends a learning potion's affect on any read.
			CAffect* learnPotion = ch->FindAffect(AFFECT_POTION_GENERAL_USE, POINT_LEARN_CHANCE);
			if (learnPotion)
				ch->RemoveAffect(learnPotion);
			const bool learnt = number(1, 100) <= rolled;
			if (learnt)
			{
				SetPlayerBotCraftProgress(ch, recipeVnum, progress + 1);
				if (GetPlayerBotRecipeLearnDelay(ch, recipeVnum) != 0)
					SetPlayerBotRecipeLearnDelay(ch, recipeVnum, 0);
			}
			const DWORD vnum = item->GetVnum();
			const int left = (int) item->GetCount() - 1;
			if (left > 0)
				item->SetCount(left);
			else
				ITEM_MANAGER::instance().RemoveItem(item, "PLAYERBOT_RECIPE");
			sys_log(0, "PLAYERBOT_HERB: recipe read pid=%u name=%s item=%u recipe=%u progress=%d/%d chance=%d left=%d %s",
					ch->GetPlayerID(), ch->GetName(), vnum, recipeVnum,
					learnt ? progress + 1 : progress, maxRead, rolled, left,
					learnt ? "LEARNT" : "FAILED");
			return true;
		}
		return false;
	}

	bool PlayerBotHoldsCraftRecipe(LPCHARACTER ch)
	{
		for (int cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			if (IsPlayerBotCraftRecipeItem(ch->GetInventoryItem(cell)))
				return true;
		return false;
	}

	// A pass of its own, with its own clock. The first build hung this on the
	// tail of ManagePlayerBotSkillBooks - the branch that runs when no class
	// book is due - and that branch is unreachable for the bots that matter:
	// MordercaBezSerca3 finished the onboarding at 22:28 with the recipe in its
	// bag and 55 skill books beside it, so the book pass always had something
	// better to do and the recipe sat unread for half an hour. A feature wired
	// into somebody else's early return is a feature that never runs.
	//
	// And the second build waited for an onboarding only Baek-Go's visit gave,
	// which only the Zielarz makes - a Conqueror of forty-five under the
	// PERSONA switch. On 24 September m2zip had 1597 recipes in the bags of 822
	// bots and not one bot onboarded ("maja ich pelno w eq a powinny czytac od
	// razu po dropnieciu", Iwakura). A bot holding a recipe is onboarded here,
	// wherever it stands, and then reads one every few seconds until nothing in
	// its bag can teach it more.
	void ManagePlayerBotCraftRecipes(LPCHARACTER ch, DWORD dwNow)
	{
		static std::map<DWORD, DWORD> s_mapPlayerBotRecipeNext;
		if (!ch || !ch->IsItemLoaded() || ch->IsDead() || ch->GetExchange() ||
				ch->GetMyShop())
			return;
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotRecipeNext.find(pid);
		if (it != s_mapPlayerBotRecipeNext.end() && dwNow < it->second)
			return;
		if (!IsPlayerBotHerbalismUnlocked(ch))
		{
			if (!PlayerBotHoldsCraftRecipe(ch) || !EnsurePlayerBotHerbalismStarted(ch))
			{
				s_mapPlayerBotRecipeNext[pid] = dwNow + number(
						PLAYERBOT_HERBALISM_ONBOARD_RETRY_MIN_MS, PLAYERBOT_HERBALISM_ONBOARD_RETRY_MAX_MS);
				return;
			}
		}
		const bool read = ReadPlayerBotCraftRecipe(ch);
		s_mapPlayerBotRecipeNext[pid] = dwNow + (read ?
				number(PLAYERBOT_HERBALISM_RECIPE_READ_GAP_MIN_MS, PLAYERBOT_HERBALISM_RECIPE_READ_GAP_MAX_MS) :
				number(PLAYERBOT_HERBALISM_RECIPE_IDLE_MIN_MS, PLAYERBOT_HERBALISM_RECIPE_IDLE_MAX_MS));
	}

	// The bottles are Baek-Go's shop, which is a quest window like the board.
	// Bought the way EnsurePlayerBotFishingPass buys the fishing pass: the item
	// is created for the price the shop asks, so nothing is had for free.
	bool BuyPlayerBotCraftBottles(LPCHARACTER ch, DWORD vnum, int needed)
	{
		if (!ch || needed <= 0)
			return false;
		long long price = 0;
		if (vnum == PLAYERBOT_HERBALISM_BOTTLE_M)
			price = PLAYERBOT_HERBALISM_BOTTLE_M_PRICE;
		else if (vnum == PLAYERBOT_HERBALISM_BOTTLE_S)
			price = PLAYERBOT_HERBALISM_BOTTLE_S_PRICE;
		else if (vnum == PLAYERBOT_HERBALISM_BOTTLE_D)
			price = PLAYERBOT_HERBALISM_BOTTLE_D_PRICE;
		else
			return false;
		// The shop sells them ten at a time and so does this: a pack at a time
		// until the row is covered, each one paid for.
		int packs = (needed + PLAYERBOT_HERBALISM_BOTTLE_PACK - 1) /
				PLAYERBOT_HERBALISM_BOTTLE_PACK;
		if (packs <= 0)
			return false;
		const long long total = price * packs;
		if ((long long) ch->GetGold() < total + GetPlayerBotHerbalismGoldReserve(ch))   // MT2009_PLUS_BOT_HERBALIST_FIX_V1
			return false;
		if (CountPlayerBotFreeInventoryCells(ch) < 1)
			return false;
		// PlayerBotChangeGold, not PointChange: mt2009 refuses POINT_GOLD there
		// ("unknown point change type 11") and the bottles went for nothing.
		PlayerBotChangeGold(ch, -total);
		ch->AutoGiveItem(vnum, packs * PLAYERBOT_HERBALISM_BOTTLE_PACK);
		sys_log(0, "PLAYERBOT_HERB: bottles bought pid=%u name=%s vnum=%u packs=%d gold=%lld",
				ch->GetPlayerID(), ch->GetName(), vnum, packs, total);
		return true;
	}

	bool IsPlayerBotCraftBottle(DWORD vnum)
	{
		return vnum == PLAYERBOT_HERBALISM_BOTTLE_M ||
				vnum == PLAYERBOT_HERBALISM_BOTTLE_S ||
				vnum == PLAYERBOT_HERBALISM_BOTTLE_D;
	}

	// Everything is_crafting_item_available asks, minus the window: the row is
	// on this board, the bot is old enough for it and its knowledge reaches the
	// row's threshold.
	bool PlayerBotKnowsCraftRow(LPCHARACTER ch, const TCraftingItem* row)
	{
		if (!ch || !row)
			return false;
		if (ch->GetLevel() < row->reqLevel)
			return false;
		if (row->reqProgress == 0)
			return true;
		return (DWORD) GetPlayerBotCraftProgress(ch, row->recipeVnum) >= row->reqProgress;
	}

	// Whether the bag covers the row, buying the bottles it is short of. The
	// bottles are the one material a bot can always get, which is why they are
	// the only thing bought here; every herb comes from the world.
	bool PreparePlayerBotCraftMaterials(LPCHARACTER ch, const TCraftingItem* row, bool buy)
	{
		if (!ch || !row)
			return false;
		for (int i = 0; i < CRAFTING_MATERIAL_MAX_NUM; ++i)
		{
			const DWORD vnum = row->materials[i].vnum;
			const int need = (int) row->materials[i].count;
			if (vnum == 0 || need <= 0)
				continue;
			const int have = (int) ch->CountSpecifyItem(vnum);
			if (have >= need)
				continue;
			if (!IsPlayerBotCraftBottle(vnum))
				return false;
			// A bottle is the one material that is always available: Baek-Go
			// sells it at the same counter. When only asked whether the row is
			// possible (buy == false), an empty bottle shelf is not a refusal -
			// otherwise no bot would ever set out for its first craft, because
			// the bottles can only be bought once it has arrived.
			if (!buy)
				continue;
			if (!BuyPlayerBotCraftBottles(ch, vnum, need - have))
				return false;
			if ((int) ch->CountSpecifyItem(vnum) < need)
				return false;
		}
		return true;
	}

	// What a bot makes when it is at the board. The highest row it can afford
	// comes first, because the chain feeds itself - a Water eats ten Juices -
	// so working the top of what a bot knows is what turns a heap of herbs into
	// something worth carrying, and it is also what Iwakura asked for: keep the
	// lower tier for the stronger one rather than drinking it.
	const TCraftingItem* ChoosePlayerBotCraftRow(LPCHARACTER ch)
	{
		if (!ch)
			return NULL;
		const TCraftingItem* best = NULL;
		// The reserve once, not once a row: a gatherer's is asked of its bag.
		const long long reserve = GetPlayerBotHerbalismGoldReserve(ch);   // MT2009_PLUS_BOT_HERBALIST_ACTIVITY_V1
		for (size_t i = 0; i < PLAYERBOT_HERBALISM_ROW_COUNT; ++i)
		{
			const TCraftingItem* row =
					CCraftingManager::instance().GetCraftingRecipe(PLAYERBOT_HERBALISM_ROWS[i]);
			if (!row || row->itemVnum == 0)
				continue;
			if (!PlayerBotKnowsCraftRow(ch, row))
				continue;
			if ((long long) ch->GetGold() < (long long) row->price + reserve)   // MT2009_PLUS_BOT_HERBALIST_FIX_V1
				continue;
			if (!PreparePlayerBotCraftMaterials(ch, row, false))
				continue;
			if (!best || row->reqProgress > best->reqProgress ||
					(row->reqProgress == best->reqProgress && row->price > best->price))
				best = row;
		}
		return best;
	}

	// Is there a row this bot could make right now, if only it were standing at
	// the board? The travel asks this before it spends a trip to a first
	// village, so it is the full list - knowledge, herbs, purse - and not a
	// hope. The bottles are left out on purpose: they are bought at the counter
	// itself, so a row short of only those is still a reason to go.
	// Iwakura's Zielarz: under the PERSONA switch Baek-Go's board is a
	// Conqueror's errand, from level forty-five ("Reakcja Zdobywcy ... odpala
	// mikro-faze Alchemika"). Every bot still picks the herbs up on the way.
	bool IsPlayerBotZielarz(LPCHARACTER ch)
	{
		if (!IsPlayerBotPersonaEnabled())
			return true;
		if (!ch)
			return false;
		// MT2009_PLUS_BOT_HERBALIST_ACTIVITY_V1: a gatherer brews what it
		// picked, at any level from Baek-Go's fifteen.
		if (IsPlayerBotHerbGatherer(ch))
			return true;
		// MT2009_PLUS_BOTLIFE_V1: over 100 the HERB slider ("Zielarstwo")
		// brings a share of the other bots from Baek-Go's own level fifteen
		// too - a fixed share by pid, every one of them at 250.
		const int herb = GetPlayerBotWeight(PLAYERBOT_WEIGHT_HERB);
		if (herb > PLAYERBOT_WEIGHT_NEUTRAL && ch->GetLevel() >= PLAYERBOT_HERBALISM_MIN_LEVEL &&
				(int)(PlayerBotNavHash(ch->GetPlayerID() ^ 0x5a49454cU) % 100U) <
					(herb - PLAYERBOT_WEIGHT_NEUTRAL) * 100 / (PLAYERBOT_WEIGHT_LIMIT - PLAYERBOT_WEIGHT_NEUTRAL))
			return true;
		if ((int)ch->GetLevel() < PLAYERBOT_ZIELARZ_MIN_LEVEL)
			return false;
		TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		return it != s_mapPlayerBotAIStates.end() && it->second.persona.bRestored &&
				it->second.persona.bAdvanced;
	}

	// MT2009_PLUS_BOTLIFE_V1: under 100 the HERB slider closes the board to a
	// share of the herbalists, half an hour at a time (the gate the REFINE and
	// SKILL sliders close theirs with). Asked where a visit is decided, never
	// by the rule that keeps a herbalist's herbs, which would otherwise take
	// them in and out of the bag every half hour.
	bool IsPlayerBotHerbBoardOpen(LPCHARACTER ch, DWORD dwNow)
	{
		return ch && IsPlayerBotWeightGateOpen(ch->GetPlayerID(), PLAYERBOT_WEIGHT_HERB,
				PLAYERBOT_WEIGHT_GATE_SALT_HERB, dwNow);
	}

	// And the wait between two visits: shorter as the slider goes up.
	DWORD DrawPlayerBotHerbalistVisitGap()
	{
		return ScalePlayerBotWaitByWeight((DWORD)number((int)PLAYERBOT_HERBALISM_VISIT_MIN_MS,
				(int)PLAYERBOT_HERBALISM_VISIT_MAX_MS), PLAYERBOT_WEIGHT_HERB);
	}

	bool PlayerBotHasReadyCraftRow(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded() || !IsPlayerBotHerbalismUnlocked(ch))
			return false;
		if (ch->GetLevel() < PLAYERBOT_HERBALISM_MIN_LEVEL || !IsPlayerBotZielarz(ch) ||
				!IsPlayerBotHerbBoardOpen(ch, get_dword_time()))
			return false;
		if (CountPlayerBotFreeInventoryCells(ch) < PLAYERBOT_HERBALISM_FREE_CELLS)
			return false;
		return ChoosePlayerBotCraftRow(ch) != NULL;
	}

	// The craft itself, in crafting.create's order: materials out, gold out,
	// one roll per unit asked for, the product in. One unit at a time here -
	// the window lets a player ask for several and a bot has no reason to.
	bool CraftPlayerBotPotion(LPCHARACTER ch, const TCraftingItem* row)
	{
		if (!ch || !row || row->itemVnum == 0)
			return false;
		if (CountPlayerBotFreeInventoryCells(ch) < 1)
			return false;
		if (!PreparePlayerBotCraftMaterials(ch, row, true))
			return false;
		for (int i = 0; i < CRAFTING_MATERIAL_MAX_NUM; ++i)
		{
			if (row->materials[i].vnum == 0 || row->materials[i].count <= 0)
				continue;
			ch->RemoveSpecifyItem(row->materials[i].vnum, row->materials[i].count);
		}
		if (row->price > 0)
			PlayerBotChangeGold(ch, -(long long) row->price);
		const bool made = number(1, 100) <= row->chance;
		if (made)
			ch->AutoGiveItem(row->itemVnum, row->count);
		sys_log(0, "PLAYERBOT_HERB: craft pid=%u name=%s row=%u item=%u count=%d chance=%d price=%lld %s",
				ch->GetPlayerID(), ch->GetName(), row->vnum, row->itemVnum,
				made ? (int) row->count : 0, row->chance, (long long) row->price,
				made ? "OK" : "FAILED");
		return true;
	}

	// MT2009_PLUS_BOT_HERBALIST_ACTIVITY_V1: how many of a potion a bot keeps
	// for itself - its reserve - before the rest goes on a counter ("boty
	// zostawiaja sobie to, czego potrzebuja, a reszte wystawiaja", the owner,
	// 2 October). PLAYERBOT_HERBALISM_POTION_KEEP of every brew for the fights
	// worth a buff; of a green or purple potion the belt the bot buys up to at
	// the General Store (GetPlayerBotPotionSupplyLimit), or it listed the
	// potions it walked to the merchant for an hour later; and of a potion the
	// next row it knows is brewed from - a Water eats ten Juices - that row's
	// count over the keep, or the counter sold the chain out from under the
	// board.
	int GetPlayerBotCraftedPotionKeep(LPCHARACTER ch, DWORD vnum)
	{
		int keep = PLAYERBOT_HERBALISM_POTION_KEEP;
		const EPlayerBotPotionSupply supply = GetPlayerBotPotionSupply(vnum);
		if (supply != PLAYERBOT_POTION_SUPPLY_NONE)
			keep = std::max(keep, (int)GetPlayerBotPotionSupplyLimit(ch, supply));
		if (!ch || !IsPlayerBotHerbalismUnlocked(ch))
			return keep;
		for (size_t i = 0; i < PLAYERBOT_HERBALISM_ROW_COUNT; ++i)
		{
			const TCraftingItem* row =
					CCraftingManager::instance().GetCraftingRecipe(PLAYERBOT_HERBALISM_ROWS[i]);
			if (!row || row->itemVnum == 0 || !PlayerBotKnowsCraftRow(ch, row))
				continue;
			for (int m = 0; m < CRAFTING_MATERIAL_MAX_NUM; ++m)
				if (row->materials[m].vnum == vnum && row->materials[m].count > 0)
					keep = std::max(keep, PLAYERBOT_HERBALISM_POTION_KEEP + (int)row->materials[m].count);
		}
		return keep;
	}

	// The rest is what a counter can carry, because until now no player could
	// buy one anywhere.
	bool IsPlayerBotSurplusPotion(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !IsPlayerBotCraftedPotion(item))
			return false;
		const int spare = (int) ch->CountSpecifyItem(item->GetVnum()) -
				GetPlayerBotCraftedPotionKeep(ch, item->GetVnum());   // MT2009_PLUS_BOT_HERBALIST_ACTIVITY_V1
		// A packed potion is goods once the spare fills the smallest pack.
		if (IsPlayerBotPackedPotion(item))
			return GetPlayerBotPotionPackUnits(spare) > 0;
		return spare > 0;
	}

	// Drinking. A crafted potion is ten minutes of something a bot cannot get
	// any other way - 60 attack value, 12% critical, 90 defence - and the bag
	// holds a handful, so it is spent where ten minutes are worth spending: a
	// boss, a Metin stone, a Demon Tower floor. Never on the ordinary monster a
	// bot kills every four seconds, which is what would drain a bag in an hour.
	//
	// The engine counts the affects per group (potion_system.lua: 5 boosts, 3
	// offensive, 2 defensive) and the quest refuses a sixth, so this asks
	// whether the group's affect is already running rather than counting: one
	// of each kind up is what a bot can reliably keep, and a refused use would
	// be a wasted potion.
	//
	// The target is passed in rather than read from GetVictim(): the tick knows
	// what the bot is fighting (`curTarget`) long before the engine's victim is
	// set, and the first build asked the engine - 87 Metin lines and not one
	// potion in the two minutes after it went live.
	// A fight with a player is one too, when the Anti-PK protocol is the one
	// asking (playerbot_anti_pk.h): "jesli posiada w ekwipunku Rosy/Wody ...
	// odpala je, by zwiekszyc swoje szanse".
	bool DrinkPlayerBotCraftedPotion(LPCHARACTER ch, LPCHARACTER target, DWORD dwNow, bool pvp = false)
	{
		static std::map<DWORD, DWORD> s_mapPlayerBotPotionNext;
		if (!ch || !ch->IsItemLoaded() || ch->IsDead())
			return false;
		if (!target || target->IsDead())
			return false;
		const bool worthIt = target->IsStone() ||
				(target->IsMonster() && target->GetMobRank() >= MOB_RANK_BOSS) ||
				(pvp && target->IsPC());
		if (!worthIt)
			return false;
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotPotionNext.find(pid);
		if (it != s_mapPlayerBotPotionNext.end() && dwNow < it->second)
			return false;
		s_mapPlayerBotPotionNext[pid] = dwNow + PLAYERBOT_HERBALISM_DRINK_RETRY_MS;

		for (int cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!IsPlayerBotCraftedPotion(item))
				continue;
			if (ch->GetLevel() < item->GetLevelLimit())
				continue;
			// value1 is the group; the affect the quest adds for it is
			// AFFECT_POTION_START + group. Only the three that are a fight's
			// worth of buff: 1 boost, 2 offensive, 3 defensive. Group 0 is the
			// general-use shelf and group 4 is FOOD - the grilled fish an angler
			// brings home, which the first run drank at a Metin stone
			// (xTurbina, 22:23, vnum 27866) because the type is shared. Food is
			// for a bot that is hurt, not for a stone.
			const int group = item->GetValue(1);
			if (group < 1 || group > 3)
				continue;
			if (ch->FindAffect(AFFECT_POTION_START + group))
				continue;   // that kind is already running
			const DWORD vnum = item->GetVnum();
			if (!ch->UseItem(TItemPos(INVENTORY, cell)))
				continue;
			sys_log(0, "PLAYERBOT_HERB: potion drunk pid=%u name=%s vnum=%u group=%d against=%s",
					pid, ch->GetName(), vnum, group,
					target->IsStone() ? "stone" : (target->IsPC() ? "player" : "boss"));
			return true;
		}
		return false;
	}

	// A recipe is goods only once the bot can learn nothing more from it: the
	// ceiling is the item's own value2, and up to it every copy is knowledge
	// the bot still wants. Listing one it could read would be the bookshelf
	// mistake again - selling the thing that makes the trade possible.
	bool IsPlayerBotSurplusRecipe(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !IsPlayerBotCraftRecipeItem(item))
			return false;
		const DWORD recipeVnum = item->GetValue(0);
		const int maxRead = item->GetValue(2);
		// A recipe nothing can be learnt from: no reads, or a row the board
		// does not have (Mikstura Nietykalnosci, 50931, names row 70).
		if (recipeVnum == 0 || maxRead <= 0 || !GetPlayerBotRecipeRow(item))
			return true;
		return GetPlayerBotCraftProgress(ch, recipeVnum) >= maxRead;
	}

	// ---------------------------------------------------------------------
	// MT2009_PLUS_BOT_HERBALIST_FIX_V1: picking the herbs.
	//
	// The first build left this out on purpose - "this world spawns four of
	// the sixteen" - and the world has changed under it: stone.txt now puts a
	// herb group on every map from the first villages up (map1_herbs ..
	// map3_herbs, group_group.txt), each group one bush of the sixteen the
	// quest answers a click on. So the owner's report of 2 October held: the
	// herbalists carried no knife and never picked anything, and the only
	// herbs at the board were the ones that happened to drop.
	//
	// The pick is herbalism.lua's own, done server-side the way the board is
	// (a bot has no client to click with): the knife 29201-29210 in the weapon
	// hand, a bush of the bot's level or under within two metres, three
	// seconds, then 30% plus the knife's value0 plus the bot's failure bonus
	// (4 a miss, up to 20, the quest's flag herbalism.fail_bonus); a success
	// gives two or three of the bush's drop item and counts the bush's "herb"
	// flag up, and the bush goes at the quest's odds (0, 15, 40, 60, 80, 100%
	// on its first to sixth pick). The knife's points go up as the quest's do.
	// ---------------------------------------------------------------------
	const DWORD PLAYERBOT_HERB_BUSH_RACES[] = {
		20602, 20606, 20609, 20610, 20614, 20617, 20619, 20620,
		20623, 20624, 20628, 20629, 20631, 20632, 20641, 20644
	};
	const size_t PLAYERBOT_HERB_BUSH_RACE_COUNT =
			sizeof(PLAYERBOT_HERB_BUSH_RACES) / sizeof(PLAYERBOT_HERB_BUSH_RACES[0]);

	bool IsPlayerBotHerbBushRace(DWORD race)
	{
		for (size_t i = 0; i < PLAYERBOT_HERB_BUSH_RACE_COUNT; ++i)
			if (PLAYERBOT_HERB_BUSH_RACES[i] == race)
				return true;
		return false;
	}

	// The session's clocks, by pid (the mining pass's reason: no new fields in
	// TPlayerBotAIState and its initialiser list).
	std::map<DWORD, DWORD> s_mapPlayerBotHerbUntil;    // session end; the Zielarz until then
	std::map<DWORD, DWORD> s_mapPlayerBotHerbStarted;  // session start, for the log's minutes
	std::map<DWORD, DWORD> s_mapPlayerBotHerbNext;     // when to consider a session again
	std::map<DWORD, DWORD> s_mapPlayerBotHerbBush;     // the bush this bot is on
	std::map<DWORD, DWORD> s_mapPlayerBotHerbBushSince;// since when (a bush out of reach is dropped)
	std::map<DWORD, DWORD> s_mapPlayerBotHerbPickAt;   // when the running pick resolves
	std::map<DWORD, DWORD> s_mapPlayerBotHerbResume;   // after a blow, the bushes again from
	std::map<DWORD, int> s_mapPlayerBotHerbHP;
	std::map<DWORD, DWORD> s_mapPlayerBotHerbSkipBush; // one bush it could not reach, and until when
	std::map<DWORD, DWORD> s_mapPlayerBotHerbSkipUntil;
	std::map<DWORD, int> s_mapPlayerBotHerbEquipFails;  // knife equips refused in a row

	bool IsPlayerBotHerbSessionNow(DWORD pid, DWORD dwNow)
	{
		std::map<DWORD, DWORD>::const_iterator it = s_mapPlayerBotHerbUntil.find(pid);
		return it != s_mapPlayerBotHerbUntil.end() && (int)(it->second - dwNow) > 0;
	}

	bool IsPlayerBotHoldingHerbKnife(LPCHARACTER ch)
	{
		LPITEM knife = ch ? ch->GetWear(WEAR_WEAPON) : NULL;
		return knife && knife->GetType() == ITEM_HERB_KNIFE;
	}

	// The gear pass keeps its hands off the weapon slot while this is true.
	bool IsPlayerBotHerbPickingNow(LPCHARACTER ch, DWORD dwNow)
	{
		return ch && IsPlayerBotHoldingHerbKnife(ch) && IsPlayerBotHerbSessionNow(ch->GetPlayerID(), dwNow);
	}

	int CountPlayerBotHerbKnives(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		int count = IsPlayerBotHoldingHerbKnife(ch) ? 1 : 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetType() == ITEM_HERB_KNIFE)
				++count;
		}
		return count;
	}

	// Baek-Go's shop sells it (his special shop, a quest window like the
	// board); bought the way the pickaxe and the bottles are, for the item's
	// own price, and never a second one.
	bool EnsurePlayerBotHerbKnife(LPCHARACTER ch, const char* where)
	{
		if (!ch)
			return false;
		if (CountPlayerBotHerbKnives(ch) > 0)
			return true;
		if ((long long)ch->GetGold() < PLAYERBOT_HERB_KNIFE_PRICE + (long long)GetPlayerBotReservedGold(ch))
			return false;
		if (ch->GetEmptyInventory(1) < 0)
			return false;
		LPITEM knife = ch->AutoGiveItem(PLAYERBOT_HERB_KNIFE_VNUM, 1, -1, false);
		if (!knife)
			return false;
		PlayerBotChangeGold(ch, -PLAYERBOT_HERB_KNIFE_PRICE);
		sys_log(0, "PLAYERBOT_HERB: knife bought pid=%u name=%s vnum=%u price=%lld gold=%lld at=%s",
				ch->GetPlayerID(), ch->GetName(), PLAYERBOT_HERB_KNIFE_VNUM, PLAYERBOT_HERB_KNIFE_PRICE,
				(long long)ch->GetGold(), where ? where : "-");
		return true;
	}

	bool EquipPlayerBotHerbKnife(LPCHARACTER ch)
	{
		if (!ch || IsPlayerBotGearFrozen(ch))
			return false;
		if (IsPlayerBotHoldingHerbKnife(ch))
			return true;
		LPITEM best = NULL;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetType() == ITEM_HERB_KNIFE &&
					(!best || item->GetVnum() > best->GetVnum()))
				best = item;
		}
		if (!best)
			return false;
		LPITEM worn = ch->GetWear(WEAR_WEAPON);
		if (worn && (ch->GetEmptyInventory(worn->GetSize()) < 0 || !ch->UnequipItem(worn) ||
				worn->IsEquipped()))
			return false;
		return PlayerBotEquipItem(ch, best) && IsPlayerBotHoldingHerbKnife(ch);
	}

	// The knife out of the hand and the weapon back in it - never a fight
	// with a knife (it deals nothing: Item_GetDamage returns at once).
	void StowPlayerBotHerbKnife(LPCHARACTER ch)
	{
		LPITEM worn = ch ? ch->GetWear(WEAR_WEAPON) : NULL;
		if (!worn || worn->GetType() != ITEM_HERB_KNIFE || IsPlayerBotGearFrozen(ch))
			return;
		if (ch->GetEmptyInventory(worn->GetSize()) < 0 || !ch->UnequipItem(worn))
			return;
		EquipFirstAvailablePlayerBotWeapon(ch);
	}

	void EndPlayerBotHerbSession(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow,
			const char* szReason, DWORD dwRest = 0)
	{
		if (!ch)
			return;
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, DWORD>::iterator started = s_mapPlayerBotHerbStarted.find(pid);
		const int minutes = started != s_mapPlayerBotHerbStarted.end() ? (int)((dwNow - started->second) / 60000U) : -1;
		if (started != s_mapPlayerBotHerbStarted.end())
			s_mapPlayerBotHerbStarted.erase(started);
		s_mapPlayerBotHerbUntil.erase(pid);
		s_mapPlayerBotHerbBush.erase(pid);
		s_mapPlayerBotHerbBushSince.erase(pid);
		s_mapPlayerBotHerbPickAt.erase(pid);
		s_mapPlayerBotHerbResume.erase(pid);
		s_mapPlayerBotHerbHP.erase(pid);
		StowPlayerBotHerbKnife(ch);
		s_mapPlayerBotHerbNext[pid] = dwNow + (dwRest != 0 ? dwRest : ScalePlayerBotWaitByWeight(
				(DWORD)number((int)PLAYERBOT_HERB_REST_MIN_MS, (int)PLAYERBOT_HERB_REST_MAX_MS),
				PLAYERBOT_WEIGHT_HERB));
		ClearPlayerBotRoute(state, true);
		// MT2009_PLUS_BOT_HERBALIST_ACTIVITY_V1: what it picked goes to the
		// board when it next stands in Baek-Go's village, not a visit gap later.
		if ((int)(state.dwNextHerbalistCheckTime - dwNow) > 0)
			state.dwNextHerbalistCheckTime = dwNow;
		sys_log(0, "PLAYERBOT_HERB: session end pid=%u name=%s reason=%s minutes=%d level=%d activity=1",
				pid, ch->GetName(), szReason ? szReason : "done", minutes, (int)ch->GetLevel());
	}

	// Is a bush on this bot already? Another herbalist's bush is left to it.
	bool IsPlayerBotHerbBushTaken(DWORD pid, DWORD vid)
	{
		for (std::map<DWORD, DWORD>::const_iterator it = s_mapPlayerBotHerbBush.begin();
				it != s_mapPlayerBotHerbBush.end(); ++it)
			if (it->first != pid && it->second == vid)
				return true;
		return false;
	}

	// The nearest bush on the bot's map it may pick (its level reaches the
	// bush's, as the quest asks) and nobody else is on.
	LPCHARACTER FindPlayerBotHerbBush(LPCHARACTER ch, long* pDistance)
	{
		if (!ch)
			return NULL;
		const DWORD pid = ch->GetPlayerID();
		const DWORD dwNow = get_dword_time();
		std::map<DWORD, DWORD>::const_iterator skip = s_mapPlayerBotHerbSkipBush.find(pid);
		std::map<DWORD, DWORD>::const_iterator skipUntil = s_mapPlayerBotHerbSkipUntil.find(pid);
		const DWORD skipVid = (skip != s_mapPlayerBotHerbSkipBush.end() && skipUntil != s_mapPlayerBotHerbSkipUntil.end() &&
				(int)(skipUntil->second - dwNow) > 0) ? skip->second : 0;
		LPCHARACTER best = NULL;
		long bestDistance = 0;
		for (size_t r = 0; r < PLAYERBOT_HERB_BUSH_RACE_COUNT; ++r)
		{
			CharacterVectorInteractor bushes;
			if (!CHARACTER_MANAGER::instance().GetCharactersByRaceNum(PLAYERBOT_HERB_BUSH_RACES[r], bushes))
				continue;
			for (CharacterVectorInteractor::iterator it = bushes.begin(); it != bushes.end(); ++it)
			{
				LPCHARACTER bush = *it;
				if (!bush || bush->IsDead() || bush->GetMapIndex() != ch->GetMapIndex() ||
						!bush->GetSectree())
					continue;
				if ((int)ch->GetLevel() < (int)bush->GetMobTable().bLevel || bush->GetMobDropItemVnum() == 0)
					continue;
				const DWORD vid = (DWORD)bush->GetVID();
				if (vid == skipVid || IsPlayerBotHerbBushTaken(pid, vid))
					continue;
				const long distance = DISTANCE_APPROX(ch->GetX() - bush->GetX(), ch->GetY() - bush->GetY());
				if (distance > PLAYERBOT_HERB_SEARCH_RANGE)
					continue;
				if (!best || distance < bestDistance)
				{
					best = bush;
					bestDistance = distance;
				}
			}
		}
		if (best && pDistance)
			*pDistance = bestDistance;
		return best;
	}

	// The three seconds are over: herb_pick.timer, server-side.
	void ResolvePlayerBotHerbPick(LPCHARACTER ch, LPCHARACTER bush)
	{
		LPITEM knife = ch ? ch->GetWear(WEAR_WEAPON) : NULL;
		if (!ch || !bush || !knife || knife->GetType() != ITEM_HERB_KNIFE)
			return;
		const int failBonus = std::max(0, ch->GetQuestFlag("herbalism.fail_bonus"));
		int chance = PLAYERBOT_HERB_PICK_BASE_CHANCE + (int)knife->GetValue(0) + failBonus;
		const bool herbalistBonus = ch->FindAffect(AFFECT_HERBALIST_BONUS) != NULL;
		if (herbalistBonus)
			chance += 2;
		const bool success = number(1, 100) <= chance;
		// herbalism.upgrade_knife: a point on a success, half the time on a miss.
		if (success || number(1, 2) == 1)
		{
			const long points = knife->GetSocket(0);
			const long maxPoints = knife->GetValue(2);
			if (points < maxPoints)
				knife->SetSocket(0, points + 1);
		}
		const DWORD herb = bush->GetMobDropItemVnum();
		const DWORD race = bush->GetRaceNum();
		int count = 0;
		bool gone = false;
		if (success && herb != 0)
		{
			ch->SetQuestFlag("herbalism.fail_bonus", 0);
			count = number(2, 3);
			if (herbalistBonus && number(1, 5) == 1)
				count += 2;
			ch->AutoGiveItem(herb, count, -1, false);
			ch->AddPlayerStat(PLAYER_STATS_HERBALISM_FLAG, count);
			const long long progress = bush->GetSpecialFlag("herb") + 1;
			bush->SetSpecialFlag("herb", progress, true, false);
			static const int purge[] = { 0, 15, 40, 60, 80, 100 };
			const int n = (int)(sizeof(purge) / sizeof(purge[0]));
			gone = progress >= n || (progress >= 1 && number(1, 100) <= purge[progress - 1]);
		}
		else
			ch->SetQuestFlag("herbalism.fail_bonus", std::min(failBonus + PLAYERBOT_HERB_FAIL_BONUS_STEP,
					PLAYERBOT_HERB_FAIL_BONUS_MAX));
		sys_log(0, "PLAYERBOT_HERB: pick pid=%u name=%s bush=%u herb=%u count=%d chance=%d knife=%u %s%s",
				ch->GetPlayerID(), ch->GetName(), race, herb, count, chance, knife->GetVnum(),
				success ? "OK" : "FAILED", gone ? " bush_gone" : "");
		if (gone)
		{
			s_mapPlayerBotHerbBush.erase(ch->GetPlayerID());
			M2_DESTROY_CHARACTER(bush);
		}
	}

	// Would Baek-Go's visit pass take this bot now? Asked so the bushes let
	// go of a herbalist that has a row to brew and stands in his village.
	bool IsPlayerBotHerbalistVisitDue(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow)
	{
		// The answer walks the board's rows and the bag: once in ten seconds.
		static std::map<DWORD, DWORD> s_mapPlayerBotHerbVisitAsk;
		playerbot_empire_rules::TPoint herbalistPos;
		if (!ch || dwNow < state.dwNextHerbalistCheckTime ||
				!playerbot_empire_rules::GetHerbalist(ch->GetMapIndex(), herbalistPos) ||
				!IsPlayerBotHerbBoardOpen(ch, dwNow))
			return false;
		std::map<DWORD, DWORD>::iterator ask = s_mapPlayerBotHerbVisitAsk.find(ch->GetPlayerID());
		if (ask != s_mapPlayerBotHerbVisitAsk.end() && (int)(dwNow - ask->second) < 0)
			return false;
		s_mapPlayerBotHerbVisitAsk[ch->GetPlayerID()] = dwNow + 10000;
		if (CountPlayerBotFreeInventoryCells(ch) < PLAYERBOT_HERBALISM_FREE_CELLS)
			return false;
		if (!IsPlayerBotHerbalismUnlocked(ch))
			return (int)ch->CountSpecifyItem(PLAYERBOT_HERBALISM_ONBOARD_FLOWER) >= PLAYERBOT_HERBALISM_ONBOARD_COUNT;
		return ChoosePlayerBotCraftRow(ch) != NULL;
	}

	// MT2009_PLUS_BOT_HERBALIST_ACTIVITY_V1: whether this bot takes the bushes
	// up now. The anglers' and the miners' scheduler, not a trade: from the
	// knife's own level (fifteen; asked of the item, as the rod's thirty is),
	// never a dropper, a companion or a shouter, never on a horse trial or
	// answering a world event (IsPlayerBotAngler's reasons), never in a party
	// (the Rybak's: "jesli bot jest w PT nie powinien lowic"), and then a roll
	// by pid for every half-hour window - spread by pid so the bots do not all
	// turn at once - against PLAYERBOT_HERB_ACTIVITY_PERCENT, a collector's
	// larger share and a little more for a bot that owns a knife already, all
	// of it stretched or shrunk by the HERB slider (PlayerBotWeightedRoll: 0
	// is nobody, 250 two and a half times the share). The rest after a
	// session and the slider's half-hour gate (IsPlayerBotHerbBoardOpen) are
	// the caller's, as the veins' are.
	bool IsPlayerBotHerbalistNow(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->GetLevel() < PLAYERBOT_HERBALISM_MIN_LEVEL || ch->GetParty())
			return false;
		TItemTable* knife = ITEM_MANAGER::instance().GetTable(PLAYERBOT_HERB_KNIFE_VNUM);
		if (!knife || GetPlayerBotProtoLevelLimit(knife) > (int)ch->GetLevel())
			return false;
		const DWORD pid = ch->GetPlayerID();
		if (IsPlayerBotDropper(state.bPersonality) || IsPlayerBotSidekickPID(pid) || IsPlayerBotShouterPID(pid))
			return false;
		if (IsPlayerBotOnBattleHorseTrial(ch) || IsPlayerBotOnMilitaryHorseTrial(ch) || state.bWorldEventKind != 0)
			return false;
		const DWORD window = (dwNow + (pid * 7919U) % PLAYERBOT_HERB_ACTIVITY_WINDOW_MS) /
				PLAYERBOT_HERB_ACTIVITY_WINDOW_MS;
		const DWORD roll = PlayerBotNavHash(pid ^ 0x48524254U ^ (window * 0x9E3779B1U)) % 100U;
		int chance = state.bPersonality == BOT_PERSONALITY_CAREFUL_COLLECTOR
				? PLAYERBOT_HERB_ACTIVITY_COLLECTOR_PERCENT : PLAYERBOT_HERB_ACTIVITY_PERCENT;
		if (CountPlayerBotHerbKnives(ch) > 0)
			chance += PLAYERBOT_HERB_ACTIVITY_KNIFE_BONUS;
		return PlayerBotWeightedRoll(roll, chance, PLAYERBOT_WEIGHT_HERB);
	}

	// The session. It owns the tick the way the vein's does - the knife sits
	// in the weapon hand - and lets go of it for a fight (a blow, then the
	// bushes again PLAYERBOT_HERB_RESUME_MS later), for Baek-Go when a row is
	// ready, and for everything the bot is actually doing; the session itself,
	// and with it the Zielarz, runs on until its clock is out.
	bool ManagePlayerBotHerbGathering(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->IsDead() || !ch->IsItemLoaded())
			return false;
		const DWORD pid = ch->GetPlayerID();
		const bool inSession = IsPlayerBotHerbSessionNow(pid, dwNow);
		if (!inSession && s_mapPlayerBotHerbUntil.find(pid) != s_mapPlayerBotHerbUntil.end())
		{
			EndPlayerBotHerbSession(ch, state, dwNow, "session_over");
			return false;
		}

		// Anything the bot is actually doing outranks the bushes; a session
		// under way waits it out with the knife put away.
		const bool busy = state.bVisitingShop || state.bVisitingBiologist || state.bVisitingStable ||
				state.bVisitingHerbalist || state.bVisitingAlchemist || state.bVisitingUriel ||
				state.bVisitingDsAlchemist || state.bSaddlebagErrand != 0 || state.bMarketTrip ||
				state.bRecoveringAfterDeath || state.bTacticalRetreat || state.bMultiPullActive ||
				state.bFishingSession || state.bWorldEventKind != 0 || ch->GetMyShop() != NULL ||
				IsPlayerBotMiningNow(pid, dwNow) ||
				(ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty()));
		if (busy)
		{
			if (inSession)
				StowPlayerBotHerbKnife(ch);
			return false;
		}

		if (!inSession)
		{
			std::map<DWORD, DWORD>::const_iterator next = s_mapPlayerBotHerbNext.find(pid);
			if (next != s_mapPlayerBotHerbNext.end() && (int)(dwNow - next->second) < 0)
				return false;
			s_mapPlayerBotHerbNext[pid] = dwNow + PLAYERBOT_HERB_RETRY_MS;
			// MT2009_PLUS_BOT_HERBALIST_ACTIVITY_V1: an activity's roll, not a trade.
			if (!IsPlayerBotHerbalistNow(ch, state, dwNow) || !IsPlayerBotHerbBoardOpen(ch, dwNow))
				return false;
			// Never walk off mid-fight.
			LPCHARACTER victim = state.dwTargetVID != 0
					? CHARACTER_MANAGER::instance().Find(state.dwTargetVID) : NULL;
			if (victim && !victim->IsDead())
				return false;
			if (CountPlayerBotFreeInventoryCells(ch) < PLAYERBOT_HERBALISM_FREE_CELLS)
				return false;
			long distance = 0;
			LPCHARACTER bush = FindPlayerBotHerbBush(ch, &distance);
			if (!bush)
			{
				PlayerBotLogThrottled("herb_no_bush", dwNow,
						"PLAYERBOT_HERB: no bush in reach pid=%u name=%s map=%ld level=%d",
						pid, ch->GetName(), ch->GetMapIndex(), (int)ch->GetLevel());
				return false;
			}
			if (!EnsurePlayerBotHerbKnife(ch, "field"))
			{
				PlayerBotLogThrottled("herb_no_knife", dwNow,
						"PLAYERBOT_HERB: no knife and no money for one pid=%u name=%s gold=%lld",
						pid, ch->GetName(), (long long)ch->GetGold());
				return false;
			}
			s_mapPlayerBotHerbUntil[pid] = dwNow + (DWORD)number((int)PLAYERBOT_HERB_SESSION_MIN_MS,
					(int)PLAYERBOT_HERB_SESSION_MAX_MS);
			s_mapPlayerBotHerbStarted[pid] = dwNow;
			s_mapPlayerBotHerbBush[pid] = (DWORD)bush->GetVID();
			s_mapPlayerBotHerbBushSince[pid] = dwNow;
			s_mapPlayerBotHerbPickAt.erase(pid);
			s_mapPlayerBotHerbHP.erase(pid);
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ClearPlayerBotRoute(state, true);
			sys_log(0, "PLAYERBOT_HERB: session start pid=%u name=%s map=%ld level=%d bush=%u dist=%ld minutes=%u activity=1",
					pid, ch->GetName(), ch->GetMapIndex(), (int)ch->GetLevel(),
					(unsigned int)bush->GetRaceNum(), distance,
					(unsigned int)((s_mapPlayerBotHerbUntil[pid] - dwNow) / 60000U));
		}

		// After a blow the fight is the bot's, and the bushes wait.
		std::map<DWORD, DWORD>::iterator resume = s_mapPlayerBotHerbResume.find(pid);
		if (resume != s_mapPlayerBotHerbResume.end())
		{
			if ((int)(dwNow - resume->second) < 0)
				return false;
			s_mapPlayerBotHerbResume.erase(resume);
			s_mapPlayerBotHerbHP.erase(pid);
		}
		const int hp = ch->GetHP();
		std::map<DWORD, int>::iterator lastHP = s_mapPlayerBotHerbHP.find(pid);
		if (lastHP != s_mapPlayerBotHerbHP.end() && hp < lastHP->second && hp < ch->GetMaxHP())
		{
			s_mapPlayerBotHerbPickAt.erase(pid);
			s_mapPlayerBotHerbResume[pid] = dwNow + PLAYERBOT_HERB_RESUME_MS;
			StowPlayerBotHerbKnife(ch);
			PlayerBotLogThrottled("herb_attacked", dwNow,
					"PLAYERBOT_HERB: attacked at the bushes pid=%u name=%s hp=%d/%d",
					pid, ch->GetName(), hp, ch->GetMaxHP());
			return false;
		}
		s_mapPlayerBotHerbHP[pid] = hp;

		if (CountPlayerBotFreeInventoryCells(ch) < PLAYERBOT_HERBALISM_FREE_CELLS)
		{
			EndPlayerBotHerbSession(ch, state, dwNow, "bag_full");
			return false;
		}
		// A row to brew and Baek-Go in this village: his board first.
		if (IsPlayerBotHerbalistVisitDue(ch, state, dwNow))
		{
			s_mapPlayerBotHerbPickAt.erase(pid);
			StowPlayerBotHerbKnife(ch);
			return false;
		}

		// The bush: the one it is on, or the nearest free one.
		LPCHARACTER bush = NULL;
		std::map<DWORD, DWORD>::const_iterator own = s_mapPlayerBotHerbBush.find(pid);
		if (own != s_mapPlayerBotHerbBush.end())
		{
			bush = CHARACTER_MANAGER::instance().Find(own->second);
			if (bush && (bush->IsDead() || !IsPlayerBotHerbBushRace(bush->GetRaceNum()) ||
					bush->GetMapIndex() != ch->GetMapIndex()))
				bush = NULL;
			if (!bush)
			{
				s_mapPlayerBotHerbBush.erase(pid);
				s_mapPlayerBotHerbPickAt.erase(pid);
			}
		}
		if (!bush)
		{
			long distance = 0;
			bush = FindPlayerBotHerbBush(ch, &distance);
			if (!bush)
			{
				// Every bush in reach picked bare or taken: the session goes on
				// (a herbalist hunts while its bushes grow back, as a player
				// does) and looks again in a minute. Ending it here ended 207
				// of 264 sessions on the test world within minutes.
				StowPlayerBotHerbKnife(ch);
				s_mapPlayerBotHerbResume[pid] = dwNow + 60000;
				PlayerBotLogThrottled("herb_wait_bush", dwNow,
						"PLAYERBOT_HERB: waiting for a bush pid=%u name=%s map=%ld",
						pid, ch->GetName(), ch->GetMapIndex());
				return false;
			}
			s_mapPlayerBotHerbBush[pid] = (DWORD)bush->GetVID();
			s_mapPlayerBotHerbBushSince[pid] = dwNow;
			s_mapPlayerBotHerbPickAt.erase(pid);
		}

		SetPlayerBotAction(state, BOT_ACTION_HERBALISM, dwNow);
		state.dwTargetVID = 0;
		const long distance = DISTANCE_APPROX(ch->GetX() - bush->GetX(), ch->GetY() - bush->GetY());
		if (distance > PLAYERBOT_HERB_ARRIVE)
		{
			s_mapPlayerBotHerbPickAt.erase(pid);
			// Two minutes on the way to one bush and it is somebody else's
			// ground - a wall, a cliff: the next one, and this one later.
			std::map<DWORD, DWORD>::const_iterator since = s_mapPlayerBotHerbBushSince.find(pid);
			if (since != s_mapPlayerBotHerbBushSince.end() && dwNow - since->second > 120000)
			{
				s_mapPlayerBotHerbSkipBush[pid] = (DWORD)bush->GetVID();
				s_mapPlayerBotHerbSkipUntil[pid] = dwNow + 10 * 60 * 1000;
				s_mapPlayerBotHerbBush.erase(pid);
				ClearPlayerBotRoute(state, true);
				PlayerBotLogThrottled("herb_unreachable", dwNow,
						"PLAYERBOT_HERB: bush out of reach pid=%u name=%s bush=%u dist=%ld",
						pid, ch->GetName(), (unsigned int)bush->GetRaceNum(), distance);
				return true;
			}
			StowPlayerBotHerbKnife(ch);
			MovePlayerBot(ch, bush->GetX(), bush->GetY(), dwNow, 4, false, true, false, false);
			return true;
		}

		// On foot at the bush, as at the vein.
		if (SetPlayerBotRidingForTravel(ch, state, false, dwNow, "herb"))
			ch->HorseSummon(false);
		ch->Stop();
		std::map<DWORD, DWORD>::iterator pick = s_mapPlayerBotHerbPickAt.find(pid);
		if (pick != s_mapPlayerBotHerbPickAt.end())
		{
			if ((int)(dwNow - pick->second) < 0)
				return true;
			s_mapPlayerBotHerbPickAt.erase(pick);
			s_mapPlayerBotHerbBushSince[pid] = dwNow;
			ResolvePlayerBotHerbPick(ch, bush);
			return true;
		}
		if (!EquipPlayerBotHerbKnife(ch))
		{
			// The engine refuses an equip for a moment after a blow or a swap:
			// the weapon back in the hand (the swap may have left it empty) and
			// the bush again a few seconds later. Only a knife that will not go
			// on five times running, or none at all, ends the session.
			if (!ch->GetWear(WEAR_WEAPON))
				EquipFirstAvailablePlayerBotWeapon(ch);
			int& fails = s_mapPlayerBotHerbEquipFails[pid];
			if (CountPlayerBotHerbKnives(ch) == 0 && !EnsurePlayerBotHerbKnife(ch, "field"))
				fails = 5;
			if (++fails >= 5)
			{
				s_mapPlayerBotHerbEquipFails.erase(pid);
				EndPlayerBotHerbSession(ch, state, dwNow, "no_knife", PLAYERBOT_HERB_RETRY_MS);
				return false;
			}
			s_mapPlayerBotHerbResume[pid] = dwNow + 3000;
			return false;
		}
		s_mapPlayerBotHerbEquipFails.erase(pid);
		ch->SetRotationToXY(bush->GetX(), bush->GetY());
		s_mapPlayerBotHerbPickAt[pid] = dwNow + PLAYERBOT_HERB_PICK_MS;
		return true;
	}

	static_assert(PLAYERBOT_HERB_ARRIVE >= PLAYERBOT_NAV_ARRIVAL_DISTANCE,
			"a herb arrival inside the walk's own stopping distance strands the bot");

#else   // r40250 has no crafting board, so none of this exists there.

	bool IsPlayerBotHerbalismHerb(DWORD) { return false; }
	bool IsPlayerBotCraftedPotion(LPITEM) { return false; }
	bool IsPlayerBotCraftRecipeItem(LPITEM) { return false; }
	bool IsPlayerBotPackedPotion(LPITEM) { return false; }
	bool IsPlayerBotHerbalismUnlocked(LPCHARACTER) { return false; }
	bool IsPlayerBotSurplusPotion(LPCHARACTER, LPITEM) { return false; }
	bool IsPlayerBotSurplusRecipe(LPCHARACTER, LPITEM) { return false; }
	bool ReadPlayerBotCraftRecipe(LPCHARACTER) { return false; }
	bool PlayerBotHasReadyCraftRow(LPCHARACTER) { return false; }
	void ManagePlayerBotCraftRecipes(LPCHARACTER, DWORD) { }
	bool DrinkPlayerBotCraftedPotion(LPCHARACTER, LPCHARACTER, DWORD, bool = false) { return false; }
	bool IsPlayerBotHerbGatherer(LPCHARACTER) { return false; }
	int GetPlayerBotCraftedPotionKeep(LPCHARACTER, DWORD) { return 0; }
	bool IsPlayerBotHerbBoardOpen(LPCHARACTER, DWORD) { return false; }
	bool IsPlayerBotHerbSessionNow(DWORD, DWORD) { return false; }
	bool IsPlayerBotHerbPickingNow(LPCHARACTER, DWORD) { return false; }
	bool ManagePlayerBotHerbGathering(LPCHARACTER, TPlayerBotAIState&, DWORD) { return false; }

#endif
}

#endif
