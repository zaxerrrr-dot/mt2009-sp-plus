#ifndef __INC_METIN2_PLAYERBOT_YOHARA_ELEMENTS_H__
#define __INC_METIN2_PLAYERBOT_YOHARA_ELEMENTS_H__

// MT2009_PLUS_BOT_YOHARA_ELEMENTS_V1: the elements of the Sung Ma maps for the bots (plan-boty-yohara.md, section 8,
// "Faza 6 - zywioly"; the owner's decisions of 21 October: D14 "Tak, lekko", D15 "regula automatyczna").
//
// * The map's elements are a table (plan 8.1/2.1: the shares of the ordinary monsters' elements, counted from the
//   location sheet's spawn points and mob_proto's flags, no bosses and no Metins) - not the live count of
//   playerbot_talismans.h, which on a map of two elements of near equal share (Twierdza 54/45, Yilad 54/46, the
//   Wawoz/Rozpadlina/Zejscie ice and lightning) followed what happened to be alive and swapped the talisman back and
//   forth (measured 22 October 18:29-19:36, game3: 81 pendant changes for ~100 bots, 24 bots changed it twice or
//   more on one map, 3 three times on Yilad - Mrok > Lod > Ziemia > Mrok).
// * The map a bot's elements are taken for (GetPlayerBotYoharaElementMap): its Sung Ma stay's map (Dongan's errand
//   does not count as Dongan), on the home core a trade trip's map to go back to, else the Sung Ma map it stands on,
//   else - a Champion of the top level in a village - the map of its Champion band (the G0 rule's map). Anything
//   else: no Yohara map, the rules of the old world as they were.
// * D14: a resistance to an element of that map (a share of PLAYERBOT_YOHARA_ELEMENT_DEFENCE_PERCENT or more - the
//   plan's "Obrona" column) weighs PLAYERBOT_YOHARA_RESIST_FACTOR times its usual weight, in the equipment score
//   (ScorePlayerBotApply) and in the bonus reroll (ScorePlayerBotBonusLineRaw): the flat resistance, its 6th/7th
//   "+x%" line and the hit buff's resistance. Nowhere else.
// * D14: one spare talisman - the best for the next map up - stays in the bag (IsPlayerBotKeptTalisman), and a
//   talisman on a stand that betters the map's or the spare's is bought (WantsPlayerBotTalismanOffer, the talisman's
//   price rules); the elixirs of resistance (eliksiry-yohary.md, 50836-50841) of the map's elements are drunk on the
//   map when the bot has them and their effect is gone.
// * D15 - one rule, GetPlayerBotPendantScore (playerbot_talismans.h): the pendant slot's score for both the equipment
//   pass and the talisman's light pass.
// The log: PLAYERBOT_ELEMENTS (elixir, talisman bought, census a map every 10 minutes).

namespace
{
	// In the order of playerbot_talismans.h's PLAYERBOT_TALISMAN_ELEMENT: lightning, fire, ice, wind, earth, dark.
	const int PLAYERBOT_YOHARA_ELEMENTS = 6;
	const int PLAYERBOT_YOHARA_ELEMENT_DEFENCE_PERCENT = 25;
	const int PLAYERBOT_YOHARA_RESIST_FACTOR = 2;
	const char* const PLAYERBOT_YOHARA_ELEMENT_NAMES[PLAYERBOT_YOHARA_ELEMENTS] = { "lightning", "fire", "ice", "wind", "earth", "dark" };

	struct TPlayerBotYoharaElementMap
	{
		long lMap;
		BYTE abShare[PLAYERBOT_YOHARA_ELEMENTS];	// percent of the map's ordinary monsters
	};

	// plan-boty-yohara.md 2.1 / 8.1 (tools/yohara_lokacje/lokalizacje.tsv and the test's mob_proto flags).
	const TPlayerBotYoharaElementMap PLAYERBOT_YOHARA_ELEMENT_MAPS[] = {
		//                                    lightning fire ice wind earth dark
		{ PLAYERBOT_MAP_SUNGMA_TWIERDZA,     {  0,  0,  54,  0,   0, 45 } },
		{ PLAYERBOT_MAP_SUNGMA_DONGAN,       {  0, 58,   0,  0,   0, 41 } },
		{ PLAYERBOT_MAP_SUNGMA_SEOGANLAND,   {  0,  0,   0,  0, 100,  0 } },
		{ PLAYERBOT_MAP_SUNGMA_NAMGAN,       {  0, 21,   0, 34,  16, 27 } },
		{ PLAYERBOT_MAP_SUNGMA_YILAD,        {  0,  0,   0,  0,  46, 54 } },
		{ PLAYERBOT_MAP_SUNGMA_WAWOZ,        { 48,  0,  52,  0,   0,  0 } },
		{ PLAYERBOT_MAP_SUNGMA_ROZPADLINA,   { 48,  0,  51,  0,   0,  0 } },
		{ PLAYERBOT_MAP_SUNGMA_SCHRONIENIE,  {  0,  0, 100,  0,   0,  0 } },
		{ PLAYERBOT_MAP_SUNGMA_ZEJSCIE,      { 50,  0,  50,  0,   0,  0 } },
	};
	const int PLAYERBOT_YOHARA_ELEMENT_MAP_COUNT =
			(int)(sizeof(PLAYERBOT_YOHARA_ELEMENT_MAPS) / sizeof(PLAYERBOT_YOHARA_ELEMENT_MAPS[0]));

	int GetPlayerBotYoharaElementSlot(long mapIndex)
	{
		const long base = mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? mapIndex / 10000 : mapIndex;
		for (int i = 0; i < PLAYERBOT_YOHARA_ELEMENT_MAP_COUNT; ++i)
			if (PLAYERBOT_YOHARA_ELEMENT_MAPS[i].lMap == base)
				return i;
		return -1;
	}

	// The table's shares of a Sung Ma map; false (all zero) for any other map.
	bool GetPlayerBotYoharaMapShares(long mapIndex, int share[PLAYERBOT_YOHARA_ELEMENTS])
	{
		const int slot = GetPlayerBotYoharaElementSlot(mapIndex);
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			share[e] = slot >= 0 ? (int)PLAYERBOT_YOHARA_ELEMENT_MAPS[slot].abShare[e] : 0;
		return slot >= 0;
	}

	// The map's element of the largest share (the first on a tie), -1 for none.
	int GetPlayerBotYoharaTopElement(long mapIndex)
	{
		int share[PLAYERBOT_YOHARA_ELEMENTS];
		if (!GetPlayerBotYoharaMapShares(mapIndex, share))
			return -1;
		int best = -1;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			if (share[e] > 0 && (best < 0 || share[e] > share[best]))
				best = e;
		return best;
	}

	// The element a resistance line is against (the flat line, the 6th/7th "+x%" line, the hit buff's), -1 for any
	// other line.
	int GetPlayerBotResistLineElement(BYTE type)
	{
		switch (type)
		{
			case APPLY_RESIST_ELEC: case POINT_RESIST_PER_ELEC: case POINT_HIT_BUFF_RESIST_ELEC: return 0;
			case APPLY_RESIST_FIRE: case POINT_RESIST_PER_FIRE: case POINT_HIT_BUFF_RESIST_FIRE: return 1;
			case APPLY_RESIST_ICE: case POINT_RESIST_PER_ICE: case POINT_HIT_BUFF_RESIST_ICE: return 2;
			case APPLY_RESIST_WIND: case POINT_RESIST_PER_WIND: case POINT_HIT_BUFF_RESIST_WIND: return 3;
			case APPLY_RESIST_EARTH: case POINT_RESIST_PER_EARTH: case POINT_HIT_BUFF_RESIST_EARTH: return 4;
			case APPLY_RESIST_DARK: case POINT_RESIST_PER_DARK: case POINT_HIT_BUFF_RESIST_DARK: return 5;
			default: return -1;
		}
	}

	// Defined in playerbot_yohara_elements_late.h (after the Sung Ma state of playerbot_yohara_sungma.h): the Sung Ma
	// map whose elements the bot dresses for, 0 for none; the elixirs and the census, from the talisman's light pass.
	long GetPlayerBotYoharaElementMap(LPCHARACTER ch);
	void ManagePlayerBotYoharaElements(LPCHARACTER ch, DWORD dwNow);
	// playerbot_yohara_sungma.h and playerbot_yohara_g0.h, for the spare's map and the pendant rule.
	bool IsPlayerBotSungmaMapOn(long mapIndex);
	int GetPlayerBotWillTalismanKind(DWORD vnum);

	// D14: the weight factor of a line for this bot - PLAYERBOT_YOHARA_RESIST_FACTOR for a resistance to an element of
	// its Yohara map, 1 for anything else.
	int GetPlayerBotYoharaResistFactor(LPCHARACTER ch, BYTE type)
	{
		const int e = GetPlayerBotResistLineElement(type);
		if (e < 0 || !ch)
			return 1;
		int share[PLAYERBOT_YOHARA_ELEMENTS];
		if (!GetPlayerBotYoharaMapShares(GetPlayerBotYoharaElementMap(ch), share))
			return 1;
		return share[e] >= PLAYERBOT_YOHARA_ELEMENT_DEFENCE_PERCENT ? PLAYERBOT_YOHARA_RESIST_FACTOR : 1;
	}
}

#endif
