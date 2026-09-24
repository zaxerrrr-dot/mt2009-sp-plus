#ifndef __INC_METIN2_PLAYERBOT_ITEMSHOP_H__
#define __INC_METIN2_PLAYERBOT_ITEMSHOP_H__

// The bots and the ItemShop, on the 2.x line.
//
// mt2009 carries a shop of its own inside the game (CItemShopManager,
// common.itemshop_items, "/itemshop" from the client): a hundred and fifty
// lines priced in Dragon Coins - the account's `cash` - and in Dragon Marks -
// `cash_mark`, credited one for one for every coin spent. The coins come into
// the world as Kupon SM vouchers (80014-80018, a Metin stone's or a boss's
// drop by M2_DRAGON_COIN_*_PERMILLE), and until 2.0.60 a bot kept every one
// in its bag for good: ninety-seven of them on the test world after three
// days, and not one coin on any account. "Uzywanie wydropionych kuponow SM i
// przeznaczanie na potrzebne zakupy w itemshop" (Tieru, 16 September).
//
// What a bot does with the shop is what a careful player does with a small
// allowance. A voucher is cashed the moment it is found - the same charge the
// package's itemshop_manage quest makes for a player (AddCash through the db
// core, the itemshop_dragon_scroll row), without its dialog. The balance is
// kept in the state and read back from the account once an hour, because
// GetPlayerAccountBalance is a synchronous query. A purchase is the engine's
// own CItemShopManager::BuyItem behind the browse flag a client sets by
// opening the window: the level floor, the price, the account and the
// engine's purchase log are all its, and the goods arrive through
// AutoGiveItem. One purchase an hour a bot, and only what the bot's own rules
// would use: Kamien Duchowy for a Grand Master skill it can train, the change
// stone for a worn weapon whose lines the reroll pass would still reroll,
// with marks a Blessing Scroll for a piece under scroll work and the Dragon
// God's attack potions, and a hairstyle - one in four bots, once - because a
// crowd of a thousand identical heads is the thing a player notices first.
// MT2009 Plus (24 September 2026): the look is the whole of it now - every
// bot from level 30 with coins buys, in this order and one at a time, a
// costume, a hairstyle, a weapon skin for its weapon and a pet (no mount),
// wears them (the pet is summoned from its seal), and buys a piece again
// when its time runs out and the slot is empty.
// Nothing timed: every bot already holds the premium subscription for five
// years (SpawnBot, the operator's rule), so the VIP rings and the Przepustka
// Triumfu are worth nothing to it, and BuyItem refuses a VIP item to a
// subscriber anyway.
//
// r40250 has no such shop and this file is empty there: the tick calls the
// two functions below and gets nothing.
//
// An implementation fragment in the sense playerbot_types.h describes: include
// it exactly once, after playerbot_offline_shop.h (it asks
// PlayerBotWearsScrollWork of playerbot_town.h and the reroll rules of
// playerbot_bonus.h) and before playerbot_market.h.

#if defined(PLAYERBOT_ENGINE_MT2009)
#include "itemshop_manager.h"
#include "log.h"
#if defined(__PET_SYSTEM__)
#include "PetSystem.h"
#endif
#endif

namespace
{
#if defined(PLAYERBOT_ENGINE_MT2009)
	struct TPlayerBotItemShopEntry
	{
		DWORD dwIndex;
		DWORD dwPrice;
		DWORD dwCount;
		BYTE bMinLevel;
	};

	// The catalogue as the bots read it: the cheapest line per vnum for each
	// currency, and the hairstyles for sale. Rebuilt every hour from the
	// manager, which holds what the db core sent at boot - an operator who
	// edits common.itemshop_items restarts the world anyway.
	std::map<DWORD, TPlayerBotItemShopEntry> s_mapPlayerBotItemShopCoins;
	std::map<DWORD, TPlayerBotItemShopEntry> s_mapPlayerBotItemShopMarks;
	std::vector<DWORD> s_vecPlayerBotItemShopHair;
	// MT2009 Plus: the rest of a bot's look, for coins - costumes, weapon
	// skins and pet seals (PET_PAY); a pet with its own loot is left out, it
	// costs more and a bot's pet never loots (PetSystem.cpp).
	std::vector<DWORD> s_vecPlayerBotItemShopBody;
	std::vector<DWORD> s_vecPlayerBotItemShopWeaponSkin;
	std::vector<DWORD> s_vecPlayerBotItemShopPet;
	DWORD s_dwNextPlayerBotItemShopScan = 0;

	unsigned int s_uPlayerBotVouchersUsed = 0;
	unsigned int s_uPlayerBotCoinsCharged = 0;
	unsigned int s_uPlayerBotItemShopBuys = 0;
	unsigned int s_uPlayerBotItemShopRefusals = 0;
	// Looks that found a wish the balance could not pay for.
	unsigned int s_uPlayerBotItemShopSaving = 0;
	std::map<DWORD, unsigned int> s_mapPlayerBotItemShopBought;
	DWORD s_dwNextPlayerBotItemShopCensus = 0;

	void RefreshPlayerBotItemShopCatalogue(DWORD dwNow)
	{
		if (s_dwNextPlayerBotItemShopScan != 0 && dwNow < s_dwNextPlayerBotItemShopScan)
			return;
		s_dwNextPlayerBotItemShopScan = dwNow + PLAYERBOT_ISHOP_CATALOGUE_INTERVAL;
		s_mapPlayerBotItemShopCoins.clear();
		s_mapPlayerBotItemShopMarks.clear();
		s_vecPlayerBotItemShopHair.clear();
		s_vecPlayerBotItemShopBody.clear();
		s_vecPlayerBotItemShopWeaponSkin.clear();
		s_vecPlayerBotItemShopPet.clear();

		CItemShopManager& shop = CItemShopManager::instance();
		unsigned int entries = 0;
		for (int index = 1; index <= PLAYERBOT_ISHOP_MAX_INDEX; ++index)
		{
			if (!shop.IsItemExist(index))
				continue;
			TItemShopItem item = shop.GetItem(index);
			if (!shop.IsProperItem(item) || item.dwCount == 0 || shop.IsItemTimeAuction(item))
				continue;
			const TItemTable* proto = ITEM_MANAGER::instance().GetTable(item.dwVnum);
			if (!proto)
				continue;
			++entries;
			TPlayerBotItemShopEntry entry;
			entry.dwIndex = item.dwIndex;
			entry.dwPrice = shop.GetItemPrice(item);
			entry.dwCount = item.dwCount;
			entry.bMinLevel = item.bMinLevel;
			const bool marks = shop.GetItemCurrency(item) == CItemShopManager::CURRENCY_DRAGON_MARK;
			std::map<DWORD, TPlayerBotItemShopEntry>& table = marks ? s_mapPlayerBotItemShopMarks : s_mapPlayerBotItemShopCoins;
			std::map<DWORD, TPlayerBotItemShopEntry>::iterator it = table.find(item.dwVnum);
			// The cheapest unit: "Zaczarowanie x4 for 207" beats "x1 for 69"
			// only when the bot can afford four, and it buys one at a time.
			if (it == table.end() || entry.dwPrice * it->second.dwCount < it->second.dwPrice * entry.dwCount)
				table[item.dwVnum] = entry;
			if (!marks && proto->bType == ITEM_COSTUME && proto->bSubType == COSTUME_HAIR)
				s_vecPlayerBotItemShopHair.push_back(item.dwVnum);
			if (!marks && proto->bType == ITEM_COSTUME && proto->bSubType == COSTUME_BODY)
				s_vecPlayerBotItemShopBody.push_back(item.dwVnum);
			if (!marks && proto->bType == ITEM_COSTUME && proto->bSubType == COSTUME_WEAPON)
				s_vecPlayerBotItemShopWeaponSkin.push_back(item.dwVnum);
			if (!marks && proto->bType == ITEM_PET && proto->bSubType == PET_PAY && proto->alValues[0] != 0 &&
					proto->alValues[2] == 0)
				s_vecPlayerBotItemShopPet.push_back(item.dwVnum);
		}
		if (entries == 0)
		{
			// The db core has not sent the catalogue yet: ask again soon.
			s_dwNextPlayerBotItemShopScan = dwNow + 5 * 60 * 1000;
			return;
		}
		sys_log(0, "PLAYERBOT_ISHOP: catalogue entries=%u coins=%u marks=%u hairstyles=%u costumes=%u weapon_skins=%u pets=%u",
				entries, (unsigned int)s_mapPlayerBotItemShopCoins.size(),
				(unsigned int)s_mapPlayerBotItemShopMarks.size(), (unsigned int)s_vecPlayerBotItemShopHair.size(),
				(unsigned int)s_vecPlayerBotItemShopBody.size(), (unsigned int)s_vecPlayerBotItemShopWeaponSkin.size(),
				(unsigned int)s_vecPlayerBotItemShopPet.size());
	}

	void RefreshPlayerBotDragonBalance(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		const CItemShopManager::PlayerAccountBalance balance = CItemShopManager::instance().GetPlayerAccountBalance(ch);
		state.iDragonCoins = (int)std::min<DWORD>(balance.dwDragonCoins, INT_MAX);
		state.iDragonMarks = (int)std::min<DWORD>(balance.dwDragonMarks, INT_MAX);
		state.bDragonBalanceKnown = true;
		state.dwNextItemShopBalanceTime = dwNow + PLAYERBOT_ISHOP_BALANCE_INTERVAL;
	}

	LPITEM FindPlayerBotVoucher(LPCHARACTER ch)
	{
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && !item->isLocked() && !item->IsExchanging() &&
					item->GetVnum() >= PLAYERBOT_ISHOP_VOUCHER_MIN_VNUM &&
					item->GetVnum() <= PLAYERBOT_ISHOP_VOUCHER_MAX_VNUM)
				return item;
		}
		return NULL;
	}

	// One voucher a pass, the way the package's quest cashes one for a player:
	// the charge goes through the db core (ChargeCash: cash += value), the row
	// in itemshop_dragon_scroll is the same, and the voucher goes. The quest
	// itself is not run - item.remove() there takes the whole stack for one
	// charge, and a dialog-free UseItem would still cost the bot the flag the
	// quest checks; the flag is honoured here.
	bool UsePlayerBotVoucher(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		LPITEM voucher = FindPlayerBotVoucher(ch);
		if (!voucher)
			return false;
		if (quest::CQuestManager::instance().GetEventFlag("block_dragon_voucher") > 0)
			return false;
		const int value = voucher->GetValue(0);
		if (value <= 0)
			return false;
		const DWORD id = voucher->GetID();
		if (!CItemShopManager::instance().AddCash(ch, ERequestCharge_Cash, value, false))
			return false;
		LogManager::instance().Query("INSERT INTO itemshop_dragon_scroll VALUES (%u, %u, NOW(), %u, %d)",
				ch->GetPlayerID(), ch->GetDesc()->GetAccountTable().id, id, value);
		if (voucher->GetCount() > 1)
			voucher->SetCount(voucher->GetCount() - 1);
		else
			ITEM_MANAGER::instance().RemoveItem(voucher, "PLAYERBOT_VOUCHER");
		state.iDragonCoins += value;
		++s_uPlayerBotVouchersUsed;
		s_uPlayerBotCoinsCharged += (unsigned int)value;
		sys_log(0, "PLAYERBOT_ISHOP: voucher cashed pid=%u name=%s coins=%d balance=%d",
				ch->GetPlayerID(), ch->GetName(), value, state.iDragonCoins);
		return true;
	}

	// --------------------------------------------------------------- wishes

	struct TPlayerBotItemShopWish
	{
		DWORD dwVnum;
		bool bMarks;
		const char* szReason;
	};

	// A Grand Master skill the training pass could train now, and no stone.
	bool PlayerBotWantsGrandMasterStone(LPCHARACTER ch)
	{
		if (ch->GetSkillGroup() == 0)
			return false;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetVnum() == PLAYERBOT_GRAND_MASTER_STONE_VNUM)
				return false;
		}
		const TJobSkillBuild build = GetPlayerBotSkillBuild(ch->GetJob(), ch->GetSkillGroup(), ch->GetPlayerID());
		for (BYTE i = 0; i < build.bSkillCount; ++i)
		{
			const DWORD vnum = build.dwSkills[i];
			if (vnum == 0 || ch->GetSkillMasterType(vnum) != SKILL_GRAND_MASTER)
				continue;
			const int level = ch->GetSkillLevel(vnum);
			if (level < 30 || level >= 40)
				continue;
			const int cost = 1000 + 500 * (level - 30);
			if (ch->GetRealAlignment() - cost >= 0)
				return true;
		}
		return false;
	}

	// The worn weapon the reroll pass would reroll if it had a stone, and no
	// stone in the bag: the same tests ManagePlayerBotBonusReroll makes.
	bool PlayerBotWantsChangeStone(LPCHARACTER ch)
	{
		if (ch->GetLevel() < PLAYERBOT_BONUS_MIN_LEVEL)
			return false;
		LPITEM weapon = ch->GetWear(WEAR_WEAPON);
		if (!CanPlayerBotRerollItem(weapon))
			return false;
		if (weapon->GetAttributeCount() < PLAYERBOT_BONUS_MAX_LINES ||
				weapon->GetRefineLevel() < PLAYERBOT_BONUS_CHANGE_MIN_REFINE)
			return false;
		if (HasPlayerBotFinishedBonus(ch, weapon, WEAR_WEAPON))
			return false;
		if (ScorePlayerBotItemBonuses(ch, weapon, WEAR_WEAPON) >= PLAYERBOT_BONUS_KEEP_SCORE &&
				!IsPlayerBotSpecialLevel30WeaponVnum(weapon->GetVnum()))
			return false;
		return !HasPlayerBotBonusStone(ch, PLAYERBOT_BONUS_CHANGE_VNUM);
	}

	bool PlayerBotHoldsBooster(LPCHARACTER ch)
	{
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && IsPlayerBotBoosterItem(item))
				return true;
		}
		return false;
	}

	// ------------------------------------------------------------- the look

	// MT2009 Plus (operator, 24 September 2026): a bot with Dragon Coins
	// dresses itself from the ItemShop - costume, then hairstyle, then weapon
	// skin, then pet - one piece at a time, and wears what it bought. Every bot
	// from PLAYERBOT_ISHOP_LOOK_MIN_LEVEL, not one in four once as the
	// hairstyle alone was: a piece that runs out (REAL_TIME) leaves its slot
	// empty, and the next look buys the missing piece again.

	// A weapon skin goes on only over a real weapon of its own kind: the engine
	// compares the skin's value3 with the weapon's subtype (CanEquipNow).
	bool IsPlayerBotWeaponSkinFor(LPCHARACTER ch, const TItemTable* proto)
	{
		if (!proto || proto->bType != ITEM_COSTUME || proto->bSubType != COSTUME_WEAPON ||
				!IsPlayerBotProtoForCharacter(ch, proto))
			return false;
		LPITEM weapon = ch->GetWear(WEAR_WEAPON);
		return weapon && weapon->GetType() == ITEM_WEAPON && proto->alValues[3] == (long)weapon->GetSubType();
	}

	// A piece whose level limit the bot has not reached would wait in the bag
	// for good, and a piece in the bag counts as had: never bought, never worn.
	bool IsPlayerBotLookLevelReached(LPCHARACTER ch, const TItemTable* proto)
	{
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
			if (proto->aLimits[i].bType == LIMIT_LEVEL && (long)ch->GetLevel() < proto->aLimits[i].lValue)
				return false;
		return true;
	}

	// Would this bot put the item on (or summon it) for the given piece?
	bool IsPlayerBotOwnLook(LPCHARACTER ch, const TItemTable* proto, int look)
	{
		if (!proto || !IsPlayerBotLookLevelReached(ch, proto))
			return false;
		switch (look)
		{
			case PLAYERBOT_ISHOP_LOOK_BODY:
				return proto->bType == ITEM_COSTUME && proto->bSubType == COSTUME_BODY &&
						IsPlayerBotProtoForCharacter(ch, proto);
			case PLAYERBOT_ISHOP_LOOK_HAIR:
				return proto->bType == ITEM_COSTUME && proto->bSubType == COSTUME_HAIR &&
						IsPlayerBotProtoForCharacter(ch, proto);
			case PLAYERBOT_ISHOP_LOOK_WEAPON:
				return IsPlayerBotWeaponSkinFor(ch, proto);
			case PLAYERBOT_ISHOP_LOOK_PET:
				return proto->bType == ITEM_PET && proto->bSubType == PET_PAY && proto->alValues[0] != 0;
		}
		return false;
	}

	bool IsPlayerBotPetSummoned(LPCHARACTER ch)
	{
#if defined(__PET_SYSTEM__)
		return ch->GetPetSystem() && ch->GetPetSystem()->CountSummoned() > 0;
#else
		return false;
#endif
	}

	// The piece is worn (summoned), or on its way: bought and in the bag.
	bool PlayerBotHasLook(LPCHARACTER ch, int look)
	{
		switch (look)
		{
			case PLAYERBOT_ISHOP_LOOK_BODY:
				if (ch->GetWear(WEAR_COSTUME_BODY))
					return true;
				break;
			case PLAYERBOT_ISHOP_LOOK_HAIR:
				if (ch->GetWear(WEAR_COSTUME_HAIR))
					return true;
				break;
			case PLAYERBOT_ISHOP_LOOK_WEAPON:
			{
				if (ch->GetWear(WEAR_COSTUME_WEAPON))
					return true;
				// No real weapon to dress: nothing to buy for now.
				LPITEM weapon = ch->GetWear(WEAR_WEAPON);
				if (!weapon || weapon->GetType() != ITEM_WEAPON)
					return true;
				break;
			}
			case PLAYERBOT_ISHOP_LOOK_PET:
				if (IsPlayerBotPetSummoned(ch))
					return true;
				break;
		}
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && IsPlayerBotOwnLook(ch, item->GetProto(), look))
				return true;
		}
		return false;
	}

	const std::vector<DWORD>& GetPlayerBotLookCatalogue(int look)
	{
		switch (look)
		{
			case PLAYERBOT_ISHOP_LOOK_BODY: return s_vecPlayerBotItemShopBody;
			case PLAYERBOT_ISHOP_LOOK_HAIR: return s_vecPlayerBotItemShopHair;
			case PLAYERBOT_ISHOP_LOOK_WEAPON: return s_vecPlayerBotItemShopWeaponSkin;
			default: return s_vecPlayerBotItemShopPet;
		}
	}

	const char* GetPlayerBotLookReason(int look)
	{
		switch (look)
		{
			case PLAYERBOT_ISHOP_LOOK_BODY: return "look_costume";
			case PLAYERBOT_ISHOP_LOOK_HAIR: return "hairstyle";
			case PLAYERBOT_ISHOP_LOOK_WEAPON: return "look_weapon_skin";
			default: return "look_pet";
		}
	}

	// The first piece missing, in the operator's order; 0 when the bot is
	// dressed or its piece is not for sale. The strict order is the point: a
	// bot saves for the costume before it spends on a hairstyle. Which item
	// of the kind is drawn at random among those the bot can wear.
	DWORD PickPlayerBotLook(LPCHARACTER ch, int* pLook)
	{
		if (ch->GetLevel() < PLAYERBOT_ISHOP_LOOK_MIN_LEVEL)
			return 0;
		for (int look = 0; look < PLAYERBOT_ISHOP_LOOK_COUNT; ++look)
		{
			if (PlayerBotHasLook(ch, look))
				continue;
			const std::vector<DWORD>& catalogue = GetPlayerBotLookCatalogue(look);
			std::vector<DWORD> mine;
			for (size_t i = 0; i < catalogue.size(); ++i)
				if (IsPlayerBotOwnLook(ch, ITEM_MANAGER::instance().GetTable(catalogue[i]), look))
					mine.push_back(catalogue[i]);
			if (mine.empty())
				continue;
			*pLook = look;
			// Any of them, drawn anew each time (operator: variety), so a
			// piece that runs out is followed by another.
			return mine[number(0, (int)mine.size() - 1)];
		}
		return 0;
	}

	// A head for the counter (PLAYERBOT_ISHOP_HAIR_TRADE_SHARE): one this bot
	// cannot wear, so the pass that dresses it never takes it, bought by a
	// keeper with a stand and none on the way already - in the bag or on the
	// counter.
	DWORD PickPlayerBotHairstyleForCounter(LPCHARACTER ch)
	{
		if (!ch || s_vecPlayerBotItemShopHair.empty() || !PlayerBotCanOpenShop(ch) ||
				(PlayerBotNavHash(ch->GetPlayerID() ^ 0x48545244U) % PLAYERBOT_ISHOP_HAIR_TRADE_SHARE) != 0)
			return 0;
#if defined(ENABLE_IKASHOP_RENEWAL)
		auto shop = ikashop::GetManager().GetShopByOwnerID(ch->GetPlayerID());
		if (!shop)
			return 0;
		for (const auto& [id, line] : shop->GetItems())
			if (line && line->GetTable() && line->GetTable()->bType == ITEM_COSTUME &&
					line->GetTable()->bSubType == COSTUME_HAIR)
				return 0;
#endif
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetType() == ITEM_COSTUME && item->GetSubType() == COSTUME_HAIR &&
					!item->CanUsedBy(ch))
				return 0;
		}
		std::vector<DWORD> others;
		for (size_t i = 0; i < s_vecPlayerBotItemShopHair.size(); ++i)
		{
			const TItemTable* proto = ITEM_MANAGER::instance().GetTable(s_vecPlayerBotItemShopHair[i]);
			if (proto && !IsPlayerBotProtoForCharacter(ch, proto))
				others.push_back(s_vecPlayerBotItemShopHair[i]);
		}
		if (others.empty())
			return 0;
		return others[PlayerBotNavHash(ch->GetPlayerID() ^ (DWORD)(get_global_time() / 3600)) % others.size()];
	}

	// Every wish the bot has, in the order it would spend on them. The buyer
	// takes the first it can afford: the first build picked one wish only,
	// and a bot with no marks whose first wish was the marks' Blessing Scroll
	// never got as far as the hairstyle its coins would have bought.
	const int PLAYERBOT_ISHOP_MAX_WISHES = 5;

	int CollectPlayerBotItemShopWishes(LPCHARACTER ch, const TPlayerBotAIState& state, TPlayerBotItemShopWish* wishes)
	{
		int n = 0;
		if (PlayerBotWantsGrandMasterStone(ch))
		{
			wishes[n].dwVnum = PLAYERBOT_GRAND_MASTER_STONE_VNUM;
			wishes[n].bMarks = false;
			wishes[n++].szReason = "grand_master_stone";
		}
		if (PlayerBotWantsChangeStone(ch))
		{
			wishes[n].dwVnum = PLAYERBOT_BONUS_CHANGE_VNUM;
			wishes[n].bMarks = false;
			wishes[n++].szReason = "change_stone";
		}
		if (PlayerBotWearsScrollWork(ch) && CountPlayerBotSafeRefineScrolls(ch) == 0 &&
				s_mapPlayerBotItemShopMarks.find(PLAYERBOT_ISHOP_BLESSING_SCROLL_VNUM) != s_mapPlayerBotItemShopMarks.end())
		{
			wishes[n].dwVnum = PLAYERBOT_ISHOP_BLESSING_SCROLL_VNUM;
			wishes[n].bMarks = true;
			wishes[n++].szReason = "blessing_scroll";
		}
		if (!PlayerBotHoldsBooster(ch) &&
				s_mapPlayerBotItemShopMarks.find(PLAYERBOT_ISHOP_ATTACK_POTION_VNUM) != s_mapPlayerBotItemShopMarks.end())
		{
			wishes[n].dwVnum = PLAYERBOT_ISHOP_ATTACK_POTION_VNUM;
			wishes[n].bMarks = true;
			wishes[n++].szReason = "attack_potion";
		}
		int look = 0;
		const DWORD lookVnum = PickPlayerBotLook(ch, &look);
		if (lookVnum != 0)
		{
			wishes[n].dwVnum = lookVnum;
			wishes[n].bMarks = false;
			wishes[n++].szReason = GetPlayerBotLookReason(look);
		}
		// Its own come first; a head for the counter only when nothing else
		// is wanted, or the coins saved for a Kamien Duchowy would go on it.
		if (n == 0)
		{
			const DWORD stock = PickPlayerBotHairstyleForCounter(ch);
			if (stock != 0)
			{
				wishes[n].dwVnum = stock;
				wishes[n].bMarks = false;
				wishes[n++].szReason = "counter_hairstyle";
			}
		}
		return n;
	}

	const TPlayerBotItemShopEntry* FindPlayerBotItemShopEntry(const TPlayerBotItemShopWish& wish)
	{
		const std::map<DWORD, TPlayerBotItemShopEntry>& table = wish.bMarks ? s_mapPlayerBotItemShopMarks : s_mapPlayerBotItemShopCoins;
		std::map<DWORD, TPlayerBotItemShopEntry>::const_iterator it = table.find(wish.dwVnum);
		return it == table.end() ? NULL : &it->second;
	}

	bool CanPlayerBotAffordWish(LPCHARACTER ch, const TPlayerBotAIState& state, const TPlayerBotItemShopWish& wish)
	{
		const TPlayerBotItemShopEntry* entry = FindPlayerBotItemShopEntry(wish);
		if (!entry || ch->GetLevel() < entry->bMinLevel)
			return false;
		const int have = wish.bMarks ? state.iDragonMarks : state.iDragonCoins;
		return have >= (int)entry->dwPrice;
	}

	// ------------------------------------------------------------- purchase

	// A bought piece goes on when the engine lets it: EquipItem refuses within
	// a second and a half of a blow or a cast, and the bot bought it mid-hunt,
	// so the pass asks again on every look while a slot is empty and its piece
	// waits in the bag. A pet seal is used once no pet is out: using it again
	// would send the pet away (CHARACTER::SummonPetFromItem is a toggle).
	void WearPlayerBotBoughtLook(LPCHARACTER ch, TPlayerBotAIState& state)
	{
		static const BYTE s_abWear[PLAYERBOT_ISHOP_LOOK_PET] = { WEAR_COSTUME_BODY, WEAR_COSTUME_HAIR, WEAR_COSTUME_WEAPON };
		for (int look = 0; look < PLAYERBOT_ISHOP_LOOK_COUNT; ++look)
		{
			if (look == PLAYERBOT_ISHOP_LOOK_PET ? IsPlayerBotPetSummoned(ch) : ch->GetWear(s_abWear[look]) != NULL)
				continue;
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				if (!item || item->isLocked() || item->IsExchanging() || !item->CanUsedBy(ch) ||
						!IsPlayerBotOwnLook(ch, item->GetProto(), look))
					continue;
				if (look == PLAYERBOT_ISHOP_LOOK_HAIR)
					state.bBoughtHairstyle = true;
				if (look == PLAYERBOT_ISHOP_LOOK_PET)
				{
#if defined(__PET_SYSTEM__) && defined(USE_PET_SEAL_ON_LOGIN)
					if (ch->GetPetSystem() && ch->SummonPetFromItem(item) && IsPlayerBotPetSummoned(ch))
						sys_log(0, "PLAYERBOT_ISHOP: pet out pid=%u name=%s vnum=%u",
								ch->GetPlayerID(), ch->GetName(), item->GetVnum());
#endif
				}
				else if (ch->EquipItem(item))
					sys_log(0, "PLAYERBOT_ISHOP: %s on pid=%u name=%s vnum=%u", GetPlayerBotLookReason(look),
							ch->GetPlayerID(), ch->GetName(), item->GetVnum());
				break;
			}
		}
	}

	// The engine's own purchase, as a client makes it: the browse flag the
	// window sets, BuyItem (level, price, the account's balance read back, the
	// charge through the db core, AutoGiveItem, the purchase log), the flag off
	// on the same tick so IsBusy does not hold the rest of the tick.
	bool BuyPlayerBotItemShop(LPCHARACTER ch, TPlayerBotAIState& state, const TPlayerBotItemShopWish& wish, DWORD dwNow)
	{
		const TPlayerBotItemShopEntry* pEntry = FindPlayerBotItemShopEntry(wish);
		if (!pEntry || !CanPlayerBotAffordWish(ch, state, wish))
			return false;
		const TPlayerBotItemShopEntry& entry = *pEntry;
		if (!ch->HasPlayerData() || ch->IsBusy() || !ch->CanHandleItem() || !ch->HasSlotForItem(wish.dwVnum))
		{
			PlayerBotLogThrottled("ishop_not_now", dwNow,
					"PLAYERBOT_ISHOP: cannot buy now pid=%u name=%s vnum=%u reason=%s busy=%d handle=%d slot=%d",
					ch->GetPlayerID(), ch->GetName(), wish.dwVnum, wish.szReason, (int)ch->IsBusy(),
					(int)ch->CanHandleItem(), (int)ch->HasSlotForItem(wish.dwVnum));
			return false;
		}

		ch->playerData->SetItemShopBrowse(true);
		const bool bought = CItemShopManager::instance().BuyItem(ch, (int)entry.dwIndex, 1);
		ch->playerData->SetItemShopBrowse(false);
		state.dwNextItemShopBuyTime = dwNow + PLAYERBOT_ISHOP_BUY_INTERVAL;
		if (!bought)
		{
			++s_uPlayerBotItemShopRefusals;
			// The balance the engine read may not be the one kept here.
			state.bDragonBalanceKnown = false;
			PlayerBotLogThrottled("ishop_refused", dwNow,
					"PLAYERBOT_ISHOP: purchase refused pid=%u name=%s vnum=%u index=%u price=%u %s reason=%s",
					ch->GetPlayerID(), ch->GetName(), wish.dwVnum, entry.dwIndex, entry.dwPrice,
					wish.bMarks ? "marks" : "coins", wish.szReason);
			return false;
		}
		if (wish.bMarks)
			state.iDragonMarks -= (int)entry.dwPrice;
		else
		{
			state.iDragonCoins -= (int)entry.dwPrice;
			state.iDragonMarks += (int)entry.dwPrice;
		}
		++s_uPlayerBotItemShopBuys;
		++s_mapPlayerBotItemShopBought[wish.dwVnum];
		sys_log(0, "PLAYERBOT_ISHOP: bought pid=%u name=%s vnum=%u x%u index=%u price=%u %s reason=%s coins_left=%d marks_left=%d",
				ch->GetPlayerID(), ch->GetName(), wish.dwVnum, entry.dwCount, entry.dwIndex, entry.dwPrice,
				wish.bMarks ? "marks" : "coins", wish.szReason, state.iDragonCoins, state.iDragonMarks);
		WearPlayerBotBoughtLook(ch, state);
		return true;
	}

	// ----------------------------------------------------------------- tick

	bool IsPlayerBotLookReason(const char* szReason)
	{
		for (int look = 0; look < PLAYERBOT_ISHOP_LOOK_COUNT; ++look)
			if (szReason && strcmp(szReason, GetPlayerBotLookReason(look)) == 0)
				return true;
		return false;
	}

	// After a purchase: another piece missing and the coins for it, and the
	// bot comes back in a few seconds instead of an hour.
	void ContinuePlayerBotLookSession(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		int look = 0;
		TPlayerBotItemShopWish next;
		next.dwVnum = PickPlayerBotLook(ch, &look);
		next.bMarks = false;
		next.szReason = GetPlayerBotLookReason(look);
		if (next.dwVnum == 0 || !CanPlayerBotAffordWish(ch, state, next))
			return;
		state.bItemShopLookSession = true;
		state.dwNextItemShopBuyTime = dwNow + PLAYERBOT_ISHOP_SESSION_STEP;
		state.dwNextItemShopCheckTime = dwNow + PLAYERBOT_ISHOP_SESSION_STEP;
	}

	// Upkeep, never the tick's owner: a voucher cashed, a purchase made, and
	// the rest of the tick goes on. Every ten minutes a bot; the account is
	// asked for its balance only when the bot wants something.
	void ManagePlayerBotItemShop(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || ch->IsDead() || !ch->GetDesc())
			return;
		if (dwNow < state.dwNextItemShopCheckTime)
			return;
		state.dwNextItemShopCheckTime = dwNow + PLAYERBOT_ISHOP_CHECK_INTERVAL +
				PlayerBotNavHash(ch->GetPlayerID() ^ 0x49534850U) % 60000U;
		if (!IsPlayerBotItemShopEnabled())
			return;
		if (ch->IsBusy() || ch->GetMyShop() || ch->GetExchange())
			return;
		RefreshPlayerBotItemShopCatalogue(dwNow);
		WearPlayerBotBoughtLook(ch, state);

		const bool voucher = FindPlayerBotVoucher(ch) != NULL;
		TPlayerBotItemShopWish wishes[PLAYERBOT_ISHOP_MAX_WISHES];
		const int wants = CollectPlayerBotItemShopWishes(ch, state, wishes);
		if (!voucher && wants == 0)
			return;
		// The account is read before a voucher is cashed, never after: the
		// charge is a round trip through the db core, and a read on its heels
		// would put the old balance back over the coins just added.
		if (!state.bDragonBalanceKnown || dwNow >= state.dwNextItemShopBalanceTime)
			RefreshPlayerBotDragonBalance(ch, state, dwNow);
		// And a purchase waits for the next look for the same reason: BuyItem
		// reads the account itself.
		if (voucher && UsePlayerBotVoucher(ch, state, dwNow))
			return;
		if (dwNow < state.dwNextItemShopBuyTime)
			return;
		// Within a session only the look is bought: a stone the bot still
		// wants after buying one would be bought again every few seconds.
		const bool session = state.bItemShopLookSession;
		state.bItemShopLookSession = false;
		for (int i = 0; i < wants; ++i)
		{
			if (session && !IsPlayerBotLookReason(wishes[i].szReason))
				continue;
			if (!CanPlayerBotAffordWish(ch, state, wishes[i]))
				continue;
			if (BuyPlayerBotItemShop(ch, state, wishes[i], dwNow))
				ContinuePlayerBotLookSession(ch, state, dwNow);
			return;
		}
		if (!session)
			++s_uPlayerBotItemShopSaving;
	}

	void WritePlayerBotItemShopCensus(DWORD dwNow)
	{
		if (s_dwNextPlayerBotItemShopCensus != 0 && dwNow < s_dwNextPlayerBotItemShopCensus)
			return;
		s_dwNextPlayerBotItemShopCensus = dwNow + PLAYERBOT_ISHOP_CENSUS_INTERVAL;
		if (s_uPlayerBotVouchersUsed == 0 && s_uPlayerBotItemShopBuys == 0 && s_uPlayerBotItemShopRefusals == 0 &&
				s_uPlayerBotItemShopSaving == 0)
			return;
		std::string bought;
		char buf[48];
		for (std::map<DWORD, unsigned int>::const_iterator it = s_mapPlayerBotItemShopBought.begin();
				it != s_mapPlayerBotItemShopBought.end(); ++it)
		{
			snprintf(buf, sizeof(buf), "%s%u:%u", bought.empty() ? "" : ",", it->first, it->second);
			bought += buf;
		}
		sys_log(0, "PLAYERBOT_ISHOP: census vouchers=%u coins=%u purchases=%u refused=%u saving_looks=%u bought=%s",
				s_uPlayerBotVouchersUsed, s_uPlayerBotCoinsCharged, s_uPlayerBotItemShopBuys,
				s_uPlayerBotItemShopRefusals, s_uPlayerBotItemShopSaving, bought.empty() ? "-" : bought.c_str());
	}
#else
	void ManagePlayerBotItemShop(LPCHARACTER, TPlayerBotAIState&, DWORD)
	{
	}

	void WritePlayerBotItemShopCensus(DWORD)
	{
	}
#endif
}

#endif
