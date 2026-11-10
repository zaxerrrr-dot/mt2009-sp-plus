#ifndef PLAYERBOT_ELEMENT_SECOND_SET_H
#define PLAYERBOT_ELEMENT_SECOND_SET_H

// MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1 - a Yohara bot's second set (the owner, 28 October 2026: "Boty zmieniaja zywiol
// tylko wtedy, gdy ida w gore. Jesli chca zmienic zywiol w dol, musza miec drugie EQ: drugi zestaw ekwipunku i drugi
// zestaw kostiumow, i bonuja to drugie EQ"; "Moga dostac drugi zestaw G0, aby wybonowac go pod inny zywiol, na tych
// samych zasadach co pierwszy G0").
//
// Who: a Yohara bot (IsPlayerBotYoharaBonusMember - a cohort's member or any bot with a Champion level) with a hunt
// element E1 (playerbot_element_resist.h). Nobody else has a record here; every hook below is a map lookup that ends
// at once for them.
//
// 1. The start. Once the first set is done for E1 - the talisman, armour, bracelet and helmet at their element target
//    or out of their budget or stones (IsPlayerBotElementGearReady, the move's own rule), the costume and hairstyle
//    finished by the costume pass - the bot picks E2: of the switched-on Sung Ma maps below the map its E1 was chosen
//    for, those whose element (ChoosePlayerBotHuntElement, the bot's own draw) is not E1 and does not hold E1 in its
//    tie; each such map weighs 3 when the bot's Champion level is within the map's band, 1 otherwise; E2 is the element
//    of the largest weight (a tie: the nearest map). So it is the lower map the bot would use most - the one a step
//    down after its deaths or its health lands on. E2 and that map are kept (quest flags mt2009_ss.e2 / .map).
//    Nothing starts before: the first set's stones and gold are not split.
// 2. The pieces - one a slot: armour, helmet, bracelet, talisman, costume, hairstyle (the required six), and the second
//    G0 package's necklace, earrings and glove (optional, swapped along). They come the way the first set's do: the
//    bot's own spare or older piece in the bag (a piece the equipment pass replaced, a drop, a bought one; for the
//    armour, helmet and bracelet at least PLAYERBOT_SS_MIN_SCORE_PCT of the worn piece's score; a talisman over +0,
//    since the +0 are the workshop's refine material; a costume with a week or more of its time), the market (the
//    craft hooks of playerbot_workshop.h: a piece of an empty slot out of a quarter of the spare purse, the worn
//    piece's vnum on the walk's list), the ItemShop (a costume / hairstyle wish when the bag has none) and the second
//    G0 package (its bracelet, talisman, necklace, earrings and glove go straight into the set). The best candidate
//    by its E2 line, then the equipment score (scored for E2), is taken; a taken piece stays the set's while the bot
//    has it.
// 3. The bonusing, in the bag (no piece comes off - none is worn): the same rules as the first set's - the Yohara bonus
//    pass's tiers, musts, element targets and budgets (playerbot_yohara_bonus.h, PickPlayerBotYoharaBonus) computed for
//    E2 (an element override for the one bot while the set is judged), the add stones first, the change stones over
//    PLAYERBOT_YOHARA_BONUS_CHANGE_RESERVE, PLAYERBOT_YOHARA_BONUS_STONES_PER_PASS a pass - and only when the first
//    set's pass found nothing to do. For ice, earth and dark the armour, helmet and bracelet roll no element line: their
//    target is the Max HP / race musts (fair tier, or PLAYERBOT_SS_PLAIN_CAP changes); the talisman carries E2 to 25.
//    The costume and hairstyle by the costume V1 rule for E2 (fire, lightning, wind to 15; the defensive lines for
//    the rest) with 70063 / 70064 the bot buys at Handlarka for them (BuyPlayerBotCostumeReagent asks here when the
//    worn pieces need none). A piece is ready at its target or out of its budget; the set is complete when the six are
//    there and ready.
// 4. Storage and protection: the pieces lie in the bag, their ids in the record and in quest flags (mt2009_ss.b0-8,
//    rebuilt at the first look after a login or a core change). IsPlayerBotSecondSetStored keeps them from the junk
//    rule, the merchant's bag room, the counters and the offline shop, the barter, the storekeeper, the gifts, the
//    G0 bot-to-bot sale, the talisman workshop and the equipment, pendant, hairstyle and world-set passes; while the set
//    is worn the first set's pieces in the bag (mt2009_ss.a0-8) are kept the same way and the worn set's pieces stay on
//    (IsPlayerBotSecondSetWornLocked - the equipment pass never takes them for an upgrade or a downgrade).
// 5. The swap: the set is wanted when the hunt element is E2 below the bot's own map (the map its first set hunted
//    last, mt2009_ss.amap) and the set is complete - HasPlayerBotElementSecondSet answers true then, so the map pick and
//    the element (playerbot_element_resist.h) allow the step down. A swap due holds the move's preparation (the bot
//    changes where it stands) and the bonus passes; it is made out of a fight on a Sung Ma map or in a village
//    (PlayerBotEquipItem swaps in place), every PLAYERBOT_SS_SWAP_LOOK_MS while due; going in, E2's resistance elixir
//    is drunk at once (the elixirs are per hunt element anyway). Going back up swaps the first set in again. A first
//    set flipped up to E2 by itself makes the set pointless: it is reset (its pieces back to the bag's ordinary life).
// 6. The log: PLAYERBOT_SECONDSET - started, piece (taken: own / market / g0), piece_ready, complete, swap_in, swap_out,
//    bonus / costume passes, blocked (why, throttled), reset, census every hour (bots in progress / complete / worn per
//    E2, swaps in the hour). The element census keeps its moves' second_set counter.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_element_resist.h, in the anonymous
// namespace.

#ifdef MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
namespace
{
	enum
	{
		PLAYERBOT_SS_BODY, PLAYERBOT_SS_HEAD, PLAYERBOT_SS_WRIST, PLAYERBOT_SS_TALISMAN, PLAYERBOT_SS_COSTUME, PLAYERBOT_SS_HAIR,
		PLAYERBOT_SS_REQUIRED,
		PLAYERBOT_SS_NECK = PLAYERBOT_SS_REQUIRED, PLAYERBOT_SS_EAR, PLAYERBOT_SS_GLOVE,
		PLAYERBOT_SS_SLOTS
	};
	const BYTE PLAYERBOT_SS_WEARS[PLAYERBOT_SS_SLOTS] = { WEAR_BODY, WEAR_HEAD, WEAR_WRIST, WEAR_PENDANT, WEAR_COSTUME_BODY,
		WEAR_COSTUME_HAIR, WEAR_NECK, WEAR_EAR, WEAR_GLOVE };
	const char* const PLAYERBOT_SS_NAMES[PLAYERBOT_SS_SLOTS] = { "body", "head", "wrist", "talisman", "costume", "hair", "neck",
		"ear", "glove" };

	const DWORD PLAYERBOT_SS_LOOK_MS = 60 * 1000;
	const DWORD PLAYERBOT_SS_SWAP_LOOK_MS = 5 * 1000;
	const DWORD PLAYERBOT_SS_BONUS_PASS_MS = 20 * 1000;
	const DWORD PLAYERBOT_SS_COSTUME_PASS_MS = 20 * 1000;
	const DWORD PLAYERBOT_SS_BLOCKED_LOG_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_SS_CENSUS_MS = 60 * 60 * 1000;
	const DWORD PLAYERBOT_SS_FORGET_MS = 30 * 60 * 1000;
	// the armour / helmet / bracelet of an element no gear line rolls: done at the fair tier or after this many changes
	const int PLAYERBOT_SS_PLAIN_CAP = 60;
	// a spare armour / helmet / bracelet / talisman is taken when it scores this per cent of the worn piece at least
	// MT2009_PLUS_BOT_G0_DUST_RULE_V2: 40 (was 50) - 67% of the day's blocks were no_piece (body, head, wrist): a
	// Champion's worn +9 outscored every own drop and spare of the bag by more than half
	const int PLAYERBOT_SS_MIN_SCORE_PCT = 40;
	// MT2009_PLUS_BOT_G0_DUST_RULE_V2: the market's walk list for an empty armour / helmet / bracelet slot - the worn
	// piece's family from this many pluses under the worn one up to +9 (it was the worn vnum alone, a +9 of one exact
	// kind that a counter seldom holds)
	const int PLAYERBOT_SS_MARKET_PLUS_BELOW = 3;
	// a market piece out of this per cent of the spare purse
	const int PLAYERBOT_SS_MARKET_PURSE_PCT = 25;

	const char* const PLAYERBOT_SS_FLAG_E2 = "mt2009_ss.e2";
	const char* const PLAYERBOT_SS_FLAG_MAP = "mt2009_ss.map";
	const char* const PLAYERBOT_SS_FLAG_AMAP = "mt2009_ss.amap";
	const char* const PLAYERBOT_SS_FLAG_WORN = "mt2009_ss.worn";

	struct TPlayerBotSecondSet
	{
		bool bLoaded;
		int iE2;	// -1 none yet
		long lMapE2;	// the lower map E2 was chosen for
		long lMapA;	// the element map the first set hunted on last (the set is worn below it only)
		DWORD adwB[PLAYERBOT_SS_SLOTS];	// the set's pieces
		DWORD adwA[PLAYERBOT_SS_SLOTS];	// while worn: the first set's pieces in the bag
		bool abReady[PLAYERBOT_SS_SLOTS];
		bool bWorn, bComplete;
		DWORD adwCosFor[2];
		int aiCosChanges[2], aiCosResets[2];
		DWORD dwNextLook, dwNextSwapLook, dwNextBonus, dwNextCostume, dwBlockedAt, dwSeen;
		DWORD dwBoughtVnum;
		std::string strBlocked;
		TPlayerBotSecondSet() : bLoaded(false), iE2(-1), lMapE2(0), lMapA(0), bWorn(false), bComplete(false), dwNextLook(0),
			dwNextSwapLook(0), dwNextBonus(0), dwNextCostume(0), dwBlockedAt(0), dwSeen(0), dwBoughtVnum(0)
		{
			for (int i = 0; i < PLAYERBOT_SS_SLOTS; ++i)
			{
				adwB[i] = adwA[i] = 0;
				abReady[i] = false;
			}
			for (int k = 0; k < 2; ++k)
			{
				adwCosFor[k] = 0;
				aiCosChanges[k] = aiCosResets[k] = 0;
			}
		}
	};
	std::map<DWORD, TPlayerBotSecondSet> s_mapPlayerBotSecondSet;
	// the change stones spent on the set's pieces, per bot and item id (this core's memory, as the first set's)
	std::map<DWORD, std::map<DWORD, int> > s_mapPlayerBotSecondSetSpent;

	struct TPlayerBotSecondSetStats
	{
		unsigned int started, pieces, ready, complete, swapIn, swapOut, bonusStones, costumeRolls, blocked, resets, loaded;
		unsigned int hourSwapIn, hourSwapOut;
		DWORD dwCensusAt;
		TPlayerBotSecondSetStats() : started(0), pieces(0), ready(0), complete(0), swapIn(0), swapOut(0), bonusStones(0),
			costumeRolls(0), blocked(0), resets(0), loaded(0), hourSwapIn(0), hourSwapOut(0), dwCensusAt(0) {}
	};
	TPlayerBotSecondSetStats s_kPlayerBotSecondSetStats;

	// While the set is judged: the hunt element of the one bot is E2 (GetPlayerBotHuntElementIndex asks it first), so
	// the bonus rules, the costume rules and the scoring see the set's element. Never across a call that moves the bot.
	struct TPlayerBotElementOverride
	{
		DWORD dwOldPid;
		int iOld;
		TPlayerBotElementOverride(LPCHARACTER ch, int e) : dwOldPid(s_dwPlayerBotElementOverridePid), iOld(s_iPlayerBotElementOverride)
		{
			s_dwPlayerBotElementOverridePid = ch ? ch->GetPlayerID() : 0;
			s_iPlayerBotElementOverride = e;
		}
		~TPlayerBotElementOverride()
		{
			s_dwPlayerBotElementOverridePid = dwOldPid;
			s_iPlayerBotElementOverride = iOld;
		}
	};

	// ------------------------------------------------------------ the record

	std::string GetPlayerBotSecondSetFlag(char kind, int slot)
	{
		char name[32];
		snprintf(name, sizeof(name), "mt2009_ss.%c%d", kind, slot);
		return name;
	}

	LPITEM FindPlayerBotSecondSetItem(LPCHARACTER ch, DWORD id)
	{
		if (!ch || id == 0)
			return NULL;
		LPITEM item = ITEM_MANAGER::instance().Find(id);
		return item && item->GetOwner() == ch ? item : NULL;
	}

	int GetPlayerBotSecondSetSlotOfWear(int wear)
	{
		for (int i = 0; i < PLAYERBOT_SS_SLOTS; ++i)
			if (PLAYERBOT_SS_WEARS[i] == wear)
				return i;
		return -1;
	}

	void SetPlayerBotSecondSetPiece(LPCHARACTER ch, TPlayerBotSecondSet& s, int slot, DWORD id)
	{
		s.adwB[slot] = id;
		s.abReady[slot] = false;
		s.bComplete = false;
		ch->SetQuestFlag(GetPlayerBotSecondSetFlag('b', slot), (int)id);
	}

	void SetPlayerBotSecondSetStoredA(LPCHARACTER ch, TPlayerBotSecondSet& s, int slot, DWORD id)
	{
		s.adwA[slot] = id;
		ch->SetQuestFlag(GetPlayerBotSecondSetFlag('a', slot), (int)id);
	}

	// The record from the quest flags, its pieces checked against what the bot owns (after a login or a core change).
	void LoadPlayerBotSecondSet(LPCHARACTER ch, TPlayerBotSecondSet& s)
	{
		s.bLoaded = true;
		const int e2 = ch->GetQuestFlag(PLAYERBOT_SS_FLAG_E2);
		s.iE2 = e2 >= 1 && e2 <= PLAYERBOT_YOHARA_ELEMENTS ? e2 - 1 : -1;
		s.lMapE2 = ch->GetQuestFlag(PLAYERBOT_SS_FLAG_MAP);
		s.lMapA = ch->GetQuestFlag(PLAYERBOT_SS_FLAG_AMAP);
		s.bWorn = ch->GetQuestFlag(PLAYERBOT_SS_FLAG_WORN) != 0;
		int pieces = 0, stored = 0, lost = 0;
		for (int i = 0; i < PLAYERBOT_SS_SLOTS; ++i)
		{
			const DWORD b = (DWORD)ch->GetQuestFlag(GetPlayerBotSecondSetFlag('b', i));
			const DWORD a = (DWORD)ch->GetQuestFlag(GetPlayerBotSecondSetFlag('a', i));
			if (b && FindPlayerBotSecondSetItem(ch, b))
			{
				s.adwB[i] = b;
				++pieces;
			}
			else if (b)
			{
				ch->SetQuestFlag(GetPlayerBotSecondSetFlag('b', i), 0);
				++lost;
			}
			if (a && s.bWorn && FindPlayerBotSecondSetItem(ch, a))
			{
				s.adwA[i] = a;
				++stored;
			}
			else if (a)
				ch->SetQuestFlag(GetPlayerBotSecondSetFlag('a', i), 0);
		}
		if (s.iE2 >= 0 || pieces > 0)
		{
			++s_kPlayerBotSecondSetStats.loaded;
			sys_log(0, "PLAYERBOT_SECONDSET: loaded pid=%u name=%s e2=%s map=%ld amap=%ld pieces=%d stored_first=%d lost=%d worn=%d",
					ch->GetPlayerID(), ch->GetName(), s.iE2 >= 0 ? PLAYERBOT_YOHARA_ELEMENT_NAMES[s.iE2] : "-", s.lMapE2, s.lMapA,
					pieces, stored, lost, s.bWorn ? 1 : 0);
		}
	}

	// The bot's record: made (and read from its flags) on the set's own look; the hooks only find it.
	TPlayerBotSecondSet* GetPlayerBotSecondSet(LPCHARACTER ch, bool create)
	{
		if (!ch)
			return NULL;
		std::map<DWORD, TPlayerBotSecondSet>::iterator it = s_mapPlayerBotSecondSet.find(ch->GetPlayerID());
		if (it != s_mapPlayerBotSecondSet.end())
			return &it->second;
		if (!create || !ch->IsItemLoaded() || !IsPlayerBotYoharaBonusMember(ch))
			return NULL;
		TPlayerBotSecondSet& s = s_mapPlayerBotSecondSet[ch->GetPlayerID()];
		LoadPlayerBotSecondSet(ch, s);
		return &s;
	}

	void NotePlayerBotSecondSetBlocked(LPCHARACTER ch, TPlayerBotSecondSet& s, const char* why, const char* detail, DWORD dwNow)
	{
		if (s.strBlocked == why && s.dwBlockedAt != 0 && dwNow - s.dwBlockedAt < PLAYERBOT_SS_BLOCKED_LOG_MS)
			return;
		s.strBlocked = why;
		s.dwBlockedAt = dwNow ? dwNow : 1;
		++s_kPlayerBotSecondSetStats.blocked;
		sys_log(0, "PLAYERBOT_SECONDSET: blocked pid=%u name=%s e2=%s why=%s%s%s", ch->GetPlayerID(), ch->GetName(),
				s.iE2 >= 0 ? PLAYERBOT_YOHARA_ELEMENT_NAMES[s.iE2] : "-", why, detail && *detail ? " " : "", detail ? detail : "");
	}

	// ------------------------------------------------------------ the hooks' answers

	bool IsPlayerBotSecondSetStored(LPCHARACTER ch, LPITEM item)
	{
#ifdef MT2009_PLUS_BOT_WIND_SET_V1
		// MT2009_PLUS_BOT_WIND_SET_V1: a 90+ bot's wind set in the bag, or its lightning set there while the wind set is on
		// (playerbot_element_wind_set.h) - every hook of this answer keeps it the same way
		if (IsPlayerBotWindSetStored(ch, item))
			return true;
#endif
		if (!ch || !item || s_mapPlayerBotSecondSet.empty() || item->IsEquipped() || item->GetID() == 0)
			return false;
		std::map<DWORD, TPlayerBotSecondSet>::const_iterator it = s_mapPlayerBotSecondSet.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotSecondSet.end())
			return false;
		const DWORD id = item->GetID();
		for (int i = 0; i < PLAYERBOT_SS_SLOTS; ++i)
			if (it->second.adwB[i] == id || (it->second.bWorn && it->second.adwA[i] == id))
				return true;
		return false;
	}

	bool IsPlayerBotSecondSetWornLocked(LPCHARACTER ch, LPITEM item)
	{
#ifdef MT2009_PLUS_BOT_WIND_SET_V1
		if (IsPlayerBotWindSetWornLocked(ch, item))	// MT2009_PLUS_BOT_WIND_SET_V1: the wind set worn
			return true;
#endif
		if (!ch || !item || s_mapPlayerBotSecondSet.empty() || !item->IsEquipped() || item->GetID() == 0)
			return false;
		std::map<DWORD, TPlayerBotSecondSet>::const_iterator it = s_mapPlayerBotSecondSet.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotSecondSet.end() || !it->second.bWorn)
			return false;
		for (int i = 0; i < PLAYERBOT_SS_SLOTS; ++i)
			if (it->second.adwB[i] == item->GetID())
				return true;
		return false;
	}

	int GetPlayerBotSecondSetElement(LPCHARACTER ch)
	{
		const TPlayerBotSecondSet* s = GetPlayerBotSecondSet(ch, false);
		return s ? s->iE2 : -1;
	}

	long GetPlayerBotSecondSetMap(LPCHARACTER ch)
	{
		const TPlayerBotSecondSet* s = GetPlayerBotSecondSet(ch, false);
		return s && s->iE2 >= 0 ? s->lMapE2 : 0;
	}

	bool IsPlayerBotSecondSetComplete(LPCHARACTER ch, BYTE element)
	{
		const TPlayerBotSecondSet* s = GetPlayerBotSecondSet(ch, false);
		return s && s->iE2 >= 0 && s->iE2 + 1 == (int)element && (s->bComplete || s->bWorn);
	}

	// The hunt element's map (where the element was chosen) - 0 none.
	long GetPlayerBotSecondSetHuntMap(LPCHARACTER ch)
	{
		std::map<DWORD, TPlayerBotHuntElement>::const_iterator h = s_mapPlayerBotHuntElement.find(ch->GetPlayerID());
		return h != s_mapPlayerBotHuntElement.end() ? h->second.lMap : 0;
	}

	// The set is to be worn now: the hunt element is E2, on a map below the first set's, and the set is complete (or on).
	bool IsPlayerBotSecondSetWanted(LPCHARACTER ch, const TPlayerBotSecondSet& s)
	{
		if (s.iE2 < 0 || (!s.bComplete && !s.bWorn) || GetPlayerBotHuntElementIndex(ch) != s.iE2)
			return false;
		const int here = GetPlayerBotSungmaSlot(GetPlayerBotSecondSetHuntMap(ch)), own = GetPlayerBotSungmaSlot(s.lMapA);
		return here >= 0 && (own < 0 || here < own);
	}

	bool IsPlayerBotSecondSetSwapPending(LPCHARACTER ch)
	{
#ifdef MT2009_PLUS_BOT_WIND_SET_V1
		if (IsPlayerBotWindSetSwapPending(ch))	// MT2009_PLUS_BOT_WIND_SET_V1
			return true;
#endif
		if (!ch || s_mapPlayerBotSecondSet.empty())
			return false;
		const TPlayerBotSecondSet* s = GetPlayerBotSecondSet(ch, false);
		if (!s || s->iE2 < 0 || (!s->bWorn && !s->bComplete))
			return false;
		return IsPlayerBotSecondSetWanted(ch, *s) != s->bWorn;
	}

	// ------------------------------------------------------------ E2 and the start

	// The element of the lower maps the bot would use most (weight 3 a map of its band, 1 another), never E1 nor a map
	// holding E1 in its tie; a tie to the nearest map.
	int ChoosePlayerBotSecondSetElement(LPCHARACTER ch, int e1, long fromMap, long* mapOut, std::string* why)
	{
		const int fromSlot = GetPlayerBotSungmaSlot(fromMap);
		if (fromSlot <= 0)
		{
			*why = "no_lower_map";
			return -1;
		}
		const int champion = GetPlayerBotChampionLevel(ch);
		int weight[PLAYERBOT_YOHARA_ELEMENTS] = { 0 };
		long nearest[PLAYERBOT_YOHARA_ELEMENTS] = { 0 };
		for (int i = fromSlot - 1; i >= 0; --i)
		{
			const TPlayerBotSungmaMap& m = PLAYERBOT_SUNGMA_MAPS[i];
			if (!IsPlayerBotSungmaMapOn(m.lMap) || IsPlayerBotElementInMapTie(m.lMap, e1))
				continue;
			const int e = ChoosePlayerBotHuntElement(m.lMap, ch->GetPlayerID());
			if (e < 0 || e == e1)
				continue;
			weight[e] += champion >= (int)m.bChampionMin && champion <= (int)m.bChampionMax ? 3 : 1;
			if (nearest[e] == 0)
				nearest[e] = m.lMap;
		}
		int best = -1;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			if (weight[e] > 0 && (best < 0 || weight[e] > weight[best] ||
					(weight[e] == weight[best] && GetPlayerBotSungmaSlot(nearest[e]) > GetPlayerBotSungmaSlot(nearest[best]))))
				best = e;
		if (best < 0)
		{
			*why = "no_lower_element";
			return -1;
		}
		std::string out;
		char buf[48];
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			if (weight[e] > 0)
			{
				snprintf(buf, sizeof(buf), "%s%s:%d", out.empty() ? "" : ",", PLAYERBOT_YOHARA_ELEMENT_NAMES[e], weight[e]);
				out += buf;
			}
		*why = out;
		*mapOut = nearest[best];
		return best;
	}

	// The first set is done for E1: the element target pieces (the move's rule) and the worn costume pieces finished.
	bool IsPlayerBotFirstSetDone(LPCHARACTER ch, TPlayerBotAIState& state, int e1, const char** why)
	{
		std::map<DWORD, TPlayerBotHuntElement>::const_iterator h = s_mapPlayerBotHuntElement.find(ch->GetPlayerID());
		if (h != s_mapPlayerBotHuntElement.end() && h->second.bPrepOpen)
		{
			*why = "moving";
			return false;
		}
		bool noStones = false;
		if (!IsPlayerBotElementGearReady(ch, e1, &noStones))
		{
			*why = "first_set_gear";
			return false;
		}
#ifdef MT2009_PLUS_BOT_COSTUME_RESIST_V1
		static const BYTE s_abCostume[2] = { WEAR_COSTUME_BODY, WEAR_COSTUME_HAIR };
		for (int i = 0; i < 2; ++i)
		{
			LPITEM c = ch->GetWear(s_abCostume[i]);
			if (c && GetPlayerBotCostumeBonusNeed(ch, state, c) != 0)
			{
				*why = "first_set_costume";
				return false;
			}
		}
#else
		(void)state;
#endif
		return true;
	}

	// ------------------------------------------------------------ the pieces

	// An element talisman +0: the talisman workshop's refine material, never the set's.
	bool IsPlayerBotSecondSetPlainTalisman(LPITEM item)
	{
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_ELEMENTS_V1)
		return IsPlayerBotTalismanItem(item) && GetPlayerBotTalismanPlus(item) <= 0;
#else
		(void)item;
		return false;
#endif
	}

	bool IsPlayerBotSecondSetCostumeSlot(int slot)
	{
		return slot == PLAYERBOT_SS_COSTUME || slot == PLAYERBOT_SS_HAIR;
	}

	// A piece of the bag that may become the set's piece of the slot (not judged against the others yet).
	bool IsPlayerBotSecondSetCandidate(LPCHARACTER ch, const TPlayerBotSecondSet& s, int slot, LPITEM item)
	{
		if (!item || item->IsEquipped() || item->isLocked() || item->IsExchanging() || item->GetID() == 0 ||
				item->GetWindow() != INVENTORY || !item->CanUsedBy(ch) || item->GetLevelLimit() > (int)ch->GetLevel())
			return false;
		for (int i = 0; i < PLAYERBOT_SS_SLOTS; ++i)
			if (s.adwB[i] == item->GetID() || s.adwA[i] == item->GetID())
				return false;
		if (IsPlayerBotSecondSetCostumeSlot(slot))
		{
			if (item->GetType() != ITEM_COSTUME ||
					item->GetSubType() != (slot == PLAYERBOT_SS_COSTUME ? COSTUME_BODY : COSTUME_HAIR) ||
					item->GetAttributeSetIndex() < 0 || GetPlayerBotCostumeSecondsLeft(item) < PLAYERBOT_COSTUME_BONUS_MIN_SECONDS_LEFT)
				return false;
			return true;
		}
		if (item->GetType() != ITEM_ARMOR || item->FindEquipCell(ch) != (int)PLAYERBOT_SS_WEARS[slot] ||
				Mt2009IsElementStone(item->GetVnum()) || item->GetAttributeSetIndex() < 0)
			return false;
		// the workshop's +0 talismans are its refine material
		if (slot == PLAYERBOT_SS_TALISMAN && IsPlayerBotSecondSetPlainTalisman(item))
			return false;
		if (slot >= PLAYERBOT_SS_REQUIRED)
			return false;	// the optional slots are the second G0 package's
		LPITEM worn = ch->GetWear(PLAYERBOT_SS_WEARS[slot]);
		if (worn && !IsPlayerBotSecondSetWornLocked(ch, worn) &&
				GetPlayerBotEquipmentScore(item, ch) * 100 < GetPlayerBotEquipmentScore(worn, ch) * PLAYERBOT_SS_MIN_SCORE_PCT)
			return false;
		return true;
	}

	// The best candidate of the slot in the bag: its E2 line first, then the score (E2's override set by the caller).
	LPITEM FindPlayerBotSecondSetCandidate(LPCHARACTER ch, const TPlayerBotSecondSet& s, int slot)
	{
		const BYTE point = GetPlayerBotElementResistPoint(s.iE2);
		LPITEM best = NULL;
		long bestLine = 0;
		long long bestScore = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || !IsPlayerBotSecondSetCandidate(ch, s, slot, item))
				continue;
			const long line = point ? GetPlayerBotYoharaPieceLine(item, point) : 0;
			const long long score = IsPlayerBotSecondSetCostumeSlot(slot) ? (long long)CountPlayerBotGoodCostumeLines(ch, item)
					: GetPlayerBotEquipmentScore(item, ch);
			if (!best || line > bestLine || (line == bestLine && score > bestScore))
			{
				best = item;
				bestLine = line;
				bestScore = score;
			}
		}
		return best;
	}

	int GetPlayerBotSecondSetBonusSlotIndex(int slot)
	{
		for (int s = 0; s < PLAYERBOT_YOHARA_BONUS_SLOT_COUNT; ++s)
			if (PLAYERBOT_YOHARA_BONUS_SLOTS[s].bWearCell == PLAYERBOT_SS_WEARS[slot])
				return s;
		return -1;
	}

	// The costume / hairstyle's next reagent for E2 (0 finished) - the costume V1 rule (GetPlayerBotYoharaCostumeBonusNeed)
	// with the set's own counters. *done: why it is finished. E2's override set by the caller.
	DWORD GetPlayerBotSecondSetCostumeNeedOf(LPCHARACTER ch, TPlayerBotSecondSet& s, int k, LPITEM item, const char** done)
	{
		*done = "";
		if (!item || item->GetAttributeSetIndex() == -1)
		{
			*done = "no_set";
			return 0;
		}
		if (s.adwCosFor[k] != item->GetID())
		{
			s.adwCosFor[k] = item->GetID();
			s.aiCosChanges[k] = s.aiCosResets[k] = 0;
		}
		const int count = item->GetAttributeCount();
		const bool hair = k == 1;
#ifdef MT2009_PLUS_BOT_COSTUME_RESIST_V1
		const int hunt = GetPlayerBotCostumeHuntState(ch, item);
		if (hunt > 0)
		{
			*done = "top";
			return 0;
		}
		if (hunt < 0)
		{
			if (IsPlayerBotCostumeElementTopKept(ch, item))
			{
				*done = "kept";
				return 0;
			}
			const int good = CountPlayerBotGoodCostumeLines(ch, item);
			if (hair ? (count >= 1 && good >= 1) : (count >= 2 && good >= 2))
			{
				*done = "good";
				return 0;
			}
			if (!hair && HasPlayerBotCostumeGoodMaxHp(item) && s.aiCosChanges[k] >= PLAYERBOT_COSTUME_YOHARA_HP_ALONE_AFTER)
			{
				*done = "hp";
				return 0;
			}
		}
		if (s.aiCosChanges[k] >= (hunt == 0 ? PLAYERBOT_COSTUME_YOHARA_HUNT_CHANGES : PLAYERBOT_COSTUME_MAX_CHANGES))
		{
			*done = "budget";
			return 0;
		}
		const int wanted = hunt < 0 && hair ? 1 : PLAYERBOT_COSTUME_YOHARA_LINES;
		if (count == 0)
			return PLAYERBOT_COSTUME_RESET_VNUM;
		if (count < wanted)
			return s.aiCosResets[k] < PLAYERBOT_COSTUME_YOHARA_MAX_RESETS ? PLAYERBOT_COSTUME_RESET_VNUM : PLAYERBOT_COSTUME_CHANGE_VNUM;
		return PLAYERBOT_COSTUME_CHANGE_VNUM;
#else
		(void)ch;
		(void)hair;
		(void)count;
		*done = "off";
		return 0;
#endif
	}

	// A gear piece of the set is ready (E2's override set by the caller): at its element target or out of its element
	// budget; an element no line of the slot rolls - the fair tier or PLAYERBOT_SS_PLAIN_CAP changes.
	bool IsPlayerBotSecondSetGearReady(LPCHARACTER ch, int slot, LPITEM item)
	{
		const int index = GetPlayerBotSecondSetBonusSlotIndex(slot);
		if (index < 0 || !CanPlayerBotTakeBonusStone(item))
			return true;
		const TPlayerBotYoharaBonusPiece p = { item, index };
		const playerbot_yohara_bonus_rules::TPiece built =
				BuildPlayerBotYoharaBonusPiece(ch, p, s_mapPlayerBotSecondSetSpent[ch->GetPlayerID()]);
		if (built.lines <= 0)
			return false;
		if (built.elemRank >= 0)
			return !built.elemShort || built.spent >= built.elemCap;
		return built.tier >= playerbot_yohara_bonus_rules::TIER_FAIR || built.spent >= PLAYERBOT_SS_PLAIN_CAP;
	}

	bool IsPlayerBotSecondSetPieceReady(LPCHARACTER ch, TPlayerBotSecondSet& s, int slot, LPITEM item)
	{
		if (slot >= PLAYERBOT_SS_REQUIRED)
			return true;
		if (IsPlayerBotSecondSetCostumeSlot(slot))
		{
			const char* done = "";
			return GetPlayerBotSecondSetCostumeNeedOf(ch, s, slot == PLAYERBOT_SS_COSTUME ? 0 : 1, item, &done) == 0;
		}
		return IsPlayerBotSecondSetGearReady(ch, slot, item);
	}

	void TakePlayerBotSecondSetPiece(LPCHARACTER ch, TPlayerBotSecondSet& s, int slot, LPITEM item, const char* source)
	{
		const DWORD old = s.adwB[slot];
		SetPlayerBotSecondSetPiece(ch, s, slot, item->GetID());
		++s_kPlayerBotSecondSetStats.pieces;
		const BYTE point = GetPlayerBotElementResistPoint(s.iE2);
		sys_log(0, "PLAYERBOT_SECONDSET: piece pid=%u name=%s e2=%s slot=%s vnum=%u+%d id=%u source=%s e2_line=%ld lines=%d replaced=%u",
				ch->GetPlayerID(), ch->GetName(), PLAYERBOT_YOHARA_ELEMENT_NAMES[s.iE2], PLAYERBOT_SS_NAMES[slot], item->GetVnum(),
				(int)item->GetRefineLevel(), item->GetID(), source, point ? GetPlayerBotYoharaPieceLine(item, point) : 0L,
				item->GetAttributeCount(), old);
	}

	// Forgets the set: its pieces go back to the bag's ordinary life (a bot whose first set is E2 now).
	void ResetPlayerBotSecondSet(LPCHARACTER ch, TPlayerBotSecondSet& s, const char* why)
	{
		sys_log(0, "PLAYERBOT_SECONDSET: reset pid=%u name=%s e2=%s why=%s", ch->GetPlayerID(), ch->GetName(),
				s.iE2 >= 0 ? PLAYERBOT_YOHARA_ELEMENT_NAMES[s.iE2] : "-", why);
		++s_kPlayerBotSecondSetStats.resets;
		for (int i = 0; i < PLAYERBOT_SS_SLOTS; ++i)
		{
			if (s.adwB[i])
				SetPlayerBotSecondSetPiece(ch, s, i, 0);
			if (s.adwA[i])
				SetPlayerBotSecondSetStoredA(ch, s, i, 0);
		}
		s.iE2 = -1;
		s.lMapE2 = 0;
		s.bComplete = false;
		s.bWorn = false;
		ch->SetQuestFlag(PLAYERBOT_SS_FLAG_E2, 0);
		ch->SetQuestFlag(PLAYERBOT_SS_FLAG_MAP, 0);
		ch->SetQuestFlag(PLAYERBOT_SS_FLAG_WORN, 0);
		s_mapPlayerBotSecondSetSpent.erase(ch->GetPlayerID());
	}

	// ------------------------------------------------------------ the bag's bonus passes

	int RunPlayerBotSecondSetBonus(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		(void)state;
		TPlayerBotSecondSet* s = GetPlayerBotSecondSet(ch, false);
		if (!s || s->iE2 < 0 || s->bWorn || (int)(dwNow - s->dwNextBonus) < 0)
			return 0;
		s->dwNextBonus = dwNow + PLAYERBOT_SS_BONUS_PASS_MS;
		TPlayerBotYoharaBonusBag bag;
		ReadPlayerBotYoharaBonusBag(ch, bag);
		if (bag.addCell < 0 && bag.changeCell < 0 && bag.marbleCell < 0)
			return 0;
		TPlayerBotElementOverride guard(ch, s->iE2);
		std::vector<TPlayerBotYoharaBonusPiece> pieces;
		for (int slot = PLAYERBOT_SS_BODY; slot <= PLAYERBOT_SS_TALISMAN; ++slot)
		{
			LPITEM item = FindPlayerBotSecondSetItem(ch, s->adwB[slot]);
			const int index = GetPlayerBotSecondSetBonusSlotIndex(slot);
			if (!item || item->IsEquipped() || index < 0 || !CanPlayerBotTakeBonusStone(item))
				continue;
			const TPlayerBotYoharaBonusPiece piece = { item, index };
			pieces.push_back(piece);
		}
		if (pieces.empty())
			return 0;
		std::map<DWORD, int>& spent = s_mapPlayerBotSecondSetSpent[ch->GetPlayerID()];
		std::vector<playerbot_yohara_bonus_rules::TPiece> built;
		playerbot_yohara_bonus_rules::TChoice choice = PickPlayerBotYoharaBonus(ch, pieces, spent, bag, built);
		if (choice.piece < 0)
		{
			bool short_ = false;
			for (size_t i = 0; i < built.size(); ++i)
				if (built[i].elemShort && built[i].spent < built[i].elemCap)
					short_ = true;
			if (short_)
			{
				char detail[64];
				snprintf(detail, sizeof(detail), "stock_add=%d stock_change=%d", bag.addUnits, bag.changeUnits);
				NotePlayerBotSecondSetBlocked(ch, *s, "no_stones", detail, dwNow);
			}
			return 0;
		}
		LPITEM item = pieces[choice.piece].item;
		const int slotIndex = pieces[choice.piece].slotIndex;
		const int linesBefore = item->GetAttributeCount();
		const int tierBefore = built[choice.piece].tier;
		const bool elementPhase = choice.element;
		const int cap = choice.cap;
		int used[4] = { 0, 0, 0, 0 };
		int stones = 0;
		while (stones < PLAYERBOT_YOHARA_BONUS_STONES_PER_PASS && choice.piece >= 0 && pieces[choice.piece].item == item &&
				choice.step != playerbot_yohara_bonus_rules::STEP_NONE)
		{
			const int cell = choice.step == playerbot_yohara_bonus_rules::STEP_ADD ? bag.addCell
					: (choice.step == playerbot_yohara_bonus_rules::STEP_MARBLE ? bag.marbleCell : bag.changeCell);
			if (cell < 0)
				break;
			const int count = item->GetAttributeCount();
			if (choice.step == playerbot_yohara_bonus_rules::STEP_CHANGE)
			{
				item->ChangeAttribute();
				++spent[item->GetID()];
			}
			else if (count < ITEM_ATTRIBUTE_MAX_NUM && number(1, 100) <= aiItemAttributeAddPercent[count])
				item->AddAttribute();
			ConsumePlayerBotBonusStoneAt(ch, cell);
			LogManager::instance().ItemLog(ch, item,
					choice.step == playerbot_yohara_bonus_rules::STEP_ADD ? "PLAYERBOT_SECONDSET_ADD"
						: (choice.step == playerbot_yohara_bonus_rules::STEP_MARBLE ? "PLAYERBOT_SECONDSET_MARBLE"
							: "PLAYERBOT_SECONDSET_CHANGE"), item->GetName());
			++used[choice.step];
			++stones;
			ReadPlayerBotYoharaBonusBag(ch, bag);
			choice = PickPlayerBotYoharaBonus(ch, pieces, spent, bag, built);
		}
		item->UpdatePacket();
		int tierAfter = playerbot_yohara_bonus_rules::TIER_NONE;
		for (size_t i = 0; i < pieces.size() && i < built.size(); ++i)
			if (pieces[i].item == item)
				tierAfter = built[i].tier;
		const BYTE point = GetPlayerBotElementResistPoint(s->iE2);
		s_kPlayerBotSecondSetStats.bonusStones += stones;
		sys_log(0, "PLAYERBOT_SECONDSET: bonus pid=%u name=%s e2=%s slot=%s vnum=%u+%d add=%d marble=%d change=%d lines=%d->%d "
				"tier=%c->%c e2_line=%ld spent=%d cap=%d%s stock_add=%d stock_change=%d",
				ch->GetPlayerID(), ch->GetName(), PLAYERBOT_YOHARA_ELEMENT_NAMES[s->iE2], PLAYERBOT_YOHARA_BONUS_SLOTS[slotIndex].szName,
				item->GetVnum(), (int)item->GetRefineLevel(), used[playerbot_yohara_bonus_rules::STEP_ADD],
				used[playerbot_yohara_bonus_rules::STEP_MARBLE], used[playerbot_yohara_bonus_rules::STEP_CHANGE], linesBefore,
				item->GetAttributeCount(), PlayerBotYoharaBonusTierChar(tierBefore), PlayerBotYoharaBonusTierChar(tierAfter),
				point ? GetPlayerBotYoharaPieceLine(item, point) : 0L, spent.count(item->GetID()) ? spent[item->GetID()] : 0, cap,
				elementPhase ? " element" : "", bag.addUnits, bag.changeUnits);
		return stones;
	}

	DWORD GetPlayerBotSecondSetCostumeReagentNeed(LPCHARACTER ch)
	{
		TPlayerBotSecondSet* s = GetPlayerBotSecondSet(ch, false);
		if (!s || s->iE2 < 0 || s->bWorn)
			return 0;
		TPlayerBotElementOverride guard(ch, s->iE2);
		for (int k = 0; k < 2; ++k)
		{
			LPITEM item = FindPlayerBotSecondSetItem(ch, s->adwB[PLAYERBOT_SS_COSTUME + k]);
			const char* done = "";
			if (item && !item->IsEquipped())
			{
				const DWORD need = GetPlayerBotSecondSetCostumeNeedOf(ch, *s, k, item, &done);
				if (need)
					return need;
			}
		}
		return 0;
	}

	// A few rolls on the set's costume or hairstyle in the bag, the engine's own checks of the reagents' handler (a
	// reset leaves one to three lines, a change the same count - else the old lines go back and the reagent stays).
	bool RunPlayerBotSecondSetCostumeRoll(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		(void)state;
		TPlayerBotSecondSet* s = GetPlayerBotSecondSet(ch, false);
		if (!s || s->iE2 < 0 || s->bWorn || (int)(dwNow - s->dwNextCostume) < 0)
			return false;
		s->dwNextCostume = dwNow + PLAYERBOT_SS_COSTUME_PASS_MS;
		TPlayerBotElementOverride guard(ch, s->iE2);
		for (int k = 0; k < 2; ++k)
		{
			LPITEM item = FindPlayerBotSecondSetItem(ch, s->adwB[PLAYERBOT_SS_COSTUME + k]);
			if (!item || item->IsEquipped() || item->isLocked() || item->IsExchanging())
				continue;
			const char* done = "";
			DWORD need = GetPlayerBotSecondSetCostumeNeedOf(ch, *s, k, item, &done);
			if (!need)
				continue;
			int cell = FindPlayerBotCostumeReagentCell(ch, need);
			if (cell < 0)
			{
				char detail[48];
				snprintf(detail, sizeof(detail), "piece=%s reagent=%u", k == 0 ? "costume" : "hair", need);
				NotePlayerBotSecondSetBlocked(ch, *s, "no_reagent", detail, dwNow);
				return false;
			}
			const int linesBefore = item->GetAttributeCount();
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
					sys_err("PLAYERBOT_SECONDSET: costume %s left %d line(s) (had %d) pid=%u vnum=%u - restored",
							reset ? "reset" : "change", countAfter, countBefore, ch->GetPlayerID(), item->GetVnum());
					break;
				}
				ConsumePlayerBotBonusStoneAt(ch, cell);
				if (reset)
				{
					++resets;
					++s->aiCosResets[k];
				}
				else
				{
					++changes;
					++s->aiCosChanges[k];
				}
				++s_kPlayerBotSecondSetStats.costumeRolls;
				LogManager::instance().ItemLog(ch, item, reset ? "PLAYERBOT_SECONDSET_COSTUME_RESET" : "PLAYERBOT_SECONDSET_COSTUME_CHANGE",
						item->GetName());
				need = GetPlayerBotSecondSetCostumeNeedOf(ch, *s, k, item, &done);
				cell = need ? FindPlayerBotCostumeReagentCell(ch, need) : -1;
			}
			item->UpdatePacket();
			const BYTE point = GetPlayerBotElementResistPoint(s->iE2);
			sys_log(0, "PLAYERBOT_SECONDSET: costume pid=%u name=%s e2=%s piece=%s vnum=%u resets=%d changes=%d lines=%d->%d good=%d "
					"e2_line=%ld total_changes=%d total_resets=%d%s%s",
					ch->GetPlayerID(), ch->GetName(), PLAYERBOT_YOHARA_ELEMENT_NAMES[s->iE2], k == 0 ? "costume" : "hair",
					item->GetVnum(), resets, changes, linesBefore, item->GetAttributeCount(), CountPlayerBotGoodCostumeLines(ch, item),
					point ? GetPlayerBotYoharaPieceLine(item, point) : 0L, s->aiCosChanges[k], s->aiCosResets[k],
					need ? "" : " finished=", need ? "" : done);
			return resets + changes > 0;
		}
		return false;
	}

	// ------------------------------------------------------------ the market, the ItemShop, the G0 package

	// The set's slot a market piece would fill (-1 none): an empty armour / helmet / bracelet / talisman slot.
	int GetPlayerBotSecondSetOfferSlot(LPCHARACTER ch, const TPlayerBotSecondSet& s, LPITEM offer)
	{
		if (offer->GetType() != ITEM_ARMOR || offer->GetLevelLimit() > (int)ch->GetLevel() || !offer->CanUsedBy(ch) ||
				offer->GetAttributeSetIndex() < 0 || Mt2009IsElementStone(offer->GetVnum()))
			return -1;
		const int slot = GetPlayerBotSecondSetSlotOfWear(offer->FindEquipCell(ch));
		if (slot < 0 || slot > PLAYERBOT_SS_TALISMAN || s.adwB[slot] != 0)
			return -1;
		if (slot == PLAYERBOT_SS_TALISMAN && IsPlayerBotSecondSetPlainTalisman(offer))
			return -1;
		LPITEM worn = ch->GetWear(PLAYERBOT_SS_WEARS[slot]);
		if (worn && GetPlayerBotEquipmentScore(offer, ch) * 100 < GetPlayerBotEquipmentScore(worn, ch) * PLAYERBOT_SS_MIN_SCORE_PCT)
			return -1;
		return slot;
	}

	bool WantsPlayerBotSecondSetOffer(LPCHARACTER ch, LPITEM offer)
	{
#ifdef MT2009_PLUS_BOT_WIND_SET_V1
		if (WantsPlayerBotWindSetOffer(ch, offer))	// MT2009_PLUS_BOT_WIND_SET_V1: a piece of the wind set
			return true;
#endif
		if (!ch || !offer || s_mapPlayerBotSecondSet.empty() || offer->GetType() != ITEM_ARMOR)
			return false;
		const TPlayerBotSecondSet* s = GetPlayerBotSecondSet(ch, false);
		if (!s || s->iE2 < 0 || s->bWorn)
			return false;
		return GetPlayerBotSecondSetOfferSlot(ch, *s, offer) >= 0;
	}

	bool CanPlayerBotPayForSecondSetOffer(LPCHARACTER ch, LPITEM offer, long long price)
	{
#ifdef MT2009_PLUS_BOT_WIND_SET_V1
		if (WantsPlayerBotWindSetOffer(ch, offer))	// MT2009_PLUS_BOT_WIND_SET_V1
			return CanPlayerBotPayForWindSetOffer(ch, offer, price);
#endif
		if (!ch || !offer || price <= 0)
			return false;
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		return price <= spare * PLAYERBOT_SS_MARKET_PURSE_PCT / 100;
	}

	void CollectPlayerBotSecondSetMissing(LPCHARACTER ch, std::map<DWORD, int>& missing)
	{
#ifdef MT2009_PLUS_BOT_WIND_SET_V1
		CollectPlayerBotWindSetMissing(ch, missing);	// MT2009_PLUS_BOT_WIND_SET_V1
#endif
		const TPlayerBotSecondSet* s = s_mapPlayerBotSecondSet.empty() ? NULL : GetPlayerBotSecondSet(ch, false);
		if (!s || s->iE2 < 0 || s->bWorn)
			return;
		for (int slot = PLAYERBOT_SS_BODY; slot <= PLAYERBOT_SS_TALISMAN; ++slot)
		{
			LPITEM worn = s->adwB[slot] ? NULL : ch->GetWear(PLAYERBOT_SS_WEARS[slot]);
			if (worn && missing[worn->GetVnum()] < 1)
				missing[worn->GetVnum()] = 1;
#ifdef MT2009_PLUS_BOT_G0_DUST_RULE_V2
			// MT2009_PLUS_BOT_G0_DUST_RULE_V2: and its family's lower pluses (an armour, helmet or bracelet of the
			// ordinary +0..+9 vnums: the plus is the vnum's last digit) - any of them the offer's own rule takes
			// (GetPlayerBotSecondSetOfferSlot: PLAYERBOT_SS_MIN_SCORE_PCT of the worn piece's score), and the set's
			// bonusing does the rest. No element line is bought in: ice, earth and dark roll on no armour, helmet or
			// bracelet (item_attr), the set's own pass rolls E2 where it may.
			if (!worn || slot == PLAYERBOT_SS_TALISMAN || worn->GetType() != ITEM_ARMOR)
				continue;
			const int plus = (int)(worn->GetVnum() % 10);
			if (plus != (int)worn->GetRefineLevel())
				continue;
			const DWORD base = worn->GetVnum() - (DWORD)plus;
			for (int p = std::max(0, plus - PLAYERBOT_SS_MARKET_PLUS_BELOW); p <= 9; ++p)
			{
				const DWORD vnum = base + (DWORD)p;
				const TItemTable* proto = vnum == worn->GetVnum() ? NULL : ITEM_MANAGER::instance().GetTable(vnum);
				if (proto && proto->bType == ITEM_ARMOR && proto->bSubType == worn->GetSubType() && missing[vnum] < 1)
					missing[vnum] = 1;
			}
#endif
		}
	}

#ifdef MT2009_PLUS_BOT_G0_DUST_RULE_V2
	// MT2009_PLUS_BOT_G0_DUST_RULE_V2: the set's required pieces held now (0 for a bot without a started set).
	int CountPlayerBotSecondSetPieces(LPCHARACTER ch)
	{
		const TPlayerBotSecondSet* s = s_mapPlayerBotSecondSet.empty() ? NULL : GetPlayerBotSecondSet(ch, false);
		if (!s || s->iE2 < 0)
			return 0;
		int held = 0;
		for (int slot = 0; slot < PLAYERBOT_SS_REQUIRED; ++slot)
			if (s->adwB[slot] != 0)
				++held;
		return held;
	}
#endif

	void NotePlayerBotSecondSetBought(LPCHARACTER ch, DWORD vnum, long long price)
	{
#ifdef MT2009_PLUS_BOT_WIND_SET_V1
		NotePlayerBotWindSetBought(ch, vnum, price);	// MT2009_PLUS_BOT_WIND_SET_V1
#endif
		TPlayerBotSecondSet* s = s_mapPlayerBotSecondSet.empty() ? NULL : GetPlayerBotSecondSet(ch, false);
		if (!s || s->iE2 < 0 || s->bWorn)
			return;
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		if (!proto || proto->bType != ITEM_ARMOR)
			return;
		s->dwBoughtVnum = vnum;
		s->dwNextLook = 0;	// taken at the next look
		sys_log(0, "PLAYERBOT_SECONDSET: bought pid=%u name=%s e2=%s vnum=%u price=%lld", ch->GetPlayerID(), ch->GetName(),
				PLAYERBOT_YOHARA_ELEMENT_NAMES[s->iE2], vnum, price);
	}

	// A costume / hairstyle of the ItemShop for the set's empty costume slot, when the bag holds no candidate.
	DWORD PickPlayerBotSecondSetLook(LPCHARACTER ch, int* pLook)
	{
#if defined(PLAYERBOT_ENGINE_MT2009)
		TPlayerBotSecondSet* s = s_mapPlayerBotSecondSet.empty() ? NULL : GetPlayerBotSecondSet(ch, false);
		if (!s || s->iE2 < 0 || s->bWorn || !pLook)
#ifdef MT2009_PLUS_BOT_WIND_SET_V1
			return PickPlayerBotWindSetLook(ch, pLook);	// MT2009_PLUS_BOT_WIND_SET_V1: the wind set's costume / hairstyle
#else
			return 0;
#endif
		for (int k = 0; k < 2; ++k)
		{
			const int slot = PLAYERBOT_SS_COSTUME + k;
			if (s->adwB[slot] != 0 || FindPlayerBotSecondSetCandidate(ch, *s, slot))
				continue;
			const int look = k == 0 ? PLAYERBOT_ISHOP_LOOK_BODY : PLAYERBOT_ISHOP_LOOK_HAIR;
			if (IsPlayerBotLookMonthBlocked(ch, look))	// MT2009_PLUS_BOT_LOOK_MONTHLY_V1: once a month a kind
				continue;
			const std::vector<DWORD>& catalogue = GetPlayerBotLookCatalogue(look);
			std::vector<DWORD> mine, lasting;
			for (size_t i = 0; i < catalogue.size(); ++i)
				if (IsPlayerBotOwnLook(ch, ITEM_MANAGER::instance().GetTable(catalogue[i]), look))
					mine.push_back(catalogue[i]);
			for (size_t i = 0; i < mine.size(); ++i)
			{
				const long seconds = GetPlayerBotLookSeconds(ITEM_MANAGER::instance().GetTable(mine[i]));
				if (seconds == 0 || seconds >= PLAYERBOT_ISHOP_LOOK_MIN_SECONDS)
					lasting.push_back(mine[i]);
			}
			if (lasting.empty())
				continue;
			*pLook = look;
			return lasting[number(0, (int)lasting.size() - 1)];
		}
#else
		(void)ch;
		(void)pLook;
#endif
		return 0;
	}

	void NotePlayerBotSecondSetG0Piece(LPCHARACTER ch, LPITEM item)
	{
		TPlayerBotSecondSet* s = GetPlayerBotSecondSet(ch, true);
		if (!s || !item || s->iE2 < 0 || s->bWorn)
			return;
		const int slot = GetPlayerBotSecondSetSlotOfWear(item->FindEquipCell(ch));
		if (slot < 0 || IsPlayerBotSecondSetCostumeSlot(slot) || slot == PLAYERBOT_SS_BODY || slot == PLAYERBOT_SS_HEAD)
			return;
		TakePlayerBotSecondSetPiece(ch, *s, slot, item, "g0");
	}

	// ------------------------------------------------------------ the swap

	// The set in (in) or the first set back (!in), each piece swapped in place. Returns the pieces moved.
	int SwapPlayerBotSecondSet(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotSecondSet& s, bool in, DWORD dwNow)
	{
		int moved = 0, failed = 0;
		std::string desc;
		char buf[48];
		for (int slot = 0; slot < PLAYERBOT_SS_SLOTS; ++slot)
		{
			const BYTE wear = PLAYERBOT_SS_WEARS[slot];
			LPITEM piece = FindPlayerBotSecondSetItem(ch, s.adwB[slot]);
			if (in)
			{
				if (!piece || piece->IsEquipped())
					continue;
				LPITEM worn = ch->GetWear(wear);
				if (worn && IS_SET(worn->GetFlag(), ITEM_FLAG_IRREMOVABLE))
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
				SetPlayerBotSecondSetStoredA(ch, s, slot, wornId);
				++moved;
				snprintf(buf, sizeof(buf), "%s%s:%u", desc.empty() ? "" : " ", PLAYERBOT_SS_NAMES[slot], piece->GetVnum());
				desc += buf;
			}
			else
			{
				LPITEM back = FindPlayerBotSecondSetItem(ch, s.adwA[slot]);
				if (back && !back->IsEquipped())
				{
					if (PlayerBotEquipItem(ch, back) && back->IsEquipped())
					{
						++moved;
						snprintf(buf, sizeof(buf), "%s%s:%u", desc.empty() ? "" : " ", PLAYERBOT_SS_NAMES[slot], back->GetVnum());
						desc += buf;
					}
					else
						++failed;
				}
				else if (piece && piece->IsEquipped())
				{
					// nothing of the first set to put back here (sold before the set, burnt): the slot is the
					// equipment pass's again
					if (ch->GetEmptyInventory(piece->GetSize()) >= 0 && ch->UnequipItem(piece) && !piece->IsEquipped())
						++moved;
					else
						++failed;
				}
				if (s.adwA[slot])
					SetPlayerBotSecondSetStoredA(ch, s, slot, 0);
			}
		}
		s.bWorn = in;
		ch->SetQuestFlag(PLAYERBOT_SS_FLAG_WORN, in ? 1 : 0);
		const char* elixir = "-";
		if (in)
		{
			++s_kPlayerBotSecondSetStats.swapIn;
			++s_kPlayerBotSecondSetStats.hourSwapIn;
			elixir = DrinkPlayerBotHuntElixir(ch, s.iE2);
		}
		else
		{
			++s_kPlayerBotSecondSetStats.swapOut;
			++s_kPlayerBotSecondSetStats.hourSwapOut;
		}
		state.bEquipPending = true;
		state.dwNextEquipmentCheckTime = 0;
		const int e = GetPlayerBotHuntElementIndex(ch);
		sys_log(0, "PLAYERBOT_SECONDSET: %s pid=%u name=%s e2=%s hunt=%s map=%ld hunt_map=%ld own_map=%ld pieces=%d failed=%d elixir=%s "
				"resist=%d worn=[%s]",
				in ? "swap_in" : "swap_out", ch->GetPlayerID(), ch->GetName(), PLAYERBOT_YOHARA_ELEMENT_NAMES[s.iE2],
				e >= 0 ? PLAYERBOT_YOHARA_ELEMENT_NAMES[e] : "-", ch->GetMapIndex(), GetPlayerBotSecondSetHuntMap(ch), s.lMapA, moved,
				failed, elixir, e >= 0 ? (int)ch->GetPoint(PLAYERBOT_YOHARA_RESIST_POINTS[e]) : 0, desc.c_str());
		(void)dwNow;
		return moved;
	}

	// ------------------------------------------------------------ the census

	void TickPlayerBotSecondSetCensus(DWORD dwNow)
	{
		TPlayerBotSecondSetStats& st = s_kPlayerBotSecondSetStats;
		if (st.dwCensusAt == 0)
		{
			st.dwCensusAt = dwNow + PLAYERBOT_SS_CENSUS_MS;
			return;
		}
		if ((int)(dwNow - st.dwCensusAt) < 0)
			return;
		st.dwCensusAt = dwNow + PLAYERBOT_SS_CENSUS_MS;
		int progress[PLAYERBOT_YOHARA_ELEMENTS] = { 0 }, complete[PLAYERBOT_YOHARA_ELEMENTS] = { 0 }, worn[PLAYERBOT_YOHARA_ELEMENTS] = { 0 };
		int records = 0, none = 0, piecesHeld = 0, ready = 0;
		for (std::map<DWORD, TPlayerBotSecondSet>::iterator it = s_mapPlayerBotSecondSet.begin(); it != s_mapPlayerBotSecondSet.end();)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch && dwNow - it->second.dwSeen > PLAYERBOT_SS_FORGET_MS)
			{
				s_mapPlayerBotSecondSetSpent.erase(it->first);
				s_mapPlayerBotSecondSet.erase(it++);
				continue;
			}
			const TPlayerBotSecondSet& s = it->second;
			++records;
			if (s.iE2 < 0)
				++none;
			else if (s.bWorn)
				++worn[s.iE2];
			else if (s.bComplete)
				++complete[s.iE2];
			else
				++progress[s.iE2];
			for (int i = 0; i < PLAYERBOT_SS_REQUIRED; ++i)
			{
				piecesHeld += s.adwB[i] ? 1 : 0;
				ready += s.adwB[i] && s.abReady[i] ? 1 : 0;
			}
			++it;
		}
		std::string line;
		char buf[96];
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
		{
			if (!progress[e] && !complete[e] && !worn[e])
				continue;
			snprintf(buf, sizeof(buf), " %s=[progress=%d complete=%d worn=%d]", PLAYERBOT_YOHARA_ELEMENT_NAMES[e], progress[e], complete[e],
					worn[e]);
			line += buf;
		}
		sys_log(0, "PLAYERBOT_SECONDSET: census bots=%d no_set=%d pieces=%d ready=%d swaps_in_h=%u swaps_out_h=%u started=%u "
				"pieces_taken=%u pieces_ready=%u completed=%u swaps_in=%u swaps_out=%u bonus_stones=%u costume_rolls=%u blocked=%u "
				"resets=%u loaded=%u second_set_moves=%u%s",
				records, none, piecesHeld, ready, st.hourSwapIn, st.hourSwapOut, st.started, st.pieces, st.ready, st.complete,
				st.swapIn, st.swapOut, st.bonusStones, st.costumeRolls, st.blocked, st.resets, st.loaded,
				s_kPlayerBotElementMoves.secondSet, line.c_str());
		st.hourSwapIn = st.hourSwapOut = 0;
	}

	// ------------------------------------------------------------ the tick

	void ManagePlayerBotSecondSet(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		TickPlayerBotSecondSetCensus(dwNow);
		if (!ch || ch->IsDead() || !ch->IsItemLoaded() || !ch->GetDesc() || !ch->GetDesc()->IsBot())
			return;
		TPlayerBotSecondSet* s = GetPlayerBotSecondSet(ch, true);
		if (!s)
			return;
		s->dwSeen = dwNow ? dwNow : 1;

		// The swap, on the quick clock while one may be due.
		if (s->iE2 >= 0 && (s->bWorn || s->bComplete) && (int)(dwNow - s->dwNextSwapLook) >= 0)
		{
			s->dwNextSwapLook = dwNow + PLAYERBOT_SS_SWAP_LOOK_MS;
			const bool want = IsPlayerBotSecondSetWanted(ch, *s);
			if (want != s->bWorn)
			{
				const long here = ch->GetMapIndex();
				const bool place = GetPlayerBotYoharaElementSlot(here) >= 0 || IsPlayerBotVillageMap(here);
				if (place && !ch->GetExchange() && !ch->GetMyShop() && !IsPlayerBotGearFrozen(ch) &&
						!IsPlayerBotEquipWindowShut(ch, state))
				{
					SwapPlayerBotSecondSet(ch, state, *s, want, dwNow);
					return;
				}
			}
		}

		if ((int)(dwNow - s->dwNextLook) < 0)
			return;
		s->dwNextLook = dwNow + PLAYERBOT_SS_LOOK_MS;
		if (s->bWorn)
			return;	// the set is in use: nothing to collect or roll
		const int e1 = GetPlayerBotHuntElementIndex(ch);
		const long huntMap = GetPlayerBotSecondSetHuntMap(ch);
		if (e1 < 0 || huntMap == 0)
			return;
		// the first set's own map (the set is worn below it only)
		if (e1 != s->iE2 && huntMap != s->lMapA && GetPlayerBotSungmaSlot(huntMap) >= 0)
		{
			s->lMapA = huntMap;
			ch->SetQuestFlag(PLAYERBOT_SS_FLAG_AMAP, (int)huntMap);
		}
		if (s->iE2 >= 0 && e1 == s->iE2)
		{
			// the first set hunts E2 itself (a flip up): the second set has no use left
			if (GetPlayerBotSungmaSlot(huntMap) >= GetPlayerBotSungmaSlot(s->lMapA))
				ResetPlayerBotSecondSet(ch, *s, "first_set_is_e2");
			return;
		}
		if (s->iE2 < 0)
		{
			const char* why = "";
			if (!IsPlayerBotFirstSetDone(ch, state, e1, &why))
			{
				NotePlayerBotSecondSetBlocked(ch, *s, why, "", dwNow);
				return;
			}
			long map = 0;
			std::string weights;
			const int e2 = ChoosePlayerBotSecondSetElement(ch, e1, huntMap, &map, &weights);
			if (e2 < 0)
			{
				NotePlayerBotSecondSetBlocked(ch, *s, weights.c_str(), "", dwNow);
				return;
			}
			s->iE2 = e2;
			s->lMapE2 = map;
			s->lMapA = huntMap;
			ch->SetQuestFlag(PLAYERBOT_SS_FLAG_E2, e2 + 1);
			ch->SetQuestFlag(PLAYERBOT_SS_FLAG_MAP, (int)map);
			ch->SetQuestFlag(PLAYERBOT_SS_FLAG_AMAP, (int)huntMap);
			++s_kPlayerBotSecondSetStats.started;
			sys_log(0, "PLAYERBOT_SECONDSET: started pid=%u name=%s champion=%d e1=%s map=%ld e2=%s for_map=%ld weights=[%s] gear=[%s]",
					ch->GetPlayerID(), ch->GetName(), GetPlayerBotChampionLevel(ch), PLAYERBOT_YOHARA_ELEMENT_NAMES[e1], huntMap,
					PLAYERBOT_YOHARA_ELEMENT_NAMES[e2], map, weights.c_str(), DescribePlayerBotElementGear(ch, e1).c_str());
		}

		// The pieces: an empty slot takes the best candidate of the bag; every piece judged for E2.
		TPlayerBotElementOverride guard(ch, s->iE2);
		int held = 0, readyCount = 0;
		std::string missing;
		for (int slot = 0; slot < PLAYERBOT_SS_SLOTS; ++slot)
		{
			LPITEM piece = FindPlayerBotSecondSetItem(ch, s->adwB[slot]);
			if (piece && piece->IsEquipped())
			{
				// put on as the first set's (a path that does not ask the set): the first set's now
				sys_log(0, "PLAYERBOT_SECONDSET: piece worn by the first set pid=%u name=%s e2=%s slot=%s vnum=%u id=%u",
						ch->GetPlayerID(), ch->GetName(), PLAYERBOT_YOHARA_ELEMENT_NAMES[s->iE2], PLAYERBOT_SS_NAMES[slot],
						piece->GetVnum(), piece->GetID());
				SetPlayerBotSecondSetPiece(ch, *s, slot, 0);
				piece = NULL;
			}
			else if (!piece && s->adwB[slot])
			{
				sys_log(0, "PLAYERBOT_SECONDSET: piece lost pid=%u name=%s e2=%s slot=%s id=%u", ch->GetPlayerID(), ch->GetName(),
						PLAYERBOT_YOHARA_ELEMENT_NAMES[s->iE2], PLAYERBOT_SS_NAMES[slot], s->adwB[slot]);
				SetPlayerBotSecondSetPiece(ch, *s, slot, 0);
			}
			if (!piece && slot < PLAYERBOT_SS_REQUIRED)
			{
				LPITEM candidate = FindPlayerBotSecondSetCandidate(ch, *s, slot);
				if (candidate)
				{
					const bool bought = s->dwBoughtVnum != 0 && candidate->GetVnum() == s->dwBoughtVnum;
					TakePlayerBotSecondSetPiece(ch, *s, slot, candidate, bought ? "market" : "own");
					if (bought)
						s->dwBoughtVnum = 0;
					piece = candidate;
				}
			}
			if (!piece)
			{
				if (slot < PLAYERBOT_SS_REQUIRED)
					missing += missing.empty() ? PLAYERBOT_SS_NAMES[slot] : std::string(",") + PLAYERBOT_SS_NAMES[slot];
				continue;
			}
			++held;
			const bool ready = IsPlayerBotSecondSetPieceReady(ch, *s, slot, piece);
			if (ready && !s->abReady[slot])
			{
				++s_kPlayerBotSecondSetStats.ready;
				const BYTE point = GetPlayerBotElementResistPoint(s->iE2);
				sys_log(0, "PLAYERBOT_SECONDSET: piece_ready pid=%u name=%s e2=%s slot=%s vnum=%u+%d e2_line=%ld lines=%d spent=%d",
						ch->GetPlayerID(), ch->GetName(), PLAYERBOT_YOHARA_ELEMENT_NAMES[s->iE2], PLAYERBOT_SS_NAMES[slot],
						piece->GetVnum(), (int)piece->GetRefineLevel(), point ? GetPlayerBotYoharaPieceLine(piece, point) : 0L,
						piece->GetAttributeCount(), s_mapPlayerBotSecondSetSpent[ch->GetPlayerID()][piece->GetID()]);
			}
			s->abReady[slot] = ready;
			if (ready && slot < PLAYERBOT_SS_REQUIRED)
				++readyCount;
		}
		const bool complete = missing.empty() && readyCount == PLAYERBOT_SS_REQUIRED;
		if (complete && !s->bComplete)
		{
			++s_kPlayerBotSecondSetStats.complete;
			sys_log(0, "PLAYERBOT_SECONDSET: complete pid=%u name=%s champion=%d e1=%s e2=%s for_map=%ld own_map=%ld pieces=%d",
					ch->GetPlayerID(), ch->GetName(), GetPlayerBotChampionLevel(ch), PLAYERBOT_YOHARA_ELEMENT_NAMES[e1],
					PLAYERBOT_YOHARA_ELEMENT_NAMES[s->iE2], s->lMapE2, s->lMapA, held);
		}
		s->bComplete = complete;
		if (!missing.empty())
			NotePlayerBotSecondSetBlocked(ch, *s, "no_piece", ("slots=" + missing).c_str(), dwNow);
	}
}
#endif

#endif
