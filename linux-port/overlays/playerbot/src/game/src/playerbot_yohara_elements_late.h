#ifndef __INC_METIN2_PLAYERBOT_YOHARA_ELEMENTS_LATE_H__
#define __INC_METIN2_PLAYERBOT_YOHARA_ELEMENTS_LATE_H__

// MT2009_PLUS_BOT_YOHARA_ELEMENTS_V1: the part of playerbot_yohara_elements.h that reads the Sung Ma state
// (playerbot_yohara_bots.h, playerbot_yohara_sungma.h, playerbot_yohara_g0.h) - included after them.

namespace
{
	// The elixirs of resistance (eliksiry-yohary.md): Odp. na Pioruny, Ogien, Lod, Pln. Wiatr, Ziemie, Mrok - in the
	// table's element order.
	const DWORD PLAYERBOT_YOHARA_RESIST_ELIXIRS[PLAYERBOT_YOHARA_ELEMENTS] = { 50838, 50836, 50837, 50839, 50840, 50841 };
	const BYTE PLAYERBOT_YOHARA_RESIST_POINTS[PLAYERBOT_YOHARA_ELEMENTS] = {
		POINT_RESIST_ELEC, POINT_RESIST_FIRE, POINT_RESIST_ICE, POINT_RESIST_WIND, POINT_RESIST_EARTH, POINT_RESIST_DARK };
	// MT2009_PLUS_BOT_YOHARA_SHOP_V1: the elixirs of power (Piorunowej, Ognistej, Mroznej, Pln. Wiatru, Ziemi, Mrocznej Mocy)
	// - the element's power (POINT_ENCHANT_ELECT..DARK, the talismans' points), drunk the same way; made at Dongan's
	// exchange (playerbot_yohara_shop.h).
	const DWORD PLAYERBOT_YOHARA_POWER_ELIXIRS[PLAYERBOT_YOHARA_ELEMENTS] = { 50832, 50830, 50831, 50833, 50834, 50835 };
	const DWORD PLAYERBOT_YOHARA_ELEMENTS_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_YOHARA_ELEMENTS_SEEN_MS = 4 * 60 * 1000;

	long GetPlayerBotYoharaElementMap(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC())
			return 0;
		const DWORD pid = ch->GetPlayerID();
		// The stay's map on the Yohara core (Dongan's errand is not a stay on Dongan).
		std::map<DWORD, TPlayerBotYoharaResident>::const_iterator r = s_mapPlayerBotYoharaResident.find(pid);
		if (r != s_mapPlayerBotYoharaResident.end() && r->second.iPurpose == YOHARA_PURPOSE_SUNGMA &&
				GetPlayerBotYoharaElementSlot(r->second.lMap) >= 0)
			return r->second.lMap;
		// A trade trip's bot in its first village: the map it goes back to.
		std::map<DWORD, TPlayerBotSungmaTradeHome>::const_iterator t = s_mapPlayerBotSungmaTradeHome.find(pid);
		if (t != s_mapPlayerBotSungmaTradeHome.end() && GetPlayerBotYoharaElementSlot(t->second.lBackMap) >= 0)
			return t->second.lBackMap;
		const long here = ch->GetMapIndex();
		if (GetPlayerBotYoharaElementSlot(here) >= 0)
			return here;
		// A Champion of the top level in a village: its band's map (the G0 rule's - where it is going).
		if (IsPlayerBotVillageMap(here) && IsPlayerBotSungmaWillUser(ch))
		{
			const int slot = GetPlayerBotG0BandSlot(ch);
			if (slot >= 0)
				return PLAYERBOT_SUNGMA_MAPS[slot].lMap;
		}
		return 0;
	}

	// The expected bonus (GetPlayerBotTalismanGain's hundredths of a percent) of a Talizman Woli's random element line
	// (server-patches/talizmanwoli: power 1-24 of one element, POINT_ENCHANT_ELECT..DARK) on the bot's map - the
	// engine adds it to the element power like a talisman's.
	long long GetPlayerBotWillTalismanElementGain(LPCHARACTER ch, LPITEM item)
	{
		long long best = 0;
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_ELEMENTS_V1)
		int share[PLAYERBOT_TALISMAN_ELEMENTS];
		GetPlayerBotTalismanMapShares(ch, share);
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		{
			const int type = (int)item->GetAttributeType(i);
			if (type >= POINT_ENCHANT_ELECT && type <= POINT_ENCHANT_DARK)
				best = std::max<long long>(best, GetPlayerBotTalismanGain(type - POINT_ENCHANT_ELECT, (int)item->GetAttributeValue(i), share));
		}
#endif
		return best;
	}

	// D15, the owner's "regula automatyczna" - the pendant slot's one rule, for the equipment pass
	// (GetPlayerBotEquipmentScore) and the talisman's light pass (WearPlayerBotBestTalisman, by the same score):
	//   * a Talizman Woli while the bot, its worn pendant's Will taken out, lacks that Will for the map of its Champion
	//     band (GetPlayerBotG0WillTalismanScore) - over any element talisman; the Will it makes up first, then its
	//     element line on the bot's map (plan 8.2: "the one whose random element suits the map"). The same answer
	//     whichever pendant it wears, so no swapping back and forth;
	//   * else every pendant by its expected element bonus on the bot's map (the Sung Ma map's table on Yohara): an
	//     element talisman by GetPlayerBotTalismanScore, a Talizman Woli of a Champion by its element line the same way;
	//     the worn one stays on a tie.
	// False: not a pendant of these (a Talizman Woli of a bot that is no Champion: its lines, as any piece).
	bool GetPlayerBotPendantScore(LPCHARACTER ch, LPITEM item, long long& score)
	{
		if (!ch || !item)
			return false;
		if (IsPlayerBotTalismanItem(item))
		{
			score = GetPlayerBotTalismanScore(ch, item);
			return true;
		}
		if (GetPlayerBotWillTalismanKind(item->GetVnum()) < 0)
			return false;
		const long long elementGain = GetPlayerBotWillTalismanElementGain(ch, item);
		const long long plus = (long long)(item->GetVnum() % 10);
		long long willShort = 0;
		if (GetPlayerBotG0WillTalismanScore(ch, item, willShort))
		{
			const long long made = (willShort - PLAYERBOT_G0_WILL_TALISMAN_SHORT_SCORE) / 1000;
			score = PLAYERBOT_G0_WILL_TALISMAN_SHORT_SCORE + made * 100000 + elementGain * 10 + plus;
			return true;
		}
		if (!IsPlayerBotSungmaWillUser(ch))
			return false;
		score = 1 + elementGain * 1000 + plus;
		return true;
	}

	struct TPlayerBotYoharaElementsSeen
	{
		DWORD dwAt;
		long lMap;
		int iKind;	// 0 nothing worn, 1 a talisman of the map's element, 2 of another element, 3 a Talizman Woli, 4 other
	};
	std::map<DWORD, TPlayerBotYoharaElementsSeen> s_mapPlayerBotYoharaElementsSeen;
	DWORD s_dwPlayerBotYoharaElementsCensusAt = 0;
	unsigned int s_uPlayerBotYoharaElixirs = 0;

	void LogPlayerBotYoharaElementsCensus(DWORD dwNow)
	{
		for (int slot = 0; slot < PLAYERBOT_YOHARA_ELEMENT_MAP_COUNT; ++slot)
		{
			const long map = PLAYERBOT_YOHARA_ELEMENT_MAPS[slot].lMap;
			int kinds[5] = { 0, 0, 0, 0, 0 };
			int bots = 0;
			for (std::map<DWORD, TPlayerBotYoharaElementsSeen>::const_iterator it = s_mapPlayerBotYoharaElementsSeen.begin();
					it != s_mapPlayerBotYoharaElementsSeen.end(); ++it)
			{
				if (it->second.lMap != map || (int)(dwNow - it->second.dwAt) > (int)PLAYERBOT_YOHARA_ELEMENTS_SEEN_MS)
					continue;
				++bots;
				++kinds[std::max(0, std::min(4, it->second.iKind))];
			}
			if (bots == 0)
				continue;
			sys_log(0, "PLAYERBOT_ELEMENTS: census map=%ld bots=%d element=%d other_element=%d will=%d none=%d other=%d top=%s elixirs=%u",
					map, bots, kinds[1], kinds[2], kinds[3], kinds[0], kinds[4],
					GetPlayerBotYoharaTopElement(map) >= 0 ? PLAYERBOT_YOHARA_ELEMENT_NAMES[GetPlayerBotYoharaTopElement(map)] : "-",
					s_uPlayerBotYoharaElixirs);
		}
		for (std::map<DWORD, TPlayerBotYoharaElementsSeen>::iterator it = s_mapPlayerBotYoharaElementsSeen.begin();
				it != s_mapPlayerBotYoharaElementsSeen.end();)
		{
			if ((int)(dwNow - it->second.dwAt) > (int)PLAYERBOT_YOHARA_ELEMENTS_SEEN_MS)
				s_mapPlayerBotYoharaElementsSeen.erase(it++);
			else
				++it;
		}
	}

	// From the talisman's light pass (playerbot_workshop.h): on its Sung Ma map, the elixirs of resistance to the
	// map's elements whose effect is gone, if the bot has them; the pendant noted for the census.
	void ManagePlayerBotYoharaElements(LPCHARACTER ch, DWORD dwNow)
	{
		if (s_dwPlayerBotYoharaElementsCensusAt == 0 || (int)(dwNow - s_dwPlayerBotYoharaElementsCensusAt) >= 0)
		{
			if (s_dwPlayerBotYoharaElementsCensusAt != 0)
				LogPlayerBotYoharaElementsCensus(dwNow);
			s_dwPlayerBotYoharaElementsCensusAt = dwNow + PLAYERBOT_YOHARA_ELEMENTS_CENSUS_MS;
		}
		TickPlayerBotElementCensus(dwNow);	// MT2009_PLUS_BOT_ELEMENT_RESIST_V1
		if (!ch || !ch->IsItemLoaded() || ch->IsDead())
			return;
		const long map = GetPlayerBotYoharaElementMap(ch);
		const long here = ch->GetMapIndex();
		if (map == 0 || GetPlayerBotYoharaElementSlot(here) != GetPlayerBotYoharaElementSlot(map))
			return;	// in a village, or on Dongan's errand: nothing to drink, nothing to count
		int share[PLAYERBOT_YOHARA_ELEMENTS];
		GetPlayerBotYoharaMapShares(map, share);
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V1: a bot with a hunt element drinks that element's elixirs only (the owner:
		// one element, everything for it) - the table's shares stay the census's.
		const int hunt = (int)GetPlayerBotHuntElement(ch) - 1;
		bool drink[PLAYERBOT_YOHARA_ELEMENTS];
		for (int i = 0; i < PLAYERBOT_YOHARA_ELEMENTS; ++i)
			drink[i] = hunt >= 0 ? i == hunt : share[i] >= PLAYERBOT_YOHARA_ELEMENT_DEFENCE_PERCENT;

		TPlayerBotYoharaElementsSeen& seen = s_mapPlayerBotYoharaElementsSeen[ch->GetPlayerID()];
		seen.dwAt = dwNow;
		seen.lMap = map;
		LPITEM worn = ch->GetWear(WEAR_PENDANT);
		const int e = worn ? GetPlayerBotTalismanElementOf(worn->GetVnum()) : -1;
		seen.iKind = !worn ? 0 : e >= 0 ? (share[e] >= PLAYERBOT_YOHARA_ELEMENT_DEFENCE_PERCENT ? 1 : 2) :
				GetPlayerBotWillTalismanKind(worn->GetVnum()) >= 0 ? 3 : 4;

		for (int i = 0; i < PLAYERBOT_YOHARA_ELEMENTS; ++i)
		{
			if (!drink[i] || ch->FindAffect(AFFECT_BLEND, PLAYERBOT_YOHARA_RESIST_POINTS[i]))
				continue;
			LPITEM item = ch->FindSpecifyItem(PLAYERBOT_YOHARA_RESIST_ELIXIRS[i]);
			if (!item || item->GetSocket(0) == 0)
				continue;
			const int value = (int)item->GetSocket(1), seconds = (int)item->GetSocket(2);
			if (!ch->UseItem(TItemPos(INVENTORY, item->GetCell())) ||
					!ch->FindAffect(AFFECT_BLEND, PLAYERBOT_YOHARA_RESIST_POINTS[i]))
				continue;
			++s_uPlayerBotYoharaElixirs;
			sys_log(0, "PLAYERBOT_ELEMENTS: elixir pid=%u name=%s map=%ld element=%s vnum=%u value=%d seconds=%d left=%d",
					ch->GetPlayerID(), ch->GetName(), map, PLAYERBOT_YOHARA_ELEMENT_NAMES[i], PLAYERBOT_YOHARA_RESIST_ELIXIRS[i],
					value, seconds, (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_RESIST_ELIXIRS[i]));
		}
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_ELEMENTS_V1)
		// MT2009_PLUS_BOT_YOHARA_SHOP_V1: and the elixirs of power of the same elements, the same way.
		for (int i = 0; i < PLAYERBOT_YOHARA_ELEMENTS; ++i)
		{
			const BYTE point = (BYTE)(POINT_ENCHANT_ELECT + i);
			if (!drink[i] || ch->FindAffect(AFFECT_BLEND, point))
				continue;
			LPITEM item = ch->FindSpecifyItem(PLAYERBOT_YOHARA_POWER_ELIXIRS[i]);
			if (!item || item->GetSocket(0) == 0)
				continue;
			const int value = (int)item->GetSocket(1), seconds = (int)item->GetSocket(2);
			if (!ch->UseItem(TItemPos(INVENTORY, item->GetCell())) || !ch->FindAffect(AFFECT_BLEND, point))
				continue;
			++s_uPlayerBotYoharaElixirs;
			sys_log(0, "PLAYERBOT_ELEMENTS: elixir pid=%u name=%s map=%ld element=%s kind=power vnum=%u value=%d seconds=%d left=%d",
					ch->GetPlayerID(), ch->GetName(), map, PLAYERBOT_YOHARA_ELEMENT_NAMES[i], PLAYERBOT_YOHARA_POWER_ELIXIRS[i],
					value, seconds, (int)ch->CountSpecifyItem(PLAYERBOT_YOHARA_POWER_ELIXIRS[i]));
		}
#endif
	}
}

#endif
