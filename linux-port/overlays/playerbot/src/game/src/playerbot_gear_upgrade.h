#ifndef __INC_METIN2_PLAYERBOT_GEAR_UPGRADE_H__
#define __INC_METIN2_PLAYERBOT_GEAR_UPGRADE_H__

// MT2009_PLUS_BOT_GEAR_UPGRADE_V1: a bot plays for the hardest blow it can
// buy. "Boty niech kupuja lepsze bronie i daza do tego aby miec jak
// najwieksze obrazenia. Jesli tylko dana bron jest dostepna na rynku, to ja
// kupuja i ulepszaja" (the owner, 5 October), after the dungeon runs of the
// test world showed bots of 75 to 79 swinging a weapon of level 48 on
// average, 122 of 160 a weapon more than twenty levels under them, and a
// Shaman in a dungeon with a pickaxe in its hand.
//
// What the counters held that day: 30 765 weapons on the bots' stands, 18 000
// of them of level 40 and up, 16 100 of those at +4 and 31 at +6 or more. The
// market's gear rule bought a finished piece only (+6 and a grade over the
// one worn - Iwakura's Patch 4, point 2), which is right for armour bought to
// be worn as it is and wrong for a weapon two tiers above the hand: none of
// the sixteen thousand was ever a candidate, and the weapon goal
// (playerbot_weapon_goal.h) sent bots to the market for a weapon the market
// then refused to sell them. Under the old rule 76 of the 1539 bots of 40 and
// up could pay for any line that beat their weapon by a tenth; under this one
// 334 can, from the same counters and the same purses.
//
// The rule: a counter weapon at any plus the bot can wear now, whose blow by
// the damage model (GetPlayerBotWeaponHitDamage - the dice, the plus, the
// level bonus, the lines) beats the best weapon it owns by
// PLAYERBOT_WEAPON_UPGRADE_MIN_GAIN_PERCENT, and which the equipment pass will
// put on (its score over the hand's). It is the blow the weapon has now, not
// the one it might reach: what is bought goes on at once, and the anvil takes
// it on from there (GetPlayerBotRefineTarget: the weapon in the hand climbs to
// the bot's aim, +6 at least). Paid from half of what the bot holds over the
// floor, or four fifths of it for a gain of a quarter or more - one weapon at
// a time, since the next one has to beat this one by a tenth again.
//
// Also here: the village merchant's best weapon for a bot under 36 whose
// ladder names a tier the merchant does not stock (the ladder's piece for a
// bot of 20 to 24 is the level-20 one, which no merchant sells, so the bots of
// 20 kept the level-one sword +6), and the tool guard - a rod, a pickaxe or
// a herbalist's knife never stays in the hand outside its own session.
//
// Included after playerbot_herbalism.h (the tool sessions) and before
// playerbot_economy.h, playerbot_progression_needs.h and playerbot_market.h,
// which ask it.
namespace
{
	// The best weapon this bot owns that it could fight with now - the one in
	// the hand when it is a weapon of its kind, else the best of the bag - by
	// blow and by the equipment score the equipment pass ranks with.
	struct TPlayerBotOwnedWeapon
	{
		LPITEM item;
		long long blow;
		long long score;
		int subType;

		TPlayerBotOwnedWeapon() : item(NULL), blow(0), score(0), subType(-1)
		{
		}
	};

	TPlayerBotOwnedWeapon ReadPlayerBotBestOwnedWeapon(LPCHARACTER ch)
	{
		TPlayerBotOwnedWeapon best;
		if (!ch || !ch->IsItemLoaded())
			return best;
		LPITEM worn = ch->GetWear(WEAR_WEAPON);
		if (worn && worn->GetType() == ITEM_WEAPON && IsPlayerBotWeapon(ch, worn))
		{
			best.item = worn;
			best.blow = GetPlayerBotWeaponHitDamage(worn, ch);
			best.score = GetPlayerBotEquipmentScore(worn, ch);
		}
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || item->IsEquipped() || item->GetType() != ITEM_WEAPON ||
					!IsPlayerBotEquipmentCandidate(ch, item) || item->GetLevelLimit() > ch->GetLevel() ||
					item->FindEquipCell(ch) != WEAR_WEAPON)
				continue;
			const long long blow = GetPlayerBotWeaponHitDamage(item, ch);
			if (best.item && blow <= best.blow)
				continue;
			best.item = item;
			best.blow = blow;
			best.score = GetPlayerBotEquipmentScore(item, ch);
		}
		best.subType = best.item ? (int)best.item->GetSubType() : -1;
		return best;
	}

	// The gain of a blow over the best weapon owned, in percent; a bot with no
	// weapon at all gains everything.
	long long GetPlayerBotWeaponGainPercent(long long blow, long long ownedBlow)
	{
		if (ownedBlow <= 0)
			return 1000;
		return blow * 100 / ownedBlow - 100;
	}

	// What a weapon upgrade with this gain may cost: a share of what the bot
	// holds over its reserve and PLAYERBOT_WEAPON_UPGRADE_GOLD_FLOOR.
	long long GetPlayerBotWeaponUpgradeBudget(LPCHARACTER ch, long long gainPercent)
	{
		if (!ch)
			return 0;
		const long long spare = (long long)ch->GetGold() - (long long)GetPlayerBotReservedGold(ch) -
				PLAYERBOT_WEAPON_UPGRADE_GOLD_FLOOR;
		if (spare <= 0)
			return 0;
		return spare * (gainPercent >= PLAYERBOT_WEAPON_UPGRADE_BIG_GAIN_PERCENT
				? PLAYERBOT_WEAPON_UPGRADE_BIG_BUDGET_PERCENT : PLAYERBOT_WEAPON_UPGRADE_SMALL_BUDGET_PERCENT) / 100;
	}

	// A weapon nobody holds yet, by its proto, that this bot could carry now:
	// its kind, its class and sex, a level it has reached and not one of the
	// tenth level or under in the hand of a bot of thirty.
	bool IsPlayerBotWeaponProtoFor(LPCHARACTER ch, const TItemTable* proto)
	{
		if (!ch || !proto || proto->bType != ITEM_WEAPON || proto->bSubType == WEAPON_ARROW ||
				!IsPlayerBotWeaponSubTypeFor(ch, proto->bSubType) || !IsPlayerBotProtoForCharacter(ch, proto))
			return false;
		const int level = GetPlayerBotProtoLevelLimit(proto);
		return level <= (int)ch->GetLevel() &&
				!playerbot_refine_rules::IsLowWeaponFor((int)ch->GetLevel(), level);
	}

	// A counter weapon this bot should buy: one it can wear now whose blow
	// beats the best weapon it owns by PLAYERBOT_WEAPON_UPGRADE_MIN_GAIN_PERCENT
	// and which the equipment pass would put on over it. gainOut, when given,
	// is the gain in percent the purse is drawn by.
	bool IsPlayerBotWeaponUpgradeOffer(LPCHARACTER ch, LPITEM offer, long long* gainOut)
	{
		if (!ch || !offer || offer->GetType() != ITEM_WEAPON || offer->GetSubType() == WEAPON_ARROW ||
				!IsPlayerBotEquipmentCandidate(ch, offer) || offer->GetLevelLimit() > ch->GetLevel() ||
				offer->FindEquipCell(ch) != WEAR_WEAPON || IsPlayerBotArcherStoneWeapon(ch, offer))
			return false;
		const TPlayerBotOwnedWeapon owned = ReadPlayerBotBestOwnedWeapon(ch);
		if (owned.item == offer)
			return false;
		const long long blow = GetPlayerBotWeaponHitDamage(offer, ch);
		if (owned.item && blow * 100 < owned.blow * (100 + PLAYERBOT_WEAPON_UPGRADE_MIN_GAIN_PERCENT))
			return false;
		// The class's preferences (a bow for an Archer, a dagger for a Dagger
		// Ninja) are in the score and not in the blow: a weapon the equipment
		// pass would leave in the bag is no upgrade, however hard it hits.
		if (owned.item && GetPlayerBotEquipmentScore(offer, ch) <= owned.score)
			return false;
		if (gainOut)
			*gainOut = GetPlayerBotWeaponGainPercent(blow, owned.item ? owned.blow : 0);
		return true;
	}

	// The cheapest line of every weapon on the stands, by map: written with the
	// ledger once a minute (AddPlayerBotOfflineLedger), so a bot on the
	// frontier knows without reading a counter whether its first village holds
	// a weapon it would buy.
	std::map<unsigned long long, long long> s_mapPlayerBotWeaponLineCheapest;

	void ClearPlayerBotWeaponLinePrices()
	{
		s_mapPlayerBotWeaponLineCheapest.clear();
	}

	void NotePlayerBotWeaponLinePrice(long lMapIndex, const TItemTable* table, DWORD count, long long price)
	{
		if (lMapIndex <= 0 || !table || table->bType != ITEM_WEAPON || table->bSubType == WEAPON_ARROW ||
				count != 1 || price <= 0)
			return;
		long long& cheapest = s_mapPlayerBotWeaponLineCheapest[PlayerBotMarketLocalKey(lMapIndex, table->dwVnum)];
		if (cheapest <= 0 || price < cheapest)
			cheapest = price;
	}

	// One bot's last look at its first village's weapons.
	struct TPlayerBotWeaponUpgradeLook
	{
		DWORD when;
		DWORD vnum;
		long long price;
		long long gain;

		TPlayerBotWeaponUpgradeLook() : when(0), vnum(0), price(0), gain(0)
		{
		}
	};
	std::map<DWORD, TPlayerBotWeaponUpgradeLook> s_mapPlayerBotWeaponUpgradeLooks;
	// Bots that set off for or picked such a weapon since the last report.
	DWORD s_dwPlayerBotWeaponUpgradePicks = 0;
	DWORD s_dwPlayerBotMerchantWeaponUpgrades = 0;

	// Whether a stand of the bot's first village holds a weapon it would buy
	// and could pay for now - by the cheapest line of each weapon and its blow
	// at that line's plus, the line's rolled lines left out (they only ever
	// make the line better). Read again every PLAYERBOT_WEAPON_UPGRADE_LOOK_MS.
	// The kind of the weapon owned is kept, so an Archer is never sent for a
	// sword its preference would leave in the bag.
	const TPlayerBotWeaponUpgradeLook& LookPlayerBotWeaponUpgrade(LPCHARACTER ch, DWORD dwNow)
	{
		TPlayerBotWeaponUpgradeLook& look = s_mapPlayerBotWeaponUpgradeLooks[ch->GetPlayerID()];
		if (look.when != 0 && dwNow - look.when < PLAYERBOT_WEAPON_UPGRADE_LOOK_MS)
			return look;
		look.when = dwNow != 0 ? dwNow : 1;
		look.vnum = 0;
		look.price = 0;
		look.gain = 0;
		if (!ch->IsItemLoaded() || s_mapPlayerBotWeaponLineCheapest.empty() ||
				GetPlayerBotWeaponUpgradeBudget(ch, PLAYERBOT_WEAPON_UPGRADE_BIG_GAIN_PERCENT) <= 0)
			return look;
		const long firstVillage = playerbot_empire_rules::GetHomeMap(ch->GetEmpire(),
				playerbot_empire_rules::MAP_ROLE_M1);
		if (firstVillage <= 0)
			return look;
		const TPlayerBotOwnedWeapon owned = ReadPlayerBotBestOwnedWeapon(ch);
		long long bestBlow = 0;
		const unsigned long long lo = PlayerBotMarketLocalKey(firstVillage, 0);
		const unsigned long long hi = PlayerBotMarketLocalKey(firstVillage, 0xFFFFFFFFU);
		for (std::map<unsigned long long, long long>::const_iterator it = s_mapPlayerBotWeaponLineCheapest.lower_bound(lo);
				it != s_mapPlayerBotWeaponLineCheapest.end() && it->first <= hi; ++it)
		{
			const DWORD vnum = (DWORD)(it->first & 0xFFFFFFFFULL);
			const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
			if (!IsPlayerBotWeaponProtoFor(ch, proto) ||
					(owned.subType >= 0 && (int)proto->bSubType != owned.subType))
				continue;
			const long long blow = GetPlayerBotWeaponHitDamageAt(NULL, proto, ch);
			if (blow <= bestBlow ||
					(owned.item && blow * 100 < owned.blow * (100 + PLAYERBOT_WEAPON_UPGRADE_MIN_GAIN_PERCENT)))
				continue;
			const long long gain = GetPlayerBotWeaponGainPercent(blow, owned.item ? owned.blow : 0);
			if (it->second > GetPlayerBotWeaponUpgradeBudget(ch, gain))
				continue;
			bestBlow = blow;
			look.vnum = vnum;
			look.price = it->second;
			look.gain = gain;
		}
		return look;
	}

	bool PlayerBotWantsWeaponUpgradeFromMarket(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded() || IsPlayerBotGearFrozen(ch))
			return false;
		return LookPlayerBotWeaponUpgrade(ch, get_dword_time()).vnum != 0;
	}

	// The village merchant's best weapon for this bot, when it beats the best
	// one owned by the upgrade's share and the purse pays for it. The ladder
	// (GetPlayerBotProgressionWeaponVnum) names the family's own tier for the
	// bot's level, and the merchants stock the tiers of 15, 25 and 36 only.
	DWORD FindPlayerBotMerchantWeaponUpgrade(LPCHARACTER ch, long long* priceOut)
	{
		if (priceOut)
			*priceOut = 0;
		if (!ch || !ch->IsItemLoaded())
			return 0;
		static const DWORD merchants[] = { 9001, 9002, 9003 };
		TPlayerBotOwnedWeapon owned;
		bool ownedRead = false;
		DWORD bestVnum = 0;
		long long bestBlow = 0;
		for (size_t i = 0; i < sizeof(merchants) / sizeof(merchants[0]); ++i)
		{
			LPSHOP shop = CShopManager::instance().GetByNPCVnum(merchants[i]);
			if (!shop)
				continue;
			const std::vector<CShop::SHOP_ITEM>& offers = shop->GetItemVector();
			for (size_t k = 0; k < offers.size(); ++k)
			{
				const TItemTable* proto = ITEM_MANAGER::instance().GetTable(offers[k].vnum);
				if (!IsPlayerBotWeaponProtoFor(ch, proto))
					continue;
				if (!ownedRead)
				{
					owned = ReadPlayerBotBestOwnedWeapon(ch);
					ownedRead = true;
				}
				if (owned.subType >= 0 && (int)proto->bSubType != owned.subType)
					continue;
				const long long blow = GetPlayerBotWeaponHitDamageAt(NULL, proto, ch);
				if (blow <= bestBlow ||
						(owned.item && blow * 100 < owned.blow * (100 + PLAYERBOT_WEAPON_UPGRADE_MIN_GAIN_PERCENT)))
					continue;
				// Half of the purse over PLAYERBOT_WEAPON_UPGRADE_MERCHANT_FLOOR:
				// the counters' floor would keep a bot of twenty, whose purse is a
				// few hundred thousand, from a sword of 5 000.
				const long long price = GetPlayerBotMerchantOfferPrice(offers[k], proto);
				if (price * 2 > (long long)ch->GetGold() - (long long)GetPlayerBotReservedGold(ch) -
						PLAYERBOT_WEAPON_UPGRADE_MERCHANT_FLOOR)
					continue;
				bestVnum = offers[k].vnum;
				bestBlow = blow;
				if (priceOut)
					*priceOut = price;
			}
		}
		return bestVnum;
	}

	bool PlayerBotWantsMerchantWeaponUpgrade(LPCHARACTER ch)
	{
		return ch && ch->IsItemLoaded() && !IsPlayerBotGearFrozen(ch) &&
				FindPlayerBotMerchantWeaponUpgrade(ch, NULL) != 0;
	}

	bool BuyPlayerBotMerchantWeaponUpgrade(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded() || IsPlayerBotGearFrozen(ch))
			return false;
		long long price = 0;
		const DWORD vnum = FindPlayerBotMerchantWeaponUpgrade(ch, &price);
		if (vnum == 0 || !BuyPlayerBotProgressionGear(ch, vnum, "weapon upgrade"))
			return false;
		++s_dwPlayerBotMerchantWeaponUpgrades;
		return true;
	}

	// A rod, a pickaxe or a herbalist's knife stays in the hand only while its
	// own session owns the bot, and never in a dungeon. Every session puts its
	// tool away when it ends, and every swing and cast takes it out of the
	// hand first (ReadyPlayerBotHandForFight) - but the dungeon runs, the
	// Arezzo cohort, a person's dungeon and the shouters claim the tick above
	// the sessions and above the equipment pass, so a bot called away from the
	// water or the vein kept its tool for as long as the call lasted, and a
	// healing Shaman, which never swings, walked a whole dungeon with its
	// pickaxe (the dungeon runs of 5 October). Asked at the top of the tick,
	// above every pass that claims it.
	std::map<DWORD, DWORD> s_mapPlayerBotToolGuardNext;

	bool ManagePlayerBotToolHand(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->IsDead() || !ch->IsItemLoaded())
			return false;
		LPITEM held = ch->GetWear(WEAR_WEAPON);
		if (!held || !IsPlayerBotToolType(held->GetType()) || IsPlayerBotGearFrozen(ch) || ch->GetMyShop() ||
				ch->GetExchange())
			return false;
		const DWORD pid = ch->GetPlayerID();
		bool sessionLive = false;
		if (held->GetType() == ITEM_ROD)
			sessionLive = state.bFishingSession;
		else if (held->GetType() == ITEM_PICK)
			sessionLive = IsPlayerBotMiningNow(pid, dwNow);
		else
			sessionLive = IsPlayerBotHerbPickingNow(ch, dwNow);
		const bool calledAway = IsPlayerBotOnDungeonRun(pid) || IsPlayerBotInDungeonBusiness(ch, state);
		if (sessionLive && !calledAway)
			return false;
		std::map<DWORD, DWORD>::iterator next = s_mapPlayerBotToolGuardNext.find(pid);
		if (next != s_mapPlayerBotToolGuardNext.end() && (int)(dwNow - next->second) < 0)
			return false;
		s_mapPlayerBotToolGuardNext[pid] = dwNow + PLAYERBOT_TOOL_GUARD_RETRY_MS;
		const DWORD toolVnum = held->GetVnum();
		// A digging session whose clock ran out is ended here with its rest:
		// its own end is asked only while the clock still runs, and the next
		// look at the veins would otherwise start another at once.
		if (held->GetType() == ITEM_PICK && !sessionLive && !calledAway)
			EndPlayerBotMiningSession(ch, state, dwNow, "tool_guard");
		ReadyPlayerBotHandForFight(ch, state, dwNow, calledAway ? "tool_guard_dungeon" : "tool_guard_stale");
		LPITEM now = ch->GetWear(WEAR_WEAPON);
		PlayerBotLogThrottled("tool_guard", dwNow,
				"PLAYERBOT_GEAR: tool put away pid=%u name=%s tool=%u weapon=%u session=%d called_away=%d map=%ld",
				pid, ch->GetName(), toolVnum, now ? now->GetVnum() : 0, sessionLive ? 1 : 0, calledAway ? 1 : 0,
				ch->GetMapIndex());
		return false;
	}

	// Once a report interval with the weapon census (ReportPlayerBotWeaponGoals):
	// how many bots' last look found a weapon on their first village's stands
	// they would buy now, and how many went for one since the last report.
	void ReportPlayerBotWeaponUpgrades(DWORD dwNow)
	{
		DWORD fresh = 0, wanting = 0;
		long long gainSum = 0;
		for (std::map<DWORD, TPlayerBotWeaponUpgradeLook>::iterator it = s_mapPlayerBotWeaponUpgradeLooks.begin();
				it != s_mapPlayerBotWeaponUpgradeLooks.end(); )
		{
			if (it->second.when == 0 || dwNow - it->second.when >= 4 * PLAYERBOT_WEAPON_UPGRADE_LOOK_MS)
			{
				s_mapPlayerBotWeaponUpgradeLooks.erase(it++);
				continue;
			}
			++fresh;
			if (it->second.vnum != 0)
			{
				++wanting;
				gainSum += std::min<long long>(it->second.gain, 1000);
			}
			++it;
		}
		sys_log(0, "PLAYERBOT_GEAR_UPGRADE: census looked=%u affordable_upgrade=%u avg_gain=%lld%% lines_priced=%u picks=%u merchant_buys=%u",
				fresh, wanting, wanting ? gainSum / wanting : 0LL,
				(unsigned int)s_mapPlayerBotWeaponLineCheapest.size(), s_dwPlayerBotWeaponUpgradePicks,
				s_dwPlayerBotMerchantWeaponUpgrades);
		s_dwPlayerBotWeaponUpgradePicks = 0;
		s_dwPlayerBotMerchantWeaponUpgrades = 0;
	}
}

#endif
