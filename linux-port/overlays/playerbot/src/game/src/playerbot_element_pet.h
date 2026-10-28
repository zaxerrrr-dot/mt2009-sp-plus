#ifndef __INC_METIN2_PLAYERBOT_ELEMENT_PET_H__
#define __INC_METIN2_PLAYERBOT_ELEMENT_PET_H__

// MT2009_PLUS_BOT_ELEMENT_PET_V1 - the owner, 28 October 2026: "Yohara bots buy in the item shop the Maly Zywiolak for
// their hunt element and wear it".
//
// The item: Maly Zywiolak (53290-53295) is ITEM_PET / PET_PAY (type 37, subtype 12) - a pet seal, never worn in a
// slot: it stays in the bag and CHARACTER::SummonPetFromItem (the seal's use, a toggle) calls its pet (value0, the
// mobs 34124-34129). While the pet is out the seal's item_proto applies count (CPetSystem::RefreshBuff from
// ComputePoints -> CItem::ModifyPoints): the element's resistance +10 and its power +5 (applies 178-183 are
// POINT_ENCHANT_ELECT..DARK, the element powers of the talismans). LIMIT_REAL_TIME 1 296 000 s: 15 days from the
// purchase, worn or not; the engine deletes the seal then and the pet goes with it (CPetActor::Update). The seal is
// never junk nor counter goods (IsPlayerBotJunkItem / the counter's ITEM_PET rule), so an old element's seal stays
// in the bag - for a second set's element later - until its 15 days end.
//
// Who: a member of the Sung Ma maps' cohort (common.playerbot_yohara_cohort, purposes 'yohara' and 'yohara800',
// YOHARA_PURPOSE_SUNGMA) loaded on this core, with a hunt element (GetPlayerBotHuntElement: 1 lightning 53292,
// 2 fire 53290, 3 ice 53291, 4 wind 53293, 5 earth 53294, 6 dark 53295).
//
// What, on its own clock (PLAYERBOT_ELEMPET_INTERVAL_MS, spread by pid):
//   * the element's pet out - nothing to do;
//   * its seal in the bag - out: another pet out (the ItemShop look's, or an old element's) is called back first
//     (SummonPetFromItem is a toggle: UnsummonAll), then this one is called;
//   * none - bought in the ItemShop through the bots' shop path (BuyPlayerBotItemShop: the balance read first when it
//     is not known, the engine's BuyItem, AutoGiveItem), at most once per PLAYERBOT_ELEMPET_RENEW_MS. No coins - no
//     pet (counted, no gift). This is the renewal too: a seal past its 15 days is gone, the next look buys again.
// A changed element (only upward now, or a second set's) is a new seal: the old one stays in the bag, kept.
// The gear pass never touches a pet seal (it is no slot's), and the ItemShop look (WearPlayerBotBoughtLook) calls a
// pet only when none is out, so the element's pet stays out once it is.
//
// The log: PLAYERBOT_ELEMPET (out / bought / cannot, and an hourly census of the members seen in the last hour on this
// core - out per element, bag_only, missing, no_element, and the hour's bought, no_coins, summoned, shop_off).
//
// An implementation fragment (playerbot_types.h): include it exactly once, from playerbot_manager.cpp, after
// playerbot_yohara_bots.h (the cohort), playerbot_itemshop.h (the purchase) and playerbot_element_resist.h (the hunt
// element).

#include <map>

namespace
{
	// By GetPlayerBotHuntElement - 1 (PLAYERBOT_YOHARA_ELEMENT_NAMES' order: lightning, fire, ice, wind, earth, dark).
	const DWORD PLAYERBOT_ELEMPET_VNUMS[PLAYERBOT_YOHARA_ELEMENTS] = { 53292, 53290, 53291, 53293, 53294, 53295 };
	const DWORD PLAYERBOT_ELEMPET_INTERVAL_MS = 30000;
	const DWORD PLAYERBOT_ELEMPET_RETRY_MS = 3000;
	const DWORD PLAYERBOT_ELEMPET_RENEW_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_ELEMPET_CENSUS_MS = 60 * 60 * 1000;

	enum
	{
		PLAYERBOT_ELEMPET_NO_ELEMENT = 0,
		PLAYERBOT_ELEMPET_MISSING,
		PLAYERBOT_ELEMPET_BAG_ONLY,
		PLAYERBOT_ELEMPET_OUT,
	};

	struct TPlayerBotElementPetState
	{
		DWORD dwNextLook;
		DWORD dwNextRenew;
		DWORD dwSeen;
		BYTE bStatus;
		int iElement;	// the hunt element's index (0-5) of the last look, -1 none
		TPlayerBotElementPetState() : dwNextLook(0), dwNextRenew(0), dwSeen(0), bStatus(PLAYERBOT_ELEMPET_NO_ELEMENT),
			iElement(-1) {}
	};
	std::map<DWORD, TPlayerBotElementPetState> s_mapPlayerBotElementPet;
	unsigned int s_uPlayerBotElementPetBought = 0;
	unsigned int s_uPlayerBotElementPetNoCoins = 0;
	unsigned int s_uPlayerBotElementPetSummoned = 0;
	unsigned int s_uPlayerBotElementPetShopOff = 0;
	DWORD s_dwPlayerBotElementPetCensus = 0;

	// The seal whose pet is out now, NULL for none (the engine's own test, item.cpp's set pass).
	LPITEM FindPlayerBotSummonedPetSeal(LPCHARACTER ch)
	{
#if defined(__PET_SYSTEM__)
		CPetSystem* pets = ch ? ch->GetPetSystem() : NULL;
		if (!pets || !pets->CountSummoned())
			return NULL;
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetType() != ITEM_PET || (item->GetSubType() != PET_PAY && item->GetSubType() != PET_UPBRINGING))
				continue;
			CPetActor* pet = pets->GetByVnum(item->GetValue(0));
			if (pet && pet->IsSummoned() && pet->GetSummonItemVID() == item->GetVID())
				return item;
		}
#else
		(void)ch;
#endif
		return NULL;
	}

	// For the element census (playerbot_element_resist.h, the "pet" source): what the pet out gives to the point.
	long GetPlayerBotElementPetResist(LPCHARACTER ch, BYTE point)
	{
		LPITEM seal = FindPlayerBotSummonedPetSeal(ch);
		long total = 0;
		if (!seal || !seal->GetProto() || !point)
			return 0;
		for (int i = 0; i < ITEM_APPLY_MAX_NUM; ++i)
			if (seal->GetProto()->aApplies[i].bType == point)
				total += seal->GetProto()->aApplies[i].lValue;
		return total;
	}

	LPITEM FindPlayerBotBagElementPet(LPCHARACTER ch, DWORD vnum)
	{
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetVnum() == vnum && !item->isLocked() && !item->IsExchanging())
				return item;
		}
		return NULL;
	}

	// A new seal from the ItemShop, when it sells one and the coins cover it.
	void BuyPlayerBotElementPet(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotElementPetState& ep, DWORD vnum,
			DWORD dwNow)
	{
		if (dwNow < ep.dwNextRenew)
			return;
#if defined(PLAYERBOT_ENGINE_MT2009)
		if (!IsPlayerBotItemShopEnabled() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
		{
			++s_uPlayerBotElementPetShopOff;
			ep.dwNextRenew = dwNow + PLAYERBOT_ELEMPET_RENEW_MS;
			return;
		}
		if (dwNow < state.dwNextItemShopBuyTime || ch->IsBusy() || ch->GetExchange() || ch->GetMyShop())
			return;	// the shop's own pace (one purchase at a time): the next look
		if (ch->GetEmptyInventory(1) < 0)
		{
			PlayerBotLogThrottled("elempet_bag_full", dwNow,
					"PLAYERBOT_ELEMPET: cannot buy pid=%u name=%s vnum=%u reason=bag_full", ch->GetPlayerID(), ch->GetName(),
					vnum);
			ep.dwNextLook = dwNow + PLAYERBOT_ELEMPET_INTERVAL_MS * 4;
			return;
		}
		ep.dwNextRenew = dwNow + PLAYERBOT_ELEMPET_RENEW_MS;
		RefreshPlayerBotItemShopCatalogue(dwNow);
		const DWORD price = GetPlayerBotItemShopCheapest(ch, vnum, false);
		if (price == 0)
		{
			PlayerBotLogThrottled("elempet_not_sold", dwNow,
					"PLAYERBOT_ELEMPET: cannot buy pid=%u name=%s vnum=%u reason=not_in_itemshop", ch->GetPlayerID(),
					ch->GetName(), vnum);
			return;
		}
		// The balance read first when the shop pass never needed it - once a renewal, at most every
		// PLAYERBOT_ELEMPET_RENEW_MS (as the element stone, playerbot_element_stones.h).
		if (!state.bDragonBalanceKnown)
			RefreshPlayerBotDragonBalance(ch, state, dwNow);
		TPlayerBotItemShopWish wish;
		wish.dwVnum = vnum;
		wish.bMarks = false;
		wish.szReason = "element_pet";
		if (!CanPlayerBotAffordWish(ch, state, wish))
		{
			++s_uPlayerBotElementPetNoCoins;
			PlayerBotLogThrottled("elempet_no_coins", dwNow,
					"PLAYERBOT_ELEMPET: cannot buy pid=%u name=%s vnum=%u reason=no_coins coins=%d price=%u",
					ch->GetPlayerID(), ch->GetName(), vnum, state.iDragonCoins, price);
			return;
		}
		if (BuyPlayerBotItemShop(ch, state, wish, dwNow))
		{
			++s_uPlayerBotElementPetBought;
			sys_log(0, "PLAYERBOT_ELEMPET: bought pid=%u name=%s lv=%d vnum=%u element=%s coins_left=%d", ch->GetPlayerID(),
					ch->GetName(), ch->GetLevel(), vnum, ep.iElement >= 0 ? PLAYERBOT_YOHARA_ELEMENT_NAMES[ep.iElement] : "-",
					state.iDragonCoins);
			ep.dwNextLook = dwNow + PLAYERBOT_ELEMPET_RETRY_MS;
		}
#else
		(void)state; (void)vnum;
#endif
	}

	void ManagePlayerBotElementPet(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || ch->IsDead() || !ch->GetSectree() ||
				GetPlayerBotYoharaCohortPurpose(ch->GetPlayerID()) != YOHARA_PURPOSE_SUNGMA)
			return;
		TPlayerBotElementPetState& ep = s_mapPlayerBotElementPet[ch->GetPlayerID()];
		if (ep.dwNextLook == 0)
			ep.dwNextLook = dwNow + PlayerBotNavHash(ch->GetPlayerID() ^ 0x45504554U) % PLAYERBOT_ELEMPET_INTERVAL_MS;
		if (dwNow < ep.dwNextLook)
			return;
		ep.dwNextLook = dwNow + PLAYERBOT_ELEMPET_INTERVAL_MS;
		ep.dwSeen = dwNow;

		const int e = (int)GetPlayerBotHuntElement(ch) - 1;
		if (e < 0 || e >= PLAYERBOT_YOHARA_ELEMENTS)
		{
			ep.bStatus = PLAYERBOT_ELEMPET_NO_ELEMENT;
			return;
		}
		if (e != ep.iElement && ep.iElement >= 0)
			ep.dwNextRenew = 0;	// a new element: its seal at once, not after the old one's renewal wait
		ep.iElement = e;
		const DWORD vnum = PLAYERBOT_ELEMPET_VNUMS[e];
		LPITEM out = FindPlayerBotSummonedPetSeal(ch);
		if (out && out->GetVnum() == vnum)
		{
			ep.bStatus = PLAYERBOT_ELEMPET_OUT;
			return;
		}
		LPITEM seal = FindPlayerBotBagElementPet(ch, vnum);
		ep.bStatus = seal ? PLAYERBOT_ELEMPET_BAG_ONLY : PLAYERBOT_ELEMPET_MISSING;
		if (ch->GetExchange() || ch->GetMyShop() || !ch->CanHandleItem())
			return;
		if (!seal)
		{
			BuyPlayerBotElementPet(ch, state, ep, vnum, dwNow);
			return;
		}
#if defined(__PET_SYSTEM__) && defined(USE_PET_SEAL_ON_LOGIN)
		if (!ch->GetPetSystem())
			return;
		const DWORD oldVnum = out ? out->GetVnum() : 0;
		// Another pet out: called back first (the seal's use is a toggle - UnsummonAll, nothing called).
		if (out)
			ch->SummonPetFromItem(out);
		if (ch->SummonPetFromItem(seal) && FindPlayerBotSummonedPetSeal(ch) == seal)
		{
			++s_uPlayerBotElementPetSummoned;
			ep.bStatus = PLAYERBOT_ELEMPET_OUT;
			sys_log(0, "PLAYERBOT_ELEMPET: out pid=%u name=%s lv=%d vnum=%u element=%s replaced=%u ends=%ld resist=%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), vnum, PLAYERBOT_YOHARA_ELEMENT_NAMES[e], oldVnum,
					(long)seal->GetSocket(0), (int)ch->GetPoint(PLAYERBOT_YOHARA_RESIST_POINTS[e]));
		}
		else
		{
			PlayerBotLogThrottled("elempet_summon", dwNow,
					"PLAYERBOT_ELEMPET: cannot call pid=%u name=%s vnum=%u old=%u", ch->GetPlayerID(), ch->GetName(), vnum,
					oldVnum);
			ep.dwNextLook = dwNow + PLAYERBOT_ELEMPET_RETRY_MS * 10;
		}
#endif
	}

	// Hourly: the members this core looked at in the last hour, by their pet, and what the hour did.
	void WritePlayerBotElementPetCensus(DWORD dwNow)
	{
		if (s_dwPlayerBotElementPetCensus == 0)
		{
			s_dwPlayerBotElementPetCensus = dwNow + PLAYERBOT_ELEMPET_CENSUS_MS;
			return;
		}
		if (dwNow < s_dwPlayerBotElementPetCensus)
			return;
		s_dwPlayerBotElementPetCensus = dwNow + PLAYERBOT_ELEMPET_CENSUS_MS;
		unsigned int count[4] = { 0, 0, 0, 0 };
		unsigned int outBy[PLAYERBOT_YOHARA_ELEMENTS] = { 0 }, missingBy[PLAYERBOT_YOHARA_ELEMENTS] = { 0 };
		for (std::map<DWORD, TPlayerBotElementPetState>::iterator it = s_mapPlayerBotElementPet.begin();
				it != s_mapPlayerBotElementPet.end();)
		{
			if (it->second.dwSeen == 0 || dwNow - it->second.dwSeen > PLAYERBOT_ELEMPET_CENSUS_MS)
			{
				s_mapPlayerBotElementPet.erase(it++);
				continue;
			}
			const BYTE status = it->second.bStatus;
			const int e = it->second.iElement;
			if (status < 4)
				++count[status];
			if (e >= 0 && e < PLAYERBOT_YOHARA_ELEMENTS && status != PLAYERBOT_ELEMPET_NO_ELEMENT)
				++(status == PLAYERBOT_ELEMPET_OUT ? outBy[e] : missingBy[e]);
			++it;
		}
		const unsigned int members = count[0] + count[1] + count[2] + count[3];
		if (members == 0 && s_uPlayerBotElementPetBought == 0)
			return;
		std::string by;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
		{
			char one[48];
			snprintf(one, sizeof(one), "%s%s=%u/%u", e ? " " : "", PLAYERBOT_YOHARA_ELEMENT_NAMES[e], outBy[e],
					outBy[e] + missingBy[e]);
			by += one;
		}
		sys_log(0, "PLAYERBOT_ELEMPET: census members=%u out=%u bag_only=%u missing=%u no_element=%u out_by_element=[%s] "
				"bought=%u no_coins=%u summoned=%u shop_off=%u",
				members, count[PLAYERBOT_ELEMPET_OUT], count[PLAYERBOT_ELEMPET_BAG_ONLY], count[PLAYERBOT_ELEMPET_MISSING],
				count[PLAYERBOT_ELEMPET_NO_ELEMENT], by.c_str(), s_uPlayerBotElementPetBought, s_uPlayerBotElementPetNoCoins,
				s_uPlayerBotElementPetSummoned, s_uPlayerBotElementPetShopOff);
		s_uPlayerBotElementPetBought = s_uPlayerBotElementPetNoCoins = 0;
		s_uPlayerBotElementPetSummoned = s_uPlayerBotElementPetShopOff = 0;
	}
}

#endif
