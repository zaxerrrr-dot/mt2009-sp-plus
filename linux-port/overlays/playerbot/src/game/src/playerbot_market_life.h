#ifndef __INC_METIN2_PLAYERBOT_MARKET_LIFE_H__
#define __INC_METIN2_PLAYERBOT_MARKET_LIFE_H__

// MT2009_PLUS_MARKET_LIFE_V1 - the owner's market list of 9 October.
//
// The market has no fixed prices: every price is a base of the sheet put
// through the world's yang curve and inflation (playerbot_price_tables.h,
// ScalePlayerBotIwakuraPrice), then the market index, the sale memory, the
// keeper's spread and the counters' markdowns (playerbot_town.h). The points
// of the list build on those, and most of them live where the thing they
// change lives; this file holds what has no other home:
//
//   1. no Blessing Scroll on a piece worth less than the scroll
//      (IsPlayerBotCheaperThanBlessingScroll, asked by IsPlayerBotScrollFreeGear,
//      so the refine passes, the planner and the scroll purchase agree);
//   2. a scroll on a piece of level 18 or under only where the step pays
//      (IsPlayerBotLowGearScrollWorthIt);
//   3. the level-30 weapons at +0..+3 - GetPlayerBotLevel30LowPlusPercent,
//      playerbot_town.h;
//   4. Marchewka and Czerwony Zen-szen: the kingdom's counters' count
//      (GetPlayerBotKingdomMarketUnits, IsPlayerBotHorseFeedForCounter) and
//      the exchange at the General Store (ExchangePlayerBotHorseFeed,
//      playerbot_economy.h);
//   5. rare goods - IsPlayerBotRareOnMarket, playerbot_town.h, and the
//      buyers' caps in playerbot_market.h;
//   6. Kupony SM on the counters - playerbot_itemshop.h;
//   7. the material market's test option: the share of a stack owed to the
//      merchant (NotePlayerBotShopRoomOwed, SellPlayerBotShopRoomOwed; the cut
//      itself is BotOfflineRoomCut, playerbot_offline_shop.h);
//   8. the drifting keeper spread - playerbot_town.h;
//   9. the bargain hunters and the impulse buys (the whims:
//      IsPlayerBotWhimCandidate, GetPlayerBotWhimKind), the curious refine
//      (IsPlayerBotCuriosityRefinePiece) and the hunters' chat lines
//      (playerbot_chat_world.h);
//  10. the barter between two bots (RunPlayerBotBarterPass).
//
// An implementation fragment: include it once, after playerbot_explain_late.h
// (it asks the town's prices, the economy's refine rules and the market's
// purse); the files before it declare what they ask of it.

namespace
{
	// ---------------------------------------------------- points 1 and 2

	// What a piece is worth to the scroll rules and to the barter: the sheet's
	// price at the plus, and at its own plus lifted by its lines and its
	// average (LiftPlayerBotGearPrice) - one measure, nobody's spread on it.
	// 0 for a piece the sheet does not price.
	DWORD GetPlayerBotGearWorth(LPITEM item, int plus)
	{
		if (!item || (item->GetType() != ITEM_WEAPON && item->GetType() != ITEM_ARMOR))
			return 0;
		const DWORD sheet = GetPlayerBotGearSheetPriceAt(item, plus);
		if (sheet == 0)
			return 0;
		return plus == (int)item->GetRefineLevel() ? LiftPlayerBotGearPrice(item, sheet) : sheet;
	}

	DWORD GetPlayerBotBlessingScrollWorth()
	{
		return GetPlayerBotMaterialAskingBase(PLAYERBOT_BLESSING_SCROLL_VNUM);
	}

	// Point 1: "Zwoj Blogoslawienstwa nie jest uzywany na przedmiot tanszy od
	// niego" - a piece worth less, at its plus, than the scroll the step would
	// take. A piece the sheet does not price is left to the rules it had.
	bool IsPlayerBotCheaperThanBlessingScroll(LPITEM item)
	{
		if (!item || item->GetRefinedVnum() == 0)
			return false;
		const DWORD worth = GetPlayerBotGearWorth(item, item->GetRefineLevel());
		const DWORD scroll = GetPlayerBotBlessingScrollWorth();
		return worth > 0 && scroll > 0 && worth < scroll;
	}

	// Point 2: the few steps of a piece of level 18 or under worth a scroll -
	// from PLAYERBOT_LOW_GEAR_SCROLL_MIN_PLUS, where the next plus is worth
	// PLAYERBOT_LOW_GEAR_SCROLL_GAIN_PERCENT of the scroll over the present one.
	bool IsPlayerBotLowGearScrollWorthIt(LPITEM item)
	{
		if (!item || item->GetRefinedVnum() == 0 ||
				(int)item->GetRefineLevel() < PLAYERBOT_LOW_GEAR_SCROLL_MIN_PLUS || item->GetRefineLevel() >= 9)
			return false;
		const long long now = GetPlayerBotGearWorth(item, item->GetRefineLevel());
		const long long next = GetPlayerBotGearSheetPriceAt(item, item->GetRefineLevel() + 1);
		const long long scroll = GetPlayerBotBlessingScrollWorth();
		return now > 0 && scroll > 0 && next > now &&
				(next - now) * 100 >= scroll * PLAYERBOT_LOW_GEAR_SCROLL_GAIN_PERCENT;
	}

	// ------------------------------------------------------------ point 4

	// The units of a kind on the counters of the maps a kingdom owns - the
	// ledger's count by map (s_mapMarketLocalSupply), every counter on them.
	DWORD GetPlayerBotKingdomMarketUnits(BYTE empire, DWORD vnum)
	{
		DWORD units = 0;
		for (std::map<unsigned long long, DWORD>::const_iterator it = s_mapMarketLocalSupply.begin();
				it != s_mapMarketLocalSupply.end(); ++it)
		{
			if ((DWORD)(it->first & 0xFFFFFFFFULL) != vnum)
				continue;
			const long map = (long)(DWORD)(it->first >> 32);
			if (playerbot_empire_rules::GetMapOwnerEmpire(map) == (int)empire)
				units += it->second;
		}
		return units;
	}

	// A bot's Marchewka or Czerwony Zen-szen over its horse's keep goes on its
	// counter while its kingdom's counters hold fewer than
	// PLAYERBOT_HORSE_FEED_KINGDOM_CAP of the kind.
	bool IsPlayerBotHorseFeedForCounter(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !PlayerBotHasCounter(ch))
			return false;
		const DWORD vnum = item->GetVnum();
		if (vnum != PLAYERBOT_HORSE_FEED_CARROT && vnum != PLAYERBOT_HORSE_FEED_GINSENG)
			return false;
		return (int)ch->CountSpecifyItem(vnum) > GetPlayerBotHorseFeedKeep(ch, vnum) &&
				GetPlayerBotKingdomMarketUnits(ch->GetEmpire(), vnum) < PLAYERBOT_HORSE_FEED_KINGDOM_CAP;
	}

	// ------------------------------------------------------------ point 7

	const DWORD PLAYERBOT_SHOP_ROOM_BOT_GAP_MS = 10 * 60 * 1000;
	const int PLAYERBOT_SHOP_ROOM_CORE_PER_MINUTE = 10;
	const DWORD PLAYERBOT_SHOP_ROOM_OWED_TTL_MS = 3 * 60 * 60 * 1000;

	struct TPlayerBotShopRoomOwed
	{
		DWORD vnum;
		long skill;
		int units;
		DWORD at;
	};
	std::map<DWORD, std::vector<TPlayerBotShopRoomOwed> > s_mapPlayerBotShopRoomOwed;
	std::map<DWORD, DWORD> s_mapPlayerBotShopRoomCutAt;
	DWORD s_dwPlayerBotShopRoomMinute = 0;
	int s_iPlayerBotShopRoomThisMinute = 0;
	unsigned int s_uPlayerBotShopRoomCuts = 0;
	unsigned int s_uPlayerBotShopRoomSoldUnits = 0;
	long long s_llPlayerBotShopRoomGold = 0;

	bool PlayerBotMayCutShopRoom(DWORD pid, DWORD now)
	{
		if (s_dwPlayerBotShopRoomMinute == 0 || now - s_dwPlayerBotShopRoomMinute >= 60000)
		{
			s_dwPlayerBotShopRoomMinute = now ? now : 1;
			s_iPlayerBotShopRoomThisMinute = 0;
		}
		if (s_iPlayerBotShopRoomThisMinute >= PLAYERBOT_SHOP_ROOM_CORE_PER_MINUTE)
			return false;
		std::map<DWORD, DWORD>::const_iterator it = s_mapPlayerBotShopRoomCutAt.find(pid);
		return it == s_mapPlayerBotShopRoomCutAt.end() || now - it->second >= PLAYERBOT_SHOP_ROOM_BOT_GAP_MS;
	}

	void NotePlayerBotShopRoomOwed(DWORD pid, DWORD vnum, long skill, int units)
	{
		const DWORD now = get_dword_time();
		s_mapPlayerBotShopRoomCutAt[pid] = now ? now : 1;
		++s_iPlayerBotShopRoomThisMinute;
		++s_uPlayerBotShopRoomCuts;
		TPlayerBotShopRoomOwed owed = { vnum, skill, units, now };
		std::vector<TPlayerBotShopRoomOwed>& list = s_mapPlayerBotShopRoomOwed[pid];
		if (list.size() < 8)
			list.push_back(owed);
	}

	// At the General Store: the owed units the bag still holds, at the
	// merchant's price a unit. The yang it brought.
	long long SellPlayerBotShopRoomOwed(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		std::map<DWORD, std::vector<TPlayerBotShopRoomOwed> >::iterator found =
				s_mapPlayerBotShopRoomOwed.find(ch->GetPlayerID());
		if (found == s_mapPlayerBotShopRoomOwed.end())
			return 0;
		const DWORD now = get_dword_time();
		long long gold = 0;
		std::vector<TPlayerBotShopRoomOwed>& list = found->second;
		for (size_t i = 0; i < list.size(); ++i)
		{
			TPlayerBotShopRoomOwed& owed = list[i];
			if (now - owed.at >= PLAYERBOT_SHOP_ROOM_OWED_TTL_MS)
			{
				owed.units = 0;
				continue;
			}
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS && owed.units > 0; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				if (!item || item->GetCell() != cell || item->GetVnum() != owed.vnum || item->isLocked() ||
						item->IsExchanging() || item->IsEquipped())
					continue;
				if (owed.skill != 0 && item->GetSocket(0) != owed.skill)
					continue;
				const DWORD unit = GetPlayerBotNpcSellUnitPrice(item);
				const int count = (int)item->GetCount();
				const int sold = std::min(count, owed.units);
				if (sold <= 0)
					continue;
				if (sold >= count)
					ITEM_MANAGER::instance().RemoveItem(item, "PLAYERBOT_SHOP_ROOM");
				else
					item->SetCount(count - sold);
				const long long paid = (long long)unit * sold;
				gold += paid;
				owed.units -= sold;
				s_uPlayerBotShopRoomSoldUnits += (unsigned int)sold;
				sys_log(0, "PLAYERBOT_SHOPROOM: sold pid=%u name=%s vnum=%u units=%d gold=%lld",
						ch->GetPlayerID(), ch->GetName(), owed.vnum, sold, paid);
			}
			// What the bag no longer holds - it went back up whole - is let go.
			owed.units = 0;
		}
		s_mapPlayerBotShopRoomOwed.erase(found);
		if (gold > 0)
		{
			PlayerBotChangeGold(ch, gold);
			s_llPlayerBotShopRoomGold += gold;
		}
		return gold;
	}

	// ------------------------------------------------------------ point 9

	enum
	{
		PLAYERBOT_WHIM_NONE = 0,
		PLAYERBOT_WHIM_BARGAIN = 1,
		PLAYERBOT_WHIM_IMPULSE = 2,
	};

	// The bargain hunters: this share of the bots (by pid) from level 30 with
	// a counter, holding PLAYERBOT_BARGAIN_HUNTER_MIN_GOLD. A hunter buys goods
	// it does not need where a counter asks PLAYERBOT_BARGAIN_PRICE_PERCENT of
	// the market's price or less - a line marked down for hours, a keeper's
	// low draw, a person's cheap line - out of PLAYERBOT_BARGAIN_PURSE_PERCENT of
	// what it can spend, one line every PLAYERBOT_BARGAIN_GAP_MS, and its own
	// counter puts the goods up again at the market's price.
	const int PLAYERBOT_BARGAIN_HUNTER_PERCENT = 10;
	const int PLAYERBOT_BARGAIN_HUNTER_MIN_LEVEL = 30;
	const long long PLAYERBOT_BARGAIN_HUNTER_MIN_GOLD = 1000000LL;
	const int PLAYERBOT_BARGAIN_PRICE_PERCENT = 70;
	const int PLAYERBOT_BARGAIN_PURSE_PERCENT = 25;
	const DWORD PLAYERBOT_BARGAIN_GAP_MS = 20 * 60 * 1000;
	// The impulse: in this share of a bot's hours (drawn by pid and hour) a
	// bot from level 15 may buy one small line of goods it does not need -
	// at no more than PLAYERBOT_IMPULSE_FAIR_PERCENT of the market's price, two
	// thousandths of its purse at most, and never over
	// PLAYERBOT_IMPULSE_MAX_PRICE (the sheet's yang, scaled) - and then not
	// again for PLAYERBOT_IMPULSE_GAP_MS.
	const int PLAYERBOT_IMPULSE_HOUR_PERCENT = 12;
	const int PLAYERBOT_IMPULSE_MIN_LEVEL = 15;
	const int PLAYERBOT_IMPULSE_PURSE_PERMILLE = 20;
	const DWORD PLAYERBOT_IMPULSE_MAX_PRICE = 150000;
	const int PLAYERBOT_IMPULSE_FAIR_PERCENT = 110;
	const DWORD PLAYERBOT_IMPULSE_GAP_MS = 3 * 60 * 60 * 1000;

	std::map<DWORD, DWORD> s_mapPlayerBotBargainAt;
	std::map<DWORD, DWORD> s_mapPlayerBotImpulseAt;
	unsigned int s_uPlayerBotBargains = 0;
	unsigned int s_uPlayerBotImpulses = 0;
	long long s_llPlayerBotWhimYang = 0;

	bool IsPlayerBotBargainHunter(LPCHARACTER ch)
	{
		return ch && (int)ch->GetLevel() >= PLAYERBOT_BARGAIN_HUNTER_MIN_LEVEL &&
				(int)(PlayerBotNavHash(ch->GetPlayerID() ^ 0x48554e54U) % 100U) < PLAYERBOT_BARGAIN_HUNTER_PERCENT &&
				!IsPlayerBotSidekickPID(ch->GetPlayerID()) && PlayerBotHasCounter(ch);
	}

	bool IsPlayerBotWhimGapOver(const std::map<DWORD, DWORD>& stamps, DWORD pid, DWORD gap)
	{
		std::map<DWORD, DWORD>::const_iterator it = stamps.find(pid);
		return it == stamps.end() || get_dword_time() - it->second >= gap;
	}

	bool IsPlayerBotImpulseHour(LPCHARACTER ch)
	{
		const DWORD hour = (DWORD)(get_global_time() / 3600);
		// MT2009_PLUS_BOT_SHOP_MGMT_V1 (point 1: "zachecac inne boty do
		// kupowania"): while the bots' counters are glutted (IsPlayerBotShopGlut)
		// SHOP_MGMT_IMPULSE_PCT of a bot's hours are impulse hours - the purse
		// rules below (two hundredths of the spare over the reserves, the
		// small price cap) are the same.
		const int percent = IsPlayerBotShopGlut()
				? std::max(PLAYERBOT_IMPULSE_HOUR_PERCENT, GetPlayerBotShopMgmt(PLAYERBOT_SM_IMPULSE_PCT))
				: PLAYERBOT_IMPULSE_HOUR_PERCENT;
		return (int)(PlayerBotNavHash(ch->GetPlayerID() ^ (hour * 0x9E3779B9U) ^ 0x494d5055U) % 100U) < percent;
	}

	// The goods a whim takes: what a counter lists as goods - refine
	// materials, books, scrolls, soul stones, the kinds of the market index -
	// never gear, a Dragon Stone, the operator's own curve goods or a coupon.
	bool IsPlayerBotWhimGoods(LPITEM offer)
	{
		if (!offer || offer->GetType() == ITEM_WEAPON || offer->GetType() == ITEM_ARMOR ||
				offer->GetType() == ITEM_COSTUME || offer->IsDragonSoul())
			return false;
		const DWORD vnum = offer->GetVnum();
		if (IsPlayerBotCorVnum(vnum) || vnum == PLAYERBOT_CRAFT_MATERIAL_VNUM_PRICED ||
				IsPlayerBotGuildBuildMaterial(vnum) || IsPlayerBotFixedPriceTalismanVnum(vnum) ||
				(vnum >= PLAYERBOT_ISHOP_VOUCHER_MIN_VNUM && vnum <= PLAYERBOT_ISHOP_VOUCHER_MAX_VNUM) ||
				vnum == PLAYERBOT_MOONLIGHT_CHEST_VNUM)
			return false;
		// MT2009_PLUS_BOT_SOULSTONE_MARKET_V2: a soul stone one at a time (a
		// whim takes one off a stack line, PlayerBotPartBuyCount), never a
		// +0..+2 - the Alchemist's dust, not goods.
		if (offer->GetType() == ITEM_METIN &&
				(offer->GetCount() > 1 || IsPlayerBotDustGradeSoulStone(vnum)))
			return false;
		return IsPlayerBotTradeableMaterial(offer) || offer->GetType() == ITEM_SKILLBOOK ||
				offer->GetType() == ITEM_METIN || IsPlayerBotMarketIndexedVnum(vnum) ||
				IsPlayerBotSafeRefineScroll(vnum);
	}

	bool IsPlayerBotWhimCandidate(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer || !ch->IsItemLoaded() || !IsPlayerBotWhimGoods(offer) ||
				IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return false;
		const DWORD pid = ch->GetPlayerID();
		if (IsPlayerBotBargainHunter(ch) && (long long)ch->GetGold() >= PLAYERBOT_BARGAIN_HUNTER_MIN_GOLD &&
				IsPlayerBotWhimGapOver(s_mapPlayerBotBargainAt, pid, PLAYERBOT_BARGAIN_GAP_MS))
			return true;
		return (int)ch->GetLevel() >= PLAYERBOT_IMPULSE_MIN_LEVEL && IsPlayerBotImpulseHour(ch) &&
				IsPlayerBotWhimGapOver(s_mapPlayerBotImpulseAt, pid, PLAYERBOT_IMPULSE_GAP_MS);
	}

	int GetPlayerBotWhimKind(LPCHARACTER ch, LPITEM offer, long long price, DWORD sellerPID)
	{
		(void)sellerPID;
		if (price <= 0 || !IsPlayerBotWhimCandidate(ch, offer) || IsPlayerBotPriceSlipOffer(offer, price))
			return PLAYERBOT_WHIM_NONE;
		const long long fair = (long long)GetPlayerBotShopAskingPrice(offer);
		if (fair <= 0)
			return PLAYERBOT_WHIM_NONE;
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) -
				(long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		if (spare <= 0)
			return PLAYERBOT_WHIM_NONE;
		const DWORD pid = ch->GetPlayerID();
		if (IsPlayerBotBargainHunter(ch) && (long long)ch->GetGold() >= PLAYERBOT_BARGAIN_HUNTER_MIN_GOLD &&
				IsPlayerBotWhimGapOver(s_mapPlayerBotBargainAt, pid, PLAYERBOT_BARGAIN_GAP_MS) &&
				price * 100 <= fair * PLAYERBOT_BARGAIN_PRICE_PERCENT &&
				price <= spare * PLAYERBOT_BARGAIN_PURSE_PERCENT / 100)
			return PLAYERBOT_WHIM_BARGAIN;
		if ((int)ch->GetLevel() >= PLAYERBOT_IMPULSE_MIN_LEVEL && IsPlayerBotImpulseHour(ch) &&
				IsPlayerBotWhimGapOver(s_mapPlayerBotImpulseAt, pid, PLAYERBOT_IMPULSE_GAP_MS) &&
				price * 100 <= fair * PLAYERBOT_IMPULSE_FAIR_PERCENT &&
				price <= spare * PLAYERBOT_IMPULSE_PURSE_PERMILLE / 1000 &&
				price <= (long long)ScalePlayerBotIwakuraPrice(PLAYERBOT_IMPULSE_MAX_PRICE))
			return PLAYERBOT_WHIM_IMPULSE;
		return PLAYERBOT_WHIM_NONE;
	}

	void NotePlayerBotWhimBought(LPCHARACTER ch, int kind, DWORD vnum, long long price)
	{
		if (!ch || kind == PLAYERBOT_WHIM_NONE)
			return;
		const DWORD now = get_dword_time();
		if (kind == PLAYERBOT_WHIM_BARGAIN)
		{
			s_mapPlayerBotBargainAt[ch->GetPlayerID()] = now ? now : 1;
			++s_uPlayerBotBargains;
		}
		else
		{
			s_mapPlayerBotImpulseAt[ch->GetPlayerID()] = now ? now : 1;
			++s_uPlayerBotImpulses;
		}
		s_llPlayerBotWhimYang += price;
		sys_log(0, "PLAYERBOT_MARKET: %s pid=%u name=%s vnum=%u price=%lld",
				kind == PLAYERBOT_WHIM_BARGAIN ? "bargain bought" : "impulse buy",
				ch->GetPlayerID(), ch->GetName(), vnum, price);
	}

	// The curious refine: this share of the bots (by pid), on the days their
	// draw comes up (PLAYERBOT_CURIOUS_DAY_PERCENT), and holding
	// PLAYERBOT_CURIOUS_MIN_GOLD, take one piece of their goods - a weapon or
	// an armour piece at +0..+PLAYERBOT_CURIOUS_MAX_FROM_PLUS that is no
	// merchant's junk, no prize and nothing the operator's policy rules on -
	// PLAYERBOT_CURIOUS_STEPS steps up at the plain anvil "to see", the risk
	// of the burn its own. One piece a bot a day; a piece the bot keeps for
	// itself is refined by its own rules anyway.
	const int PLAYERBOT_CURIOUS_PERCENT = 6;
	const int PLAYERBOT_CURIOUS_DAY_PERCENT = 35;
	const int PLAYERBOT_CURIOUS_MAX_FROM_PLUS = 2;
	const int PLAYERBOT_CURIOUS_STEPS = 2;
	const long long PLAYERBOT_CURIOUS_MIN_GOLD = 2000000LL;

	struct TPlayerBotCuriosity
	{
		DWORD itemId;
		int target;
		DWORD day;
	};
	std::map<DWORD, TPlayerBotCuriosity> s_mapPlayerBotCuriosity;
	unsigned int s_uPlayerBotCuriousPicks = 0;

	bool IsPlayerBotCuriosityRefinePiece(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || item->IsEquipped() || item->GetWindow() != INVENTORY || item->GetRefinedVnum() == 0 ||
				(item->GetType() != ITEM_WEAPON && item->GetType() != ITEM_ARMOR) ||
				IsPlayerBotSidekickPID(ch->GetPlayerID()) ||
				(int)(PlayerBotNavHash(ch->GetPlayerID() ^ 0x43555249U) % 100U) >= PLAYERBOT_CURIOUS_PERCENT)
			return false;
		const DWORD day = (DWORD)(get_global_time() / 86400);
		std::map<DWORD, TPlayerBotCuriosity>::const_iterator known = s_mapPlayerBotCuriosity.find(ch->GetPlayerID());
		if (known != s_mapPlayerBotCuriosity.end() && known->second.day == day)
			return item->GetID() == known->second.itemId && (int)item->GetRefineLevel() < known->second.target;
		// MT2009_PLUS_BOT_SHOP_MGMT_V1 (point 3): a new piece "to see" is gear
		// refined for a counter and nothing else - the counters stood full of
		// plain +4 (42 060 lines on the supporters' world, 20 October). Off
		// under the shop management unless SHOP_MGMT_CURIOUS says otherwise; a
		// pick made today runs out.
		if (IsPlayerBotShopMgmtOn() && GetPlayerBotShopMgmt(PLAYERBOT_SM_CURIOUS) == 0)
			return false;
		if ((int)(PlayerBotNavHash(ch->GetPlayerID() ^ (day * 0x85EBCA6BU) ^ 0x44415953U) % 100U) >=
				PLAYERBOT_CURIOUS_DAY_PERCENT || (long long)ch->GetGold() < PLAYERBOT_CURIOUS_MIN_GOLD)
			return false;
		if ((int)item->GetRefineLevel() > PLAYERBOT_CURIOUS_MAX_FROM_PLUS || item->isLocked() ||
				IsPlayerBotPrizeItem(item) || GetPlayerBotItemPolicy(item) != PLAYERBOT_ITEM_POLICY_NONE ||
				IsPlayerBotSidekickPinned(ch, item) || IsPlayerBotSpecialLevel30Weapon(item))
			return false;
		// MT2009_PLUS_BOT_BAG_HOARD_FIX_V1: no new piece "to see" from a full
		// bag - it makes room first.
		if (IsPlayerBotBagFull(ch) || IsPlayerBotBagUnderPressure(ch))
			return false;
		// The junk rule asks a good deal of the bag's other rules; a question
		// of this one inside it is no pick.
		static bool s_bAsking = false;
		if (s_bAsking)
			return false;
		s_bAsking = true;
		const bool goods = !IsPlayerBotJunkItem(ch, item) && CanPlayerBotAffordRefineAttempt(ch, item);
		s_bAsking = false;
		if (!goods)
			return false;
		const int target = std::min((int)GetPlayerBotRefineTarget(ch, item),
				(int)item->GetRefineLevel() + PLAYERBOT_CURIOUS_STEPS);
		if ((int)item->GetRefineLevel() >= target)
			return false;
		TPlayerBotCuriosity pick = { item->GetID(), target, day };
		s_mapPlayerBotCuriosity[ch->GetPlayerID()] = pick;
		++s_uPlayerBotCuriousPicks;
		sys_log(0, "PLAYERBOT_MARKET: curious refine pid=%u name=%s item=%u vnum=%u plus=%u to=%d gold=%lld",
				ch->GetPlayerID(), ch->GetName(), item->GetID(), item->GetVnum(),
				(unsigned int)item->GetRefineLevel(), target, (long long)ch->GetGold());
		return true;
	}

	// ----------------------------------------------------------- point 10

	// The barter: two bots in a village give each other a piece of gear each
	// has no use for and the other would wear (IsPlayerBotUnwantedGear on the
	// giver's side, IsPlayerBotUpgradeForSelf on the taker's). Both pieces are
	// valued by one measure (GetPlayerBotGearWorth - the sheet at the plus and
	// the lines, nobody's spread or markup); the side that gets the dearer one
	// pays the difference, and the barter is off when the difference is over
	// PLAYERBOT_BARTER_TOPUP_MAX_PERCENT of the cheaper piece or over
	// PLAYERBOT_BARTER_PURSE_PERCENT of what the payer can spend
	// (playerbot_price_rules::BarterTopUp). A piece with good lines is never
	// bartered (IsPlayerBotPrizeItem, or lines asking
	// PLAYERBOT_BARTER_GOOD_BONUS_PERCENT over its base): it is a counter's
	// goods and a person's to buy. A few barters a core a minute, a bot one
	// every PLAYERBOT_BARTER_BOT_GAP_MS, both in the same village within
	// PLAYERBOT_BARTER_RANGE of each other; the pieces change bags as the
	// exchange window moves them (CExchange::Done).
	const int PLAYERBOT_BARTER_PER_PASS = 3;
	const int PLAYERBOT_BARTER_RANGE = 3000;
	const int PLAYERBOT_BARTER_TOPUP_MAX_PERCENT = 50;
	const int PLAYERBOT_BARTER_PURSE_PERCENT = 30;
	const int PLAYERBOT_BARTER_GOOD_BONUS_PERCENT = 150;
	const DWORD PLAYERBOT_BARTER_BOT_GAP_MS = 30 * 60 * 1000;
	const size_t PLAYERBOT_BARTER_ITEMS_A_BOT = 4;
	const size_t PLAYERBOT_BARTER_BOTS_A_MAP = 60;

	std::map<DWORD, DWORD> s_mapPlayerBotBarterAt;
	unsigned int s_uPlayerBotBarters = 0;
	long long s_llPlayerBotBarterTopUp = 0;

	bool IsPlayerBotBarterGoods(LPCHARACTER ch, LPITEM item)
	{
		if (!item || item->IsEquipped() || item->isLocked() || item->IsExchanging() ||
				(item->GetType() != ITEM_WEAPON && item->GetType() != ITEM_ARMOR))
			return false;
		// "ochrona dobrych bonusow": a piece with good lines is no barter's.
		if (IsPlayerBotPrizeItem(item) || GetPlayerBotBonusPricePercent(item) >= PLAYERBOT_BARTER_GOOD_BONUS_PERCENT ||
				IsPlayerBotBonusGoodsPiece(item))
			return false;
		return IsPlayerBotUnwantedGear(ch, item) && GetPlayerBotGearWorth(item, item->GetRefineLevel()) > 0;
	}

	struct TPlayerBotBarterSide
	{
		LPCHARACTER ch;
		std::vector<LPITEM> goods;
	};

	// Moves a piece from one bot's bag to a free cell of the other's, as the
	// exchange window does. False, and nothing moved, without a cell.
	bool MovePlayerBotBarterPiece(LPCHARACTER from, LPCHARACTER to, LPITEM item)
	{
		const int cell = to->GetEmptyInventory(item->GetSize());
		if (cell < 0)
			return false;
		from->SyncQuickslot(QUICKSLOT_TYPE_ITEM, item->GetCell(), 255);
		item->RemoveFromCharacter();
		item->AddToCharacter(to, TItemPos(INVENTORY, (WORD)cell));
		FlushPlayerBotItemRow(item);
		LogManager::instance().ItemLog(to, item, "PLAYERBOT_BARTER", from->GetName());
		return true;
	}

	// MT2009_PLUS_BOT_FULL_CLEAROUT_V1 (the owner, 16 October: "Jesli bot nie
	// ma miejsca na straganie, w EQ i u dozorcy - sprzedaje do handlarki
	// powiedzmy 10-15 najslabszych (najtanszych) przedmiotow, lub daje je innym
	// botom jesli im sie przydadza"). At the end of a town visit, at most once
	// in PLAYERBOT_FULL_CLEAROUT_GAP_MS a bot, when all three are full at once:
	// the stall (fewer than PLAYERBOT_STALL_WEAK_TAKEOFF_FULL_CELLS free cells,
	// or no stall at all), the bag (IsPlayerBotBagFull or under pressure) and
	// the safebox (a deposit it turned away within PLAYERBOT_BAG_ROOM_SAFEBOX_FULL_MS,
	// or no box the bot could open). Its cheapest pieces go, up to
	// PLAYERBOT_FULL_CLEAROUT_MAX - the bag room rule's own choice of what may
	// go (GetPlayerBotBagRoomSaleKind: nothing worn, locked, quest or ItemShop,
	// no operator's policy, no refine material or potion, no piece the bot
	// could wear (its next piece, backups and anvil work among them), no book
	// it keeps, Stalki, level-30 weapon, Awakening goods, Useful Items List,
	// gambler's piece, guild material, stone under its keep, nothing of
	// PLAYERBOT_BAG_ROOM_SELL_VALUE_MAX), and besides it never a +7 or higher,
	// a prize piece or a companion owner's gift, ranked by that rule's value
	// (the merchant's price or the counter's asking price, the higher). A
	// piece another bot of the village within PLAYERBOT_BARTER_RANGE would put
	// on (IsPlayerBotUpgradeForSelf) is handed to it, as the barter moves a
	// piece (MovePlayerBotBarterPiece's way); the rest is sold at the
	// merchant's price, as the bag room rule sells. Only the bag: the box is
	// open only at the Storekeeper's and the stall's lines need bag room to
	// come home - what the bag sells makes that room, and the stall's weak
	// lines come off by MT2009_PLUS_BOT_STALL_WEAK_TAKEOFF_V1.
	const int PLAYERBOT_FULL_CLEAROUT_MIN = 10;
	const int PLAYERBOT_FULL_CLEAROUT_MAX = 15;
	const DWORD PLAYERBOT_FULL_CLEAROUT_GAP_MS = 60 * 60 * 1000;
	std::map<DWORD, DWORD> s_mapPlayerBotFullClearoutAt;

	bool IsPlayerBotStallFullForClearout(LPCHARACTER ch)
	{
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		auto shop = ch ? ikashop::GetManager().GetShopByOwnerID(ch->GetPlayerID()) : nullptr;
		// MT2009_PLUS_BOT_SHOP_MGMT_V1: full is at the fill target now.
		return !shop || BotOfflineRoomForGoods(shop) < PLAYERBOT_STALL_WEAK_TAKEOFF_FULL_CELLS;
#else
		return true;
#endif
	}

	// MT2009_PLUS_BOT_HERB_SURPLUS_V1 (declared in playerbot_town.h): the lines
	// of two hundred of a herb the bot's counter takes now - none without a
	// counter, with fewer than PLAYERBOT_HERB_SURPLUS_STALL_FREE_CELLS free
	// cells, or with the kind's PLAYERBOT_HERB_SURPLUS_STALL_LINES up already.
	// What it will not take goes to the storekeeper's box.
	int GetPlayerBotHerbStallLineRoom(LPCHARACTER ch, DWORD vnum)
	{
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		if (!ch || !PlayerBotHasCounter(ch))
			return 0;
		auto shop = ikashop::GetManager().GetShopByOwnerID(ch->GetPlayerID());
		if (!shop || BotOfflineRoomForGoods(shop) < PLAYERBOT_HERB_SURPLUS_STALL_FREE_CELLS)   // MT2009_PLUS_BOT_SHOP_MGMT_V1
			return 0;
		return std::max(0, PLAYERBOT_HERB_SURPLUS_STALL_LINES - BotOfflineLinesOf(shop, vnum));
#else
		(void)ch; (void)vnum;
		return 0;
#endif
	}

	bool RunPlayerBotFullClearout(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || !IsPlayerBotVillageMap(ch->GetMapIndex()) ||
				IsPlayerBotSidekickServing(ch) || ch->GetExchange())
			return false;
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, DWORD>::const_iterator last = s_mapPlayerBotFullClearoutAt.find(pid);
		if (last != s_mapPlayerBotFullClearoutAt.end() && dwNow - last->second < PLAYERBOT_FULL_CLEAROUT_GAP_MS)
			return false;
		if (!IsPlayerBotBagFull(ch) && !IsPlayerBotBagUnderPressure(ch))
			return false;
		std::map<DWORD, DWORD>::const_iterator full = s_mapPlayerBotSafeboxFullAt.find(pid);
		const bool boxFull = (full != s_mapPlayerBotSafeboxFullAt.end() &&
				dwNow - full->second < PLAYERBOT_BAG_ROOM_SAFEBOX_FULL_MS) ||
				(ch->GetQuestFlag(PLAYERBOT_SAFEBOX_PAID_FLAG) <= 0 && ch->GetGold() < PLAYERBOT_SAFEBOX_FEE);
		if (!boxFull || !IsPlayerBotStallFullForClearout(ch))
			return false;
		s_mapPlayerBotFullClearoutAt[pid] = dwNow ? dwNow : 1;

		std::vector<std::pair<long long, LPITEM> > pieces;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell)
				continue;
			if ((int)item->GetRefineLevel() >= PLAYERBOT_MARKET_V3_BONUS_GOODS_PLUS &&
					(item->GetType() == ITEM_WEAPON || item->GetType() == ITEM_ARMOR))
				continue;
			if (IsPlayerBotPrizeItem(item) || IsPlayerBotSidekickGift(ch, item))
				continue;
			long long value = 0;
			if (GetPlayerBotBagRoomSaleKind(ch, item, value) == 0)
				continue;
			pieces.push_back(std::make_pair(value, item));
		}
		if (pieces.empty())
		{
			sys_log(0, "PLAYERBOT_ECONOMY: full clearout pid=%u name=%s sold=0 given=0 value=0 nothing_to_part_with=1",
					pid, ch->GetName());
			return false;
		}
		std::sort(pieces.begin(), pieces.end(),
				[](const std::pair<long long, LPITEM>& a, const std::pair<long long, LPITEM>& b) { return a.first < b.first; });
		// The village's other bots within reach, once.
		std::vector<LPCHARACTER> takers;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin();
				it != s_mapPlayerBotAIStates.end(); ++it)
		{
			if (it->first == pid)
				continue;
			LPCHARACTER other = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!other || other->GetMapIndex() != ch->GetMapIndex() || !other->IsItemLoaded() || other->IsDead() ||
					other->GetExchange() || other->GetMyShop() || IsPlayerBotSidekickPID(other->GetPlayerID()) ||
					DISTANCE_APPROX(other->GetX() - ch->GetX(), other->GetY() - ch->GetY()) > PLAYERBOT_BARTER_RANGE)
				continue;
			takers.push_back(other);
		}
		int sold = 0, given = 0;
		long long value = 0, gold = 0;
		const int target = std::min<int>(PLAYERBOT_FULL_CLEAROUT_MAX, (int)pieces.size());
		for (int i = 0; i < target; ++i)
		{
			LPITEM item = pieces[i].second;
			value += pieces[i].first;
			LPCHARACTER taker = NULL;
			if (item->GetType() == ITEM_WEAPON || item->GetType() == ITEM_ARMOR)
				for (size_t k = 0; k < takers.size() && !taker; ++k)
					if (IsPlayerBotUpgradeForSelf(takers[k], item) && takers[k]->GetEmptyInventory(item->GetSize()) >= 0)
						taker = takers[k];
			const DWORD vnum = item->GetVnum();
			state.mapStallUnsold.erase(item->GetID());
			state.mapStockFirstListed.erase(item->GetID());
			if (taker)
			{
				const int cell = taker->GetEmptyInventory(item->GetSize());
				ch->SyncQuickslot(QUICKSLOT_TYPE_ITEM, item->GetCell(), 255);
				item->RemoveFromCharacter();
				item->AddToCharacter(taker, TItemPos(INVENTORY, (WORD)cell));
				FlushPlayerBotItemRow(item);
				LogManager::instance().ItemLog(taker, item, "PLAYERBOT_FULL_CLEAROUT_GIFT", ch->GetName());
				sys_log(0, "PLAYERBOT_ECONOMY: full clearout gives pid=%u name=%s to=%u(%s) vnum=%u worth=%lld",
						pid, ch->GetName(), taker->GetPlayerID(), taker->GetName(), vnum, pieces[i].first);
				++given;
				continue;
			}
			const long long sale = GetPlayerBotJunkSalePrice(item);
			PlayerBotChangeGold(ch, sale);
			gold += sale;
			ITEM_MANAGER::instance().RemoveItem(item, "PLAYERBOT_FULL_CLEAROUT_SELL");
			++sold;
		}
		sys_log(0, "PLAYERBOT_ECONOMY: full clearout pid=%u name=%s sold=%d given=%d value=%lld gold=%lld short_of_min=%d free_cells=%d map=%ld",
				pid, ch->GetName(), sold, given, value, gold, sold + given < PLAYERBOT_FULL_CLEAROUT_MIN ? 1 : 0,
				CountPlayerBotFreeInventoryCells(ch), ch->GetMapIndex());
		return sold + given > 0;
	}

	bool TryPlayerBotBarter(TPlayerBotBarterSide& a, TPlayerBotBarterSide& b, DWORD now)
	{
		for (size_t i = 0; i < a.goods.size(); ++i)
		{
			LPITEM x = a.goods[i];
			if (!IsPlayerBotUpgradeForSelf(b.ch, x))
				continue;
			for (size_t k = 0; k < b.goods.size(); ++k)
			{
				LPITEM y = b.goods[k];
				if (!IsPlayerBotUpgradeForSelf(a.ch, y))
					continue;
				const long long vx = GetPlayerBotGearWorth(x, x->GetRefineLevel());
				const long long vy = GetPlayerBotGearWorth(y, y->GetRefineLevel());
				// The payer is the one who gets the dearer piece.
				LPCHARACTER payer = vy > vx ? a.ch : b.ch;
				LPCHARACTER payee = payer == a.ch ? b.ch : a.ch;
				const long long purse = std::max(0LL, (long long)payer->GetGold() - GetPlayerBotReservedGold(payer) -
						(long long)PLAYERBOT_SHOPPING_GOLD_FLOOR) * PLAYERBOT_BARTER_PURSE_PERCENT / 100;
				const long long topUp = playerbot_price_rules::BarterTopUp(vx, vy, PLAYERBOT_BARTER_TOPUP_MAX_PERCENT, purse);
				if (topUp < 0)
					continue;
				if (a.ch->GetEmptyInventory(y->GetSize()) < 0 || b.ch->GetEmptyInventory(x->GetSize()) < 0)
					continue;
				const DWORD xVnum = x->GetVnum(), yVnum = y->GetVnum();
				if (!MovePlayerBotBarterPiece(a.ch, b.ch, x))
					continue;
				if (!MovePlayerBotBarterPiece(b.ch, a.ch, y))
				{
					// No cell after all: the first piece goes back.
					MovePlayerBotBarterPiece(b.ch, a.ch, x);
					continue;
				}
				if (topUp > 0)
				{
					PlayerBotChangeGold(payer, -topUp);
					PlayerBotChangeGold(payee, topUp);
					s_llPlayerBotBarterTopUp += topUp;
				}
				s_mapPlayerBotBarterAt[a.ch->GetPlayerID()] = now ? now : 1;
				s_mapPlayerBotBarterAt[b.ch->GetPlayerID()] = now ? now : 1;
				++s_uPlayerBotBarters;
				sys_log(0, "PLAYERBOT_MARKET: barter %s(%u) gives vnum=%u worth=%lld, %s(%u) gives vnum=%u worth=%lld, top-up %lld paid by %s",
						a.ch->GetName(), a.ch->GetPlayerID(), xVnum, vx, b.ch->GetName(), b.ch->GetPlayerID(), yVnum, vy,
						topUp, payer->GetName());
				return true;
			}
		}
		return false;
	}

	void RunPlayerBotBarterPass(DWORD now)
	{
		std::map<long, std::vector<TPlayerBotBarterSide> > byMap;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin();
				it != s_mapPlayerBotAIStates.end(); ++it)
		{
			if (!IsPlayerBotWhimGapOver(s_mapPlayerBotBarterAt, it->first, PLAYERBOT_BARTER_BOT_GAP_MS))
				continue;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !ch->IsItemLoaded() || ch->IsDead() || ch->GetExchange() || ch->GetMyShop() || ch->GetShop() ||
					!IsPlayerBotVillageMap(ch->GetMapIndex()) || IsPlayerBotSidekickPID(ch->GetPlayerID()))
				continue;
			std::vector<TPlayerBotBarterSide>& sides = byMap[ch->GetMapIndex()];
			if (sides.size() >= PLAYERBOT_BARTER_BOTS_A_MAP)
				continue;
			TPlayerBotBarterSide side;
			side.ch = ch;
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS && side.goods.size() < PLAYERBOT_BARTER_ITEMS_A_BOT; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				if (item && item->GetCell() == cell && IsPlayerBotBarterGoods(ch, item))
					side.goods.push_back(item);
			}
			if (!side.goods.empty())
				sides.push_back(side);
		}
		int done = 0;
		for (std::map<long, std::vector<TPlayerBotBarterSide> >::iterator m = byMap.begin();
				m != byMap.end() && done < PLAYERBOT_BARTER_PER_PASS; ++m)
		{
			std::vector<TPlayerBotBarterSide>& sides = m->second;
			std::vector<bool> used(sides.size(), false);
			for (size_t i = 0; i < sides.size() && done < PLAYERBOT_BARTER_PER_PASS; ++i)
				for (size_t k = i + 1; k < sides.size() && !used[i]; ++k)
				{
					if (used[k] || DISTANCE_APPROX(sides[i].ch->GetX() - sides[k].ch->GetX(),
							sides[i].ch->GetY() - sides[k].ch->GetY()) > PLAYERBOT_BARTER_RANGE)
						continue;
					if (TryPlayerBotBarter(sides[i], sides[k], now))
					{
						used[i] = used[k] = true;
						++done;
					}
				}
		}
	}

	// ------------------------------------------------------------- the pass

	// Once a ledger pass (RefreshPlayerBotMarketLedger): the barter, and on the
	// report's pass a census line of the whole list's work since the last one.
	void RunPlayerBotMarketLifePass(DWORD dwNow, bool report)
	{
		RunPlayerBotBarterPass(dwNow);
		if (!report)
			return;
		sys_log(0, "PLAYERBOT_MARKET_LIFE: census bargains=%u impulses=%u whim_yang=%lld curious=%u barters=%u barter_topup=%lld "
				"l30_low=%d%% l30_on_counters=%lld shoproom=%s cuts=%u sold_units=%u gold=%lld",
				s_uPlayerBotBargains, s_uPlayerBotImpulses, s_llPlayerBotWhimYang, s_uPlayerBotCuriousPicks,
				s_uPlayerBotBarters, s_llPlayerBotBarterTopUp, GetPlayerBotLevel30LowPlusPercent(),
				s_llPlayerBotL30LowSupply, IsPlayerBotMaterialMarketTestOn() ? "on" : "off",
				s_uPlayerBotShopRoomCuts, s_uPlayerBotShopRoomSoldUnits, s_llPlayerBotShopRoomGold);
		s_uPlayerBotBargains = s_uPlayerBotImpulses = s_uPlayerBotCuriousPicks = s_uPlayerBotBarters = 0;
		s_uPlayerBotShopRoomCuts = s_uPlayerBotShopRoomSoldUnits = 0;
		s_llPlayerBotWhimYang = s_llPlayerBotBarterTopUp = s_llPlayerBotShopRoomGold = 0;
		// Yesterday's curious picks are let go.
		const DWORD day = (DWORD)(get_global_time() / 86400);
		for (std::map<DWORD, TPlayerBotCuriosity>::iterator it = s_mapPlayerBotCuriosity.begin();
				it != s_mapPlayerBotCuriosity.end(); )
		{
			if (it->second.day != day)
				s_mapPlayerBotCuriosity.erase(it++);
			else
				++it;
		}
	}
}

#endif
