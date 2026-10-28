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
// 3. The costume and the hairstyle: this world's item_attr rolls no element resistance on a costume or a hairstyle
//    (costume_body / costume_hair are 0 for all six; the 6th/7th pool none either) and the costume bonus transfer
//    (70065 at the blacksmith) only moves costume lines between costumes - so there is no resistance to put there.
//    What the costume sets do roll for Yohara is taken instead (IsPlayerBotYoharaCostumeLineGood): the costume Max HP,
//    arrow and magic resistance, the hairstyle arrow dodge and magic resistance - at level 3 of the table or more,
//    and the hunt element's resistance too should an operator ever add it to those columns. The reagents are the
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
		TPlayerBotHuntElement() : lMap(0), iElement(-1), dwAt(0), dwSeen(0), lPrepFrom(0), lPrepTo(0), iPrepFrom(-1),
			dwPrepSince(0), bPrepWait(false), bPrepOpen(false) {}
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
		const int e = ChoosePlayerBotHuntElement(base, ch->GetPlayerID());
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
		if (!point || !IsPlayerBotElementOnGear(e))
			return true;
		bool missing = false;
		for (int i = 0; i < 3; ++i)
		{
			LPITEM item = ch->GetWear(PLAYERBOT_ELEMENT_GEAR_WEARS[i]);
			// the pieces the bonus pass works on (CollectPlayerBotYoharaBonusPieces) - the rest waits for nobody
			if (!item || item->GetAttributeSetIndex() < 0 || !IsPlayerBotApplyOnAttrSet(point, item->GetAttributeSetIndex()) ||
					IS_SET(item->GetFlag(), ITEM_FLAG_IRREMOVABLE) || !CanPlayerBotTakeBonusStone(item) ||
					IsPlayerBotSidekickLockedItem(ch, item) || IsPlayerBotSidekickPinned(ch, item))
				continue;
			if (GetPlayerBotWornResistLine(ch, PLAYERBOT_ELEMENT_GEAR_WEARS[i], point) <= 0)
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
		for (int i = 0; i < 3; ++i)
		{
			LPITEM item = ch->GetWear(PLAYERBOT_ELEMENT_GEAR_WEARS[i]);
			const bool rolls = item && item->GetAttributeSetIndex() >= 0 && IsPlayerBotApplyOnAttrSet(point, item->GetAttributeSetIndex());
			if (!item)
				snprintf(buf, sizeof(buf), "%s%s:none", out.empty() ? "" : " ", s_aszNames[i]);
			else if (!rolls)
				snprintf(buf, sizeof(buf), "%s%s:n/a", out.empty() ? "" : " ", s_aszNames[i]);
			else
				snprintf(buf, sizeof(buf), "%s%s:%ld", out.empty() ? "" : " ", s_aszNames[i],
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
				snprintf(buf, sizeof(buf), " %s:%d/%d", s_aszCostume[i], CountPlayerBotGoodCostumeLines(ch, item),
						item->GetAttributeCount());
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
			FinishPlayerBotElementPrep(ch, h, noStones ? "no_stones" : (IsPlayerBotElementOnGear(e) ? "ready" : "no_gear_line"), dwNow);
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

	// (6) The census: the Yohara bots online with a hunt element, per element.
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
		int bots[PLAYERBOT_YOHARA_ELEMENTS] = { 0 }, minR[PLAYERBOT_YOHARA_ELEMENTS], maxR[PLAYERBOT_YOHARA_ELEMENTS] = { 0 };
		long long sumR[PLAYERBOT_YOHARA_ELEMENTS] = { 0 }, sumGear[PLAYERBOT_YOHARA_ELEMENTS] = { 0 };
		int pieces[PLAYERBOT_YOHARA_ELEMENTS] = { 0 }, piecesCan[PLAYERBOT_YOHARA_ELEMENTS] = { 0 };
		int elixirOn[PLAYERBOT_YOHARA_ELEMENTS] = { 0 }, elixirStock[PLAYERBOT_YOHARA_ELEMENTS] = { 0 };
		int none = 0, preparing = 0;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			minR[e] = 1 << 30;
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
			sumGear[e] += GetPlayerBotGearResist(ch, point);
			for (int i = 0; i < 3; ++i)
			{
				LPITEM item = ch->GetWear(PLAYERBOT_ELEMENT_GEAR_WEARS[i]);
				if (!item || item->GetAttributeSetIndex() < 0 || !IsPlayerBotApplyOnAttrSet(point, item->GetAttributeSetIndex()))
					continue;
				++piecesCan[e];
				if (GetPlayerBotWornResistLine(ch, PLAYERBOT_ELEMENT_GEAR_WEARS[i], point) > 0)
					++pieces[e];
			}
			elixirOn[e] += ch->FindAffect(AFFECT_BLEND, point) ? 1 : 0;
			elixirStock[e] += (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_RESIST_ELIXIRS[e]);
			++it;
		}
		std::string line;
		char buf[192];
		int total = 0;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
		{
			if (bots[e] == 0)
				continue;
			total += bots[e];
			snprintf(buf, sizeof(buf), " %s=[bots=%d resist_avg=%lld min=%d max=%d gear_avg=%lld lines=%d/%d elixir_on=%d stock_avg=%d]",
					PLAYERBOT_YOHARA_ELEMENT_NAMES[e], bots[e], sumR[e] / bots[e], minR[e], maxR[e], sumGear[e] / bots[e],
					pieces[e], piecesCan[e], elixirOn[e], elixirStock[e] / bots[e]);
			line += buf;
		}
		if (total == 0 && none == 0 && st.prepared == 0)
			return;
		sys_log(0, "PLAYERBOT_ELEMENT: census bots=%d no_element=%d preparing=%d changes=%u prepared=%u ready=%u no_stones=%u "
				"timeouts=%u urgent=%u same_element=%u elixirs_at_move=%u%s",
				total, none, preparing, st.changes, st.prepared, st.ready, st.noStones, st.timeouts, st.urgent,
				st.sameElement, st.elixirsAtMove, line.c_str());
	}
}

#endif
