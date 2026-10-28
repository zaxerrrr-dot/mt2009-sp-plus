#ifndef __INC_METIN2_PLAYERBOT_ELEMENT_RESIST_H__
#define __INC_METIN2_PLAYERBOT_ELEMENT_RESIST_H__

// MT2009_PLUS_BOT_ELEMENT_RESIST_V1 - a Yohara bot's element resistance (the owner, 28 October 2026: "Naucz boty
// odpornosci na zywioly ... bot musi wybrac, na jakim zywiole chce expic, ustawic sobie odpornosc na ten zywiol w
// zbroi, helmie i bransolecie, wymiksowac odpornosc w kostiumie i fryzurze, wypic eliksir odpornosci na ten zywiol i
// dopiero isc expic. Na Yoharze odpornosci i PZ to najwazniejsze bonusy"; then: one element, the most common on its
// map, everything for it - no second element).
//
// Who: a Yohara bot (IsPlayerBotYoharaBonusMember: a member of a Yohara cohort or any bot with a Champion level).
// Everybody else: GetPlayerBotHuntElement 0, nothing changes.
//
// 1. The hunt element (GetPlayerBotHuntElement): from the Sung Ma map the bot's elements are taken for
//    (GetPlayerBotYoharaElementMap - its stay's map, the trip's map to go back to, its band's map), by the table of
//    playerbot_yohara_elements.h (the owner's map guide): the map's largest share; elements within
//    PLAYERBOT_ELEMENT_TIE_PCT of it are a tie, and a tie goes to an element whose resistance the gear can hold
//    (item_attr: fire, lightning and wind roll on the armour, helmet and bracelet; ice, earth and dark on a talisman
//    only), several of those - or none - split between the bots by their pid. So, with this world's table:
//      374 Twierdza dark or ice (half the bots each)   373 Dongan fire        376 Seoganland earth
//      377 Namgan wind     385 Yilad earth     388 Wawoz lightning     389 Rozpadlina lightning
//      393 Schronienie ice     394 Zejscie lightning (every monster there is ice and lightning: the engine takes the
//      better of the two resistances, ElementsAttackBonus)
//    The same map gives the same element, so it is sticky; with no map at all (a moment in a village) the last one
//    stays. A new map with a new element is a new preparation (3).
// 2. The gear (playerbot_yohara_bonus.h): the hunt element's resistance is a must on the armour and the bracelet next
//    to Max HP, the helmet's must; no other element's resistance is wanted. The stones are the bot's own 71084/71085,
//    by the pass's shares - an element change re-bonuses a piece only within its share and the leftover over the
//    reserve, never the whole stock.
// 3. The costume and the hairstyle (IsPlayerBotYoharaCostumeLineGood): the costume Max HP, arrow and magic
//    resistance, the hairstyle arrow dodge and magic resistance - at level 3 of the table or more - and the hunt
//    element's resistance. MT2009_PLUS_COSTUME_ATTR_GLOBAL_V1 (costume_attr_global.sql: the global costume pools, fire,
//    lightning and wind resistance on costume_body and costume_hair): that resistance is the first line - a piece
//    whose set rolls it is not finished without it (IsPlayerBotCostumeHuntLineMissing; the body costume wants a
//    second good line next to it, Max HP first by its weight, until PLAYERBOT_COSTUME_HUNT_ALONE_AFTER changes; the
//    hairstyle the resistance alone). Ice, earth and dark roll on no costume: the old rule. The reagents are the
//    player's: 70063 / 70064 bought at Handlarka Roznosci (9003; the Dongan errand's stop too), rolled from the bag
//    out of a fight (ManagePlayerBotBonusReroll), the old pass's gold rules and limits.
// 4. The elixir: the hunt element's resistance elixir (50836-50841, and its power elixir) is the only one a bot with
//    a hunt element stocks at Dongan's exchange (playerbot_yohara_shop.h: 10 Materialy Rzemieslnicze each) and
//    drinks on its map when the effect is gone (playerbot_yohara_elements_late.h) - and once before it sets off for
//    a new map (5).
// 5. The order: when the Sung Ma pick moves the bot to a map of another element (and it may wait - not a step down
//    after its deaths, not a map it no longer fits), the move is held while the armour, helmet and bracelet that can
//    take the new resistance lack it and the bag holds change stones over the pass's reserve - the bot hunts on where
//    it is meanwhile - for at most PLAYERBOT_ELEMENT_PREP_MAX_MS; then (ready, out of stones, or the time up) it drinks
//    the elixir and goes. Nothing blocks for good.
// 6. The log: PLAYERBOT_ELEMENT - "element" (a bot's element set or changed), "prepared" (one line a move: the
//    outcome, the wait, every piece's line of the element, the costume's and hairstyle's good lines, the elixir), and
//    "census" every PLAYERBOT_ELEMENT_CENSUS_MS (per element: bots, the resistance point's average / min / max, the
//    gear's own resistance average, the pieces carrying the line, elixirs active and in stock).
//
// MT2009_PLUS_BOT_ELEMENT_RESIST_V2 (the owner, 28 October 2026, the census 20 minutes after V1 - lightning 34%, wind
// 33%, fire 22%, ice 18%, earth 8%: "musza znacznie lepiej bonowac EQ pod odpornosci"; the talisman alone gives 25):
//   * the gear (playerbot_yohara_bonus.h): the talisman is bonused too (71085/71084, all six resistances roll on it to
//     25 - the one gear line of an ice, earth or dark bot), and the element phase changes talisman, armour, bracelet
//     and helmet - in that order - until the hunt element's line is at its TOP (25 / 15), Max HP kept, each within an
//     element budget (80 / 300 / 300 / 100 changes);
//   * the costume and hairstyle (playerbot_bonus.h): the line to its top (15) within PLAYERBOT_COSTUME_HUNT_TOP_CHANGES,
//     the reagent bought five stacks at a time, the hairstyle taking two lines first;
//   * the elixir (playerbot_yohara_shop.h): the materials a hunt bot holds are its elixirs' (kept, first);
//   * the Dragon Stones (playerbot_alchemy.h): the hunt element's kind is refined and beaned first;
//   * the move's preparation (5) waits for the same element targets (the talisman's too);
//   * the census (6) breaks the resistance down by source (gear, talisman, costume, ds, elixir, other) and counts the
//     pieces at the top.
//
// MT2009_PLUS_BOT_ELEMENT_RESIST_V3 (the census of 28 October 12:35 - dark 22, ice 34, earth 46 on average; elixir on
// 6 of 65 dark bots, 23 of 54 ice, while they held 6 elixirs each):
//   * the elixir (ManagePlayerBotHuntElixirTick): the light pass that drank it (ManagePlayerBotYoharaElements, from the
//     workshop's light pass) runs only where the full tick gets past its early exits and the workshop's gates (no
//     Metin fight, no multi-pull, no full bag, no person served) - on the Twierdza it reached 20 of 112 bots. The hunt
//     element's resistance and power elixirs are now drunk from the top of every tick, on the bot's own 10 s clock,
//     alive on its element map; the census counts the uptime there and why a bot did not drink;
//   * the element moves only up the Sung Ma maps (the owner, 28 October: bots change the element only going up; a
//     step down to another element needs a second set - HasPlayerBotElementSecondSet, none yet): the map pick
//     (PickPlayerBotSungmaMap) skips a lower map of another element and the element is kept where the old one is in
//     the new map's tie (no flip for nothing); a map of the bot's element is always open to it;
//   * the element budget of a piece (playerbot_yohara_bonus.h) counts the changes made for the element it wears now,
//     the talisman's raised to 160 (the only gear line of an ice, earth or dark bot).
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_yohara_shop.h, in the anonymous
// namespace; the declarations the earlier fragments use are in playerbot_types.h.

namespace
{
	const int PLAYERBOT_ELEMENT_TIE_PCT = 10;
	const DWORD PLAYERBOT_ELEMENT_CACHE_MS = 5000;
	const DWORD PLAYERBOT_ELEMENT_PREP_MAX_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_ELEMENT_PREP_LOG_MS = 60 * 1000;
	const DWORD PLAYERBOT_ELEMENT_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_ELEMENT_SEEN_MS = 15 * 60 * 1000;
	const BYTE PLAYERBOT_ELEMENT_GEAR_WEARS[3] = { WEAR_BODY, WEAR_HEAD, WEAR_WRIST };
	// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the element phase's pieces, in its order
	const BYTE PLAYERBOT_ELEMENT_TARGET_WEARS[4] = { WEAR_PENDANT, WEAR_BODY, WEAR_WRIST, WEAR_HEAD };

	struct TPlayerBotHuntElement
	{
		long lMap;	// the map the element was chosen for
		int iElement;	// -1 none
		DWORD dwAt;	// the cache's time
		DWORD dwSeen;
		// the preparation of a move (5)
		long lPrepFrom, lPrepTo;
		int iPrepFrom;	// the element before the move
		DWORD dwPrepSince;
		bool bPrepWait, bPrepOpen;
		long lBlockedMap;	// MT2009_PLUS_BOT_ELEMENT_RESIST_V3: the lower map whose element change was refused (logged once)
		DWORD dwNextElixir;	// MT2009_PLUS_BOT_ELEMENT_RESIST_V3: the elixir tick's clock
		TPlayerBotHuntElement() : lMap(0), iElement(-1), dwAt(0), dwSeen(0), lPrepFrom(0), lPrepTo(0), iPrepFrom(-1),
			dwPrepSince(0), bPrepWait(false), bPrepOpen(false), lBlockedMap(0), dwNextElixir(0) {}
	};
	std::map<DWORD, TPlayerBotHuntElement> s_mapPlayerBotHuntElement;

	struct TPlayerBotElementStats
	{
		unsigned int changes, prepared, ready, timeouts, noStones, urgent, sameElement, elixirsAtMove;
		DWORD dwCensusAt;
		TPlayerBotElementStats() : changes(0), prepared(0), ready(0), timeouts(0), noStones(0), urgent(0), sameElement(0),
			elixirsAtMove(0), dwCensusAt(0) {}
	};
	TPlayerBotElementStats s_kPlayerBotElementStats;

#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
	const DWORD PLAYERBOT_ELEMENT_ELIXIR_TICK_MS = 10 * 1000;
	// The elixir tick's outcome a look (per hunt element, since the last census): drunk now, already on, and why not.
	enum { PLAYERBOT_ELIXIR_DRUNK, PLAYERBOT_ELIXIR_ON, PLAYERBOT_ELIXIR_OFF_MAP, PLAYERBOT_ELIXIR_DEAD,
		PLAYERBOT_ELIXIR_NO_STOCK, PLAYERBOT_ELIXIR_USE_FAILED, PLAYERBOT_ELIXIR_COUNT };
	const char* const PLAYERBOT_ELIXIR_REASON_NAMES[PLAYERBOT_ELIXIR_COUNT] = { "drunk", "on", "off_map", "dead", "no_stock",
		"use_failed" };
	unsigned int s_aPlayerBotElixirLooks[PLAYERBOT_YOHARA_ELEMENTS][PLAYERBOT_ELIXIR_COUNT];
	// The element's moves (since the start): a flip up the maps, a flip with no map order to judge (a first map, off the
	// table), the old element kept in the new map's tie, a change refused on a lower map, a lower map of another element
	// skipped by the map pick, a change down allowed by a second set.
	struct TPlayerBotElementMoveStats
	{
		unsigned int flipsUp, flipsFree, keptTie, blockedDown, pickSkipped, secondSet;
		TPlayerBotElementMoveStats() : flipsUp(0), flipsFree(0), keptTie(0), blockedDown(0), pickSkipped(0), secondSet(0) {}
	};
	TPlayerBotElementMoveStats s_kPlayerBotElementMoves;

	// The owner, 28 October 2026: a step down to a map of another element needs a second equipment and costume set made
	// for that element (element: GetPlayerBotHuntElement's encoding, 1-6). Not made yet - a later feature fills it in.
	bool HasPlayerBotElementSecondSet(LPCHARACTER ch, BYTE element)
	{
		(void)ch;
		(void)element;
		return false;
	}

	// Whether the element is the map's largest share or within PLAYERBOT_ELEMENT_TIE_PCT of it.
	bool IsPlayerBotElementInMapTie(long map, int e)
	{
		int share[PLAYERBOT_YOHARA_ELEMENTS];
		if (e < 0 || e >= PLAYERBOT_YOHARA_ELEMENTS || !GetPlayerBotYoharaMapShares(map, share))
			return false;
		int top = 0;
		for (int i = 0; i < PLAYERBOT_YOHARA_ELEMENTS; ++i)
			top = std::max(top, share[i]);
		return share[e] > 0 && share[e] + PLAYERBOT_ELEMENT_TIE_PCT >= top;
	}
#endif

	bool IsPlayerBotApplyOnAttrSet(BYTE type, int set)
	{
		if (type == 0 || set < 0 || set >= ATTRIBUTE_SET_MAX_NUM)
			return false;
		TItemAttrMap::const_iterator it = g_map_itemAttr.find(type);
		return it != g_map_itemAttr.end() && it->second.dwProb > 0 && it->second.bMaxLevelBySet[set] > 0;
	}

	BYTE GetPlayerBotElementResistPoint(int e)
	{
		return e >= 0 && e < PLAYERBOT_YOHARA_ELEMENTS ? PLAYERBOT_YOHARA_RESIST_POINTS[e] : 0;
	}

	// Whether the armour, the helmet or the bracelet can roll the element's resistance (the live item_attr).
	bool IsPlayerBotElementOnGear(int e)
	{
		const BYTE point = GetPlayerBotElementResistPoint(e);
		return point != 0 && (IsPlayerBotApplyOnAttrSet(point, ATTRIBUTE_SET_BODY) ||
				IsPlayerBotApplyOnAttrSet(point, ATTRIBUTE_SET_HEAD) || IsPlayerBotApplyOnAttrSet(point, ATTRIBUTE_SET_WRIST));
	}

	// (1) The element a bot hunts on this map: the largest share, a tie to the gear's element, the rest by the pid.
	int ChoosePlayerBotHuntElement(long map, DWORD pid)
	{
		int share[PLAYERBOT_YOHARA_ELEMENTS];
		if (!GetPlayerBotYoharaMapShares(map, share))
			return -1;
		int top = 0;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			top = std::max(top, share[e]);
		if (top <= 0)
			return -1;
		int ties[PLAYERBOT_YOHARA_ELEMENTS], gear[PLAYERBOT_YOHARA_ELEMENTS];
		int nTies = 0, nGear = 0;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			if (share[e] > 0 && share[e] + PLAYERBOT_ELEMENT_TIE_PCT >= top)
			{
				ties[nTies++] = e;
				if (IsPlayerBotElementOnGear(e))
					gear[nGear++] = e;
			}
		if (nGear > 0)
			return gear[pid % (DWORD)nGear];
		return ties[pid % (DWORD)nTies];
	}

	int GetPlayerBotHuntElementIndex(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC() || !IsPlayerBotYoharaBonusMember(ch))
			return -1;
		const DWORD now = get_dword_time();
		TPlayerBotHuntElement& h = s_mapPlayerBotHuntElement[ch->GetPlayerID()];
		h.dwSeen = now ? now : 1;
		if (h.dwAt != 0 && now - h.dwAt < PLAYERBOT_ELEMENT_CACHE_MS)
			return h.iElement;
		h.dwAt = now ? now : 1;
		const long map = GetPlayerBotYoharaElementMap(ch);
		if (map == 0)
			return h.iElement;	// a moment off its maps: the last one stays
		const long base = map >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? map / 10000 : map;
		if (base == h.lMap && h.iElement >= 0)
			return h.iElement;
		int e = ChoosePlayerBotHuntElement(base, ch->GetPlayerID());
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V3: the old element stays where the new map's tie holds it; a change only up the
		// maps (or with a second set for the new element).
		if (h.iElement >= 0 && e >= 0 && e != h.iElement)
		{
			const int fromSlot = GetPlayerBotSungmaSlot(h.lMap), toSlot = GetPlayerBotSungmaSlot(base);
			if (IsPlayerBotElementInMapTie(base, h.iElement))
			{
				++s_kPlayerBotElementMoves.keptTie;
				e = h.iElement;
			}
			else if (fromSlot >= 0 && toSlot >= 0 && toSlot < fromSlot)
			{
				if (HasPlayerBotElementSecondSet(ch, (BYTE)(e + 1)))
					++s_kPlayerBotElementMoves.secondSet;
				else
				{
					// a lower map of another element (the pick refuses it - a trip, a party's follow, a flee got it here):
					// the element and its map stay; the element's map is still the higher one
					if (h.lBlockedMap != base)
					{
						h.lBlockedMap = base;
						++s_kPlayerBotElementMoves.blockedDown;
						sys_log(0, "PLAYERBOT_ELEMENT: change refused pid=%u name=%s from_map=%ld map=%ld element=%s wanted=%s why=down",
								ch->GetPlayerID(), ch->GetName(), h.lMap, base, PLAYERBOT_YOHARA_ELEMENT_NAMES[h.iElement],
								PLAYERBOT_YOHARA_ELEMENT_NAMES[e]);
					}
					return h.iElement;
				}
			}
			else if (fromSlot >= 0 && toSlot > fromSlot)
				++s_kPlayerBotElementMoves.flipsUp;
			else
				++s_kPlayerBotElementMoves.flipsFree;
		}
		h.lBlockedMap = 0;
#endif
		if (e != h.iElement)
		{
			++s_kPlayerBotElementStats.changes;
			sys_log(0, "PLAYERBOT_ELEMENT: element pid=%u name=%s map=%ld from=%s to=%s gear=%d",
					ch->GetPlayerID(), ch->GetName(), base, h.iElement >= 0 ? PLAYERBOT_YOHARA_ELEMENT_NAMES[h.iElement] : "-",
					e >= 0 ? PLAYERBOT_YOHARA_ELEMENT_NAMES[e] : "-", e >= 0 && IsPlayerBotElementOnGear(e) ? 1 : 0);
		}
		h.lMap = base;
		h.iElement = e;
		return e;
	}

	BYTE GetPlayerBotHuntElement(LPCHARACTER ch)
	{
		const int e = GetPlayerBotHuntElementIndex(ch);
		return e >= 0 ? (BYTE)(e + 1) : 0;
	}

	BYTE GetPlayerBotHuntResistPoint(LPCHARACTER ch)
	{
		const int e = GetPlayerBotHuntElementIndex(ch);
		return e >= 0 && IsPlayerBotElementOnGear(e) ? GetPlayerBotElementResistPoint(e) : 0;
	}

	// (3) A Yohara bot's costume / hairstyle line.
	int IsPlayerBotYoharaCostumeLineGood(LPCHARACTER ch, LPITEM costume, BYTE type, long value)
	{
		if (!ch || !costume || costume->GetType() != ITEM_COSTUME || !IsPlayerBotYoharaBonusMember(ch))
			return -1;
		bool listed = false;
		const BYTE hunt = GetPlayerBotElementResistPoint(GetPlayerBotHuntElementIndex(ch));
		switch (costume->GetSubType())
		{
			case COSTUME_BODY:
				listed = type == POINT_MAX_HP || type == POINT_RESIST_BOW || type == POINT_RESIST_MAGIC || (hunt && type == hunt);
				break;
			case COSTUME_HAIR:
				listed = type == POINT_DODGE || type == POINT_RESIST_MAGIC || (hunt && type == hunt);
				break;
			default:
				return -1;	// the weapon skin: the old scoring
		}
		if (!listed || value <= 0)
			return 0;
		TItemAttrMap::const_iterator it = g_map_itemAttr.find(type);
		const long floor = it != g_map_itemAttr.end() ? it->second.lValues[2] : 0;	// level 3 of the table
		return value >= floor ? 1 : 0;
	}

	// MT2009_PLUS_COSTUME_ATTR_GLOBAL_V1: the hunt element's resistance as the costume's / hairstyle's first line.
	bool IsPlayerBotCostumeHuntLineMissing(LPCHARACTER ch, LPITEM costume)
	{
		if (!ch || !costume || costume->GetType() != ITEM_COSTUME || !IsPlayerBotYoharaBonusMember(ch) ||
				(costume->GetSubType() != COSTUME_BODY && costume->GetSubType() != COSTUME_HAIR))
			return false;
		const BYTE point = GetPlayerBotElementResistPoint(GetPlayerBotHuntElementIndex(ch));
		if (!point || !IsPlayerBotApplyOnAttrSet(point, costume->GetAttributeSetIndex()))
			return false;
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			if (costume->GetAttributeType(i) == point &&
					IsPlayerBotYoharaCostumeLineGood(ch, costume, point, costume->GetAttributeValue(i)) > 0)
				return false;
		return true;
	}

	// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the hunt element's resistance on a costume / hairstyle whose set rolls it is
	// below its top value (15 - the set's top level): the costume pass works on (70064) up to
	// PLAYERBOT_COSTUME_HUNT_TOP_CHANGES changes of the piece (playerbot_bonus.h), then the level-3 floor as before.
	bool IsPlayerBotCostumeHuntLineShort(LPCHARACTER ch, LPITEM costume)
	{
		if (!ch || !costume || costume->GetType() != ITEM_COSTUME || !IsPlayerBotYoharaBonusMember(ch) ||
				(costume->GetSubType() != COSTUME_BODY && costume->GetSubType() != COSTUME_HAIR))
			return false;
		const BYTE point = GetPlayerBotElementResistPoint(GetPlayerBotHuntElementIndex(ch));
		if (!point || !IsPlayerBotApplyOnAttrSet(point, costume->GetAttributeSetIndex()))
			return false;
		const long top = GetPlayerBotYoharaTopLineValue(costume, point);
		return top > 0 && GetPlayerBotYoharaPieceLine(costume, point) < top;
	}

#ifdef MT2009_PLUS_BOT_COSTUME_RESIST_V1
	// MT2009_PLUS_BOT_COSTUME_RESIST_V1: the costume pass' view of the hunt element (playerbot_bonus.h,
	// GetPlayerBotYoharaCostumeBonusNeed).
	int GetPlayerBotCostumeHuntState(LPCHARACTER ch, LPITEM costume)
	{
		if (!ch || !costume || costume->GetType() != ITEM_COSTUME || !IsPlayerBotYoharaBonusMember(ch) ||
				(costume->GetSubType() != COSTUME_BODY && costume->GetSubType() != COSTUME_HAIR))
			return -1;
		const BYTE point = GetPlayerBotElementResistPoint(GetPlayerBotHuntElementIndex(ch));
		if (!point || !IsPlayerBotApplyOnAttrSet(point, costume->GetAttributeSetIndex()))
			return -1;
		const long top = GetPlayerBotYoharaTopLineValue(costume, point);
		if (top <= 0)
			return -1;
		return GetPlayerBotYoharaPieceLine(costume, point) >= top ? 1 : 0;
	}

	bool IsPlayerBotCostumeElementTopKept(LPCHARACTER ch, LPITEM costume)
	{
		if (!ch || !costume || costume->GetType() != ITEM_COSTUME ||
				(costume->GetSubType() != COSTUME_BODY && costume->GetSubType() != COSTUME_HAIR) ||
				GetPlayerBotCostumeHuntState(ch, costume) >= 0)
			return false;
		static const BYTE s_abPoints[3] = { POINT_RESIST_FIRE, POINT_RESIST_ELEC, POINT_RESIST_WIND };
		for (int i = 0; i < 3; ++i)
		{
			const long top = GetPlayerBotYoharaTopLineValue(costume, s_abPoints[i]);
			if (top > 0 && GetPlayerBotYoharaPieceLine(costume, s_abPoints[i]) >= top)
				return true;
		}
		return false;
	}

	bool HasPlayerBotCostumeGoodMaxHp(LPITEM costume)
	{
		const long hp = GetPlayerBotYoharaPieceLine(costume, POINT_MAX_HP);
		if (hp <= 0)
			return false;
		TItemAttrMap::const_iterator it = g_map_itemAttr.find(POINT_MAX_HP);
		return it == g_map_itemAttr.end() || hp >= it->second.lValues[2];
	}

	// The costume pass' counters since the start, by piece (body, hair, weapon skin) - the census' costume line.
	const char* const PLAYERBOT_COSEV_NAMES[PLAYERBOT_COSEV_COUNT] = { "none", "reset_no_lines", "reset_hunt_2l",
		"reset_yohara_2l", "reset_old_2l", "reset_old_3l", "change_hunt", "change_defence", "change_one_line", "change_old",
		"fin_top", "fin_kept", "fin_good", "fin_hp", "fin_budget", "fin_old" };
	unsigned int s_aPlayerBotCostumeEvents[3][PLAYERBOT_COSEV_COUNT];

	const char* GetPlayerBotCostumeEventName(int ev)
	{
		return ev >= 0 && ev < PLAYERBOT_COSEV_COUNT ? PLAYERBOT_COSEV_NAMES[ev] : "?";
	}

	void NotePlayerBotCostumeEvent(LPITEM costume, int ev)
	{
		if (!costume || ev <= PLAYERBOT_COSEV_NONE || ev >= PLAYERBOT_COSEV_COUNT)
			return;
		const int kind = costume->GetSubType() == COSTUME_BODY ? 0 : costume->GetSubType() == COSTUME_HAIR ? 1 : 2;
		++s_aPlayerBotCostumeEvents[kind][ev];
	}
#endif

	// The worn piece's line of the element's resistance (0 none).
	long GetPlayerBotWornResistLine(LPCHARACTER ch, BYTE wear, BYTE point)
	{
		LPITEM item = ch ? ch->GetWear(wear) : NULL;
		long value = 0;
		for (int i = 0; item && point && i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			if (item->GetAttributeType(i) == point)
				value += item->GetAttributeValue(i);
		return value;
	}

	// The gear's own resistance to the element: the lines of every worn piece and its proto's applies (the elixir and
	// the buffs left out).
	long GetPlayerBotGearResist(LPCHARACTER ch, BYTE point)
	{
		long total = 0;
		for (int cell = 0; ch && point && cell < WEAR_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetWear(cell);
			if (!item || !item->GetProto())
				continue;
			for (int i = 0; i < ITEM_APPLY_MAX_NUM; ++i)
				if (item->GetProto()->aApplies[i].bType == point)
					total += item->GetProto()->aApplies[i].lValue;
			for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
				if (item->GetAttributeType(i) == point)
					total += item->GetAttributeValue(i);
		}
		return total;
	}

	// (5) Whether the armour, helmet and bracelet are as far as the stones take them for the element: every one that
	// can roll the line has it - or the bag holds no change stones over the bonus pass's reserve. *noStones: the
	// second.
	bool IsPlayerBotElementGearReady(LPCHARACTER ch, int e, bool* noStones)
	{
		*noStones = false;
		const BYTE point = GetPlayerBotElementResistPoint(e);
		if (!point)
			return true;
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the talisman too (every element), and a piece is ready at its element target
		// (the line at its top) or out of its element budget - the bonus pass's own rule (GetPlayerBotYoharaElementTarget)
		bool missing = false;
		const std::map<DWORD, int>& spent = s_mapPlayerBotYoharaBonusSpent[ch->GetPlayerID()];
		for (int i = 0; i < 4; ++i)
		{
			const BYTE wear = PLAYERBOT_ELEMENT_TARGET_WEARS[i];
			LPITEM item = ch->GetWear(wear);
			// the pieces the bonus pass works on (CollectPlayerBotYoharaBonusPieces) - the rest waits for nobody
			if (!item || item->GetAttributeSetIndex() < 0 || !IsPlayerBotApplyOnAttrSet(point, item->GetAttributeSetIndex()) ||
					IS_SET(item->GetFlag(), ITEM_FLAG_IRREMOVABLE) || !CanPlayerBotTakeBonusStone(item) ||
					IsPlayerBotSidekickLockedItem(ch, item) || IsPlayerBotSidekickPinned(ch, item))
				continue;
			std::map<DWORD, int>::const_iterator sp = spent.find(item->GetID());
			int used = sp != spent.end() ? sp->second : 0;
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
			used -= GetPlayerBotYoharaElementSpentBase(ch, item, used);
#endif
			if (GetPlayerBotYoharaElementTarget(ch, item, wear, used) == 0 && used < GetPlayerBotYoharaElementCap(wear))
				missing = true;
		}
		if (!missing)
			return true;
		TPlayerBotYoharaBonusBag bag;
		ReadPlayerBotYoharaBonusBag(ch, bag);
		if (IsPlayerBotGearFrozen(ch) || bag.changeCell < 0 || bag.changeUnits <= PLAYERBOT_YOHARA_BONUS_CHANGE_RESERVE)
		{
			*noStones = true;
			return true;
		}
		return false;
	}

	// (4) The hunt element's resistance elixir, now, unless its effect is on. "drunk", "active" or "none".
	const char* DrinkPlayerBotHuntElixir(LPCHARACTER ch, int e)
	{
		if (!ch || e < 0 || e >= PLAYERBOT_YOHARA_ELEMENTS || ch->IsDead())
			return "none";
		const BYTE point = PLAYERBOT_YOHARA_RESIST_POINTS[e];
		if (ch->FindAffect(AFFECT_BLEND, point))
			return "active";
		LPITEM item = ch->FindSpecifyItem(PLAYERBOT_YOHARA_RESIST_ELIXIRS[e]);
		if (!item || item->GetSocket(0) == 0)
			return "none";
		if (!ch->UseItem(TItemPos(INVENTORY, item->GetCell())) || !ch->FindAffect(AFFECT_BLEND, point))
			return "none";
		++s_uPlayerBotYoharaElixirs;
		++s_kPlayerBotElementStats.elixirsAtMove;
		return "drunk";
	}

	// The line of the outcome: every piece's line of the element, the costume's and hairstyle's good lines.
	std::string DescribePlayerBotElementGear(LPCHARACTER ch, int e)
	{
		const BYTE point = GetPlayerBotElementResistPoint(e);
		static const char* const s_aszNames[3] = { "body", "head", "wrist" };
		std::string out;
		char buf[64];
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the talisman's line first
		{
			LPITEM tal = ch->GetWear(WEAR_PENDANT);
			snprintf(buf, sizeof(buf), "talisman:%ld ", tal ? GetPlayerBotYoharaPieceLine(tal, point) : -1L);
			out += buf;
		}
		for (int i = 0; i < 3; ++i)
		{
			LPITEM item = ch->GetWear(PLAYERBOT_ELEMENT_GEAR_WEARS[i]);
			const bool rolls = item && item->GetAttributeSetIndex() >= 0 && IsPlayerBotApplyOnAttrSet(point, item->GetAttributeSetIndex());
			if (!item)
				snprintf(buf, sizeof(buf), "%s%s:none", i == 0 ? "" : " ", s_aszNames[i]);
			else if (!rolls)
				snprintf(buf, sizeof(buf), "%s%s:n/a", i == 0 ? "" : " ", s_aszNames[i]);
			else
				snprintf(buf, sizeof(buf), "%s%s:%ld", i == 0 ? "" : " ", s_aszNames[i],
						GetPlayerBotWornResistLine(ch, PLAYERBOT_ELEMENT_GEAR_WEARS[i], point));
			out += buf;
		}
		static const BYTE s_abCostume[2] = { WEAR_COSTUME_BODY, WEAR_COSTUME_HAIR };
		static const char* const s_aszCostume[2] = { "costume", "hair" };
		for (int i = 0; i < 2; ++i)
		{
			LPITEM item = ch->GetWear(s_abCostume[i]);
			if (!item)
				snprintf(buf, sizeof(buf), " %s:none", s_aszCostume[i]);
			else
				snprintf(buf, sizeof(buf), " %s:%d/%d%s", s_aszCostume[i], CountPlayerBotGoodCostumeLines(ch, item),
						item->GetAttributeCount(), IsPlayerBotCostumeHuntLineMissing(ch, item) ? "(no_element)" : "");
			out += buf;
		}
		return out;
	}

	void FinishPlayerBotElementPrep(LPCHARACTER ch, TPlayerBotHuntElement& h, const char* outcome, DWORD dwNow)
	{
		const int e = GetPlayerBotHuntElementIndex(ch);
		const char* elixir = DrinkPlayerBotHuntElixir(ch, e);
		TPlayerBotYoharaBonusBag bag;
		ReadPlayerBotYoharaBonusBag(ch, bag);
		++s_kPlayerBotElementStats.prepared;
		sys_log(0, "PLAYERBOT_ELEMENT: prepared pid=%u name=%s from=%ld to=%ld element=%s->%s outcome=%s waited_s=%u "
				"gear=[%s] resist=%d elixir=%s elixirs_left=%d change_stones=%d",
				ch->GetPlayerID(), ch->GetName(), h.lPrepFrom, h.lPrepTo,
				h.iPrepFrom >= 0 ? PLAYERBOT_YOHARA_ELEMENT_NAMES[h.iPrepFrom] : "-",
				e >= 0 ? PLAYERBOT_YOHARA_ELEMENT_NAMES[e] : "-", outcome, (dwNow - h.dwPrepSince) / 1000,
				e >= 0 ? DescribePlayerBotElementGear(ch, e).c_str() : "-",
				e >= 0 ? (int)ch->GetPoint(PLAYERBOT_YOHARA_RESIST_POINTS[e]) : 0, elixir,
				e >= 0 ? (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_RESIST_ELIXIRS[e]) : 0, bag.changeUnits);
		h.bPrepOpen = false;
	}

	void StartPlayerBotElementPrep(LPCHARACTER ch, long fromMap, long toMap, bool mayWait, DWORD dwNow)
	{
		if (!ch || !IsPlayerBotYoharaBonusMember(ch))
			return;
		TPlayerBotHuntElement& h = s_mapPlayerBotHuntElement[ch->GetPlayerID()];
		h.iPrepFrom = h.iElement;
		h.lPrepFrom = fromMap;
		h.lPrepTo = toMap;
		h.dwPrepSince = dwNow ? dwNow : 1;
		h.bPrepWait = mayWait;
		h.bPrepOpen = true;
		h.dwAt = 0;	// the element for the new map at the next ask
	}

	bool HoldPlayerBotElementPrep(LPCHARACTER ch, long toMap, DWORD dwNow)
	{
		if (!ch)
			return false;
		std::map<DWORD, TPlayerBotHuntElement>::iterator it = s_mapPlayerBotHuntElement.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotHuntElement.end() || !it->second.bPrepOpen || it->second.lPrepTo != toMap)
			return false;
		TPlayerBotHuntElement& h = it->second;
		const int e = GetPlayerBotHuntElementIndex(ch);
		if (!h.bPrepWait)
		{
			++s_kPlayerBotElementStats.urgent;
			FinishPlayerBotElementPrep(ch, h, "urgent", dwNow);
			return false;
		}
		if (e == h.iPrepFrom)
		{
			++s_kPlayerBotElementStats.sameElement;
			FinishPlayerBotElementPrep(ch, h, "same_element", dwNow);
			return false;
		}
		bool noStones = false;
		if (e < 0 || IsPlayerBotElementGearReady(ch, e, &noStones))
		{
			if (noStones)
				++s_kPlayerBotElementStats.noStones;
			else
				++s_kPlayerBotElementStats.ready;
			FinishPlayerBotElementPrep(ch, h, noStones ? "no_stones" : (IsPlayerBotElementOnGear(e) ? "ready" : "ready_talisman"), dwNow);
			return false;
		}
		if (dwNow - h.dwPrepSince >= PLAYERBOT_ELEMENT_PREP_MAX_MS)
		{
			++s_kPlayerBotElementStats.timeouts;
			FinishPlayerBotElementPrep(ch, h, "timeout", dwNow);
			return false;
		}
		PlayerBotLogThrottled("element_prep_wait", dwNow, "PLAYERBOT_ELEMENT: preparing pid=%u name=%s to=%ld element=%s waited_s=%u gear=[%s]",
				ch->GetPlayerID(), ch->GetName(), toMap, PLAYERBOT_YOHARA_ELEMENT_NAMES[e], (dwNow - h.dwPrepSince) / 1000,
				DescribePlayerBotElementGear(ch, e).c_str());
		return true;
	}

	// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: a bot's resistance to one element by where it comes from - the armour, helmet,
	// bracelet and the rest of the worn gear (lines and the proto's applies), the talisman, the costume pieces
	// (costume, hairstyle, weapon skin...), the active Dragon Stone deck, the elixir's affect; the rest of GetPoint
	// (skills, buffs, the Will...) is "other".
	enum { PLAYERBOT_ELEMENT_SRC_GEAR, PLAYERBOT_ELEMENT_SRC_TALISMAN, PLAYERBOT_ELEMENT_SRC_COSTUME, PLAYERBOT_ELEMENT_SRC_DS,
		PLAYERBOT_ELEMENT_SRC_ELIXIR, PLAYERBOT_ELEMENT_SRC_OTHER, PLAYERBOT_ELEMENT_SRC_COUNT };
	const char* const PLAYERBOT_ELEMENT_SRC_NAMES[PLAYERBOT_ELEMENT_SRC_COUNT] = { "gear", "talisman", "costume", "ds", "elixir", "other" };

	long SumPlayerBotItemPoint(LPITEM item, BYTE point)
	{
		long total = 0;
		if (!item || !item->GetProto())
			return 0;
		for (int i = 0; i < ITEM_APPLY_MAX_NUM; ++i)
			if (item->GetProto()->aApplies[i].bType == point)
				total += item->GetProto()->aApplies[i].lValue;
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			if (item->GetAttributeType(i) == point)
				total += item->GetAttributeValue(i);
		return total;
	}

	void GetPlayerBotElementResistSources(LPCHARACTER ch, BYTE point, long src[PLAYERBOT_ELEMENT_SRC_COUNT])
	{
		for (int i = 0; i < PLAYERBOT_ELEMENT_SRC_COUNT; ++i)
			src[i] = 0;
		if (!ch || !point)
			return;
		for (int cell = 0; cell < WEAR_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetWear(cell);
			if (!item)
				continue;
			const int kind = cell == WEAR_PENDANT ? PLAYERBOT_ELEMENT_SRC_TALISMAN
					: (item->GetType() == ITEM_COSTUME ? PLAYERBOT_ELEMENT_SRC_COSTUME : PLAYERBOT_ELEMENT_SRC_GEAR);
			src[kind] += SumPlayerBotItemPoint(item, point);
		}
		const int deck = ch->DragonSoul_GetActiveDeck();
		if (deck >= 0)
			for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
			{
				LPITEM stone = ch->GetItem(TItemPos(INVENTORY, (WORD)((int)DRAGON_SOUL_EQUIP_SLOT_START + deck * (int)DS_SLOT_MAX + kind)));
				if (stone && DSManager::instance().IsActiveDragonSoul(stone))
					for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
						if (stone->GetAttributeType(i) == point)
							src[PLAYERBOT_ELEMENT_SRC_DS] += stone->GetAttributeValue(i);
			}
		CAffect* elixir = ch->FindAffect(AFFECT_BLEND, point);
		if (elixir)
			src[PLAYERBOT_ELEMENT_SRC_ELIXIR] = elixir->lApplyValue;
		long known = 0;
		for (int i = 0; i < PLAYERBOT_ELEMENT_SRC_OTHER; ++i)
			known += src[i];
		src[PLAYERBOT_ELEMENT_SRC_OTHER] = (long)ch->GetPoint(point) - known;
	}

	// (6) The census: the Yohara bots online with a hunt element, per element.
	// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: with the sources' averages (src=[...]) and how many pieces hold the line at its
	// top: the talisman (tal_top), the armour / bracelet / helmet (gear_top), the costume and hairstyle (cos_top) - each
	// "at the top / able to roll it".
	void TickPlayerBotElementCensus(DWORD dwNow)
	{
		TPlayerBotElementStats& st = s_kPlayerBotElementStats;
		if (st.dwCensusAt == 0)
		{
			st.dwCensusAt = dwNow + PLAYERBOT_ELEMENT_CENSUS_MS;
			return;
		}
		if ((int)(dwNow - st.dwCensusAt) < 0)
			return;
		st.dwCensusAt = dwNow + PLAYERBOT_ELEMENT_CENSUS_MS;
		const int E = PLAYERBOT_YOHARA_ELEMENTS;
		int bots[E] = { 0 }, minR[E], maxR[E] = { 0 };
		long long sumR[E] = { 0 }, sumSrc[E][PLAYERBOT_ELEMENT_SRC_COUNT];
		int pieces[E] = { 0 }, piecesCan[E] = { 0 }, piecesTop[E] = { 0 };
		int talTop[E] = { 0 }, talCan[E] = { 0 }, cosTop[E] = { 0 }, cosCan[E] = { 0 };
#ifdef MT2009_PLUS_BOT_COSTUME_RESIST_V1
		// MT2009_PLUS_BOT_COSTUME_RESIST_V1: the costume / hairstyle worn (cos_worn), with the hunt line at any value
		// (cos_line), with two lines or more (cos_2l), the body costume's Max HP at level 3+ (cos_hp of the costumes)
		int cosWorn[E] = { 0 }, cosLine[E] = { 0 }, cos2l[E] = { 0 }, cosHp[E] = { 0 }, cosBody[E] = { 0 };
#endif
		int elixirOn[E] = { 0 }, elixirStock[E] = { 0 }, materials[E] = { 0 }, over60[E] = { 0 }, over40[E] = { 0 };
		int none = 0, preparing = 0;
		for (int e = 0; e < E; ++e)
		{
			minR[e] = 1 << 30;
			for (int k = 0; k < PLAYERBOT_ELEMENT_SRC_COUNT; ++k)
				sumSrc[e][k] = 0;
		}
		static const BYTE s_abCostume[2] = { WEAR_COSTUME_BODY, WEAR_COSTUME_HAIR };
		for (std::map<DWORD, TPlayerBotHuntElement>::iterator it = s_mapPlayerBotHuntElement.begin();
				it != s_mapPlayerBotHuntElement.end();)
		{
			if (dwNow - it->second.dwSeen > PLAYERBOT_ELEMENT_SEEN_MS)
			{
				s_mapPlayerBotHuntElement.erase(it++);
				continue;
			}
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			const int e = it->second.iElement;
			preparing += it->second.bPrepOpen ? 1 : 0;
			if (!ch || !ch->IsItemLoaded())
			{
				++it;
				continue;
			}
			if (e < 0)
			{
				++none;
				++it;
				continue;
			}
			const BYTE point = PLAYERBOT_YOHARA_RESIST_POINTS[e];
			const int r = (int)ch->GetPoint(point);
			++bots[e];
			sumR[e] += r;
			minR[e] = std::min(minR[e], r);
			maxR[e] = std::max(maxR[e], r);
			over60[e] += r >= 60 ? 1 : 0;
			over40[e] += r >= 40 ? 1 : 0;
			long src[PLAYERBOT_ELEMENT_SRC_COUNT];
			GetPlayerBotElementResistSources(ch, point, src);
			for (int k = 0; k < PLAYERBOT_ELEMENT_SRC_COUNT; ++k)
				sumSrc[e][k] += src[k];
			for (int i = 0; i < 3; ++i)
			{
				LPITEM item = ch->GetWear(PLAYERBOT_ELEMENT_GEAR_WEARS[i]);
				if (!item || item->GetAttributeSetIndex() < 0 || !IsPlayerBotApplyOnAttrSet(point, item->GetAttributeSetIndex()))
					continue;
				++piecesCan[e];
				const long line = GetPlayerBotWornResistLine(ch, PLAYERBOT_ELEMENT_GEAR_WEARS[i], point);
				if (line > 0)
					++pieces[e];
				const long top = GetPlayerBotYoharaTopLineValue(item, point);
				if (top > 0 && line >= top)
					++piecesTop[e];
			}
			LPITEM tal = ch->GetWear(WEAR_PENDANT);
			if (tal && tal->GetAttributeSetIndex() >= 0 && IsPlayerBotApplyOnAttrSet(point, tal->GetAttributeSetIndex()))
			{
				++talCan[e];
				const long top = GetPlayerBotYoharaTopLineValue(tal, point);
				if (top > 0 && GetPlayerBotYoharaPieceLine(tal, point) >= top)
					++talTop[e];
			}
			for (int i = 0; i < 2; ++i)
			{
				LPITEM item = ch->GetWear(s_abCostume[i]);
#ifdef MT2009_PLUS_BOT_COSTUME_RESIST_V1
				if (item)
				{
					++cosWorn[e];
					cos2l[e] += item->GetAttributeCount() >= 2 ? 1 : 0;
					cosLine[e] += GetPlayerBotYoharaPieceLine(item, point) > 0 ? 1 : 0;
					if (s_abCostume[i] == WEAR_COSTUME_BODY)
					{
						++cosBody[e];
						cosHp[e] += HasPlayerBotCostumeGoodMaxHp(item) ? 1 : 0;
					}
				}
#endif
				if (!item || item->GetAttributeSetIndex() < 0 || !IsPlayerBotApplyOnAttrSet(point, item->GetAttributeSetIndex()))
					continue;
				++cosCan[e];
				const long top = GetPlayerBotYoharaTopLineValue(item, point);
				if (top > 0 && GetPlayerBotYoharaPieceLine(item, point) >= top)
					++cosTop[e];
			}
			elixirOn[e] += ch->FindAffect(AFFECT_BLEND, point) ? 1 : 0;
			elixirStock[e] += (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_RESIST_ELIXIRS[e]);
			materials[e] += (int)ch->CountSpecifyItem(PLAYERBOT_YSHOP_MATERIAL_VNUM);
			++it;
		}
		std::string line;
		char buf[768];
		int total = 0;
		for (int e = 0; e < E; ++e)
		{
			if (bots[e] == 0)
				continue;
			total += bots[e];
			std::string src;
			for (int k = 0; k < PLAYERBOT_ELEMENT_SRC_COUNT; ++k)
			{
				char one[32];
				snprintf(one, sizeof(one), "%s%s=%lld", k ? " " : "", PLAYERBOT_ELEMENT_SRC_NAMES[k], sumSrc[e][k] / bots[e]);
				src += one;
			}
			snprintf(buf, sizeof(buf), " %s=[bots=%d resist_avg=%lld min=%d max=%d ge60=%d ge40=%d src=[%s] lines=%d/%d "
					"gear_top=%d/%d tal_top=%d/%d cos_top=%d/%d elixir_on=%d stock_avg=%d.%d materials_avg=%d]",
					PLAYERBOT_YOHARA_ELEMENT_NAMES[e], bots[e], sumR[e] / bots[e], minR[e], maxR[e], over60[e], over40[e],
					src.c_str(), pieces[e], piecesCan[e], piecesTop[e], piecesCan[e], talTop[e], talCan[e], cosTop[e], cosCan[e],
					elixirOn[e], elixirStock[e] / bots[e], (elixirStock[e] * 10 / bots[e]) % 10, materials[e] / bots[e]);
#ifdef MT2009_PLUS_BOT_COSTUME_RESIST_V1
			{
				std::string one(buf);
				if (!one.empty() && one[one.size() - 1] == ']')
					one.erase(one.size() - 1);
				snprintf(buf, sizeof(buf), "%s cos_worn=%d cos_line=%d cos_2l=%d cos_hp=%d/%d]", one.c_str(), cosWorn[e],
						cosLine[e], cos2l[e], cosHp[e], cosBody[e]);
			}
#endif
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
			// MT2009_PLUS_BOT_ELEMENT_RESIST_V3: the elixir tick's looks since the last census - the uptime on the element's
			// map (alive: on or drunk of all the looks there) and every outcome by name
			{
				const unsigned int* looks = s_aPlayerBotElixirLooks[e];
				const unsigned int on = looks[PLAYERBOT_ELIXIR_ON] + looks[PLAYERBOT_ELIXIR_DRUNK];
				const unsigned int alive = on + looks[PLAYERBOT_ELIXIR_NO_STOCK] + looks[PLAYERBOT_ELIXIR_USE_FAILED];
				std::string one(buf);
				if (!one.empty() && one[one.size() - 1] == ']')
					one.erase(one.size() - 1);
				std::string why;
				for (int k = 0; k < PLAYERBOT_ELIXIR_COUNT; ++k)
				{
					char part[40];
					snprintf(part, sizeof(part), "%s%s=%u", k ? " " : "", PLAYERBOT_ELIXIR_REASON_NAMES[k], looks[k]);
					why += part;
				}
				snprintf(buf, sizeof(buf), "%s elixir_up=%u%% elixir_looks=[%s]]", one.c_str(), alive ? on * 100 / alive : 0,
						why.c_str());
			}
#endif
			line += buf;
		}
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
		for (int e = 0; e < E; ++e)
			for (int k = 0; k < PLAYERBOT_ELIXIR_COUNT; ++k)
				s_aPlayerBotElixirLooks[e][k] = 0;
		{
			const TPlayerBotElementMoveStats& mv = s_kPlayerBotElementMoves;
			char moves[192];
			snprintf(moves, sizeof(moves), " moves=[flips_up=%u flips_free=%u kept_tie=%u blocked_down=%u pick_held=%u second_set=%u]",
					mv.flipsUp, mv.flipsFree, mv.keptTie, mv.blockedDown, mv.pickSkipped, mv.secondSet);
			line = moves + line;
		}
#endif
#ifdef MT2009_PLUS_BOT_COSTUME_RESIST_V1
		// MT2009_PLUS_BOT_COSTUME_RESIST_V1: the costume pass' rolls and finishes since the start, by reason and piece
		{
			static const char* const s_aszKinds[3] = { "body", "hair", "weapon" };
			std::string cos;
			for (int k = 0; k < 3; ++k)
			{
				std::string one;
				for (int ev = PLAYERBOT_COSEV_NONE + 1; ev < PLAYERBOT_COSEV_COUNT; ++ev)
				{
					if (!s_aPlayerBotCostumeEvents[k][ev])
						continue;
					char part[48];
					snprintf(part, sizeof(part), "%s%s=%u", one.empty() ? "" : " ", PLAYERBOT_COSEV_NAMES[ev],
							s_aPlayerBotCostumeEvents[k][ev]);
					one += part;
				}
				if (!one.empty())
					cos += std::string(" ") + s_aszKinds[k] + "=[" + one + "]";
			}
			if (!cos.empty())
				sys_log(0, "PLAYERBOT_COSTUME_BONUS: census%s", cos.c_str());
		}
#endif
		if (total == 0 && none == 0 && st.prepared == 0)
			return;
		sys_log(0, "PLAYERBOT_ELEMENT: census bots=%d no_element=%d preparing=%d changes=%u prepared=%u ready=%u no_stones=%u "
				"timeouts=%u urgent=%u same_element=%u elixirs_at_move=%u%s",
				total, none, preparing, st.changes, st.prepared, st.ready, st.noStones, st.timeouts, st.urgent,
				st.sameElement, st.elixirsAtMove, line.c_str());
	}

#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
	// MT2009_PLUS_BOT_ELEMENT_RESIST_V3: the map pick's element rule (playerbot_yohara_sungma.h). count: only the census's
	// count of a pick that the rule held (the answer false).
	bool IsPlayerBotSungmaElementMoveAllowed(LPCHARACTER ch, long toMap, bool count)
	{
		if (count)
		{
			++s_kPlayerBotElementMoves.pickSkipped;
			return false;
		}
		if (!ch || !IsPlayerBotYoharaBonusMember(ch))
			return true;
		std::map<DWORD, TPlayerBotHuntElement>::const_iterator it = s_mapPlayerBotHuntElement.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotHuntElement.end() || it->second.iElement < 0)
			return true;
		const long base = toMap >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? toMap / 10000 : toMap;
		const int toSlot = GetPlayerBotSungmaSlot(base), fromSlot = GetPlayerBotSungmaSlot(it->second.lMap);
		if (toSlot < 0 || fromSlot < 0 || toSlot >= fromSlot)
			return true;	// up the maps, the same map, or nothing to judge by
		if (IsPlayerBotElementInMapTie(base, it->second.iElement))
			return true;	// a map of its element
		const int e = ChoosePlayerBotHuntElement(base, ch->GetPlayerID());
		return e >= 0 && HasPlayerBotElementSecondSet(ch, (BYTE)(e + 1));
	}

	// One elixir of the vnum drunk when the point's blend effect is gone: the tick's outcome.
	int DrinkPlayerBotElixirKind(LPCHARACTER ch, DWORD vnum, BYTE point, long map, int e, bool power)
	{
		if (ch->FindAffect(AFFECT_BLEND, point))
			return PLAYERBOT_ELIXIR_ON;
		LPITEM item = ch->FindSpecifyItem(vnum);
		if (!item || item->GetSocket(0) == 0)
			return PLAYERBOT_ELIXIR_NO_STOCK;
		const int value = (int)item->GetSocket(1), seconds = (int)item->GetSocket(2);
		if (!ch->UseItem(TItemPos(INVENTORY, item->GetCell())) || !ch->FindAffect(AFFECT_BLEND, point))
			return PLAYERBOT_ELIXIR_USE_FAILED;
		++s_uPlayerBotYoharaElixirs;
		sys_log(0, "PLAYERBOT_ELEMENTS: elixir pid=%u name=%s map=%ld element=%s%s vnum=%u value=%d seconds=%d left=%d via=tick",
				ch->GetPlayerID(), ch->GetName(), map, PLAYERBOT_YOHARA_ELEMENT_NAMES[e], power ? " kind=power" : "", vnum,
				value, seconds, (int)ch->CountSpecifyItem(vnum));
		return PLAYERBOT_ELIXIR_DRUNK;
	}

	// From the top of the bot's tick (playerbot_manager.cpp, beside the dragon stone deck): a bot with a hunt element,
	// alive on the Sung Ma map its element is for, drinks that element's resistance elixir (and its power elixir) as
	// soon as the effect is gone - in a fight too, as a player does. Every PLAYERBOT_ELEMENT_ELIXIR_TICK_MS a bot.
	void ManagePlayerBotHuntElixirTick(LPCHARACTER ch, DWORD dwNow)
	{
		TickPlayerBotElementCensus(dwNow);
		if (!ch || !ch->IsPC() || !ch->IsItemLoaded())
			return;
		std::map<DWORD, TPlayerBotHuntElement>::iterator it = s_mapPlayerBotHuntElement.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotHuntElement.end())
		{
			if (!IsPlayerBotYoharaBonusMember(ch))
				return;
			GetPlayerBotHuntElementIndex(ch);	// the element's record made
			it = s_mapPlayerBotHuntElement.find(ch->GetPlayerID());
			if (it == s_mapPlayerBotHuntElement.end())
				return;
		}
		if (it->second.iElement < 0 && it->second.dwAt != 0 && get_dword_time() - it->second.dwAt < PLAYERBOT_ELEMENT_CACHE_MS)
			return;	// no hunt element now
		if (it->second.dwNextElixir != 0 && (int)(dwNow - it->second.dwNextElixir) < 0)
			return;
		it->second.dwNextElixir = dwNow + PLAYERBOT_ELEMENT_ELIXIR_TICK_MS;
		const int e = GetPlayerBotHuntElementIndex(ch);
		if (e < 0 || e >= PLAYERBOT_YOHARA_ELEMENTS)
			return;
		unsigned int* looks = s_aPlayerBotElixirLooks[e];
		const long map = GetPlayerBotYoharaElementMap(ch);
		const long here = ch->GetMapIndex();
		if (map == 0 || GetPlayerBotYoharaElementSlot(here) < 0 ||
				GetPlayerBotYoharaElementSlot(here) != GetPlayerBotYoharaElementSlot(map))
		{
			++looks[PLAYERBOT_ELIXIR_OFF_MAP];	// a village, Dongan's errand, a trip, the way
			return;
		}
		if (ch->IsDead() || ch->GetHP() <= 0)
		{
			++looks[PLAYERBOT_ELIXIR_DEAD];
			return;
		}
		++looks[DrinkPlayerBotElixirKind(ch, PLAYERBOT_YOHARA_RESIST_ELIXIRS[e], PLAYERBOT_YOHARA_RESIST_POINTS[e], map, e, false)];
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_ELEMENTS_V1)
		DrinkPlayerBotElixirKind(ch, PLAYERBOT_YOHARA_POWER_ELIXIRS[e], (BYTE)(POINT_ENCHANT_ELECT + e), map, e, true);
#endif
	}
#endif
}

#endif
