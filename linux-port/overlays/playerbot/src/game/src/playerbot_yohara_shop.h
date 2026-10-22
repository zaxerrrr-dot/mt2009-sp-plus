#ifndef __INC_METIN2_PLAYERBOT_YOHARA_SHOP_H__
#define __INC_METIN2_PLAYERBOT_YOHARA_SHOP_H__

// MT2009_PLUS_BOT_YOHARA_SHOP_V1 - the bots' exchange in Dongan and their world set (the owner, 22 October 2026: list
// item 24 of boty-yohara-lista.md, and "Ekstra: sklep specjalny dla botow w Dongan").
//
// The exchange (bots only - no NPC, no shop window, nothing a person ever sees): at Handlarka Roznosci (9003, Dongan
// 373, the merchant Dongan's errand calls on - playerbot_yohara_sungma.h) a Champion bot changes
//   * 10 Materialy Rzemieslnicze (30378) for 1 elixir of RESISTANCE to an element of its map (50836-50841), and
//   * 10 Magiczny Pyl (30360) for 1 elixir of POWER of an element of its map (50830-50835) - the dust only above its
//     G0 reserve (GetPlayerBotG0DustReserve: a saver's 400 are never touched; banked dust is in the box anyway).
// "Its map" is the map its elements are taken for (GetPlayerBotYoharaElementMap - its Sung Ma stay's map, never Dongan
// on an errand) and an element of it one of PLAYERBOT_YOHARA_ELEMENT_DEFENCE_PERCENT or more (the table of
// playerbot_yohara_elements.h - both of the two-element maps, Namgan's wind and dark). The elixir is made as the
// cube makes it (CreateItem -> Blend_Item_set_value: 8-20% for 1-10 minutes, rolled).
//
// The stock: up to PLAYERBOT_YSHOP_TARGET of each kind the map needs; Dongan's errand is called for it when a kind is
// under PLAYERBOT_YSHOP_LOW and the bot holds the input for one (at most every PLAYERBOT_YSHOP_ERRAND_GAP_MS). The
// inputs it keeps and buys towards: ten for each elixir short of the target, at most PLAYERBOT_YSHOP_INPUT_MAX of
// each - the materials through the saddlebag's want (GetPlayerBotCraftMaterialsWanted: kept off the counters, bought
// off them at the material's caps, refine goods changed at the Dozorca), the dust through the counters' dust keep
// (over the G0 reserve) and its own market line (PLAYERBOT_YSHOP_DUST_PRICE_CAP_PCT of the bots' dust price, out of
// PLAYERBOT_YSHOP_DUST_PURSE_PCT of the spare purse). A trade trip home (reason "buy") also goes for them, when a kind
// is low and the market holds what is short. The elixirs - up to PLAYERBOT_YSHOP_KEEP_MAX of each of the twelve - are
// never sold by a Champion; they are drunk on the map (ManagePlayerBotYoharaElements: resistance and power).
//
// The world set (item 24): a Champion that owns jade jewellery (Obrecz / Kolia / Klipsy Jadeitu) keeps, for each of
// those slots, its best piece of other jewellery (the Emerald or whatever is best off Yohara) and its best jade -
// never the merchant's, a counter's or another bot's. Off the Sung Ma maps (Zaklety Las, the Rift, the Hydra, the
// dungeons, home) the Will of its lines counts nothing (GetPlayerBotSungmaWillWeight -> 0), so the gear's score puts
// the world piece on; on a Sung Ma map the Will counts and the jade goes back on. The swap is made at once, out of a
// fight, on the bot's own clock (ManagePlayerBotYoharaShop), the same score as the equipment pass. While dressed for the
// world the Will a Sung Ma map is checked against is the Will the jade in the bag would give
// (GetPlayerBotYoharaWorldSetWillDelta, in GetPlayerBotSungmaWill) - a bot does not step down for its world set.
//
// The log: PLAYERBOT_SHOP2 (exchange, errand wanted, dust/material bought, worldset swap, census every ten minutes).
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_yohara_elements_late.h.

namespace
{
	const DWORD PLAYERBOT_YSHOP_MATERIAL_VNUM = 30378;	// Materialy Rzemieslnicze
	const int PLAYERBOT_YSHOP_RATE = 10;	// inputs a elixir
	const DWORD PLAYERBOT_YSHOP_NPC = 9003;	// Handlarka Roznosci, Dongan
	const int PLAYERBOT_YSHOP_TARGET = 8;	// elixirs of a needed kind the exchange fills to
	const int PLAYERBOT_YSHOP_LOW = 4;	// under this the errand is called for it
	const int PLAYERBOT_YSHOP_KEEP_MAX = 10;	// elixirs of a vnum never sold
	const int PLAYERBOT_YSHOP_INPUT_MAX = 100;	// materials / dust over the reserves wanted at most
	const int PLAYERBOT_YSHOP_FREE_CELLS = 4;	// free cells left in the bag after an elixir
	const DWORD PLAYERBOT_YSHOP_ERRAND_GAP_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_YSHOP_NEED_MS = 30 * 1000;
	const DWORD PLAYERBOT_YSHOP_TICK_MS = 5 * 1000;
	const DWORD PLAYERBOT_YSHOP_DRESS_LOOK_MS = 60 * 1000;	// the dress looked at again without a change of map
	const DWORD PLAYERBOT_YSHOP_CENSUS_MS = 10 * 60 * 1000;
	const int PLAYERBOT_YSHOP_DUST_PRICE_CAP_PCT = 150;
	const int PLAYERBOT_YSHOP_DUST_PURSE_PCT = 25;
	const int PLAYERBOT_YSHOP_LINE_SLACK = 20;	// a market line at most this much over what is short
	const BYTE PLAYERBOT_YSHOP_JEWEL_WEARS[3] = { WEAR_WRIST, WEAR_NECK, WEAR_EAR };

	struct TPlayerBotYoharaShopNeed
	{
		DWORD dwAt;
		long lMap;
		int iMaterials, iDust;	// inputs wanted (ten an elixir short of the target, capped)
		bool bLow;	// a needed kind under PLAYERBOT_YSHOP_LOW
		bool abResist[PLAYERBOT_YOHARA_ELEMENTS], abPower[PLAYERBOT_YOHARA_ELEMENTS];
		TPlayerBotYoharaShopNeed() : dwAt(0), lMap(0), iMaterials(0), iDust(0), bLow(false)
		{
			for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
				abResist[e] = abPower[e] = false;
		}
	};
	std::map<DWORD, TPlayerBotYoharaShopNeed> s_mapPlayerBotYoharaShopNeed;

	struct TPlayerBotYoharaShopBot
	{
		DWORD dwNextTick, dwLastErrand, dwKeptAt, dwWillAt, dwNextDressLook;
		int iDressed;	// -1 unknown, 0 world, 1 Sung Ma
		std::set<DWORD> setKept;	// world set and jade kept, item ids
		int aiWillDelta[4];
		TPlayerBotYoharaShopBot() : dwNextTick(0), dwLastErrand(0), dwKeptAt(0), dwWillAt(0), dwNextDressLook(0), iDressed(-1)
		{
			for (int i = 0; i < 4; ++i)
				aiWillDelta[i] = 0;
		}
	};
	std::map<DWORD, TPlayerBotYoharaShopBot> s_mapPlayerBotYoharaShopBot;

	struct TPlayerBotYoharaShopStats
	{
		unsigned int resistMade, powerMade, materialsPaid, dustPaid, errands, dustBought, materialsBought, swaps;
		DWORD dwCensusAt;
		TPlayerBotYoharaShopStats() : resistMade(0), powerMade(0), materialsPaid(0), dustPaid(0), errands(0), dustBought(0),
			materialsBought(0), swaps(0), dwCensusAt(0) {}
	};
	TPlayerBotYoharaShopStats s_kPlayerBotYoharaShopStats;
	// MT2009_PLUS_BOT_YOHARA_SHOP_V1: the dress a score is asked for (0 where the bot stands, 1 Sung Ma, 2 the world).
	int s_iPlayerBotYoharaDressForce = 0;

	// ------------------------------------------------------------ who, and what it needs

	bool IsPlayerBotYoharaShopUser(LPCHARACTER ch)
	{
		return ch && IsPlayerBotSungmaWillUser(ch) && ch->IsItemLoaded() && !IsPlayerBotSidekickPID(ch->GetPlayerID());
	}

	int GetPlayerBotYoharaShopDustFree(LPCHARACTER ch)
	{
		return ch ? std::max(0, (int)ch->CountSpecifyItem(PLAYERBOT_MAGIC_DUST_VNUM) - GetPlayerBotG0DustReserve(ch)) : 0;
	}

	const TPlayerBotYoharaShopNeed* GetPlayerBotYoharaShopNeed(LPCHARACTER ch)
	{
		if (!IsPlayerBotYoharaShopUser(ch))
			return NULL;
		const long map = GetPlayerBotYoharaElementMap(ch);
		if (map == 0)
			return NULL;
		const DWORD now = get_dword_time();
		TPlayerBotYoharaShopNeed& n = s_mapPlayerBotYoharaShopNeed[ch->GetPlayerID()];
		if (n.dwAt != 0 && n.lMap == map && now - n.dwAt < PLAYERBOT_YSHOP_NEED_MS)
			return &n;
		n = TPlayerBotYoharaShopNeed();
		n.dwAt = now ? now : 1;
		n.lMap = map;
		int share[PLAYERBOT_YOHARA_ELEMENTS];
		GetPlayerBotYoharaMapShares(map, share);
		int resistShort = 0, powerShort = 0;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
		{
			if (share[e] < PLAYERBOT_YOHARA_ELEMENT_DEFENCE_PERCENT)
				continue;
			n.abResist[e] = true;
			const int resist = (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_RESIST_ELIXIRS[e]);
			resistShort += std::max(0, PLAYERBOT_YSHOP_TARGET - resist);
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_ELEMENTS_V1)
			n.abPower[e] = true;
			const int power = (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_POWER_ELIXIRS[e]);
			powerShort += std::max(0, PLAYERBOT_YSHOP_TARGET - power);
			if (power < PLAYERBOT_YSHOP_LOW)
				n.bLow = true;
#endif
			if (resist < PLAYERBOT_YSHOP_LOW)
				n.bLow = true;
		}
		n.iMaterials = std::min(PLAYERBOT_YSHOP_INPUT_MAX, resistShort * PLAYERBOT_YSHOP_RATE);
		n.iDust = std::min(PLAYERBOT_YSHOP_INPUT_MAX, powerShort * PLAYERBOT_YSHOP_RATE);
		return &n;
	}

	void ForgetPlayerBotYoharaShopNeed(LPCHARACTER ch)
	{
		if (ch)
			s_mapPlayerBotYoharaShopNeed.erase(ch->GetPlayerID());
	}

	int GetPlayerBotYoharaShopMaterialsWanted(LPCHARACTER ch)
	{
		const TPlayerBotYoharaShopNeed* n = GetPlayerBotYoharaShopNeed(ch);
		return n ? n->iMaterials : 0;
	}

	// The dust over the G0 reserve kept off the counters, the marbles and the bonus stones.
	int GetPlayerBotYoharaShopDustKeep(LPCHARACTER ch)
	{
		const TPlayerBotYoharaShopNeed* n = GetPlayerBotYoharaShopNeed(ch);
		return n ? n->iDust : 0;
	}

	bool IsPlayerBotYoharaElixirVnum(DWORD vnum)
	{
		return vnum >= 50830 && vnum <= 50841;
	}

	// ------------------------------------------------------------ the market

	bool WantsPlayerBotYoharaShopDustOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer || offer->GetVnum() != PLAYERBOT_MAGIC_DUST_VNUM || IsPlayerBotG0DustHunter(ch))
			return false;
		const int want = GetPlayerBotYoharaShopDustKeep(ch);
		const int have = GetPlayerBotYoharaShopDustFree(ch);
		return want > 0 && have < want && (int)offer->GetCount() <= want - have + PLAYERBOT_YSHOP_LINE_SLACK;
	}

	bool CanPlayerBotPayForYoharaShopDust(LPCHARACTER ch, LPITEM item, long long price)
	{
		if (!ch || !item || price <= 0)
			return false;
		const long long units = std::max<long long>(1, (long long)item->GetCount());
		const long long cap = (long long)ScalePlayerBotIwakuraPrice(PLAYERBOT_PRIOR_MAGIC_DUST) * PLAYERBOT_YSHOP_DUST_PRICE_CAP_PCT / 100;
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		return price <= cap * units && price <= spare * PLAYERBOT_YSHOP_DUST_PURSE_PCT / 100;
	}

	bool PlayerBotYoharaShopWantsDustFromMarket(LPCHARACTER ch)
	{
		if (IsPlayerBotG0DustHunter(ch) || GetPlayerBotYoharaShopDustFree(ch) >= GetPlayerBotYoharaShopDustKeep(ch))
			return false;
		const TPlayerBotMarketLedgerEntry* dust = GetPlayerBotMarketLedgerEntry(PLAYERBOT_MAGIC_DUST_VNUM);
		return dust && dust->dwSupplyUnits > 0;
	}

	// A trade trip's "buy": a kind is low, and the market holds the input that is short.
	bool PlayerBotYoharaShopWantsMarket(LPCHARACTER ch)
	{
		const TPlayerBotYoharaShopNeed* n = GetPlayerBotYoharaShopNeed(ch);
		if (!n || !n->bLow)
			return false;
		if (PlayerBotYoharaShopWantsDustFromMarket(ch))
			return true;
		if ((int)ch->CountSpecifyItem(PLAYERBOT_YSHOP_MATERIAL_VNUM) < n->iMaterials)
		{
			const TPlayerBotMarketLedgerEntry* mats = GetPlayerBotMarketLedgerEntry(PLAYERBOT_YSHOP_MATERIAL_VNUM);
			return mats && mats->dwSupplyUnits > 0;
		}
		return false;
	}

	void NotePlayerBotYoharaShopBought(LPCHARACTER ch, DWORD vnum, long long price, DWORD count)
	{
		if (!ch || (vnum != PLAYERBOT_MAGIC_DUST_VNUM && vnum != PLAYERBOT_YSHOP_MATERIAL_VNUM) || !IsPlayerBotYoharaShopUser(ch))
			return;
		const TPlayerBotYoharaShopNeed* n = GetPlayerBotYoharaShopNeed(ch);
		if (!n || (vnum == PLAYERBOT_MAGIC_DUST_VNUM ? n->iDust : n->iMaterials) <= 0)
			return;
		if (vnum == PLAYERBOT_MAGIC_DUST_VNUM)
			s_kPlayerBotYoharaShopStats.dustBought += count;
		else
			s_kPlayerBotYoharaShopStats.materialsBought += count;
		sys_log(0, "PLAYERBOT_SHOP2: %s bought pid=%u name=%s count=%u price=%lld have=%d want=%d",
				vnum == PLAYERBOT_MAGIC_DUST_VNUM ? "dust" : "material", ch->GetPlayerID(), ch->GetName(), (unsigned int)count, price,
				vnum == PLAYERBOT_MAGIC_DUST_VNUM ? GetPlayerBotYoharaShopDustFree(ch) : (int)ch->CountSpecifyItem(vnum),
				vnum == PLAYERBOT_MAGIC_DUST_VNUM ? n->iDust : n->iMaterials);
	}

	// ------------------------------------------------------------ the exchange at Handlarka Roznosci

	// The materials the exchange may take: the bag's, less what the horse and the saddlebag rows still keep.
	int GetPlayerBotYoharaShopMaterialsFree(LPCHARACTER ch)
	{
		const int held = (int)ch->CountSpecifyItem(PLAYERBOT_YSHOP_MATERIAL_VNUM);
		const int others = std::max(0, GetPlayerBotCraftMaterialsWanted(ch, false) - GetPlayerBotYoharaShopMaterialsWanted(ch));
		return std::max(0, held - others);
	}

	// One kind filled towards the target from one input; the elixirs made.
	int ExchangePlayerBotYoharaShopKind(LPCHARACTER ch, long map, int e, bool power, DWORD npc)
	{
		const DWORD elixir = power ? PLAYERBOT_YOHARA_POWER_ELIXIRS[e] : PLAYERBOT_YOHARA_RESIST_ELIXIRS[e];
		const DWORD input = power ? PLAYERBOT_MAGIC_DUST_VNUM : PLAYERBOT_YSHOP_MATERIAL_VNUM;
		int made = 0;
		while ((int)ch->CountSpecifyItem(elixir) < PLAYERBOT_YSHOP_TARGET &&
				(power ? GetPlayerBotYoharaShopDustFree(ch) : GetPlayerBotYoharaShopMaterialsFree(ch)) >= PLAYERBOT_YSHOP_RATE &&
				CountPlayerBotFreeInventoryCells(ch) > PLAYERBOT_YSHOP_FREE_CELLS)
		{
			ch->RemoveSpecifyItem(input, PLAYERBOT_YSHOP_RATE);
			LPITEM item = ch->AutoGiveItem(elixir, 1, -1, false);
			if (!item)
			{
				ch->AutoGiveItem(input, PLAYERBOT_YSHOP_RATE, -1, false);	// no room after all: the input back
				break;
			}
			LogManager::instance().ItemLog(ch, item, "PLAYERBOT_SHOP2", power ? "dust" : "materials");
			++made;
			if (power)
			{
				++s_kPlayerBotYoharaShopStats.powerMade;
				s_kPlayerBotYoharaShopStats.dustPaid += PLAYERBOT_YSHOP_RATE;
			}
			else
			{
				++s_kPlayerBotYoharaShopStats.resistMade;
				s_kPlayerBotYoharaShopStats.materialsPaid += PLAYERBOT_YSHOP_RATE;
			}
			sys_log(0, "PLAYERBOT_SHOP2: exchange pid=%u name=%s npc=%u map=%ld for_map=%ld kind=%s element=%s paid=%d paid_vnum=%u got=%u value=%ld seconds=%ld have=%d input_left=%d",
					ch->GetPlayerID(), ch->GetName(), npc, ch->GetMapIndex(), map, power ? "power" : "resist",
					PLAYERBOT_YOHARA_ELEMENT_NAMES[e], PLAYERBOT_YSHOP_RATE, input, elixir, (long)item->GetSocket(1),
					(long)item->GetSocket(2), (int)ch->CountSpecifyItem(elixir), (int)ch->CountSpecifyItem(input));
		}
		return made;
	}

	// At Dongan's Handlarka Roznosci (Dongan's errand, playerbot_yohara_sungma.h): every needed kind filled towards the
	// target - the map's top element first, resistance before power. The elixirs made.
	int RunPlayerBotYoharaShopExchange(LPCHARACTER ch, DWORD npc)
	{
		if (npc != PLAYERBOT_YSHOP_NPC || !ch || ch->IsDead() || ch->GetExchange() || ch->GetMyShop() ||
				GetPlayerBotYoharaElementSlot(ch->GetMapIndex()) != GetPlayerBotYoharaElementSlot(PLAYERBOT_MAP_SUNGMA_DONGAN))
			return 0;
		const TPlayerBotYoharaShopNeed* n = GetPlayerBotYoharaShopNeed(ch);
		if (!n)
			return 0;
		const long map = n->lMap;
		int share[PLAYERBOT_YOHARA_ELEMENTS];
		GetPlayerBotYoharaMapShares(map, share);
		int order[PLAYERBOT_YOHARA_ELEMENTS];
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			order[e] = e;
		for (int i = 1; i < PLAYERBOT_YOHARA_ELEMENTS; ++i)
			for (int j = i; j > 0 && share[order[j]] > share[order[j - 1]]; --j)
				std::swap(order[j], order[j - 1]);
		bool resist[PLAYERBOT_YOHARA_ELEMENTS], power[PLAYERBOT_YOHARA_ELEMENTS];
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
		{
			resist[e] = n->abResist[e];
			power[e] = n->abPower[e];
		}
		int made = 0;
		for (int i = 0; i < PLAYERBOT_YOHARA_ELEMENTS; ++i)
			if (resist[order[i]])
				made += ExchangePlayerBotYoharaShopKind(ch, map, order[i], false, npc);
		for (int i = 0; i < PLAYERBOT_YOHARA_ELEMENTS; ++i)
			if (power[order[i]])
				made += ExchangePlayerBotYoharaShopKind(ch, map, order[i], true, npc);
		ForgetPlayerBotYoharaShopNeed(ch);
		if (made > 0)
			sys_log(0, "PLAYERBOT_SHOP2: exchange done pid=%u name=%s for_map=%ld made=%d materials=%d dust=%d dust_reserve=%d",
					ch->GetPlayerID(), ch->GetName(), map, made, (int)ch->CountSpecifyItem(PLAYERBOT_YSHOP_MATERIAL_VNUM),
					(int)ch->CountSpecifyItem(PLAYERBOT_MAGIC_DUST_VNUM), GetPlayerBotG0DustReserve(ch));
		return made;
	}

	// Dongan's errand for the exchange (GetPlayerBotSungmaErrandNeed): on its Sung Ma map, a needed kind under the low
	// mark with the input for one of it, room in the bag, not more often than PLAYERBOT_YSHOP_ERRAND_GAP_MS.
	bool PlayerBotYoharaShopWantsErrand(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch || GetPlayerBotYoharaElementSlot(ch->GetMapIndex()) < 0)
			return false;
		const TPlayerBotYoharaShopNeed* n = GetPlayerBotYoharaShopNeed(ch);
		if (!n || !n->bLow || CountPlayerBotFreeInventoryCells(ch) <= PLAYERBOT_YSHOP_FREE_CELLS)
			return false;
		TPlayerBotYoharaShopBot& b = s_mapPlayerBotYoharaShopBot[ch->GetPlayerID()];
		if (b.dwLastErrand != 0 && dwNow - b.dwLastErrand < PLAYERBOT_YSHOP_ERRAND_GAP_MS)
			return false;
		const bool materials = GetPlayerBotYoharaShopMaterialsFree(ch) >= PLAYERBOT_YSHOP_RATE;
		const bool dust = GetPlayerBotYoharaShopDustFree(ch) >= PLAYERBOT_YSHOP_RATE;
		const char* kind = NULL;
		const char* element = NULL;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS && !kind; ++e)
		{
			if (materials && n->abResist[e] && (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_RESIST_ELIXIRS[e]) < PLAYERBOT_YSHOP_LOW)
				kind = "resist", element = PLAYERBOT_YOHARA_ELEMENT_NAMES[e];
			else if (dust && n->abPower[e] && (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_POWER_ELIXIRS[e]) < PLAYERBOT_YSHOP_LOW)
				kind = "power", element = PLAYERBOT_YOHARA_ELEMENT_NAMES[e];
		}
		if (!kind)
			return false;
		b.dwLastErrand = dwNow ? dwNow : 1;
		++s_kPlayerBotYoharaShopStats.errands;
		sys_log(0, "PLAYERBOT_SHOP2: errand wanted pid=%u name=%s map=%ld for_map=%ld kind=%s element=%s materials=%d dust_free=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), n->lMap, kind, element,
				(int)ch->CountSpecifyItem(PLAYERBOT_YSHOP_MATERIAL_VNUM), GetPlayerBotYoharaShopDustFree(ch));
		return true;
	}

	// ------------------------------------------------------------ the world set (item 24)

	bool IsPlayerBotYoharaJadeVnum(DWORD vnum)
	{
		return (vnum >= 14580 && vnum <= 14619) || (vnum >= 16580 && vnum <= 16619) || (vnum >= 17570 && vnum <= 17609);
	}

	// Whether the bot dresses for the Sung Ma maps (its Will counts): standing on one of them - or asked so.
	bool IsPlayerBotDressedForSungma(LPCHARACTER ch)
	{
		if (s_iPlayerBotYoharaDressForce != 0)
			return s_iPlayerBotYoharaDressForce == 1;
		return ch && GetPlayerBotYoharaElementSlot(ch->GetMapIndex()) >= 0;
	}

	long long ScorePlayerBotYoharaDress(LPCHARACTER ch, LPITEM item, int dress)
	{
		const int was = s_iPlayerBotYoharaDressForce;
		s_iPlayerBotYoharaDressForce = dress;
		const long long score = GetPlayerBotEquipmentScore(item, ch);
		s_iPlayerBotYoharaDressForce = was;
		return score;
	}

	// The best piece of a jewellery slot the bot owns (worn or in the bag) for a dress (1 Sung Ma, 2 the world, 0 where
	// it stands); family 0 any, 1 jade only, 2 no jade.
	LPITEM FindPlayerBotYoharaJewel(LPCHARACTER ch, BYTE wear, int dress, int family, long long* scoreOut)
	{
		LPITEM best = NULL;
		long long bestScore = 0;
		LPITEM worn = ch->GetWear(wear);
		for (int cell = -1; cell < (int)PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = cell < 0 ? worn : ch->GetInventoryItem((WORD)cell);
			if (!item || (cell >= 0 && (item->GetCell() != cell || item->IsEquipped())))
				continue;
			const bool jade = IsPlayerBotYoharaJadeVnum(item->GetVnum());
			if ((family == 1 && !jade) || (family == 2 && jade))
				continue;
			if (cell >= 0 && (item->GetType() != ITEM_ARMOR || !IsPlayerBotEquipmentCandidate(ch, item) ||
					item->GetLevelLimit() > ch->GetLevel() || item->FindEquipCell(ch) != wear))
				continue;
			const long long score = ScorePlayerBotYoharaDress(ch, item, dress);
			// the worn piece wins a tie
			if (!best || score > bestScore || (score == bestScore && item == worn))
			{
				best = item;
				bestScore = score;
			}
		}
		if (scoreOut)
			*scoreOut = bestScore;
		return best;
	}

	bool OwnsPlayerBotYoharaJade(LPCHARACTER ch, BYTE wear)
	{
		return FindPlayerBotYoharaJewel(ch, wear, 1, 1, NULL) != NULL;
	}

	TPlayerBotYoharaShopBot& GetPlayerBotYoharaShopBot(LPCHARACTER ch)
	{
		return s_mapPlayerBotYoharaShopBot[ch->GetPlayerID()];
	}

	// The kept pieces of a Champion with jade: per jewellery slot with a jade piece, its best jade (Sung Ma's score) and
	// its best other piece (the world's score). Refreshed every half minute.
	const std::set<DWORD>& GetPlayerBotYoharaKeptJewels(LPCHARACTER ch)
	{
		TPlayerBotYoharaShopBot& b = GetPlayerBotYoharaShopBot(ch);
		const DWORD now = get_dword_time();
		if (b.dwKeptAt != 0 && now - b.dwKeptAt < PLAYERBOT_YSHOP_NEED_MS)
			return b.setKept;
		b.dwKeptAt = now ? now : 1;
		b.setKept.clear();
		if (!IsPlayerBotYoharaShopUser(ch))
			return b.setKept;
		for (int i = 0; i < 3; ++i)
		{
			LPITEM jade = FindPlayerBotYoharaJewel(ch, PLAYERBOT_YSHOP_JEWEL_WEARS[i], 1, 1, NULL);
			if (!jade)
				continue;
			b.setKept.insert(jade->GetID());
			LPITEM world = FindPlayerBotYoharaJewel(ch, PLAYERBOT_YSHOP_JEWEL_WEARS[i], 2, 2, NULL);
			if (world)
				b.setKept.insert(world->GetID());
		}
		return b.setKept;
	}

	// Kept off the merchant, the counters and the other bots: the world set and its jade (above), the elixirs of Yohara
	// up to PLAYERBOT_YSHOP_KEEP_MAX of a vnum, the materials the exchange wants (the dust has the counters' dust keep).
	bool IsPlayerBotYoharaShopKept(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !IsPlayerBotYoharaShopUser(ch))
			return false;
		const DWORD vnum = item->GetVnum();
		if (IsPlayerBotYoharaElixirVnum(vnum))
			return CountPlayerBotVnumUnitsAhead(ch, item) < PLAYERBOT_YSHOP_KEEP_MAX;
		if (vnum == PLAYERBOT_YSHOP_MATERIAL_VNUM)
		{
			const int keep = GetPlayerBotYoharaShopMaterialsWanted(ch);
			return keep > 0 && CountPlayerBotVnumUnitsAhead(ch, item) < keep;
		}
		if (item->GetType() != ITEM_ARMOR || (item->GetSubType() != ARMOR_WRIST && item->GetSubType() != ARMOR_NECK &&
				item->GetSubType() != ARMOR_EAR))
			return false;
		return GetPlayerBotYoharaKeptJewels(ch).count(item->GetID()) != 0;
	}

	// The G0 sale (IsPlayerBotG0PieceReplaced): a kept jade piece is not replaced, whatever the dress.
	bool IsPlayerBotYoharaWorldSetKeptJade(LPCHARACTER ch, LPITEM item)
	{
		return ch && item && IsPlayerBotYoharaJadeVnum(item->GetVnum()) && IsPlayerBotYoharaShopKept(ch, item);
	}

	// GetPlayerBotSungmaWill: while dressed for the world, the Will the jade in the bag would bring back on a Sung Ma
	// map (its lines over the worn piece's, per jewellery slot), with the Will's per cent bonus.
	int GetPlayerBotYoharaWorldSetWillDelta(LPCHARACTER ch, int what)
	{
		if (what < 0 || what > 3 || !ch || IsPlayerBotDressedForSungma(ch) || !IsPlayerBotYoharaShopUser(ch))
			return 0;
		TPlayerBotYoharaShopBot& b = GetPlayerBotYoharaShopBot(ch);
		const DWORD now = get_dword_time();
		if (b.dwWillAt == 0 || now - b.dwWillAt >= PLAYERBOT_YSHOP_TICK_MS)
		{
			b.dwWillAt = now ? now : 1;
			static const BYTE s_aPoint[4] = { POINT_SUNGMA_STR, POINT_SUNGMA_HP, POINT_SUNGMA_MOVE, POINT_SUNGMA_IMMUNE };
			for (int k = 0; k < 4; ++k)
				b.aiWillDelta[k] = 0;
			for (int i = 0; i < 3; ++i)
			{
				const BYTE wear = PLAYERBOT_YSHOP_JEWEL_WEARS[i];
				LPITEM worn = ch->GetWear(wear);
				LPITEM best = FindPlayerBotYoharaJewel(ch, wear, 1, 0, NULL);
				if (!best || best == worn)
					continue;
				for (int k = 0; k < 4; ++k)
					b.aiWillDelta[k] += (int)SumPlayerBotItemLines(best, s_aPoint[k]) - (worn ? (int)SumPlayerBotItemLines(worn, s_aPoint[k]) : 0);
			}
			for (int k = 0; k < 4; ++k)
			{
				const int pct = std::max(-100, (int)ch->GetPoint(POINT_SUNGMA_PER_STR + k));
				b.aiWillDelta[k] = b.aiWillDelta[k] * (100 + pct) / 100;
			}
		}
		return b.aiWillDelta[what];
	}

	// The swap: each jewellery slot to its best piece for where the bot stands (the equipment pass's score), at once.
	int WearPlayerBotYoharaDress(LPCHARACTER ch, bool sungma)
	{
		int swapped = 0;
		for (int i = 0; i < 3; ++i)
		{
			const BYTE wear = PLAYERBOT_YSHOP_JEWEL_WEARS[i];
			LPITEM worn = ch->GetWear(wear);
			long long bestScore = 0;
			LPITEM best = FindPlayerBotYoharaJewel(ch, wear, 0, 0, &bestScore);
			if (!best || best == worn)
				continue;
			if (worn && (IsPlayerBotSidekickLockedItem(ch, worn) || ch->GetEmptyInventory(worn->GetSize()) < 0 ||
					!ch->UnequipItem(worn) || worn->IsEquipped()))
				continue;
			if (!ch->EquipItem(best))
			{
				if (worn && !worn->IsEquipped())
					ch->EquipItem(worn);
				continue;
			}
			++swapped;
			++s_kPlayerBotYoharaShopStats.swaps;
			sys_log(0, "PLAYERBOT_SHOP2: worldset swap pid=%u name=%s map=%ld dress=%s wear=%d vnum=%u old=%u",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), sungma ? "sungma" : "world", (int)wear, best->GetVnum(),
					worn ? worn->GetVnum() : 0);
		}
		return swapped;
	}

	void LogPlayerBotYoharaShopCensus()
	{
		const TPlayerBotYoharaShopStats& s = s_kPlayerBotYoharaShopStats;
		sys_log(0, "PLAYERBOT_SHOP2: census resist_made=%u power_made=%u materials_paid=%u dust_paid=%u errands=%u dust_bought=%u materials_bought=%u worldset_swaps=%u bots=%u",
				s.resistMade, s.powerMade, s.materialsPaid, s.dustPaid, s.errands, s.dustBought, s.materialsBought, s.swaps,
				(unsigned int)s_mapPlayerBotYoharaShopBot.size());
	}

	// The AI's tick (playerbot_manager.cpp, beside the G0 look; never owns the tick): the world set's dress on the bot's
	// own clock, out of a fight. A dress changed asks the equipment pass too.
	void ManagePlayerBotYoharaShop(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (s_kPlayerBotYoharaShopStats.dwCensusAt == 0 || (int)(dwNow - s_kPlayerBotYoharaShopStats.dwCensusAt) >= 0)
		{
			if (s_kPlayerBotYoharaShopStats.dwCensusAt != 0)
				LogPlayerBotYoharaShopCensus();
			s_kPlayerBotYoharaShopStats.dwCensusAt = dwNow + PLAYERBOT_YSHOP_CENSUS_MS;
		}
		if (!IsPlayerBotYoharaShopUser(ch) || ch->IsDead())
			return;
		TPlayerBotYoharaShopBot& b = GetPlayerBotYoharaShopBot(ch);
		if (b.dwNextTick != 0 && (int)(dwNow - b.dwNextTick) < 0)
			return;
		b.dwNextTick = dwNow + PLAYERBOT_YSHOP_TICK_MS;
		if (state.dwTargetVID != 0 || ch->GetVictim() || ch->GetExchange() || ch->GetMyShop() || IsPlayerBotGearFrozen(ch))
			return;
		const bool sungma = IsPlayerBotDressedForSungma(ch);
		const int dress = sungma ? 1 : 0;
		const bool changed = b.iDressed != dress;
		if (!changed && (int)(dwNow - b.dwNextDressLook) < 0)
			return;
		b.dwNextDressLook = dwNow + PLAYERBOT_YSHOP_DRESS_LOOK_MS;
		if (changed)
		{
			b.iDressed = dress;
			b.dwKeptAt = 0;
			b.dwWillAt = 0;
		}
		bool jade = false;
		for (int i = 0; i < 3 && !jade; ++i)
			jade = OwnsPlayerBotYoharaJade(ch, PLAYERBOT_YSHOP_JEWEL_WEARS[i]);
		if (jade && WearPlayerBotYoharaDress(ch, sungma) > 0)
		{
			b.dwWillAt = 0;
			state.bEquipPending = true;
			state.dwNextEquipmentCheckTime = 0;
		}
	}
}

#endif
