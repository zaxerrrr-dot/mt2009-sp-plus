#ifndef __INC_METIN2_PLAYERBOT_ELEMENT_MAPS_H__
#define __INC_METIN2_PLAYERBOT_ELEMENT_MAPS_H__

// MT2009_PLUS_BOT_ELEMENT_MAPS_V1 - element resistance on the maps 1-120 (the owner, 31 October 2026: "Naucz boty
// uzywac bonusow odpornosci na zywioly na mapach 1-120": Loch Pajakow 2 and 3 fire ~60%, Zaklety Las wind 75%, Grota
// Wygnancow lightning 75%, the other maps with a dominant element by our data).
//
// The engine (playerbot_elements.cpp, ElementsAttackBonus, called from battle.cpp CalcAttBonus): a monster carrying
// element flags (setRaceFlag bits 11-16) hits a player for R% less, R = the largest of min(Bonus67Total(victim,
// POINT_RESIST_<element>), 80) over the monster's elements - the full percent in both bonus modes (BonusModeElementResist,
// since 23 October), capped at 80. Bonus67Total = GetPoint (worn proto applies - an accessory's sockets raise them by
// 10/20/40% (aiAccessorySocketEffectivePct), rolled lines, costume, talisman, dragon stones, elixir, element stone, pet)
// + the hit buff of the point + its 6th/7th "+x% of the total" line. Nothing else (battle.cpp's own 30% line is
// commented out). So 1% of resistance is 1% less damage from every monster of that element - on a map where they all
// are, as good as 1% more Max HP.
//
// The maps (PLAYERBOT_ELEMENT_MAP_ROWS): the element, the bot's target resistance on it (want) and the minimum to pick
// or stay on it (gate; 0 - no gate, the target is only a gear goal). The element share is LIVE - the mob_proto flags of
// the map's ordinary spawns (the samples: the most common vnums of its regen.txt, groups and group_groups resolved,
// weighed by their spawn count), so the same table is right in both modes: in M2_BONUS_MODE=mt2009 the Spider
// Dungeons, Hwang or Zaklety Las carry no element (zywioly_moby.sql) and their gate is off; the Grotto is lightning in
// both. A row counts while its element is PLAYERBOT_ELEMENT_MAP_ACTIVE_SHARE of the samples or more.
// MT2009_PLUS_BOT_ELEMENT_MAP_GATES_V1: the gate column below is the code's column again (it was 0 everywhere since the
// owner's "no gates yet" of 31 October while this table said 60/75); it is read only with the event flag
// m2_bot_element_map_gates = 1 (GetPlayerBotElementMapRowGate) - off, every gate is 0 as before.
// MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1 (the owner, 8 November 2026): the five progression maps below (spider_v2 / v3
// fire, grotto_v1 / v2 lightning, zaklety wind) are gated at 40 by default (event flag m2_bot_element_progress_off 1 -
// the paragraph above again), with early access, retreats and the next map's resistance built ahead - the progression
// block after GetPlayerBotElementMapResist.
//   map  name          element    want gate  shares measured in the test world (global, 31 October)
//    71  spider_v2     fire        60   60   fire 100%            lv 60-68   (the owner)
//   217  spider_v3     fire        60   60   fire 100%            lv 60-68   (the owner)
//   353  zaklety       wind        75   75   wind 100%            lv 100-108 (the owner)
//    72  grotto_v1     lightning   75   75   lightning 53 ice 47  lv 81-89   (the owner; mt2009: lightning 100)
//    73  grotto_v2     lightning   75   75   lightning 100%       lv 87-97   (the owner)
//    62  fire_land     fire        50    0   fire 100%            lv 69-72
//    70  giantland     lightning   50    0   lightning 100%       lv 66-77
//    65  hwang         wind        40    0   wind 100%            lv 52-61
//    64  orc_valley    wind        25    0   wind 98%             lv 29-51
//   3/23/43 (a3/b3/c3) wind        10    0   wind ~51%            lv 18-36
//   360  arezzo_exp    lightning   30    0   lightning 100%       lv 43-49
//    61  sohan         ice         15    0   ice 63%              lv 49-66   (ice: talisman only)
//    66  demon_tower   dark        15    0   dark 100%            lv 57-69   (dark: talisman only)
//   216  catacomb      dark        20    0   dark 100%            lv 79-83
//    67  forest        earth       15    0   earth 100%           lv 71-77   (earth: talisman only)
//    68  red_forest    earth       20    0   earth 100%           lv 80-88
// Fire Land and Kraina Gigantow have a gear goal and no gate: on 31 October 375 bots hunted Fire Land with a median
// fire resistance of 0 (max 25) - a gate there would empty the map in one pass. The gates are on fire, lightning and wind only - the elements the armour, helmet and bracelet roll in global mode;
// ice, earth and dark stay talisman-only (the owner's rule of 28 October, playerbot_element_resist.h) and get a gear
// goal, never a gate. The loot-run maps 301-304 are of two elements each (none over 80%): no row.
//
// Where it is wired (all of it for a bot without a Yohara hunt element - a Yohara bot keeps its own rules):
//   * the hunting map (playerbot_travel.h, GetPlayerBotFrontierMapForLevel -> GatePlayerBotElementMap): a gated map
//     the bot's resistance is under is not picked - the bot takes the highest other ground its level opens that it
//     passes (GetPlayerBotElementMapFallback) - and a bot standing on it leaves once it is PLAYERBOT_ELEMENT_MAP_STAY_SLACK
//     under the gate (an elixir or a hit buff running out does not bounce it). With no other ground at all (a bot of
//     90+ over the Red Forest's ceiling and under Ochao's 95) it keeps the map rather than stand in its village
//     ("no_fallback"). The map it wanted stays its goal;
//   * the goal (GetPlayerBotElementMapGoal): the wanted map's row (else the map it stands on) - its element, want and
//     gate, and the bot's resistance now;
//   * the gear's worth of the goal element's resistance, short of the want: one point is worth 1% of the bot's Max HP
//     (by the map's share) - the equipment score (ScorePlayerBotApply: a necklace or bracelet whose own apply is the
//     element - Miedziany Naszyjnik lightning, Drewniany fire, Srebrny wind, up to 10 at +9 and +4 more with three
//     sockets - and the stalls' pieces, the market's buy, read it), the boots' score (Bambusowe fire, Drewniane
//     lightning, Wyszywane Zlotem wind: their own apply counts now, GetPlayerBotBootsScore) and the bonus line's score
//     (ScorePlayerBotBonusLineRaw: the reroll keeps such a line); at or over the want, half of it;
//   * the reroll's stop rule (HasPlayerBotFinishedBonus): an armour, helmet or bracelet whose attribute set rolls the
//     goal's resistance (global: fire / lightning / wind 2-15 on those three) is not finished without that line at
//     the table's level-4 value (10 in global) while the bot is short of the want - with Max HP for the armour and
//     the bracelet, alone for the helmet. Only with the element's gate or a want of 25 or more (a 10% goal on a level
//     20 map does not reroll anything). The ItemShop V3 stone goals follow the pass's own answer;
//   * the costume and hairstyle (GetPlayerBotCostumeBonusNeed): in global the costume and hairstyle pools roll fire,
//     lightning and wind (costume_attr_global.sql) - the goal's line is the first one, to its top, within
//     PLAYERBOT_ELEMENT_MAP_COSTUME_CHANGES changes of the piece;
//   * Kamien Ochrony Zywiolow (39120, +10 to all six, playerbot_element_stones.h): bought in the ItemShop (never given)
//     by a bot short of a gated map's resistance.
// The log: PLAYERBOT_ELEMENT map_gate (the pick's decision when it changes: map, element, resist, want, gate, share,
// decision pick / skip / stay / leave and the fallback) and PLAYERBOT_ELEMENT map_census every 10 minutes (per map:
// bots aiming at it, below the gate, resistance avg / min / max).
//
// An implementation fragment: included by playerbot_manager.cpp right after playerbot_yohara_elements.h (before the
// gear, bonus and travel passes that ask it), in the anonymous namespace.

#include "playerbot_bonus67.h"

namespace
{
	const int PLAYERBOT_ELEMENT_MAP_ACTIVE_SHARE = 40;
	const int PLAYERBOT_ELEMENT_MAP_STAY_SLACK = 5;
	const int PLAYERBOT_ELEMENT_MAP_RESIST_CAP = 80;
	const int PLAYERBOT_ELEMENT_MAP_REROLL_WANT = 25;
	const int PLAYERBOT_ELEMENT_MAP_COSTUME_CHANGES = 40;
	const DWORD PLAYERBOT_ELEMENT_MAP_SHARE_MS = 60 * 1000;
	const DWORD PLAYERBOT_ELEMENT_MAP_GOAL_MS = 20 * 60 * 1000;
	const DWORD PLAYERBOT_ELEMENT_MAP_CENSUS_MS = 10 * 60 * 1000;
	const int PLAYERBOT_ELEMENT_MAP_SAMPLES = 8;

	// lightning, fire, ice, wind, earth, dark - PLAYERBOT_YOHARA_ELEMENT_NAMES' order
	const BYTE PLAYERBOT_ELEMENT_MAP_POINTS[6] = { POINT_RESIST_ELEC, POINT_RESIST_FIRE, POINT_RESIST_ICE, POINT_RESIST_WIND,
		POINT_RESIST_EARTH, POINT_RESIST_DARK };
	const DWORD PLAYERBOT_ELEMENT_MAP_FLAGS[6] = { RACE_FLAG_ATT_ELEC, RACE_FLAG_ATT_FIRE, RACE_FLAG_ATT_ICE, RACE_FLAG_ATT_TEMPLE,
		RACE_FLAG_ATT_EARTH, RACE_FLAG_ATT_DARK };
	enum { PLAYERBOT_EM_ELEC = 0, PLAYERBOT_EM_FIRE, PLAYERBOT_EM_ICE, PLAYERBOT_EM_WIND, PLAYERBOT_EM_EARTH, PLAYERBOT_EM_DARK };

	struct TPlayerBotElementMapSample { DWORD vnum; BYTE weight; };
	struct TPlayerBotElementMapRow
	{
		long lMap;
		const char* szName;
		int iElement;
		int iWant;
		int iGate;
		TPlayerBotElementMapSample aSamples[PLAYERBOT_ELEMENT_MAP_SAMPLES];
	};

	// The samples: the map's most common ordinary monsters (tools: regen.txt + group.txt + group_group.txt of the test
	// world, 31 October 2026), percent of its spawns - the rest of a map's spawns are rarer kinds of the same mix.
	const TPlayerBotElementMapRow PLAYERBOT_ELEMENT_MAP_ROWS[] = {
		{ PLAYERBOT_MAP_SPIDER_V2, "spider_v2", PLAYERBOT_EM_FIRE, 60, 60,
			{ { 2133, 15 }, { 2061, 14 }, { 2064, 14 }, { 2062, 13 }, { 2132, 10 }, { 2063, 10 }, { 2065, 10 }, { 2134, 9 } } },
		{ PLAYERBOT_MAP_SPIDER_V3, "spider_v3", PLAYERBOT_EM_FIRE, 60, 60,
			{ { 2072, 28 }, { 2073, 25 }, { 2074, 20 }, { 2071, 19 } } },
		{ PLAYERBOT_MAP_ZAKLETY, "zaklety", PLAYERBOT_EM_WIND, 75, 75,
			{ { 6402, 37 }, { 6401, 29 }, { 6403, 25 } } },
		{ PLAYERBOT_MAP_GROTTO_V1, "grotto_v1", PLAYERBOT_EM_ELEC, 75, 75,
			{ { 2401, 32 }, { 2402, 17 }, { 1136, 9 }, { 1131, 8 }, { 1132, 7 }, { 1137, 6 }, { 1133, 6 }, { 1135, 6 } } },
		{ PLAYERBOT_MAP_GROTTO_V2, "grotto_v2", PLAYERBOT_EM_ELEC, 75, 75,
			{ { 2411, 28 }, { 2401, 23 }, { 2402, 18 }, { 2412, 10 }, { 2413, 10 }, { 2403, 7 } } },
		{ PLAYERBOT_MAP_FIRE_LAND, "fire_land", PLAYERBOT_EM_FIRE, 50, 0,
			{ { 2201, 26 }, { 2203, 25 }, { 2202, 20 }, { 2204, 20 } } },
		{ PLAYERBOT_MAP_GIANTLAND, "giantland", PLAYERBOT_EM_ELEC, 50, 0,
			{ { 1601, 25 }, { 1602, 25 }, { 1401, 19 }, { 1402, 12 }, { 1603, 12 } } },
		{ PLAYERBOT_MAP_HWANG, "hwang", PLAYERBOT_EM_WIND, 40, 0,
			{ { 774, 10 }, { 776, 9 }, { 777, 9 }, { 1301, 9 }, { 1332, 9 }, { 775, 8 }, { 1303, 7 }, { 732, 7 } } },
		{ PLAYERBOT_MAP_ORC_VALLEY, "orc_valley", PLAYERBOT_EM_WIND, 25, 0,
			{ { 632, 12 }, { 633, 9 }, { 751, 8 }, { 631, 8 }, { 634, 6 }, { 704, 5 }, { 656, 4 }, { 636, 4 } } },
		{ 3, "a3", PLAYERBOT_EM_WIND, 10, 0,
			{ { 502, 12 }, { 402, 9 }, { 501, 8 }, { 403, 8 }, { 401, 7 }, { 453, 6 }, { 454, 6 }, { 301, 5 } } },
		{ 23, "b3", PLAYERBOT_EM_WIND, 10, 0,
			{ { 502, 12 }, { 402, 10 }, { 501, 9 }, { 403, 8 }, { 401, 7 }, { 453, 6 }, { 454, 6 }, { 551, 5 } } },
		{ 43, "c3", PLAYERBOT_EM_WIND, 10, 0,
			{ { 502, 12 }, { 501, 9 }, { 402, 9 }, { 403, 8 }, { 401, 7 }, { 453, 6 }, { 454, 6 }, { 551, 6 } } },
		{ PLAYERBOT_MAP_AREZZO_CYCLOPS, "arezzo_cyclops", PLAYERBOT_EM_ELEC, 30, 0,
			{ { 9601, 43 }, { 9602, 29 }, { 9603, 14 }, { 9605, 7 } } },
		{ PLAYERBOT_MAP_SOHAN, "sohan", PLAYERBOT_EM_ICE, 15, 0,
			{ { 1171, 16 }, { 1106, 14 }, { 1105, 12 }, { 933, 6 }, { 1104, 6 }, { 1107, 5 }, { 902, 5 }, { 936, 5 } } },
		{ PLAYERBOT_MAP_DEMON_TOWER, "demon_tower", PLAYERBOT_EM_DARK, 15, 0,
			{ { 1002, 42 }, { 1001, 31 }, { 1003, 19 } } },
		{ PLAYERBOT_MAP_CATACOMB, "catacomb", PLAYERBOT_EM_DARK, 20, 0,
			{ { 2501, 38 }, { 2502, 33 }, { 2503, 15 }, { 2504, 12 } } },
		{ PLAYERBOT_MAP_FOREST, "forest", PLAYERBOT_EM_EARTH, 15, 0,
			{ { 2302, 28 }, { 2301, 26 }, { 2303, 23 }, { 2304, 14 } } },
		{ PLAYERBOT_MAP_RED_FOREST, "red_forest", PLAYERBOT_EM_EARTH, 20, 0,
			{ { 2312, 39 }, { 2313, 26 }, { 2314, 17 }, { 2311, 11 } } },
	};
	const int PLAYERBOT_ELEMENT_MAP_ROW_COUNT = (int)(sizeof(PLAYERBOT_ELEMENT_MAP_ROWS) / sizeof(PLAYERBOT_ELEMENT_MAP_ROWS[0]));

	// MT2009_PLUS_BOT_ELEMENT_MAP_GATES_V1: the table's gate column is the owner's (31 October: Loch Pajakow fire 60,
	// Zaklety Las wind 75, the Grotto lightning 75) - and the owner's word of the same day, "no gates yet", stands: the
	// gate is read only with the event flag m2_bot_element_map_gates set (1); otherwise 0 (the want stays a gear goal).
	// Measured on the test on 7 November 14:54 (PLAYERBOT_ELEMENT map_census, game1 / channel2): the bots aiming at
	// those maps held 8-24 of the element on average (spider_v2 9, zaklety 9, grotto_v1 11-12, grotto_v2 11-24, max 80) -
	// the gates on would empty the five maps in one pass, so they wait for the owner's word.
	bool ArePlayerBotElementMapGatesOn()
	{
		static DWORD s_dwAt = 0;
		static bool s_bOn = false;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 5000)
		{
			s_bOn = quest::CQuestManager::instance().GetEventFlag("m2_bot_element_map_gates") != 0;
			s_dwAt = now ? now : 1;
		}
		return s_bOn;
	}

	// MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1 (below): the progression maps' own gate (fire 40 the Spider Dungeons, ...), 0 for
	// any other map or with the progression off.
	int GetPlayerBotElementProgressGateForMap(long map);

	int GetPlayerBotElementMapRowGate(int row)
	{
		if (row < 0 || row >= PLAYERBOT_ELEMENT_MAP_ROW_COUNT)
			return 0;
		// MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1: the owner's progression of 8 November (default on) takes the row's gate
		// from its table; the old 60/75 column is read only with it off and m2_bot_element_map_gates = 1.
		const int progress = GetPlayerBotElementProgressGateForMap(PLAYERBOT_ELEMENT_MAP_ROWS[row].lMap);
		if (progress > 0)
			return progress;
		if (!ArePlayerBotElementMapGatesOn())
			return 0;
		return PLAYERBOT_ELEMENT_MAP_ROWS[row].iGate;
	}

	const char* GetPlayerBotElementMapElementName(int e)
	{
		static const char* const s_aszNames[6] = { "lightning", "fire", "ice", "wind", "earth", "dark" };
		return e >= 0 && e < 6 ? s_aszNames[e] : "-";
	}

	long GetPlayerBotElementMapBase(long map)
	{
		return map >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? map / 10000 : map;
	}

	int FindPlayerBotElementMapRow(long map)
	{
		const long base = GetPlayerBotElementMapBase(map);
		for (int i = 0; base > 0 && i < PLAYERBOT_ELEMENT_MAP_ROW_COUNT; ++i)
			if (PLAYERBOT_ELEMENT_MAP_ROWS[i].lMap == base)
				return i;
		return -1;
	}

	// The row's element share now, by the live mob_proto of its samples (0-100), cached a minute.
	int GetPlayerBotElementMapShare(int row)
	{
		static int s_aiShare[64];
		static DWORD s_adwAt[64];
		if (row < 0 || row >= PLAYERBOT_ELEMENT_MAP_ROW_COUNT || row >= 64)
			return 0;
		const DWORD now = get_dword_time();
		if (s_adwAt[row] != 0 && now - s_adwAt[row] < PLAYERBOT_ELEMENT_MAP_SHARE_MS)
			return s_aiShare[row];
		const TPlayerBotElementMapRow& r = PLAYERBOT_ELEMENT_MAP_ROWS[row];
		int total = 0, with = 0;
		for (int i = 0; i < PLAYERBOT_ELEMENT_MAP_SAMPLES && r.aSamples[i].vnum; ++i)
		{
			const CMob* mob = CMobManager::instance().Get(r.aSamples[i].vnum);
			if (!mob)
				continue;
			total += r.aSamples[i].weight;
			if (mob->m_table.dwRaceFlag & PLAYERBOT_ELEMENT_MAP_FLAGS[r.iElement])
				with += r.aSamples[i].weight;
		}
		s_aiShare[row] = total > 0 ? with * 100 / total : 0;
		s_adwAt[row] = now ? now : 1;
		return s_aiShare[row];
	}

	// MT2009_PLUS_BOT_GEAR_FLIPFLOP_V1: while the equipment pass weighs two pieces for one wear slot, the resistance
	// below leaves out what the piece worn in that slot gives (its proto applies and rolled lines of the point). The
	// line's worth halves at the want (GetPlayerBotElementMapPointInHp), and the worn piece counted itself towards it:
	// worn, a bracelet / necklace / pair of boots with the goal's resistance lifted the bot to the want and its own line
	// was worth half, so a piece without it outscored it; off, the bot fell under the want and the line was worth full
	// again - the two took turns in the slot. Without the slot's own piece both are weighed against the same total.
	// Set by PlayerBotElementMapSlotScope only around the scoring; -1 otherwise.
	LPCHARACTER s_pPlayerBotElementMapScoringCh = NULL;
	int s_iPlayerBotElementMapScoringWear = -1;

	struct PlayerBotElementMapSlotScope
	{
		LPCHARACTER m_pPrevCh;
		int m_iPrevWear;
		PlayerBotElementMapSlotScope(LPCHARACTER ch, int wearCell)
			: m_pPrevCh(s_pPlayerBotElementMapScoringCh), m_iPrevWear(s_iPlayerBotElementMapScoringWear)
		{
			s_pPlayerBotElementMapScoringCh = ch;
			s_iPlayerBotElementMapScoringWear = wearCell;
		}
		~PlayerBotElementMapSlotScope()
		{
			s_pPlayerBotElementMapScoringCh = m_pPrevCh;
			s_iPlayerBotElementMapScoringWear = m_iPrevWear;
		}
	};

	int GetPlayerBotElementMapPieceValue(LPITEM item, WORD point)
	{
		if (!item || !item->GetProto())
			return 0;
		int value = 0;
		for (int i = 0; i < ITEM_APPLY_MAX_NUM; ++i)
			if (item->GetProto()->aApplies[i].bType == point)
				value += (int)item->GetProto()->aApplies[i].lValue;
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			if (item->GetAttributeType(i) == point)
				value += (int)item->GetAttributeValue(i);
		return value;
	}

	// The resistance the engine counts against a monster of element e now (ElementsAttackBonus): capped at 80.
	int GetPlayerBotElementMapResist(LPCHARACTER ch, int e)
	{
		if (!ch || e < 0 || e >= 6)
			return 0;
		int total = Bonus67Total(ch, PLAYERBOT_ELEMENT_MAP_POINTS[e]);
		if (ch == s_pPlayerBotElementMapScoringCh && s_iPlayerBotElementMapScoringWear >= 0 &&
				s_iPlayerBotElementMapScoringWear < WEAR_MAX_NUM)
			total -= GetPlayerBotElementMapPieceValue(ch->GetWear((BYTE)s_iPlayerBotElementMapScoringWear),
					PLAYERBOT_ELEMENT_MAP_POINTS[e]);
		return std::max(0, std::min(total, PLAYERBOT_ELEMENT_MAP_RESIST_CAP));
	}

	// ======================================================================================================================
	// MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1 - the resistance progression of the maps 1-120 (the owner, 8 November 2026:
	// "Pierwsza odpornosc, jaka powinny wykorzystywac, to odpornosc na ogien w Lochu Pajakow v2. Jesli bot jest ubrany w
	// odpornosc na ogien (40%), to moze juz tam expic, nawet na 45 poziomie. Jesli nie daje rady, wraca na swoje
	// expowisko. Kolejna odpornosc to odpornosc na blyskawice w Grocie Wygnancow. Nastepna - odpornosc na wiatr w Zakletym
	// Lesie. Potem juz odpornosci na dane zywioly danych map Yohary").
	//
	//   step  map              element    early  normal entry (panel row)          gate   prebuild window
	//   0     71  spider_v2    fire        45    54 (spider2)                       40     40-80
	//   0     217 spider_v3    fire        -     66 (spider3, by the V2 record)     40
	//   1     72  grotto_v1    lightning   72    78 (grotto1)                       40     67-99
	//   1     73  grotto_v2    lightning   80    84 (grotto2)                       40
	//   2     353 zaklety      wind        95    100 (env PLAYERBOT_ZAKLETY_MIN_LEVEL) 40  90-109
	//   3     the Sung Ma maps - a Yohara bot's hunt element (MT2009_PLUS_BOT_ELEMENT_RESIST_*, MT2009_PLUS_BOT_YRESIST):
	//         unchanged; a bot with a hunt element has no goal here (GetPlayerBotElementMapGoal) and no early access.
	// Lightning and wind take the owner's fire number (40): the same slots build any of the three to it (global
	// item_attr: armour, helmet, bracelet, costume, hairstyle and talisman roll fire / lightning / wind 2-15; ice, earth
	// and dark only on the talisman, 5-25), and so do the element items (the necklace and the boots of each element, 10
	// at +9) and Kamien Ochrony Zywiolow (+10 to all six).
	//
	//   * the gate: the table's row gate is this one (GetPlayerBotElementMapRowGate) - a bot under it does not pick the map
	//     and one standing on it leaves PLAYERBOT_ELEMENT_MAP_STAY_SLACK under (the old pass, GatePlayerBotElementMap,
	//     with its fallback); a resident of Zaklety Las is not asked where it stands (the Yohara stay moves it);
	//   * early: a bot from the map's early level, under its normal entry, at the gate, with the dungeon's gear (the
	//     Spider Dungeon's rule), no stone hunter and no retreat running, hunts the map in place of its draw's ground
	//     (ApplyPlayerBotElementProgressEarly, playerbot_travel.h; Zaklety Las in playerbot_yohara_bots.h); its hubs are
	//     read lower by the gap and its target reach is the normal entry's (GetPlayerBotTargetLevelDelta);
	//   * retreat ("jesli nie daje rady"): on a progression map PLAYERBOT_EPROG_DEATHS deaths or PLAYERBOT_EPROG_RETREATS
	//     HP retreats within PLAYERBOT_EPROG_WINDOW_MS - and for an early bot fewer than PLAYERBOT_EPROG_SLOW_KILLS kills
	//     in a window there - shut the map for the bot for PLAYERBOT_EPROG_SHUT_MIN minutes: the gate refuses it (an early
	//     bot gets its draw's ground back, one in the band the gate's fallback), then it may come back;
	//   * prebuild: within a step's window (its first early level - PLAYERBOT_EPROG_LEAD to its top) the bonus goal is the
	//     step's element (the latest step whose window holds the level) to the gate + PLAYERBOT_EPROG_PREBUILD_MARGIN - the
	//     reroll's stop rule, the line and apply scores (the element necklace / boots), the costume line and the
	//     protection stone (GetPlayerBotElementMapGoal's users) - unless the bot hunts or wants a gated map: its element
	//     is kept while it hunts there (one gear set below Yohara; the next element is built on the ground between).
	// Switches (event flags): m2_bot_element_progress_off 1 - all off (the old table, gates by m2_bot_element_map_gates);
	// m2_bot_element_progress_early_off / _prebuild_off / _retreat_off / _target_off 1 - one part;
	// m2_bot_element_progress_gate N (10-80) - the gate instead of 40; m2_bot_element_progress_shut_min N (10-1440).
	// The log: PLAYERBOT_EPROG early_pick / early_none / early_gear_short (a decision change, per bot), retreat, back;
	// PLAYERBOT_EPROG census every 10 minutes (per band and the totals).
	// ======================================================================================================================
	int ReadPlayerBotYoharaEnvInt(const char* name, int def, int lo, int hi);	// playerbot_yohara_bots.h
	bool IsPlayerBotYoharaBonusMember(LPCHARACTER ch);	// playerbot_yohara_bonus.h (a cohort member or a Champion)

	const int PLAYERBOT_EPROG_GATE = 40;
	const int PLAYERBOT_EPROG_LEAD = 5;
	const int PLAYERBOT_EPROG_PREBUILD_MARGIN = 5;
	const DWORD PLAYERBOT_EPROG_WINDOW_MS = 30 * 60 * 1000;
	const int PLAYERBOT_EPROG_DEATHS = 3;
	const int PLAYERBOT_EPROG_RETREATS = 8;
	const int PLAYERBOT_EPROG_SLOW_KILLS = 25;
	const int PLAYERBOT_EPROG_SHUT_MIN = 120;
	const DWORD PLAYERBOT_EPROG_CENSUS_MS = 10 * 60 * 1000;
	const size_t PLAYERBOT_EPROG_KILLS_KEPT = 64;
	// MT2009_PLUS_BOT_EPROG_STAY_FIX_V1: a record not touched on its map this long is a new visit (the bot was away -
	// an errand, the offline shop, a horse medal - and came back), whatever the off-map look below missed.
	const DWORD PLAYERBOT_EPROG_ABSENT_MS = 10 * 60 * 1000;
	// MT2009_PLUS_BOT_EPROG_STAY_FIX_V1: a party member's kill near the bot counts for it too (an assisting member lands
	// few last hits) - same map, this far.
	const int PLAYERBOT_EPROG_PARTY_KILL_RANGE = 5000;
	// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1 (the owner, 8 November 2026): a retreat of a bot that can afford more resistance
	// raises its target by this step up to this maximum (the slots' practical top: stone 10, pet 10, armour / helmet /
	// bracelet 15 each, the talisman, the costume and hairstyle) instead of shutting the map.
	const int PLAYERBOT_EPROG_BOOST_STEP = 10;
	const int PLAYERBOT_EPROG_BOOST_MAX = 65;
	const DWORD PLAYERBOT_EPROG_BOOST_KEEP_MS = 24U * 60U * 60U * 1000U;

	enum { PLAYERBOT_EPROG_ALL = 0, PLAYERBOT_EPROG_EARLY, PLAYERBOT_EPROG_PREBUILD, PLAYERBOT_EPROG_RETREAT,
		PLAYERBOT_EPROG_TARGET, PLAYERBOT_EPROG_STAYFIX, PLAYERBOT_EPROG_GEAR, PLAYERBOT_EPROG_BOOST, PLAYERBOT_EPROG_PARTS };

	struct TPlayerBotEProgMap
	{
		long lMap;
		int iStep;
		int iElement;
		int iEarly;	// 0: no early access (V3 comes by the V2 record)
		const char* szName;
	};
	const TPlayerBotEProgMap PLAYERBOT_EPROG_MAPS[] = {
		{ PLAYERBOT_MAP_SPIDER_V2, 0, PLAYERBOT_EM_FIRE, 45, "spider_v2" },
		{ PLAYERBOT_MAP_SPIDER_V3, 0, PLAYERBOT_EM_FIRE, 0, "spider_v3" },
		{ PLAYERBOT_MAP_GROTTO_V1, 1, PLAYERBOT_EM_ELEC, 72, "grotto_v1" },
		{ PLAYERBOT_MAP_GROTTO_V2, 1, PLAYERBOT_EM_ELEC, 80, "grotto_v2" },
		{ PLAYERBOT_MAP_ZAKLETY, 2, PLAYERBOT_EM_WIND, 95, "zaklety" },
	};
	const int PLAYERBOT_EPROG_MAP_COUNT = (int)(sizeof(PLAYERBOT_EPROG_MAPS) / sizeof(PLAYERBOT_EPROG_MAPS[0]));
	const int PLAYERBOT_EPROG_STEPS = 3;

	bool IsPlayerBotElementProgressOn(int part)
	{
		static const char* const s_aszFlags[PLAYERBOT_EPROG_PARTS] = { "m2_bot_element_progress_off",
			"m2_bot_element_progress_early_off", "m2_bot_element_progress_prebuild_off", "m2_bot_element_progress_retreat_off",
			"m2_bot_element_progress_target_off",
			// MT2009_PLUS_BOT_EPROG_STAY_FIX_V1 / MT2009_PLUS_BOT_EPROG_RESIST_GEAR_V1 / MT2009_PLUS_BOT_EPROG_BUY_MORE_V1
			"m2_bot_element_progress_stayfix_off", "m2_bot_element_progress_gear_off", "m2_bot_element_progress_boost_off" };
		static DWORD s_dwAt = 0;
		static bool s_abOn[PLAYERBOT_EPROG_PARTS] = { true, true, true, true, true, true, true, true };
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 5000)
		{
			s_dwAt = now ? now : 1;
			const bool all = quest::CQuestManager::instance().GetEventFlag(s_aszFlags[0]) == 0;
			s_abOn[0] = all;
			for (int i = 1; i < PLAYERBOT_EPROG_PARTS; ++i)
				s_abOn[i] = all && quest::CQuestManager::instance().GetEventFlag(s_aszFlags[i]) == 0;
		}
		return part >= 0 && part < PLAYERBOT_EPROG_PARTS && s_abOn[part];
	}

	// MT2009_PLUS_BOT_GATE55_FIRE_V1 (the owner, 8 November 2026; playerbot_progression_rules.h, FireAltLook): the
	// level-55 gate's alternative to helmet / armour / shield +6 - fire resistance >= min with the three at +plus.
	// Event flags: m2_bot_gate55_fire_off 1 - the old rule only; m2_bot_gate55_fire_min N (10-80, default 50);
	// m2_bot_gate55_fire_plus N (1-9, default 4). false: off (min / plus still answered).
	// MT2009_PLUS_BOT_GATE55_FIRE_ANYLEVEL_V1: *pAnyLevel - the alternative's three pieces of any item level (default on;
	// m2_bot_gate55_fire_anylevel_off 1: the rows' levels kept, as before).
	const int PLAYERBOT_GATE55_FIRE_LEVEL = 55;
	const int PLAYERBOT_GATE55_FIRE_MIN = 50;
	const int PLAYERBOT_GATE55_FIRE_PLUS = 4;
	bool GetPlayerBotGate55Fire(int* pMin = NULL, int* pPlus = NULL, bool* pAnyLevel = NULL)
	{
		static DWORD s_dwAt = 0;
		static bool s_bOn = true;
		static bool s_bAnyLevel = true;
		static int s_iMin = PLAYERBOT_GATE55_FIRE_MIN, s_iPlus = PLAYERBOT_GATE55_FIRE_PLUS;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 5000)
		{
			s_dwAt = now ? now : 1;
			quest::CQuestManager& q = quest::CQuestManager::instance();
			s_bOn = q.GetEventFlag("m2_bot_gate55_fire_off") == 0;
			const int fmin = q.GetEventFlag("m2_bot_gate55_fire_min");
			s_iMin = fmin >= 10 && fmin <= PLAYERBOT_ELEMENT_MAP_RESIST_CAP ? fmin : PLAYERBOT_GATE55_FIRE_MIN;
			const int fplus = q.GetEventFlag("m2_bot_gate55_fire_plus");
			s_iPlus = fplus >= 1 && fplus <= 9 ? fplus : PLAYERBOT_GATE55_FIRE_PLUS;
			s_bAnyLevel = q.GetEventFlag("m2_bot_gate55_fire_anylevel_off") == 0;
		}
		if (pMin)
			*pMin = s_iMin;
		if (pPlus)
			*pPlus = s_iPlus;
		if (pAnyLevel)
			*pAnyLevel = s_bAnyLevel;
		return s_bOn;
	}

	// playerbot_progression.h: the fire resistance a bot builds for the level-55 gate's alternative (held there with
	// helmet / armour / shield short of their rows, or passed by the alternative and still in the gate's window); 0 none.
	int GetPlayerBotGate55FireGoal(LPCHARACTER ch);

	int GetPlayerBotElementProgressGate()
	{
		static DWORD s_dwAt = 0;
		static int s_iGate = PLAYERBOT_EPROG_GATE;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 5000)
		{
			s_dwAt = now ? now : 1;
			const int flag = quest::CQuestManager::instance().GetEventFlag("m2_bot_element_progress_gate");
			s_iGate = flag >= 10 && flag <= PLAYERBOT_ELEMENT_MAP_RESIST_CAP ? flag : PLAYERBOT_EPROG_GATE;
		}
		return s_iGate;
	}

	DWORD GetPlayerBotElementProgressShutMs()
	{
		const int flag = quest::CQuestManager::instance().GetEventFlag("m2_bot_element_progress_shut_min");
		return (DWORD)(flag >= 10 && flag <= 24 * 60 ? flag : PLAYERBOT_EPROG_SHUT_MIN) * 60000U;
	}

	int FindPlayerBotElementProgressMap(long map)
	{
		const long base = GetPlayerBotElementMapBase(map);
		for (int i = 0; base > 0 && i < PLAYERBOT_EPROG_MAP_COUNT; ++i)
			if (PLAYERBOT_EPROG_MAPS[i].lMap == base)
				return i;
		return -1;
	}

	int GetPlayerBotElementProgressGateForMap(long map)
	{
		if (!IsPlayerBotElementProgressOn(PLAYERBOT_EPROG_ALL) || FindPlayerBotElementProgressMap(map) < 0)
			return 0;
		// MT2009_PLUS_BOT_GATE55_FIRE_V1: the Spider Dungeon V2 never asks more fire than the level-55 gate's
		// alternative - a bot let through 55 by it qualifies there (with m2_bot_element_progress_gate over the
		// alternative's minimum; at the defaults 40 < 50, unchanged)
		int fireMin = 0;
		if (GetPlayerBotElementMapBase(map) == PLAYERBOT_MAP_SPIDER_V2 && GetPlayerBotGate55Fire(&fireMin))
			return std::min(GetPlayerBotElementProgressGate(), fireMin);
		return GetPlayerBotElementProgressGate();
	}

	// The map's normal entry level (the panel's map table; Zaklety Las by its env, as playerbot_yohara_bots.h reads it).
	int GetPlayerBotElementProgressNormalLevel(int idx)
	{
		using namespace playerbot_progression;
		if (idx < 0 || idx >= PLAYERBOT_EPROG_MAP_COUNT)
			return 255;
		switch (PLAYERBOT_EPROG_MAPS[idx].lMap)
		{
			case PLAYERBOT_MAP_SPIDER_V2: return (int)MapFrom(MAP_SPIDER2);
			case PLAYERBOT_MAP_SPIDER_V3: return (int)MapFrom(MAP_SPIDER3);
			case PLAYERBOT_MAP_GROTTO_V1: return (int)MapFrom(MAP_GROTTO1);
			case PLAYERBOT_MAP_GROTTO_V2: return (int)MapFrom(MAP_GROTTO2);
			case PLAYERBOT_MAP_ZAKLETY:
			{
				static int s_iZaklety = -1;
				if (s_iZaklety < 0)
					s_iZaklety = ReadPlayerBotYoharaEnvInt("PLAYERBOT_ZAKLETY_MIN_LEVEL", PLAYERBOT_ZAKLETY_MIN_LEVEL,
							PLAYERBOT_OCHAO_MIN_LEVEL, PLAYERBOT_ZAKLETY_MAX_LEVEL);
				return s_iZaklety;
			}
			default: return 255;
		}
	}

	// The step's prebuild window: from its lowest early level (or normal entry) - PLAYERBOT_EPROG_LEAD to its top (the
	// Spider Dungeons' ceilings; the Grotto to Zaklety Las's entry; Zaklety Las to its band's end).
	void GetPlayerBotElementProgressStepWindow(int step, int& from, int& to)
	{
		using namespace playerbot_progression;
		from = 255;
		int zaklety = -1;
		for (int i = 0; i < PLAYERBOT_EPROG_MAP_COUNT; ++i)
		{
			if (PLAYERBOT_EPROG_MAPS[i].lMap == PLAYERBOT_MAP_ZAKLETY)
				zaklety = i;
			if (PLAYERBOT_EPROG_MAPS[i].iStep == step)
				from = std::min(from, PLAYERBOT_EPROG_MAPS[i].iEarly > 0 ? PLAYERBOT_EPROG_MAPS[i].iEarly
						: GetPlayerBotElementProgressNormalLevel(i));
		}
		from = std::max(1, from - PLAYERBOT_EPROG_LEAD);
		switch (step)
		{
			case 0: to = std::max((int)MapTo(MAP_SPIDER2), (int)MapTo(MAP_SPIDER3)); break;
			case 1: to = GetPlayerBotElementProgressNormalLevel(zaklety) - 1; break;
			default: to = PLAYERBOT_ZAKLETY_MAX_LEVEL; break;
		}
	}

	struct TPlayerBotEProgRecord
	{
		long lMap;			// the progression map (base) the bot was last seen on (0: none), and since when
		DWORD dwArrived;
		std::deque<DWORD> kills, deaths, retreats;
		std::map<long, DWORD> shut;	// map -> until (a retreat)
		long lEarlyMap;			// the early decision's memo for the log
		int iEarlyDecision;
		DWORD dwSeen;
		DWORD dwOnMapSeen;		// MT2009_PLUS_BOT_EPROG_STAY_FIX_V1: the last touch on lMap
		// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1: the raised resistance target after a retreat it could afford (0: none)
		int iBoostElement;
		int iBoostTarget;
		int iBoosts;
		DWORD dwBoostAt;
		bool bRefusedCounted;	// the census's distinct refused bots (this period)
		TPlayerBotEProgRecord() : lMap(0), dwArrived(0), lEarlyMap(-1), iEarlyDecision(-1), dwSeen(0), dwOnMapSeen(0),
			iBoostElement(-1), iBoostTarget(0), iBoosts(0), dwBoostAt(0), bRefusedCounted(false) {}
	};
	std::map<DWORD, TPlayerBotEProgRecord> s_mapPlayerBotEProg;

	struct TPlayerBotEProgStats
	{
		unsigned int early, retreatDeaths, retreatRetreats, retreatSlow, back, gateRefusals;
		// MT2009_PLUS_BOT_EPROG_STAY_FIX_V1: the refusals by bot and cause; the stale visits dropped
		unsigned int refusedBots, refusedShut, refusedResist, staleResets, partyKills;
		// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1: the retreats' actions
		unsigned int buyMore, buyMoreSm, buyMoreYang, leave, leaveMaxed, leaveNoFunds, leaveOff;
		TPlayerBotEProgStats() : early(0), retreatDeaths(0), retreatRetreats(0), retreatSlow(0), back(0), gateRefusals(0),
			refusedBots(0), refusedShut(0), refusedResist(0), staleResets(0), partyKills(0), buyMore(0), buyMoreSm(0),
			buyMoreYang(0), leave(0), leaveMaxed(0), leaveNoFunds(0), leaveOff(0) {}
	};
	TPlayerBotEProgStats s_kPlayerBotEProg;

	void PrunePlayerBotEProgWindow(std::deque<DWORD>& q, DWORD now)
	{
		while (!q.empty() && now - q.front() >= PLAYERBOT_EPROG_WINDOW_MS)
			q.pop_front();
	}

	// The bot's record, its presence on a progression map refreshed (another map starts the window again).
	// MT2009_PLUS_BOT_EPROG_STAY_FIX_V1 (the test of 8 November 2026, 09:40: every one of the early bots' slow_kills
	// retreats came 1 s after the bot came back to the Spider Dungeon V2 - "kills=0 on_map_min=78-130": the record was
	// touched only on the map, so a bot that went off for an errand (the offline shop, a horse medal, 20-45 min) and came
	// back found its old lMap, its old arrival and its kills pruned out of the window, and the coping check shut the map
	// at once. They killed fine there - GIVE_GOLD and CRUSH every few seconds.) Now a visit begins again after
	// PLAYERBOT_EPROG_ABSENT_MS without a touch on the map, and NotePlayerBotElementProgressAway ends it when the bot is
	// seen elsewhere.
	void ResetPlayerBotEProgVisit(TPlayerBotEProgRecord& r, long base, DWORD now)
	{
		r.lMap = base;
		r.dwArrived = now ? now : 1;
		r.kills.clear();
		r.deaths.clear();
		r.retreats.clear();
	}

	TPlayerBotEProgRecord* TouchPlayerBotEProg(LPCHARACTER ch, DWORD now)
	{
		if (!ch || !ch->IsPC() || s_mapPlayerBotAIStates.find(ch->GetPlayerID()) == s_mapPlayerBotAIStates.end())
			return NULL;
		TPlayerBotEProgRecord& r = s_mapPlayerBotEProg[ch->GetPlayerID()];
		r.dwSeen = now ? now : 1;
		const int idx = FindPlayerBotElementProgressMap(ch->GetMapIndex());
		const long base = idx >= 0 ? PLAYERBOT_EPROG_MAPS[idx].lMap : 0;
		if (base != r.lMap)
			ResetPlayerBotEProgVisit(r, base, now);
		else if (base != 0 && IsPlayerBotElementProgressOn(PLAYERBOT_EPROG_STAYFIX) && r.dwOnMapSeen != 0 &&
				now - r.dwOnMapSeen >= PLAYERBOT_EPROG_ABSENT_MS)
		{
			++s_kPlayerBotEProg.staleResets;
			ResetPlayerBotEProgVisit(r, base, now);
		}
		if (base != 0)
			r.dwOnMapSeen = now ? now : 1;
		return &r;
	}

	// MT2009_PLUS_BOT_EPROG_STAY_FIX_V1: the bot is seen off its progression map - the visit is over (its next arrival
	// starts a new window). Cheap: a lookup, nothing for a bot without a record.
	void NotePlayerBotElementProgressAway(LPCHARACTER ch)
	{
		if (!ch || s_mapPlayerBotEProg.empty() || !IsPlayerBotElementProgressOn(PLAYERBOT_EPROG_STAYFIX))
			return;
		std::map<DWORD, TPlayerBotEProgRecord>::iterator it = s_mapPlayerBotEProg.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotEProg.end() || it->second.lMap == 0)
			return;
		if (FindPlayerBotElementProgressMap(ch->GetMapIndex()) >= 0)
			return;
		ResetPlayerBotEProgVisit(it->second, 0, get_dword_time());
		it->second.dwOnMapSeen = 0;
	}

	// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1: the raised target of the element (0: none, or it is a day old).
	int GetPlayerBotElementProgressBoostTarget(LPCHARACTER ch, int element)
	{
		if (!ch || element < 0 || s_mapPlayerBotEProg.empty() || !IsPlayerBotElementProgressOn(PLAYERBOT_EPROG_BOOST))
			return 0;
		std::map<DWORD, TPlayerBotEProgRecord>::const_iterator it = s_mapPlayerBotEProg.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotEProg.end() || it->second.iBoostElement != element || it->second.iBoostTarget <= 0 ||
				get_dword_time() - it->second.dwBoostAt >= PLAYERBOT_EPROG_BOOST_KEEP_MS)
			return 0;
		return it->second.iBoostTarget;
	}

	int GetPlayerBotElementProgressBoostStep()
	{
		const int flag = quest::CQuestManager::instance().GetEventFlag("m2_bot_element_progress_boost_step");
		return flag >= 5 && flag <= 30 ? flag : PLAYERBOT_EPROG_BOOST_STEP;
	}

	int GetPlayerBotElementProgressBoostMax()
	{
		const int flag = quest::CQuestManager::instance().GetEventFlag("m2_bot_element_progress_boost_max");
		return flag >= 45 && flag <= PLAYERBOT_ELEMENT_MAP_RESIST_CAP ? flag : PLAYERBOT_EPROG_BOOST_MAX;
	}

	// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1: the element shop's side (playerbot_element_shop.h): can the bot afford the
	// resistance to target now (SM by the plan within the step's budget, or yang for the Handlarka's costume lines)? If
	// so its record is made urgent again for that target, with the HP lines after it. *pTarget may come down to what the
	// SM plan reaches (at least +5). how: "sm", "yang" or "sm+yang"; why (false): "no_view", "no_sm", ...
	bool TryPlayerBotElementShopBoost(LPCHARACTER ch, int element, int* pTarget, const char** how, const char** why,
			long long* pCost);

	bool IsPlayerBotElementProgressEarlyHere(LPCHARACTER ch, int idx)
	{
		return ch && idx >= 0 && idx < PLAYERBOT_EPROG_MAP_COUNT && PLAYERBOT_EPROG_MAPS[idx].iEarly > 0 &&
				(int)ch->GetLevel() < GetPlayerBotElementProgressNormalLevel(idx);
	}

	// Is the map shut for the bot (a retreat running)? An expired one is dropped with a "back" line.
	bool IsPlayerBotElementProgressShut(LPCHARACTER ch, long map)
	{
		if (!ch || s_mapPlayerBotEProg.empty() || !IsPlayerBotElementProgressOn(PLAYERBOT_EPROG_RETREAT))
			return false;
		std::map<DWORD, TPlayerBotEProgRecord>::iterator it = s_mapPlayerBotEProg.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotEProg.end() || it->second.shut.empty())
			return false;
		const long base = GetPlayerBotElementMapBase(map);
		std::map<long, DWORD>::iterator s = it->second.shut.find(base);
		if (s == it->second.shut.end())
			return false;
		if ((int)(s->second - get_dword_time()) > 0)
			return true;
		++s_kPlayerBotEProg.back;
		sys_log(0, "PLAYERBOT_EPROG: back pid=%u name=%s lv=%d map=%ld (the retreat is over, the map may be picked again)",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), base);
		it->second.shut.erase(s);
		return false;
	}

	// The coping check on a progression map, after each death, HP retreat or kill noticed there.
	void CheckPlayerBotElementProgressCoping(LPCHARACTER ch, TPlayerBotEProgRecord& r, DWORD now)
	{
		if (!IsPlayerBotElementProgressOn(PLAYERBOT_EPROG_RETREAT) || r.lMap == 0)
			return;
		const int idx = FindPlayerBotElementProgressMap(r.lMap);
		if (idx < 0)
			return;
		PrunePlayerBotEProgWindow(r.kills, now);
		PrunePlayerBotEProgWindow(r.deaths, now);
		PrunePlayerBotEProgWindow(r.retreats, now);
		const bool early = IsPlayerBotElementProgressEarlyHere(ch, idx);
		const char* why = NULL;
		if ((int)r.deaths.size() >= PLAYERBOT_EPROG_DEATHS)
		{
			why = "deaths";
			++s_kPlayerBotEProg.retreatDeaths;
		}
		else if ((int)r.retreats.size() >= PLAYERBOT_EPROG_RETREATS)
		{
			why = "hp_retreats";
			++s_kPlayerBotEProg.retreatRetreats;
		}
		else if (early && now - r.dwArrived >= PLAYERBOT_EPROG_WINDOW_MS && (int)r.kills.size() < PLAYERBOT_EPROG_SLOW_KILLS)
		{
			why = "slow_kills";
			++s_kPlayerBotEProg.retreatSlow;
		}
		if (!why)
			return;
		const int element = PLAYERBOT_EPROG_MAPS[idx].iElement;
		const int resist = GetPlayerBotElementMapResist(ch, element);
		// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1 (the owner, 8 November 2026: "Boty nie daja rady na Lochu Pajakow V2 -> maja SM
		// -> wbijaja wiecej odpornosci i wracaja do expa na lochu. Jak nie maja SM lub Yang -> ida na inna mape."): a bot
		// that can afford it raises its resistance target by the step (to the maximum) - the element shop works it and the
		// HP lines after it - and stays on the map (the window starts again); only one that cannot goes elsewhere (the shut).
		const char* action = "leave";
		const char* via = "-";
		const char* leaveWhy = "off";
		long long cost = 0;
		int target = 0;
		const int prevBoost = r.iBoostElement == element ? r.iBoostTarget : 0;
		if (IsPlayerBotElementProgressOn(PLAYERBOT_EPROG_BOOST))
		{
			const int boostMax = GetPlayerBotElementProgressBoostMax();
			target = std::min(boostMax, std::max(std::max(prevBoost, GetPlayerBotElementProgressGate()), resist) +
					GetPlayerBotElementProgressBoostStep());
			if (target <= resist)
				leaveWhy = "maxed";
			else if (TryPlayerBotElementShopBoost(ch, element, &target, &via, &leaveWhy, &cost))
				action = "buy_more";
		}
		if (strcmp(action, "buy_more") == 0)
		{
			r.iBoostElement = element;
			r.iBoostTarget = target;
			++r.iBoosts;
			r.dwBoostAt = now ? now : 1;
			++s_kPlayerBotEProg.buyMore;
			if (strstr(via, "sm"))
				++s_kPlayerBotEProg.buyMoreSm;
			if (strstr(via, "yang"))
				++s_kPlayerBotEProg.buyMoreYang;
			sys_log(0, "PLAYERBOT_EPROG: retreat pid=%u name=%s lv=%d map=%ld(%s) element=%s resist=%d gate=%d early=%d why=%s "
					"deaths=%u hp_retreats=%u kills=%u on_map_min=%u action=buy_more via=%s target=%d prev_target=%d boosts=%d "
					"sm_expected=%lld",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), r.lMap, PLAYERBOT_EPROG_MAPS[idx].szName,
					GetPlayerBotElementMapElementName(element), resist, GetPlayerBotElementProgressGate(), early ? 1 : 0, why,
					(unsigned int)r.deaths.size(), (unsigned int)r.retreats.size(), (unsigned int)r.kills.size(),
					(unsigned int)((now - r.dwArrived) / 60000U), via, target, prevBoost, r.iBoosts, cost);
			r.kills.clear();
			r.deaths.clear();
			r.retreats.clear();
			r.dwArrived = now ? now : 1;
			return;
		}
		++s_kPlayerBotEProg.leave;
		if (strcmp(leaveWhy, "maxed") == 0)
			++s_kPlayerBotEProg.leaveMaxed;
		else if (strcmp(leaveWhy, "off") == 0)
			++s_kPlayerBotEProg.leaveOff;
		else
			++s_kPlayerBotEProg.leaveNoFunds;
		const DWORD shutMs = GetPlayerBotElementProgressShutMs();
		const DWORD until = now + shutMs;
		r.shut[r.lMap] = until ? until : 1;
		sys_log(0, "PLAYERBOT_EPROG: retreat pid=%u name=%s lv=%d map=%ld(%s) element=%s resist=%d gate=%d early=%d why=%s "
				"deaths=%u hp_retreats=%u kills=%u on_map_min=%u shut_min=%u action=leave leave_why=%s target=%d prev_target=%d "
				"boosts=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), r.lMap, PLAYERBOT_EPROG_MAPS[idx].szName,
				GetPlayerBotElementMapElementName(element), resist, GetPlayerBotElementProgressGate(),
				early ? 1 : 0, why, (unsigned int)r.deaths.size(), (unsigned int)r.retreats.size(), (unsigned int)r.kills.size(),
				(unsigned int)((now - r.dwArrived) / 60000U), (unsigned int)(shutMs / 60000U), leaveWhy, target, prevBoost,
				r.iBoosts);
		r.kills.clear();
		r.deaths.clear();
		r.retreats.clear();
		r.dwArrived = now ? now : 1;
	}

	// The slow-kill rule needs a look while nothing happens (no kill, no death): the gate's pass for a bot standing there.
	void LookPlayerBotElementProgressCoping(LPCHARACTER ch, DWORD now)
	{
		if (!ch || FindPlayerBotElementProgressMap(ch->GetMapIndex()) < 0)
			return;
		TPlayerBotEProgRecord* r = TouchPlayerBotEProg(ch, now);
		if (r)
			CheckPlayerBotElementProgressCoping(ch, *r, now);
	}

	// MT2009_PLUS_BOT_GATE_TRIAL_V1: the gate trial's coping record (playerbot_progression.h, included later) takes the
	// same three events, on any map.
	enum { PLAYERBOT_GATE_TRIAL_EV_KILL = 0, PLAYERBOT_GATE_TRIAL_EV_DEATH, PLAYERBOT_GATE_TRIAL_EV_RETREAT };
	void NotePlayerBotGateTrialEvent(LPCHARACTER ch, int kind, DWORD now);

	// The hooks: BattlePassOnKill (playerbot_battlepass.h), the death pass and the tactical retreat (playerbot_survival.h).
	void NotePlayerBotElementProgressKillFor(LPCHARACTER ch, DWORD now)
	{
		TPlayerBotEProgRecord* r = TouchPlayerBotEProg(ch, now);
		if (!r)
			return;
		r->kills.push_back(now);
		if (r->kills.size() > PLAYERBOT_EPROG_KILLS_KEPT)
			r->kills.pop_front();
	}

	// MT2009_PLUS_BOT_EPROG_STAY_FIX_V1: the killer's party members on the map near it (their own kill counted once).
	struct FPlayerBotEProgPartyKill
	{
		LPCHARACTER m_pKiller;
		DWORD m_dwNow;
		FPlayerBotEProgPartyKill(LPCHARACTER killer, DWORD now) : m_pKiller(killer), m_dwNow(now) {}
		void operator()(LPCHARACTER member)
		{
			if (!member || member == m_pKiller || member->GetMapIndex() != m_pKiller->GetMapIndex() ||
					DISTANCE_APPROX(member->GetX() - m_pKiller->GetX(), member->GetY() - m_pKiller->GetY()) > PLAYERBOT_EPROG_PARTY_KILL_RANGE)
				return;
			if (s_mapPlayerBotAIStates.find(member->GetPlayerID()) == s_mapPlayerBotAIStates.end())
				return;
			++s_kPlayerBotEProg.partyKills;
			NotePlayerBotElementProgressKillFor(member, m_dwNow);
		}
	};

	void NotePlayerBotElementProgressKill(LPCHARACTER killer, LPCHARACTER victim)
	{
		if (!killer || !victim || victim->IsPC() || !killer->IsPC())
			return;
		NotePlayerBotGateTrialEvent(killer, PLAYERBOT_GATE_TRIAL_EV_KILL, get_dword_time());	// MT2009_PLUS_BOT_GATE_TRIAL_V1
		if (FindPlayerBotElementProgressMap(killer->GetMapIndex()) < 0)
		{
			NotePlayerBotElementProgressAway(killer);	// MT2009_PLUS_BOT_EPROG_STAY_FIX_V1
			return;
		}
		const DWORD now = get_dword_time();
		NotePlayerBotElementProgressKillFor(killer, now);
		if (killer->GetParty() && IsPlayerBotElementProgressOn(PLAYERBOT_EPROG_STAYFIX))
		{
			FPlayerBotEProgPartyKill f(killer, now);
			killer->GetParty()->ForEachOnMapMember(f, killer->GetMapIndex());
		}
	}

	void NotePlayerBotElementProgressDeath(LPCHARACTER ch, DWORD now)
	{
		NotePlayerBotGateTrialEvent(ch, PLAYERBOT_GATE_TRIAL_EV_DEATH, now);	// MT2009_PLUS_BOT_GATE_TRIAL_V1
		if (!ch || FindPlayerBotElementProgressMap(ch->GetMapIndex()) < 0)
			return;
		TPlayerBotEProgRecord* r = TouchPlayerBotEProg(ch, now);
		if (!r)
			return;
		r->deaths.push_back(now);
		CheckPlayerBotElementProgressCoping(ch, *r, now);
	}

	void NotePlayerBotElementProgressRetreat(LPCHARACTER ch, DWORD now)
	{
		NotePlayerBotGateTrialEvent(ch, PLAYERBOT_GATE_TRIAL_EV_RETREAT, now);	// MT2009_PLUS_BOT_GATE_TRIAL_V1
		if (!ch || FindPlayerBotElementProgressMap(ch->GetMapIndex()) < 0)
			return;
		TPlayerBotEProgRecord* r = TouchPlayerBotEProg(ch, now);
		if (!r)
			return;
		r->retreats.push_back(now);
		CheckPlayerBotElementProgressCoping(ch, *r, now);
	}

	int GetPlayerBotElementProgressStepElement(int step)
	{
		for (int i = 0; i < PLAYERBOT_EPROG_MAP_COUNT; ++i)
			if (PLAYERBOT_EPROG_MAPS[i].iStep == step)
				return PLAYERBOT_EPROG_MAPS[i].iElement;
		return -1;
	}

	int GetPlayerBotElementProgressStepRow(int step)
	{
		for (int i = 0; i < PLAYERBOT_EPROG_MAP_COUNT; ++i)
			if (PLAYERBOT_EPROG_MAPS[i].iStep == step)
			{
				const int row = FindPlayerBotElementMapRow(PLAYERBOT_EPROG_MAPS[i].lMap);
				if (row >= 0)
					return row;
			}
		return -1;
	}

	// The step's first early level (or its normal entry where no map of it has one).
	int GetPlayerBotElementProgressStepEarly(int step)
	{
		int from = 0, to = 0;
		GetPlayerBotElementProgressStepWindow(step, from, to);
		return from + PLAYERBOT_EPROG_LEAD;
	}

	// The prebuild goal's row in PLAYERBOT_ELEMENT_MAP_ROWS, or -1: the latest step whose window holds the level - but
	// the step before while the bot holds that one's resistance at the gate, its window still holds the level and the
	// later step's first early level is not reached (it keeps what it hunts with now); past that early level the later
	// step is built and the earlier element is kept on the pieces that carry it while its window lasts (*pKeep: that
	// element, -1 none - IsPlayerBotElementMapLineMissing / HasPlayerBotElementMapLine).
	int GetPlayerBotElementProgressPrebuildRow(LPCHARACTER ch, int* pStep, int* pKeep = NULL)
	{
		if (pStep)
			*pStep = -1;
		if (pKeep)
			*pKeep = -1;
		if (!ch || !IsPlayerBotElementProgressOn(PLAYERBOT_EPROG_PREBUILD))
			return -1;
		const int level = (int)ch->GetLevel();
		int step = -1;
		for (int s = PLAYERBOT_EPROG_STEPS - 1; s >= 0 && step < 0; --s)
		{
			int from = 0, to = 0;
			GetPlayerBotElementProgressStepWindow(s, from, to);
			if (level >= from && level <= to)
				step = s;
		}
		if (step < 0)
			return -1;
		int keep = -1;
		if (step > 0)
		{
			int from = 0, to = 0;
			GetPlayerBotElementProgressStepWindow(step - 1, from, to);
			const int prevElement = GetPlayerBotElementProgressStepElement(step - 1);
			if (level >= from && level <= to && prevElement >= 0 &&
					GetPlayerBotElementMapResist(ch, prevElement) >= GetPlayerBotElementProgressGate())
			{
				if (level < GetPlayerBotElementProgressStepEarly(step))
					--step;
				else
					keep = prevElement;
			}
		}
		const int row = GetPlayerBotElementProgressStepRow(step);
		if (row < 0)
			return -1;
		if (pStep)
			*pStep = step;
		if (pKeep)
			*pKeep = keep;
		return row;
	}

	// A piece carrying the kept element's line at the table's level-4 value (10 in global).
	bool HasPlayerBotElementProgressKeptLine(LPITEM item, int keep)
	{
		if (!item || keep < 0 || keep >= 6)
			return false;
		const BYTE point = PLAYERBOT_ELEMENT_MAP_POINTS[keep];
		TItemAttrMap::const_iterator it = g_map_itemAttr.find(point);
		const long floor = it != g_map_itemAttr.end() ? it->second.lValues[3] : 10;
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			if (item->GetAttributeType(i) == point && item->GetAttributeValue(i) >= floor)
				return true;
		return false;
	}

	// May the bot take the progression map early (from its early level, under its normal entry)? Its resistance at the
	// gate (PLAYERBOT_ELEMENT_MAP_STAY_SLACK under while it stands there), no retreat running, no Yohara hunt element.
	// The gear, the role, the errands and the hosting are the caller's.
	bool CanPlayerBotTakeElementProgressEarly(LPCHARACTER ch, int idx, int* pResist)
	{
		if (pResist)
			*pResist = 0;
		if (!ch || idx < 0 || idx >= PLAYERBOT_EPROG_MAP_COUNT || !IsPlayerBotElementProgressOn(PLAYERBOT_EPROG_EARLY))
			return false;
		const TPlayerBotEProgMap& m = PLAYERBOT_EPROG_MAPS[idx];
		const int level = (int)ch->GetLevel();
		if (m.iEarly <= 0 || level < m.iEarly || level >= GetPlayerBotElementProgressNormalLevel(idx) ||
				GetPlayerBotHuntElement(ch) != 0 || IsPlayerBotYoharaBonusMember(ch))
			return false;
		const int row = FindPlayerBotElementMapRow(m.lMap);
		if (row < 0 || GetPlayerBotElementMapShare(row) < PLAYERBOT_ELEMENT_MAP_ACTIVE_SHARE)
			return false;
		const int resist = GetPlayerBotElementMapResist(ch, m.iElement);
		if (pResist)
			*pResist = resist;
		const bool here = GetPlayerBotElementMapBase(ch->GetMapIndex()) == m.lMap;
		const int gate = GetPlayerBotElementProgressGate();
		if (resist < (here ? gate - PLAYERBOT_ELEMENT_MAP_STAY_SLACK : gate))
			return false;
		if (here)
			LookPlayerBotElementProgressCoping(ch, get_dword_time());
		return !IsPlayerBotElementProgressShut(ch, m.lMap);
	}

	enum { PLAYERBOT_EPROG_EARLY_PICK = 0, PLAYERBOT_EPROG_EARLY_NONE, PLAYERBOT_EPROG_EARLY_GEAR_SHORT };

	void LogPlayerBotElementProgressEarly(LPCHARACTER ch, long draw, long map, int decision, int resist)
	{
		static const char* const s_aszDecisions[3] = { "early_pick", "early_none", "early_gear_short" };
		if (!ch || decision < 0 || decision > 2)
			return;
		std::map<DWORD, TPlayerBotEProgRecord>::iterator it = s_mapPlayerBotEProg.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotEProg.end())
		{
			if (decision == PLAYERBOT_EPROG_EARLY_NONE)
				return;	// nothing to say about a bot never eligible
			it = s_mapPlayerBotEProg.insert(std::make_pair(ch->GetPlayerID(), TPlayerBotEProgRecord())).first;
		}
		const DWORD now = get_dword_time();
		it->second.dwSeen = now ? now : 1;
		if (it->second.lEarlyMap == map && it->second.iEarlyDecision == decision)
			return;
		if (decision == PLAYERBOT_EPROG_EARLY_NONE && it->second.iEarlyDecision < 0)
			return;
		it->second.lEarlyMap = map;
		it->second.iEarlyDecision = decision;
		if (decision == PLAYERBOT_EPROG_EARLY_PICK)
			++s_kPlayerBotEProg.early;
		const int idx = FindPlayerBotElementProgressMap(map);
		sys_log(0, "PLAYERBOT_EPROG: %s pid=%u name=%s lv=%d draw=%ld map=%ld(%s) element=%s resist=%d gate=%d here=%ld",
				s_aszDecisions[decision], ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), draw, map,
				idx >= 0 ? PLAYERBOT_EPROG_MAPS[idx].szName : "-",
				idx >= 0 ? GetPlayerBotElementMapElementName(PLAYERBOT_EPROG_MAPS[idx].iElement) : "-", resist,
				GetPlayerBotElementProgressGate(), ch->GetMapIndex());
	}

	// Every PLAYERBOT_EPROG_CENSUS_MS: per ten-level band of this core's bots of 40-119 - how many, their fire / lightning /
	// wind resistance (avg, how many at the gate), how many may hunt each step's maps now (open by level - early or in
	// band -, at the gate, no retreat), how many are on them and early there, the prebuild goal per step, retreats
	// running; then the totals since the last census (early picks, retreats by cause, backs, gate refusals).
	void TickPlayerBotElementProgressCensus(DWORD now)
	{
		static DWORD s_dwAt = 0;
		if (s_dwAt == 0)
		{
			s_dwAt = now + PLAYERBOT_EPROG_CENSUS_MS;
			return;
		}
		if ((int)(now - s_dwAt) < 0)
			return;
		s_dwAt = now + PLAYERBOT_EPROG_CENSUS_MS;
		if (!IsPlayerBotElementProgressOn(PLAYERBOT_EPROG_ALL))
			return;
		const int BANDS = 8;	// 40-49 .. 110-119
		int bots[BANDS] = { 0 }, atGate[BANDS][3] = { { 0 } }, eligible[BANDS][3] = { { 0 } }, onMap[BANDS][3] = { { 0 } };
		int early[BANDS] = { 0 }, prebuild[BANDS][3] = { { 0 } }, shut[BANDS] = { 0 };
		long sum[BANDS][3] = { { 0 } };
		const int gate = GetPlayerBotElementProgressGate();
		const int elements[3] = { PLAYERBOT_EM_FIRE, PLAYERBOT_EM_ELEC, PLAYERBOT_EM_WIND };
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !ch->IsItemLoaded() || ch->GetLevel() < 40 || ch->GetLevel() >= 120)
				continue;
			const int b = ((int)ch->GetLevel() - 40) / 10;
			const int level = (int)ch->GetLevel();
			++bots[b];
			for (int s = 0; s < 3; ++s)
			{
				const int r = GetPlayerBotElementMapResist(ch, elements[s]);
				sum[b][s] += r;
				atGate[b][s] += r >= gate ? 1 : 0;
			}
			bool counted[3] = { false, false, false };
			for (int i = 0; i < PLAYERBOT_EPROG_MAP_COUNT; ++i)
			{
				const int s = PLAYERBOT_EPROG_MAPS[i].iStep;
				if (s < 0 || s >= 3 || counted[s])
					continue;
				const bool open = (PLAYERBOT_EPROG_MAPS[i].iEarly > 0 && level >= PLAYERBOT_EPROG_MAPS[i].iEarly) ||
						level >= GetPlayerBotElementProgressNormalLevel(i);
				if (open && GetPlayerBotElementMapResist(ch, PLAYERBOT_EPROG_MAPS[i].iElement) >= gate &&
						!IsPlayerBotElementProgressShut(ch, PLAYERBOT_EPROG_MAPS[i].lMap))
				{
					++eligible[b][s];
					counted[s] = true;
				}
			}
			const int here = FindPlayerBotElementProgressMap(ch->GetMapIndex());
			if (here >= 0 && PLAYERBOT_EPROG_MAPS[here].iStep < 3)
			{
				++onMap[b][PLAYERBOT_EPROG_MAPS[here].iStep];
				early[b] += IsPlayerBotElementProgressEarlyHere(ch, here) ? 1 : 0;
			}
			int step = -1;
			if (GetPlayerBotHuntElement(ch) == 0 && GetPlayerBotElementProgressPrebuildRow(ch, &step) >= 0 && step >= 0 && step < 3)
				++prebuild[b][step];
			std::map<DWORD, TPlayerBotEProgRecord>::const_iterator r = s_mapPlayerBotEProg.find(it->first);
			if (r != s_mapPlayerBotEProg.end())
				for (std::map<long, DWORD>::const_iterator s = r->second.shut.begin(); s != r->second.shut.end(); ++s)
					if ((int)(s->second - now) > 0)
					{
						++shut[b];
						break;
					}
		}
		for (int b = 0; b < BANDS; ++b)
		{
			if (!bots[b])
				continue;
			sys_log(0, "PLAYERBOT_EPROG: census band=%d-%d bots=%d gate=%d fire=[avg=%ld at_gate=%d] lightning=[avg=%ld at_gate=%d] "
					"wind=[avg=%ld at_gate=%d] eligible=[spider=%d grotto=%d zaklety=%d] on=[spider=%d grotto=%d zaklety=%d] "
					"early_on=%d prebuild=[fire=%d lightning=%d wind=%d] shut=%d",
					40 + b * 10, 49 + b * 10, bots[b], gate, sum[b][0] / bots[b], atGate[b][0], sum[b][1] / bots[b], atGate[b][1],
					sum[b][2] / bots[b], atGate[b][2], eligible[b][0], eligible[b][1], eligible[b][2], onMap[b][0], onMap[b][1],
					onMap[b][2], early[b], prebuild[b][0], prebuild[b][1], prebuild[b][2], shut[b]);
		}
		// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1: the boosts running now (a raised target, a day old at most)
		int boosted = 0, boostedOn = 0;
		for (std::map<DWORD, TPlayerBotEProgRecord>::iterator it = s_mapPlayerBotEProg.begin(); it != s_mapPlayerBotEProg.end(); ++it)
		{
			it->second.bRefusedCounted = false;
			if (it->second.iBoostTarget > 0 && now - it->second.dwBoostAt < PLAYERBOT_EPROG_BOOST_KEEP_MS)
			{
				++boosted;
				boostedOn += it->second.lMap != 0 ? 1 : 0;
			}
		}
		sys_log(0, "PLAYERBOT_EPROG: census totals early_picks=%u retreats=[deaths=%u hp_retreats=%u slow_kills=%u] "
				"actions=[buy_more=%u via_sm=%u via_yang=%u leave=%u leave_maxed=%u leave_no_funds=%u leave_off=%u] "
				"boosted=[bots=%d on_map=%d] backs=%u gate_refusals=%u refused=[bots=%u shut=%u resist=%u] stale_resets=%u "
				"party_kills=%u records=%u",
				s_kPlayerBotEProg.early, s_kPlayerBotEProg.retreatDeaths, s_kPlayerBotEProg.retreatRetreats,
				s_kPlayerBotEProg.retreatSlow, s_kPlayerBotEProg.buyMore, s_kPlayerBotEProg.buyMoreSm,
				s_kPlayerBotEProg.buyMoreYang, s_kPlayerBotEProg.leave, s_kPlayerBotEProg.leaveMaxed,
				s_kPlayerBotEProg.leaveNoFunds, s_kPlayerBotEProg.leaveOff, boosted, boostedOn, s_kPlayerBotEProg.back,
				s_kPlayerBotEProg.gateRefusals, s_kPlayerBotEProg.refusedBots, s_kPlayerBotEProg.refusedShut,
				s_kPlayerBotEProg.refusedResist, s_kPlayerBotEProg.staleResets, s_kPlayerBotEProg.partyKills,
				(unsigned int)s_mapPlayerBotEProg.size());
		s_kPlayerBotEProg = TPlayerBotEProgStats();
		// the record of a bot not seen on this core for a day is dropped
		for (std::map<DWORD, TPlayerBotEProgRecord>::iterator it = s_mapPlayerBotEProg.begin(); it != s_mapPlayerBotEProg.end();)
		{
			if (now - it->second.dwSeen > 24U * 60U * 60U * 1000U)
				s_mapPlayerBotEProg.erase(it++);
			else
				++it;
		}
	}

	// Zaklety Las's entry level for this bot (playerbot_yohara_bots.h, the route's band): the env's, or the early level
	// for a bot at the wind gate (on the forest, PLAYERBOT_ELEMENT_MAP_STAY_SLACK under) with no retreat running.
	int GetPlayerBotElementProgressZakletyMinLevel(LPCHARACTER ch, int normal)
	{
		const int idx = FindPlayerBotElementProgressMap(PLAYERBOT_MAP_ZAKLETY);
		if (!ch || idx < 0)
			return normal;
		const int level = (int)ch->GetLevel();
		const TPlayerBotEProgMap& m = PLAYERBOT_EPROG_MAPS[idx];
		if (m.iEarly <= 0 || level >= normal || level < m.iEarly)
			return normal;
		int resist = 0;
		if (!CanPlayerBotTakeElementProgressEarly(ch, idx, &resist))
		{
			LogPlayerBotElementProgressEarly(ch, 0, m.lMap, PLAYERBOT_EPROG_EARLY_NONE, resist);
			return normal;
		}
		LogPlayerBotElementProgressEarly(ch, 0, m.lMap, PLAYERBOT_EPROG_EARLY_PICK, resist);
		return std::min(normal, m.iEarly);
	}
	// MT2009_PLUS_BOT_EPROG_RESIST_GEAR_V1 (the test of 8 November 2026, 09:40: 167 of the ~460 early-eligible bots' last
	// decision was early_gear_short - 119 of them in body armour under +5, V2's grade; the owner: "Jesli bot jest ubrany w
	// odpornosc na ogien (40%), to moze juz tam expic, nawet na 45 poziomie"): in the Spider Dungeon V2 a bot holding its
	// fire at the gate wears V1's grades (weapon and armour +4) - the resistance is its armour there. The helmet, a weapon
	// of its level and the red potions stay. Event flag m2_bot_element_progress_gear_off 1 - V2's grades for all.
	bool IsPlayerBotElementProgressResistGear(LPCHARACTER ch, long map)
	{
		if (!ch || GetPlayerBotElementMapBase(map) != PLAYERBOT_MAP_SPIDER_V2 || !IsPlayerBotElementProgressOn(PLAYERBOT_EPROG_GEAR) ||
				GetPlayerBotElementProgressGateForMap(map) <= 0 || GetPlayerBotHuntElement(ch) != 0)
			return false;
		const int idx = FindPlayerBotElementProgressMap(map);
		// MT2009_PLUS_BOT_GATE55_FIRE_V1: the map's own gate (never over the level-55 alternative's minimum), so a bot
		// passed 55 by fire >= 50 with +4 gear and a young heroes' weapon wears V2's resist grades (weapon / armour +4)
		return idx >= 0 && GetPlayerBotElementMapResist(ch, PLAYERBOT_EPROG_MAPS[idx].iElement) >=
				GetPlayerBotElementProgressGateForMap(map);
	}
	// ====================================================================== end of MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1

	struct TPlayerBotElementMapGoal
	{
		long lWanted;	// the map the pick wanted (0: none with an element)
		DWORD dwAt;
		// the pick's last decision for the log (map, decision)
		long lLastMap;
		int iLastDecision;
		long lLastFallback;
		TPlayerBotElementMapGoal() : lWanted(0), dwAt(0), lLastMap(0), iLastDecision(-1), lLastFallback(0) {}
	};
	std::map<DWORD, TPlayerBotElementMapGoal> s_mapPlayerBotElementMapGoal;

	// The goal now: the row (its element, want, gate), the share and the bot's resistance. false: no goal - a Yohara
	// bot (its hunt element rules), no element row for its wanted map nor where it stands, or the row's element is off
	// in this bonus mode.
	struct TPlayerBotElementMapView
	{
		int iRow;
		int iElement;
		int iWant;
		int iGate;
		int iShare;
		int iResist;
		int iKeep;	// MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1: the element kept on its pieces during a prebuild, -1 none
		bool bPrebuild;	// MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1: the goal is the progression's next map (not hunted yet)
	};

	bool GetPlayerBotElementMapGoal(LPCHARACTER ch, TPlayerBotElementMapView& out)
	{
		if (!ch || !ch->IsPC() || GetPlayerBotHuntElement(ch) != 0)
			return false;
		int row = -1;
		std::map<DWORD, TPlayerBotElementMapGoal>::const_iterator it = s_mapPlayerBotElementMapGoal.find(ch->GetPlayerID());
		if (it != s_mapPlayerBotElementMapGoal.end() && it->second.dwAt != 0 &&
				get_dword_time() - it->second.dwAt < PLAYERBOT_ELEMENT_MAP_GOAL_MS)
			row = FindPlayerBotElementMapRow(it->second.lWanted);
		if (row < 0)
			row = FindPlayerBotElementMapRow(ch->GetMapIndex());
		// MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1: the prebuild - a bot that neither hunts nor wants a gated map builds the
		// resistance of the progression's next map for its level (the gate + PLAYERBOT_EPROG_PREBUILD_MARGIN); one that
		// does keeps that map's element.
		bool prebuild = false;
		int keep = -1;
		if (row < 0 || GetPlayerBotElementMapRowGate(row) <= 0)
		{
			const int next = GetPlayerBotElementProgressPrebuildRow(ch, NULL, &keep);
			if (next >= 0 && GetPlayerBotElementMapShare(next) >= PLAYERBOT_ELEMENT_MAP_ACTIVE_SHARE)
			{
				row = next;
				prebuild = true;
			}
		}
		// MT2009_PLUS_BOT_GATE55_FIRE_V1: a bot on the level-55 gate's fire path builds fire - the Spider Dungeon V2's
		// row - unless it hunts or wants a gated map of another element
		const int fire55 = GetPlayerBotGate55FireGoal(ch);
		if (fire55 > 0 && (row < 0 || (PLAYERBOT_ELEMENT_MAP_ROWS[row].iElement != PLAYERBOT_EM_FIRE &&
				(prebuild || GetPlayerBotElementMapRowGate(row) <= 0))))
		{
			const int spider = FindPlayerBotElementMapRow(PLAYERBOT_MAP_SPIDER_V2);
			if (spider >= 0 && GetPlayerBotElementMapShare(spider) >= PLAYERBOT_ELEMENT_MAP_ACTIVE_SHARE)
			{
				if (row != spider)
					keep = -1;
				row = spider;
				prebuild = GetPlayerBotElementMapBase(ch->GetMapIndex()) != PLAYERBOT_MAP_SPIDER_V2;
			}
		}
		if (row < 0)
			return false;
		const int share = GetPlayerBotElementMapShare(row);
		if (share < PLAYERBOT_ELEMENT_MAP_ACTIVE_SHARE)
			return false;
		const TPlayerBotElementMapRow& r = PLAYERBOT_ELEMENT_MAP_ROWS[row];
		out.iRow = row;
		out.iElement = r.iElement;
		out.iWant = r.iWant;
		out.iGate = GetPlayerBotElementMapRowGate(row);	// MT2009_PLUS_BOT_ELEMENT_MAP_GATES_V1
		if (prebuild && out.iGate > 0)
			out.iWant = std::min(PLAYERBOT_ELEMENT_MAP_RESIST_CAP, out.iGate + PLAYERBOT_EPROG_PREBUILD_MARGIN);
		// MT2009_PLUS_BOT_EPROG_BUY_MORE_V1: a retreat's raised target is the want (the costume line, the reroll's stop
		// rule, the stone and the element shop read it)
		if (out.iGate > 0)
			out.iWant = std::max(out.iWant, GetPlayerBotElementProgressBoostTarget(ch, r.iElement));
		// MT2009_PLUS_BOT_GATE55_FIRE_V1: the gate's minimum is the goal's gate (the element shop's target is it + its
		// margin, 52), the want two over it (the reroll's stop rule, the stone, the costume line)
		if (fire55 > 0 && r.iElement == PLAYERBOT_EM_FIRE)
		{
			out.iGate = std::max(out.iGate, fire55);
			out.iWant = std::max(out.iWant, std::min(PLAYERBOT_ELEMENT_MAP_RESIST_CAP, fire55 + 2));
		}
		out.iShare = share;
		out.iResist = GetPlayerBotElementMapResist(ch, r.iElement);
		out.iKeep = prebuild && keep != r.iElement ? keep : -1;
		out.bPrebuild = prebuild;
		return true;
	}

	int GetPlayerBotElementMapLineElement(WORD type) // MT2009_PLUS_WIDE_ATTR_V1
	{
		for (int e = 0; e < 6; ++e)
			if (PLAYERBOT_ELEMENT_MAP_POINTS[e] == type)
				return e;
		return -1;
	}

	// One point of the goal's resistance in Max HP: 1% of it on a map all of that element, by the share; half at or
	// over the want. -1: not the goal's element (the caller's own weight).
	long GetPlayerBotElementMapPointInHp(LPCHARACTER ch, WORD type) // MT2009_PLUS_WIDE_ATTR_V1
	{
		const int e = GetPlayerBotElementMapLineElement(type);
		TPlayerBotElementMapView v;
		if (e < 0 || !GetPlayerBotElementMapGoal(ch, v) || v.iElement != e)
			return -1;
		long hp = std::max(1000L, (long)ch->GetMaxHP()) * v.iShare / 10000;
		if (v.iResist >= v.iWant)
			hp /= 2;
		return std::max(1L, hp);
	}

	// The equipment score (ScorePlayerBotApply's scale - Max HP fifteen a point).
	long long GetPlayerBotElementMapApplyScore(LPCHARACTER ch, WORD type, long value) // MT2009_PLUS_WIDE_ATTR_V1
	{
		const long hp = value > 0 ? GetPlayerBotElementMapPointInHp(ch, type) : -1;
		return hp < 0 ? -1 : (long long)value * hp * 15;
	}

	// The bonus line's score (ScorePlayerBotBonusLineRaw's scale - Max HP a quarter a point), never under the old weight.
	int GetPlayerBotElementMapLineScore(LPCHARACTER ch, WORD type, long value) // MT2009_PLUS_WIDE_ATTR_V1
	{
		const long hp = value > 0 ? GetPlayerBotElementMapPointInHp(ch, type) : -1;
		return hp < 0 ? -1 : (int)std::max<long>(value * 3, value * hp / 4);
	}

	// The boots' own apply of the goal's element (Bambusowe / Drewniane / Wyszywane Zlotem Buty): GetPlayerBotBootsScore
	// counts only rolled lines, so a pair worn for its resistance needs this.
	long long GetPlayerBotElementMapProtoScore(LPITEM item, LPCHARACTER ch)
	{
		if (!item || !item->GetProto() || !ch)
			return 0;
		long long score = 0;
		for (int i = 0; i < ITEM_APPLY_MAX_NUM; ++i)
		{
			const long long s = GetPlayerBotElementMapApplyScore(ch, item->GetProto()->aApplies[i].bType,
					item->GetProto()->aApplies[i].lValue);
			if (s > 0)
				score += s;
		}
		return score;
	}

	// The reroll's stop rule: the piece (armour, helmet, bracelet) can roll the goal's resistance and lacks it at the
	// table's level-4 value while the bot is short of the want. *pHas: whether the line is there at that value.
	bool IsPlayerBotElementMapLineMissing(LPCHARACTER ch, LPITEM item, BYTE wearCell)
	{
		if (!ch || !item || (wearCell != WEAR_BODY && wearCell != WEAR_HEAD && wearCell != WEAR_WRIST))
			return false;
		TPlayerBotElementMapView v;
		if (!GetPlayerBotElementMapGoal(ch, v) || v.iResist >= v.iWant ||
				(v.iGate <= 0 && v.iWant < PLAYERBOT_ELEMENT_MAP_REROLL_WANT))
			return false;
		// MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1: a piece holding the element the bot still hunts with is not rerolled for
		// the next one
		if (HasPlayerBotElementProgressKeptLine(item, v.iKeep))
			return false;
		const BYTE point = PLAYERBOT_ELEMENT_MAP_POINTS[v.iElement];
		const int set = item->GetAttributeSetIndex();
		if (set < 0 || !IsPlayerBotApplyOnAttrSet(point, set))
			return false;
		TItemAttrMap::const_iterator it = g_map_itemAttr.find(point);
		if (it == g_map_itemAttr.end())
			return false;
		const int top = std::max(1, std::min((int)it->second.bMaxLevelBySet[set], 4));
		const long floor = it->second.lValues[top - 1];
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			if (item->GetAttributeType(i) == point && item->GetAttributeValue(i) >= floor)
				return false;
		return true;
	}

	bool HasPlayerBotElementMapLine(LPCHARACTER ch, LPITEM item)
	{
		TPlayerBotElementMapView v;
		if (!ch || !item || !GetPlayerBotElementMapGoal(ch, v))
			return false;
		if (HasPlayerBotElementProgressKeptLine(item, v.iKeep))	// MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1: a finishing line too
			return true;
		const BYTE point = PLAYERBOT_ELEMENT_MAP_POINTS[v.iElement];
		TItemAttrMap::const_iterator it = g_map_itemAttr.find(point);
		const long floor = it != g_map_itemAttr.end() ? it->second.lValues[3] : 10;
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			if (item->GetAttributeType(i) == point && item->GetAttributeValue(i) >= floor)
				return true;
		return false;
	}

	// The costume / hairstyle: its set rolls the goal's resistance (global costume pools) and its line is under the
	// set's top while the bot is short of the want.
	bool IsPlayerBotElementMapCostumeLineShort(LPCHARACTER ch, LPITEM costume)
	{
		if (!ch || !costume || costume->GetType() != ITEM_COSTUME ||
				(costume->GetSubType() != COSTUME_BODY && costume->GetSubType() != COSTUME_HAIR))
			return false;
		TPlayerBotElementMapView v;
		if (!GetPlayerBotElementMapGoal(ch, v) || v.iResist >= v.iWant ||
				(v.iGate <= 0 && v.iWant < PLAYERBOT_ELEMENT_MAP_REROLL_WANT))
			return false;
		if (HasPlayerBotElementProgressKeptLine(costume, v.iKeep))	// MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1
			return false;
		const BYTE point = PLAYERBOT_ELEMENT_MAP_POINTS[v.iElement];
		const int set = costume->GetAttributeSetIndex();
		if (set < 0 || !IsPlayerBotApplyOnAttrSet(point, set))
			return false;
		TItemAttrMap::const_iterator it = g_map_itemAttr.find(point);
		if (it == g_map_itemAttr.end())
			return false;
		const int top = std::max(1, std::min((int)it->second.bMaxLevelBySet[set], 5));
		long line = 0;
		for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			if (costume->GetAttributeType(i) == point)
				line += costume->GetAttributeValue(i);
		return line < it->second.lValues[top - 1];
	}

	// The owner, 31 October: no gates yet - the bots hunt there and gather resistance to hunt faster (the wants 60/75
	// stay as gear goals; the gates come later). Kamien Ochrony Zywiolow for a bot short of a gated map's resistance
	// or of a big want (60+) (playerbot_element_stones.h: bought only).
	bool IsPlayerBotElementShopStoneWanted(LPCHARACTER ch);	// MT2009_PLUS_BOT_ELEMENT_SHOP_V1 (playerbot_element_shop.h)

	bool IsPlayerBotElementMapStoneWanted(LPCHARACTER ch)
	{
		// MT2009_PLUS_BOT_ELEMENT_SHOP_V1: the element gate's plan holds the stone (its cheapest point - 65 SM for 10)
		if (IsPlayerBotElementShopStoneWanted(ch))
			return true;
		TPlayerBotElementMapView v;
		// MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1: for a prebuild only as the last piece - its 10 closes the gap to the gate
		return GetPlayerBotElementMapGoal(ch, v) && (v.iGate > 0 || v.iWant >= 60) && v.iResist < v.iWant &&
				(!v.bPrebuild || v.iResist + 10 >= v.iGate);
	}

	// The gate: may the bot pick (or stay on) the map? true for a map without a gate or whose element is off in this
	// mode. *pView: the row's view when there is one.
	bool PassPlayerBotElementMapGate(LPCHARACTER ch, long map, TPlayerBotElementMapView* pView, bool* pGated)
	{
		if (pGated)
			*pGated = false;
		const int row = FindPlayerBotElementMapRow(map);
		if (!ch || row < 0 || GetPlayerBotElementMapRowGate(row) <= 0)	// MT2009_PLUS_BOT_ELEMENT_MAP_GATES_V1
			return true;
		const int share = GetPlayerBotElementMapShare(row);
		if (share < PLAYERBOT_ELEMENT_MAP_ACTIVE_SHARE)
			return true;
		const TPlayerBotElementMapRow& r = PLAYERBOT_ELEMENT_MAP_ROWS[row];
		const int resist = GetPlayerBotElementMapResist(ch, r.iElement);
		if (pView)
		{
			pView->iRow = row;
			pView->iElement = r.iElement;
			pView->iWant = r.iWant;
			pView->iGate = GetPlayerBotElementMapRowGate(row);
			pView->iShare = share;
			pView->iResist = resist;
			pView->iKeep = -1;
			pView->bPrebuild = false;
		}
		if (pGated)
			*pGated = true;
		const bool here = GetPlayerBotElementMapBase(ch->GetMapIndex()) == r.lMap;
		const int gate = GetPlayerBotElementMapRowGate(row);
		// MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1: a resident of Zaklety Las is not asked where it stands (the Yohara stay
		// takes it out; the gate is the way in), and a progression map in a retreat is refused until the retreat ends.
		if (here && r.lMap == PLAYERBOT_MAP_ZAKLETY && GetPlayerBotElementProgressGateForMap(r.lMap) > 0)
			return true;
		// and a Yohara bot (a cohort member, a Champion on its G0 trip) keeps its own element rules (step 3)
		if (GetPlayerBotElementProgressGateForMap(r.lMap) > 0 && IsPlayerBotYoharaBonusMember(ch))
			return true;
		if (GetPlayerBotElementProgressGateForMap(r.lMap) > 0)
		{
			if (here)
				LookPlayerBotElementProgressCoping(ch, get_dword_time());
			if (IsPlayerBotElementProgressShut(ch, r.lMap))
				return false;
		}
		return resist >= (here ? gate - PLAYERBOT_ELEMENT_MAP_STAY_SLACK : gate);
	}

	// MT2009_PLUS_BOT_EPROG_STAY_FIX_V1: a progression gate's refusal for the census - per call (gate_refusals, as before),
	// per bot once a period, and by cause (a retreat's shut or the resistance).
	void NotePlayerBotElementProgressRefusal(LPCHARACTER ch, long map)
	{
		++s_kPlayerBotEProg.gateRefusals;
		if (!ch)
			return;
		const bool shut = IsPlayerBotElementProgressShut(ch, map);
		TPlayerBotEProgRecord& r = s_mapPlayerBotEProg[ch->GetPlayerID()];
		const DWORD now = get_dword_time();
		r.dwSeen = now ? now : 1;
		if (r.bRefusedCounted)
			return;
		r.bRefusedCounted = true;
		++s_kPlayerBotEProg.refusedBots;
		++(shut ? s_kPlayerBotEProg.refusedShut : s_kPlayerBotEProg.refusedResist);
	}

	void NotePlayerBotElementMapWanted(LPCHARACTER ch, long wanted)
	{
		if (!ch)
			return;
		TPlayerBotElementMapGoal& g = s_mapPlayerBotElementMapGoal[ch->GetPlayerID()];
		const DWORD now = get_dword_time();
		g.lWanted = FindPlayerBotElementMapRow(wanted) >= 0 ? GetPlayerBotElementMapBase(wanted) : 0;
		g.dwAt = now ? now : 1;
	}

	enum { PLAYERBOT_EM_PICK = 0, PLAYERBOT_EM_SKIP, PLAYERBOT_EM_STAY, PLAYERBOT_EM_LEAVE, PLAYERBOT_EM_NO_FALLBACK };

	void LogPlayerBotElementMapDecision(LPCHARACTER ch, long map, const TPlayerBotElementMapView& v, int decision, long fallback)
	{
		static const char* const s_aszDecisions[5] = { "pick", "skip", "stay", "leave", "no_fallback" };
		TPlayerBotElementMapGoal& g = s_mapPlayerBotElementMapGoal[ch->GetPlayerID()];
		if (g.lLastMap == map && g.iLastDecision == decision && g.lLastFallback == fallback)
			return;
		g.lLastMap = map;
		g.iLastDecision = decision;
		g.lLastFallback = fallback;
		sys_log(0, "PLAYERBOT_ELEMENT: map_gate pid=%u name=%s lv=%d map=%ld(%s) element=%s resist=%d want=%d gate=%d share=%d "
				"decision=%s fallback=%ld here=%ld",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), map, PLAYERBOT_ELEMENT_MAP_ROWS[v.iRow].szName,
				GetPlayerBotElementMapElementName(v.iElement), v.iResist, v.iWant, v.iGate, v.iShare,
				s_aszDecisions[decision], fallback, ch->GetMapIndex());
	}

	// Every PLAYERBOT_ELEMENT_MAP_CENSUS_MS: per row, the bots aiming at it seen in the window - how many, how many under
	// the gate, the resistance's average / min / max.
	void TickPlayerBotElementMapCensus(DWORD dwNow)
	{
		static DWORD s_dwAt = 0;
		if (s_dwAt == 0)
		{
			s_dwAt = dwNow + PLAYERBOT_ELEMENT_MAP_CENSUS_MS;
			return;
		}
		if ((int)(dwNow - s_dwAt) < 0)
			return;
		s_dwAt = dwNow + PLAYERBOT_ELEMENT_MAP_CENSUS_MS;
		int bots[64] = { 0 }, under[64] = { 0 }, minR[64], maxR[64] = { 0 };
		long sum[64] = { 0 };
		for (int i = 0; i < 64; ++i)
			minR[i] = 1000;
		for (std::map<DWORD, TPlayerBotElementMapGoal>::iterator it = s_mapPlayerBotElementMapGoal.begin();
				it != s_mapPlayerBotElementMapGoal.end();)
		{
			if (it->second.dwAt == 0 || dwNow - it->second.dwAt > PLAYERBOT_ELEMENT_MAP_GOAL_MS)
			{
				s_mapPlayerBotElementMapGoal.erase(it++);
				continue;
			}
			const int row = FindPlayerBotElementMapRow(it->second.lWanted);
			LPCHARACTER ch = row >= 0 && row < 64 ? CHARACTER_MANAGER::instance().FindByPID(it->first) : NULL;
			if (ch && ch->IsItemLoaded())
			{
				const int r = GetPlayerBotElementMapResist(ch, PLAYERBOT_ELEMENT_MAP_ROWS[row].iElement);
				++bots[row];
				sum[row] += r;
				minR[row] = std::min(minR[row], r);
				maxR[row] = std::max(maxR[row], r);
				under[row] += r < GetPlayerBotElementMapRowGate(row) ? 1 : 0;
			}
			++it;
		}
		std::string line;
		for (int row = 0; row < PLAYERBOT_ELEMENT_MAP_ROW_COUNT && row < 64; ++row)
		{
			if (!bots[row])
				continue;
			char buf[192];
			snprintf(buf, sizeof(buf), " %s=[element=%s share=%d want=%d gate=%d bots=%d under_gate=%d resist_avg=%ld min=%d max=%d]",
					PLAYERBOT_ELEMENT_MAP_ROWS[row].szName, GetPlayerBotElementMapElementName(PLAYERBOT_ELEMENT_MAP_ROWS[row].iElement),
					GetPlayerBotElementMapShare(row), PLAYERBOT_ELEMENT_MAP_ROWS[row].iWant, GetPlayerBotElementMapRowGate(row),
					bots[row], under[row], sum[row] / bots[row], minR[row], maxR[row]);
			line += buf;
		}
		if (!line.empty())
			sys_log(0, "PLAYERBOT_ELEMENT: map_census%s", line.c_str());
	}
}

#endif
