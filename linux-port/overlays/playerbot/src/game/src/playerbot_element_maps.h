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
		{ PLAYERBOT_MAP_SPIDER_V2, "spider_v2", PLAYERBOT_EM_FIRE, 60, 0,
			{ { 2133, 15 }, { 2061, 14 }, { 2064, 14 }, { 2062, 13 }, { 2132, 10 }, { 2063, 10 }, { 2065, 10 }, { 2134, 9 } } },
		{ PLAYERBOT_MAP_SPIDER_V3, "spider_v3", PLAYERBOT_EM_FIRE, 60, 0,
			{ { 2072, 28 }, { 2073, 25 }, { 2074, 20 }, { 2071, 19 } } },
		{ PLAYERBOT_MAP_ZAKLETY, "zaklety", PLAYERBOT_EM_WIND, 75, 0,
			{ { 6402, 37 }, { 6401, 29 }, { 6403, 25 } } },
		{ PLAYERBOT_MAP_GROTTO_V1, "grotto_v1", PLAYERBOT_EM_ELEC, 75, 0,
			{ { 2401, 32 }, { 2402, 17 }, { 1136, 9 }, { 1131, 8 }, { 1132, 7 }, { 1137, 6 }, { 1133, 6 }, { 1135, 6 } } },
		{ PLAYERBOT_MAP_GROTTO_V2, "grotto_v2", PLAYERBOT_EM_ELEC, 75, 0,
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

	// The resistance the engine counts against a monster of element e now (ElementsAttackBonus): capped at 80.
	int GetPlayerBotElementMapResist(LPCHARACTER ch, int e)
	{
		if (!ch || e < 0 || e >= 6)
			return 0;
		return std::max(0, std::min(Bonus67Total(ch, PLAYERBOT_ELEMENT_MAP_POINTS[e]), PLAYERBOT_ELEMENT_MAP_RESIST_CAP));
	}

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
		if (row < 0)
			return false;
		const int share = GetPlayerBotElementMapShare(row);
		if (share < PLAYERBOT_ELEMENT_MAP_ACTIVE_SHARE)
			return false;
		const TPlayerBotElementMapRow& r = PLAYERBOT_ELEMENT_MAP_ROWS[row];
		out.iRow = row;
		out.iElement = r.iElement;
		out.iWant = r.iWant;
		out.iGate = r.iGate;
		out.iShare = share;
		out.iResist = GetPlayerBotElementMapResist(ch, r.iElement);
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
	bool IsPlayerBotElementMapStoneWanted(LPCHARACTER ch)
	{
		TPlayerBotElementMapView v;
		return GetPlayerBotElementMapGoal(ch, v) && (v.iGate > 0 || v.iWant >= 60) && v.iResist < v.iWant;
	}

	// The gate: may the bot pick (or stay on) the map? true for a map without a gate or whose element is off in this
	// mode. *pView: the row's view when there is one.
	bool PassPlayerBotElementMapGate(LPCHARACTER ch, long map, TPlayerBotElementMapView* pView, bool* pGated)
	{
		if (pGated)
			*pGated = false;
		const int row = FindPlayerBotElementMapRow(map);
		if (!ch || row < 0 || PLAYERBOT_ELEMENT_MAP_ROWS[row].iGate <= 0)
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
			pView->iGate = r.iGate;
			pView->iShare = share;
			pView->iResist = resist;
		}
		if (pGated)
			*pGated = true;
		const bool here = GetPlayerBotElementMapBase(ch->GetMapIndex()) == r.lMap;
		return resist >= (here ? r.iGate - PLAYERBOT_ELEMENT_MAP_STAY_SLACK : r.iGate);
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
				under[row] += r < PLAYERBOT_ELEMENT_MAP_ROWS[row].iGate ? 1 : 0;
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
					GetPlayerBotElementMapShare(row), PLAYERBOT_ELEMENT_MAP_ROWS[row].iWant, PLAYERBOT_ELEMENT_MAP_ROWS[row].iGate,
					bots[row], under[row], sum[row] / bots[row], minR[row], maxR[row]);
			line += buf;
		}
		if (!line.empty())
			sys_log(0, "PLAYERBOT_ELEMENT: map_census%s", line.c_str());
	}
}

#endif
