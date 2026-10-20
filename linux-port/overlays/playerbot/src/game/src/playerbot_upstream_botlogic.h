#ifndef __INC_METIN2_PLAYERBOT_UPSTREAM_BOTLOGIC_H__
#define __INC_METIN2_PLAYERBOT_UPSTREAM_BOTLOGIC_H__

// MT2009_PLUS_UPSTREAM_BOTLOGIC_*_V1 - a package of bot-logic rules after the
// upstream bots' changelog of 17-18 October (their 2.2.103 and 2.2.108). The
// upstream server is shipped protected, so these are our own implementations
// of the behaviour the changelog describes, fitted to our rules (the stall
// rules, the two-bonus goods rule, the Law of Advancement, the safebox's
// LPP / soul stone +4 / herb surplus work):
//
// - LOTTERY30_V1: a surplus level-30 weapon goes to the anvil instead of the
//   counter, a few a day, while the counters are full of the family at +0.
// - FUTURE_V1: the richest bots buy and raise, in the bag, the weapon or body
//   armour of the next tier a few levels before they can wear it - never
//   while the Law of Advancement is short of something.
// - OWN_BOX_V1: a weapon or armour piece in the bot's own safebox that beats
//   what it wears comes out at the storekeeper, and while the box holds one
//   for a slot the counters do not sell it one.
//
// The rest of the package lives where its rule is asked: LEVEL75_V1 and
// LOW_GEAR_V1 in playerbot_gear.h, MATERIAL_PRICE_V1 in playerbot_town.h,
// HUNT70_V1 in playerbot_travel.h, SPIRIT_STONE_V1 in
// playerbot_progression_needs.h / playerbot_market.h / playerbot_manager.cpp,
// ZELKOVA_V1 in collect_quest_lv70.quest.
//
// An implementation fragment in the sense playerbot_types.h describes:
// included once, from playerbot_manager.cpp, after playerbot_progression_needs.h
// and before playerbot_town.h.

namespace
{
	// Defined with the town code, after this file.
	DWORD GetPlayerBotShopAskingPrice(LPITEM item);

	// ---------------------------------------------------------------------
	// MT2009_PLUS_UPSTREAM_BOTLOGIC_LOTTERY30_V1
	// ---------------------------------------------------------------------
	// How many surplus level-30 weapons a bot takes to the anvil a day, and
	// how many +0 units of the family the counters must hold for it to.
	const int PLAYERBOT_LOTTERY30_PER_DAY = 2;
	const int PLAYERBOT_LOTTERY30_MARKET_PLUS0 = 6;
	const char* const PLAYERBOT_LOTTERY30_DAY_FLAG = "mt2009_botlogic.lot30_day";
	const char* const PLAYERBOT_LOTTERY30_COUNT_FLAG = "mt2009_botlogic.lot30_n";
	const char* const PLAYERBOT_LOTTERY30_ID_FLAG = "mt2009_botlogic.lot30_id";

	int GetPlayerBotLottery30Today()
	{
		return (int)(get_global_time() / 86400);
	}

	// A level-30 weapon no other rule works: not the class's own, not the
	// project, not one kept for the anvil or ground for sale, not the sash's
	// grail, not over the scroll-only line, not a level-30 dropper's goods.
	bool IsPlayerBotLottery30Surplus(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !IsPlayerBotSpecialLevel30Weapon(item) || item->IsEquipped() ||
				item->GetWindow() != INVENTORY || (int)ch->GetLevel() < 30 ||
				IsPlayerBotSidekickServing(ch) || IsPlayerBotL30WeaponSeller(ch) ||
				IsPlayerBotScrollOnlyWeapon(item) || IsPlayerBotSashGrailProject(ch, item) ||
				item == FindPlayerBotClassLevel30Weapon(ch) || IsPlayerBotLevel30Project(ch, item) ||
				PlayerBotKeepsLevel30ForAnvil(ch, item) || PlayerBotRefinesLevel30ForSale(ch, item))
			return false;
		// The shop management's word on grinding for sale (point 3): off, none.
		if (IsPlayerBotShopMgmtOn() && GetPlayerBotShopMgmt(PLAYERBOT_SM_L30_SALE_LINES) <= 0)
			return false;
		return item->GetRefineLevel() < GetPlayerBotLevel30SaleTarget(item);
	}

	// The one the anvil took today, while it is still under its ceiling.
	bool IsPlayerBotLottery30Piece(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || ch->GetQuestFlag(PLAYERBOT_LOTTERY30_DAY_FLAG) != GetPlayerBotLottery30Today() ||
				(DWORD)ch->GetQuestFlag(PLAYERBOT_LOTTERY30_ID_FLAG) != item->GetID())
			return false;
		return IsPlayerBotLottery30Surplus(ch, item);
	}

	// Asked by the refine pass of a bag piece no rule works: a +0 surplus
	// weapon of a family the counters hold plenty of at +0 goes to the anvil,
	// PLAYERBOT_LOTTERY30_PER_DAY a day, when the bag pays for the step.
	bool TryPickPlayerBotLottery30(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || item->GetRefineLevel() != 0 || IsPlayerBotLottery30Piece(ch, item) ||
				!IsPlayerBotLottery30Surplus(ch, item) || !CanPlayerBotAffordRefineAttempt(ch, item))
			return false;
		const int today = GetPlayerBotLottery30Today();
		int taken = ch->GetQuestFlag(PLAYERBOT_LOTTERY30_DAY_FLAG) == today
				? ch->GetQuestFlag(PLAYERBOT_LOTTERY30_COUNT_FLAG) : 0;
		if (taken >= PLAYERBOT_LOTTERY30_PER_DAY)
			return false;
		// The current one, still under its ceiling, finishes first.
		if (ch->GetQuestFlag(PLAYERBOT_LOTTERY30_DAY_FLAG) == today)
		{
			LPITEM current = ITEM_MANAGER::instance().Find((DWORD)ch->GetQuestFlag(PLAYERBOT_LOTTERY30_ID_FLAG));
			if (current && current != item && current->GetOwner() == ch && IsPlayerBotLottery30Surplus(ch, current))
				return false;
		}
		const TPlayerBotMarketLedgerEntry* plus0 = GetPlayerBotMarketLedgerEntry(item->GetVnum());
		const int market = plus0 ? (int)plus0->dwSupplyUnits : 0;
		if (market < PLAYERBOT_LOTTERY30_MARKET_PLUS0)
			return false;
		ch->SetQuestFlag(PLAYERBOT_LOTTERY30_DAY_FLAG, today);
		ch->SetQuestFlag(PLAYERBOT_LOTTERY30_COUNT_FLAG, ++taken);
		ch->SetQuestFlag(PLAYERBOT_LOTTERY30_ID_FLAG, (int)item->GetID());
		sys_log(0, "PLAYERBOT_SURPLUS: lottery30 takes pid=%u name=%s item=%u vnum=%u plus=%u avg=%ld market_plus0=%d today=%d target=%u",
				ch->GetPlayerID(), ch->GetName(), item->GetID(), item->GetVnum(), (unsigned int)item->GetRefineLevel(),
				SumPlayerBotItemLines(item, APPLY_NORMAL_HIT_DAMAGE_BONUS), market, taken,
				(unsigned int)GetPlayerBotLevel30SaleTarget(item));
		return true;
	}

	// ---------------------------------------------------------------------
	// MT2009_PLUS_UPSTREAM_BOTLOGIC_FUTURE_V1
	// ---------------------------------------------------------------------
	// How many levels ahead a piece is made ready, who is rich enough (the
	// floor, or this many market median wallets), how far it is raised, and
	// how much of the purse one purchase may take.
	const int PLAYERBOT_FUTURE_PROJECT_AHEAD = 5;
	const long long PLAYERBOT_FUTURE_PROJECT_MIN_GOLD = 20000000LL;
	const int PLAYERBOT_FUTURE_PROJECT_WALLET_MULT = 5;
	const int PLAYERBOT_FUTURE_PROJECT_MAX_PLUS = 7;
	const int PLAYERBOT_FUTURE_PROJECT_PURSE_PERCENT = 15;

	bool IsPlayerBotRichForFuture(LPCHARACTER ch)
	{
		if (!ch || IsPlayerBotSidekickServing(ch) || PlayerBotHasLawRefineWork(ch))
			return false;
		const long long wallet = (long long)GetPlayerBotMarketMedianWallet() * PLAYERBOT_FUTURE_PROJECT_WALLET_MULT;
		return (long long)ch->GetGold() >= std::max(PLAYERBOT_FUTURE_PROJECT_MIN_GOLD, wallet);
	}

	// A weapon or body armour of the bot's own, a level it has not reached and
	// at most PLAYERBOT_FUTURE_PROJECT_AHEAD over it, of a higher level than the
	// piece worn in its slot. Not a Stalki: playerbot_stalki.h keeps those.
	int GetPlayerBotFutureSlot(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || IsPlayerBotStalkiItem(item) || IsPlayerBotSpecialLevel30Weapon(item) ||
				!IsPlayerBotEquipmentCandidate(ch, item))
			return -1;
		const int level = (int)item->GetLevelLimit();
		if (level <= (int)ch->GetLevel() || level > (int)ch->GetLevel() + PLAYERBOT_FUTURE_PROJECT_AHEAD)
			return -1;
		const int slot = item->FindEquipCell(ch);
		if (slot != WEAR_WEAPON && slot != WEAR_BODY)
			return -1;
		LPITEM worn = ch->GetWear((WORD)slot);
		if (!worn || (int)worn->GetLevelLimit() >= level)
			return -1;
		return slot;
	}

	// The bag's one future piece for the slot: the best by the equipment
	// pass's score, the lower id on a tie.
	LPITEM FindPlayerBotFutureProject(LPCHARACTER ch, int slot)
	{
		if (!ch || !ch->IsItemLoaded())
			return NULL;
		LPITEM best = NULL;
		long long bestScore = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || item->IsEquipped() || GetPlayerBotFutureSlot(ch, item) != slot)
				continue;
			const long long score = GetPlayerBotEquipmentScore(item, ch);
			if (!best || score > bestScore || (score == bestScore && item->GetID() < best->GetID()))
			{
				best = item;
				bestScore = score;
			}
		}
		return best;
	}

	// Kept whatever the purse (neither scrap nor counter goods); raised only
	// while the bot is rich.
	bool IsPlayerBotFutureProject(LPCHARACTER ch, LPITEM item)
	{
		const int slot = GetPlayerBotFutureSlot(ch, item);
		return slot >= 0 && FindPlayerBotFutureProject(ch, slot) == item;
	}

	// To the plus the worn piece has (at least +4), at most
	// PLAYERBOT_FUTURE_PROJECT_MAX_PLUS; none of it for a bot that is not rich.
	BYTE GetPlayerBotFutureProjectTarget(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !IsPlayerBotRichForFuture(ch))
			return item ? item->GetRefineLevel() : 0;
		const int slot = item->FindEquipCell(ch);
		LPITEM worn = slot >= 0 && slot < WEAR_MAX_NUM ? ch->GetWear((WORD)slot) : NULL;
		const int wornPlus = worn ? (int)worn->GetRefineLevel() : 0;
		return (BYTE)std::min(PLAYERBOT_FUTURE_PROJECT_MAX_PLUS, std::max(4, wornPlus));
	}

	// A counter's line a rich bot buys for its next tier: a future piece for a
	// slot the bag holds none for, within its share of the purse.
	bool WantsPlayerBotFutureOffer(LPCHARACTER ch, LPITEM offer)
	{
		const int slot = GetPlayerBotFutureSlot(ch, offer);
		if (slot < 0 || !IsPlayerBotRichForFuture(ch) || FindPlayerBotFutureProject(ch, slot) != NULL)
			return false;
		const long long fair = (long long)GetPlayerBotShopAskingPrice(offer);
		return fair > 0 && fair <= (long long)ch->GetGold() * PLAYERBOT_FUTURE_PROJECT_PURSE_PERCENT / 100;
	}

	// ---------------------------------------------------------------------
	// MT2009_PLUS_UPSTREAM_BOTLOGIC_OWN_BOX_V1
	// ---------------------------------------------------------------------
	// How long after a storekeeper visit for the box's gear the next one may
	// be asked for that reason.
	const DWORD PLAYERBOT_OWN_BOX_VISIT_GAP_MS = 60 * 60 * 1000;
	std::map<DWORD, DWORD> s_mapPlayerBotOwnBoxVisitAt;

	// The slots a stored piece is looked for in.
	bool IsPlayerBotOwnBoxSlot(int wearCell)
	{
		return wearCell == WEAR_WEAPON || wearCell == WEAR_BODY || wearCell == WEAR_SHIELD || wearCell == WEAR_HEAD;
	}

	// A piece in the box this bot would put on now: its own, of its level, for
	// a slot that is empty or that it outscores, and no better one in the bag.
	bool IsPlayerBotOwnBoxGear(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || (item->GetType() != ITEM_WEAPON && item->GetType() != ITEM_ARMOR) ||
				item->GetLevelLimit() > ch->GetLevel() || !IsPlayerBotEquipmentCandidate(ch, item))
			return false;
		const int slot = item->FindEquipCell(ch);
		if (!IsPlayerBotOwnBoxSlot(slot))
			return false;
		const long long score = GetPlayerBotEquipmentScore(item, ch);
		LPITEM worn = ch->GetWear((WORD)slot);
		if (worn && GetPlayerBotEquipmentScore(worn, ch) >= score)
			return false;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM other = ch->GetInventoryItem(cell);
			if (other && other->GetCell() == cell && !other->IsEquipped() && other->FindEquipCell(ch) == slot &&
					other->GetLevelLimit() <= ch->GetLevel() && IsPlayerBotEquipmentCandidate(ch, other) &&
					GetPlayerBotEquipmentScore(other, ch) >= score)
				return false;
		}
		return true;
	}

	// What the last look at the box remembers (TPlayerBotPersona::mapGearStored,
	// by family): a piece of the bot's own for the slot, of its level, of a
	// higher level than the worn one or for an empty slot. The +0 of the
	// family stands for it - its level and its kind are the family's.
	bool PlayerBotBoxHoldsGearFor(LPCHARACTER ch, const TPlayerBotPersona& p, int wearCell, int minLevel)
	{
		if (!ch || !p.bLppStoredKnown || !IsPlayerBotOwnBoxSlot(wearCell) || p.mapGearStored.empty())
			return false;
		LPITEM worn = ch->GetWear((WORD)wearCell);
		const int wornLevel = worn ? (int)worn->GetLevelLimit() : -1;
		for (std::map<DWORD, BYTE>::const_iterator it = p.mapGearStored.begin(); it != p.mapGearStored.end(); ++it)
		{
			if (it->second == 0)
				continue;
			const TItemTable* proto = ITEM_MANAGER::instance().GetTable(it->first);
			if (!proto || (proto->bType != ITEM_WEAPON && proto->bType != ITEM_ARMOR) ||
					!IsPlayerBotProtoForCharacter(ch, proto))
				continue;
			if (proto->bType == ITEM_WEAPON)
			{
				if (wearCell != WEAR_WEAPON || !IsPlayerBotWeaponSubTypeFor(ch, proto->bSubType))
					continue;
			}
			else if ((wearCell == WEAR_BODY && proto->bSubType != ARMOR_BODY) ||
					(wearCell == WEAR_SHIELD && proto->bSubType != ARMOR_SHIELD) ||
					(wearCell == WEAR_HEAD && proto->bSubType != ARMOR_HEAD) || wearCell == WEAR_WEAPON)
				continue;
			const int level = GetPlayerBotProtoLevelLimit(proto);
			if (level <= (int)ch->GetLevel() && level > wornLevel && level >= minLevel)
				return true;
		}
		return false;
	}

	// The town visit's question: the box holds a piece for one of the four
	// slots - asked at most once in PLAYERBOT_OWN_BOX_VISIT_GAP_MS, so a piece
	// the withdrawal will not take (its score) costs one visit, not every one.
	bool PlayerBotWantsOwnBoxGear(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !IsPlayerBotPersonaEnabled() || IsPlayerBotSidekickServing(ch))
			return false;
		std::map<DWORD, DWORD>::const_iterator at = s_mapPlayerBotOwnBoxVisitAt.find(ch->GetPlayerID());
		if (at != s_mapPlayerBotOwnBoxVisitAt.end() && dwNow - at->second < PLAYERBOT_OWN_BOX_VISIT_GAP_MS)
			return false;
		static const int slots[] = { WEAR_WEAPON, WEAR_BODY, WEAR_SHIELD, WEAR_HEAD };
		for (size_t i = 0; i < sizeof(slots) / sizeof(slots[0]); ++i)
		{
			if (PlayerBotBoxHoldsGearFor(ch, state.persona, slots[i], 0) && ch->GetEmptyInventory(3) >= 0)
			{
				s_mapPlayerBotOwnBoxVisitAt[ch->GetPlayerID()] = dwNow;
				return true;
			}
		}
		return false;
	}

	// A counter's weapon or armour piece the bot does not buy because its box
	// holds one for the slot of the offer's level or over (the storekeeper
	// first). Read off the remembered box, so it costs no visit.
	bool IsPlayerBotOfferBeatenByOwnBox(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer || (offer->GetType() != ITEM_WEAPON && offer->GetType() != ITEM_ARMOR) ||
				!IsPlayerBotPersonaEnabled())
			return false;
		TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		if (st == s_mapPlayerBotAIStates.end())
			return false;
		const int slot = offer->FindEquipCell(ch);
		if (!IsPlayerBotOwnBoxSlot(slot) || !PlayerBotBoxHoldsGearFor(ch, st->second.persona, slot, (int)offer->GetLevelLimit()))
			return false;
		PlayerBotLogThrottled("own_box_first", get_dword_time(),
				"PLAYERBOT_MARKET: own box first pid=%u name=%s slot=%d offer_vnum=%u offer_level=%u",
				ch->GetPlayerID(), ch->GetName(), slot, offer->GetVnum(), (unsigned int)offer->GetLevelLimit());
		return true;
	}
}

#endif
