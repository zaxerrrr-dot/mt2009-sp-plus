#ifndef __INC_METIN2_PLAYERBOT_ELEMENT_STONES_H__
#define __INC_METIN2_PLAYERBOT_ELEMENT_STONES_H__

// MT2009_PLUS_ELEMENT_STONES_V1 (bots): every Yohara bot wears Kamien Ochrony Zywiolow (39120, +10% resistance to all
// six elements, 7 days of real time) in a unique slot - the owner, 28 October 2026: "Wszystkie boty Yohary wyposaz w
// ten ochronny".
//
// Who: a member of the Sung Ma maps' cohort (common.playerbot_yohara_cohort, purposes 'yohara' and 'yohara800' -
// YOHARA_PURPOSE_SUNGMA, playerbot_yohara_bots.h) loaded on this core.
//
// What, on its own clock (PLAYERBOT_ELEMSTONE_INTERVAL_MS, spread by pid), never the tick's owner:
//   * a stone worn (either kind - only one at a time, playerbot_element_stones.cpp) - nothing to do;
//   * a protection stone in the bag - on: into a free unique slot, else in place of the least useful unique there
//     (one that pays a bot nothing first, then a plain one - a lollipop, an amulet -, then a thief's glove, then a ring
//     of experience; never the Prophecy King's glove or symbol at a negative rank, never what the engine or the
//     player's companion pins). Out of a fight's swing window (IsPlayerBotUniqueSwapWindowOpen), as the ring pass;
//   * none - a new one: bought in the ItemShop when the in-game catalogue sells it and the coins cover it (the bots'
//     shop path, BuyPlayerBotItemShop), else given (AutoGiveItem) - once per PLAYERBOT_ELEMSTONE_RENEW_MS at most, so
//     a stone that cannot go on is not handed out again and again. This is the renewal: the engine deletes the stone
//     when its 7 days are over, worn or not.
// The other passes leave it alone: the gear pass neither puts it on nor takes it off (playerbot_gear.h), the ring pass
// counts it as a held slot (IsPlayerBotUniqueSlotHeld, playerbot_unique_slots.h), the merchant never gets it
// (IsPlayerBotJunkItem, playerbot_economy.h); the antiflags keep it off the counters and the ground.
//
// The log: PLAYERBOT_ELEMSTONE (on / replaced / bought / given / cannot, and an hourly census of the members seen in
// the last hour on this core - worn, worn_power, bag_only, missing, renewed (bought + given), equipped, replaced).
//
// An implementation fragment (playerbot_types.h): include it exactly once, from playerbot_manager.cpp, after
// playerbot_yohara_bots.h (the cohort), playerbot_itemshop.h (the purchase) and playerbot_unique_slots.h (the slots).

#include <map>

namespace
{
	const DWORD PLAYERBOT_ELEMSTONE_PROTECT_VNUM = 39120;	// Kamien Ochrony Zywiolow
	const DWORD PLAYERBOT_ELEMSTONE_POWER_VNUM = 39119;		// Kamien Mocy Zywiolow
	const DWORD PLAYERBOT_ELEMSTONE_INTERVAL_MS = 30000;
	const DWORD PLAYERBOT_ELEMSTONE_RETRY_MS = 3000;
	const DWORD PLAYERBOT_ELEMSTONE_RENEW_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_ELEMSTONE_CENSUS_MS = 60 * 60 * 1000;

	enum
	{
		PLAYERBOT_ELEMSTONE_MISSING = 0,
		PLAYERBOT_ELEMSTONE_WORN,
		PLAYERBOT_ELEMSTONE_WORN_POWER,
		PLAYERBOT_ELEMSTONE_BAG_ONLY,
	};

	struct TPlayerBotElementStoneState
	{
		DWORD dwNextLook;
		DWORD dwNextRenew;
		DWORD dwSeen;
		BYTE bStatus;
		TPlayerBotElementStoneState() : dwNextLook(0), dwNextRenew(0), dwSeen(0), bStatus(PLAYERBOT_ELEMSTONE_MISSING) {}
	};
	std::map<DWORD, TPlayerBotElementStoneState> s_mapPlayerBotElementStone;
	unsigned int s_uPlayerBotElementStoneBought = 0;
	unsigned int s_uPlayerBotElementStoneGiven = 0;
	unsigned int s_uPlayerBotElementStoneEquipped = 0;
	unsigned int s_uPlayerBotElementStoneReplaced = 0;
	DWORD s_dwPlayerBotElementStoneCensus = 0;

	bool IsPlayerBotElementStoneMember(LPCHARACTER ch)
	{
		return ch && GetPlayerBotYoharaCohortPurpose(ch->GetPlayerID()) == YOHARA_PURPOSE_SUNGMA;
	}

	LPITEM FindPlayerBotWornElementStone(LPCHARACTER ch)
	{
		for (int wear = WEAR_UNIQUE1; wear <= WEAR_UNIQUE2; ++wear)
		{
			LPITEM worn = ch->GetWear(wear);
			if (worn && Mt2009IsElementStone(worn->GetVnum()))
				return worn;
		}
		return NULL;
	}

	LPITEM FindPlayerBotBagElementStone(LPCHARACTER ch, WORD& outCell)
	{
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetVnum() != PLAYERBOT_ELEMSTONE_PROTECT_VNUM || item->isLocked() || item->IsExchanging())
				continue;
			outCell = cell;
			return item;
		}
		return NULL;
	}

	// How little a worn unique is worth to a Yohara bot against the stone: 0 nothing at all, 1 a plain one, 2 a
	// thief's glove, 3 a ring of experience; -1 not to be taken off (pinned, stuck, the rank glove or symbol while the
	// rank is below zero, a stone).
	int GetPlayerBotElementStoneDisplaceRank(LPCHARACTER ch, LPITEM worn, int wear)
	{
		if (!worn || !IsPlayerBotWornItemSound(ch, worn, wear) || IS_SET(worn->GetFlag(), ITEM_FLAG_IRREMOVABLE) ||
				IsPlayerBotSidekickPinned(ch, worn))
			return -1;
		const DWORD vnum = worn->GetVnum();
		if (Mt2009IsElementStone(vnum))
			return -1;
		if (IsPlayerBotNeverWornUnique(vnum) || (IsPlayerBotRankUnique(vnum) && ch->GetRealAlignment() >= 0))
			return 0;
		if (IsPlayerBotRankUnique(vnum))
			return -1;
		if (IsPlayerBotThiefGlove(vnum))
			return 2;
		if (IsPlayerBotExpRing(vnum))
			return 3;
		return 1;
	}

	// A new stone: the ItemShop's when it sells one the bot can pay for, else given.
	void RenewPlayerBotElementStone(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotElementStoneState& es, DWORD dwNow)
	{
		if (dwNow < es.dwNextRenew)
			return;
		if (ch->GetEmptyInventory(1) < 0)
		{
			PlayerBotLogThrottled("elemstone_bag_full", dwNow,
					"PLAYERBOT_ELEMSTONE: cannot renew pid=%u name=%s reason=bag_full", ch->GetPlayerID(), ch->GetName());
			es.dwNextLook = dwNow + PLAYERBOT_ELEMSTONE_INTERVAL_MS * 4;
			return;
		}
		es.dwNextRenew = dwNow + PLAYERBOT_ELEMSTONE_RENEW_MS;
#if defined(PLAYERBOT_ENGINE_MT2009)
		if (IsPlayerBotItemShopEnabled() && !IsPlayerBotSidekickPID(ch->GetPlayerID()) &&
				dwNow >= state.dwNextItemShopBuyTime && !ch->IsBusy() && !ch->GetExchange() && !ch->GetMyShop())
		{
			RefreshPlayerBotItemShopCatalogue(dwNow);
			// The in-game line (apply.sh, index 70): the balance read first when the shop pass never needed it (a bot
			// with its whole look) - once a renewal, at most every PLAYERBOT_ELEMSTONE_RENEW_MS.
			if (!state.bDragonBalanceKnown && GetPlayerBotItemShopCheapest(ch, PLAYERBOT_ELEMSTONE_PROTECT_VNUM, false) != 0)
				RefreshPlayerBotDragonBalance(ch, state, dwNow);
			TPlayerBotItemShopWish wish;
			wish.dwVnum = PLAYERBOT_ELEMSTONE_PROTECT_VNUM;
			wish.bMarks = false;
			wish.szReason = "element_stone";
			if (CanPlayerBotAffordWish(ch, state, wish) && BuyPlayerBotItemShop(ch, state, wish, dwNow))
			{
				// The engine's purchase gives the goods (AutoGiveItem): the next look puts it on.
				++s_uPlayerBotElementStoneBought;
				sys_log(0, "PLAYERBOT_ELEMSTONE: bought pid=%u name=%s lv=%d coins_left=%d", ch->GetPlayerID(),
						ch->GetName(), ch->GetLevel(), state.iDragonCoins);
				es.dwNextLook = dwNow + PLAYERBOT_ELEMSTONE_RETRY_MS;
				return;
			}
		}
#else
		(void) state;
#endif
		LPITEM given = ch->AutoGiveItem(PLAYERBOT_ELEMSTONE_PROTECT_VNUM, 1, -1, false);
		if (!given)
		{
			PlayerBotLogThrottled("elemstone_give_failed", dwNow,
					"PLAYERBOT_ELEMSTONE: cannot renew pid=%u name=%s reason=no_item (is 39120 in item_proto?)",
					ch->GetPlayerID(), ch->GetName());
			return;
		}
		++s_uPlayerBotElementStoneGiven;
		sys_log(0, "PLAYERBOT_ELEMSTONE: given pid=%u name=%s lv=%d map=%ld ends=%ld", ch->GetPlayerID(), ch->GetName(),
				ch->GetLevel(), ch->GetMapIndex(), given->GetSocket(0));
		es.dwNextLook = dwNow + PLAYERBOT_ELEMSTONE_RETRY_MS;
	}

	void ManagePlayerBotElementStone(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || ch->IsDead() || !IsPlayerBotElementStoneMember(ch))
			return;
		TPlayerBotElementStoneState& es = s_mapPlayerBotElementStone[ch->GetPlayerID()];
		if (es.dwNextLook == 0)
			es.dwNextLook = dwNow + PlayerBotNavHash(ch->GetPlayerID() ^ 0x454c5354U) % PLAYERBOT_ELEMSTONE_INTERVAL_MS;
		if (dwNow < es.dwNextLook)
			return;
		es.dwNextLook = dwNow + PLAYERBOT_ELEMSTONE_INTERVAL_MS;
		es.dwSeen = dwNow;

		LPITEM worn = FindPlayerBotWornElementStone(ch);
		if (worn)
		{
			es.bStatus = worn->GetVnum() == PLAYERBOT_ELEMSTONE_PROTECT_VNUM ? PLAYERBOT_ELEMSTONE_WORN :
					PLAYERBOT_ELEMSTONE_WORN_POWER;
			return;
		}
		WORD cell = 0;
		LPITEM stone = FindPlayerBotBagElementStone(ch, cell);
		es.bStatus = stone ? PLAYERBOT_ELEMSTONE_BAG_ONLY : PLAYERBOT_ELEMSTONE_MISSING;
		if (IsPlayerBotGearFrozen(ch) || ch->GetExchange() || ch->GetMyShop() || !ch->CanHandleItem())
			return;
		if (!stone)
		{
			RenewPlayerBotElementStone(ch, state, es, dwNow);
			return;
		}
		if (!IsPlayerBotUniqueSwapWindowOpen(ch, state, dwNow))
		{
			es.dwNextLook = dwNow + PLAYERBOT_ELEMSTONE_RETRY_MS;
			return;
		}
		if (!PlayerBotCanEquipNow(ch, stone, TItemPos(INVENTORY, cell)))
			return;

		// A free slot, or the least useful unique's.
		LPITEM displaced = NULL;
		if (ch->GetWear(WEAR_UNIQUE1) && ch->GetWear(WEAR_UNIQUE2))
		{
			int best = -1;
			for (int wear = WEAR_UNIQUE1; wear <= WEAR_UNIQUE2; ++wear)
			{
				LPITEM w = ch->GetWear(wear);
				const int rank = GetPlayerBotElementStoneDisplaceRank(ch, w, wear);
				if (rank >= 0 && (best < 0 || rank < best))
				{
					best = rank;
					displaced = w;
				}
			}
			if (!displaced)
			{
				PlayerBotLogThrottled("elemstone_slots_held", dwNow,
						"PLAYERBOT_ELEMSTONE: cannot wear pid=%u name=%s reason=slots_held unique1=%u unique2=%u",
						ch->GetPlayerID(), ch->GetName(), ch->GetWear(WEAR_UNIQUE1)->GetVnum(),
						ch->GetWear(WEAR_UNIQUE2)->GetVnum());
				es.dwNextLook = dwNow + PLAYERBOT_ELEMSTONE_INTERVAL_MS * 10;
				return;
			}
			if (ch->GetEmptyInventory(displaced->GetSize()) < 0 || !ch->UnequipItem(displaced))
			{
				PlayerBotLogThrottled("elemstone_unequip", dwNow,
						"PLAYERBOT_ELEMSTONE: cannot wear pid=%u name=%s reason=unequip vnum=%u", ch->GetPlayerID(),
						ch->GetName(), displaced->GetVnum());
				return;
			}
		}
		const DWORD displacedVnum = displaced ? displaced->GetVnum() : 0;
		if (ch->EquipItem(stone))
		{
			++s_uPlayerBotElementStoneEquipped;
			if (displacedVnum)
				++s_uPlayerBotElementStoneReplaced;
			es.bStatus = PLAYERBOT_ELEMSTONE_WORN;
			sys_log(0, "PLAYERBOT_ELEMSTONE: on pid=%u name=%s lv=%d replaced=%u ends=%ld", ch->GetPlayerID(),
					ch->GetName(), ch->GetLevel(), displacedVnum, stone->GetSocket(0));
		}
		else
			es.dwNextLook = dwNow + PLAYERBOT_ELEMSTONE_RETRY_MS;
	}

	// Hourly: the members this core looked at in the last hour, by what they wear, and what the hour did.
	void WritePlayerBotElementStoneCensus(DWORD dwNow)
	{
		if (s_dwPlayerBotElementStoneCensus == 0)
		{
			s_dwPlayerBotElementStoneCensus = dwNow + PLAYERBOT_ELEMSTONE_CENSUS_MS;
			return;
		}
		if (dwNow < s_dwPlayerBotElementStoneCensus)
			return;
		s_dwPlayerBotElementStoneCensus = dwNow + PLAYERBOT_ELEMSTONE_CENSUS_MS;
		unsigned int count[4] = { 0, 0, 0, 0 };
		for (std::map<DWORD, TPlayerBotElementStoneState>::iterator it = s_mapPlayerBotElementStone.begin();
				it != s_mapPlayerBotElementStone.end();)
		{
			if (it->second.dwSeen == 0 || dwNow - it->second.dwSeen > PLAYERBOT_ELEMSTONE_CENSUS_MS)
			{
				s_mapPlayerBotElementStone.erase(it++);
				continue;
			}
			if (it->second.bStatus < 4)
				++count[it->second.bStatus];
			++it;
		}
		const unsigned int members = count[0] + count[1] + count[2] + count[3];
		if (members == 0 && s_uPlayerBotElementStoneBought + s_uPlayerBotElementStoneGiven == 0)
			return;
		sys_log(0, "PLAYERBOT_ELEMSTONE: census members=%u worn=%u worn_power=%u bag_only=%u missing=%u renewed=%u "
				"bought=%u given=%u equipped=%u replaced=%u",
				members, count[PLAYERBOT_ELEMSTONE_WORN], count[PLAYERBOT_ELEMSTONE_WORN_POWER],
				count[PLAYERBOT_ELEMSTONE_BAG_ONLY], count[PLAYERBOT_ELEMSTONE_MISSING],
				s_uPlayerBotElementStoneBought + s_uPlayerBotElementStoneGiven, s_uPlayerBotElementStoneBought,
				s_uPlayerBotElementStoneGiven, s_uPlayerBotElementStoneEquipped, s_uPlayerBotElementStoneReplaced);
		s_uPlayerBotElementStoneBought = s_uPlayerBotElementStoneGiven = 0;
		s_uPlayerBotElementStoneEquipped = s_uPlayerBotElementStoneReplaced = 0;
	}
}

#endif
