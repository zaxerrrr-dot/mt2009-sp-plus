#ifndef __INC_METIN2_PLAYERBOT_SM_COUPONS_H__
#define __INC_METIN2_PLAYERBOT_SM_COUPONS_H__

// MT2009_PLUS_BOT_SM_COUPON_MARKET_V1 - a bot short of Smocze Monety for a need buys a Kupon SM on the market (the owner,
// 3 November 2026: "Do Yohara update dodaj botom mozliwosc kupowania SM z rynku. Jesli nie maja SM do wydania, a
// potrzebuja cos zakupic w ItemShopie, to sprawdzaja kupony na rynku i je kupuja").
//
// The coupons: every Kupon SM is an ITEM_QUEST whose value0 is the coins a piece - 80032 (10), 80031 (20), 80017 (50),
// 80014 (100), 80018 (250), 80015 (500), 80016 (1000) (IsPlayerBotSmCouponVnum, playerbot_types.h). A player cashes one
// by its quest (the package's itemshop quest for 80014-80018, worldboss_kupony.quest for 80031 / 80032 - pc.charge_cash);
// a bot by the voucher pass (UsePlayerBotVoucher, playerbot_itemshop.h: AddCash through the db core, the stack at once).
// They come into the world from the Metins and bosses (80014 since kupon100), the Battle Pass and the wheel (80017,
// 80018) and Boss Swiata (80031 / 80032); a bot whose needs the balance covers lists half of them on its counter
// (MT2009_PLUS_MARKET_LIFE_V1, point 6), people list theirs.
//
// The need - only a real one, as the ItemShop's own rules have it ("tylko gdy ich potrzebuja - nie na zapas"):
//   * noted where a need's purchase in Smocze Monety is refused for want of coins (NotePlayerBotSmShortfall): a V3 goal's
//     batch (BuyPlayerBotIshop3Pieces - the batch's rest at its cheapest line a piece, the goals' need and hold caps
//     already applied), a V3 line (BuyPlayerBotIshop3Line), the Sung Ma premium, the element pet and the element stone.
//     Never a look (costume, hairstyle, skin, pet, mount, the counter's hairstyle), a set chest, the beans (bought in V3
//     only when cheaper in yang than the Alchemist's), a Loch ticket (sold on the counters itself) nor a COMFORT need of
//     the catalogue; never a companion (its owner's coins). A purchase refused by the daily pool while the balance
//     would pay is no shortfall - the bot has the coins.
//   * the shortfall is the coins the purchase lacked, at most PLAYERBOT_SM_COUPON_SHORT_MAX, kept as the balance the
//     need wants (the balance then plus the shortfall); the gap is that less the balance now, the coupons in the bag and
//     those bought and not yet delivered. A need not noted again within PLAYERBOT_SM_COUPON_NEED_TTL_MS is gone (the
//     goals ask every few minutes while one is open).
// The purchase: from the offline shopping pass (ManagePlayerBotOfflineShopping, before the other picks), on every
// stand of the map (bots' and people's), at most every PLAYERBOT_SM_COUPON_LOOK_MS: the coupon - or the part of a stack -
// that covers the gap with the least overshoot (no more than the gap again, or 100 coins), the cheapest that covers it,
// else the cheapest a coin; at most PLAYERBOT_SM_COUPON_PRICE_CAP_PCT of its coins' worth at the market's rate (the
// price sheet's Kupon SM (100), GetPlayerBotSmCouponYangPerCoin - 20 000 yang a coin on the yang-rate curve, the world-yang
// inflation clamped; MT2009_PLUS_BOT_SM_COUPON_PRICE_V1, playerbot_town.h: the rate the bots' own coupon lines ask, at
// most 105% of it, so a bot's line is another bot's buy) and out of
// PLAYERBOT_SM_COUPON_PURSE_PCT of what the bot can spare (its gold less its reserves and the floor); a person's line
// also within the bots' cap on a person's price. PLAYERBOT_SM_COUPON_DAY_COUPONS coupons and
// PLAYERBOT_SM_COUPON_DAY_COINS coins a bot a day at most. A Sung Ma bot goes home to its first village's stands for one
// (the "buy" trip, WantsPlayerBotSmCouponFromMarket - while a counter of the core holds a coupon).
// Then: the coupon is cashed by the voucher pass at its next look (a bot with an open need never keeps a coupon for its
// counter, nor lists one - PlayerBotKeepsVouchersForCounter / IsPlayerBotVoucherForCounter); the coins of a market
// coupon go over the daily pool's allowance (NotePlayerBotSmPoolBonus - the bot's own yang paid for them) and the V3
// goals look again at once; the purchase that waited is made by its own pass.
//
// The log: PLAYERBOT_SMKUPON - shortfall (opened / raised), goes for a coupon, none on the market (throttled), bought,
// cashed, purchase unblocked; the census every ten minutes (with the ItemShop's): shortfalls by reason, looks, picks,
// none found, refused by price / by purse, day caps, coupons and coins bought, the yang paid, the coins cashed from the
// market's coupons, the purchases unblocked, the needs open.
//
// An implementation fragment: include it once, from playerbot_manager.cpp, after playerbot_yohara_guides.h (the
// itemshop's pool and voucher pass, the goals, the market's picks are all above).

#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_BOT_SM_COUPON_MARKET_V1)

namespace
{
	const DWORD PLAYERBOT_SM_COUPON_NEED_TTL_MS = 20 * 60 * 1000;
	const long long PLAYERBOT_SM_COUPON_SHORT_MAX = 500;
	const int PLAYERBOT_SM_COUPON_DAY_COUPONS = 4;
	const long long PLAYERBOT_SM_COUPON_DAY_COINS = 1000;
	const int PLAYERBOT_SM_COUPON_PRICE_CAP_PCT = 110;
	const int PLAYERBOT_SM_COUPON_PURSE_PCT = 50;
	const DWORD PLAYERBOT_SM_COUPON_LOOK_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_SM_COUPON_INFLIGHT_MS = 3 * 60 * 1000;
	const DWORD PLAYERBOT_SM_COUPON_UNBLOCK_MS = 30 * 60 * 1000;
	const long long PLAYERBOT_SM_COUPON_OVERSHOOT_MIN = 100;
	const DWORD PLAYERBOT_SM_COUPON_VNUMS[] = { 80032, 80031, 80017, 80014, 80018, 80015, 80016 };

	struct TPlayerBotSmCouponNeed
	{
		long long llTarget = 0;		// the balance the need wants
		DWORD dwNoted = 0;		// 0: no need open
		const char* szReason = "";	// a literal or a catalogue need's name (static)
		DWORD dwVnum = 0;
		DWORD dwNextLook = 0;
		long lDay = 0;
		int iDayCoupons = 0;
		long long llDayCoins = 0;
		long long llPending = 0;	// bought, not delivered yet
		DWORD dwPendingUntil = 0;
		long long llMarketCoins = 0;	// bought on the market, not cashed yet
		DWORD dwCashedAt = 0;		// the last market coupon cashed (the unblocked count)
	};
	std::map<DWORD, TPlayerBotSmCouponNeed> s_mapPlayerBotSmCouponNeed;

	struct TPlayerBotSmCouponStats
	{
		unsigned int uShortfalls = 0, uRaised = 0, uLooks = 0, uPicks = 0, uNoOffer = 0, uRefusedPrice = 0,
				uRefusedPurse = 0, uDayCap = 0, uBoughtCoupons = 0, uBuys = 0, uCashes = 0, uUnblocked = 0;
		long long llBoughtCoins = 0, llYang = 0, llCashedCoins = 0, llOtherCashed = 0;
		std::map<std::string, unsigned int> byReason;
	};
	TPlayerBotSmCouponStats s_kPlayerBotSmCoupons;

	long long GetPlayerBotSmCouponValue(DWORD vnum)
	{
		if (!IsPlayerBotSmCouponVnum(vnum))
			return 0;
#ifdef MT2009_PLUS_BOT_SM_COUPON_PRICE_V1
		return GetPlayerBotSmCouponCoinsOf(vnum);
#else
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		return proto ? std::max<long long>(0, proto->alValues[0]) : 0;
#endif
	}

	// The yang a coin is worth to a buyer of a coupon - the one rate the bots' coupon lines ask by
	// (MT2009_PLUS_BOT_SM_COUPON_PRICE_V1); the V3 goals' own rate before it.
	long long GetPlayerBotSmCouponBuyRate()
	{
#ifdef MT2009_PLUS_BOT_SM_COUPON_PRICE_V1
		return GetPlayerBotSmCouponYangPerCoin();
#else
		return GetPlayerBotIshop3YangPerCoin();
#endif
	}

	// The coins of the coupons in the bag (every cell, as the voucher pass reads it).
	long long CountPlayerBotSmCouponCoins(LPCHARACTER ch)
	{
		long long coins = 0;
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && IsPlayerBotSmCouponVnum(item->GetVnum()))
				coins += GetPlayerBotSmCouponValue(item->GetVnum()) * (long long)item->GetCount();
		}
		return coins;
	}

	void RollPlayerBotSmCouponDay(TPlayerBotSmCouponNeed& n)
	{
		const long day = (long)(get_global_time() / 86400);
		if (n.lDay != day)
		{
			n.lDay = day;
			n.iDayCoupons = 0;
			n.llDayCoins = 0;
		}
	}

	// What a need's reason may buy a coupon for (the header's list).
	bool IsPlayerBotSmCouponReason(const char* reason)
	{
		if (!reason || !*reason)
			return false;
		const char* category = GetPlayerBotIshop3Category(reason);
		// (the old wishes' list buys only what the balance pays - CanPlayerBotAffordWish - and never reaches here)
		if (strcmp(category, "look") == 0 || strcmp(category, "chest") == 0 || strcmp(category, "bean") == 0 ||
				strcmp(category, "loch") == 0)
			return false;
		for (int need = 0; need < PLAYERBOT_ISHOP3_NEED_COUNT; ++need)
			if (strcmp(reason, PLAYERBOT_ISHOP3_NEED_NAMES[need]) == 0)
				return PLAYERBOT_ISHOP3_NEED_CLASS[need] == PLAYERBOT_ISHOP3_CLASS_USE;
		return true;
	}

	TPlayerBotSmCouponNeed* FindPlayerBotSmCouponNeed(DWORD pid, DWORD dwNow)
	{
		std::map<DWORD, TPlayerBotSmCouponNeed>::iterator it = s_mapPlayerBotSmCouponNeed.find(pid);
		if (it == s_mapPlayerBotSmCouponNeed.end() || it->second.dwNoted == 0)
			return NULL;
		if (dwNow - it->second.dwNoted >= PLAYERBOT_SM_COUPON_NEED_TTL_MS)
		{
			it->second.dwNoted = 0;	// gone; the day's counts and the coins on their way stay
			return NULL;
		}
		return &it->second;
	}

	// The coins the open need still lacks: the balance it wants less the balance now, and (bag) the coupons in the bag
	// and on their way. 0: no need.
	long long GetPlayerBotSmCouponGap(LPCHARACTER ch, const TPlayerBotAIState& state, bool bag)
	{
		if (!ch || !state.bDragonBalanceKnown || !IsPlayerBotItemShopEnabled() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return 0;
		const DWORD now = get_dword_time();
		TPlayerBotSmCouponNeed* n = FindPlayerBotSmCouponNeed(ch->GetPlayerID(), now);
		if (!n)
			return 0;
		long long gap = n->llTarget - (long long)state.iDragonCoins;
		if (bag)
		{
			gap -= CountPlayerBotSmCouponCoins(ch);
			if (n->llPending > 0 && (int)(n->dwPendingUntil - now) > 0)
				gap -= n->llPending;
		}
		return std::max(0LL, std::min(gap, PLAYERBOT_SM_COUPON_SHORT_MAX));
	}

	const TPlayerBotAIState* FindPlayerBotSmCouponState(LPCHARACTER ch)
	{
		if (!ch)
			return NULL;
		TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		return st != s_mapPlayerBotAIStates.end() ? &st->second : NULL;
	}

	long long GetPlayerBotSmCouponNeed(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		return GetPlayerBotSmCouponGap(ch, state, true);
	}

	// An open need the balance does not cover - the bag's coupons are for it (cashed, never kept for the counter).
	bool HasPlayerBotSmCouponNeed(LPCHARACTER ch)
	{
		const TPlayerBotAIState* state = FindPlayerBotSmCouponState(ch);
		return state && GetPlayerBotSmCouponGap(ch, *state, false) > 0;
	}

	bool IsPlayerBotSmCouponDayFull(TPlayerBotSmCouponNeed& n)
	{
		RollPlayerBotSmCouponDay(n);
		return n.iDayCoupons >= PLAYERBOT_SM_COUPON_DAY_COUPONS || n.llDayCoins >= PLAYERBOT_SM_COUPON_DAY_COINS;
	}

	void NotePlayerBotSmShortfall(LPCHARACTER ch, const TPlayerBotAIState& state, long long coins, const char* reason,
			DWORD vnum, DWORD dwNow)
	{
		if (!ch || coins <= 0 || !state.bDragonBalanceKnown || !IsPlayerBotItemShopEnabled() ||
				IsPlayerBotSidekickPID(ch->GetPlayerID()) || !IsPlayerBotSmCouponReason(reason))
			return;
		coins = std::min(coins, PLAYERBOT_SM_COUPON_SHORT_MAX);
		const long long target = (long long)state.iDragonCoins + coins;
		const bool open = FindPlayerBotSmCouponNeed(ch->GetPlayerID(), dwNow) != NULL;
		TPlayerBotSmCouponNeed& n = s_mapPlayerBotSmCouponNeed[ch->GetPlayerID()];
		const bool raised = open && target > n.llTarget;
		if (!open || raised)
		{
			n.llTarget = open ? std::max(n.llTarget, target) : target;
			n.szReason = reason;
			n.dwVnum = vnum;
			++(open ? s_kPlayerBotSmCoupons.uRaised : s_kPlayerBotSmCoupons.uShortfalls);
			++s_kPlayerBotSmCoupons.byReason[GetPlayerBotIshop3Category(reason)];
			sys_log(0, "PLAYERBOT_SMKUPON: shortfall %s pid=%u name=%s lv=%d reason=%s vnum=%u short=%lld coins=%d target=%lld "
					"bag_coupons=%lld gold=%lld", open ? "raised" : "opened", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(),
					reason, vnum, coins, state.iDragonCoins, n.llTarget, CountPlayerBotSmCouponCoins(ch), (long long)ch->GetGold());
		}
		n.dwNoted = dwNow ? dwNow : 1;
	}

	// 0 the price is right, 1 over the coins' worth, 2 over the purse's share.
	int CheckPlayerBotSmCouponPrice(LPCHARACTER ch, long long coins, long long price)
	{
		if (coins <= 0 || price <= 0)
			return 1;
		const long long cap = coins * GetPlayerBotSmCouponBuyRate() * PLAYERBOT_SM_COUPON_PRICE_CAP_PCT / 100;
		if (price > cap)
			return 1;
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		if (price > spare * PLAYERBOT_SM_COUPON_PURSE_PCT / 100)
			return 2;
		return 0;
	}

	// The coins an offer brings may be bought for the gap: within the day's caps and the overshoot.
	bool IsPlayerBotSmCouponFit(TPlayerBotSmCouponNeed& n, long long gap, long long coins, int units)
	{
		if (gap <= 0 || coins <= 0 || units <= 0 || IsPlayerBotSmCouponDayFull(n))
			return false;
		if (n.iDayCoupons + units > PLAYERBOT_SM_COUPON_DAY_COUPONS || n.llDayCoins + coins > PLAYERBOT_SM_COUPON_DAY_COINS)
			return false;
		return coins <= gap + std::max(gap, PLAYERBOT_SM_COUPON_OVERSHOOT_MIN);
	}

	bool WantsPlayerBotSmCouponOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer || !IsPlayerBotSmCouponVnum(offer->GetVnum()))
			return false;
		const TPlayerBotAIState* state = FindPlayerBotSmCouponState(ch);
		if (!state)
			return false;
		const long long gap = GetPlayerBotSmCouponGap(ch, *state, true);
		if (gap <= 0)
			return false;
		TPlayerBotSmCouponNeed& n = s_mapPlayerBotSmCouponNeed[ch->GetPlayerID()];
		const int units = (int)std::max<long long>(1, (long long)offer->GetCount());
		return IsPlayerBotSmCouponFit(n, gap, GetPlayerBotSmCouponValue(offer->GetVnum()) * units, units);
	}

	bool CanPlayerBotPayForSmCoupon(LPCHARACTER ch, LPITEM item, long long price)
	{
		if (!ch || !item)
			return false;
		const long long coins = GetPlayerBotSmCouponValue(item->GetVnum()) * std::max<long long>(1, (long long)item->GetCount());
		return CheckPlayerBotSmCouponPrice(ch, coins, price) == 0;
	}

	bool WantsPlayerBotSmCouponFromMarket(LPCHARACTER ch)
	{
		const TPlayerBotAIState* state = FindPlayerBotSmCouponState(ch);
		if (!state || GetPlayerBotSmCouponGap(ch, *state, true) <= 0)
			return false;
		if (IsPlayerBotSmCouponDayFull(s_mapPlayerBotSmCouponNeed[ch->GetPlayerID()]))
			return false;
		for (size_t i = 0; i < sizeof(PLAYERBOT_SM_COUPON_VNUMS) / sizeof(PLAYERBOT_SM_COUPON_VNUMS[0]); ++i)
		{
			const TPlayerBotMarketLedgerEntry* e = GetPlayerBotMarketLedgerEntry(PLAYERBOT_SM_COUPON_VNUMS[i]);
			if (e && e->dwSupplyUnits > 0)
				return true;
		}
		return false;
	}

#if defined(ENABLE_IKASHOP_RENEWAL)
	// The coupon for the gap on a stand of the map the bot can walk to (the gambler's scan): of the lines (or the part of
	// a stack) that fit the gap, the cheapest that covers it, else the cheapest a coin - the purchase's own tests asked of
	// the line. Handed to the buyer and claimed for the walk.
	bool FindPlayerBotSmCouponPick(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now)
	{
		using namespace playerbot_offline;
		if (!ch || !IsPlayerBotItemShopEnabled() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return false;
		const long long gap = GetPlayerBotSmCouponGap(ch, state, true);
		if (gap <= 0)
			return false;
		TPlayerBotSmCouponNeed& n = s_mapPlayerBotSmCouponNeed[ch->GetPlayerID()];
		if (n.dwNextLook != 0 && (int)(now - n.dwNextLook) < 0)
			return false;
		n.dwNextLook = now + PLAYERBOT_SM_COUPON_LOOK_MS;
		if (IsPlayerBotSmCouponDayFull(n))
		{
			++s_kPlayerBotSmCoupons.uDayCap;
			PlayerBotLogThrottled("smkupon_day_cap", now, "PLAYERBOT_SMKUPON: day cap pid=%u name=%s coupons=%d coins=%lld gap=%lld",
					ch->GetPlayerID(), ch->GetName(), n.iDayCoupons, n.llDayCoins, gap);
			return false;
		}
		++s_kPlayerBotSmCoupons.uLooks;
		const int shopChannel = CPlayerBotManager::instance().IsChannelTableMode()
				? playerbot_channel_rules::SHOP_CHANNEL : (int)g_bChannel;
		CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(ch->GetMapIndex());
		const bool haveNav = navigation.Init(ch->GetMapIndex());
		DWORD bestOwner = 0, bestItem = 0, bestPart = 0, bestVnum = 0;
		long long bestPrice = 0, bestCoins = 0;
		bool bestCovers = false;
		bool sawPrice = false, sawPurse = false, sawAny = false;
		const int dayUnits = PLAYERBOT_SM_COUPON_DAY_COUPONS - n.iDayCoupons;
		for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
		{
			if (!shop || pid == ch->GetPlayerID() || shop->GetDuration() == 0 || shop->IsEditMode())
				continue;
			const auto spawn = shop->GetSpawn();
			if (spawn.map != ch->GetMapIndex() || (int)spawn.channel != shopChannel)
				continue;
			int reach = -1;
			for (const auto& [id, line] : shop->GetItems())
			{
				if (!line || !IsPlayerBotSmCouponVnum(line->GetInfo().vnum) || IsPlayerBotLineClaimedByOther(id, ch->GetPlayerID(), now))
					continue;
				const DWORD vnum = line->GetInfo().vnum;
				const long long value = GetPlayerBotSmCouponValue(vnum);
				const long long count = std::max<long long>(1, (long long)line->GetInfo().count);
				const long long lineYang = (long long)line->GetPrice().GetTotalYangAmount();
				if (value <= 0 || lineYang <= 0)
					continue;
				sawAny = true;
				// the units the gap takes (rounded up), within the day's coupons; a part of a bigger stack
				long long units = std::min<long long>(count, std::max<long long>(1, (gap + value - 1) / value));
				units = std::min<long long>(units, std::max(0, dayUnits));
				if (units <= 0)
					continue;
				DWORD part = 0;
				long long price = lineYang;
				if (units < count)
				{
					const long long partYang = IsPlayerBotPartBuyOn() ? PlayerBotPartPrice(lineYang, count, units) : 0;
					if (partYang <= 0)
						continue;
					part = (DWORD)units;
					price = partYang;
				}
				const long long coins = value * units;
				if (!IsPlayerBotSmCouponFit(n, gap, coins, (int)units))
					continue;
				const int check = CheckPlayerBotSmCouponPrice(ch, coins, price);
				if (check != 0)
				{
					(check == 1 ? sawPrice : sawPurse) = true;
					continue;
				}
				const bool covers = coins >= gap;
				// the cheapest that covers the gap; else the cheapest a coin
				bool better = !bestOwner;
				if (!better && covers != bestCovers)
					better = covers;
				else if (!better && covers)
					better = price < bestPrice;
				else if (!better)
					better = price * bestCoins < bestPrice * coins;
				if (!better)
					continue;
				if (reach < 0)
					reach = !haveNav || navigation.CanReach(ch->GetX(), ch->GetY(), spawn.x, spawn.y) ? 1 : 0;
				if (reach == 0)
					break;
				LPITEM preview = BotOfflinePreview(*line);
				if (!preview)
					continue;
				if (part)
					preview->SetCount(part);
				const bool buyable = WantsPlayerBotStallItem(ch, preview) &&
						CanPlayerBotPayForOffer(ch, preview, price, shop->GetOwnerPID()) && ch->GetEmptyInventory(preview->GetSize()) >= 0;
				M2_DELETE(preview);
				if (!buyable)
				{
					sawPrice = true;	// a person's line over the bots' cap on a person's price (or no room)
					continue;
				}
				bestOwner = shop->GetOwnerPID();
				bestItem = id;
				bestPart = part;
				bestVnum = vnum;
				bestPrice = price;
				bestCoins = coins;
				bestCovers = covers;
			}
		}
		if (!bestOwner)
		{
			if (sawPurse)
				++s_kPlayerBotSmCoupons.uRefusedPurse;
			else if (sawPrice)
				++s_kPlayerBotSmCoupons.uRefusedPrice;
			else
				++s_kPlayerBotSmCoupons.uNoOffer;
			PlayerBotLogThrottled("smkupon_none", now,
					"PLAYERBOT_SMKUPON: none bought pid=%u name=%s map=%ld gap=%lld reason=%s why=%s gold=%lld yang_per_coin=%lld",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), gap, n.szReason,
					sawPurse ? "purse" : sawPrice ? "price" : sawAny ? "no_fit" : "no_offer", (long long)ch->GetGold(),
					GetPlayerBotSmCouponBuyRate());
			return false;
		}
		auto& o = state.offlineShop;
		o.buyOwner = bestOwner;
		o.buyItem = bestItem;
		o.buyQuantity = bestPart;
		o.buyUntil = now + PLAYERBOT_MARKET_FAR_PICK_WALK_MS;
		o.farBuy = false;
		ClaimPlayerBotLineUntil(bestItem, ch->GetPlayerID(), now, o.buyUntil);
		++s_kPlayerBotSmCoupons.uPicks;
		sys_log(0, "PLAYERBOT_SMKUPON: goes for a coupon pid=%u name=%s owner=%u item=%u vnum=%u part=%u coins=%lld price=%lld "
				"gap=%lld reason=%s person=%d gold=%lld", ch->GetPlayerID(), ch->GetName(), bestOwner, bestItem, bestVnum,
				bestPart, bestCoins, bestPrice, gap, n.szReason, CPlayerBotManager::instance().IsRegisteredBotPID(bestOwner) ? 0 : 1,
				(long long)ch->GetGold());
		return true;
	}
#endif

	// The purchase asked of the engine (RunPlayerBotOfflinePick, every buy of a coupon - the browse's too).
	void NotePlayerBotSmCouponBought(LPCHARACTER ch, DWORD vnum, long long price, DWORD count)
	{
		if (!ch || !IsPlayerBotSmCouponVnum(vnum) || count == 0)
			return;
		const long long coins = GetPlayerBotSmCouponValue(vnum) * (long long)count;
		TPlayerBotSmCouponNeed& n = s_mapPlayerBotSmCouponNeed[ch->GetPlayerID()];
		RollPlayerBotSmCouponDay(n);
		n.iDayCoupons += (int)count;
		n.llDayCoins += coins;
		const DWORD now = get_dword_time();
		n.llPending = (int)(n.dwPendingUntil - now) > 0 ? n.llPending + coins : coins;
		n.dwPendingUntil = now + PLAYERBOT_SM_COUPON_INFLIGHT_MS;
		n.llMarketCoins += coins;
		++s_kPlayerBotSmCoupons.uBuys;
		s_kPlayerBotSmCoupons.uBoughtCoupons += count;
		s_kPlayerBotSmCoupons.llBoughtCoins += coins;
		s_kPlayerBotSmCoupons.llYang += price;
		sys_log(0, "PLAYERBOT_SMKUPON: bought pid=%u name=%s vnum=%u count=%u coins=%lld price=%lld yang_per_coin=%lld reason=%s "
				"day_coupons=%d day_coins=%lld gold=%lld", ch->GetPlayerID(), ch->GetName(), vnum, (unsigned int)count, coins, price,
				coins > 0 ? price / coins : 0LL, n.szReason, n.iDayCoupons, n.llDayCoins, (long long)ch->GetGold());
	}

	// The voucher pass cashed coupons (UsePlayerBotVoucher): the market's coins over the daily pool, the goals at once.
	void NotePlayerBotSmCouponsCashed(LPCHARACTER ch, long long coins, DWORD dwNow)
	{
		if (!ch || coins <= 0)
			return;
		std::map<DWORD, TPlayerBotSmCouponNeed>::iterator it = s_mapPlayerBotSmCouponNeed.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotSmCouponNeed.end())
			return;
		TPlayerBotSmCouponNeed& n = it->second;
		const long long market = std::min(coins, n.llMarketCoins);
		const bool open = n.dwNoted != 0;
		if (market <= 0 && !open)
			return;
		if (market > 0)
		{
			n.llMarketCoins -= market;
			n.llPending = 0;
			n.dwPendingUntil = 0;
			n.dwCashedAt = dwNow ? dwNow : 1;
			++s_kPlayerBotSmCoupons.uCashes;
			s_kPlayerBotSmCoupons.llCashedCoins += market;
#ifdef MT2009_PLUS_BOT_SM_DAILY_POOL_V1
			NotePlayerBotSmPoolBonus(ch, market);
#endif
			// the goal that waited looks again at once (playerbot_ishop3_goals.h)
			s_mapPlayerBotIshop3NextGoal[ch->GetPlayerID()] = dwNow;
		}
		if (coins > market && open)
			s_kPlayerBotSmCoupons.llOtherCashed += coins - market;
		sys_log(0, "PLAYERBOT_SMKUPON: cashed pid=%u name=%s coins=%lld market=%lld need_open=%d reason=%s target=%lld",
				ch->GetPlayerID(), ch->GetName(), coins, market, (int)open, n.szReason, n.llTarget);
	}

	// A purchase in Smocze Monety made (BuyPlayerBotIshop3Line): one a market coupon unblocked is counted once.
	void NotePlayerBotSmCouponPurchase(LPCHARACTER ch, const char* reason)
	{
		if (!ch)
			return;
		std::map<DWORD, TPlayerBotSmCouponNeed>::iterator it = s_mapPlayerBotSmCouponNeed.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotSmCouponNeed.end() || it->second.dwCashedAt == 0)
			return;
		TPlayerBotSmCouponNeed& n = it->second;
		const DWORD now = get_dword_time();
		const bool recent = now - n.dwCashedAt < PLAYERBOT_SM_COUPON_UNBLOCK_MS;
		n.dwCashedAt = 0;
		if (!recent)
			return;
		++s_kPlayerBotSmCoupons.uUnblocked;
		sys_log(0, "PLAYERBOT_SMKUPON: purchase unblocked pid=%u name=%s reason=%s need=%s", ch->GetPlayerID(), ch->GetName(),
				reason ? reason : "-", n.szReason);
	}

	void WritePlayerBotSmCouponCensus(DWORD dwNow)
	{
		TPlayerBotSmCouponStats& s = s_kPlayerBotSmCoupons;
		// MT2009_PLUS_BOT_SM_COUPON_PRICE_V1: the coupon lines on the bots' counters of this core, those out of the coin
		// rule's band (put right at their keepers' next service) and those put right since the last census.
		unsigned int lines = 0, outOfBand = 0;
		long long lineCoins = 0;
#if defined(ENABLE_IKASHOP_RENEWAL) && defined(MT2009_PLUS_BOT_SM_COUPON_PRICE_V1)
		for (const auto& [pid, shop] : ikashop::GetManager().GetPlayerBotOfflineShops())
		{
			if (!shop || !CPlayerBotManager::instance().IsRegisteredBotPID(shop->GetOwnerPID()))
				continue;	// the engine's ledger holds people's counters too - never theirs
			for (const auto& [id, line] : shop->GetItems())
			{
				if (!line || !IsPlayerBotSmCouponVnum(line->GetInfo().vnum))
					continue;
				const long long count = std::max<long long>(1, (long long)line->GetInfo().count);
				++lines;
				lineCoins += GetPlayerBotSmCouponValue(line->GetInfo().vnum) * count;
				if (IsPlayerBotSmCouponPriceOutOfBand(line->GetInfo().vnum, count, (long long)line->GetPrice().GetTotalYangAmount()))
					++outOfBand;
			}
		}
#endif
		unsigned int repriced = 0;
#ifdef MT2009_PLUS_BOT_SM_COUPON_PRICE_V1
		repriced = s_uPlayerBotSmCouponRepriced;
		s_uPlayerBotSmCouponRepriced = 0;
#endif
		unsigned int open = 0;
		const long today = (long)(get_global_time() / 86400);
		for (std::map<DWORD, TPlayerBotSmCouponNeed>::iterator it = s_mapPlayerBotSmCouponNeed.begin();
				it != s_mapPlayerBotSmCouponNeed.end();)
		{
			TPlayerBotSmCouponNeed& n = it->second;
			if (n.dwNoted != 0 && dwNow - n.dwNoted >= PLAYERBOT_SM_COUPON_NEED_TTL_MS)
				n.dwNoted = 0;
			if (n.dwNoted != 0)
				++open;
			// a bot with nothing open, nothing on its way and no purchase today is forgotten
			if (n.dwNoted == 0 && n.llMarketCoins <= 0 && n.lDay != today)
				s_mapPlayerBotSmCouponNeed.erase(it++);
			else
				++it;
		}
		if (s.uShortfalls == 0 && s.uRaised == 0 && s.uLooks == 0 && s.uBuys == 0 && s.uCashes == 0 && open == 0 &&
				lines == 0 && repriced == 0)
			return;
		std::string reasons;
		for (std::map<std::string, unsigned int>::const_iterator r = s.byReason.begin(); r != s.byReason.end(); ++r)
		{
			char buf[64];
			snprintf(buf, sizeof(buf), "%s%s:%u", reasons.empty() ? "" : ",", r->first.c_str(), r->second);
			reasons += buf;
		}
		sys_log(0, "PLAYERBOT_SMKUPON: census shortfalls=%u raised=%u by=%s looks=%u picks=%u no_offer=%u refused_price=%u "
				"refused_purse=%u day_cap=%u buys=%u coupons=%u coins_bought=%lld yang=%lld cashed=%u sm_gained=%lld "
				"other_cashed_for_need=%lld unblocked=%u open=%u yang_per_coin=%lld counter_lines=%u counter_coins=%lld "
				"out_of_band=%u repriced=%u",
				s.uShortfalls, s.uRaised, reasons.empty() ? "-" : reasons.c_str(), s.uLooks, s.uPicks, s.uNoOffer,
				s.uRefusedPrice, s.uRefusedPurse, s.uDayCap, s.uBuys, s.uBoughtCoupons, s.llBoughtCoins, s.llYang, s.uCashes,
				s.llCashedCoins, s.llOtherCashed, s.uUnblocked, open, GetPlayerBotSmCouponBuyRate(), lines, lineCoins,
				outOfBand, repriced);
		s = TPlayerBotSmCouponStats();
	}
}

#endif

#endif
