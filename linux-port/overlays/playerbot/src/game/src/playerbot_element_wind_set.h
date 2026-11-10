#ifndef __INC_METIN2_PLAYERBOT_ELEMENT_WIND_SET_H__
#define __INC_METIN2_PLAYERBOT_ELEMENT_WIND_SET_H__

// MT2009_PLUS_BOT_WIND_SET_V1 - a 90+ bot's second, wind set (the owner, 10 November 2026, rejecting the WIND_BUILD_V1
// reroll of the lightning pieces: "EQ na blyskawice niech zostawia, ono ma duza wartosc, wiec albo moze je sprzedac na
// rynku, albo zostawic sobie na przyklad na pozniej. Na wiatr niech zrobi nowe EQ, nowe kostiumy, nowa fryzure, nowa
// bizuterie itd."; the standing rule of 28 October: another element = a second EQ set and a second costume set).
//
// Who: a bot of PLAYERBOT_WS levels (the wind window's first level, GetPlayerBotElementProgressWindFrom - 90 - up to 119),
// no Yohara hunt element, not a Yohara bonus member, not a companion. The record starts when the worn set holds less
// wind (without the wind pet) than Zaklety Las's gate - a bot whose worn set is a wind set already needs none.
//
// The set: the armour, helmet and bracelet (item_attr of this world: fire / lightning / wind 2-15 roll on body, wrist,
// head, costume body, costume hair and the pendant only - no necklace, earrings, boots or shield line; the element
// necklaces / boots, Srebrny Naszyjnik 16040 / Buty Wyszywane Zlotem 15060, are level-20-50 pieces a 90+ bot does not
// wear), the costume and the hairstyle. The talisman is per element by itself (playerbot_talismans.h picks the one of the
// hunting map's element): the set buys the Talizman Wiatru +0 at the Blacksmith's daily deal (500 000, the same
// once-a-day flag as MT2009_PLUS_BOT_TALISMAN_DAILY_V1) when the bot owns none, and the workshop keeps the best lightning
// and the best wind talisman (IsPlayerBotWindSetTalismanKept); the daily step goods raise the wind one on Zaklety Las.
// A piece carrying any lightning line is never the set's - the lightning EQ is not rerolled.
//
// How the pieces come (one a slot, the best by its wind line, then the equipment score; at least
// PLAYERBOT_WS_MIN_SCORE_PCT of the lightning piece's score):
//   * the bot's own bag - a drop, a spare, an older piece, a costume with a week of time;
//   * the market - the second set's craft hooks (playerbot_workshop.h through playerbot_element_second_set.h): the
//     lightning piece's family from PLAYERBOT_WS_MARKET_PLUS_BELOW pluses under it to +9, out of a quarter of the spare
//     purse (the fair-price stands);
//   * the ItemShop V3 - a costume / hairstyle look for an empty costume slot (the bots buy anything in V3);
//   * the anvil - the armour, helmet and bracelet climb to the plus of the lightning piece of their slot
//     (GetPlayerBotWindSetRefineTarget in the refine pass's bag candidates; the scroll rules are the pass's own).
// The bonusing, in the bag (nothing worn comes off): the armour, helmet and bracelet to the wind line at its level-4
// value (10) - the armour and bracelet with a Max HP line too, up to PLAYERBOT_WS_HP_CHANGES changes - with the V3 add
// and change stones of the element shop (bought as they run out, the bag's own first), the set's SM capped at the wind
// budget (m2_bot_wind_shop_budget, 15 000); PLAYERBOT_WS_GIVE_UP changes a piece at most. The costume and hairstyle to
// wind 10 with the Handlarka's 70063 / 70064 (the costume pass buys them for it), PLAYERBOT_WS_COSTUME_CHANGES at most.
//
// The swap (PlayerBotEquipItem in place, out of a fight, every PLAYERBOT_WS_SWAP_LOOK_MS): on Zaklety Las the wind set
// goes on when it holds more wind than the worn set; on a lightning map (the Grotto V1 / V2, Kraina Gigantow, Arezzo's
// cyclops) the lightning set goes back on; in a village the set of the map the travel pass wants (Zaklety Las only when
// the wind set holds its gate). The map gates (PassPlayerBotElementMapGate, CanPlayerBotTakeElementProgressEarly) count
// the stored set as worn (GetPlayerBotWindSetElementResist), so the bot goes to Zaklety Las with its wind set in the bag
// and back to the Grotto (a failed trial) with its lightning set in the bag. The waiting set is kept off every sale,
// gift, junk rule and the equipment pass (IsPlayerBotSecondSetStored / IsPlayerBotSecondSetWornLocked answer it), and the
// element shop and the reroll passes never touch the worn lightning set for wind (IsPlayerBotWindSetGuardedPiece).
//
// The lightning set's sale: kept while the bot may be sent back to the lightning maps; released to the bag's ordinary
// life - the spare-gear rules put it on the counter at the fair price - once the bot is PLAYERBOT_WS_SELL_LEVEL+ and has
// worn the wind set PLAYERBOT_WS_SELL_DAYS days without a swap back (the trial never sent it back), or once it leaves the
// band (120 / a Yohara bonus member: the set not worn then is released). The record is closed then (mt2009_ws.on 2).
//
// Switches (event flags): m2_bot_wind_set_off 1 - the set off (its pieces' keep with it); m2_bot_wind_set_sell_level N
// (95-125, default 105); m2_bot_wind_set_sell_days N (1-30, default 3); m2_bot_wind_shop_budget N (the SM cap).
// The log: PLAYERBOT_WINDSET: started / piece / bought / bonus / piece_ready / costume / complete / swap_in / swap_out /
// refined / talisman / blocked / sold / retired, and the census every PLAYERBOT_WS_CENSUS_MS - per band (90-94, 95-99,
// 100-104, 105-119): bots, records, pieces acquired / bonused / worn, set usable, set worn, lightning set kept / sold,
// wind talisman; the period's work.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_element_shop.h, in the anonymous namespace.

#ifdef MT2009_PLUS_BOT_WIND_SET_V1
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_ELEMENTS_V1) && defined(MT2009_PLUS_BOT_ISHOP_V3_V1)
namespace
{
	enum { PLAYERBOT_WS_BODY = 0, PLAYERBOT_WS_HEAD, PLAYERBOT_WS_WRIST, PLAYERBOT_WS_COSTUME, PLAYERBOT_WS_HAIR, PLAYERBOT_WS_SLOTS };
	const int PLAYERBOT_WS_GEAR = PLAYERBOT_WS_COSTUME;	// the slots under it are the gear
	const BYTE PLAYERBOT_WS_WEARS[PLAYERBOT_WS_SLOTS] = { WEAR_BODY, WEAR_HEAD, WEAR_WRIST, WEAR_COSTUME_BODY, WEAR_COSTUME_HAIR };
	const char* const PLAYERBOT_WS_NAMES[PLAYERBOT_WS_SLOTS] = { "body", "head", "wrist", "costume", "hair" };

	const DWORD PLAYERBOT_WS_LOOK_MS = 60 * 1000;
	const DWORD PLAYERBOT_WS_SWAP_LOOK_MS = 5 * 1000;
	const DWORD PLAYERBOT_WS_BONUS_MS = 20 * 1000;
	const DWORD PLAYERBOT_WS_COSTUME_MS = 20 * 1000;
	const DWORD PLAYERBOT_WS_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_WS_FORGET_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_WS_BLOCKED_LOG_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_WS_LOOK_PENDING_MS = 10 * 60 * 1000;
	const int PLAYERBOT_WS_MAX_LEVEL = 119;
	const int PLAYERBOT_WS_MIN_SCORE_PCT = 40;
	const int PLAYERBOT_WS_MARKET_PLUS_BELOW = 3;
	const int PLAYERBOT_WS_MARKET_PURSE_PCT = 25;
	const int PLAYERBOT_WS_STONES_PER_PASS = 20;
	const int PLAYERBOT_WS_GIVE_UP = 120;
	const int PLAYERBOT_WS_HP_CHANGES = 40;
	const int PLAYERBOT_WS_COSTUME_CHANGES = 40;
	const int PLAYERBOT_WS_COSTUME_RESETS = 8;
	const int PLAYERBOT_WS_SELL_LEVEL = 105;
	const int PLAYERBOT_WS_SELL_DAYS = 3;

	const char* const PLAYERBOT_WS_FLAG_ON = "mt2009_ws.on";		// 1 the set's record, 2 closed (the lightning set sold)
	const char* const PLAYERBOT_WS_FLAG_WORN = "mt2009_ws.worn";
	const char* const PLAYERBOT_WS_FLAG_SINCE = "mt2009_ws.since";	// the wind set on since (unix time)
	const char* const PLAYERBOT_WS_FLAG_SM = "mt2009_ws.sm";		// the set's SM spent

	struct TPlayerBotWindSet
	{
		int iOn;		// 0 none, 1 the record, 2 closed
		bool bWorn;
		DWORD adwW[PLAYERBOT_WS_SLOTS];	// the wind set
		DWORD adwL[PLAYERBOT_WS_SLOTS];	// while the wind set is on: the lightning set in the bag
		bool abReady[PLAYERBOT_WS_SLOTS];
		bool bComplete, bSwapDue;
		int iSince;
		long long llSm;
		DWORD dwNextLook, dwNextSwapLook, dwNextBonus, dwNextCostume, dwSeen, dwBlockedAt;
		DWORD dwBoughtVnum, dwLookVnum, dwLookAt;
		std::string strBlocked;
		std::map<DWORD, int> mapChanges;	// changes by item id (this core's memory)
		TPlayerBotWindSet() : iOn(0), bWorn(false), bComplete(false), bSwapDue(false), iSince(0), llSm(0), dwNextLook(0),
			dwNextSwapLook(0), dwNextBonus(0), dwNextCostume(0), dwSeen(0), dwBlockedAt(0), dwBoughtVnum(0), dwLookVnum(0), dwLookAt(0)
		{
			for (int i = 0; i < PLAYERBOT_WS_SLOTS; ++i)
			{
				adwW[i] = adwL[i] = 0;
				abReady[i] = false;
			}
		}
	};
	std::map<DWORD, TPlayerBotWindSet> s_mapPlayerBotWindSet;

	struct TPlayerBotWindSetStats
	{
		unsigned int started, piecesOwn, piecesMarket, piecesLook, ready, complete, swapIn, swapOut, adds, changes, costumeRolls,
			talismans, refined, burned, sold, released, blocked, firstSetWind, bought;
		long long sm;
		DWORD dwCensusAt;
		TPlayerBotWindSetStats() : started(0), piecesOwn(0), piecesMarket(0), piecesLook(0), ready(0), complete(0), swapIn(0),
			swapOut(0), adds(0), changes(0), costumeRolls(0), talismans(0), refined(0), burned(0), sold(0), released(0), blocked(0),
			firstSetWind(0), bought(0), sm(0), dwCensusAt(0) {}
	};
	TPlayerBotWindSetStats s_kPlayerBotWindSetStats;

	// ------------------------------------------------------------ the switches

	bool IsPlayerBotWindSetOn()
	{
		static DWORD s_dwAt = 0;
		static bool s_bOn = true;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 5000)
		{
			s_dwAt = now ? now : 1;
			s_bOn = quest::CQuestManager::instance().GetEventFlag("m2_bot_wind_set_off") == 0;
		}
		return s_bOn;
	}

	int GetPlayerBotWindSetFromLevel()
	{
		const int from = GetPlayerBotElementProgressWindFrom();
		return from > 0 ? from : PLAYERBOT_EPROG_WIND_FROM;
	}

	int GetPlayerBotWindSetSellLevel()
	{
		const int flag = quest::CQuestManager::instance().GetEventFlag("m2_bot_wind_set_sell_level");
		return flag >= 95 && flag <= 125 ? flag : PLAYERBOT_WS_SELL_LEVEL;
	}

	int GetPlayerBotWindSetSellDays()
	{
		const int flag = quest::CQuestManager::instance().GetEventFlag("m2_bot_wind_set_sell_days");
		return flag >= 1 && flag <= 30 ? flag : PLAYERBOT_WS_SELL_DAYS;
	}

	int GetPlayerBotWindSetGate()
	{
		const int gate = GetPlayerBotElementProgressGateForMap(PLAYERBOT_MAP_ZAKLETY);
		return gate > 0 ? gate : GetPlayerBotElementProgressGate();
	}

	// The band's bot (the set may start or stay open).
	bool IsPlayerBotWindSetBandBot(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && ch->GetDesc()->IsBot() && ch->IsItemLoaded() &&
				(int)ch->GetLevel() >= GetPlayerBotWindSetFromLevel() && (int)ch->GetLevel() <= PLAYERBOT_WS_MAX_LEVEL &&
				!IsPlayerBotSidekickPID(ch->GetPlayerID()) && GetPlayerBotHuntElement(ch) == 0 && !IsPlayerBotYoharaBonusMember(ch) &&
				IsPlayerBotElementProgressOn(PLAYERBOT_EPROG_ALL);
	}

	// ------------------------------------------------------------ the record

	std::string GetPlayerBotWindSetFlag(char kind, int slot)
	{
		char name[32];
		snprintf(name, sizeof(name), "mt2009_ws.%c%d", kind, slot);
		return name;
	}

	LPITEM FindPlayerBotWindSetItem(LPCHARACTER ch, DWORD id)
	{
		if (!ch || id == 0)
			return NULL;
		LPITEM item = ITEM_MANAGER::instance().Find(id);
		return item && item->GetOwner() == ch ? item : NULL;
	}

	void SetPlayerBotWindSetPiece(LPCHARACTER ch, TPlayerBotWindSet& s, int slot, DWORD id)
	{
		s.adwW[slot] = id;
		s.abReady[slot] = false;
		s.bComplete = false;
		ch->SetQuestFlag(GetPlayerBotWindSetFlag('w', slot), (int)id);
	}

	void SetPlayerBotWindSetStoredL(LPCHARACTER ch, TPlayerBotWindSet& s, int slot, DWORD id)
	{
		s.adwL[slot] = id;
		ch->SetQuestFlag(GetPlayerBotWindSetFlag('l', slot), (int)id);
	}

	void LoadPlayerBotWindSet(LPCHARACTER ch, TPlayerBotWindSet& s)
	{
		s.iOn = ch->GetQuestFlag(PLAYERBOT_WS_FLAG_ON);
		if (s.iOn != 1)
			return;
		s.bWorn = ch->GetQuestFlag(PLAYERBOT_WS_FLAG_WORN) != 0;
		s.iSince = ch->GetQuestFlag(PLAYERBOT_WS_FLAG_SINCE);
		s.llSm = std::max(0, ch->GetQuestFlag(PLAYERBOT_WS_FLAG_SM));
		int pieces = 0, stored = 0, lost = 0;
		for (int i = 0; i < PLAYERBOT_WS_SLOTS; ++i)
		{
			const DWORD w = (DWORD)ch->GetQuestFlag(GetPlayerBotWindSetFlag('w', i));
			const DWORD l = (DWORD)ch->GetQuestFlag(GetPlayerBotWindSetFlag('l', i));
			if (w && FindPlayerBotWindSetItem(ch, w))
			{
				s.adwW[i] = w;
				++pieces;
			}
			else if (w)
			{
				ch->SetQuestFlag(GetPlayerBotWindSetFlag('w', i), 0);
				++lost;
			}
			if (l && s.bWorn && FindPlayerBotWindSetItem(ch, l))
			{
				s.adwL[i] = l;
				++stored;
			}
			else if (l)
				ch->SetQuestFlag(GetPlayerBotWindSetFlag('l', i), 0);
		}
		sys_log(0, "PLAYERBOT_WINDSET: loaded pid=%u name=%s lv=%d pieces=%d stored_lightning=%d lost=%d worn=%d sm=%lld",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), pieces, stored, lost, s.bWorn ? 1 : 0, s.llSm);
	}

	TPlayerBotWindSet* FindPlayerBotWindSet(LPCHARACTER ch)
	{
		if (!ch || s_mapPlayerBotWindSet.empty())
			return NULL;
		std::map<DWORD, TPlayerBotWindSet>::iterator it = s_mapPlayerBotWindSet.find(ch->GetPlayerID());
		return it != s_mapPlayerBotWindSet.end() ? &it->second : NULL;
	}

	// An open record (the set kept, built or worn): its pieces are kept whatever the switch says...
	TPlayerBotWindSet* FindPlayerBotWindSetKept(LPCHARACTER ch)
	{
		TPlayerBotWindSet* s = FindPlayerBotWindSet(ch);
		return s && s->iOn == 1 ? s : NULL;
	}

	// ... and it steers the other passes (the guard, the gates, the swap) only with the switch on.
	TPlayerBotWindSet* FindPlayerBotWindSetOpen(LPCHARACTER ch)
	{
		TPlayerBotWindSet* s = FindPlayerBotWindSetKept(ch);
		return s && IsPlayerBotWindSetOn() ? s : NULL;
	}

	void NotePlayerBotWindSetBlocked(LPCHARACTER ch, TPlayerBotWindSet& s, const char* why, const char* detail, DWORD dwNow)
	{
		if (s.strBlocked == why && s.dwBlockedAt != 0 && dwNow - s.dwBlockedAt < PLAYERBOT_WS_BLOCKED_LOG_MS)
			return;
		s.strBlocked = why;
		s.dwBlockedAt = dwNow ? dwNow : 1;
		++s_kPlayerBotWindSetStats.blocked;
		sys_log(0, "PLAYERBOT_WINDSET: blocked pid=%u name=%s lv=%d why=%s%s%s", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(),
				why, detail && *detail ? " " : "", detail ? detail : "");
	}

	int GetPlayerBotWindSetSlotOfWear(int wear)
	{
		for (int i = 0; i < PLAYERBOT_WS_SLOTS; ++i)
			if (PLAYERBOT_WS_WEARS[i] == wear)
				return i;
		return -1;
	}

	bool IsPlayerBotWindSetCostumeSlot(int slot)
	{
		return slot == PLAYERBOT_WS_COSTUME || slot == PLAYERBOT_WS_HAIR;
	}

	// The lightning piece of the slot: worn now, or waiting in the bag while the wind set is on.
	LPITEM GetPlayerBotWindSetLightningPiece(LPCHARACTER ch, const TPlayerBotWindSet& s, int slot)
	{
		return s.bWorn ? FindPlayerBotWindSetItem(ch, s.adwL[slot]) : ch->GetWear(PLAYERBOT_WS_WEARS[slot]);
	}

	// ------------------------------------------------------------ the hooks' answers

	bool IsPlayerBotWindSetStored(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || s_mapPlayerBotWindSet.empty() || item->IsEquipped() || item->GetID() == 0)
			return false;
		const TPlayerBotWindSet* s = FindPlayerBotWindSetKept(ch);
		if (!s)
			return false;
		const DWORD id = item->GetID();
		for (int i = 0; i < PLAYERBOT_WS_SLOTS; ++i)
			if (s->adwW[i] == id || (s->bWorn && s->adwL[i] == id))
				return true;
		// the look bought for the set, until the set's look takes it
		return s->dwLookVnum != 0 && item->GetVnum() == s->dwLookVnum && item->GetType() == ITEM_COSTUME &&
				get_dword_time() - s->dwLookAt < PLAYERBOT_WS_LOOK_PENDING_MS;
	}

	bool IsPlayerBotWindSetWornLocked(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || s_mapPlayerBotWindSet.empty() || !item->IsEquipped() || item->GetID() == 0)
			return false;
		const TPlayerBotWindSet* s = FindPlayerBotWindSetKept(ch);
		if (!s || !s->bWorn)
			return false;
		for (int i = 0; i < PLAYERBOT_WS_SLOTS; ++i)
			if (s->adwW[i] == item->GetID())
				return true;
		return false;
	}

	bool IsPlayerBotWindSetGuardedPiece(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || s_mapPlayerBotWindSet.empty() || !item->IsEquipped() || item->GetOwner() != ch)
			return false;
		const TPlayerBotWindSet* s = FindPlayerBotWindSetOpen(ch);
		if (!s || s->bWorn)
			return false;
		for (int i = 0; i < PLAYERBOT_WS_SLOTS; ++i)
			if (s->adwW[i] == item->GetID())
				return false;
		return true;
	}

	bool IsPlayerBotWindSetBuilding(LPCHARACTER ch)
	{
		const TPlayerBotWindSet* s = FindPlayerBotWindSetOpen(ch);
		return s && !s->bWorn;
	}

	bool IsPlayerBotWindSetSwapPending(LPCHARACTER ch)
	{
		const TPlayerBotWindSet* s = FindPlayerBotWindSetOpen(ch);
		return s && s->bSwapDue;
	}

	// What the element's resistance would be with the stored set on in place of the worn pieces of its slots, and the
	// best talisman of the element on the pendant (the talisman pass wears it on the element's map). -1: no such set.
	int GetPlayerBotWindSetElementResist(LPCHARACTER ch, int e)
	{
		const TPlayerBotWindSet* s = FindPlayerBotWindSetOpen(ch);
		if (!s || e < 0 || e >= 6)
			return -1;
		const DWORD* other = NULL;
		if (e == PLAYERBOT_EM_WIND && !s->bWorn)
			other = s->adwW;
		else if (e == PLAYERBOT_EM_ELEC && s->bWorn)
			other = s->adwL;
		else
			return -1;
		const BYTE point = PLAYERBOT_ELEMENT_MAP_POINTS[e];
		int total = Bonus67Total(ch, point);
		int pieces = 0;
		for (int slot = 0; slot < PLAYERBOT_WS_SLOTS; ++slot)
		{
			LPITEM piece = FindPlayerBotWindSetItem(ch, other[slot]);
			if (!piece || piece->IsEquipped())
				continue;
			++pieces;
			total += GetPlayerBotElementMapPieceValue(piece, point) -
					GetPlayerBotElementMapPieceValue(ch->GetWear(PLAYERBOT_WS_WEARS[slot]), point);
		}
		if (pieces == 0)
			return -1;
		LPITEM talisman = FindPlayerBotTalismanOfElement(ch, e);
		LPITEM pendant = ch->GetWear(WEAR_PENDANT);
		if (talisman && talisman != pendant)
			total += std::max(0, GetPlayerBotElementMapPieceValue(talisman, point) - GetPlayerBotElementMapPieceValue(pendant, point));
		return std::max(0, std::min(total, PLAYERBOT_ELEMENT_MAP_RESIST_CAP));
	}

	int GetPlayerBotWindSetRefineTarget(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || s_mapPlayerBotWindSet.empty() || item->GetRefinedVnum() == 0)
			return -1;
		const TPlayerBotWindSet* s = FindPlayerBotWindSetOpen(ch);
		if (!s)
			return -1;
		for (int slot = 0; slot < PLAYERBOT_WS_GEAR; ++slot)
		{
			if (s->adwW[slot] != item->GetID())
				continue;
			LPITEM lightning = GetPlayerBotWindSetLightningPiece(ch, *s, slot);
			if (!lightning)
				return -1;	// the ordinary rules
			return std::max((int)item->GetRefineLevel(), std::min((int)lightning->GetRefineLevel(), 9));
		}
		return -1;
	}

	void NotePlayerBotWindSetRefined(LPCHARACTER ch, DWORD oldId, LPITEM made)
	{
		TPlayerBotWindSet* s = FindPlayerBotWindSetOpen(ch);
		if (!s || oldId == 0)
			return;
		for (int slot = 0; slot < PLAYERBOT_WS_SLOTS; ++slot)
		{
			const bool wind = s->adwW[slot] == oldId;
			if (!wind && s->adwL[slot] != oldId)
				continue;
			const DWORD newId = made && made->GetID() != oldId && made->GetOwner() == ch ? made->GetID() : 0;
			if (wind)
				SetPlayerBotWindSetPiece(ch, *s, slot, newId);
			else
				SetPlayerBotWindSetStoredL(ch, *s, slot, newId);
			if (newId)
			{
				// the changes spent follow the piece
				std::map<DWORD, int>::iterator c = s->mapChanges.find(oldId);
				if (c != s->mapChanges.end())
				{
					s->mapChanges[newId] = c->second;
					s->mapChanges.erase(oldId);
				}
				++s_kPlayerBotWindSetStats.refined;
			}
			else
				++s_kPlayerBotWindSetStats.burned;
			sys_log(0, "PLAYERBOT_WINDSET: refined pid=%u name=%s set=%s slot=%s old_id=%u new=%u+%d id=%u",
					ch->GetPlayerID(), ch->GetName(), wind ? "wind" : "lightning", PLAYERBOT_WS_NAMES[slot], oldId,
					newId ? made->GetVnum() : 0, newId ? (int)made->GetRefineLevel() : -1, newId);
			return;
		}
	}

	bool IsPlayerBotWindSetTalismanKept(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !IsPlayerBotTalismanItem(item) || !FindPlayerBotWindSetKept(ch))
			return false;
		const int e = GetPlayerBotTalismanElementOf(item->GetVnum());
		if (e != PLAYERBOT_EM_ELEC && e != PLAYERBOT_EM_WIND)
			return false;
		return item == FindPlayerBotTalismanOfElement(ch, e);
	}

	// ------------------------------------------------------------ the pieces

	long long GetPlayerBotWindSetPieceScore(LPCHARACTER ch, int slot, LPITEM item)
	{
		return IsPlayerBotWindSetCostumeSlot(slot) ? (long long)CountPlayerBotGoodCostumeLines(ch, item)
				: GetPlayerBotEquipmentScore(item, ch);
	}

	bool IsPlayerBotWindSetCandidate(LPCHARACTER ch, const TPlayerBotWindSet& s, int slot, LPITEM item)
	{
		if (!item || item->IsEquipped() || item->isLocked() || item->IsExchanging() || item->GetID() == 0 ||
				item->GetWindow() != INVENTORY || !item->CanUsedBy(ch) || item->GetLevelLimit() > (int)ch->GetLevel())
			return false;
		for (int i = 0; i < PLAYERBOT_WS_SLOTS; ++i)
			if (s.adwW[i] == item->GetID() || s.adwL[i] == item->GetID())
				return false;
		// the lightning EQ is never rerolled for wind: a piece with a lightning line is not the set's
		if (HasPlayerBotElementProgressKeptLine(item, PLAYERBOT_EM_ELEC) || item->GetAttributeSetIndex() < 0 ||
				IsPlayerBotSidekickLockedItem(ch, item))
			return false;
		if (IsPlayerBotWindSetCostumeSlot(slot))
			return item->GetType() == ITEM_COSTUME &&
					item->GetSubType() == (slot == PLAYERBOT_WS_COSTUME ? COSTUME_BODY : COSTUME_HAIR) &&
					GetPlayerBotCostumeSecondsLeft(item) >= PLAYERBOT_COSTUME_BONUS_MIN_SECONDS_LEFT;
		if (item->GetType() != ITEM_ARMOR || item->FindEquipCell(ch) != (int)PLAYERBOT_WS_WEARS[slot] ||
				Mt2009IsElementStone(item->GetVnum()) || IsPlayerBotTalismanItem(item))
			return false;
		LPITEM lightning = GetPlayerBotWindSetLightningPiece(ch, s, slot);
		return !lightning || GetPlayerBotEquipmentScore(item, ch) * 100 >=
				GetPlayerBotEquipmentScore(lightning, ch) * PLAYERBOT_WS_MIN_SCORE_PCT;
	}

	LPITEM FindPlayerBotWindSetCandidate(LPCHARACTER ch, const TPlayerBotWindSet& s, int slot)
	{
		const BYTE point = PLAYERBOT_ELEMENT_MAP_POINTS[PLAYERBOT_EM_WIND];
		LPITEM best = NULL;
		int bestLine = 0;
		long long bestScore = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || !IsPlayerBotWindSetCandidate(ch, s, slot, item))
				continue;
			const int line = GetPlayerBotElementShopLine(item, point);
			const long long score = GetPlayerBotWindSetPieceScore(ch, slot, item);
			if (!best || line > bestLine || (line == bestLine && score > bestScore))
			{
				best = item;
				bestLine = line;
				bestScore = score;
			}
		}
		return best;
	}

	// The wind line's level-4 value on the piece's attribute set (0: the set rolls no wind).
	int GetPlayerBotWindSetFloor(LPITEM item)
	{
		const BYTE point = PLAYERBOT_ELEMENT_MAP_POINTS[PLAYERBOT_EM_WIND];
		const int set = item ? item->GetAttributeSetIndex() : -1;
		if (set < 0 || set >= ATTRIBUTE_SET_MAX_NUM || !IsPlayerBotApplyOnAttrSet(point, set))
			return 0;
		TItemAttrMap::const_iterator it = g_map_itemAttr.find(point);
		if (it == g_map_itemAttr.end() || it->second.bMaxLevelBySet[set] == 0)
			return 0;
		const int maxLevel = std::max(1, std::min((int)it->second.bMaxLevelBySet[set], 5));
		return (int)GetPlayerBotElementShopLevelValue(set, point, it->second, std::min(4, maxLevel));
	}

	bool IsPlayerBotWindSetHpWanted(int slot, LPITEM item)
	{
		const int set = item ? item->GetAttributeSetIndex() : -1;
		return (slot == PLAYERBOT_WS_BODY || slot == PLAYERBOT_WS_WRIST) && set >= 0 && set < ATTRIBUTE_SET_MAX_NUM &&
				IsPlayerBotApplyOnAttrSet((BYTE)APPLY_MAX_HP, set);
	}

	int GetPlayerBotWindSetChanges(const TPlayerBotWindSet& s, LPITEM item)
	{
		std::map<DWORD, int>::const_iterator it = s.mapChanges.find(item->GetID());
		return it != s.mapChanges.end() ? it->second : 0;
	}

	// The costume / hairstyle's next reagent (0 finished): a reset while it has no line, changes until wind 10.
	DWORD GetPlayerBotWindSetCostumeNeedOf(const TPlayerBotWindSet& s, LPITEM item, const char** done)
	{
		*done = "";
		const int floor = GetPlayerBotWindSetFloor(item);
		if (floor <= 0)
		{
			*done = "no_wind";
			return 0;
		}
		if (GetPlayerBotElementShopLine(item, PLAYERBOT_ELEMENT_MAP_POINTS[PLAYERBOT_EM_WIND]) >= floor)
		{
			*done = "wind";
			return 0;
		}
		if (GetPlayerBotWindSetChanges(s, item) >= PLAYERBOT_WS_COSTUME_CHANGES)
		{
			*done = "budget";
			return 0;
		}
		return item->GetAttributeCount() == 0 ? PLAYERBOT_COSTUME_RESET_VNUM : PLAYERBOT_COSTUME_CHANGE_VNUM;
	}

	bool IsPlayerBotWindSetPieceReady(const TPlayerBotWindSet& s, int slot, LPITEM item)
	{
		if (IsPlayerBotWindSetCostumeSlot(slot))
		{
			const char* done = "";
			return GetPlayerBotWindSetCostumeNeedOf(s, item, &done) == 0;
		}
		const int floor = GetPlayerBotWindSetFloor(item);
		const int spent = GetPlayerBotWindSetChanges(s, item);
		if (floor <= 0 || !CanPlayerBotTakeBonusStone(item) || spent >= PLAYERBOT_WS_GIVE_UP)
			return true;
		if (GetPlayerBotElementShopLine(item, PLAYERBOT_ELEMENT_MAP_POINTS[PLAYERBOT_EM_WIND]) < floor)
			return false;
		return !IsPlayerBotWindSetHpWanted(slot, item) || GetPlayerBotElementShopLine(item, (BYTE)APPLY_MAX_HP) > 0 ||
				spent >= PLAYERBOT_WS_HP_CHANGES;
	}

	void TakePlayerBotWindSetPiece(LPCHARACTER ch, TPlayerBotWindSet& s, int slot, LPITEM item, const char* source)
	{
		const DWORD old = s.adwW[slot];
		SetPlayerBotWindSetPiece(ch, s, slot, item->GetID());
		if (!strcmp(source, "market"))
			++s_kPlayerBotWindSetStats.piecesMarket;
		else if (!strcmp(source, "itemshop"))
			++s_kPlayerBotWindSetStats.piecesLook;
		else
			++s_kPlayerBotWindSetStats.piecesOwn;
		LPITEM lightning = GetPlayerBotWindSetLightningPiece(ch, s, slot);
		sys_log(0, "PLAYERBOT_WINDSET: piece pid=%u name=%s lv=%d slot=%s vnum=%u+%d id=%u source=%s wind=%d lines=%d "
				"lightning_piece=%u+%d replaced=%u",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), PLAYERBOT_WS_NAMES[slot], item->GetVnum(),
				(int)item->GetRefineLevel(), item->GetID(), source,
				GetPlayerBotElementShopLine(item, PLAYERBOT_ELEMENT_MAP_POINTS[PLAYERBOT_EM_WIND]), item->GetAttributeCount(),
				lightning ? lightning->GetVnum() : 0, lightning ? (int)lightning->GetRefineLevel() : -1, old);
	}

	// ------------------------------------------------------------ the market and the ItemShop

	int GetPlayerBotWindSetOfferSlot(LPCHARACTER ch, const TPlayerBotWindSet& s, LPITEM offer)
	{
		if (offer->GetType() != ITEM_ARMOR || offer->GetLevelLimit() > (int)ch->GetLevel() || !offer->CanUsedBy(ch) ||
				offer->GetAttributeSetIndex() < 0 || Mt2009IsElementStone(offer->GetVnum()) || IsPlayerBotTalismanItem(offer) ||
				HasPlayerBotElementProgressKeptLine(offer, PLAYERBOT_EM_ELEC))
			return -1;
		const int slot = GetPlayerBotWindSetSlotOfWear(offer->FindEquipCell(ch));
		if (slot < 0 || slot >= PLAYERBOT_WS_GEAR || s.adwW[slot] != 0)
			return -1;
		LPITEM lightning = GetPlayerBotWindSetLightningPiece(ch, s, slot);
		if (lightning && GetPlayerBotEquipmentScore(offer, ch) * 100 <
				GetPlayerBotEquipmentScore(lightning, ch) * PLAYERBOT_WS_MIN_SCORE_PCT)
			return -1;
		return slot;
	}

	bool WantsPlayerBotWindSetOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer || s_mapPlayerBotWindSet.empty() || offer->GetType() != ITEM_ARMOR)
			return false;
		const TPlayerBotWindSet* s = FindPlayerBotWindSetOpen(ch);
		return s && !s->bWorn && GetPlayerBotWindSetOfferSlot(ch, *s, offer) >= 0;
	}

	bool CanPlayerBotPayForWindSetOffer(LPCHARACTER ch, LPITEM offer, long long price)
	{
		if (!ch || !offer || price <= 0)
			return false;
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		return price <= spare * PLAYERBOT_WS_MARKET_PURSE_PCT / 100;
	}

	// The empty gear slots' walk list: the lightning piece's family from PLAYERBOT_WS_MARKET_PLUS_BELOW under its plus to +9.
	void CollectPlayerBotWindSetMissing(LPCHARACTER ch, std::map<DWORD, int>& missing)
	{
		const TPlayerBotWindSet* s = FindPlayerBotWindSetOpen(ch);
		if (!s || s->bWorn)
			return;
		for (int slot = 0; slot < PLAYERBOT_WS_GEAR; ++slot)
		{
			if (s->adwW[slot] != 0)
				continue;
			LPITEM lightning = GetPlayerBotWindSetLightningPiece(ch, *s, slot);
			if (!lightning || lightning->GetType() != ITEM_ARMOR)
				continue;
			const int plus = (int)(lightning->GetVnum() % 10);
			if (plus != (int)lightning->GetRefineLevel())
				continue;
			const DWORD base = lightning->GetVnum() - (DWORD)plus;
			for (int p = std::max(0, plus - PLAYERBOT_WS_MARKET_PLUS_BELOW); p <= 9; ++p)
			{
				const DWORD vnum = base + (DWORD)p;
				const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
				if (proto && proto->bType == ITEM_ARMOR && proto->bSubType == lightning->GetSubType() && missing[vnum] < 1)
					missing[vnum] = 1;
			}
		}
	}

	void NotePlayerBotWindSetBought(LPCHARACTER ch, DWORD vnum, long long price)
	{
		TPlayerBotWindSet* s = FindPlayerBotWindSetOpen(ch);
		if (!s || s->bWorn)
			return;
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		if (!proto || proto->bType != ITEM_ARMOR)
			return;
		s->dwBoughtVnum = vnum;
		s->dwNextLook = 0;
		++s_kPlayerBotWindSetStats.bought;
		sys_log(0, "PLAYERBOT_WINDSET: bought pid=%u name=%s lv=%d vnum=%u price=%lld", ch->GetPlayerID(), ch->GetName(),
				ch->GetLevel(), vnum, price);
	}

	// A costume / hairstyle of the ItemShop V3 for the set's empty costume slot, when the bag holds no candidate.
	DWORD PickPlayerBotWindSetLook(LPCHARACTER ch, int* pLook)
	{
		TPlayerBotWindSet* s = FindPlayerBotWindSetOpen(ch);
		if (!s || s->bWorn || !pLook)
			return 0;
		for (int k = 0; k < 2; ++k)
		{
			const int slot = PLAYERBOT_WS_COSTUME + k;
			if (s->adwW[slot] != 0 || FindPlayerBotWindSetCandidate(ch, *s, slot))
				continue;
			const int look = k == 0 ? PLAYERBOT_ISHOP_LOOK_BODY : PLAYERBOT_ISHOP_LOOK_HAIR;
			if (IsPlayerBotLookMonthBlocked(ch, look))
				continue;
			const std::vector<DWORD>& catalogue = GetPlayerBotLookCatalogue(look);
			std::vector<DWORD> lasting;
			for (size_t i = 0; i < catalogue.size(); ++i)
			{
				const TItemTable* proto = ITEM_MANAGER::instance().GetTable(catalogue[i]);
				if (!IsPlayerBotOwnLook(ch, proto, look))
					continue;
				const long seconds = GetPlayerBotLookSeconds(proto);
				if (seconds == 0 || seconds >= PLAYERBOT_ISHOP_LOOK_MIN_SECONDS)
					lasting.push_back(catalogue[i]);
			}
			if (lasting.empty())
				continue;
			*pLook = look;
			s->dwLookVnum = lasting[number(0, (int)lasting.size() - 1)];
			s->dwLookAt = get_dword_time();
			s->dwNextLook = 0;
			return s->dwLookVnum;
		}
		return 0;
	}

	// The wind talisman: the Blacksmith's daily deal (MT2009_PLUS_BOT_TALISMAN_DAILY_V1's price and once-a-day flag) when
	// the bot owns no talisman of wind, in a village.
	bool BuyPlayerBotWindSetTalisman(LPCHARACTER ch)
	{
		if (!IsPlayerBotVillageMap(ch->GetMapIndex()) || (int)ch->GetLevel() < PLAYERBOT_TALISMAN_FIRST_MIN_LEVEL ||
				FindPlayerBotTalismanOfElement(ch, PLAYERBOT_EM_WIND) || IsPlayerBotGearFrozen(ch) || ch->GetExchange() ||
				ch->GetMyShop())
			return false;
		quest::CQuestManager& q = quest::CQuestManager::instance();
		if (q.GetEventFlag("m2_bot_talisman_first_off") != 0)
			return false;
		const int last = ch->GetQuestFlag(PLAYERBOT_TALISMAN_FIRST_FLAG);
		if (last != 0 && get_global_time() - last < PLAYERBOT_TALISMAN_FIRST_GAP_H * 3600)
			return false;
		const DWORD vnum = PLAYERBOT_TALISMAN_ELEMENT[PLAYERBOT_EM_WIND].baseVnum;
		const int flag = q.GetEventFlag("m2_bot_talisman_first_yang");
		const long long price = flag >= 10000 && flag <= 5000000 ? (long long)flag : PLAYERBOT_TALISMAN_FIRST_YANG;
		if (!IsPlayerBotWearableAtLevel(ch, vnum) || GetPlayerBotTalismanSpare(ch) < price || ch->GetEmptyInventory(1) < 0)
			return false;
		PlayerBotChangeGold(ch, -price);
		if (!ch->AutoGiveItem(vnum, 1, -1, false))
		{
			PlayerBotChangeGold(ch, price);
			return false;
		}
		ch->SetQuestFlag(PLAYERBOT_TALISMAN_FIRST_FLAG, get_global_time());
		ForgetPlayerBotTalismanPlan(ch);
		++s_kPlayerBotWindSetStats.talismans;
		sys_log(0, "PLAYERBOT_WINDSET: talisman pid=%u name=%s lv=%d vnum=%u price=%lld gold=%lld", ch->GetPlayerID(), ch->GetName(),
				ch->GetLevel(), vnum, price, (long long)ch->GetGold());
		return true;
	}

	// ------------------------------------------------------------ the bonusing (in the bag)

	// One gear piece a pass: the bag's stones first, the V3 batches within the set's SM cap.
	int RunPlayerBotWindSetBonus(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotWindSet& s, DWORD dwNow)
	{
		if (s.bWorn || (int)(dwNow - s.dwNextBonus) < 0)
			return 0;
		s.dwNextBonus = dwNow + PLAYERBOT_WS_BONUS_MS;
		LPITEM item = NULL;
		int slot = -1;
		for (int i = 0; i < PLAYERBOT_WS_GEAR && !item; ++i)
		{
			LPITEM piece = FindPlayerBotWindSetItem(ch, s.adwW[i]);
			if (piece && !piece->IsEquipped() && !piece->isLocked() && !piece->IsExchanging() &&
					!IsPlayerBotWindSetPieceReady(s, i, piece))
			{
				item = piece;
				slot = i;
			}
		}
		if (!item)
			return 0;
		const BYTE point = PLAYERBOT_ELEMENT_MAP_POINTS[PLAYERBOT_EM_WIND];
		const int floor = GetPlayerBotWindSetFloor(item);
		const bool hp = IsPlayerBotWindSetHpWanted(slot, item);
		const long long budget = GetPlayerBotElementShopBudgetFor(PLAYERBOT_EM_WIND);
		const long long smBefore = s.llSm;
		int purchases = 0;
		const bool fill = item->GetAttributeCount() < PLAYERBOT_BONUS_MAX_LINES && CanPlayerBotItemRollNewLine(item);
		if (s.llSm < budget)
		{
			if (fill && (int)ch->CountSpecifyItem(PLAYERBOT_BONUS_ADD_VNUM) < PLAYERBOT_BONUS_MAX_LINES - item->GetAttributeCount() + 1)
				s.llSm += BuyPlayerBotElementShopBatch(ch, state, PLAYERBOT_BONUS_ADD_VNUM, PLAYERBOT_ESHOP_ADD_BATCH, "wind_set_add",
						dwNow, &purchases);
			if (s.llSm < budget && (int)ch->CountSpecifyItem(PLAYERBOT_BONUS_CHANGE_VNUM) < PLAYERBOT_WS_STONES_PER_PASS)
				s.llSm += BuyPlayerBotElementShopBatch(ch, state, PLAYERBOT_BONUS_CHANGE_VNUM, PLAYERBOT_ESHOP_CHANGE_BATCH,
						"wind_set_change", dwNow, &purchases);
		}
		const int lineBefore = GetPlayerBotElementShopLine(item, point);
		const int linesBefore = item->GetAttributeCount();
		int adds = 0, changes = 0;
		int& spent = s.mapChanges[item->GetID()];
		while (adds + changes < PLAYERBOT_WS_STONES_PER_PASS && !IsPlayerBotWindSetPieceReady(s, slot, item))
		{
			const int count = item->GetAttributeCount();
			int cell = -1;
			if (count < PLAYERBOT_BONUS_MAX_LINES && CanPlayerBotItemRollNewLine(item) &&
					(cell = FindPlayerBotElementShopStone(ch, PLAYERBOT_BONUS_ADD_VNUM, item)) >= 0)
			{
				if (number(1, 100) <= aiItemAttributeAddPercent[count])
					item->AddAttribute();
				ConsumePlayerBotBonusStoneAt(ch, cell);
				LogManager::instance().ItemLog(ch, item, "PLAYERBOT_WINDSET_ADD", item->GetName());
				++adds;
			}
			else if (count > 0 && (cell = FindPlayerBotElementShopStone(ch, PLAYERBOT_BONUS_CHANGE_VNUM, item)) >= 0)
			{
				item->ChangeAttribute();
				ConsumePlayerBotBonusStoneAt(ch, cell);
				LogManager::instance().ItemLog(ch, item, "PLAYERBOT_WINDSET_CHANGE", item->GetName());
				++changes;
				++spent;
			}
			else
				break;
		}
		if (s.llSm != smBefore)
		{
			ch->SetQuestFlag(PLAYERBOT_WS_FLAG_SM, (int)std::min<long long>(s.llSm, 2000000000LL));
			s_kPlayerBotWindSetStats.sm += s.llSm - smBefore;
		}
		if (adds + changes == 0)
		{
			char detail[96];
			snprintf(detail, sizeof(detail), "slot=%s sm=%lld budget=%lld coins=%d", PLAYERBOT_WS_NAMES[slot], s.llSm, budget,
					state.iDragonCoins);
			NotePlayerBotWindSetBlocked(ch, s, s.llSm >= budget ? "budget" : "no_stones", detail, dwNow);
			return 0;
		}
		item->UpdatePacket();
		s_kPlayerBotWindSetStats.adds += (unsigned int)adds;
		s_kPlayerBotWindSetStats.changes += (unsigned int)changes;
		sys_log(0, "PLAYERBOT_WINDSET: bonus pid=%u name=%s lv=%d slot=%s vnum=%u+%d lines=%d->%d wind=%d->%d floor=%d hp=%d/%d "
				"adds=%d changes=%d piece_changes=%d sm=%lld budget=%lld coins=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), PLAYERBOT_WS_NAMES[slot], item->GetVnum(),
				(int)item->GetRefineLevel(), linesBefore, item->GetAttributeCount(), lineBefore, GetPlayerBotElementShopLine(item, point),
				floor, hp ? 1 : 0, GetPlayerBotElementShopLine(item, (BYTE)APPLY_MAX_HP), adds, changes, spent, s.llSm, budget,
				state.iDragonCoins);
		return adds + changes;
	}

	DWORD GetPlayerBotWindSetCostumeReagentNeed(LPCHARACTER ch)
	{
		const TPlayerBotWindSet* s = FindPlayerBotWindSetOpen(ch);
		if (!s || s->bWorn)
			return 0;
		for (int k = 0; k < 2; ++k)
		{
			LPITEM item = FindPlayerBotWindSetItem(ch, s->adwW[PLAYERBOT_WS_COSTUME + k]);
			const char* done = "";
			if (item && !item->IsEquipped())
			{
				const DWORD need = GetPlayerBotWindSetCostumeNeedOf(*s, item, &done);
				if (need)
					return need;
			}
		}
		return 0;
	}

	// A few rolls on the set's costume or hairstyle in the bag, with the engine's checks of the reagents' handler (a reset
	// leaves one to three lines, a change the same count - else the old lines go back and the reagent stays).
	bool RunPlayerBotWindSetCostumeRoll(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		(void)state;
		TPlayerBotWindSet* s = FindPlayerBotWindSetOpen(ch);
		if (!s || s->bWorn || (int)(dwNow - s->dwNextCostume) < 0)
			return false;
		s->dwNextCostume = dwNow + PLAYERBOT_WS_COSTUME_MS;
		const BYTE point = PLAYERBOT_ELEMENT_MAP_POINTS[PLAYERBOT_EM_WIND];
		for (int k = 0; k < 2; ++k)
		{
			LPITEM item = FindPlayerBotWindSetItem(ch, s->adwW[PLAYERBOT_WS_COSTUME + k]);
			if (!item || item->IsEquipped() || item->isLocked() || item->IsExchanging())
				continue;
			const char* done = "";
			DWORD need = GetPlayerBotWindSetCostumeNeedOf(*s, item, &done);
			if (!need)
				continue;
			int cell = FindPlayerBotCostumeReagentCell(ch, need);
			if (cell < 0)
			{
				char detail[48];
				snprintf(detail, sizeof(detail), "piece=%s reagent=%u", k == 0 ? "costume" : "hair", need);
				NotePlayerBotWindSetBlocked(ch, *s, "no_reagent", detail, dwNow);
				return false;
			}
			const int linesBefore = item->GetAttributeCount();
			const int lineBefore = GetPlayerBotElementShopLine(item, point);
			int resets = 0, changes = 0;
			while (resets + changes < PLAYERBOT_COSTUME_ROLLS_PER_PASS && need && cell >= 0)
			{
				const int countBefore = item->GetAttributeCount();
				TPlayerItemAttribute aBefore[ITEM_ATTRIBUTE_MAX_NUM];
				memcpy(aBefore, item->GetAttributes(), sizeof(aBefore));
				const bool reset = need == PLAYERBOT_COSTUME_RESET_VNUM;
				if (reset)
				{
					item->ClearAttribute();
					item->AlterToMagicItem();
				}
				else
					item->ChangeAttribute();
				const int countAfter = item->GetAttributeCount();
				if (reset ? (countAfter < 1 || countAfter > 3) : countAfter != countBefore)
				{
					item->SetAttributes(aBefore);
					sys_err("PLAYERBOT_WINDSET: costume %s left %d line(s) (had %d) pid=%u vnum=%u - restored",
							reset ? "reset" : "change", countAfter, countBefore, ch->GetPlayerID(), item->GetVnum());
					break;
				}
				ConsumePlayerBotBonusStoneAt(ch, cell);
				if (reset)
					++resets;
				else
				{
					++changes;
					++s->mapChanges[item->GetID()];
				}
				++s_kPlayerBotWindSetStats.costumeRolls;
				LogManager::instance().ItemLog(ch, item, reset ? "PLAYERBOT_WINDSET_COSTUME_RESET" : "PLAYERBOT_WINDSET_COSTUME_CHANGE",
						item->GetName());
				// a reset that ran out of its count: changes only from here
				if (reset && resets >= PLAYERBOT_WS_COSTUME_RESETS)
					break;
				need = GetPlayerBotWindSetCostumeNeedOf(*s, item, &done);
				cell = need ? FindPlayerBotCostumeReagentCell(ch, need) : -1;
			}
			item->UpdatePacket();
			sys_log(0, "PLAYERBOT_WINDSET: costume pid=%u name=%s lv=%d piece=%s vnum=%u resets=%d changes=%d lines=%d->%d wind=%d->%d "
					"total_changes=%d%s%s",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), k == 0 ? "costume" : "hair", item->GetVnum(), resets, changes,
					linesBefore, item->GetAttributeCount(), lineBefore, GetPlayerBotElementShopLine(item, point),
					GetPlayerBotWindSetChanges(*s, item), need ? "" : " finished=", need ? "" : done);
			return resets + changes > 0;
		}
		return false;
	}

	// ------------------------------------------------------------ the swap

	// Which set the bot should wear where it stands: 1 wind, 0 lightning, -1 no opinion (keep what is on).
	int GetPlayerBotWindSetWanted(LPCHARACTER ch, const TPlayerBotWindSet& s)
	{
		const long here = ch->GetMapIndex();
		const long base = GetPlayerBotElementMapBase(here);
		if (base == PLAYERBOT_MAP_ZAKLETY)
		{
			if (s.bWorn)
				return 1;
			return GetPlayerBotWindSetElementResist(ch, PLAYERBOT_EM_WIND) > GetPlayerBotElementMapResist(ch, PLAYERBOT_EM_WIND)
					? 1 : -1;
		}
		const int row = FindPlayerBotElementMapRow(here);
		if (row >= 0 && PLAYERBOT_ELEMENT_MAP_ROWS[row].iElement == PLAYERBOT_EM_ELEC)
			return 0;
		if (!IsPlayerBotVillageMap(here))
			return -1;
		// in a village: the map the travel pass wants
		std::map<DWORD, TPlayerBotElementMapGoal>::const_iterator g = s_mapPlayerBotElementMapGoal.find(ch->GetPlayerID());
		if (g == s_mapPlayerBotElementMapGoal.end() || g->second.dwAt == 0 ||
				get_dword_time() - g->second.dwAt >= PLAYERBOT_ELEMENT_MAP_GOAL_MS)
			return -1;
		if (g->second.lWanted == PLAYERBOT_MAP_ZAKLETY)
		{
			if (s.bWorn)
				return 1;
			return GetPlayerBotWindSetElementResist(ch, PLAYERBOT_EM_WIND) >= GetPlayerBotWindSetGate() ? 1 : -1;
		}
		const int wantedRow = FindPlayerBotElementMapRow(g->second.lWanted);
		return wantedRow >= 0 && PLAYERBOT_ELEMENT_MAP_ROWS[wantedRow].iElement == PLAYERBOT_EM_ELEC ? 0 : -1;
	}

	int SwapPlayerBotWindSet(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotWindSet& s, bool in)
	{
		int moved = 0, failed = 0;
		std::string desc;
		char buf[48];
		const int windBefore = GetPlayerBotElementMapResist(ch, PLAYERBOT_EM_WIND);
		const int elecBefore = GetPlayerBotElementMapResist(ch, PLAYERBOT_EM_ELEC);
		for (int slot = 0; slot < PLAYERBOT_WS_SLOTS; ++slot)
		{
			const BYTE wear = PLAYERBOT_WS_WEARS[slot];
			LPITEM piece = FindPlayerBotWindSetItem(ch, s.adwW[slot]);
			if (in)
			{
				if (!piece || piece->IsEquipped())
					continue;
				LPITEM worn = ch->GetWear(wear);
				if (worn && (IS_SET(worn->GetFlag(), ITEM_FLAG_IRREMOVABLE) || IsPlayerBotSidekickLockedItem(ch, worn)))
				{
					++failed;
					continue;
				}
				const DWORD wornId = worn ? worn->GetID() : 0;
				if (!PlayerBotEquipItem(ch, piece) || !piece->IsEquipped())
				{
					++failed;
					continue;
				}
				SetPlayerBotWindSetStoredL(ch, s, slot, wornId);
				++moved;
				snprintf(buf, sizeof(buf), "%s%s:%u", desc.empty() ? "" : " ", PLAYERBOT_WS_NAMES[slot], piece->GetVnum());
				desc += buf;
			}
			else
			{
				LPITEM back = FindPlayerBotWindSetItem(ch, s.adwL[slot]);
				if (back && !back->IsEquipped())
				{
					if (PlayerBotEquipItem(ch, back) && back->IsEquipped())
					{
						++moved;
						snprintf(buf, sizeof(buf), "%s%s:%u", desc.empty() ? "" : " ", PLAYERBOT_WS_NAMES[slot], back->GetVnum());
						desc += buf;
					}
					else
						++failed;
				}
				else if (piece && piece->IsEquipped())
				{
					// nothing of the lightning set for the slot (it had none): the slot is the equipment pass's again
					if (ch->GetEmptyInventory(piece->GetSize()) >= 0 && ch->UnequipItem(piece) && !piece->IsEquipped())
						++moved;
					else
						++failed;
				}
				if (s.adwL[slot])
					SetPlayerBotWindSetStoredL(ch, s, slot, 0);
			}
		}
		s.bWorn = in;
		s.bSwapDue = false;
		s.iSince = in ? get_global_time() : 0;
		ch->SetQuestFlag(PLAYERBOT_WS_FLAG_WORN, in ? 1 : 0);
		ch->SetQuestFlag(PLAYERBOT_WS_FLAG_SINCE, s.iSince);
		++(in ? s_kPlayerBotWindSetStats.swapIn : s_kPlayerBotWindSetStats.swapOut);
		state.bEquipPending = true;
		state.dwNextEquipmentCheckTime = 0;
		sys_log(0, "PLAYERBOT_WINDSET: %s pid=%u name=%s lv=%d map=%ld pieces=%d failed=%d wind=%d->%d lightning=%d->%d worn=[%s]",
				in ? "swap_in" : "swap_out", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), ch->GetMapIndex(), moved, failed,
				windBefore, GetPlayerBotElementMapResist(ch, PLAYERBOT_EM_WIND), elecBefore,
				GetPlayerBotElementMapResist(ch, PLAYERBOT_EM_ELEC), desc.c_str());
		return moved;
	}

	// ------------------------------------------------------------ the close (the lightning set's sale)

	// The record closed: the set not worn goes back to the bag's ordinary life (the spare-gear rules put it on the counter
	// at the fair price), the worn one stays the bot's gear. on=2 - never opened again.
	void ClosePlayerBotWindSet(LPCHARACTER ch, TPlayerBotWindSet& s, const char* why)
	{
		std::string desc;
		char buf[48];
		int released = 0;
		for (int slot = 0; slot < PLAYERBOT_WS_SLOTS; ++slot)
		{
			LPITEM piece = FindPlayerBotWindSetItem(ch, s.bWorn ? s.adwL[slot] : s.adwW[slot]);
			if (piece && !piece->IsEquipped())
			{
				++released;
				snprintf(buf, sizeof(buf), "%s%s:%u+%d", desc.empty() ? "" : " ", PLAYERBOT_WS_NAMES[slot], piece->GetVnum(),
						(int)piece->GetRefineLevel());
				desc += buf;
			}
			if (s.adwW[slot])
				SetPlayerBotWindSetPiece(ch, s, slot, 0);
			if (s.adwL[slot])
				SetPlayerBotWindSetStoredL(ch, s, slot, 0);
		}
		if (s.bWorn)
			s_kPlayerBotWindSetStats.sold += (unsigned int)released;
		else
			s_kPlayerBotWindSetStats.released += (unsigned int)released;
		sys_log(0, "PLAYERBOT_WINDSET: %s pid=%u name=%s lv=%d why=%s set=%s pieces=%d released=[%s] wind_worn_days=%d",
				s.bWorn ? "sold" : "retired", ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), why, s.bWorn ? "lightning" : "wind",
				released, desc.c_str(), s.iSince > 0 ? (int)((get_global_time() - s.iSince) / 86400) : 0);
		s.iOn = 2;
		s.bWorn = false;
		s.bSwapDue = false;
		s.bComplete = false;
		s.iSince = 0;
		s.mapChanges.clear();
		ch->SetQuestFlag(PLAYERBOT_WS_FLAG_ON, 2);
		ch->SetQuestFlag(PLAYERBOT_WS_FLAG_WORN, 0);
		ch->SetQuestFlag(PLAYERBOT_WS_FLAG_SINCE, 0);
	}

	// ------------------------------------------------------------ the census

	void TickPlayerBotWindSetCensus(DWORD dwNow)
	{
		TPlayerBotWindSetStats& st = s_kPlayerBotWindSetStats;
		if (st.dwCensusAt == 0)
		{
			st.dwCensusAt = dwNow + PLAYERBOT_WS_CENSUS_MS;
			return;
		}
		if ((int)(dwNow - st.dwCensusAt) < 0)
			return;
		st.dwCensusAt = dwNow + PLAYERBOT_WS_CENSUS_MS;
		for (std::map<DWORD, TPlayerBotWindSet>::iterator it = s_mapPlayerBotWindSet.begin(); it != s_mapPlayerBotWindSet.end();)
		{
			if (!CHARACTER_MANAGER::instance().FindByPID(it->first) && dwNow - it->second.dwSeen > PLAYERBOT_WS_FORGET_MS)
				s_mapPlayerBotWindSet.erase(it++);
			else
				++it;
		}
		const int BANDS = 4;
		static const char* const s_aszBands[BANDS] = { "90-94", "95-99", "100-104", "105-119" };
		int bots[BANDS] = { 0 }, records[BANDS] = { 0 }, held[BANDS] = { 0 }, ready[BANDS] = { 0 }, wornPieces[BANDS] = { 0 };
		int complete[BANDS] = { 0 }, usable[BANDS] = { 0 }, worn[BANDS] = { 0 }, lightKept[BANDS] = { 0 }, sold[BANDS] = { 0 };
		int talisman[BANDS] = { 0 }, firstWind[BANDS] = { 0 };
		const int gate = GetPlayerBotWindSetGate();
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !ch->IsItemLoaded() || (int)ch->GetLevel() < 90 || (int)ch->GetLevel() > PLAYERBOT_WS_MAX_LEVEL ||
					GetPlayerBotHuntElement(ch) != 0 || IsPlayerBotYoharaBonusMember(ch))
				continue;
			const int level = (int)ch->GetLevel();
			const int b = level < 95 ? 0 : level < 100 ? 1 : level < 105 ? 2 : 3;
			++bots[b];
			talisman[b] += FindPlayerBotTalismanOfElement(ch, PLAYERBOT_EM_WIND) ? 1 : 0;
			const TPlayerBotWindSet* s = FindPlayerBotWindSet(ch);
			if (!s)
				continue;
			if (s->iOn == 2)
			{
				++sold[b];
				continue;
			}
			if (s->iOn != 1)
			{
				firstWind[b] += s->strBlocked == "first_set_wind" ? 1 : 0;
				continue;
			}
			++records[b];
			for (int i = 0; i < PLAYERBOT_WS_SLOTS; ++i)
			{
				held[b] += s->adwW[i] ? 1 : 0;
				ready[b] += s->adwW[i] && s->abReady[i] ? 1 : 0;
				if (s->bWorn)
				{
					LPITEM piece = FindPlayerBotWindSetItem(ch, s->adwW[i]);
					wornPieces[b] += piece && piece->IsEquipped() ? 1 : 0;
					lightKept[b] += s->adwL[i] ? 1 : 0;
				}
			}
			complete[b] += s->bComplete ? 1 : 0;
			worn[b] += s->bWorn ? 1 : 0;
			usable[b] += s->bWorn || GetPlayerBotWindSetElementResist(ch, PLAYERBOT_EM_WIND) >= gate ? 1 : 0;
		}
		std::string line;
		for (int b = 0; b < BANDS; ++b)
		{
			if (!bots[b])
				continue;
			char buf[320];
			snprintf(buf, sizeof(buf), " %s=[bots=%d sets=%d pieces=%d/%d bonused=%d complete=%d usable=%d worn=%d worn_pieces=%d "
					"lightning_kept_pieces=%d lightning_on=%d lightning_sold=%d first_set_wind=%d wind_talisman=%d]",
					s_aszBands[b], bots[b], records[b], held[b], records[b] * PLAYERBOT_WS_SLOTS, ready[b], complete[b], usable[b],
					worn[b], wornPieces[b], lightKept[b], records[b] - worn[b], sold[b], firstWind[b], talisman[b]);
			line += buf;
		}
		sys_log(0, "PLAYERBOT_WINDSET: census%s period=[started=%u pieces_own=%u pieces_market=%u pieces_itemshop=%u bought=%u "
				"ready=%u complete=%u adds=%u changes=%u costume_rolls=%u sm=%lld talismans=%u refined=%u burned=%u swaps_in=%u "
				"swaps_out=%u lightning_sold_pieces=%u wind_released_pieces=%u blocked=%u] gate=%d budget=%lld sell_level=%d "
				"sell_days=%d on=%d",
				line.empty() ? " none" : line.c_str(), st.started, st.piecesOwn, st.piecesMarket, st.piecesLook, st.bought, st.ready,
				st.complete, st.adds, st.changes, st.costumeRolls, st.sm, st.talismans, st.refined, st.burned, st.swapIn, st.swapOut,
				st.sold, st.released, st.blocked, gate, GetPlayerBotElementShopBudgetFor(PLAYERBOT_EM_WIND),
				GetPlayerBotWindSetSellLevel(), GetPlayerBotWindSetSellDays(), IsPlayerBotWindSetOn() ? 1 : 0);
		const DWORD census = st.dwCensusAt;
		st = TPlayerBotWindSetStats();
		st.dwCensusAt = census;
	}

	// ------------------------------------------------------------ the tick

	void ManagePlayerBotWindSet(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow, bool bFighting)
	{
		TickPlayerBotWindSetCensus(dwNow);
		if (!ch || ch->IsDead() || !ch->IsItemLoaded() || !ch->GetDesc() || !ch->GetDesc()->IsBot() ||
				(int)ch->GetLevel() < GetPlayerBotWindSetFromLevel() || !IsPlayerBotWindSetOn())
			return;
		std::map<DWORD, TPlayerBotWindSet>::iterator it = s_mapPlayerBotWindSet.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotWindSet.end())
		{
			it = s_mapPlayerBotWindSet.insert(std::make_pair(ch->GetPlayerID(), TPlayerBotWindSet())).first;
			LoadPlayerBotWindSet(ch, it->second);
		}
		TPlayerBotWindSet& s = it->second;
		s.dwSeen = dwNow ? dwNow : 1;
		if (s.iOn == 2)
			return;

		// The swap, on the quick clock.
		if (s.iOn == 1 && (int)(dwNow - s.dwNextSwapLook) >= 0)
		{
			s.dwNextSwapLook = dwNow + PLAYERBOT_WS_SWAP_LOOK_MS;
			const int want = GetPlayerBotWindSetWanted(ch, s);
			s.bSwapDue = want >= 0 && (want == 1) != s.bWorn;
			const bool free = !bFighting && !ch->GetExchange() && !ch->GetMyShop() && !IsPlayerBotGearFrozen(ch) &&
					!IsPlayerBotEquipWindowShut(ch, state);
			if (s.bSwapDue && free)
			{
				SwapPlayerBotWindSet(ch, state, s, want == 1);
				return;
			}
			// the wind set on: a piece of it taken off by another pass (the element shop's or the anvil's work) goes back
			// on in the field - the equipment pass leaves the set's pieces in the bag alone
			if (s.bWorn && !s.bSwapDue && free && !IsPlayerBotVillageMap(ch->GetMapIndex()))
				for (int slot = 0; slot < PLAYERBOT_WS_SLOTS; ++slot)
				{
					LPITEM piece = FindPlayerBotWindSetItem(ch, s.adwW[slot]);
					if (piece && !piece->IsEquipped() && !piece->isLocked() && !piece->IsExchanging() &&
							PlayerBotEquipItem(ch, piece) && piece->IsEquipped())
						sys_log(0, "PLAYERBOT_WINDSET: rewear pid=%u name=%s slot=%s vnum=%u+%d", ch->GetPlayerID(), ch->GetName(),
								PLAYERBOT_WS_NAMES[slot], piece->GetVnum(), (int)piece->GetRefineLevel());
				}
		}

		if ((int)(dwNow - s.dwNextLook) < 0)
		{
			if (s.iOn == 1 && !bFighting)
				RunPlayerBotWindSetBonus(ch, state, s, dwNow);
			return;
		}
		s.dwNextLook = dwNow + PLAYERBOT_WS_LOOK_MS;

		// Out of the band: the set not worn is released (a Champion's Yohara gear is its own), the record closed.
		if (s.iOn == 1 && ((int)ch->GetLevel() > PLAYERBOT_WS_MAX_LEVEL || IsPlayerBotYoharaBonusMember(ch) ||
				GetPlayerBotHuntElement(ch) != 0))
		{
			ClosePlayerBotWindSet(ch, s, (int)ch->GetLevel() > PLAYERBOT_WS_MAX_LEVEL ? "level" : "yohara");
			return;
		}
		// The lightning set's sale: the bot on its wind set for good.
		if (s.iOn == 1 && s.bWorn && (int)ch->GetLevel() >= GetPlayerBotWindSetSellLevel() && s.iSince > 0 &&
				get_global_time() - s.iSince >= GetPlayerBotWindSetSellDays() * 86400)
		{
			ClosePlayerBotWindSet(ch, s, "past_lightning");
			return;
		}

		if (s.iOn == 0)
		{
			if (!IsPlayerBotWindSetBandBot(ch))
				return;
			// a worn set that holds Zaklety Las's wind itself needs no second one
			const int windOwn = GetPlayerBotElementMapResistOwn(ch, PLAYERBOT_EM_WIND);
			if (windOwn >= GetPlayerBotWindSetGate())
			{
				if (s.strBlocked != "first_set_wind")
					++s_kPlayerBotWindSetStats.firstSetWind;
				NotePlayerBotWindSetBlocked(ch, s, "first_set_wind", "", dwNow);
				return;
			}
			s.iOn = 1;
			s.strBlocked.clear();
			ch->SetQuestFlag(PLAYERBOT_WS_FLAG_ON, 1);
			++s_kPlayerBotWindSetStats.started;
			sys_log(0, "PLAYERBOT_WINDSET: started pid=%u name=%s lv=%d map=%ld wind_own=%d lightning_own=%d gate=%d gold=%lld coins=%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), ch->GetMapIndex(), windOwn,
					GetPlayerBotElementMapResistOwn(ch, PLAYERBOT_EM_ELEC), GetPlayerBotWindSetGate(), (long long)ch->GetGold(),
					state.iDragonCoins);
		}
		if (s.bWorn)
			return;	// the set is in use: nothing to collect or roll

		// The wind talisman.
		BuyPlayerBotWindSetTalisman(ch);

		// The pieces: an empty slot takes the best candidate of the bag.
		int heldCount = 0, readyCount = 0;
		std::string missing;
		for (int slot = 0; slot < PLAYERBOT_WS_SLOTS; ++slot)
		{
			LPITEM piece = FindPlayerBotWindSetItem(ch, s.adwW[slot]);
			if (piece && piece->IsEquipped())
			{
				// put on by another path while the lightning set is on: that path's piece now
				sys_log(0, "PLAYERBOT_WINDSET: piece worn by the lightning set pid=%u name=%s slot=%s vnum=%u id=%u", ch->GetPlayerID(),
						ch->GetName(), PLAYERBOT_WS_NAMES[slot], piece->GetVnum(), piece->GetID());
				SetPlayerBotWindSetPiece(ch, s, slot, 0);
				piece = NULL;
			}
			else if (!piece && s.adwW[slot])
			{
				sys_log(0, "PLAYERBOT_WINDSET: piece lost pid=%u name=%s slot=%s id=%u", ch->GetPlayerID(), ch->GetName(),
						PLAYERBOT_WS_NAMES[slot], s.adwW[slot]);
				SetPlayerBotWindSetPiece(ch, s, slot, 0);
			}
			if (!piece)
			{
				LPITEM candidate = FindPlayerBotWindSetCandidate(ch, s, slot);
				if (candidate)
				{
					const bool bought = s.dwBoughtVnum != 0 && candidate->GetVnum() == s.dwBoughtVnum;
					const bool look = s.dwLookVnum != 0 && candidate->GetVnum() == s.dwLookVnum;
					TakePlayerBotWindSetPiece(ch, s, slot, candidate, bought ? "market" : look ? "itemshop" : "own");
					if (bought)
						s.dwBoughtVnum = 0;
					if (look)
						s.dwLookVnum = 0;
					piece = candidate;
				}
			}
			if (!piece)
			{
				missing += missing.empty() ? PLAYERBOT_WS_NAMES[slot] : std::string(",") + PLAYERBOT_WS_NAMES[slot];
				continue;
			}
			++heldCount;
			const bool ready = IsPlayerBotWindSetPieceReady(s, slot, piece);
			if (ready && !s.abReady[slot])
			{
				++s_kPlayerBotWindSetStats.ready;
				sys_log(0, "PLAYERBOT_WINDSET: piece_ready pid=%u name=%s lv=%d slot=%s vnum=%u+%d wind=%d hp=%d lines=%d changes=%d",
						ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), PLAYERBOT_WS_NAMES[slot], piece->GetVnum(),
						(int)piece->GetRefineLevel(), GetPlayerBotElementShopLine(piece, PLAYERBOT_ELEMENT_MAP_POINTS[PLAYERBOT_EM_WIND]),
						GetPlayerBotElementShopLine(piece, (BYTE)APPLY_MAX_HP), piece->GetAttributeCount(),
						GetPlayerBotWindSetChanges(s, piece));
			}
			s.abReady[slot] = ready;
			readyCount += ready ? 1 : 0;
		}
		if (s.dwLookVnum != 0 && dwNow - s.dwLookAt >= PLAYERBOT_WS_LOOK_PENDING_MS)
			s.dwLookVnum = 0;
		const bool complete = missing.empty() && readyCount == PLAYERBOT_WS_SLOTS;
		if (complete && !s.bComplete)
		{
			++s_kPlayerBotWindSetStats.complete;
			sys_log(0, "PLAYERBOT_WINDSET: complete pid=%u name=%s lv=%d wind_with_set=%d wind_worn=%d gate=%d sm=%lld",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), GetPlayerBotWindSetElementResist(ch, PLAYERBOT_EM_WIND),
					GetPlayerBotElementMapResist(ch, PLAYERBOT_EM_WIND), GetPlayerBotWindSetGate(), s.llSm);
		}
		s.bComplete = complete;
		if (!missing.empty())
		{
			char detail[96];
			snprintf(detail, sizeof(detail), "slots=%s held=%d", missing.c_str(), heldCount);
			NotePlayerBotWindSetBlocked(ch, s, "no_piece", detail, dwNow);
		}
		if (!bFighting)
			RunPlayerBotWindSetBonus(ch, state, s, dwNow);
	}
}
#else
namespace
{
	bool IsPlayerBotWindSetStored(LPCHARACTER, LPITEM) { return false; }
	bool IsPlayerBotWindSetWornLocked(LPCHARACTER, LPITEM) { return false; }
	bool IsPlayerBotWindSetGuardedPiece(LPCHARACTER, LPITEM) { return false; }
	bool IsPlayerBotWindSetBuilding(LPCHARACTER) { return false; }
	bool IsPlayerBotWindSetSwapPending(LPCHARACTER) { return false; }
	int GetPlayerBotWindSetElementResist(LPCHARACTER, int) { return -1; }
	int GetPlayerBotWindSetRefineTarget(LPCHARACTER, LPITEM) { return -1; }
	void NotePlayerBotWindSetRefined(LPCHARACTER, DWORD, LPITEM) {}
	bool WantsPlayerBotWindSetOffer(LPCHARACTER, LPITEM) { return false; }
	bool CanPlayerBotPayForWindSetOffer(LPCHARACTER, LPITEM, long long) { return false; }
	void CollectPlayerBotWindSetMissing(LPCHARACTER, std::map<DWORD, int>&) {}
	void NotePlayerBotWindSetBought(LPCHARACTER, DWORD, long long) {}
	DWORD PickPlayerBotWindSetLook(LPCHARACTER, int*) { return 0; }
	bool RunPlayerBotWindSetCostumeRoll(LPCHARACTER, TPlayerBotAIState&, DWORD) { return false; }
	DWORD GetPlayerBotWindSetCostumeReagentNeed(LPCHARACTER) { return 0; }
	bool IsPlayerBotWindSetTalismanKept(LPCHARACTER, LPITEM) { return false; }
	void ManagePlayerBotWindSet(LPCHARACTER, TPlayerBotAIState&, DWORD, bool) {}
}
#endif
#endif

#endif
