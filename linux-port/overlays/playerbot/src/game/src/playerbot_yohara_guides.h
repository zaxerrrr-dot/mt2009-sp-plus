#ifndef __INC_METIN2_PLAYERBOT_YOHARA_GUIDES_H__
#define __INC_METIN2_PLAYERBOT_YOHARA_GUIDES_H__

// MT2009_PLUS_BOT_YOHARA_GUIDES_V1 - four guides for the bots of the Sung Ma maps (the owner's approved points 2, 3, 4
// and 6 of 28 October 2026; doc: cache/yohara/boty-mapy-yohary.md, sections 9-12).
//
// 2. Sung Ma buffs (PLAYERBOT_SUNGMABUFF). Buff Premium SungMa (72803, ItemShop V3: 1 / 7 / 15 / 30 days for
//    39 / 299 / 599 / 999 Smocze Monety, +10 to all four Sung Ma stats - quest ishop_v3_przedmioty, affects 565-568,
//    the time added to what is left) and the Eliksiry Woli SungMa (72804-72807, 300 Smocze Znaki, +5 to one stat for
//    30 minutes, affects 561-564, gone with a death). Both are affects on POINT_SUNGMA_*, so the Will the map pick reads
//    (GetPlayerBotSungmaWill: GetPoint) counts them, and a buff used moves the pick forward (dwNextPick) - the bot steps
//    up at once. A bot buys:
//    * the premium when the Will is the only thing between it and the next map (the band two levels in, the health,
//      the room and the element allow it) and no stat is short by more than 10; the line by the cheapest cover of the
//      time its points need to close the gap (its own champion experience an hour, PLAYERBOT_SUNGMABUFF_RENEW_OVERHEAD
//      a purchase for the risk of a lapse - one day for a short gap, a week or a month when it lasts; a bot at the top
//      Champion level with no points to come takes the month);
//    * the premium again (the time added) while it still holds the bot on its own map and less than
//      PLAYERBOT_SUNGMABUFF_RENEW_LEFT_S is left;
//    * one day of the premium after a "not now" step down, or while it struggles (deaths in the window, the G0 rule's
//      struggle), once in PLAYERBOT_SUNGMABUFF_STRUGGLE_GAP_MS - the Will over the requirement is health and damage;
//    * an elixir only for one stat short by 1-5, a push its points close within the elixir's half hour, a bot that
//      has not died in its stay window (PLAYERBOT_SUNGMABUFF_ELIXIR_MAX_DEATHS), Smocze Znaki over the boosters' reserve.
// 3. Combat boosters (PLAYERBOT_SUNGMA: booster). A Sung Ma hunter counts as fighting for the Dragon God boosters
//    (V3, Smocze Znaki: 71027 / 71028 / 71030 95, 71029 75, 71044 / 71045 125): the defence and the life first on the
//    harder maps (Yilad on, the Loch, deaths in its window, its health near its map's floor), the attack and the
//    critical when its kills are slow (PLAYERBOT_BOOSTER_SLOW_KILLS_H an hour over at least 20 minutes); one of a kind
//    held, none while its affect runs (UsePlayerBotBoosters drinks them in the fight), a day's budget of a quarter of
//    the Smocze Znaki over PLAYERBOT_BOOSTER_MARKS_RESERVE, at most PLAYERBOT_BOOSTER_DAY_MAX - every Smocze Moneta a
//    bot spends in V3 comes back as a Smocze Znak, so the budget follows its income.
// 4. Tajemniczy Loch (396, metin2_map_anglar_dungeon_01 - "Tajemnicza Instancja", PLAYERBOT_SUNGMA: loch). The map is
//    an open one (no instance, no timer): Tajemniczy Oltarz (20850, Namgan 960,242 - quest yohara_mapy3) takes one
//    Tajemniczy Bilet (70408) an entry from a Champion of level 120, Wyjscie (10204) leads back to the altar. Its
//    sungma_table row: 25 / 15 / 25 / 30, Precyzja 25. The bots' excursion: a resident of Namgan..Schronienie of Champion
//    PLAYERBOT_LOCH_CHAMPION_MIN-30 with the Will (Sila, Witalnosc, Odpornosc), the health floor and a ticket - at most
//    PLAYERBOT_LOCH_MAX of the channel at once - goes to the altar (a warp to Namgan as a person's Teleporter, the walk to
//    the altar), gives its ticket there and is put on the Loch's arrival; it hunts PLAYERBOT_LOCH_STAY_MS (its stay map,
//    its element and its rows stay its own map's - no element change, the rule "only up" untouched) and leaves by
//    Wyjscie (walked when near, else the scroll's warp - the map forbids no scroll) to the altar; then the map pick
//    takes it home. Three deaths in its window - out, the Loch "not now" for two hours. Its spots: the regen's 1 810
//    lines (1 200 dark, 610 ice, groups of five or six aggressive 123-125 monsters) clustered by element (the "yellowish
//    dark rooms" and the ice rooms, tools: the map's grid walk from the arrival) - PLAYERBOT_LOCH_HUBS; the ice rooms
//    first, the dark ones only for a bot whose hunt element is dark (AdjustPlayerBotYoharaLochHubScore); spots of eight
//    lines and more a party's. A bot with a ticket keeps it (IsPlayerBotYoharaLochTicketKept - no sale, list, gift,
//    storage), and a Champion still levelling buys one off a counter under PLAYERBOT_LOCH_TICKET_PRICE_CAP. V3 sells the
//    ticket itself (29 SM, 20 for 449 SM): bought by the bots unless PLAYERBOT_LOCH_ISHOP=0 (on by default - the owner, 28 October: "boty mogą kupować wszystko w itemshopie"; was not in
//    the owner's list). The map is on game3 of each channel with every Sung Ma map; its 11 060 monsters are spawned
//    whether bots go there or not.
// 6. The boss route (PLAYERBOT_SUNGMA: boss_route). The bosses' spawn areas of the Sung Ma maps and the Loch
//    (PLAYERBOT_BOSS_AREAS: boss.txt of each map - Myr Prymus / Weteran 6723/6724 on Seoganland, 6730/6731 on Namgan,
//    Wielka Stopa and the War Chief (6782/6783/6894/6895) on Rozpadlina Dusz, Argos and Natanan on Dongan, the War
//    Chiefs of Yilad, Wawoz, Schronienie and Zejscie, Kao on the Twierdza, the Mnichy of the Loch), each with
//    its respawn (the regen's period, scaled by fastBossSpawn<map> as the engine scales it) and the loot it is worth
//    (PLAYERBOT_BOSS_WORTH: the drop tables of 28 October priced by playerbot_price_tables.h - dark jade, Northwind anvils,
//    the demon stones +4, the jade, ...). Memory a channel (the core's own): a kill seen (any bot's), a boss found
//    standing, an area found empty (due again in half its period). A party leader with three members by it, all over
//    PLAYERBOT_BOSS_ROUTE_READY_HP and the map's band floor + 2 Champion levels on average, plans a route over the areas
//    of its map that are due or unknown, by worth over the walk, takes the first, and goes on from there. A Weteran's
//    area is worth its Prymus's (it must be cleared for the Prymus to roll). The log: plan, arrive (found / empty),
//    give up, and the census of kills a boss an hour.
//
// The census: PLAYERBOT_SUNGMABUFF: census and PLAYERBOT_SUNGMA: guides census (boosters, the Loch, the boss route),
// from the Sung Ma census's clock.
//
// An implementation fragment: include it once, from playerbot_manager.cpp, after playerbot_ishop3_goals.h.

#if defined(MT2009_PLUS_BOT_YOHARA_GUIDES_V1) && defined(MT2009_PLUS_BOT_ISHOP_V3_V1)

namespace
{
	// ------------------------------------------------------------ the numbers

	const DWORD PLAYERBOT_SUNGMABUFF_PREMIUM_VNUM = 72803;
	const DWORD PLAYERBOT_SUNGMABUFF_ELIXIR_VNUM = 72804;	// 72804-72807: Sila, Witalnosc, Odpornosc, Inteligencja
	const DWORD PLAYERBOT_SUNGMABUFF_PREMIUM_AFFECT = 565;	// 565-568
	const DWORD PLAYERBOT_SUNGMABUFF_ELIXIR_AFFECT = 561;	// 561-564
	const int PLAYERBOT_SUNGMABUFF_PREMIUM_VALUE = 10;
	const int PLAYERBOT_SUNGMABUFF_ELIXIR_VALUE = 5;
	const DWORD PLAYERBOT_SUNGMABUFF_LOOK_MS = 60 * 1000;
	const long PLAYERBOT_SUNGMABUFF_RENEW_LEFT_S = 3 * 60 * 60;
	const int PLAYERBOT_SUNGMABUFF_RENEW_OVERHEAD = 8;	// SM a purchase: the risk of a lapse between two
	const DWORD PLAYERBOT_SUNGMABUFF_STRUGGLE_GAP_MS = 20 * 60 * 60 * 1000;
	const double PLAYERBOT_SUNGMABUFF_ELIXIR_MAX_HOURS = 0.5;
	const int PLAYERBOT_SUNGMABUFF_ELIXIR_MAX_DEATHS = 0;
	const int PLAYERBOT_SUNGMABUFF_ELIXIR_DAY_MAX = 3;
	const int PLAYERBOT_SUNGMABUFF_ELIXIR_MARKS_LEFT = 100;	// Smocze Znaki an elixir leaves at least
	const DWORD PLAYERBOT_SUNGMABUFF_RATE_MIN_MS = 15 * 60 * 1000;	// a bot's own champion rate only from this long
	const DWORD PLAYERBOT_SUNGMABUFF_RATE_RESET_MS = 3 * 60 * 60 * 1000;
	const double PLAYERBOT_SUNGMABUFF_UNKNOWN_HOURS = 12.0;	// no rate yet: a day's line, looked at again at renewal
	const double PLAYERBOT_SUNGMABUFF_MARGIN = 1.25;

	const DWORD PLAYERBOT_BOOSTER_LOOK_MS = 2 * 60 * 1000;
	const int PLAYERBOT_BOOSTER_MARKS_RESERVE = 400;	// an elixir (300) and a little more stay out of the boosters' reach
	const int PLAYERBOT_BOOSTER_DAY_MAX = 600;
	const int PLAYERBOT_BOOSTER_SLOW_KILLS_H = 150;
	const DWORD PLAYERBOT_BOOSTER_KILL_WINDOW_MS = 20 * 60 * 1000;
	const DWORD PLAYERBOT_BOOSTER_DAY_MS = 24 * 60 * 60 * 1000;
	const int PLAYERBOT_BOOSTER_HARD_SLOT = 4;	// Przelecz Yilad and up (PLAYERBOT_SUNGMA_MAPS)
	const DWORD PLAYERBOT_BOOSTER_HP = 71027, PLAYERBOT_BOOSTER_ATTACK = 71028, PLAYERBOT_BOOSTER_DEFENCE = 71030,
			PLAYERBOT_BOOSTER_CRITICAL = 71044;

	const DWORD PLAYERBOT_LOCH_TICKET_VNUM = 70408;
	const DWORD PLAYERBOT_LOCH_ALTAR_RACE = 20850;
	const DWORD PLAYERBOT_LOCH_EXIT_RACE = 10204;
	const long PLAYERBOT_LOCH_ALTAR_X = 1324400, PLAYERBOT_LOCH_ALTAR_Y = 459000;	// the quest's place by the altar (956,238)
	const long PLAYERBOT_LOCH_ARRIVAL_X = 160900, PLAYERBOT_LOCH_ARRIVAL_Y = 1061500;	// Town.txt (73,119)
	const long PLAYERBOT_LOCH_EXIT_X = 157500, PLAYERBOT_LOCH_EXIT_Y = 1061500;	// Wyjscie 10204 (39,119)
	const int PLAYERBOT_LOCH_REACH = 400;
	const int PLAYERBOT_LOCH_EXIT_WALK_NEAR = 12000;
	const int PLAYERBOT_LOCH_CHAMPION_MIN = 10;
	const int PLAYERBOT_LOCH_HP_FLOOR = 16000;
	const DWORD PLAYERBOT_LOCH_LOOK_MS = 3 * 60 * 1000;
	const DWORD PLAYERBOT_LOCH_STAY_MS = 120 * 60 * 1000;
	const DWORD PLAYERBOT_LOCH_GAP_MS = 60 * 60 * 1000;	// between two excursions of a bot
	const DWORD PLAYERBOT_LOCH_TO_ALTAR_MS = 6 * 60 * 1000;
	const DWORD PLAYERBOT_LOCH_EXIT_WALK_MS = 3 * 60 * 1000;
	const int PLAYERBOT_LOCH_DEATHS_OUT = 3;
	const int PLAYERBOT_LOCH_GO_PERCENT = 35;	// an eligible bot's chance a look (the tickets are few - the rest wait)
	const int PLAYERBOT_LOCH_TICKET_MARKET_HOLD = 2;
	const DWORD PLAYERBOT_LOCH_TICKET_PRICE_CAP = 1500000;
	const int PLAYERBOT_LOCH_TICKET_PURSE_PCT = 25;
	const int PLAYERBOT_LOCH_ICE = 2, PLAYERBOT_LOCH_DARK = 5;	// PLAYERBOT_YOHARA_ELEMENT_NAMES' indexes

	const DWORD PLAYERBOT_BOSS_ROUTE_LOOK_MS = 15 * 1000;
	const DWORD PLAYERBOT_BOSS_ROUTE_LEG_MS = 4 * 60 * 1000;
	const int PLAYERBOT_BOSS_ROUTE_ARRIVE = 1500;
	const int PLAYERBOT_BOSS_ROUTE_SCAN = 4000;
	const int PLAYERBOT_BOSS_ROUTE_READY_HP = 60;
	const int PLAYERBOT_BOSS_ROUTE_RED_MIN = 40;
	const int PLAYERBOT_BOSS_ROUTE_HALF_WALK = 25000;
	const DWORD PLAYERBOT_BOSS_ROUTE_SKIP_MS = 10 * 60 * 1000;	// an area given up (unreachable, too long)
	const DWORD PLAYERBOT_BOSS_ROUTE_SEEN_MS = 10 * 60 * 1000;	// a boss found standing is "there" this long
	const int PLAYERBOT_BOSS_ROUTE_UNKNOWN_PCT = 60;
	const int PLAYERBOT_BOSS_ROUTE_PLAN_STOPS = 3;
	const DWORD PLAYERBOT_GUIDES_CENSUS_MS = 30 * 60 * 1000;

	// ------------------------------------------------------------ the Loch's spots

	// tools: the live map files of 28 October (regen.txt 1 810 lines, server_attr), each element's spawn lines clustered
	// (the densest 30x30-cell window first, 3 000 apart), snapped to open ground (4 free cells round) the arrival's walk
	// reaches - the whole map is one piece; the level column 100 + the Champion floor by the walk from the arrival
	// (110 to 1 500 m, 111 to 3 000 m, 112 farther); eight lines and more - a party's; the three Mnichy - a party's boss.
	const TPlayerBotHuntingHub PLAYERBOT_LOCH_HUBS[] = {
		{ 167050, 1087750, 110, 255, true, 0 },		// dark 9 lines, walk 323 m from the arrival
		{ 182050, 1124250, 110, 255, true, 0 },		// dark 8, 960 m
		{ 296650, 1080450, 111, 255, true, 0 },		// dark 9, 2034 m
		{ 264050, 1079950, 111, 255, true, 0 },		// dark 8, 2129 m
		{ 230050, 1149650, 111, 255, true, 0 },		// dark 8, 2272 m
		{ 304150, 1102350, 111, 255, true, 0 },		// dark 9, 2328 m
		{ 264350, 1116850, 111, 255, true, 0 },		// dark 8, 2495 m
		{ 264250, 1142250, 111, 255, true, 0 },		// dark 9, 2750 m
		{ 278550, 1142250, 111, 255, true, 0 },		// dark 8, 2763 m
		{ 217350, 1128050, 112, 255, false, 0 },	// dark 7, 3077 m
		{ 202350, 1128050, 112, 255, true, 0 },		// dark 8, 3227 m
		{ 239850, 1173750, 112, 255, true, 0 },		// dark 8, 4315 m
		{ 160350, 1160250, 110, 255, false, 0 },	// ice 4, 1111 m
		{ 177850, 1148650, 110, 255, true, 0 },		// ice 8, 1170 m
		{ 218250, 1079350, 110, 255, false, 0 },	// ice 7, 1239 m
		{ 235650, 1062650, 110, 255, false, 0 },	// ice 6, 1246 m
		{ 229450, 1079750, 110, 255, false, 0 },	// ice 6, 1355 m
		{ 196350, 1149350, 110, 255, false, 0 },	// ice 5, 1362 m
		{ 178450, 1179150, 110, 255, false, 0 },	// ice 7, 1481 m
		{ 266650, 1063350, 111, 255, false, 0 },	// ice 5 (dark 4 by it), 1563 m
		{ 177750, 1194150, 111, 255, true, 0 },		// ice 8 (dark 3 by it), 1624 m
		{ 222050, 1178350, 111, 255, false, 0 },	// ice 6, 1909 m
		{ 208650, 1159350, 111, 255, true, 0 },		// ice 8, 1961 m
		{ 222250, 1191850, 111, 255, false, 0 },	// ice 4, 2046 m
		{ 191350, 1138850, 112, 255, false, 0 },	// ice 6, 3445 m
		{ 192250, 1114150, 112, 255, true, 0 },		// ice 9, 3455 m
		{ 294850, 1194350, 112, 255, false, 0 },	// ice 5 (dark 3 by it), 3543 m
		{ 282950, 1192850, 112, 255, false, 0 },	// ice 5 (dark 4 by it), 3655 m
		{ 243750, 1169150, 112, 255, true, 0 },		// ice 9, 4284 m
		{ 236350, 1169350, 112, 255, false, 0 },	// ice 7, 4356 m
		{ 296050, 1194050, 112, 255, true, 6870 },	// boss Tajemniczy Mnich (ice), 127, 1.85 M HP, 6 h
		{ 237950, 1171350, 112, 255, true, 6871 },	// boss Tajemniczy Mnich (dark), 127, 1.85 M HP, 6 h
		{ 197350, 1178450, 111, 255, true, 6871 },	// boss Tajemniczy Mnich (dark), 127, 1.85 M HP, 6 h
	};
	const int PLAYERBOT_LOCH_HUB_ELEMENT[] = {
		PLAYERBOT_LOCH_DARK, PLAYERBOT_LOCH_DARK, PLAYERBOT_LOCH_DARK, PLAYERBOT_LOCH_DARK, PLAYERBOT_LOCH_DARK,
		PLAYERBOT_LOCH_DARK, PLAYERBOT_LOCH_DARK, PLAYERBOT_LOCH_DARK, PLAYERBOT_LOCH_DARK, PLAYERBOT_LOCH_DARK,
		PLAYERBOT_LOCH_DARK, PLAYERBOT_LOCH_DARK,
		PLAYERBOT_LOCH_ICE, PLAYERBOT_LOCH_ICE, PLAYERBOT_LOCH_ICE, PLAYERBOT_LOCH_ICE, PLAYERBOT_LOCH_ICE,
		PLAYERBOT_LOCH_ICE, PLAYERBOT_LOCH_ICE, PLAYERBOT_LOCH_ICE, PLAYERBOT_LOCH_ICE, PLAYERBOT_LOCH_ICE,
		PLAYERBOT_LOCH_ICE, PLAYERBOT_LOCH_ICE, PLAYERBOT_LOCH_ICE, PLAYERBOT_LOCH_ICE, PLAYERBOT_LOCH_ICE,
		PLAYERBOT_LOCH_ICE, PLAYERBOT_LOCH_ICE, PLAYERBOT_LOCH_ICE,
		PLAYERBOT_LOCH_ICE, PLAYERBOT_LOCH_DARK, PLAYERBOT_LOCH_DARK,
	};
	static_assert(sizeof(PLAYERBOT_LOCH_HUBS) / sizeof(PLAYERBOT_LOCH_HUBS[0]) ==
			sizeof(PLAYERBOT_LOCH_HUB_ELEMENT) / sizeof(PLAYERBOT_LOCH_HUB_ELEMENT[0]), "an element a Loch spot");

	// ------------------------------------------------------------ the bosses' areas

	// boss.txt of each map (the live files of 28 October; x, y = the map's base + the line's cell x 100): the map, the
	// spot, the races that roll there (an "r" line: one of its group_group's groups a respawn), the period in seconds.
	// Left out: the Twierdza's King Bao lines (6692 / 6699 every 10 s - the quest's, already the boss spots' raid).
	struct TPlayerBotBossArea
	{
		long lMap, x, y;
		DWORD adwRace[4];
		DWORD dwPeriodS;
		const char* szName;
	};
	const TPlayerBotBossArea PLAYERBOT_BOSS_AREAS[] = {
		{ 374, 544800, 509200, { 6698, 0, 0, 0 }, 3600, "kao" },
		{ 374, 547000, 505400, { 6698, 0, 0, 0 }, 3600, "kao" },
		{ 373, 1056300, 498700, { 6706, 0, 0, 0 }, 3600, "argos" },
		{ 373, 1117000, 523200, { 6717, 0, 0, 0 }, 3600, "argos" },
		{ 373, 1111500, 487800, { 6716, 0, 0, 0 }, 3600, "natanan" },
		{ 373, 1071600, 555200, { 6706, 6716, 6717, 0 }, 3600, "argos_natanan" },
		{ 373, 1142600, 485400, { 6705, 6706, 6716, 6717 }, 3600, "argos_natanan" },
		{ 376, 1198500, 511100, { 6724, 0, 0, 0 }, 3600, "prymus" },
		{ 376, 1192000, 545200, { 6723, 0, 0, 0 }, 3600, "weteran" },
		{ 376, 1204000, 516200, { 6723, 6724, 0, 0 }, 3600, "weteran_prymus" },
		{ 377, 1293600, 463600, { 6731, 0, 0, 0 }, 3600, "prymus" },
		{ 377, 1245800, 470200, { 6730, 0, 0, 0 }, 3600, "weteran" },
		{ 377, 1288800, 458200, { 6730, 0, 0, 0 }, 3600, "weteran" },
		{ 377, 1321600, 450200, { 6705, 0, 0, 0 }, 3600, "natanan" },
		{ 377, 1283800, 443200, { 6705, 0, 0, 0 }, 3600, "natanan" },
		{ 385, 115000, 1438000, { 6763, 6764, 6880, 6881 }, 3600, "war_chief" },
		{ 385, 119500, 1462000, { 6763, 6764, 6880, 6881 }, 3600, "war_chief" },
		{ 388, 58000, 1585400, { 6775, 6776, 6887, 6888 }, 3600, "war_chief" },
		{ 388, 85000, 1595400, { 6775, 6776, 6887, 6888 }, 3600, "war_chief" },
		{ 389, 148000, 1560400, { 6782, 6783, 6894, 6895 }, 3600, "bigfoot_war_chief" },
		{ 389, 190000, 1535400, { 6782, 6894, 6895, 0 }, 3600, "bigfoot_war_chief" },
		{ 393, 1018400, 1320200, { 6789, 0, 0, 0 }, 3600, "war_chief" },
		{ 393, 1037400, 1224000, { 6789, 0, 0, 0 }, 3600, "war_chief" },
		{ 393, 1044400, 1323200, { 6789, 0, 0, 0 }, 3600, "war_chief" },
		{ 393, 1053900, 1233200, { 6789, 0, 0, 0 }, 3600, "war_chief" },
		{ 393, 1062400, 1276200, { 6789, 0, 0, 0 }, 3600, "war_chief" },
		{ 393, 1075700, 1334600, { 6789, 0, 0, 0 }, 3600, "war_chief" },
		{ 393, 1088400, 1336200, { 6789, 0, 0, 0 }, 3600, "war_chief" },
		{ 393, 1109500, 1286200, { 6789, 0, 0, 0 }, 3600, "war_chief" },
		{ 393, 1119900, 1298200, { 6789, 0, 0, 0 }, 3600, "war_chief" },
		{ 393, 1146400, 1256200, { 6789, 0, 0, 0 }, 3600, "war_chief" },
		{ 394, 1187400, 1218000, { 6797, 0, 0, 0 }, 1800, "war_chief" },
		{ 394, 1199500, 1209000, { 6797, 0, 0, 0 }, 1800, "war_chief" },
		{ 396, 296000, 1194000, { 6870, 0, 0, 0 }, 21600, "mnich" },
		{ 396, 237900, 1171300, { 6871, 0, 0, 0 }, 21600, "mnich" },
		{ 396, 197300, 1178400, { 6871, 0, 0, 0 }, 21600, "mnich" },
		{ 396, 171300, 1148400, { 6870, 6871, 0, 0 }, 21600, "mnich" },
		{ 396, 181700, 1063000, { 6870, 6871, 0, 0 }, 21600, "mnich" },
		{ 396, 196400, 1114800, { 6870, 6871, 0, 0 }, 21600, "mnich" },
		{ 396, 222900, 1061900, { 6870, 6871, 0, 0 }, 21600, "mnich" },
		{ 396, 223300, 1192600, { 6870, 6871, 0, 0 }, 21600, "mnich" },
		{ 396, 228700, 1079900, { 6870, 6871, 0, 0 }, 21600, "mnich" },
		{ 396, 269200, 1141600, { 6870, 6871, 0, 0 }, 21600, "mnich" },
	};
	const int PLAYERBOT_BOSS_AREA_COUNT = (int)(sizeof(PLAYERBOT_BOSS_AREAS) / sizeof(PLAYERBOT_BOSS_AREAS[0]));

	// The loot a kill is worth (yang): the expected value of each boss's drop groups (mob_drop_item.txt of 28 October -
	// drop rows at their chance, kill rows at chance / kill_drop, the chests at their own groups' average) priced by
	// playerbot_price_tables.h. The top lines: Myr 6723/6724 Szkatulka (83066), Kamien Mocy Demonow +4 (50529),
	// Peleryna Mestwa, Jadeit Nocy (50662); Wielka Stopa / War Chief of Rozpadlina + the Northwind anvil (49991);
	// Argos 50662 / 50661 jade; Zejscie's chief the Northwind anvils (31239-31241).
	struct TPlayerBotBossWorth { DWORD dwRace; DWORD dwWorth; };
	const TPlayerBotBossWorth PLAYERBOT_BOSS_WORTH[] = {
		{ 6698, 1415000 }, { 6699, 2086000 }, { 6705, 1549000 }, { 6706, 2222000 }, { 6716, 1551000 },
		{ 6717, 2225000 }, { 6723, 909000 }, { 6724, 911000 }, { 6730, 909000 }, { 6731, 911000 },
		{ 6763, 616000 }, { 6764, 819000 }, { 6880, 617000 }, { 6881, 820000 }, { 6775, 634000 },
		{ 6776, 1036000 }, { 6887, 635000 }, { 6888, 1006000 }, { 6782, 1098000 }, { 6783, 1088000 },
		{ 6894, 1098000 }, { 6895, 1089000 }, { 6789, 803000 }, { 6797, 1868000 }, { 6870, 319000 },
		{ 6871, 319000 },
	};

	DWORD GetPlayerBotBossWorth(DWORD race)
	{
		for (size_t i = 0; i < sizeof(PLAYERBOT_BOSS_WORTH) / sizeof(PLAYERBOT_BOSS_WORTH[0]); ++i)
			if (PLAYERBOT_BOSS_WORTH[i].dwRace == race)
				return PLAYERBOT_BOSS_WORTH[i].dwWorth;
		return 0;
	}

	// A Weteran is worth its Prymus: its area must be cleared before the Prymus can roll there again.
	DWORD GetPlayerBotBossAreaWorth(const TPlayerBotBossArea& a)
	{
		DWORD sum = 0, n = 0;
		for (int i = 0; i < 4 && a.adwRace[i]; ++i)
		{
			DWORD w = GetPlayerBotBossWorth(a.adwRace[i]);
			if (a.adwRace[i] == 6723)
				w = std::max(w, GetPlayerBotBossWorth(6724));
			else if (a.adwRace[i] == 6730)
				w = std::max(w, GetPlayerBotBossWorth(6731));
			sum += w;
			++n;
		}
		return n ? sum / n : 0;
	}

	// ------------------------------------------------------------ the state

	struct TPlayerBotGuideBot
	{
		// 2. the buffs
		DWORD dwNextBuffLook, dwRateSince, dwRateExp, dwLastStruggleBuff, dwBuffedAt, dwElixirDay;
		int iRateLevel, iElixirsToday;
		long lBuffedFor;		// the map the premium / an elixir was bought for (its step up counted)
		double dRateExpH;		// champion experience an hour (0: not known yet)
		// 3. the boosters
		DWORD dwNextBoosterLook, dwBoosterDay, dwKillWindow;
		int iBoosterSpent, iKills, iKillsH;
		// 4. the Loch
		int iLochPhase;			// 0 none, 1 to the altar, 2 inside, 3 to the exit
		DWORD dwLochSince, dwNextLochLook, dwLochEnded, dwLochExitWalk;
		int iLochDeaths;		// the stay's deaths when it went in
		// 6. the boss route (a leader)
		int iRouteArea;
		DWORD dwRouteSince, dwNextRouteLook;
		TPlayerBotGuideBot() : dwNextBuffLook(0), dwRateSince(0), dwRateExp(0), dwLastStruggleBuff(0), dwBuffedAt(0),
			dwElixirDay(0), iRateLevel(0), iElixirsToday(0), lBuffedFor(0), dRateExpH(0.0), dwNextBoosterLook(0),
			dwBoosterDay(0), dwKillWindow(0), iBoosterSpent(0), iKills(0), iKillsH(-1), iLochPhase(0), dwLochSince(0),
			dwNextLochLook(0), dwLochEnded(0), dwLochExitWalk(0), iLochDeaths(0), iRouteArea(-1), dwRouteSince(0),
			dwNextRouteLook(0) {}
	};
	std::map<DWORD, TPlayerBotGuideBot> s_mapPlayerBotGuide;

	struct TPlayerBotBossAreaMemory
	{
		DWORD dwKilledAt, dwSeenAt, dwEmptyAt, dwSkipUntil;
		DWORD dwLastRace;
		TPlayerBotBossAreaMemory() : dwKilledAt(0), dwSeenAt(0), dwEmptyAt(0), dwSkipUntil(0), dwLastRace(0) {}
	};
	TPlayerBotBossAreaMemory s_aPlayerBotBossArea[sizeof(PLAYERBOT_BOSS_AREAS) / sizeof(PLAYERBOT_BOSS_AREAS[0])];

	struct TPlayerBotGuidesStats
	{
		// 2.
		unsigned int premium[4], premiumFor[4], premiumNoCoins, premiumUsed, premiumUseFailed, elixirs[4], elixirNoMarks,
				stepUps, renewals, struggles;
		long long premiumCoins, elixirMarks;
		// 3.
		unsigned int boosters, boosterBudget;
		long long boosterMarks;
		std::map<DWORD, unsigned int> boosterBy;
		// 4.
		unsigned int lochTrips, lochEntries, lochExits, lochDeathsOut, lochAborts, lochTicketsUsed, lochTicketsBought,
				lochTicketsV3, lochNoAltar;
		// 6.
		unsigned int routes, arrived, found, empty, giveUps;
		std::map<DWORD, unsigned int> bossKills;
		DWORD dwSince;
		TPlayerBotGuidesStats() : premiumNoCoins(0), premiumUsed(0), premiumUseFailed(0), elixirNoMarks(0), stepUps(0),
			renewals(0), struggles(0), premiumCoins(0), elixirMarks(0), boosters(0), boosterBudget(0), boosterMarks(0),
			lochTrips(0), lochEntries(0), lochExits(0), lochDeathsOut(0), lochAborts(0), lochTicketsUsed(0),
			lochTicketsBought(0), lochTicketsV3(0), lochNoAltar(0), routes(0), arrived(0), found(0), empty(0), giveUps(0),
			dwSince(0)
		{
			for (int i = 0; i < 4; ++i)
				premium[i] = premiumFor[i] = elixirs[i] = 0;
		}
	};
	TPlayerBotGuidesStats s_kPlayerBotGuides;
	DWORD s_dwPlayerBotGuidesLastCensus = 0;

	int GetPlayerBotLochMax()
	{
		static int s_iMax = -1;
		if (s_iMax < 0)
			s_iMax = ReadPlayerBotYoharaEnvInt("PLAYERBOT_LOCH_MAX", 20, 0, 200);
		return s_iMax;
	}

	bool IsPlayerBotLochIshopOn()
	{
		static int s_iOn = -1;
		if (s_iOn < 0)
			s_iOn = ReadPlayerBotYoharaEnvInt("PLAYERBOT_LOCH_ISHOP", 1, 0, 1);
		return s_iOn == 1;
	}

	long GetPlayerBotGuideBase(long mapIndex)
	{
		return mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? mapIndex / 10000 : mapIndex;
	}

	// ------------------------------------------------------------ 2. the Sung Ma buffs

	// The champion experience the bot makes an hour, from its own samples (0: not known yet).
	double SamplePlayerBotChampionRate(LPCHARACTER ch, TPlayerBotGuideBot& g, DWORD dwNow)
	{
#ifdef ENABLE_CONQUEROR_LEVEL
		const int level = (int)ch->GetConquerorLevel();
		const DWORD exp = ch->GetConquerorExp();
		if (g.dwRateSince == 0 || level < g.iRateLevel || dwNow - g.dwRateSince >= PLAYERBOT_SUNGMABUFF_RATE_RESET_MS)
		{
			// a long sample is kept as the rate before a new one starts
			if (g.dwRateSince != 0 && level >= g.iRateLevel && dwNow - g.dwRateSince >= PLAYERBOT_SUNGMABUFF_RATE_MIN_MS)
			{
				long long gained = (long long)exp;
				for (int l = g.iRateLevel; l < level; ++l)
					gained += (long long)champion::NextExp(l) - (l == g.iRateLevel ? (long long)g.dwRateExp : 0);
				if (level == g.iRateLevel)
					gained = (long long)exp - (long long)g.dwRateExp;
				g.dRateExpH = std::max(0.0, (double)gained * 3600000.0 / (double)(dwNow - g.dwRateSince));
			}
			g.dwRateSince = dwNow ? dwNow : 1;
			g.iRateLevel = level;
			g.dwRateExp = exp;
			return g.dRateExpH;
		}
		if (dwNow - g.dwRateSince < PLAYERBOT_SUNGMABUFF_RATE_MIN_MS)
			return g.dRateExpH;
		long long gained = (long long)exp;
		for (int l = g.iRateLevel; l < level; ++l)
			gained += (long long)champion::NextExp(l) - (l == g.iRateLevel ? (long long)g.dwRateExp : 0);
		if (level == g.iRateLevel)
			gained = (long long)exp - (long long)g.dwRateExp;
		const double now = std::max(0.0, (double)gained * 3600000.0 / (double)(dwNow - g.dwRateSince));
		g.dRateExpH = g.dRateExpH > 0.0 ? (g.dRateExpH + now) / 2.0 : now;
		return g.dRateExpH;
#else
		(void)ch; (void)g; (void)dwNow;
		return 0.0;
#endif
	}

	// The hours the bot's points need to bring `points` Sung Ma points (3 a Champion level): -1 never (the top level, no
	// point to come), PLAYERBOT_SUNGMABUFF_UNKNOWN_HOURS while its rate is unknown.
	double GetPlayerBotSungmaPointHours(LPCHARACTER ch, const TPlayerBotGuideBot& g, int points)
	{
#ifdef ENABLE_CONQUEROR_LEVEL
		if (points <= 0)
			return 0.0;
		int level = (int)ch->GetConquerorLevel();
		const int spare = ch->GetConquerorPoint();
		points -= std::max(0, spare);
		if (points <= 0)
			return 0.0;
		if (level >= (int)champion::MAX_LEVEL)
			return -1.0;
		if (g.dRateExpH <= 0.0)
			return PLAYERBOT_SUNGMABUFF_UNKNOWN_HOURS;
		double exp = (double)champion::NextExp(level) - (double)ch->GetConquerorExp();
		int got = (int)champion::POINTS_PER_LEVEL;
		while (got < points && level + 1 < (int)champion::MAX_LEVEL)
		{
			++level;
			exp += (double)champion::NextExp(level);
			got += (int)champion::POINTS_PER_LEVEL;
		}
		if (got < points)
			return -1.0;
		return std::max(0.0, exp) / g.dRateExpH;
#else
		(void)ch; (void)g; (void)points;
		return -1.0;
#endif
	}

	// The Will the premium / the elixirs add now (what a stat would be without them).
	int GetPlayerBotSungmaBuffWill(LPCHARACTER ch, int stat)
	{
		int add = 0;
		if (ch->FindAffect(PLAYERBOT_SUNGMABUFF_PREMIUM_AFFECT + stat))
			add += PLAYERBOT_SUNGMABUFF_PREMIUM_VALUE;
		if (ch->FindAffect(PLAYERBOT_SUNGMABUFF_ELIXIR_AFFECT + stat))
			add += PLAYERBOT_SUNGMABUFF_ELIXIR_VALUE;
		return add;
	}

	long GetPlayerBotSungmaPremiumLeft(LPCHARACTER ch)
	{
		const CAffect* a = ch->FindAffect(PLAYERBOT_SUNGMABUFF_PREMIUM_AFFECT);
		return a ? a->lDuration : 0;
	}

	// The next map up the bot would step onto were it not for its Will: its slot, and every stat's gap (requirement - Will,
	// positive = short); -1 when something else holds it (the band, the health, the room, the element, "not now") or it
	// is ready already.
	int GetPlayerBotSungmaNextGaps(LPCHARACTER ch, const TPlayerBotYoharaResident& res, const TPlayerBotSungmaBot& b,
			int gaps[4], DWORD dwNow)
	{
		const int current = GetPlayerBotSungmaSlot(res.lMap);
		if (current < 0)
			return -1;
		const int champion = GetPlayerBotChampionLevel(ch);
		for (int s = current + 1; s < PLAYERBOT_SUNGMA_MAP_COUNT; ++s)
		{
			const TPlayerBotSungmaMap& m = PLAYERBOT_SUNGMA_MAPS[s];
			if (!IsPlayerBotSungmaMapOn(m.lMap))
				continue;
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
			if (!IsPlayerBotSungmaElementMoveAllowed(ch, m.lMap, false))
				return -1;
#endif
			std::map<long, DWORD>::const_iterator nn = b.mapNotNow.find(m.lMap);
			if (nn != b.mapNotNow.end() && (int)(nn->second - dwNow) > 0)
				return -1;
			if (champion < (int)m.bChampionMin + PLAYERBOT_SUNGMA_STEP_UP_LEVELS || !IsPlayerBotSungmaHpEnough(ch, s, false) ||
					!HasPlayerBotSungmaRoom(s, res.lMap))
				return -1;
			bool any = false;
			for (int i = 0; i < 4; ++i)
			{
				gaps[i] = GetPlayerBotSungmaReq(s, i) - GetPlayerBotSungmaWill(ch, i);
				any = any || gaps[i] > 0;
			}
			return any ? s : -1;
		}
		return -1;
	}

	// The bot's Will is held up on its own map by the buffs (without them a stat its map asks would be short).
	bool IsPlayerBotSungmaHeldByBuff(LPCHARACTER ch, const TPlayerBotYoharaResident& res)
	{
		const int slot = GetPlayerBotSungmaSlot(res.lMap);
		if (slot < 0)
			return false;
		for (int i = 0; i < 3; ++i)
			if (GetPlayerBotSungmaWill(ch, i) - GetPlayerBotSungmaBuffWill(ch, i) < GetPlayerBotSungmaReq(slot, i))
				return true;
		return false;
	}

	// The premium's cheapest cover of `hours` (-1: as long as possible): the line and the purchases it takes.
	const TPlayerBotItemShopEntry* PickPlayerBotSungmaPremiumLine(LPCHARACTER ch, double hours, int& dayIndex)
	{
		std::vector<const TPlayerBotItemShopEntry*> lines;
		SortPlayerBotIshop3Lines(ch, PLAYERBOT_SUNGMABUFF_PREMIUM_VNUM, false, lines);
		const TPlayerBotItemShopEntry* best = NULL;
		long long bestCost = 0;
		for (size_t i = 0; i < lines.size(); ++i)
		{
			const DWORD minutes = lines[i]->dwMinutes ? lines[i]->dwMinutes : 1440;
			const double cover = hours < 0.0 ? 30.0 * 24.0 : std::max(1.0, hours * PLAYERBOT_SUNGMABUFF_MARGIN);
			const long long n = std::max<long long>(1, (long long)std::ceil(cover * 60.0 / (double)minutes));
			const long long cost = n * ((long long)lines[i]->dwPrice + PLAYERBOT_SUNGMABUFF_RENEW_OVERHEAD);
			if (!best || cost < bestCost || (cost == bestCost && minutes > best->dwMinutes))
			{
				best = lines[i];
				bestCost = cost;
			}
		}
		dayIndex = 0;
		if (best)
		{
			const DWORD days = (best->dwMinutes ? best->dwMinutes : 1440) / 1440;
			dayIndex = days >= 30 ? 3 : (days >= 15 ? 2 : (days >= 7 ? 1 : 0));
		}
		return best;
	}

	// Uses a held 72803 / elixir: the affect is the proof (the quest's own use).
	bool UsePlayerBotSungmaBuffItem(LPCHARACTER ch, DWORD vnum, DWORD affect)
	{
		LPITEM item = ch->FindSpecifyItem(vnum);
		if (!item)
			return false;
		const long before = ch->FindAffect(affect) ? ch->FindAffect(affect)->lDuration : 0;
		if (!ch->UseItem(TItemPos(INVENTORY, item->GetCell())))
			return false;
		const CAffect* a = ch->FindAffect(affect);
		return a && a->lDuration > before;
	}

	// One premium line bought and used (why: next / renew / struggle).
	bool BuyPlayerBotSungmaPremium(LPCHARACTER ch, TPlayerBotAIState& state, double hours, const char* why, long forMap,
			DWORD dwNow)
	{
		const long leftBefore = GetPlayerBotSungmaPremiumLeft(ch);
		if (ch->CountSpecifyItem(PLAYERBOT_SUNGMABUFF_PREMIUM_VNUM) == 0)
		{
			int dayIndex = 0;
			const TPlayerBotItemShopEntry* line = PickPlayerBotSungmaPremiumLine(ch, hours, dayIndex);
			if (!line)
				return false;
			EnsurePlayerBotIshop3FreshBalance(ch, state, dwNow);
			if (state.iDragonCoins < (int)line->dwPrice)
			{
				++s_kPlayerBotGuides.premiumNoCoins;
				PlayerBotLogThrottled("sungmabuff_no_coins", dwNow, "PLAYERBOT_SUNGMABUFF: no coins pid=%u name=%s why=%s price=%u coins=%d",
						ch->GetPlayerID(), ch->GetName(), why, line->dwPrice, state.iDragonCoins);
				return false;
			}
			// MT2009_PLUS_BOT_SM_DAILY_POOL_V1: the Will alone before the next map is urgent (the daily pool's borrow)
			if (!BuyPlayerBotIshop3Line(ch, state, *line, PLAYERBOT_SUNGMABUFF_PREMIUM_VNUM, false, 1,
					strcmp(why, "next_map") == 0 ? "sungma_buff_next" : "sungma_buff", dwNow))
				return false;
			++s_kPlayerBotGuides.premium[dayIndex];
			s_kPlayerBotGuides.premiumCoins += line->dwPrice;
			sys_log(0, "PLAYERBOT_SUNGMABUFF: bought pid=%u name=%s why=%s days=%u price=%u hours_needed=%.1f map=%ld for=%ld coins=%d",
					ch->GetPlayerID(), ch->GetName(), why, (line->dwMinutes ? line->dwMinutes : 1440) / 1440, line->dwPrice,
					hours, ch->GetMapIndex(), forMap, state.iDragonCoins);
		}
		if (!UsePlayerBotSungmaBuffItem(ch, PLAYERBOT_SUNGMABUFF_PREMIUM_VNUM, PLAYERBOT_SUNGMABUFF_PREMIUM_AFFECT))
		{
			++s_kPlayerBotGuides.premiumUseFailed;
			PlayerBotLogThrottled("sungmabuff_use_failed", dwNow, "PLAYERBOT_SUNGMABUFF: use failed pid=%u name=%s why=%s",
					ch->GetPlayerID(), ch->GetName(), why);
			return false;
		}
		++s_kPlayerBotGuides.premiumUsed;
		sys_log(0, "PLAYERBOT_SUNGMABUFF: used pid=%u name=%s why=%s left_h=%ld->%ld will=%d/%d/%d/%d map=%ld for=%ld",
				ch->GetPlayerID(), ch->GetName(), why, leftBefore / 3600, GetPlayerBotSungmaPremiumLeft(ch) / 3600,
				GetPlayerBotSungmaWill(ch, 0), GetPlayerBotSungmaWill(ch, 1), GetPlayerBotSungmaWill(ch, 2),
				GetPlayerBotSungmaWill(ch, 3), ch->GetMapIndex(), forMap);
		return true;
	}

	bool BuyPlayerBotSungmaElixir(LPCHARACTER ch, TPlayerBotAIState& state, int stat, long forMap, DWORD dwNow)
	{
		const DWORD vnum = PLAYERBOT_SUNGMABUFF_ELIXIR_VNUM + (DWORD)stat;
		if (ch->CountSpecifyItem(vnum) == 0)
		{
			std::vector<const TPlayerBotItemShopEntry*> lines;
			SortPlayerBotIshop3Lines(ch, vnum, true, lines);
			if (lines.empty())
				return false;
			EnsurePlayerBotIshop3FreshBalance(ch, state, dwNow);
			if (state.iDragonMarks < (int)lines[0]->dwPrice + PLAYERBOT_SUNGMABUFF_ELIXIR_MARKS_LEFT)
			{
				++s_kPlayerBotGuides.elixirNoMarks;
				return false;
			}
			if (!BuyPlayerBotIshop3Line(ch, state, *lines[0], vnum, true, 1, "sungma_elixir", dwNow))
				return false;
			++s_kPlayerBotGuides.elixirs[stat];
			s_kPlayerBotGuides.elixirMarks += lines[0]->dwPrice;
		}
		if (!UsePlayerBotSungmaBuffItem(ch, vnum, PLAYERBOT_SUNGMABUFF_ELIXIR_AFFECT + stat))
			return false;
		static const char* const s_aName[4] = { "str", "hp", "move", "immune" };
		sys_log(0, "PLAYERBOT_SUNGMABUFF: elixir pid=%u name=%s stat=%s will=%d/%d/%d/%d map=%ld for=%ld marks=%d",
				ch->GetPlayerID(), ch->GetName(), s_aName[stat], GetPlayerBotSungmaWill(ch, 0), GetPlayerBotSungmaWill(ch, 1),
				GetPlayerBotSungmaWill(ch, 2), GetPlayerBotSungmaWill(ch, 3), ch->GetMapIndex(), forMap, state.iDragonMarks);
		return true;
	}

	void ManagePlayerBotSungmaBuff(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotYoharaResident& res,
			TPlayerBotSungmaBot& b, TPlayerBotGuideBot& g, long base, DWORD dwNow)
	{
		if ((int)(dwNow - g.dwNextBuffLook) < 0)
			return;
		g.dwNextBuffLook = dwNow + PLAYERBOT_SUNGMABUFF_LOOK_MS;
		SamplePlayerBotChampionRate(ch, g, dwNow);
		// the step up the buff was bought for, made
		if (g.lBuffedFor != 0 && res.lMap == g.lBuffedFor)
		{
			++s_kPlayerBotGuides.stepUps;
			sys_log(0, "PLAYERBOT_SUNGMABUFF: stepped up pid=%u name=%s map=%ld after_s=%u will=%d/%d/%d/%d",
					ch->GetPlayerID(), ch->GetName(), res.lMap, (dwNow - g.dwBuffedAt) / 1000, GetPlayerBotSungmaWill(ch, 0),
					GetPlayerBotSungmaWill(ch, 1), GetPlayerBotSungmaWill(ch, 2), GetPlayerBotSungmaWill(ch, 3));
			g.lBuffedFor = 0;
		}
		if (base != res.lMap || GetPlayerBotItemShopSource() != 2 || !IsPlayerBotItemShopEnabled() || ch->IsDead() ||
				!ch->IsItemLoaded() || !ch->CanHandleItem() || ch->GetExchange() || ch->GetMyShop())
			return;
		if (dwNow - b.dwOnMapSince < PLAYERBOT_SUNGMA_FIT_SETTLE_MS)
			return;
		RefreshPlayerBotItemShopCatalogue(dwNow);
		const long left = GetPlayerBotSungmaPremiumLeft(ch);
		// (a) the renewal: it still holds the bot where it stands
		if (left > 0 && left < PLAYERBOT_SUNGMABUFF_RENEW_LEFT_S && IsPlayerBotSungmaHeldByBuff(ch, res))
		{
			const int slot = GetPlayerBotSungmaSlot(res.lMap);
			int points = 0;
			for (int i = 0; i < 3; ++i)
				points += std::max(0, GetPlayerBotSungmaReq(slot, i) - (GetPlayerBotSungmaWill(ch, i) - GetPlayerBotSungmaBuffWill(ch, i)));
			if (BuyPlayerBotSungmaPremium(ch, state, GetPlayerBotSungmaPointHours(ch, g, points), "renew", res.lMap, dwNow))
				++s_kPlayerBotGuides.renewals;
			return;
		}
		// (b) the Will alone between it and the next map
		int gaps[4] = { 0, 0, 0, 0 };
		const int next = GetPlayerBotSungmaNextGaps(ch, res, b, gaps, dwNow);
		if (next >= 0)
		{
			int short_ = 0, worst = 0, stat = -1, points = 0;
			for (int i = 0; i < 4; ++i)
				if (gaps[i] > 0)
				{
					++short_;
					worst = std::max(worst, gaps[i]);
					stat = i;
					points += gaps[i];
				}
			const double hours = GetPlayerBotSungmaPointHours(ch, g, points);
			const long nextMap = PLAYERBOT_SUNGMA_MAPS[next].lMap;
			// the elixir: one stat, 1-5 short, closed within its half hour, a bot that has not died in its window
			if (short_ == 1 && worst <= PLAYERBOT_SUNGMABUFF_ELIXIR_VALUE && hours >= 0.0 &&
					hours <= PLAYERBOT_SUNGMABUFF_ELIXIR_MAX_HOURS && g.dRateExpH > 0.0 &&
					res.iDeathsWindowed <= PLAYERBOT_SUNGMABUFF_ELIXIR_MAX_DEATHS &&
					!ch->FindAffect(PLAYERBOT_SUNGMABUFF_ELIXIR_AFFECT + stat))
			{
				if (dwNow - g.dwElixirDay >= PLAYERBOT_BOOSTER_DAY_MS)
				{
					g.dwElixirDay = dwNow ? dwNow : 1;
					g.iElixirsToday = 0;
				}
				if (g.iElixirsToday < PLAYERBOT_SUNGMABUFF_ELIXIR_DAY_MAX && BuyPlayerBotSungmaElixir(ch, state, stat, nextMap, dwNow))
				{
					++g.iElixirsToday;
					g.lBuffedFor = nextMap;
					g.dwBuffedAt = dwNow ? dwNow : 1;
					b.dwNextPick = 0;	// the pick reads the new Will at once
					return;
				}
			}
			if (worst <= PLAYERBOT_SUNGMABUFF_PREMIUM_VALUE && left <= 0)
			{
				if (BuyPlayerBotSungmaPremium(ch, state, hours, "next_map", nextMap, dwNow))
				{
					++s_kPlayerBotGuides.premiumFor[0];
					g.lBuffedFor = nextMap;
					g.dwBuffedAt = dwNow ? dwNow : 1;
					b.dwNextPick = 0;
				}
				return;
			}
		}
		// (c) a step down "not now", or a struggle: a day of the premium
		if (left > 0 || (g.dwLastStruggleBuff != 0 && dwNow - g.dwLastStruggleBuff < PLAYERBOT_SUNGMABUFF_STRUGGLE_GAP_MS))
			return;
		const char* why = NULL;
		for (std::map<long, DWORD>::const_iterator nn = b.mapNotNow.begin(); nn != b.mapNotNow.end() && !why; ++nn)
			if ((int)(nn->second - dwNow) > 0 && GetPlayerBotSungmaSlot(nn->first) > GetPlayerBotSungmaSlot(res.lMap))
				why = "stepped_down";
		if (!why && res.iDeathsWindowed >= 2)
			why = "deaths";
#ifdef MT2009_PLUS_BOT_G0_DUST_RULE_V1
		const char* struggle = NULL;
		if (!why && IsPlayerBotG0Struggling(ch, &struggle))
			why = "struggling";
#endif
		if (!why)
			return;
		g.dwLastStruggleBuff = dwNow ? dwNow : 1;
		if (BuyPlayerBotSungmaPremium(ch, state, 12.0, why, res.lMap, dwNow))
			++s_kPlayerBotGuides.struggles;
	}

	// ------------------------------------------------------------ 3. the boosters

	bool IsPlayerBotBoosterRunning(LPCHARACTER ch, DWORD vnum)
	{
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		return proto && ch->FindAffect((DWORD)proto->alValues[0], (BYTE)proto->alValues[1]) != NULL;
	}

	void ManagePlayerBotYoharaBoosters(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotYoharaResident& res,
			TPlayerBotGuideBot& g, long base, DWORD dwNow)
	{
		if ((int)(dwNow - g.dwNextBoosterLook) < 0)
			return;
		g.dwNextBoosterLook = dwNow + PLAYERBOT_BOOSTER_LOOK_MS;
		// the kills an hour, over its own window
		if (g.dwKillWindow == 0)
			g.dwKillWindow = dwNow ? dwNow : 1;
		else if (dwNow - g.dwKillWindow >= PLAYERBOT_BOOSTER_KILL_WINDOW_MS)
		{
			g.iKillsH = (int)((long long)g.iKills * 3600000LL / (long long)(dwNow - g.dwKillWindow));
			g.iKills = 0;
			g.dwKillWindow = dwNow ? dwNow : 1;
		}
		const int slot = GetPlayerBotSungmaSlot(base);
		const bool loch = base == PLAYERBOT_MAP_SUNGMA_LOCH;
		if ((slot < 0 && !loch) || (!loch && base != res.lMap) || GetPlayerBotItemShopSource() != 2 ||
				!IsPlayerBotItemShopEnabled() || ch->IsDead() || !ch->IsItemLoaded() || !ch->CanHandleItem() ||
				ch->GetExchange() || ch->GetMyShop())
			return;
		if (dwNow - g.dwBoosterDay >= PLAYERBOT_BOOSTER_DAY_MS)
		{
			g.dwBoosterDay = dwNow ? dwNow : 1;
			g.iBoosterSpent = 0;
		}
		DWORD want[2] = { 0, 0 };
		int n = 0;
		const bool hard = loch || slot >= PLAYERBOT_BOOSTER_HARD_SLOT || res.iDeathsWindowed >= 1 ||
				(slot >= 0 && !IsPlayerBotSungmaHpEnough(ch, slot, false));
		const bool slow = g.iKillsH >= 0 && g.iKillsH < PLAYERBOT_BOOSTER_SLOW_KILLS_H;
		if (hard)
		{
			want[n++] = PLAYERBOT_BOOSTER_HP;
			want[n++] = PLAYERBOT_BOOSTER_DEFENCE;
		}
		else if (slow)
		{
			want[n++] = PLAYERBOT_BOOSTER_ATTACK;
			want[n++] = PLAYERBOT_BOOSTER_CRITICAL;
		}
		if (n == 0)
			return;
		RefreshPlayerBotItemShopCatalogue(dwNow);
		EnsurePlayerBotIshop3FreshBalance(ch, state, dwNow);
		const int budget = std::min(PLAYERBOT_BOOSTER_DAY_MAX, std::max(0, (state.iDragonMarks - PLAYERBOT_BOOSTER_MARKS_RESERVE) / 4));
		for (int i = 0; i < n; ++i)
		{
			if (ch->CountSpecifyItem(want[i]) > 0 || IsPlayerBotBoosterRunning(ch, want[i]))
				continue;
			std::vector<const TPlayerBotItemShopEntry*> lines;
			SortPlayerBotIshop3Lines(ch, want[i], true, lines);
			if (lines.empty())
				continue;
			if (g.iBoosterSpent + (int)lines[0]->dwPrice > budget)
			{
				++s_kPlayerBotGuides.boosterBudget;
				PlayerBotLogThrottled("sungma_booster_budget", dwNow, "PLAYERBOT_SUNGMA: booster budget pid=%u name=%s vnum=%u spent=%d budget=%d marks=%d",
						ch->GetPlayerID(), ch->GetName(), want[i], g.iBoosterSpent, budget, state.iDragonMarks);
				return;
			}
			if (!BuyPlayerBotIshop3Line(ch, state, *lines[0], want[i], true, 1, "sungma_booster", dwNow))
				return;
			g.iBoosterSpent += (int)lines[0]->dwPrice;
			++s_kPlayerBotGuides.boosters;
			s_kPlayerBotGuides.boosterMarks += lines[0]->dwPrice;
			++s_kPlayerBotGuides.boosterBy[want[i]];
			sys_log(0, "PLAYERBOT_SUNGMA: booster pid=%u name=%s map=%ld vnum=%u why=%s kills_h=%d deaths_window=%d spent_today=%d budget=%d marks=%d",
					ch->GetPlayerID(), ch->GetName(), base, want[i], hard ? "hard" : "slow", g.iKillsH, res.iDeathsWindowed,
					g.iBoosterSpent, budget, state.iDragonMarks);
		}
	}

	// ------------------------------------------------------------ 4. Tajemniczy Loch

	int CountPlayerBotLochGuests()
	{
		int n = 0;
		for (std::map<DWORD, TPlayerBotGuideBot>::const_iterator i = s_mapPlayerBotGuide.begin(); i != s_mapPlayerBotGuide.end(); ++i)
			n += i->second.iLochPhase != 0 ? 1 : 0;
		return n;
	}

	bool IsPlayerBotYoharaLochGuest(DWORD pid, long base)
	{
		if (GetPlayerBotGuideBase(base) != PLAYERBOT_MAP_SUNGMA_LOCH)
			return false;
		std::map<DWORD, TPlayerBotGuideBot>::const_iterator g = s_mapPlayerBotGuide.find(pid);
		return g != s_mapPlayerBotGuide.end() && g->second.iLochPhase == 2;
	}

	// TransitionPlayerBotMap's gate (IsPlayerBotSungmaEntryAllowed): the Loch for a bot on its way in (the altar's warp).
	bool IsPlayerBotYoharaLochEntry(LPCHARACTER ch, long base)
	{
		if (!ch || GetPlayerBotGuideBase(base) != PLAYERBOT_MAP_SUNGMA_LOCH)
			return false;
		std::map<DWORD, TPlayerBotGuideBot>::const_iterator g = s_mapPlayerBotGuide.find(ch->GetPlayerID());
		return g != s_mapPlayerBotGuide.end() && g->second.iLochPhase >= 1;
	}

	// The Loch's Sung Ma requirement (sungma_table's row, else 25 / 15 / 25 / 30).
	int GetPlayerBotLochReq(int what)
	{
		static const int s_aiCopy[4] = { 25, 15, 25, 30 };
		const champion::SungmaRequirement* r = champion::MapRequirement(PLAYERBOT_MAP_SUNGMA_LOCH);
		if (!r)
			return s_aiCopy[what];
		switch (what)
		{
			case 0: return r->str;
			case 1: return r->hp;
			case 2: return r->move;
			default: return r->immune;
		}
	}

	// GetPlayerBotYoharaHubs' answer for the Loch.
	const TPlayerBotHuntingHub* GetPlayerBotYoharaLochHubs(long mapIndex, size_t& count)
	{
		if (GetPlayerBotGuideBase(mapIndex) != PLAYERBOT_MAP_SUNGMA_LOCH)
			return NULL;
		count = sizeof(PLAYERBOT_LOCH_HUBS) / sizeof(PLAYERBOT_LOCH_HUBS[0]);
		return PLAYERBOT_LOCH_HUBS;
	}

	// ChoosePlayerBotHuntingHub's score of a Loch spot: the ice rooms first, the dark ones for a bot geared for dark.
	int AdjustPlayerBotYoharaLochHubScore(LPCHARACTER ch, long x, long y, int score)
	{
		if (!ch || score <= 0 || GetPlayerBotGuideBase(ch->GetMapIndex()) != PLAYERBOT_MAP_SUNGMA_LOCH)
			return score;
		for (size_t i = 0; i < sizeof(PLAYERBOT_LOCH_HUBS) / sizeof(PLAYERBOT_LOCH_HUBS[0]); ++i)
		{
			if (PLAYERBOT_LOCH_HUBS[i].x != x || PLAYERBOT_LOCH_HUBS[i].y != y)
				continue;
			const bool darkBot = GetPlayerBotHuntElementIndex(ch) == PLAYERBOT_LOCH_DARK;
			const bool darkSpot = PLAYERBOT_LOCH_HUB_ELEMENT[i] == PLAYERBOT_LOCH_DARK;
			long long s = score;
			if (darkSpot)
				s = darkBot ? s * 160 / 100 : s * 15 / 100;
			else
				s = darkBot ? s * 80 / 100 : s * 160 / 100;
			return (int)std::min<long long>(std::max<long long>(1, s), INT_MAX / 2);
		}
		return score;
	}

	// The ticket is kept by a Champion (its own excursions): no sale, counter, gift or storage.
	bool IsPlayerBotYoharaLochTicketKept(LPCHARACTER ch, LPITEM item)
	{
		return ch && item && item->GetVnum() == PLAYERBOT_LOCH_TICKET_VNUM && GetPlayerBotChampionLevel(ch) >= 1 &&
				ch->GetDesc() && ch->GetDesc()->IsBot();
	}

	// A Champion still levelling (the Loch's band) wants a ticket or two off a counter.
	bool IsPlayerBotLochTicketBuyer(LPCHARACTER ch)
	{
		const int champion = ch ? GetPlayerBotChampionLevel(ch) : 0;
		return champion >= PLAYERBOT_LOCH_CHAMPION_MIN - 2 && champion < 30 && GetPlayerBotLochMax() > 0 &&
				ch->CountSpecifyItem(PLAYERBOT_LOCH_TICKET_VNUM) < PLAYERBOT_LOCH_TICKET_MARKET_HOLD;
	}

	bool WantsPlayerBotLochTicketOffer(LPCHARACTER ch, LPITEM offer)
	{
		return ch && offer && offer->GetVnum() == PLAYERBOT_LOCH_TICKET_VNUM && IsPlayerBotLochTicketBuyer(ch);
	}

	bool CanPlayerBotPayForLochTicket(LPCHARACTER ch, LPITEM item, long long price)
	{
		if (!ch || !item || price <= 0)
			return false;
		const long long units = std::max<long long>(1, (long long)item->GetCount());
		const long long cap = (long long)ScalePlayerBotIwakuraPrice(PLAYERBOT_LOCH_TICKET_PRICE_CAP);
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		const bool ok = price <= cap * units && price <= spare * PLAYERBOT_LOCH_TICKET_PURSE_PCT / 100;
		if (ok)
		{
			++s_kPlayerBotGuides.lochTicketsBought;
			sys_log(0, "PLAYERBOT_SUNGMA: loch ticket offer pid=%u name=%s count=%u price=%lld cap=%lld",
					ch->GetPlayerID(), ch->GetName(), (unsigned int)item->GetCount(), price, cap * units);
		}
		return ok;
	}

	bool WantsPlayerBotLochTicketFromMarket(LPCHARACTER ch)
	{
		if (!IsPlayerBotLochTicketBuyer(ch))
			return false;
		const TPlayerBotMarketLedgerEntry* t = GetPlayerBotMarketLedgerEntry(PLAYERBOT_LOCH_TICKET_VNUM);
		return t && t->dwSupplyUnits > 0;
	}

	// The bot may go in now (the look; its Will, its band, its health, the cap, the gap).
	const char* GetPlayerBotLochRefusal(LPCHARACTER ch, const TPlayerBotYoharaResident& res, const TPlayerBotSungmaBot& b,
			const TPlayerBotGuideBot& g, DWORD dwNow)
	{
		const int champion = GetPlayerBotChampionLevel(ch);
		const int slot = GetPlayerBotSungmaSlot(res.lMap);
		if (GetPlayerBotLochMax() <= 0 || !IsPlayerBotMapHostedHere(PLAYERBOT_MAP_SUNGMA_LOCH) ||
				!IsPlayerBotMapHostedHere(PLAYERBOT_MAP_SUNGMA_NAMGAN))
			return "off";
		if (champion < PLAYERBOT_LOCH_CHAMPION_MIN || slot < GetPlayerBotSungmaSlot(PLAYERBOT_MAP_SUNGMA_NAMGAN))
			return "band";
		if (g.dwLochEnded != 0 && dwNow - g.dwLochEnded < PLAYERBOT_LOCH_GAP_MS)
			return "gap";
		std::map<long, DWORD>::const_iterator nn = b.mapNotNow.find(PLAYERBOT_MAP_SUNGMA_LOCH);
		if (nn != b.mapNotNow.end() && (int)(nn->second - dwNow) > 0)
			return "not_now";
		for (int i = 0; i < 3; ++i)
			if (GetPlayerBotSungmaWill(ch, i) < GetPlayerBotLochReq(i))
				return "will";
		if (ch->GetMaxHP() < PLAYERBOT_LOCH_HP_FLOOR)
			return "health";
		if (res.iDeathsWindowed > 0)
			return "deaths";
		if (CountPlayerBotLochGuests() >= GetPlayerBotLochMax())
			return "cap";
		return NULL;
	}

	void EndPlayerBotLoch(LPCHARACTER ch, TPlayerBotGuideBot& g, const char* why, DWORD dwNow)
	{
		sys_log(0, "PLAYERBOT_SUNGMA: loch end pid=%u name=%s why=%s phase=%d stay_s=%u map=%ld",
				ch->GetPlayerID(), ch->GetName(), why, g.iLochPhase, g.dwLochSince ? (dwNow - g.dwLochSince) / 1000 : 0,
				ch->GetMapIndex());
		g.iLochPhase = 0;
		g.dwLochEnded = dwNow ? dwNow : 1;
		g.dwLochExitWalk = 0;
	}

	// The excursion: -2 not on one (the resident's own flow goes on), else the travel pass's answer (-1 hunt on, 0/1).
	int ManagePlayerBotYoharaLoch(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotYoharaResident& res,
			TPlayerBotSungmaBot& b, TPlayerBotGuideBot& g, long base, DWORD dwNow)
	{
		const DWORD pid = ch->GetPlayerID();
		// a bot standing in the Loch with no excursion of its own (a log-in there): a guest until it goes out
		if (g.iLochPhase == 0 && base == PLAYERBOT_MAP_SUNGMA_LOCH)
		{
			g.iLochPhase = 2;
			g.dwLochSince = dwNow ? dwNow : 1;
			g.iLochDeaths = res.iDeaths;
			sys_log(0, "PLAYERBOT_SUNGMA: loch guest found pid=%u name=%s champion=%d", pid, ch->GetName(), GetPlayerBotChampionLevel(ch));
		}
		if (g.iLochPhase == 0)
		{
			if ((int)(dwNow - g.dwNextLochLook) < 0 || base != res.lMap || b.bErrand || b.dwWalkSince != 0)
				return -2;
			g.dwNextLochLook = dwNow + PLAYERBOT_LOCH_LOOK_MS + PlayerBotNavHash(pid ^ 0x4c4f4348U) % 60000U;
			if (ch->IsDead() || state.bRecoveringAfterDeath || state.dwTargetVID != 0 || ch->GetVictim() != NULL ||
					state.bTacticalRetreat || ch->GetHP() * 100 < ch->GetMaxHP() * 60 || IsPlayerBotSungmaPartyOnObjective(ch) ||
					IsPlayerBotOnDungeonRun(pid) || !ch->IsItemLoaded())
				return -2;
			const char* refusal = GetPlayerBotLochRefusal(ch, res, b, g, dwNow);
			if (refusal)
				return -2;
			if (ch->CountSpecifyItem(PLAYERBOT_LOCH_TICKET_VNUM) == 0)
			{
				// V3's own ticket unless PLAYERBOT_LOCH_ISHOP=0 (on by default)
				if (!IsPlayerBotLochIshopOn() || GetPlayerBotItemShopSource() != 2 || !IsPlayerBotItemShopEnabled())
					return -2;
				std::vector<const TPlayerBotItemShopEntry*> lines;
				RefreshPlayerBotItemShopCatalogue(dwNow);
				SortPlayerBotIshop3Lines(ch, PLAYERBOT_LOCH_TICKET_VNUM, false, lines);
				size_t pick = lines.size();
				for (size_t i = 0; i < lines.size(); ++i)
					if (lines[i]->dwCount == 1)
						pick = i;
				if (pick >= lines.size() || !BuyPlayerBotIshop3Line(ch, state, *lines[pick], PLAYERBOT_LOCH_TICKET_VNUM, false, 1,
						"loch_ticket", dwNow))
					return -2;
				++s_kPlayerBotGuides.lochTicketsV3;
			}
			if ((int)(PlayerBotNavHash(pid ^ dwNow) % 100U) >= PLAYERBOT_LOCH_GO_PERCENT)
				return -2;
			LeavePlayerBotSungmaParty(ch, "loch", true);
			g.iLochPhase = 1;
			g.dwLochSince = dwNow ? dwNow : 1;
			++s_kPlayerBotGuides.lochTrips;
			sys_log(0, "PLAYERBOT_SUNGMA: loch go pid=%u name=%s from=%ld champion=%d will=%d/%d/%d/%d max_hp=%d tickets=%u element=%d guests=%d",
					pid, ch->GetName(), base, GetPlayerBotChampionLevel(ch), GetPlayerBotSungmaWill(ch, 0),
					GetPlayerBotSungmaWill(ch, 1), GetPlayerBotSungmaWill(ch, 2), GetPlayerBotSungmaWill(ch, 3), ch->GetMaxHP(),
					(unsigned int)ch->CountSpecifyItem(PLAYERBOT_LOCH_TICKET_VNUM), GetPlayerBotHuntElementIndex(ch),
					CountPlayerBotLochGuests());
		}
		if (ch->IsDead() || state.bRecoveringAfterDeath)
			return -1;
		if (g.iLochPhase == 1)
		{
			if (dwNow - g.dwLochSince >= PLAYERBOT_LOCH_TO_ALTAR_MS)
			{
				++s_kPlayerBotGuides.lochAborts;
				EndPlayerBotLoch(ch, g, "altar_too_long", dwNow);
				return -2;
			}
			long ox = 0, oy = 0;
			GetPlayerBotStableOffset(pid, 0x414c5452U, 50, 200, ox, oy);
			const long ax = PLAYERBOT_LOCH_ALTAR_X + ox, ay = PLAYERBOT_LOCH_ALTAR_Y + oy;
			if (base != PLAYERBOT_MAP_SUNGMA_NAMGAN)
			{
				s_szPlayerBotTransitionRefusal = NULL;
				if (!TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_SUNGMA_NAMGAN, ax, ay, dwNow, "sungma_loch_altar"))
				{
					++s_kPlayerBotGuides.lochAborts;
					EndPlayerBotLoch(ch, g, s_szPlayerBotTransitionRefusal ? s_szPlayerBotTransitionRefusal : "warp_refused", dwNow);
					return -2;
				}
				return 1;
			}
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			if (DISTANCE_APPROX(ch->GetX() - ax, ch->GetY() - ay) > PLAYERBOT_LOCH_REACH)
			{
				SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
				MovePlayerBot(ch, ax, ay, dwNow, 6, true, false, false, false);
				return 1;
			}
			ch->Stop();
			// the altar's own rules (quest yohara_mapy3): the altar standing, level 120, Champion 1, a ticket
			bool altar = false;
			{
				CharacterVectorInteractor found;
				if (CHARACTER_MANAGER::instance().GetCharactersByRaceNum(PLAYERBOT_LOCH_ALTAR_RACE, found))
					for (CharacterVectorInteractor::iterator it = found.begin(); it != found.end() && !altar; ++it)
						altar = *it && (*it)->GetMapIndex() == ch->GetMapIndex() &&
								DISTANCE_APPROX((*it)->GetX() - ch->GetX(), (*it)->GetY() - ch->GetY()) <= 1500;
			}
			if (!altar || (int)ch->GetLevel() < 120 || GetPlayerBotChampionLevel(ch) < 1 ||
					ch->CountSpecifyItem(PLAYERBOT_LOCH_TICKET_VNUM) < 1)
			{
				if (!altar)
					++s_kPlayerBotGuides.lochNoAltar;
				++s_kPlayerBotGuides.lochAborts;
				EndPlayerBotLoch(ch, g, !altar ? "no_altar" : "no_ticket", dwNow);
				return -2;
			}
			ch->RemoveSpecifyItem(PLAYERBOT_LOCH_TICKET_VNUM, 1);
			++s_kPlayerBotGuides.lochTicketsUsed;
			g.iLochPhase = 2;	// the gate lets it through now
			long lx = 0, ly = 0;
			GetPlayerBotStableOffset(pid, 0x4c4f4348U, 50, 250, lx, ly);
			s_szPlayerBotTransitionRefusal = NULL;
			if (!TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_SUNGMA_LOCH, PLAYERBOT_LOCH_ARRIVAL_X + lx,
					PLAYERBOT_LOCH_ARRIVAL_Y + ly, dwNow, "sungma_loch"))
			{
				// the ticket back: the warp never happened
				ch->AutoGiveItem(PLAYERBOT_LOCH_TICKET_VNUM, 1);
				--s_kPlayerBotGuides.lochTicketsUsed;
				++s_kPlayerBotGuides.lochAborts;
				EndPlayerBotLoch(ch, g, s_szPlayerBotTransitionRefusal ? s_szPlayerBotTransitionRefusal : "warp_refused", dwNow);
				return -2;
			}
			g.dwLochSince = dwNow ? dwNow : 1;
			g.iLochDeaths = res.iDeaths;
			++s_kPlayerBotGuides.lochEntries;
			sys_log(0, "PLAYERBOT_SUNGMA: loch enter pid=%u name=%s champion=%d tickets_left=%u guests=%d",
					pid, ch->GetName(), GetPlayerBotChampionLevel(ch),
					(unsigned int)ch->CountSpecifyItem(PLAYERBOT_LOCH_TICKET_VNUM), CountPlayerBotLochGuests());
			return 1;
		}
		if (g.iLochPhase == 2)
		{
			if (base != PLAYERBOT_MAP_SUNGMA_LOCH)
			{
				// still on its way in (the warp's tick), or out by another road
				if (dwNow - g.dwLochSince < 30 * 1000)
					return 0;
				EndPlayerBotLoch(ch, g, "left", dwNow);
				return -2;
			}
			const char* out = NULL;
			const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
			if (res.iDeathsWindowed >= PLAYERBOT_LOCH_DEATHS_OUT || res.iDeaths - g.iLochDeaths >= PLAYERBOT_LOCH_DEATHS_OUT + 2)
				out = "deaths";
			else if (dwNow - g.dwLochSince >= PLAYERBOT_LOCH_STAY_MS)
				out = "stay_over";
			else if (ch->GetEmptyInventory(3) < 0 && CountPlayerBotJunkItems(ch) > 0)
				out = "bag";
			else if (IsPlayerBotYoharaCohortPID(pid) && dwNow - res.dwArrived >= (DWORD)cfg.cohortStayMin * 60000U)
				out = "cohort_rest";
			if (!out)
			{
				// the belt kept full where it stands (no Dongan from here)
				size_t red = 0, blue = 0;
				CountPlayerBotPotions(ch, red, blue);
				if (red < PLAYERBOT_SUNGMA_ERRAND_RED)
					RestockPlayerBotYohara(ch, res, dwNow);
				// a party's leader: the Mnichy's route (6)
				if (ManagePlayerBotYoharaBossRoute(ch, state, dwNow) > 0)
					return 1;
				return -1;	// the Loch's spots
			}
			if (out[0] == 'd')
			{
				b.mapNotNow[PLAYERBOT_MAP_SUNGMA_LOCH] = dwNow + PLAYERBOT_SUNGMA_NOT_NOW_MS;
				res.iDeathsWindowed = 0;
				res.dwWindowStart = 0;
				++s_kPlayerBotGuides.lochDeathsOut;
			}
			sys_log(0, "PLAYERBOT_SUNGMA: loch out pid=%u name=%s why=%s stay_s=%u deaths=%d pos=(%ld,%ld)",
					pid, ch->GetName(), out, (dwNow - g.dwLochSince) / 1000, res.iDeaths - g.iLochDeaths, ch->GetX(), ch->GetY());
			LeavePlayerBotSungmaParty(ch, "loch_out", false);
			g.iLochPhase = 3;
			g.dwLochExitWalk = dwNow ? dwNow : 1;
		}
		if (g.iLochPhase == 3)
		{
			if (base != PLAYERBOT_MAP_SUNGMA_LOCH)
			{
				++s_kPlayerBotGuides.lochExits;
				EndPlayerBotLoch(ch, g, "out", dwNow);
				b.dwNextPick = 0;
				return -2;
			}
			const int d = DISTANCE_APPROX(ch->GetX() - PLAYERBOT_LOCH_EXIT_X, ch->GetY() - PLAYERBOT_LOCH_EXIT_Y);
			if (d > PLAYERBOT_LOCH_REACH && d <= PLAYERBOT_LOCH_EXIT_WALK_NEAR && dwNow - g.dwLochExitWalk < PLAYERBOT_LOCH_EXIT_WALK_MS)
			{
				state.dwTargetVID = 0;
				ch->SetVictim(NULL);
				SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
				MovePlayerBot(ch, PLAYERBOT_LOCH_EXIT_X, PLAYERBOT_LOCH_EXIT_Y, dwNow, 6, true, false, false, false);
				return 1;
			}
			// Wyjscie (by it) or the scroll's warp (far): back by the altar, as the quest puts a person
			long ox = 0, oy = 0;
			GetPlayerBotStableOffset(pid, 0x45584954U, 50, 200, ox, oy);
			s_szPlayerBotTransitionRefusal = NULL;
			if (!TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_SUNGMA_NAMGAN, PLAYERBOT_LOCH_ALTAR_X + ox,
					PLAYERBOT_LOCH_ALTAR_Y + oy, dwNow, d <= PLAYERBOT_LOCH_REACH ? "sungma_loch_exit" : "sungma_loch_scroll"))
			{
				PlayerBotLogThrottled("sungma_loch_exit_failed", dwNow, "PLAYERBOT_SUNGMA: loch exit refused pid=%u name=%s refusal=%s",
						pid, ch->GetName(), s_szPlayerBotTransitionRefusal ? s_szPlayerBotTransitionRefusal : "-");
				return LeavePlayerBotSungma(ch, state, dwNow, "sungma_loch_stuck");
			}
			return 1;
		}
		return -2;
	}

	// ------------------------------------------------------------ 6. the boss route

	// The period the engine gives an area's line now (fastBossSpawn<map> / fastBossSpawn, as regen_event reads them).
	DWORD GetPlayerBotBossAreaPeriodMs(const TPlayerBotBossArea& a)
	{
		char flag[48];
		snprintf(flag, sizeof(flag), "fastBossSpawn%ld", a.lMap);
		int pct = MINMAX(0, quest::CQuestManager::instance().GetEventFlag(flag), 100);
		if (pct == 0)
			pct = MINMAX(0, quest::CQuestManager::instance().GetEventFlag("fastBossSpawn"), 100);
		DWORD s = a.dwPeriodS;
		if (pct)
			s = std::max<DWORD>(3, s * (DWORD)pct / 100);
		return s * 1000;
	}

	bool IsPlayerBotBossAreaRace(const TPlayerBotBossArea& a, DWORD race)
	{
		for (int i = 0; i < 4 && a.adwRace[i]; ++i)
			if (a.adwRace[i] == race)
				return true;
		return false;
	}

	struct FFindPlayerBotAreaBoss
	{
		const TPlayerBotBossArea& m_area;
		long m_map;
		LPCHARACTER m_found;
		FFindPlayerBotAreaBoss(const TPlayerBotBossArea& area, long mapIndex) : m_area(area), m_map(mapIndex), m_found(NULL) {}
		void operator()(LPENTITY entity)
		{
			if (m_found || !entity || !entity->IsType(ENTITY_CHARACTER))
				return;
			LPCHARACTER mob = static_cast<LPCHARACTER>(entity);
			if (!mob->IsMonster() || mob->IsDead() || mob->GetMapIndex() != m_map || !IsPlayerBotBossAreaRace(m_area, mob->GetRaceNum()) ||
					DISTANCE_APPROX(mob->GetX() - m_area.x, mob->GetY() - m_area.y) > PLAYERBOT_BOSS_ROUTE_SCAN)
				return;
			m_found = mob;
		}
	};

	LPCHARACTER FindPlayerBotAreaBoss(int area, long mapIndex)
	{
		const TPlayerBotBossArea& a = PLAYERBOT_BOSS_AREAS[area];
		LPSECTREE tree = SECTREE_MANAGER::instance().Get(mapIndex, a.x, a.y);
		if (!tree)
			return NULL;
		FFindPlayerBotAreaBoss f(a, mapIndex);
		tree->ForEachAround(f);
		return f.m_found;
	}

	// The chance (per cent) the area's boss stands there now, by the channel's memory.
	int GetPlayerBotBossAreaChance(int area, DWORD dwNow)
	{
		const TPlayerBotBossAreaMemory& m = s_aPlayerBotBossArea[area];
		if (m.dwSkipUntil != 0 && (int)(m.dwSkipUntil - dwNow) > 0)
			return 0;
		if (m.dwSeenAt != 0 && dwNow - m.dwSeenAt < PLAYERBOT_BOSS_ROUTE_SEEN_MS &&
				(m.dwKilledAt == 0 || (int)(m.dwSeenAt - m.dwKilledAt) > 0))
			return 100;
		const DWORD period = GetPlayerBotBossAreaPeriodMs(PLAYERBOT_BOSS_AREAS[area]);
		if (m.dwKilledAt != 0 && dwNow - m.dwKilledAt < period)
			return 0;
		if (m.dwEmptyAt != 0 && dwNow - m.dwEmptyAt < period / 2)
			return 0;
		if (m.dwKilledAt != 0 || m.dwEmptyAt != 0)
			return 100;	// due again
		return PLAYERBOT_BOSS_ROUTE_UNKNOWN_PCT;
	}

	// A kill of a bot (NotePlayerBotSungmaKill): the area's memory, the census, the kill window of the boosters.
	void NotePlayerBotYoharaGuidesKill(LPCHARACTER killer, LPCHARACTER victim)
	{
		if (!killer || !victim || victim->IsPC() || !killer->IsPC() || !killer->GetDesc() || !killer->GetDesc()->IsBot())
			return;
		std::map<DWORD, TPlayerBotGuideBot>::iterator g = s_mapPlayerBotGuide.find(killer->GetPlayerID());
		if (g != s_mapPlayerBotGuide.end())
			++g->second.iKills;
		if (victim->GetMobRank() < MOB_RANK_BOSS)
			return;
		const long base = GetPlayerBotGuideBase(victim->GetMapIndex());
		const DWORD race = victim->GetRaceNum();
		int best = -1, bestD = 0;
		for (int i = 0; i < PLAYERBOT_BOSS_AREA_COUNT; ++i)
		{
			const TPlayerBotBossArea& a = PLAYERBOT_BOSS_AREAS[i];
			if (a.lMap != base || !IsPlayerBotBossAreaRace(a, race))
				continue;
			const int d = DISTANCE_APPROX(victim->GetX() - a.x, victim->GetY() - a.y);
			if (d <= 8000 && (best < 0 || d < bestD))
			{
				best = i;
				bestD = d;
			}
		}
		++s_kPlayerBotGuides.bossKills[race];
		if (best < 0)
			return;
		const DWORD dwNow = get_dword_time();
		TPlayerBotBossAreaMemory& m = s_aPlayerBotBossArea[best];
		m.dwKilledAt = dwNow ? dwNow : 1;
		m.dwLastRace = race;
		m.dwEmptyAt = 0;
		sys_log(0, "PLAYERBOT_SUNGMA: boss_route kill channel=%u map=%ld area=%d name=%s race=%u by=%s worth=%u next_in_s=%u",
				(unsigned int)g_bChannel, base, best, PLAYERBOT_BOSS_AREAS[best].szName, race, killer->GetName(),
				GetPlayerBotBossWorth(race), GetPlayerBotBossAreaPeriodMs(PLAYERBOT_BOSS_AREAS[best]) / 1000);
	}

	struct FCheckPlayerBotRouteParty
	{
		LPCHARACTER m_leader;
		int m_count, m_ready, m_championSum, m_weak;
		int m_slot;
		explicit FCheckPlayerBotRouteParty(LPCHARACTER leader, int slot) : m_leader(leader), m_count(0), m_ready(0),
			m_championSum(0), m_weak(0), m_slot(slot) {}
		void operator()(LPCHARACTER member)
		{
			if (!member || member->IsDead())
				return;
			if (member != m_leader && DISTANCE_APPROX(member->GetX() - m_leader->GetX(), member->GetY() - m_leader->GetY()) >
					PLAYERBOT_SUNGMA_PARTY_NEAR)
				return;
			++m_count;
			m_championSum += GetPlayerBotChampionLevel(member);
			if (GetPlayerBotSungmaHpPercent(member) >= PLAYERBOT_BOSS_ROUTE_READY_HP)
				++m_ready;
			if (m_slot >= 0 && !IsPlayerBotSungmaHpEnough(member, m_slot, true))
				++m_weak;
		}
	};

	// Strong enough: three members by the leader, all ready, the band's floor + 2 on average, none under its map's health.
	bool IsPlayerBotRoutePartyStrong(LPCHARACTER ch, long base)
	{
		LPPARTY party = ch->GetParty();
		if (!party || party->GetLeaderPID() != ch->GetPlayerID() || IsPlayerBotHumanLedParty(party))
			return false;
		const int slot = GetPlayerBotSungmaSlot(base);
		FCheckPlayerBotRouteParty f(ch, slot);
		party->ForEachOnMapMember(f, ch->GetMapIndex());
		if (f.m_count < PLAYERBOT_SUNGMA_PARTY_MIN || f.m_ready < f.m_count || f.m_weak > 0)
			return false;
		const int floorLevel = base == PLAYERBOT_MAP_SUNGMA_LOCH ? PLAYERBOT_LOCH_CHAMPION_MIN : GetPlayerBotSungmaBandFloor(base);
		size_t red = 0, blue = 0;
		CountPlayerBotPotions(ch, red, blue);
		return f.m_championSum >= (floorLevel + 2) * f.m_count && (int)red >= PLAYERBOT_BOSS_ROUTE_RED_MIN;
	}

	// The worth of going for an area from (x, y): its loot x its chance, halved every PLAYERBOT_BOSS_ROUTE_HALF_WALK.
	long long ScorePlayerBotBossArea(int area, long x, long y, DWORD dwNow)
	{
		const int chance = GetPlayerBotBossAreaChance(area, dwNow);
		if (chance <= 0)
			return 0;
		const TPlayerBotBossArea& a = PLAYERBOT_BOSS_AREAS[area];
		const long long worth = (long long)GetPlayerBotBossAreaWorth(a) * chance / 100;
		const int d = DISTANCE_APPROX(x - a.x, y - a.y);
		return worth * PLAYERBOT_BOSS_ROUTE_HALF_WALK / (PLAYERBOT_BOSS_ROUTE_HALF_WALK + d);
	}

	// The leader's route: -1 not now (the tick goes on), 1 the tick is the route's walk.
	int ManagePlayerBotYoharaBossRoute(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->IsDead() || state.bRecoveringAfterDeath || state.bTacticalRetreat)
			return -1;
		LPPARTY party = ch->GetParty();
		if (!party || party->GetLeaderPID() != ch->GetPlayerID())
			return -1;
		TPlayerBotGuideBot& g = s_mapPlayerBotGuide[ch->GetPlayerID()];
		const long base = GetPlayerBotGuideBase(ch->GetMapIndex());
		// a fight: the route waits (the target pick takes the boss once it is by the party)
		if (state.dwTargetVID != 0 || ch->GetVictim() != NULL)
		{
			if (g.iRouteArea >= 0 && PLAYERBOT_BOSS_AREAS[g.iRouteArea].lMap == base &&
					DISTANCE_APPROX(ch->GetX() - PLAYERBOT_BOSS_AREAS[g.iRouteArea].x, ch->GetY() - PLAYERBOT_BOSS_AREAS[g.iRouteArea].y) <=
					PLAYERBOT_BOSS_ROUTE_SCAN)
				g.dwRouteSince = dwNow ? dwNow : 1;	// the leg's clock waits at the boss
			return -1;
		}
		if (g.iRouteArea >= 0 && PLAYERBOT_BOSS_AREAS[g.iRouteArea].lMap != base)
			g.iRouteArea = -1;
		if (g.iRouteArea < 0)
		{
			if ((int)(dwNow - g.dwNextRouteLook) < 0)
				return -1;
			g.dwNextRouteLook = dwNow + PLAYERBOT_BOSS_ROUTE_LOOK_MS;
			if (!IsPlayerBotRoutePartyStrong(ch, base) || FindPlayerBotEngagedTarget(ch, &state, dwNow))
				return -1;
			// the plan: the best area by worth over the walk, then the next from there (the log's route)
			CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(ch->GetMapIndex());
			const bool nav = navigation.Init(ch->GetMapIndex());
			int stops[PLAYERBOT_BOSS_ROUTE_PLAN_STOPS] = { -1, -1, -1 };
			long long worths[PLAYERBOT_BOSS_ROUTE_PLAN_STOPS] = { 0, 0, 0 };
			long fx = ch->GetX(), fy = ch->GetY();
			for (int k = 0; k < PLAYERBOT_BOSS_ROUTE_PLAN_STOPS; ++k)
			{
				long long best = 0;
				for (int i = 0; i < PLAYERBOT_BOSS_AREA_COUNT; ++i)
				{
					if (PLAYERBOT_BOSS_AREAS[i].lMap != base || (k > 0 && (stops[0] == i || (k > 1 && stops[1] == i))))
						continue;
					const long long s = ScorePlayerBotBossArea(i, fx, fy, dwNow);
					if (s <= best)
						continue;
					if (k == 0 && nav && !navigation.CanReach(ch->GetX(), ch->GetY(), PLAYERBOT_BOSS_AREAS[i].x, PLAYERBOT_BOSS_AREAS[i].y))
						continue;
					best = s;
					stops[k] = i;
				}
				if (stops[k] < 0)
					break;
				worths[k] = best;
				fx = PLAYERBOT_BOSS_AREAS[stops[k]].x;
				fy = PLAYERBOT_BOSS_AREAS[stops[k]].y;
			}
			if (stops[0] < 0)
				return -1;
			g.iRouteArea = stops[0];
			g.dwRouteSince = dwNow ? dwNow : 1;
			++s_kPlayerBotGuides.routes;
			std::string plan;
			for (int k = 0; k < PLAYERBOT_BOSS_ROUTE_PLAN_STOPS && stops[k] >= 0; ++k)
			{
				char one[64];
				snprintf(one, sizeof(one), "%s%d:%s:%lldk", k ? "," : "", stops[k], PLAYERBOT_BOSS_AREAS[stops[k]].szName, worths[k] / 1000);
				plan += one;
			}
			sys_log(0, "PLAYERBOT_SUNGMA: boss_route plan channel=%u pid=%u name=%s map=%ld members=%u route=[%s] chance=%d dist=%d",
					(unsigned int)g_bChannel, ch->GetPlayerID(), ch->GetName(), base, (unsigned int)party->GetMemberCount(), plan.c_str(),
					GetPlayerBotBossAreaChance(stops[0], dwNow),
					DISTANCE_APPROX(ch->GetX() - PLAYERBOT_BOSS_AREAS[stops[0]].x, ch->GetY() - PLAYERBOT_BOSS_AREAS[stops[0]].y));
		}
		const int area = g.iRouteArea;
		const TPlayerBotBossArea& a = PLAYERBOT_BOSS_AREAS[area];
		TPlayerBotBossAreaMemory& m = s_aPlayerBotBossArea[area];
		// the boss of the leg is dead (this party's kill or another's): the leg is done, the next plan at once
		if (m.dwKilledAt != 0 && dwNow - m.dwKilledAt < PLAYERBOT_BOSS_ROUTE_LEG_MS &&
				GetPlayerBotBossAreaChance(area, dwNow) == 0)
		{
			sys_log(0, "PLAYERBOT_SUNGMA: boss_route done channel=%u pid=%u name=%s map=%ld area=%d name=%s race=%u took_s=%u",
					(unsigned int)g_bChannel, ch->GetPlayerID(), ch->GetName(), base, area, a.szName, m.dwLastRace,
					(dwNow - g.dwRouteSince) / 1000);
			g.iRouteArea = -1;
			g.dwNextRouteLook = 0;
			return -1;
		}
		// the party fell behind (a death, a retreat): the regroup first, the route after
		if (CountPlayerBotSungmaPartyNear(ch, PLAYERBOT_SUNGMA_PARTY_NEAR) < PLAYERBOT_SUNGMA_PARTY_MIN)
			return -1;
		if (dwNow - g.dwRouteSince >= PLAYERBOT_BOSS_ROUTE_LEG_MS)
		{
			++s_kPlayerBotGuides.giveUps;
			m.dwSkipUntil = dwNow + PLAYERBOT_BOSS_ROUTE_SKIP_MS;
			sys_log(0, "PLAYERBOT_SUNGMA: boss_route give up channel=%u pid=%u name=%s map=%ld area=%d name=%s dist=%d",
					(unsigned int)g_bChannel, ch->GetPlayerID(), ch->GetName(), base, area, a.szName,
					DISTANCE_APPROX(ch->GetX() - a.x, ch->GetY() - a.y));
			g.iRouteArea = -1;
			return -1;
		}
		const int d = DISTANCE_APPROX(ch->GetX() - a.x, ch->GetY() - a.y);
		LPCHARACTER boss = d <= PLAYERBOT_BOSS_ROUTE_SCAN + 2000 ? FindPlayerBotAreaBoss(area, ch->GetMapIndex()) : NULL;
		if (boss)
		{
			if (m.dwSeenAt == 0 || dwNow - m.dwSeenAt >= PLAYERBOT_BOSS_ROUTE_SEEN_MS)
			{
				++s_kPlayerBotGuides.found;
				sys_log(0, "PLAYERBOT_SUNGMA: boss_route arrive channel=%u pid=%u name=%s map=%ld area=%d name=%s found=%u hp=%d%%",
						(unsigned int)g_bChannel, ch->GetPlayerID(), ch->GetName(), base, area, a.szName, boss->GetRaceNum(),
						boss->GetMaxHP() > 0 ? (int)((long long)boss->GetHP() * 100 / boss->GetMaxHP()) : 0);
			}
			m.dwSeenAt = dwNow ? dwNow : 1;
			m.dwLastRace = boss->GetRaceNum();
			// close enough for the party's target pick (a boss with three ready members by the leader)
			if (DISTANCE_APPROX(ch->GetX() - boss->GetX(), ch->GetY() - boss->GetY()) <= 1200)
				return -1;
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
			MovePlayerBot(ch, boss->GetX(), boss->GetY(), dwNow, 6, true, false, false, false);
			return 1;
		}
		if (d <= PLAYERBOT_BOSS_ROUTE_ARRIVE)
		{
			// nobody there: a death we did not see - due again in half the period
			++s_kPlayerBotGuides.arrived;
			++s_kPlayerBotGuides.empty;
			m.dwEmptyAt = dwNow ? dwNow : 1;
			sys_log(0, "PLAYERBOT_SUNGMA: boss_route arrive channel=%u pid=%u name=%s map=%ld area=%d name=%s found=0 due_in_s=%u",
					(unsigned int)g_bChannel, ch->GetPlayerID(), ch->GetName(), base, area, a.szName,
					GetPlayerBotBossAreaPeriodMs(a) / 2000);
			g.iRouteArea = -1;
			g.dwNextRouteLook = 0;
			return -1;
		}
		// on the way; a pack that takes the party first is fought (the target pick, above)
		if (FindPlayerBotEngagedTarget(ch, &state, dwNow))
			return -1;
		SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
		MovePlayerBot(ch, a.x, a.y, dwNow, 6, true, false, false, false);
		return 1;
	}

	// ------------------------------------------------------------ the resident's hook and the census

	// From ManagePlayerBotSungmaResident, after the points: -2 the resident's own flow goes on, else its answer.
	int ManagePlayerBotYoharaGuides(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotYoharaResident& res,
			TPlayerBotSungmaBot& b, long base, DWORD dwNow)
	{
		if (!ch)
			return -2;
		TPlayerBotGuideBot& g = s_mapPlayerBotGuide[ch->GetPlayerID()];
		if (s_kPlayerBotGuides.dwSince == 0)
			s_kPlayerBotGuides.dwSince = dwNow ? dwNow : 1;
		if (g.iLochPhase == 0 || g.iLochPhase == 2)
		{
			ManagePlayerBotSungmaBuff(ch, state, res, b, g, base, dwNow);
			ManagePlayerBotYoharaBoosters(ch, state, res, g, base, dwNow);
		}
		return ManagePlayerBotYoharaLoch(ch, state, res, b, g, base, dwNow);
	}

	void LogPlayerBotYoharaGuidesCensus(DWORD dwNow)
	{
		// the bots gone from the core: their rows forgotten (a Loch guest that logged out frees its place)
		for (std::map<DWORD, TPlayerBotGuideBot>::iterator i = s_mapPlayerBotGuide.begin(); i != s_mapPlayerBotGuide.end();)
		{
			if (!CHARACTER_MANAGER::instance().FindByPID(i->first))
				s_mapPlayerBotGuide.erase(i++);
			else
				++i;
		}
		if (s_dwPlayerBotGuidesLastCensus != 0 && dwNow - s_dwPlayerBotGuidesLastCensus < PLAYERBOT_GUIDES_CENSUS_MS)
			return;
		const DWORD span = s_dwPlayerBotGuidesLastCensus ? dwNow - s_dwPlayerBotGuidesLastCensus : 0;
		s_dwPlayerBotGuidesLastCensus = dwNow ? dwNow : 1;
		TPlayerBotGuidesStats& st = s_kPlayerBotGuides;
		int premiumNow = 0, elixirNow = 0, guests = 0, inside = 0, leaders = 0;
		long long marks = 0;
		int marksN = 0;
		for (std::map<DWORD, TPlayerBotGuideBot>::const_iterator i = s_mapPlayerBotGuide.begin(); i != s_mapPlayerBotGuide.end(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(i->first);
			if (!ch)
				continue;
			premiumNow += ch->FindAffect(PLAYERBOT_SUNGMABUFF_PREMIUM_AFFECT) ? 1 : 0;
			for (int s = 0; s < 4; ++s)
				if (ch->FindAffect(PLAYERBOT_SUNGMABUFF_ELIXIR_AFFECT + s))
				{
					++elixirNow;
					break;
				}
			guests += i->second.iLochPhase != 0 ? 1 : 0;
			inside += GetPlayerBotGuideBase(ch->GetMapIndex()) == PLAYERBOT_MAP_SUNGMA_LOCH ? 1 : 0;
			leaders += i->second.iRouteArea >= 0 ? 1 : 0;
			TPlayerBotAIStateMap::const_iterator s = s_mapPlayerBotAIStates.find(i->first);
			if (s != s_mapPlayerBotAIStates.end() && s->second.bDragonBalanceKnown)
			{
				marks += s->second.iDragonMarks;
				++marksN;
			}
		}
		sys_log(0, "PLAYERBOT_SUNGMABUFF: census channel=%u span_min=%u premium_days=[1:%u,7:%u,15:%u,30:%u] premium_sm=%lld used=%u "
				"use_failed=%u no_coins=%u for_next=%u renewals=%u struggles=%u stepped_up=%u elixirs=[str:%u,hp:%u,move:%u,immune:%u] "
				"elixir_sz=%lld elixir_no_marks=%u premium_now=%d elixir_now=%d",
				(unsigned int)g_bChannel, span / 60000, st.premium[0], st.premium[1], st.premium[2], st.premium[3], st.premiumCoins,
				st.premiumUsed, st.premiumUseFailed, st.premiumNoCoins, st.premiumFor[0], st.renewals, st.struggles, st.stepUps,
				st.elixirs[0], st.elixirs[1], st.elixirs[2], st.elixirs[3], st.elixirMarks, st.elixirNoMarks, premiumNow, elixirNow);
		std::string by;
		for (std::map<DWORD, unsigned int>::const_iterator i = st.boosterBy.begin(); i != st.boosterBy.end(); ++i)
			by += (by.empty() ? "" : ",") + std::to_string(i->first) + ":" + std::to_string(i->second);
		std::string kills;
		for (std::map<DWORD, unsigned int>::const_iterator i = st.bossKills.begin(); i != st.bossKills.end(); ++i)
		{
			const long long h = span > 0 ? (long long)i->second * 3600000LL / (long long)span : 0;
			kills += (kills.empty() ? "" : ",") + std::to_string(i->first) + ":" + std::to_string(i->second) + "(" +
					std::to_string(h) + "/h)";
		}
		int due = 0, unknown = 0;
		for (int i = 0; i < PLAYERBOT_BOSS_AREA_COUNT; ++i)
		{
			const int c = GetPlayerBotBossAreaChance(i, dwNow);
			due += c == 100 ? 1 : 0;
			unknown += c == PLAYERBOT_BOSS_ROUTE_UNKNOWN_PCT ? 1 : 0;
		}
		sys_log(0, "PLAYERBOT_SUNGMA: guides census channel=%u span_min=%u boosters=%u booster_sz=%lld booster_by=[%s] booster_budget_hits=%u "
				"marks_avg=%lld loch_guests=%d loch_inside=%d loch_trips=%u loch_entries=%u loch_exits=%u loch_deaths_out=%u "
				"loch_aborts=%u loch_no_altar=%u loch_tickets_used=%u loch_tickets_bought=%u loch_tickets_v3=%u loch_max=%d",
				(unsigned int)g_bChannel, span / 60000, st.boosters, st.boosterMarks, by.empty() ? "-" : by.c_str(), st.boosterBudget,
				marksN ? marks / marksN : 0, guests, inside, st.lochTrips, st.lochEntries, st.lochExits, st.lochDeathsOut,
				st.lochAborts, st.lochNoAltar, st.lochTicketsUsed, st.lochTicketsBought, st.lochTicketsV3, GetPlayerBotLochMax());
		sys_log(0, "PLAYERBOT_SUNGMA: boss_route census channel=%u span_min=%u routing=%d routes=%u found=%u empty=%u give_ups=%u "
				"areas=%d due=%d unknown=%d kills=[%s]",
				(unsigned int)g_bChannel, span / 60000, leaders, st.routes, st.found, st.empty, st.giveUps, PLAYERBOT_BOSS_AREA_COUNT,
				due, unknown, kills.empty() ? "-" : kills.c_str());
		// the census's window: the kills an hour are the span's
		st.bossKills.clear();
	}
}

#endif

#endif
