#ifndef __INC_METIN2_PLAYERBOT_YOHARA_SUNGMA_H__
#define __INC_METIN2_PLAYERBOT_YOHARA_SUNGMA_H__

// MT2009_PLUS_BOT_YOHARA_MAPS_V1 - the bots on the Sung Ma maps of Yohara (the owner, 22 October 2026: "Przygotuj 100
// botow z takim EQ jak do Hydry i wpusc je na mapy Yohary, krok po kroku bedziemy testowac nawigacje, zabijanie
// potworow, exp, ich logike. Naucz je, jak sie po nich poruszac, jakie sa mapy, na jakich poziomach Czempiona maja
// byc na jakich mapach, jakie statystyki musza miec na kazda mape. Uwaga: wszystkie boty domyslnie maja miec
// maksymalny poziom Precyzji. Ten system ich nie dotyczy."). Plan: cache/yohara/plan-boty-yohara.md (2.1, 4.3, 5.3,
// 5.4, 7.1-7.4); the doc for the owner: cache/yohara/boty-mapy-yohary.md.
//
// The knowledge - PLAYERBOT_SUNGMA_MAPS, in the players' order of the maps (each one's portal leads to the next):
//
//   map                          core   Champion band   Sung Ma str/hp/move/immune   Precyzja   monsters
//   374 Opuszczona Twierdza      game3   1-5             0/0/1/0                       0          119-120
//   373 Dongan                   game3   3-10           15/10/15/20                   10          119-120
//   376 Seoganland               game3   6-12           20/10/20/25                   10          119-120
//   377 Namgan                   game3   8-15           25/15/25/30                   10          119-120
//   385 Przelecz Yilad           game3  12-20           30/20/30/35                   30          122-123
//   388 Wawoz Polnocnego Wiatru  game3  15-22           30/25/30/35                   50          123-124
//   389 Rozpadlina Dusz          game3  18-25           35/25/35/40                   50          123-124
//   393 Schronienie Pln. Wiatru  game3  22-30           45/35/45/50                   50          124-125
//   394 Zejscie Pln. Wiatru      game3  26-30           50/40/50/55                   50          125-126
//
// The bands are the plan's (5.4: the Will the gear of each stage adds, plus three points a Champion level); the
// requirements are sungma_table.txt's, read at run time (champion::MapRequirement - the column copy below is the
// fallback and the doc). "Odpornosc" is POINT_SUNGMA_MOVE, "Inteligencja" POINT_SUNGMA_IMMUNE (playerbot_champion.cpp).
//
// A bot's map: the highest map of the table switched on (PLAYERBOT_SUNGMA_MAPS) whose band floor its Champion level
// has reached and whose Sila, Witalnosc and Odpornosc its effective Will (points + items, yohara_gear::SungmaEffective)
// meets, with room (PLAYERBOT_SUNGMA_MAP_MAX a map), and not "not now" (a step down after its deaths); none - the
// Twierdza (it asks Odpornosc 1). Inteligencja is not asked: its penalty halves only the poison / fire / bleeding the
// bot's blows put on monsters. Precyzja is not asked either - no bot's blow misses (ChampionDamage) and every bot has
// Precyzja P (PrecisionSkillBonus): the owner's rule of 22 October.
//
// The roads: a bot of the home core (game1) whose map it is goes by the core handover (purpose "yohara", the row's
// target_map the map) and lands on the map's arrival (Town.txt, the players' landing by the portal from the map
// before). Between the maps (all on game3) a bot walks to the portal of its map that leads the way it goes (npc.txt
// 10127-10203: the WARP monsters) and is put on the next map's arrival - the players' way; a map with no portal that
// way (Rozpadlina -> Schronienie, Dongan -> Twierdza by its Teleporter), or a walk over PLAYERBOT_SUNGMA_PORTAL_WALK_MS,
// warps from where it stands. Zejscie (394) is built in rooms its portals join (8 pieces of terrain): a bot hunts the
// room it stands in and is moved to another room every PLAYERBOT_SUNGMA_CHAMBER_MS, or when its room has no spot for
// it (the chamber hop).
//
// On a map: the spots (PLAYERBOT_SUNGMA_HUBS_<map>, tools/yohara_bot_sungma_map.py on the map's files and
// server_attr) carry 100 + the Champion floor in their level columns (PlayerBotHubLevel, playerbot_wandering.h) -
// the two by the arrival from the map's floor, the stronger packs a level or two over it; the bosses are a party's
// (their raid hubs); the Metins and the outposts for a party of three only (IsPlayerBotSungmaStoneForMe -
// MT2009_PLUS_BOT_SUNGMA_DEATHS_V1). The stay is an expedition (PLAYERBOT_SUNGMA_STAY_MIN, a cohort's
// member its cohort's): the belt kept full on the map (RestockPlayerBotYohara), a member's bag tidied where it stands.
// Deaths: PLAYERBOT_YOHARA_DEATHS_WINDOWED (3) in half an hour - a step down a map for two hours ("not now" on this
// one), warped there at once (MT2009_PLUS_BOT_SUNGMA_DEATHS_V1: no walk to the portal through the packs that killed
// it); PLAYERBOT_SUNGMA_DEATHS_STAY (10) in a stay - home (a member: its rest).
//
// The Champion's growth: a bot's champion experience comes as a person's (champion::GiveExp; conqueror_exp_rate_bot
// on top - 100 by default); its Sung Ma points are spent at once, on the stat its next map lacks most (Sila,
// Odpornosc, Witalnosc; Inteligencja when those three suffice for the top map - plan 5.3), and the pick moves it up a
// map as soon as the band and the Will allow (looked at every PLAYERBOT_SUNGMA_PICK_MS after PLAYERBOT_SUNGMA_SETTLE_MS
// on a map).
//
// The log: PLAYERBOT_SUNGMA (move, portal, chamber hop, points, champion level up, step down, census a map every five
// minutes: here, the channel's rows, kills and kills an hour, experience and champion experience an hour, deaths,
// stuck, navigation failures, level-ups, champion level-ups, moves in and out, the average Champion level).
//
// MT2009_PLUS_BOT_YOHARA_MAPS_V2 (the owner, 22 October evening: "dokoncz mapy" - the roads, Dongan's services, the
// deaths on the higher maps; doc: cache/yohara/boty-mapy-yohary.md, section 9):
//   * the spots are the bots' at last (GetPlayerBotYoharaHubs never answered for these maps: V1's bots walked +-1200
//     round wherever they stood);
//   * a portal is walked to only from near it (PLAYERBOT_SUNGMA_PORTAL_WALK_NEAR) - the onward portals stand 87-355 k
//     units' walk from the arrivals, past up to 144 spawn points: the Yilad nav_fail and most deaths of the first run;
//   * a revived resident stands up at its map's safe point (PLAYERBOT_SUNGMA_SAFE_POINTS), not in the pack;
//   * a lone bot leaves a Sung Ma boss alone (BuildPlayerBotCombatContext), Schronienie's five densest spots are a
//     party's;
//   * a step up asks PLAYERBOT_SUNGMA_STEP_UP_LEVELS over the floor and every requirement, Inteligencja too (its points
//     now go to the next map's Inteligencja as well); the map judged only once the items (the glove's Will) are in;
//   * Dongan's errand (ManagePlayerBotSungmaErrand): potions and junk at Dongan's merchants, never home; the belt kept
//     full where it stands only as the errand's fallback.
//
// MT2009_PLUS_BOT_YOHARA_TRADE_TRIP_V1 (the owner, 22 October: "do M1 ida tylko handlowac"): home (its first village on
// game1, by the handover) only to trade - its counter served, the stands browsed - and back to its map by a new handover
// at once, the bot a "yohara" bot all the while (StartPlayerBotSungmaTradeTrip, ManagePlayerBotSungmaTradeHomes; the log's
// "trade trip start / home / back / landed", the census's trade_trips). The stay's end (PLAYERBOT_SUNGMA_STAY_MIN) is that
// trip's round now, not a way home; the deaths, no weapon or armour and the cohort's rest stay as they were.
//
// An implementation fragment: included by playerbot_yohara_bots.h inside its namespace, after the cohorts and the
// way out, before the route.

	// ------------------------------------------------------------ the spots
	// tools/yohara_bot_sungma_map.py on the test world's map files (22 October 2026): x, y, 100 + the Champion floor, 255,
	// a party's, the boss's race; the spots nearest the arrival first. MT2009_PLUS_BOT_YOHARA_MAPS_V2 (the same tool, the
	// same files): Schronienie's five densest spots (13-16 spawn lines, 52-64 aggressive monsters round each) a party's.
	// map 374 (metin2_map_empirecastle): arrival (537650, 494950); monsters 119-120; band 1-5; 14 spots, 4 bosses
	const TPlayerBotHuntingHub PLAYERBOT_SUNGMA_HUBS_374[] = {
		{ 534550, 501650, 101, 255, false, 0 },	// 12 lines, to 120, 64k HP: 6700 Hell_Hound, 6693 Jin_Bing
		{ 540850, 501650, 101, 255, false, 0 },	// 5 lines, to 120, 64k HP: 6700 Hell_Hound, 6694 Soldier_Ki
		{ 547850, 504350, 102, 255, false, 0 },	// 13 lines, to 120, 64k HP: 6700 Hell_Hound, 6687 Soldier_Ki
		{ 525450, 501650, 102, 255, false, 0 },	// 15 lines, to 120, 64k HP: 6700 Hell_Hound, 6693 Jin_Bing
		{ 533650, 509550, 102, 255, false, 0 },	// 8 lines, to 120, 64k HP: 6700 Hell_Hound, 6693 Jin_Bing
		{ 553150, 499550, 102, 255, false, 0 },	// 4 lines, to 120, 86k HP: 6700 Hell_Hound, 6687 Soldier_Ki
		{ 542750, 511250, 102, 255, false, 0 },	// 7 lines, to 120, 64k HP: 6700 Hell_Hound, 6687 Soldier_Ki
		{ 554150, 504450, 102, 255, false, 0 },	// 9 lines, to 120, 64k HP: 6700 Hell_Hound, 6687 Soldier_Ki
		{ 549850, 511050, 102, 255, false, 0 },	// 6 lines, to 120, 64k HP: 6700 Hell_Hound, 6686 Jin_Bing
		{ 560450, 508150, 102, 255, false, 0 },	// 3 lines, to 120, 93k HP: 6694 Soldier_Ki, 6695 Soldier_Mao
		{ 548850, 523450, 102, 255, false, 0 },	// 4 lines, to 120, 86k HP: 6700 Hell_Hound, 6687 Soldier_Ki
		{ 524850, 523450, 102, 255, false, 0 },	// 5 lines, to 120, 64k HP: 6700 Hell_Hound, 6693 Jin_Bing
		{ 530850, 526750, 102, 255, false, 0 },	// 3 lines, to 120, 64k HP: 6700 Hell_Hound, 6693 Jin_Bing
		{ 543650, 528650, 102, 255, false, 0 },	// 3 lines, to 120, 93k HP: 6687 Soldier_Ki, 6688 Soldier_Mao
		{ 552550, 507450, 103, 255, true, 6692 },	// boss King_Bao_(Quest), 125, 467k HP
		{ 523050, 500850, 103, 255, true, 6699 },	// boss King_Bao, 125, 567k HP
		{ 544850, 509250, 103, 255, true, 6698 },	// boss Kao, 123, 424k HP
		{ 547050, 505450, 103, 255, true, 6698 },	// boss Kao, 123, 424k HP
	};
	// map 373 (metin2_map_eastplain_01): arrival (1102450, 506850); monsters 119-120; band 3-10; 20 spots, 4 bosses
	const TPlayerBotHuntingHub PLAYERBOT_SUNGMA_HUBS_373[] = {
		{ 1114550, 507550, 103, 255, false, 0 },	// 7 lines, to 120, 87k HP: 6713 Troll_Warrior, 6700 Hell_Hound
		{ 1090550, 501950, 103, 255, false, 0 },	// 6 lines, to 120, 87k HP: 6712 Troll_Soldier, 6713 Troll_Warrior
		{ 1101450, 492650, 104, 255, false, 0 },	// 7 lines, to 120, 87k HP: 6713 Troll_Warrior, 6712 Troll_Soldier
		{ 1084250, 515850, 104, 255, false, 0 },	// 8 lines, to 120, 87k HP: 6712 Troll_Soldier, 6713 Troll_Warrior
		{ 1122050, 517050, 104, 255, false, 0 },	// 9 lines, to 120, 87k HP: 6712 Troll_Soldier, 6713 Troll_Warrior
		{ 1080350, 496850, 104, 255, false, 0 },	// 7 lines, to 120, 87k HP: 6713 Troll_Warrior, 6700 Hell_Hound
		{ 1120350, 524350, 104, 255, false, 0 },	// 7 lines, to 120, 87k HP: 6713 Troll_Warrior, 6700 Hell_Hound
		{ 1067950, 516050, 104, 255, false, 0 },	// 9 lines, to 120, 87k HP: 6713 Troll_Warrior, 6700 Hell_Hound
		{ 1124850, 537750, 104, 255, false, 0 },	// 7 lines, to 120, 87k HP: 6712 Troll_Soldier, 6713 Troll_Warrior
		{ 1064450, 500650, 104, 255, false, 0 },	// 7 lines, to 120, 86k HP: 6700 Hell_Hound, 6710 Mistreated_Ghost
		{ 1140950, 515950, 104, 255, false, 0 },	// 6 lines, to 120, 87k HP: 6712 Troll_Soldier, 6713 Troll_Warrior
		{ 1061550, 492250, 104, 255, false, 0 },	// 7 lines, to 120, 86k HP: 6700 Hell_Hound, 6713 Troll_Warrior
		{ 1065050, 529350, 104, 255, false, 0 },	// 9 lines, to 120, 87k HP: 6712 Troll_Soldier, 6713 Troll_Warrior
		{ 1057250, 509650, 104, 255, false, 0 },	// 7 lines, to 120, 87k HP: 6712 Troll_Soldier, 6713 Troll_Warrior
		{ 1074050, 543550, 104, 255, false, 0 },	// 8 lines, to 120, 87k HP: 6713 Troll_Warrior, 6700 Hell_Hound
		{ 1055950, 517250, 104, 255, false, 0 },	// 6 lines, to 120, 87k HP: 6713 Troll_Warrior, 6700 Hell_Hound
		{ 1059050, 532250, 104, 255, false, 0 },	// 7 lines, to 120, 86k HP: 6710 Mistreated_Ghost, 6700 Hell_Hound
		{ 1064750, 541950, 104, 255, false, 0 },	// 6 lines, to 120, 86k HP: 6700 Hell_Hound, 6710 Mistreated_Ghost
		{ 1138350, 544150, 104, 255, false, 0 },	// 10 lines, to 120, 87k HP: 6712 Troll_Soldier, 6713 Troll_Warrior
		{ 1123050, 556350, 104, 255, false, 0 },	// 8 lines, to 120, 87k HP: 6710 Mistreated_Ghost, 6712 Troll_Soldier
		{ 1056350, 498750, 105, 255, true, 6706 },	// boss Argos, 125, 687k HP
		{ 1117050, 523250, 105, 255, true, 6717 },	// boss Argos, 125, 687k HP
		{ 1111550, 487850, 105, 255, true, 6716 },	// boss Natanan, 123, 454k HP
		{ 1071650, 555250, 105, 255, true, 6706 },	// boss Argos, 125, 687k HP
	};
	// map 376 (metin2_map_eastplain_02): arrival (1223350, 491750); monsters 119-120; band 6-12; 20 spots, 3 bosses
	const TPlayerBotHuntingHub PLAYERBOT_SUNGMA_HUBS_376[] = {
		{ 1215650, 504050, 106, 255, false, 0 },	// 10 lines, to 120, 147k HP: 6719 Quag_Worker, 6722 Quag_Sorcerer
		{ 1210050, 497750, 106, 255, false, 0 },	// 9 lines, to 120, 147k HP: 6719 Quag_Worker, 6722 Quag_Sorcerer
		{ 1220050, 509750, 107, 255, false, 0 },	// 9 lines, to 120, 147k HP: 6719 Quag_Worker, 6722 Quag_Sorcerer
		{ 1205650, 511450, 107, 255, false, 0 },	// 13 lines, to 120, 147k HP: 6719 Quag_Worker, 6722 Quag_Sorcerer
		{ 1193550, 495350, 107, 255, false, 0 },	// 10 lines, to 120, 147k HP: 6719 Quag_Worker, 6721 Quag_Warrior
		{ 1198850, 509650, 107, 255, false, 0 },	// 10 lines, to 120, 147k HP: 6719 Quag_Worker, 6718 Quag_Kovix
		{ 1191950, 487550, 107, 255, false, 0 },	// 17 lines, to 120, 147k HP: 6719 Quag_Worker, 6718 Quag_Kovix
		{ 1183750, 484350, 107, 255, false, 0 },	// 12 lines, to 120, 147k HP: 6719 Quag_Worker, 6722 Quag_Sorcerer
		{ 1212750, 533450, 107, 255, false, 0 },	// 9 lines, to 120, 147k HP: 6719 Quag_Worker, 6722 Quag_Sorcerer
		{ 1193650, 528450, 107, 255, false, 0 },	// 9 lines, to 120, 147k HP: 6719 Quag_Worker, 6721 Quag_Warrior
		{ 1176150, 484550, 107, 255, false, 0 },	// 13 lines, to 120, 147k HP: 6719 Quag_Worker, 6722 Quag_Sorcerer
		{ 1202050, 535150, 107, 255, false, 0 },	// 10 lines, to 120, 147k HP: 6719 Quag_Worker, 6718 Quag_Kovix
		{ 1171650, 491950, 107, 255, false, 0 },	// 15 lines, to 120, 147k HP: 6719 Quag_Worker, 6721 Quag_Warrior
		{ 1193950, 535350, 107, 255, false, 0 },	// 14 lines, to 120, 147k HP: 6719 Quag_Worker, 6718 Quag_Kovix
		{ 1199650, 542550, 107, 255, false, 0 },	// 14 lines, to 120, 147k HP: 6719 Quag_Worker, 6718 Quag_Kovix
		{ 1167250, 487350, 107, 255, false, 0 },	// 9 lines, to 120, 147k HP: 6719 Quag_Worker, 6718 Quag_Kovix
		{ 1192850, 542150, 107, 255, false, 0 },	// 19 lines, to 120, 147k HP: 6719 Quag_Worker, 6718 Quag_Kovix
		{ 1185250, 538450, 107, 255, false, 0 },	// 12 lines, to 120, 147k HP: 6719 Quag_Worker, 6722 Quag_Sorcerer
		{ 1164550, 507950, 107, 255, false, 0 },	// 9 lines, to 120, 147k HP: 6722 Quag_Sorcerer, 6719 Quag_Worker
		{ 1163950, 542250, 107, 255, false, 0 },	// 14 lines, to 120, 147k HP: 6719 Quag_Worker, 6718 Quag_Kovix
		{ 1198550, 511150, 108, 255, true, 6724 },	// boss Quag_Primus, 125, 767k HP
		{ 1192050, 545250, 108, 255, true, 6723 },	// boss Quag_Veteran, 123, 514k HP
		{ 1204050, 516250, 108, 255, true, 6724 },	// boss Quag_Primus, 125, 767k HP
	};
	// map 377 (metin2_map_eastplain_03): arrival (1279650, 440950); monsters 119-120; band 8-15; 20 spots, 4 bosses
	// MT2009_PLUS_BOT_SUNGMA_NEST_V1: the spots of 13 spawn lines and more a party's (as Schronienie's, V2). Namgan never
	// gave the bots a kill (census 27 October: kills 0 at 19:02, 19:58 and 21:06 - 268 deaths): its two spots by the
	// arrival (18 and 16 lines, 3-6 k from it, Myr sorcerers aggressive among them) were every lone bot's first, and
	// Hydra's bots of 22-24 k health were "pulled" there by 5-12 monsters within a minute of landing (20:16-20:18). The
	// lone bots' floor now: the 6 and 8 line spots 10 and 21 k from the arrival.
	const TPlayerBotHuntingHub PLAYERBOT_SUNGMA_HUBS_377[] = {
		{ 1285850, 443350, 108, 255, true, 0 },	// 18 lines, to 120, 93k HP: 6700 Hell_Hound, 6712 Troll_Soldier (NEST_V1: a party's - dense)
		{ 1273550, 444650, 108, 255, true, 0 },	// 16 lines, to 120, 147k HP: 6727 Quag_Golem, 6729 Quag_Sorcerer (NEST_V1: a party's - dense)
		{ 1277850, 450750, 108, 255, false, 0 },	// 6 lines, to 120, 147k HP: 6725 Quag_Kovix, 6726 Quag_Worker (NEST_V1: the band's floor - the lone bots' first spots)
		{ 1262850, 453550, 108, 255, false, 0 },	// 8 lines, to 120, 147k HP: 6729 Quag_Sorcerer, 6727 Quag_Golem (NEST_V1: the band's floor - the lone bots' first spots)
		{ 1293250, 459950, 109, 255, false, 0 },	// 7 lines, to 120, 147k HP: 6727 Quag_Golem, 6729 Quag_Sorcerer
		{ 1287550, 463450, 109, 255, false, 0 },	// 9 lines, to 120, 147k HP: 6729 Quag_Sorcerer, 6727 Quag_Golem
		{ 1301350, 452950, 109, 255, false, 0 },	// 5 lines, to 120, 147k HP: 6722 Quag_Sorcerer, 6725 Quag_Kovix
		{ 1255550, 447250, 109, 255, false, 0 },	// 5 lines, to 120, 147k HP: 6725 Quag_Kovix, 6726 Quag_Worker
		{ 1300250, 461750, 109, 255, true, 0 },	// 15 lines, to 120, 147k HP: 6729 Quag_Sorcerer, 6727 Quag_Golem (NEST_V1: a party's - dense)
		{ 1250350, 444150, 109, 255, true, 0 },	// 13 lines, to 120, 147k HP: 6727 Quag_Golem, 6726 Quag_Worker (NEST_V1: a party's - dense)
		{ 1293750, 468050, 109, 255, true, 0 },	// 14 lines, to 120, 147k HP: 6727 Quag_Golem, 6729 Quag_Sorcerer (NEST_V1: a party's - dense)
		{ 1313550, 449750, 109, 255, false, 0 },	// 7 lines, to 120, 106k HP: 6727 Quag_Golem, 6729 Quag_Sorcerer
		{ 1297150, 472650, 109, 255, false, 0 },	// 6 lines, to 120, 147k HP: 6727 Quag_Golem, 6725 Quag_Kovix
		{ 1307750, 464050, 109, 255, false, 0 },	// 7 lines, to 120, 147k HP: 6725 Quag_Kovix, 6726 Quag_Worker
		{ 1254350, 467250, 109, 255, false, 0 },	// 7 lines, to 120, 147k HP: 6727 Quag_Golem, 6729 Quag_Sorcerer
		{ 1243150, 443350, 109, 255, true, 0 },	// 18 lines, to 120, 114k HP: 6727 Quag_Golem, 6729 Quag_Sorcerer (NEST_V1: a party's - dense)
		{ 1318250, 456250, 109, 255, false, 0 },	// 10 lines, to 120, 93k HP: 6726 Quag_Worker, 6727 Quag_Golem
		{ 1247950, 470550, 109, 255, true, 0 },	// 15 lines, to 120, 147k HP: 6726 Quag_Worker, 6727 Quag_Golem (NEST_V1: a party's - dense)
		{ 1318050, 463350, 109, 255, false, 0 },	// 6 lines, to 120, 114k HP: 6727 Quag_Golem, 6729 Quag_Sorcerer
		{ 1323750, 452250, 109, 255, true, 0 },	// 16 lines, to 120, 93k HP: 6700 Hell_Hound, 6710 Mistreated_Ghost (NEST_V1: a party's - dense)
		{ 1293650, 463650, 110, 255, true, 6731 },	// boss Quag_Primus, 125, 767k HP
		{ 1245850, 470250, 110, 255, true, 6730 },	// boss Quag_Veteran, 123, 514k HP
		{ 1288850, 458250, 110, 255, true, 6730 },	// boss Quag_Veteran, 123, 514k HP
		{ 1321650, 450250, 110, 255, true, 6705 },	// boss Natanan, 123, 454k HP
	};
	// map 385 (metin2_map_snakevalley): arrival (31650, 1414850); monsters 122-123; band 12-20; 20 spots, 2 bosses
	const TPlayerBotHuntingHub PLAYERBOT_SUNGMA_HUBS_385[] = {
		{ 44250, 1428250, 112, 255, false, 0 },	// 17 lines, to 123, 157k HP: 6875 Tainted_Soldier, 6758 Tainted_Soldier
		{ 30550, 1434550, 112, 255, false, 0 },	// 14 lines, to 123, 157k HP: 6758 Tainted_Soldier, 6875 Tainted_Soldier
		{ 18950, 1431450, 113, 255, false, 0 },	// 33 lines, to 123, 157k HP: 6875 Tainted_Soldier, 6876 Tainted_Skirmisher
		{ 48750, 1433450, 113, 255, false, 0 },	// 10 lines, to 123, 124k HP: 6758 Tainted_Soldier, 6875 Tainted_Soldier
		{ 65450, 1425050, 113, 255, false, 0 },	// 10 lines, to 123, 157k HP: 6878 Tainted_Monk, 6761 Tainted_Monk
		{ 20650, 1451050, 113, 255, false, 0 },	// 14 lines, to 123, 167k HP: 6876 Tainted_Skirmisher, 6875 Tainted_Soldier
		{ 68250, 1437250, 113, 255, false, 0 },	// 11 lines, to 123, 183k HP: 6760 Tainted_Warrior, 6877 Tainted_Warrior
		{ 23450, 1457350, 113, 255, false, 0 },	// 11 lines, to 123, 157k HP: 6876 Tainted_Skirmisher, 6758 Tainted_Soldier
		{ 62850, 1448450, 113, 255, false, 0 },	// 11 lines, to 123, 157k HP: 6875 Tainted_Soldier, 6876 Tainted_Skirmisher
		{ 42750, 1459450, 113, 255, false, 0 },	// 11 lines, to 123, 157k HP: 6761 Tainted_Monk, 6878 Tainted_Monk
		{ 75150, 1433650, 113, 255, false, 0 },	// 21 lines, to 123, 157k HP: 6875 Tainted_Soldier, 6876 Tainted_Skirmisher
		{ 26050, 1464250, 113, 255, false, 0 },	// 10 lines, to 123, 183k HP: 6877 Tainted_Warrior, 6760 Tainted_Warrior
		{ 84650, 1434150, 113, 255, false, 0 },	// 11 lines, to 123, 124k HP: 6758 Tainted_Soldier, 6875 Tainted_Soldier
		{ 92450, 1437350, 113, 255, false, 0 },	// 17 lines, to 123, 157k HP: 6875 Tainted_Soldier, 6758 Tainted_Soldier
		{ 100150, 1437450, 113, 255, false, 0 },	// 22 lines, to 123, 124k HP: 6875 Tainted_Soldier, 6758 Tainted_Soldier
		{ 98050, 1455450, 113, 255, false, 0 },	// 10 lines, to 123, 157k HP: 6758 Tainted_Soldier, 6878 Tainted_Monk
		{ 108550, 1455850, 113, 255, false, 0 },	// 15 lines, to 123, 167k HP: 6759 Tainted_Skirmisher, 6878 Tainted_Monk
		{ 119750, 1435050, 113, 255, false, 0 },	// 18 lines, to 123, 167k HP: 6759 Tainted_Skirmisher, 6761 Tainted_Monk
		{ 117650, 1459850, 113, 255, false, 0 },	// 15 lines, to 123, 157k HP: 6878 Tainted_Monk, 6761 Tainted_Monk
		{ 115250, 1468050, 113, 255, false, 0 },	// 16 lines, to 123, 176k HP: 6877 Tainted_Warrior, 6760 Tainted_Warrior
		{ 115050, 1438050, 114, 255, true, 6764 },	// boss Tainted_War_Chief, 126, 867k HP
		{ 119550, 1462050, 114, 255, true, 6764 },	// boss Tainted_War_Chief, 126, 867k HP
	};
	// map 388 (metin2_map_icecrystalcave): arrival (110650, 1599750); monsters 123-124; band 15-22; 20 spots, 2 bosses
	const TPlayerBotHuntingHub PLAYERBOT_SUNGMA_HUBS_388[] = {
		{ 94950, 1594250, 115, 255, false, 0 },	// 8 lines, to 124, 170k HP: 6882 Soulless_Fox, 6883 Frozen_Scout
		{ 99450, 1582350, 115, 255, false, 0 },	// 9 lines, to 124, 170k HP: 6882 Soulless_Fox, 6883 Frozen_Scout
		{ 80650, 1587350, 116, 255, false, 0 },	// 8 lines, to 124, 170k HP: 6770 Frozen_Fox, 6771 Frozen_Scout
		{ 80950, 1576550, 116, 255, false, 0 },	// 8 lines, to 124, 170k HP: 6882 Soulless_Fox, 6883 Frozen_Scout
		{ 93550, 1562650, 116, 255, false, 0 },	// 8 lines, to 124, 170k HP: 6882 Soulless_Fox, 6883 Frozen_Scout
		{ 52650, 1583350, 116, 255, false, 0 },	// 8 lines, to 124, 170k HP: 6882 Soulless_Fox, 6883 Frozen_Scout
		{ 87950, 1542250, 116, 255, false, 0 },	// 8 lines, to 124, 170k HP: 6882 Soulless_Fox, 6883 Frozen_Scout
		{ 95850, 1533250, 116, 255, false, 0 },	// 9 lines, to 124, 170k HP: 6770 Frozen_Fox, 6771 Frozen_Scout
		{ 85950, 1535750, 116, 255, false, 0 },	// 8 lines, to 124, 170k HP: 6770 Frozen_Fox, 6771 Frozen_Scout
		{ 46450, 1574250, 116, 255, false, 0 },	// 9 lines, to 124, 170k HP: 6882 Soulless_Fox, 6883 Frozen_Scout
		{ 40850, 1583850, 116, 255, false, 0 },	// 8 lines, to 124, 170k HP: 6882 Soulless_Fox, 6883 Frozen_Scout
		{ 59450, 1547450, 116, 255, false, 0 },	// 8 lines, to 124, 170k HP: 6882 Soulless_Fox, 6883 Frozen_Scout
		{ 36450, 1594250, 116, 255, false, 0 },	// 10 lines, to 124, 170k HP: 6770 Frozen_Fox, 6771 Frozen_Scout
		{ 76650, 1528550, 116, 255, false, 0 },	// 9 lines, to 124, 170k HP: 6770 Frozen_Fox, 6771 Frozen_Scout
		{ 84450, 1524750, 116, 255, false, 0 },	// 8 lines, to 124, 170k HP: 6882 Soulless_Fox, 6883 Frozen_Scout
		{ 46550, 1549850, 116, 255, false, 0 },	// 9 lines, to 124, 170k HP: 6882 Soulless_Fox, 6883 Frozen_Scout
		{ 40350, 1557050, 116, 255, false, 0 },	// 8 lines, to 124, 170k HP: 6882 Soulless_Fox, 6883 Frozen_Scout
		{ 31150, 1567750, 116, 255, false, 0 },	// 8 lines, to 124, 170k HP: 6770 Frozen_Fox, 6771 Frozen_Scout
		{ 22750, 1583050, 116, 255, false, 0 },	// 8 lines, to 124, 170k HP: 6882 Soulless_Fox, 6883 Frozen_Scout
		{ 30450, 1544250, 116, 255, false, 0 },	// 8 lines, to 124, 170k HP: 6770 Frozen_Fox, 6771 Frozen_Scout
		{ 58050, 1585450, 117, 255, true, 6776 },	// boss Frozen_War_Chief, 127, 897k HP
		{ 85050, 1595450, 117, 255, true, 6776 },	// boss Frozen_War_Chief, 127, 897k HP
	};
	// map 389 (metin2_map_whitdragonvalley): arrival (183050, 1579450); monsters 123-124; band 18-25; 20 spots, 2 bosses
	const TPlayerBotHuntingHub PLAYERBOT_SUNGMA_HUBS_389[] = {
		{ 185450, 1565350, 118, 255, false, 0 },	// 7 lines, to 124, 173k HP: 6777 Frenzied_Frost_Deer, 6778 Frenzied_Snow_Leopard
		{ 184050, 1557150, 118, 255, false, 0 },	// 7 lines, to 124, 173k HP: 6777 Frenzied_Frost_Deer, 6778 Frenzied_Snow_Leopard
		{ 173350, 1557450, 119, 255, false, 0 },	// 6 lines, to 124, 173k HP: 6777 Frenzied_Frost_Deer, 6778 Frenzied_Snow_Leopard
		{ 173550, 1546150, 119, 255, false, 0 },	// 6 lines, to 124, 173k HP: 6777 Frenzied_Frost_Deer, 6778 Frenzied_Snow_Leopard
		{ 163250, 1549250, 119, 255, false, 0 },	// 7 lines, to 124, 173k HP: 6889 Cursed_Frost_Deer, 6890 Frenzied_Snow_Leopard
		{ 155250, 1556050, 119, 255, false, 0 },	// 7 lines, to 124, 173k HP: 6889 Cursed_Frost_Deer, 6890 Frenzied_Snow_Leopard
		{ 185950, 1540050, 119, 255, false, 0 },	// 8 lines, to 124, 173k HP: 6889 Cursed_Frost_Deer, 6890 Frenzied_Snow_Leopard
		{ 171650, 1538450, 119, 255, false, 0 },	// 7 lines, to 124, 173k HP: 6889 Cursed_Frost_Deer, 6890 Frenzied_Snow_Leopard
		{ 152550, 1546650, 119, 255, false, 0 },	// 8 lines, to 124, 173k HP: 6889 Cursed_Frost_Deer, 6890 Frenzied_Snow_Leopard
		{ 188550, 1533250, 119, 255, false, 0 },	// 6 lines, to 124, 173k HP: 6777 Frenzied_Frost_Deer, 6778 Frenzied_Snow_Leopard
		{ 158650, 1538750, 119, 255, false, 0 },	// 8 lines, to 124, 173k HP: 6777 Frenzied_Frost_Deer, 6778 Frenzied_Snow_Leopard
		{ 169950, 1531950, 119, 255, false, 0 },	// 7 lines, to 124, 173k HP: 6889 Cursed_Frost_Deer, 6890 Frenzied_Snow_Leopard
		{ 140750, 1553750, 119, 255, false, 0 },	// 6 lines, to 124, 173k HP: 6777 Frenzied_Frost_Deer, 6778 Frenzied_Snow_Leopard
		{ 151650, 1536350, 119, 255, false, 0 },	// 6 lines, to 124, 173k HP: 6889 Cursed_Frost_Deer, 6890 Frenzied_Snow_Leopard
		{ 184350, 1524650, 119, 255, false, 0 },	// 7 lines, to 124, 173k HP: 6777 Frenzied_Frost_Deer, 6778 Frenzied_Snow_Leopard
		{ 175150, 1521850, 119, 255, false, 0 },	// 5 lines, to 124, 173k HP: 6889 Cursed_Frost_Deer, 6890 Frenzied_Snow_Leopard
		{ 163550, 1522550, 119, 255, false, 0 },	// 6 lines, to 124, 173k HP: 6777 Frenzied_Frost_Deer, 6778 Frenzied_Snow_Leopard
		{ 146350, 1528550, 119, 255, false, 0 },	// 6 lines, to 124, 173k HP: 6777 Frenzied_Frost_Deer, 6778 Frenzied_Snow_Leopard
		{ 155550, 1522350, 119, 255, false, 0 },	// 5 lines, to 124, 173k HP: 6777 Frenzied_Frost_Deer, 6778 Frenzied_Snow_Leopard
		{ 139250, 1528350, 119, 255, false, 0 },	// 5 lines, to 124, 173k HP: 6889 Cursed_Frost_Deer, 6890 Frenzied_Snow_Leopard
		{ 148050, 1560450, 120, 255, true, 6783 },	// boss Northwind_War_Chief, 127, 917k HP
		{ 190050, 1535450, 120, 255, true, 6895 },	// boss Northwind_War_Chief, 127, 917k HP
	};
	// map 393 (metin2_map_whitedragoncave_01): arrival (1006450, 1267250); monsters 124-125; band 22-30; 20 spots, 4 bosses
	const TPlayerBotHuntingHub PLAYERBOT_SUNGMA_HUBS_393[] = {
		{ 1018650, 1305050, 122, 255, false, 0 },	// 11 lines, to 125, 187k HP: 6787 Northwind_Sh._Warlock, 6784 Northwind_Sh._Soldier
		{ 1039450, 1244350, 122, 255, false, 0 },	// 10 lines, to 125, 187k HP: 6787 Northwind_Sh._Warlock, 6784 Northwind_Sh._Soldier
		{ 1021750, 1224550, 123, 255, true, 0 },	// 15 lines, to 125, 175k HP: 6784 Northwind_Sh._Soldier, 6786 Northwind_Sh._Warrior (V2: a party's - dense)
		{ 1038650, 1224550, 123, 255, false, 0 },	// 12 lines, to 125, 175k HP: 6784 Northwind_Sh._Soldier, 6786 Northwind_Sh._Warrior
		{ 1044550, 1306050, 123, 255, false, 0 },	// 10 lines, to 125, 187k HP: 6787 Northwind_Sh._Warlock, 6784 Northwind_Sh._Soldier
		{ 1017450, 1321950, 123, 255, true, 0 },	// 13 lines, to 125, 187k HP: 6787 Northwind_Sh._Warlock, 6784 Northwind_Sh._Soldier (V2: a party's - dense)
		{ 1054150, 1233150, 123, 255, false, 0 },	// 12 lines, to 125, 187k HP: 6784 Northwind_Sh._Soldier, 6787 Northwind_Sh._Warlock
		{ 1069350, 1288550, 123, 255, false, 0 },	// 11 lines, to 125, 187k HP: 6787 Northwind_Sh._Warlock, 6788 Northwind_Sh._General
		{ 1005050, 1336350, 123, 255, true, 0 },	// 16 lines, to 125, 175k HP: 6784 Northwind_Sh._Soldier, 6787 Northwind_Sh._Warlock (V2: a party's - dense)
		{ 1035250, 1337050, 123, 255, false, 0 },	// 10 lines, to 125, 187k HP: 6787 Northwind_Sh._Warlock, 6784 Northwind_Sh._Soldier
		{ 1082350, 1213450, 123, 255, false, 0 },	// 12 lines, to 125, 187k HP: 6784 Northwind_Sh._Soldier, 6786 Northwind_Sh._Warrior
		{ 1075150, 1336350, 123, 255, false, 0 },	// 10 lines, to 125, 187k HP: 6787 Northwind_Sh._Warlock, 6784 Northwind_Sh._Soldier
		{ 1104050, 1239350, 123, 255, false, 0 },	// 12 lines, to 125, 187k HP: 6787 Northwind_Sh._Warlock, 6784 Northwind_Sh._Soldier
		{ 1087250, 1337150, 123, 255, true, 0 },	// 13 lines, to 125, 187k HP: 6787 Northwind_Sh._Warlock, 6785 Shelter_Skirmisher (V2: a party's - dense)
		{ 1100550, 1322550, 123, 255, false, 0 },	// 11 lines, to 125, 187k HP: 6787 Northwind_Sh._Warlock, 6788 Northwind_Sh._General
		{ 1119950, 1300450, 123, 255, false, 0 },	// 11 lines, to 125, 187k HP: 6787 Northwind_Sh._Warlock, 6785 Shelter_Skirmisher
		{ 1119550, 1213650, 123, 255, false, 0 },	// 11 lines, to 125, 175k HP: 6784 Northwind_Sh._Soldier, 6787 Northwind_Sh._Warlock
		{ 1129850, 1227350, 123, 255, false, 0 },	// 12 lines, to 125, 187k HP: 6787 Northwind_Sh._Warlock, 6784 Northwind_Sh._Soldier
		{ 1146650, 1212750, 123, 255, false, 0 },	// 10 lines, to 125, 175k HP: 6784 Northwind_Sh._Soldier, 6786 Northwind_Sh._Warrior
		{ 1146450, 1337250, 123, 255, true, 0 },	// 15 lines, to 125, 187k HP: 6787 Northwind_Sh._Warlock, 6785 Shelter_Skirmisher (V2: a party's - dense)
		{ 1018450, 1320250, 124, 255, true, 6789 },	// boss Northwind_Sh._War_Chief, 130, 937k HP
		{ 1037450, 1224050, 124, 255, true, 6789 },	// boss Northwind_Sh._War_Chief, 130, 937k HP
		{ 1044450, 1323250, 124, 255, true, 6789 },	// boss Northwind_Sh._War_Chief, 130, 937k HP
		{ 1053950, 1233250, 124, 255, true, 6789 },	// boss Northwind_Sh._War_Chief, 130, 937k HP
	};
	// map 394 (metin2_map_whitedragoncave_02): arrival (1159050, 1218250); monsters 125-126; band 26-30; 20 spots, 2 bosses
	const TPlayerBotHuntingHub PLAYERBOT_SUNGMA_HUBS_394[] = {
		{ 1161150, 1210550, 126, 255, false, 0 },	// 4 lines, to 125, 178k HP: 6792 Northwind_Sh._Soldier, 6793 Shelter_Skirmisher
		{ 1169850, 1210750, 126, 255, false, 0 },	// 4 lines, to 125, 178k HP: 6792 Northwind_Sh._Soldier, 6793 Shelter_Skirmisher
		{ 1166850, 1236650, 126, 255, false, 0 },	// 4 lines, to 125, 178k HP: 6794 Northwind_Sh._Warrior, 6792 Northwind_Sh._Soldier
		{ 1184850, 1211150, 126, 255, false, 0 },	// 5 lines, to 125, 191k HP: 6793 Shelter_Skirmisher, 6792 Northwind_Sh._Soldier
		{ 1174250, 1243150, 126, 255, false, 0 },	// 4 lines, to 125, 178k HP: 6794 Northwind_Sh._Warrior, 6792 Northwind_Sh._Soldier
		{ 1167650, 1247050, 127, 255, false, 0 },	// 7 lines, to 126, 178k HP: 6794 Northwind_Sh._Warrior, 6792 Northwind_Sh._Soldier
		{ 1191650, 1211050, 126, 255, false, 0 },	// 3 lines, to 125, 191k HP: 6793 Shelter_Skirmisher, 6792 Northwind_Sh._Soldier
		{ 1193550, 1217650, 126, 255, false, 0 },	// 4 lines, to 125, 191k HP: 6793 Shelter_Skirmisher, 6792 Northwind_Sh._Soldier
		{ 1199150, 1220850, 126, 255, false, 0 },	// 4 lines, to 125, 178k HP: 6792 Northwind_Sh._Soldier, 6793 Shelter_Skirmisher
		{ 1191550, 1241950, 127, 255, false, 0 },	// 5 lines, to 126, 189k HP: 6796 Northwind_Sh._General, 6794 Northwind_Sh._Warrior
		{ 1158950, 1261650, 127, 255, false, 0 },	// 5 lines, to 126, 189k HP: 6792 Northwind_Sh._Soldier, 6793 Shelter_Skirmisher
		{ 1165950, 1261550, 126, 255, false, 0 },	// 4 lines, to 125, 189k HP: 6793 Shelter_Skirmisher, 6792 Northwind_Sh._Soldier
		{ 1173350, 1262650, 126, 255, false, 0 },	// 4 lines, to 125, 189k HP: 6795 Northwind_Sh._Warlock, 6793 Shelter_Skirmisher
		{ 1209150, 1219050, 126, 255, false, 0 },	// 4 lines, to 125, 178k HP: 6792 Northwind_Sh._Soldier, 6793 Shelter_Skirmisher
		{ 1208950, 1211850, 126, 255, false, 0 },	// 5 lines, to 125, 178k HP: 6792 Northwind_Sh._Soldier, 6793 Shelter_Skirmisher
		{ 1210750, 1236150, 126, 255, false, 0 },	// 6 lines, to 125, 178k HP: 6794 Northwind_Sh._Warrior, 6792 Northwind_Sh._Soldier
		{ 1169950, 1272550, 127, 255, false, 0 },	// 7 lines, to 126, 189k HP: 6795 Northwind_Sh._Warlock, 6793 Shelter_Skirmisher
		{ 1215250, 1209550, 126, 255, false, 0 },	// 3 lines, to 125, 178k HP: 6792 Northwind_Sh._Soldier, 6793 Shelter_Skirmisher
		{ 1214750, 1245850, 126, 255, false, 0 },	// 5 lines, to 125, 178k HP: 6792 Northwind_Sh._Soldier, 6795 Northwind_Sh._Warlock
		{ 1219050, 1235650, 126, 255, false, 0 },	// 4 lines, to 125, 178k HP: 6794 Northwind_Sh._Warrior, 6792 Northwind_Sh._Soldier
		{ 1187450, 1218050, 128, 255, true, 6797 },	// boss Northwind_Sh._War_Chief, 131, 947k HP
		{ 1199550, 1209050, 128, 255, true, 6797 },	// boss Northwind_Sh._War_Chief, 131, 947k HP
	};

	// ------------------------------------------------------------ the maps

	struct TPlayerBotSungmaMap
	{
		long lMap;
		const char* szKey;		// the log's name
		BYTE bChampionMin, bChampionMax;
		int aiReq[5];			// sungma_table.txt of 22 October: str, hp, move, immune, hit (the run time reads the file)
		const TPlayerBotHuntingHub* pHubs;
		size_t uHubs;
		bool bChambered;		// rooms joined only by portals (the chamber hop)
	};
#define PLAYERBOT_SUNGMA_HUBS(m) PLAYERBOT_SUNGMA_HUBS_##m, sizeof(PLAYERBOT_SUNGMA_HUBS_##m) / sizeof(PLAYERBOT_SUNGMA_HUBS_##m[0])
	const TPlayerBotSungmaMap PLAYERBOT_SUNGMA_MAPS[] = {
		{ PLAYERBOT_MAP_SUNGMA_TWIERDZA, "twierdza", 1, 5, { 0, 0, 1, 0, 0 }, PLAYERBOT_SUNGMA_HUBS(374), false },
		{ PLAYERBOT_MAP_SUNGMA_DONGAN, "dongan", 3, 10, { 15, 10, 15, 20, 10 }, PLAYERBOT_SUNGMA_HUBS(373), false },
		{ PLAYERBOT_MAP_SUNGMA_SEOGANLAND, "seoganland", 6, 12, { 20, 10, 20, 25, 10 }, PLAYERBOT_SUNGMA_HUBS(376), false },
		{ PLAYERBOT_MAP_SUNGMA_NAMGAN, "namgan", 8, 15, { 25, 15, 25, 30, 10 }, PLAYERBOT_SUNGMA_HUBS(377), false },
		{ PLAYERBOT_MAP_SUNGMA_YILAD, "yilad", 12, 20, { 30, 20, 30, 35, 30 }, PLAYERBOT_SUNGMA_HUBS(385), false },
		{ PLAYERBOT_MAP_SUNGMA_WAWOZ, "wawoz", 15, 22, { 30, 25, 30, 35, 50 }, PLAYERBOT_SUNGMA_HUBS(388), false },
		{ PLAYERBOT_MAP_SUNGMA_ROZPADLINA, "rozpadlina", 18, 25, { 35, 25, 35, 40, 50 }, PLAYERBOT_SUNGMA_HUBS(389), false },
		{ PLAYERBOT_MAP_SUNGMA_SCHRONIENIE, "schronienie", 22, 30, { 45, 35, 45, 50, 50 }, PLAYERBOT_SUNGMA_HUBS(393), false },
		{ PLAYERBOT_MAP_SUNGMA_ZEJSCIE, "zejscie", 26, 30, { 50, 40, 50, 55, 50 }, PLAYERBOT_SUNGMA_HUBS(394), true },
	};
#undef PLAYERBOT_SUNGMA_HUBS
	const int PLAYERBOT_SUNGMA_MAP_COUNT = (int)(sizeof(PLAYERBOT_SUNGMA_MAPS) / sizeof(PLAYERBOT_SUNGMA_MAPS[0]));

	// MT2009_PLUS_BOT_YOHARA_MAPS_V2: tools/yohara_bot_sungma_map.py - the open ground by each arrival farthest from the
	// spawns (to 6 000), where a revived resident stands up (MovePlayerBotSungmaRevived).
	struct TPlayerBotSungmaSafePoint { long lMap, x, y; };
	// the safe points by the arrivals (the revival) - map, x, y; the nearest spawn from it / from the arrival:
	const TPlayerBotSungmaSafePoint PLAYERBOT_SUNGMA_SAFE_POINTS[] = {
		{ 374, 537350, 492750 },	// 6010 / 3868
		{ 373, 1102450, 506850 },	// 9475 / 9475
		{ 376, 1224350, 497450 },	// 6122 / 2196
		{ 377, 1279450, 440550 },	// 3259 / 2815
		{ 385, 31650, 1414850 },	// 9995 / 9995
		{ 388, 112450, 1600050 },	// 5255 / 3611
		{ 389, 182550, 1579650 },	// 5008 / 4474
		{ 393, 1006450, 1267250 },	// 11828 / 11828
		{ 394, 1159050, 1221150 },	// 4752 / 1856
	};

	// MT2009_PLUS_BOT_SUNGMA_NEST_V1: the health a bot needs for a map (its maximum, the Sung Ma penalty counted - what
	// it fights with): a step up only with the floor, a stay with PLAYERBOT_SUNGMA_HP_STAY_PERCENT of it; under it - a
	// map lower (the move's why "unfit"), and up again once its bonuses and its alchemy have raised it. The test of
	// 27 October (20:15-21:06): the cohort's fallen stood at a median of 10 860 (Namgan) - 14 670 (Dongan) maximum health,
	// Hydra's bots at 22 380-24 750; the cohort's 13 790 did on Yilad (35 deaths against ~1 000 kills of the map) and its
	// 15 150 on the Twierdza, while its 13 450-14 190 on Wawoz-Zejscie fell 406, 373, 265 and 118 times; a blow of a
	// berserk 123-125 takes 4-6 k (15-25% of 23-33 k), three at once 25-30% of 23.6 k a second (the test of 22 October).
	// The floors keep the weakest third of the cohort off the maps whose packs are all aggressive (Namgan's sorcerers;
	// Wawoz on: four to a spawn line, 170-190 k each) - Hydra's bots and the cohort's bonused pass them.
	struct TPlayerBotSungmaHpFloor { long lMap; int iMaxHp; };
	const TPlayerBotSungmaHpFloor PLAYERBOT_SUNGMA_HP_FLOORS[] = {
		{ 374, 0 }, { 373, 0 }, { 376, 12000 }, { 377, 15000 }, { 385, 13000 }, { 388, 16000 }, { 389, 16000 },
		{ 393, 20000 }, { 394, 20000 },
	};
	const int PLAYERBOT_SUNGMA_HP_STAY_PERCENT = 90;

	// The portals (npc.txt; a cell centre beside each, tools/yohara_bot_sungma_map.py): on map lFrom, the one to lTo.
	struct TPlayerBotSungmaPortal { long lFrom, lTo, x, y; };
	const TPlayerBotSungmaPortal PLAYERBOT_SUNGMA_PORTALS[] = {
		{ PLAYERBOT_MAP_SUNGMA_TWIERDZA, PLAYERBOT_MAP_SUNGMA_DONGAN, 557350, 531950 },		// 10144, by the gate (453,455)
		{ PLAYERBOT_MAP_SUNGMA_DONGAN, PLAYERBOT_MAP_SUNGMA_SEOGANLAND, 1053650, 488350 },	// 10128 (40,531)
		{ PLAYERBOT_MAP_SUNGMA_SEOGANLAND, PLAYERBOT_MAP_SUNGMA_DONGAN, 1224150, 492550 },	// 10127 (721,573)
		{ PLAYERBOT_MAP_SUNGMA_SEOGANLAND, PLAYERBOT_MAP_SUNGMA_NAMGAN, 1212550, 557250 },	// 10129 (605,1220)
		{ PLAYERBOT_MAP_SUNGMA_NAMGAN, PLAYERBOT_MAP_SUNGMA_SEOGANLAND, 1280050, 440750 },	// 10130 (513,55)
		{ PLAYERBOT_MAP_SUNGMA_NAMGAN, PLAYERBOT_MAP_SUNGMA_YILAD, 1320950, 473550 },		// 10136 (921,383)
		{ PLAYERBOT_MAP_SUNGMA_YILAD, PLAYERBOT_MAP_SUNGMA_NAMGAN, 28850, 1414150 },		// 10137 (288,61)
		{ PLAYERBOT_MAP_SUNGMA_YILAD, PLAYERBOT_MAP_SUNGMA_WAWOZ, 4550, 1477050 },			// 10139 (45,690)
		{ PLAYERBOT_MAP_SUNGMA_WAWOZ, PLAYERBOT_MAP_SUNGMA_YILAD, 112350, 1600650 },		// 10140 (1125,902)
		{ PLAYERBOT_MAP_SUNGMA_WAWOZ, PLAYERBOT_MAP_SUNGMA_ROZPADLINA, 23550, 1537150 },	// 10142 (235,267)
		{ PLAYERBOT_MAP_SUNGMA_ROZPADLINA, PLAYERBOT_MAP_SUNGMA_WAWOZ, 185550, 1580950 },	// 10143 (575,705)
		{ PLAYERBOT_MAP_SUNGMA_SCHRONIENIE, PLAYERBOT_MAP_SUNGMA_ROZPADLINA, 1000350, 1267250 },	// 10201 (19,640)
		{ PLAYERBOT_MAP_SUNGMA_SCHRONIENIE, PLAYERBOT_MAP_SUNGMA_ZEJSCIE, 1134250, 1349950 },	// 10202 (1358,1467)
		{ PLAYERBOT_MAP_SUNGMA_ZEJSCIE, PLAYERBOT_MAP_SUNGMA_SCHRONIENIE, 1159050, 1219350 },	// 10203 (70,161)
	};

	// The numbers.
	const DWORD PLAYERBOT_SUNGMA_PICK_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_SETTLE_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_POINTS_MS = 30 * 1000;
	const DWORD PLAYERBOT_SUNGMA_PORTAL_WALK_MS = 4 * 60 * 1000;
	const int PLAYERBOT_SUNGMA_PORTAL_USE = 500;
	const DWORD PLAYERBOT_SUNGMA_CHAMBER_MS = 12 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_NOT_NOW_MS = 2 * 60 * 60 * 1000;
	const int PLAYERBOT_SUNGMA_DEATHS_STAY = 10;
	const DWORD PLAYERBOT_SUNGMA_HP_LOOK_MS = 10 * 1000;	// MT2009_PLUS_BOT_SUNGMA_DEATHS_V1
	// MT2009_PLUS_BOT_YOHARA_MAPS_V2 (the owner, 22 October evening: "dokoncz mapy" - the roads, Dongan's services, the
	// deaths on the higher maps):
	// The walk to a portal only from this near (a straight line, and the navigation joining the two); farther - the warp,
	// as a person takes a Teleporter. The portals onward stand at the far ends of the maps: the walk from the arrival is
	// 87 000 (Dongan -> Seoganland) to 355 500 units (Yilad -> Wawoz; Schronienie -> Zejscie 343 500) on the maps' grids,
	// past 20-144 spawn points - over PLAYERBOT_SUNGMA_PORTAL_WALK_MS at a bot's ~900 units a second, so every step up
	// from Yilad ended "portal walk too long" (the census's nav_fail: 14 in half an hour, 9 in the first 5 minutes of the
	// next run) and 24 of Yilad's 24 deaths, 26 of Dongan's 34 and 19 of Seoganland's 27 (18:40-18:47) came on such walks.
	// The portals back stand by the arrivals (600-6 100 units' walk) and are still walked to.
	const int PLAYERBOT_SUNGMA_PORTAL_WALK_NEAR = 12000;
	// The map judged (the Will, the band) only once the items are loaded and this long after the bot came onto it: a bot
	// just loaded read its glove's Will as 0 (Sila 0, Witalnosc without the glove's stone) and was sent down to the
	// Twierdza as "unfit" (ChybaTy, Champion 17, 0/10/18/20 on Wawoz; Parowapl, Champion 27, on Zejscie).
	const DWORD PLAYERBOT_SUNGMA_FIT_SETTLE_MS = 30 * 1000;
	// A step up (onto a map above the one it stands on, or the first map from home) only this many Champion levels over
	// the band's floor, with every requirement met - Inteligencja too; staying on a map asks the floor and Sila /
	// Witalnosc / Odpornosc as before. The owner's "step up only when the bot is some levels above the band floor AND
	// meets every requirement".
	const int PLAYERBOT_SUNGMA_STEP_UP_LEVELS = 2;
	// Dongan's services (the errand): a resident short of potions (under PLAYERBOT_SUNGMA_ERRAND_RED / _BLUE) or with no
	// free column of three and junk to sell goes to Dongan's merchants (373 is on this core: a warp, as a person's
	// Teleporter; walked from Dongan's own ground) - Handlarka Roznosci (9003: junk, potions to _FILL), Handlarz Bronia
	// (9001) and Handlarz Zbrojami (9002) for their junk - and goes back to its map. An errand over _MS, or a warp
	// refused, keeps the belt full where it stands (RestockPlayerBotYohara) for _FALLBACK_MS. Never home: Dongan is
	// game3's. (No repair: an item here does not wear.)
	const size_t PLAYERBOT_SUNGMA_ERRAND_RED = 60;
	const size_t PLAYERBOT_SUNGMA_ERRAND_BLUE = 60;
	const size_t PLAYERBOT_SUNGMA_ERRAND_FILL = 600;
	const size_t PLAYERBOT_SUNGMA_ERRAND_EMERGENCY = 15;	// fewer and no errand now (a fight): the fallback at once
	const DWORD PLAYERBOT_SUNGMA_ERRAND_LOOK_MS = 15 * 1000;
	const DWORD PLAYERBOT_SUNGMA_ERRAND_MS = 4 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_ERRAND_FALLBACK_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_ERRAND_BAG_MS = 20 * 60 * 1000;	// a bag errand at most this often (its junk may not free it)
	const int PLAYERBOT_SUNGMA_ERRAND_REACH = 350;
	// Dongan's merchants (npc.txt of metin2_map_eastplain_01, base 1049600,435200): 9003 (566,687), 9001 (484,677),
	// 9002 (484,727) - beside the arrival (1102450,506850), no spawn within 9 400 units of it.
	// MT2009_PLUS_BOT_YOHARA_TRADE_TRIP_V1 (the owner, 22 October: supplies in Dongan, "do M1 ida tylko handlowac"): a
	// resident goes home to its first village (game1, the handover) only to trade - its offline counter served with Yohara's
	// loot and valuables, the market's stands browsed for what it needs (the G0 package's dust, refine materials) - and is
	// handed over back to its map at once (no draw, no cooldown). Why (GetPlayerBotSungmaTradeReason), looked at every
	// _LOOK_MS out of a fight: "bag" - no free column of three, nothing for Dongan's merchants, _BAG_GOODS goods (from
	// _BAG_GAP_MS into the stay / after the last trip); "goods" - _GOODS lines a counter takes; "shop" - its counter gone,
	// run out or under _SHOP_LINES lines, with _SHOP_GOODS goods (both from _GOODS_GAP_MS); "buy" - the G0 dust or a refine
	// material wanted (from _BUY_GAP_MS); "routine" - every PLAYERBOT_SUNGMA_STAY_MIN (the stay's end, which sent a
	// non-member home before). At most PLAYERBOT_SUNGMA_TRADE_MAX bots of the channel away at once (game1's memory: a bot
	// at home holds no game3 room - its row is "home"). At home: _HOME_MIN_MS at least, its counter served (or
	// _HOME_SERVE_MS without), _HOME_MAX_MS at most; no room back for _STRANDED_MS more - an ordinary bot at home.
	const DWORD PLAYERBOT_SUNGMA_TRADE_LOOK_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_TRADE_BAG_GAP_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_TRADE_GOODS_GAP_MS = 60 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_TRADE_BUY_GAP_MS = 3 * 60 * 60 * 1000;
	const int PLAYERBOT_SUNGMA_TRADE_BAG_GOODS = 4;
	const int PLAYERBOT_SUNGMA_TRADE_GOODS = 12;
	const int PLAYERBOT_SUNGMA_TRADE_SHOP_GOODS = 4;
	const int PLAYERBOT_SUNGMA_TRADE_SHOP_LINES = 4;
	const DWORD PLAYERBOT_SUNGMA_TRADE_LOST_MS = 90 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_TRADE_HOME_MIN_MS = 3 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_TRADE_HOME_SERVE_MS = 8 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_TRADE_HOME_MAX_MS = 15 * 60 * 1000;
	const DWORD PLAYERBOT_SUNGMA_TRADE_STRANDED_MS = 30 * 60 * 1000;
	struct TPlayerBotSungmaMerchant { DWORD dwRace; long x, y; EPlayerBotMerchantCategory eCategory; const char* szTag; };
	const TPlayerBotSungmaMerchant PLAYERBOT_SUNGMA_DONGAN_MERCHANTS[] = {
		{ 9003, 1106200, 503900, BOT_MERCHANT_MISC, "dongan_misc" },
		{ 9001, 1098000, 502900, BOT_MERCHANT_WEAPON, "dongan_weapon" },
		{ 9002, 1098000, 507900, BOT_MERCHANT_ARMOR, "dongan_armor" },
	};
	const int PLAYERBOT_SUNGMA_DONGAN_MERCHANT_COUNT = 3;

	int GetPlayerBotSungmaSlot(long mapIndex)
	{
		const long base = mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? mapIndex / 10000 : mapIndex;
		for (int i = 0; i < PLAYERBOT_SUNGMA_MAP_COUNT; ++i)
			if (PLAYERBOT_SUNGMA_MAPS[i].lMap == base)
				return i;
		return -1;
	}

	// MT2009_PLUS_BOT_YOHARA_FIGHT_V1: the band's Champion floor of a map (0: not a Sung Ma map).
	int GetPlayerBotSungmaBandFloor(long mapIndex)
	{
		const int slot = GetPlayerBotSungmaSlot(mapIndex);
		return slot >= 0 ? (int)PLAYERBOT_SUNGMA_MAPS[slot].bChampionMin : 0;
	}

	// MT2009_PLUS_BOT_YOHARA_FIGHT_V1: a map's safe point (PLAYERBOT_SUNGMA_SAFE_POINTS) - the revival's and the retreat's.
	bool GetPlayerBotSungmaSafePoint(long mapIndex, long& x, long& y)
	{
		const long base = mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? mapIndex / 10000 : mapIndex;
		for (size_t i = 0; i < sizeof(PLAYERBOT_SUNGMA_SAFE_POINTS) / sizeof(PLAYERBOT_SUNGMA_SAFE_POINTS[0]); ++i)
			if (PLAYERBOT_SUNGMA_SAFE_POINTS[i].lMap == base)
			{
				x = PLAYERBOT_SUNGMA_SAFE_POINTS[i].x;
				y = PLAYERBOT_SUNGMA_SAFE_POINTS[i].y;
				return true;
			}
		return false;
	}

	bool IsPlayerBotSungmaMapOn(long mapIndex)
	{
		const std::vector<long>& maps = GetPlayerBotYoharaConfig().sungmaMaps;
		return GetPlayerBotSungmaSlot(mapIndex) >= 0 && std::find(maps.begin(), maps.end(), mapIndex) != maps.end();
	}

	// A requirement of a slot's map: 0 str, 1 hp, 2 move, 3 immune, 4 hit - the world's sungma_table.txt, else the copy.
	int GetPlayerBotSungmaReq(int slot, int what)
	{
		if (slot < 0 || slot >= PLAYERBOT_SUNGMA_MAP_COUNT || what < 0 || what > 4)
			return 0;
		const champion::SungmaRequirement* r = champion::MapRequirement(PLAYERBOT_SUNGMA_MAPS[slot].lMap);
		if (!r)
			return PLAYERBOT_SUNGMA_MAPS[slot].aiReq[what];
		switch (what)
		{
			case 0: return r->str;
			case 1: return r->hp;
			case 2: return r->move;
			case 3: return r->immune;
			default: return r->hit;
		}
	}

	int GetPlayerBotChampionLevel(LPCHARACTER ch)
	{
#ifdef ENABLE_CONQUEROR_LEVEL
		return ch ? (int)ch->GetConquerorLevel() : 0;
#else
		return 0;
#endif
	}

	// The bot's effective Will (points, items, the per cent bonuses): 0 Sila, 1 Witalnosc, 2 Odpornosc, 3 Inteligencja.
	int GetPlayerBotSungmaWill(LPCHARACTER ch, int what)
	{
#ifdef ENABLE_CONQUEROR_LEVEL
		static const BYTE s_aPoint[4] = { POINT_SUNGMA_STR, POINT_SUNGMA_HP, POINT_SUNGMA_MOVE, POINT_SUNGMA_IMMUNE };
		if (!ch || what < 0 || what >= 4)
			return 0;
		// MT2009_PLUS_SUNGMA_BONUS_V1 (dragon stones): a bot's deck is on only for a fight (playerbot_alchemy.h), so out of
		// one GetPoint lacks the Sung Ma lines of its worn stones (the Amethyst's) and the map choice / the points judged
		// the bot short of Will it has once it fights - counted here as the deck would add them (the first deck, the one
		// the bots switch on, stones with time left, a qualified bot).
		int iWill = yohara_gear::SungmaEffective(ch, s_aPoint[what]);
		if (ch->DragonSoul_GetActiveDeck() < 0 && ch->DragonSoul_IsQualified())
		{
			int iFlat = 0, iPct = 0;
			for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
			{
				LPITEM stone = GetPlayerBotWornDs(ch, kind);
				if (!stone || !HasPlayerBotDsTime(stone))
					continue;
				for (int a = 0; a < ITEM_ATTRIBUTE_MAX_NUM; ++a)
				{
					const WORD bType = stone->GetAttributeType(a); // MT2009_PLUS_WIDE_ATTR_V1
					if (bType == s_aPoint[what])
						iFlat += stone->GetAttributeValue(a);
					else if (bType == POINT_SUNGMA_PER_STR + what)
						iPct += stone->GetAttributeValue(a);
				}
			}
			if (iFlat || iPct)
			{
				const int iPctAll = MAX(-100, (int)ch->GetPoint(POINT_SUNGMA_PER_STR + what) + iPct);
				iWill = ((int)ch->GetPoint(s_aPoint[what]) + iFlat) * (100 + iPctAll) / 100;
			}
		}
		// MT2009_PLUS_BOT_YOHARA_SHOP_V1: dressed for the world, plus what its jade in the bag gives back (playerbot_yohara_shop.h)
		return iWill + GetPlayerBotYoharaWorldSetWillDelta(ch, what);
#else
		return 0;
#endif
	}

	// The Sila, Witalnosc and Odpornosc a map asks are there (Inteligencja is not asked - see the head).
	bool IsPlayerBotSungmaWillEnough(LPCHARACTER ch, int slot)
	{
		for (int i = 0; i < 3; ++i)
			if (GetPlayerBotSungmaWill(ch, i) < GetPlayerBotSungmaReq(slot, i))
				return false;
		return true;
	}

	// MT2009_PLUS_BOT_YOHARA_MAPS_V2: a step up onto a slot's map - PLAYERBOT_SUNGMA_STEP_UP_LEVELS over its floor and every
	// requirement met, Inteligencja too (see there).
	bool IsPlayerBotSungmaStepUpReady(LPCHARACTER ch, int slot, int champion)
	{
		if (champion < (int)PLAYERBOT_SUNGMA_MAPS[slot].bChampionMin + PLAYERBOT_SUNGMA_STEP_UP_LEVELS)
			return false;
		for (int i = 0; i < 4; ++i)
			if (GetPlayerBotSungmaWill(ch, i) < GetPlayerBotSungmaReq(slot, i))
				return false;
		return true;
	}

	// MT2009_PLUS_BOT_SUNGMA_NEST_V1: the bot's maximum health is enough for a slot's map (PLAYERBOT_SUNGMA_HP_FLOORS):
	// stay - the stay's share of the floor, else the whole floor.
	bool IsPlayerBotSungmaHpEnough(LPCHARACTER ch, int slot, bool stay)
	{
		if (!ch || slot < 0 || slot >= PLAYERBOT_SUNGMA_MAP_COUNT)
			return true;
		for (size_t i = 0; i < sizeof(PLAYERBOT_SUNGMA_HP_FLOORS) / sizeof(PLAYERBOT_SUNGMA_HP_FLOORS[0]); ++i)
			if (PLAYERBOT_SUNGMA_HP_FLOORS[i].lMap == PLAYERBOT_SUNGMA_MAPS[slot].lMap)
			{
				const long long need = (long long)PLAYERBOT_SUNGMA_HP_FLOORS[i].iMaxHp * (stay ? PLAYERBOT_SUNGMA_HP_STAY_PERCENT : 100) / 100;
				return (long long)ch->GetMaxHP() >= need;
			}
		return true;
	}

	// ------------------------------------------------------------ the state

	struct TPlayerBotSungmaBot
	{
		DWORD dwNextPoints, dwNextPick, dwOnMapSince, dwWalkSince, dwChamberSince;
		long lMapSeen;
		std::map<long, DWORD> mapNotNow;	// a map stepped down from after its deaths: until
		// the poll's last look (the census's experience and the level-ups)
		bool bSeen, bStuck;
		int iLastLevel, iLastChampion;
		DWORD dwLastExp, dwLastNeed, dwLastChampionExp;
		bool bFlee;			// MT2009_PLUS_BOT_SUNGMA_DEATHS_V1: stepped down after its deaths - the next move warps
		DWORD dwNextHpLook;	// MT2009_PLUS_BOT_SUNGMA_DEATHS_V1: the maximum health's look (TrackPlayerBotSungma)
		// MT2009_PLUS_BOT_YOHARA_MAPS_V2: Dongan's errand - on it (bErrand), its next merchant, since when, what for
		// (1 potions, 2 the bag), the fallback's end, the next look, the last bag errand.
		bool bErrand;
		int iErrandStop, iErrandNeed;
		DWORD dwErrandSince, dwErrandFallbackUntil, dwNextErrandLook, dwLastBagErrand;
		DWORD dwNextTradeLook;	// MT2009_PLUS_BOT_YOHARA_TRADE_TRIP_V1: the trade trip's next look
		DWORD dwErrandBackSince;	// MT2009_PLUS_BOT_SUNGMA_PARTY_KEEP_V1: on the way back from an errand since (0: not)
		TPlayerBotSungmaBot() : dwNextPoints(0), dwNextPick(0), dwOnMapSince(0), dwWalkSince(0), dwChamberSince(0), lMapSeen(0),
			bSeen(false), bStuck(false), iLastLevel(0), iLastChampion(0), dwLastExp(0), dwLastNeed(0), dwLastChampionExp(0),
			bFlee(false), dwNextHpLook(0), bErrand(false), iErrandStop(0), iErrandNeed(0), dwErrandSince(0),
			dwErrandFallbackUntil(0), dwNextErrandLook(0), dwLastBagErrand(0), dwNextTradeLook(0), dwErrandBackSince(0) {}
	};
	std::map<DWORD, TPlayerBotSungmaBot> s_mapPlayerBotSungma;
#ifdef MT2009_PLUS_BOT_YOHARA_GUIDES_V1
	// MT2009_PLUS_BOT_YOHARA_GUIDES_V1 (playerbot_yohara_guides.h, after playerbot_ishop3_goals.h): the Sung Ma buffs, the
	// boosters and the Loch's excursion (-2: the resident's own flow goes on), the leaders' boss route, the kills' memory,
	// the Loch's gate and the census.
	int ManagePlayerBotYoharaGuides(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotYoharaResident& res,
			TPlayerBotSungmaBot& b, long base, DWORD dwNow);
	int ManagePlayerBotYoharaBossRoute(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow);
	void NotePlayerBotYoharaGuidesKill(LPCHARACTER killer, LPCHARACTER victim);
	bool IsPlayerBotYoharaLochEntry(LPCHARACTER ch, long base);
	void LogPlayerBotYoharaGuidesCensus(DWORD dwNow);
#endif

	// MT2009_PLUS_BOT_YOHARA_FIGHT_V1: what a resident does beside the hunt - 1 the walk to a portal, 2 Dongan's errand
	// (a death's cause, NotePlayerBotSungmaFallen).
	int GetPlayerBotSungmaActivity(DWORD pid)
	{
		std::map<DWORD, TPlayerBotSungmaBot>::const_iterator b = s_mapPlayerBotSungma.find(pid);
		if (b == s_mapPlayerBotSungma.end())
			return 0;
		return b->second.bErrand ? 2 : (b->second.dwWalkSince != 0 ? 1 : 0);
	}
	// MT2009_PLUS_BOT_SUNGMA_PARTY_KEEP_V1 (the owner, 31 October 2026 - BOTY-YOHARA-ANALIZA-v2.md, Etap 3: "boty maja sie
	// trzymac druzyny"): 12 756 of the day's party leaves were Dongan's errand (`party leave why=errand`, 30-31 October),
	// nearly every errand took its bot out of its party (party_errand_leaves 14 061 since the start), and an errand is
	// short - 12 s a median from the warp out to "errand done". 53% of the deaths were of bots in a party with fewer than
	// two of it by them. So the errand keeps the party: the bot warps to Dongan and back as a member (or its leader - the
	// members wait for it, playerbot_yohara_sungma_party.h), while the errand lasts (PLAYERBOT_SUNGMA_ERRAND_MS at most)
	// and on its way back for PLAYERBOT_SUNGMA_ERRAND_BACK_MS. The bag's errand (32% of them) is tidied in place for a
	// party's member instead (ManagePlayerBotSungmaErrand).
	const DWORD PLAYERBOT_SUNGMA_ERRAND_BACK_MS = 90 * 1000;
	bool IsPlayerBotSungmaErrandKeepingParty(DWORD pid, DWORD dwNow)
	{
		std::map<DWORD, TPlayerBotSungmaBot>::const_iterator b = s_mapPlayerBotSungma.find(pid);
		if (b == s_mapPlayerBotSungma.end())
			return false;
		if (b->second.bErrand)
			return dwNow - b->second.dwErrandSince < PLAYERBOT_SUNGMA_ERRAND_MS + 15 * 1000;
		return b->second.dwErrandBackSince != 0 && dwNow - b->second.dwErrandBackSince < PLAYERBOT_SUNGMA_ERRAND_BACK_MS;
	}
	// MT2009_PLUS_BOT_YOHARA_FIGHT_V1: the party's leader waits for its members (playerbot_yohara_sungma_party.h).
	bool HoldPlayerBotSungmaRegroup(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow);
	// MT2009_PLUS_BOT_YOHARA_TRADE_TRIP_V1: game3's trips out (the map to come back to), the last trip of a bot (kept over
	// its stays), and the home core's bots on the errand.
	struct TPlayerBotSungmaTradeOut
	{
		DWORD dwAt;
		long lMap;
		TPlayerBotSungmaTradeOut() : dwAt(0), lMap(0) {}
	};
	struct TPlayerBotSungmaTradeHome
	{
		long lBackMap;
		DWORD dwSince;
		bool bNudged;
		long long llGold;
		char szWhy[16];
		TPlayerBotSungmaTradeHome() : lBackMap(0), dwSince(0), bNudged(false), llGold(0) { szWhy[0] = '\0'; }
	};
	std::map<DWORD, TPlayerBotSungmaTradeOut> s_mapPlayerBotSungmaTradeOut;
	std::map<DWORD, DWORD> s_mapPlayerBotSungmaTradeLast;
	std::map<DWORD, TPlayerBotSungmaTradeHome> s_mapPlayerBotSungmaTradeHome;
	unsigned int s_uPlayerBotSungmaTradeHomeArrived = 0, s_uPlayerBotSungmaTradeHomeBack = 0, s_uPlayerBotSungmaTradeStranded = 0;

	struct TPlayerBotSungmaStats
	{
		unsigned int kills, killsAtCensus, deaths, stuck, navFail, levelUps, championUps, movesIn, movesOut, stepsDown, hops;
		long long exp, expAtCensus, championExp, championExpAtCensus;
		// MT2009_PLUS_BOT_YOHARA_MAPS_V2: the walks to a portal, the warps instead of one, the revivals at the arrival,
		// Dongan's errands from this map and their fallbacks
		unsigned int portalWalks, portalWarps, revives, errands, errandFallbacks;
		unsigned int tradeTrips, tradeBacks;	// MT2009_PLUS_BOT_YOHARA_TRADE_TRIP_V1: trips home from this map, landings back on it
		TPlayerBotSungmaStats() : kills(0), killsAtCensus(0), deaths(0), stuck(0), navFail(0), levelUps(0), championUps(0),
			movesIn(0), movesOut(0), stepsDown(0), hops(0), exp(0), expAtCensus(0), championExp(0), championExpAtCensus(0),
			portalWalks(0), portalWarps(0), revives(0), errands(0), errandFallbacks(0), tradeTrips(0), tradeBacks(0) {}
	};
	TPlayerBotSungmaStats s_aPlayerBotSungmaStats[9];
	static_assert(sizeof(s_aPlayerBotSungmaStats) / sizeof(s_aPlayerBotSungmaStats[0]) ==
			sizeof(PLAYERBOT_SUNGMA_MAPS) / sizeof(PLAYERBOT_SUNGMA_MAPS[0]), "a census slot a map");
	// The channel's rows a map, the last poll's (on their way or staying) - the maps' room.
	int s_aiPlayerBotSungmaMapCensus[9] = { 0 };
	DWORD s_dwPlayerBotSungmaLastCensus = 0;

	// MT2009_PLUS_BOT_TRAINER_MAP_PICK_V1 - the map by the champion experience it gives, measured (the night's trainer,
	// 3/4 November: in six hours of 3 November a bot earned 59 700 champion experience an hour on Twierdza, 37 900 on
	// Dongan, 29 000 on Seoganland, 32 600 on Namgan, 18 700 on Yilad, 18 600 on Wawoz, 45 200 on Rozpadlina, 2 000 on
	// Schronienie and 84 000 on Zejscie - the highest map a bot may take is not the best one: a Champion of 25 on
	// Schronienie earned a twentieth of what Rozpadlina would have given it). The census keeps a map's champion
	// experience and its bots' time over the last PLAYERBOT_SUNGMA_RATE_SLOTS censuses (five minutes each); the pick
	// takes, of the maps the bot may stand on (every rule of the pick as before), a lower one only when it gives at least
	// PLAYERBOT_SUNGMA_RATE_BETTER_PCT of the highest one's rate, both measured over PLAYERBOT_SUNGMA_RATE_MIN_BH bot-hours,
	// and the lower one's band reaches the bot's Champion level within PLAYERBOT_SUNGMA_RATE_BAND_SLACK (at most
	// PLAYERBOT_SUNGMA_RATE_MAX_DOWN maps under the default; the Twierdza only within its own band). The map it stands
	// on is held a further PLAYERBOT_SUNGMA_RATE_STAY_PCT (no flapping). A cold core (after a restart) starts from the
	// rates above (PLAYERBOT_SUNGMA_RATE_SEED, a weight of PLAYERBOT_SUNGMA_RATE_SEED_BH bot-hours). The champion's tempo
	// is untouched (no rate, no table): only where the bot spends its hour. Event flag m2_bot_map_rate_off: the old pick.
	const int PLAYERBOT_SUNGMA_RATE_SLOTS = 36;	// three hours of censuses
	const double PLAYERBOT_SUNGMA_RATE_MIN_BH = 2.0;
	const int PLAYERBOT_SUNGMA_RATE_BETTER_PCT = 140;
	const int PLAYERBOT_SUNGMA_RATE_STAY_PCT = 115;
	const int PLAYERBOT_SUNGMA_RATE_BAND_SLACK = 3;
	const int PLAYERBOT_SUNGMA_RATE_MAX_DOWN = 2;
	const double PLAYERBOT_SUNGMA_RATE_SEED_BH = 4.0;
	const long long PLAYERBOT_SUNGMA_RATE_SEED[9] = { 59700, 37900, 29000, 32600, 18700, 18600, 45200, 2000, 84000 };
	struct TPlayerBotSungmaRate
	{
		long long exp[PLAYERBOT_SUNGMA_RATE_SLOTS];
		long long botMs[PLAYERBOT_SUNGMA_RATE_SLOTS];
		int pos;
		unsigned int picksDown, picksHeld;
		TPlayerBotSungmaRate() : pos(0), picksDown(0), picksHeld(0)
		{
			memset(exp, 0, sizeof(exp));
			memset(botMs, 0, sizeof(botMs));
		}
	};
	TPlayerBotSungmaRate s_aPlayerBotSungmaRate[9];

	bool IsPlayerBotSungmaRateOff()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_bot_map_rate_off") != 0;
	}

	void NotePlayerBotSungmaRate(int slot, long long championExp, long long botMs)
	{
		if (slot < 0 || slot >= 9 || botMs < 0)
			return;
		TPlayerBotSungmaRate& r = s_aPlayerBotSungmaRate[slot];
		r.exp[r.pos] = std::max<long long>(0, championExp);
		r.botMs[r.pos] = botMs;
		r.pos = (r.pos + 1) % PLAYERBOT_SUNGMA_RATE_SLOTS;
	}

	// The map's champion experience a bot-hour (the seed's weight on top of the window's); botHours the window's own.
	long long GetPlayerBotSungmaRate(int slot, double* botHours)
	{
		if (slot < 0 || slot >= 9)
			return 0;
		const TPlayerBotSungmaRate& r = s_aPlayerBotSungmaRate[slot];
		long long exp = 0, ms = 0;
		for (int i = 0; i < PLAYERBOT_SUNGMA_RATE_SLOTS; ++i)
		{
			exp += r.exp[i];
			ms += r.botMs[i];
		}
		const double bh = (double)ms / 3600000.0;
		if (botHours)
			*botHours = bh;
		const double seedExp = (double)PLAYERBOT_SUNGMA_RATE_SEED[slot] * PLAYERBOT_SUNGMA_RATE_SEED_BH;
		return (long long)(((double)exp + seedExp) / (bh + PLAYERBOT_SUNGMA_RATE_SEED_BH));
	}

	// ------------------------------------------------------------ the pick

	bool HasPlayerBotSungmaRoom(int slot, long currentMap)
	{
		if (PLAYERBOT_SUNGMA_MAPS[slot].lMap == currentMap)
			return true;
		return s_aiPlayerBotSungmaMapCensus[slot] < GetPlayerBotYoharaConfig().sungmaMapMax;
	}

	// The bot's map now (0: none switched on). currentMap: the map it stays on (its room is its own).
	// MT2009_PLUS_BOT_SUNGMA_NEST_V1: judgeHp - its maximum health is the one it fights with (not at the Alchemist, whose
	// visit takes the dragon stones off; not just loaded).
	long PickPlayerBotSungmaMap(LPCHARACTER ch, long currentMap, bool judgeHp = true)
	{
		if (!ch)
			return 0;
		const int champion = GetPlayerBotChampionLevel(ch);
		if (champion < 1)
			return 0;
		const DWORD dwNow = get_dword_time();
		std::map<DWORD, TPlayerBotSungmaBot>::const_iterator b = s_mapPlayerBotSungma.find(ch->GetPlayerID());
		// MT2009_PLUS_BOT_YOHARA_MAPS_V2: a map above the one it stands on (any map, from home) is a step up
		const int currentSlot = currentMap ? GetPlayerBotSungmaSlot(currentMap) : -1;
		long lowest = 0;
		int defaultSlot = -1, bestSlot = -1;	// MT2009_PLUS_BOT_TRAINER_MAP_PICK_V1
		long long bestRate = 0;
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V3: a lower map of another element is no pick (the element changes only up the
		// maps); with nothing else that fits, the bot stays where it is - or, from home, the lowest map it may take.
		long lowestAllowed = 0;
		bool skipped = false;
#endif
		for (int i = PLAYERBOT_SUNGMA_MAP_COUNT - 1; i >= 0; --i)
		{
			const TPlayerBotSungmaMap& m = PLAYERBOT_SUNGMA_MAPS[i];
			if (!IsPlayerBotSungmaMapOn(m.lMap))
				continue;
			lowest = m.lMap;
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
			if (!IsPlayerBotSungmaElementMoveAllowed(ch, m.lMap, false))
			{
				skipped = true;
				continue;
			}
			lowestAllowed = m.lMap;
#endif
			if (champion < (int)m.bChampionMin || !IsPlayerBotSungmaWillEnough(ch, i) || !HasPlayerBotSungmaRoom(i, currentMap))
				continue;
			if (i > currentSlot && !IsPlayerBotSungmaStepUpReady(ch, i, champion))
				continue;
			// MT2009_PLUS_BOT_SUNGMA_NEST_V1: its health (the items in: a bot just loaded is judged later, by the caller)
			if (judgeHp && ch->IsItemLoaded() && !IsPlayerBotSungmaHpEnough(ch, i, i <= currentSlot))
			{
				if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(m.lMap))
					++st->hpRefused;
				continue;
			}
			if (b != s_mapPlayerBotSungma.end())
			{
				std::map<long, DWORD>::const_iterator nn = b->second.mapNotNow.find(m.lMap);
				if (nn != b->second.mapNotNow.end() && (int)(nn->second - dwNow) > 0)
					continue;
			}
			// MT2009_PLUS_BOT_TRAINER_MAP_PICK_V1: the highest map that fits is the default; a lower one that fits too
			// and gives clearly more champion experience a bot-hour (measured) is taken instead
			if (defaultSlot < 0)
			{
				defaultSlot = i;
				if (IsPlayerBotSungmaRateOff())
					return m.lMap;
				continue;
			}
			// at most PLAYERBOT_SUNGMA_RATE_MAX_DOWN maps under the default, within the band's slack - the first map
			// (the Twierdza, the beginners') only within its own band
			if (i < defaultSlot - PLAYERBOT_SUNGMA_RATE_MAX_DOWN ||
					champion > (int)m.bChampionMax + (i == 0 ? 0 : PLAYERBOT_SUNGMA_RATE_BAND_SLACK))
				continue;
			double bh = 0.0;
			long long rate = GetPlayerBotSungmaRate(i, &bh);
			if (i == currentSlot)
				rate = rate * PLAYERBOT_SUNGMA_RATE_STAY_PCT / 100;
			if (rate > bestRate)
			{
				bestRate = rate;
				bestSlot = i;
			}
		}
		if (defaultSlot >= 0)
		{
			double bhDefault = 0.0;
			long long rateDefault = GetPlayerBotSungmaRate(defaultSlot, &bhDefault);
			if (defaultSlot == currentSlot)
				rateDefault = rateDefault * PLAYERBOT_SUNGMA_RATE_STAY_PCT / 100;
			if (bestSlot >= 0 && bestRate * 100 >= rateDefault * PLAYERBOT_SUNGMA_RATE_BETTER_PCT)
			{
				// the highest map's own measure is what is being overruled: only with its window's bot-hours (an
				// emptied map goes back to its default bots once its window runs dry - the pick looks at it again)
				if (bhDefault >= PLAYERBOT_SUNGMA_RATE_MIN_BH)
				{
					if (bestSlot == currentSlot)
						++s_aPlayerBotSungmaRate[bestSlot].picksHeld;
					else
					{
						++s_aPlayerBotSungmaRate[bestSlot].picksDown;
						PlayerBotLogThrottled("sungma_rate_pick", dwNow,
								"PLAYERBOT_SUNGMA: pick by rate pid=%u name=%s champion=%d default=%ld (%lld) pick=%ld (%lld) current=%ld",
								ch->GetPlayerID(), ch->GetName(), champion, PLAYERBOT_SUNGMA_MAPS[defaultSlot].lMap, rateDefault,
								PLAYERBOT_SUNGMA_MAPS[bestSlot].lMap, bestRate, currentMap);
					}
					return PLAYERBOT_SUNGMA_MAPS[bestSlot].lMap;
				}
			}
			return PLAYERBOT_SUNGMA_MAPS[defaultSlot].lMap;
		}
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
		if (skipped)
		{
			IsPlayerBotSungmaElementMoveAllowed(ch, 0, true);	// the census's count of a pick held by the element
#ifdef MT2009_PLUS_BOT_G0_DUST_RULE_V1
			// MT2009_PLUS_BOT_G0_DUST_RULE_V1: the maps above (its own too) did not fit and the one below is another
			// element's - a step down refused for want of the second set
			NotePlayerBotG0DownBlocked(ch, "pick");
#endif
			if (currentSlot >= 0 && IsPlayerBotSungmaMapOn(currentMap))
				return currentMap;
			if (lowestAllowed != 0)
				return lowestAllowed;
		}
#endif
		return lowest;
	}

	// An offline member's map by its Champion level alone (the dispatcher: its gear is not loaded; the cohort tool gave
	// it the Will of the band's map, and its stay corrects the rest).
	long PickPlayerBotSungmaMapByBand(int champion)
	{
		if (champion < 1)
			return 0;
		long lowest = 0;
		for (int i = PLAYERBOT_SUNGMA_MAP_COUNT - 1; i >= 0; --i)
		{
			const TPlayerBotSungmaMap& m = PLAYERBOT_SUNGMA_MAPS[i];
			if (!IsPlayerBotSungmaMapOn(m.lMap))
				continue;
			lowest = m.lMap;
			// MT2009_PLUS_BOT_YOHARA_MAPS_V2: from home every map is a step up (its Will is read there, on the map)
			if (champion >= (int)m.bChampionMin + PLAYERBOT_SUNGMA_STEP_UP_LEVELS && HasPlayerBotSungmaRoom(i, 0))
				return m.lMap;
		}
		return lowest;
	}

	// A bot of the home core whose life is the Sung Ma maps now: a Champion of the top level, eligible, the switch on.
	bool IsPlayerBotSungmaCandidate(LPCHARACTER ch)
	{
		return ch && GetPlayerBotChampionLevel(ch) >= 1 && (int)ch->GetLevel() >= gPlayerMaxLevel &&
				GetPlayerBotYoharaConfig().sungmaMax > 0 && !GetPlayerBotYoharaConfig().sungmaMaps.empty();
	}

	// TransitionPlayerBotMap's gate (playerbot_travel.h).
	bool IsPlayerBotSungmaEntryAllowed(LPCHARACTER ch, long targetMap, const char* reason)
	{
		if (!ch || GetPlayerBotChampionLevel(ch) < 1 || (int)ch->GetLevel() < gPlayerMaxLevel)
			return false;
		const long base = targetMap >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? targetMap / 10000 : targetMap;
		if (IsPlayerBotSungmaMapOn(base))
			return true;
		// MT2009_PLUS_BOT_GLEBIE_V1: a bots' dungeon run on a Sung Ma map (Glebie 395 and its gathering in Zejscie 394) -
		// to the gathering, into the run's instance, out again.
		if (IsPlayerBotDungeonRunMove(ch, targetMap, reason))
			return true;
#ifdef MT2009_PLUS_BOT_YOHARA_GUIDES_V1
		if (IsPlayerBotYoharaLochEntry(ch, base))	// MT2009_PLUS_BOT_YOHARA_GUIDES_V1: the Loch, by its altar and ticket
			return true;
#endif
		// a person of its party took it along (a dungeon's jump, the follow)
		return IsPlayerBotDungeonPartyMove(ch, targetMap, reason);
	}

	// ------------------------------------------------------------ the Sung Ma points

	// A free point on the stat the bot's next map lacks most (plan 5.3): the lowest map of the table whose Sila /
	// Witalnosc / Odpornosc the bot does not meet; all three met everywhere - Inteligencja to the top map's; then the
	// lowest of the four. Nothing to spend with no point, or every stat at the top (90).
	// MT2009_PLUS_SUNGMA_BONUS_V1: the Will above a map's requirement is worth something now (playerbot_champion.cpp: Sila
	// +0.01% damage, Witalnosc +5.33 max HP a point, Odpornosc / Inteligencja every 100). The maps are met in order up to
	// the next one the bot cannot step onto yet (bChampionMin + PLAYERBOT_SUNGMA_STEP_UP_LEVELS over its Champion level) -
	// the map-reaching as before; then Witalnosc up to the top map's requirement (the survival bonus where it fights, and
	// never a lost point: every later map asks that Witalnosc too); then the further maps as before, Inteligencja of the
	// top map, Witalnosc to the cap (90), the lowest of the four.
	int GetPlayerBotSungmaGapStat(LPCHARACTER ch, int slot)
	{
		int best = -1, bestGap = 0;
		static const int order[4] = { 0, 2, 1, 3 };
		for (int k = 0; k < 4; ++k)
		{
			const int i = order[k];
			const int gap = GetPlayerBotSungmaReq(slot, i) - GetPlayerBotSungmaWill(ch, i);
			if (gap > bestGap)
			{
				best = i;
				bestGap = gap;
			}
		}
		return best;
	}

	int ChoosePlayerBotDropkiSungmaStat(LPCHARACTER ch);	// MT2009_PLUS_BOT_DROPKI_V1 (playerbot_dropki.h)

	int ChoosePlayerBotSungmaStat(LPCHARACTER ch)
	{
		// MT2009_PLUS_BOT_DROPKI_V1: a Dropki's points go to its dungeon's Sung Ma ask first
		{
			const int dropki = ChoosePlayerBotDropkiSungmaStat(ch);
			if (dropki >= 0)
				return dropki;
		}
		{
			const int champion = GetPlayerBotChampionLevel(ch);
			int horizon = PLAYERBOT_SUNGMA_MAP_COUNT - 1;
			for (int slot = 0; slot < PLAYERBOT_SUNGMA_MAP_COUNT; ++slot)
				if (champion < (int)PLAYERBOT_SUNGMA_MAPS[slot].bChampionMin + PLAYERBOT_SUNGMA_STEP_UP_LEVELS)
				{
					horizon = slot;
					break;
				}
			for (int slot = 0; slot <= horizon; ++slot)
			{
				const int best = GetPlayerBotSungmaGapStat(ch, slot);
				if (best >= 0)
					return best;
			}
#ifdef ENABLE_CONQUEROR_LEVEL
			if (GetPlayerBotSungmaWill(ch, 1) < GetPlayerBotSungmaReq(PLAYERBOT_SUNGMA_MAP_COUNT - 1, 1) &&
					ch->GetRealPoint(POINT_SUNGMA_HP) < (int)champion::STAT_MAX)
				return 1;
#endif
		}
		for (int slot = 0; slot < PLAYERBOT_SUNGMA_MAP_COUNT; ++slot)
		{
			int best = -1, bestGap = 0;
			// Sila first on a tie (its penalty halves the damage), then Odpornosc (the speed), then Witalnosc;
			// MT2009_PLUS_BOT_YOHARA_MAPS_V2: then Inteligencja - a step up asks it too (IsPlayerBotSungmaStepUpReady)
			static const int order[4] = { 0, 2, 1, 3 };
			for (int k = 0; k < 4; ++k)
			{
				const int i = order[k];
				const int gap = GetPlayerBotSungmaReq(slot, i) - GetPlayerBotSungmaWill(ch, i);
				if (gap > bestGap)
				{
					best = i;
					bestGap = gap;
				}
			}
			if (best >= 0)
				return best;
		}
		if (GetPlayerBotSungmaWill(ch, 3) < GetPlayerBotSungmaReq(PLAYERBOT_SUNGMA_MAP_COUNT - 1, 3))
			return 3;
		int low = -1;
#ifdef ENABLE_CONQUEROR_LEVEL
		// MT2009_PLUS_SUNGMA_BONUS_V1: every map met - Witalnosc to the cap first (+5.33 max HP a point above).
		if (ch->GetRealPoint(POINT_SUNGMA_HP) < (int)champion::STAT_MAX)
			return 1;
		static const BYTE s_aPoint[4] = { POINT_SUNGMA_STR, POINT_SUNGMA_HP, POINT_SUNGMA_MOVE, POINT_SUNGMA_IMMUNE };
		for (int i = 0; i < 4; ++i)
			if (ch->GetRealPoint(s_aPoint[i]) < (int)champion::STAT_MAX &&
					(low < 0 || ch->GetRealPoint(s_aPoint[i]) < ch->GetRealPoint(s_aPoint[low])))
				low = i;
#endif
		return low;
	}

	void SpendPlayerBotSungmaPoints(LPCHARACTER ch, TPlayerBotSungmaBot& b, DWORD dwNow)
	{
#ifdef ENABLE_CONQUEROR_LEVEL
		if ((int)(dwNow - b.dwNextPoints) < 0 || !ch || ch->GetConquerorLevel() < 1 || ch->GetConquerorPoint() <= 0)
			return;
		b.dwNextPoints = dwNow + PLAYERBOT_SUNGMA_POINTS_MS;
		static const char* const s_aName[4] = { "str", "hp", "move", "immune" };
		int spent[4] = { 0, 0, 0, 0 };
		for (int n = 0; n < 90 && ch->GetConquerorPoint() > 0; ++n)
		{
			const int stat = ChoosePlayerBotSungmaStat(ch);
			if (stat < 0 || !champion::SpendPoint(ch, stat))
				break;
			++spent[stat];
		}
		if (spent[0] + spent[1] + spent[2] + spent[3] > 0)
			sys_log(0, "PLAYERBOT_SUNGMA: points pid=%u name=%s champion=%d spent %s+%d %s+%d %s+%d %s+%d left=%d will=%d/%d/%d/%d map=%ld",
					ch->GetPlayerID(), ch->GetName(), (int)ch->GetConquerorLevel(), s_aName[0], spent[0], s_aName[1], spent[1],
					s_aName[2], spent[2], s_aName[3], spent[3], ch->GetConquerorPoint(), GetPlayerBotSungmaWill(ch, 0),
					GetPlayerBotSungmaWill(ch, 1), GetPlayerBotSungmaWill(ch, 2), GetPlayerBotSungmaWill(ch, 3), ch->GetMapIndex());
#else
		(void)ch; (void)b; (void)dwNow;
#endif
	}

	// ------------------------------------------------------------ the stones and the kills

	int IsPlayerBotSungmaStoneForMe(LPCHARACTER ch, LPCHARACTER stone)
	{
		if (!ch || !stone || !stone->IsStone())
			return -1;
		const int slot = GetPlayerBotSungmaSlot(ch->GetMapIndex());
		if (slot < 0)
			return -1;
		// MT2009_PLUS_BOT_SUNGMA_DEATHS_V1: a party of three only. A Sung Ma map's stone - the outposts (Posterunek Trolli /
		// Myr 8625-8627, 0.58-0.9 M health; 25 on Dongan, 23 on Seoganland, 19 on Namgan) and the Metins (1.9-2.5 M) -
		// calls 22 groups of its map's monsters (char_state.cpp __StateIdle_Stone: 1+1+2+2+2+2+3+3+3+3 at 99..10%, four or
		// five monsters of 87-147 k health a group, berserk, archers and shamans among them) onto whoever hits it. The
		// first test (22 October, 12:37-12:55, game3 ch1) let a bot three Champion levels into its band take one alone:
		// the bots stepped down from Seoganland / Namgan (Champion 6-11) were exactly those on Dongan and Seoganland, and
		// 51 of Dongan's 73 deaths and 34 of Seoganland's 53 came within 25 m of an outpost - one bot died 17 times at one
		// (killed at last by another, log.log STONE_KILL 8625 at its spot), revived where it lay and went back to the stone,
		// whose fight kept the travel pass (the deaths' step down) away. The higher maps have 0-6 stones each - hence
		// "the lower maps are deadlier".
		// MT2009_PLUS_BOT_YOHARA_FIGHT_V1: three of the party BY the bot (PLAYERBOT_SUNGMA_PARTY_NEAR, alive), not three on
		// the party's list - a leader whose members were still walking up, or had gone on an errand, took it alone.
		return CountPlayerBotSungmaPartyNear(ch, PLAYERBOT_SUNGMA_PARTY_NEAR) >= PLAYERBOT_SUNGMA_PARTY_MIN ? 1 : 0;
	}

	void NotePlayerBotSungmaKill(LPCHARACTER killer, LPCHARACTER victim)
	{
		if (!killer || !victim || victim->IsPC() || !killer->IsPC() || !killer->GetDesc() || !killer->GetDesc()->IsBot())
			return;
#ifdef MT2009_PLUS_BOT_YOHARA_GUIDES_V1
		NotePlayerBotYoharaGuidesKill(killer, victim);	// the bosses' memory, the boosters' kill rate
#endif
		const int slot = GetPlayerBotSungmaSlot(killer->GetMapIndex());
		if (slot >= 0)
		{
			++s_aPlayerBotSungmaStats[slot].kills;
#ifdef MT2009_PLUS_BOT_G0_DUST_RULE_V1
			NotePlayerBotG0StruggleKill(killer);	// MT2009_PLUS_BOT_G0_DUST_RULE_V1: the bot's own window
#endif
		}
	}

	void NotePlayerBotSungmaDeath(LPCHARACTER ch)
	{
		const int slot = ch ? GetPlayerBotSungmaSlot(ch->GetMapIndex()) : -1;
		if (slot >= 0)
		{
			++s_aPlayerBotSungmaStats[slot].deaths;
#ifdef MT2009_PLUS_BOT_G0_DUST_RULE_V1
			NotePlayerBotG0StruggleDeath(ch);	// MT2009_PLUS_BOT_G0_DUST_RULE_V1: the bot's own window
#endif
		}
	}

	// ------------------------------------------------------------ the poll's look at a resident

	// Its experience, champion experience and level-ups since the poll before, and whether it stands stuck.
	void TrackPlayerBotSungma(LPCHARACTER ch)
	{
		if (!ch)
			return;
		const int slot = GetPlayerBotSungmaSlot(ch->GetMapIndex());
		if (slot < 0)
			return;
		TPlayerBotSungmaBot& b = s_mapPlayerBotSungma[ch->GetPlayerID()];
		TPlayerBotSungmaStats& st = s_aPlayerBotSungmaStats[slot];
		const int level = ch->GetLevel();
		const DWORD exp = ch->GetExp();
		const int champion = GetPlayerBotChampionLevel(ch);
#ifdef ENABLE_CONQUEROR_LEVEL
		const DWORD championExp = ch->GetConquerorExp();
#else
		const DWORD championExp = 0;
#endif
		if (b.bSeen)
		{
			if (level == b.iLastLevel)
				st.exp += exp > b.dwLastExp ? (long long)(exp - b.dwLastExp) : 0;
			else if (level > b.iLastLevel)
			{
				st.exp += (b.dwLastNeed > b.dwLastExp ? (long long)(b.dwLastNeed - b.dwLastExp) : 0) + (long long)exp;
				st.levelUps += (unsigned int)(level - b.iLastLevel);
			}
			if (champion == b.iLastChampion)
				st.championExp += championExp > b.dwLastChampionExp ? (long long)(championExp - b.dwLastChampionExp) : 0;
			else if (champion > b.iLastChampion)
			{
				long long gained = (long long)championExp;
				for (int l = b.iLastChampion; l < champion; ++l)
					gained += (long long)champion::NextExp(l) - (l == b.iLastChampion ? (long long)b.dwLastChampionExp : 0);
				st.championExp += std::max(0LL, gained);
				st.championUps += (unsigned int)(champion - b.iLastChampion);
				sys_log(0, "PLAYERBOT_SUNGMA: champion level up pid=%u name=%s champion=%d->%d map=%ld will=%d/%d/%d/%d",
						ch->GetPlayerID(), ch->GetName(), b.iLastChampion, champion, ch->GetMapIndex(), GetPlayerBotSungmaWill(ch, 0),
						GetPlayerBotSungmaWill(ch, 1), GetPlayerBotSungmaWill(ch, 2), GetPlayerBotSungmaWill(ch, 3));
			}
		}
		b.bSeen = true;
		b.iLastLevel = level;
		b.dwLastExp = exp;
		b.dwLastNeed = ch->GetNextExp();
		b.iLastChampion = champion;
		b.dwLastChampionExp = championExp;
		TPlayerBotAIStateMap::const_iterator s = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		const bool stuck = s != s_mapPlayerBotAIStates.end() && s->second.bStuckCounter >= 3;
		if (stuck && !b.bStuck)
			++st.stuck;
		b.bStuck = stuck;
		// MT2009_PLUS_BOT_SUNGMA_DEATHS_V1: the maximum health counted again once the Will is all there. The Sung Ma HP
		// penalty (ChampionMaxHP: half while Witalnosc is short) is judged at each POINT_MAX_HP change, and ComputePoints
		// makes the last of those before a glove's Will (the cohort's Witalnosc is the glove's stone) is in - a bot
		// revived or just landed stood at half until some later change (Namgan, 22 October: 11 995 of 23 990 after a
		// revive in a pack, 11 290 on landing three seconds before its death). Since MT2009_PLUS_SUNGMA_HP_ORDER_V1
		// (server-patches/czempion: each Witalnosc change counts the max HP again) the engine does it for persons and bots
		// alike; this look stays as a harmless safety net (PointChange(POINT_MAX_HP, 0) only recounts).
		const DWORD dwNow = get_dword_time();
		if (!ch->IsDead() && (int)(dwNow - b.dwNextHpLook) >= 0)
		{
			b.dwNextHpLook = dwNow + PLAYERBOT_SUNGMA_HP_LOOK_MS;
			if (GetPlayerBotSungmaWill(ch, 1) >= GetPlayerBotSungmaReq(slot, 1))
			{
				const int before = ch->GetMaxHP();
				ch->PointChange(POINT_MAX_HP, 0);
				if (ch->GetMaxHP() > before)
					PlayerBotLogThrottled("sungma_max_hp", dwNow, "PLAYERBOT_SUNGMA: max hp counted again pid=%u name=%s map=%ld max_hp=%d->%d",
							ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), before, ch->GetMaxHP());
			}
		}
	}

	// ------------------------------------------------------------ the stay

	// Out of this core (home; a member - its rest).
	int LeavePlayerBotSungma(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow, const char* why)
	{
		LeavePlayerBotSungmaParty(ch, why, false);	// MT2009_PLUS_BOT_YOHARA_FIGHT_V1
		return SendPlayerBotYoharaHome(ch, state, dwNow, why) ? 1 : 0;
	}

	// Onto another map of this core: the walk to the portal of this map that leads that way, then the warp to the
	// map's arrival (0/1 the travel pass's answer).
	int MovePlayerBotSungma(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotSungmaBot& b, long toMap, DWORD dwNow)
	{
		const long here = ch->GetMapIndex() >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? ch->GetMapIndex() / 10000 : ch->GetMapIndex();
		long ax = 0, ay = 0;
		if (!GetPlayerBotSungmaArrival(toMap, ax, ay))
			return 0;
		const int from = GetPlayerBotSungmaSlot(here), to = GetPlayerBotSungmaSlot(toMap);
		const TPlayerBotSungmaPortal* portal = NULL;
		// MT2009_PLUS_BOT_SUNGMA_DEATHS_V1: a step down after its deaths warps from where it stands. The walk to the portal
		// went back through the packs that had killed it: 9 of Seoganland's deaths, 11 of Namgan's and 28 of Zejscie's 46
		// (its rooms are joined by portals only - four minutes of a walk that cannot arrive) came on that walk (22 October).
		if (from >= 0 && to >= 0 && from != to && !b.bFlee)
		{
			// the portal toward it: the next map of the order up or down
			const long step = PLAYERBOT_SUNGMA_MAPS[to > from ? from + 1 : from - 1].lMap;
			for (size_t i = 0; i < sizeof(PLAYERBOT_SUNGMA_PORTALS) / sizeof(PLAYERBOT_SUNGMA_PORTALS[0]); ++i)
				if (PLAYERBOT_SUNGMA_PORTALS[i].lFrom == here && PLAYERBOT_SUNGMA_PORTALS[i].lTo == step)
					portal = &PLAYERBOT_SUNGMA_PORTALS[i];
			// MT2009_PLUS_BOT_YOHARA_MAPS_V2: walked to only from near it (PLAYERBOT_SUNGMA_PORTAL_WALK_NEAR) and on its
			// ground; a walk begun goes on (the bot comes nearer).
			if (portal && b.dwWalkSince == 0)
			{
				CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(ch->GetMapIndex());
				const int d = DISTANCE_APPROX(ch->GetX() - portal->x, ch->GetY() - portal->y);
				if (d > PLAYERBOT_SUNGMA_PORTAL_USE && (d > PLAYERBOT_SUNGMA_PORTAL_WALK_NEAR ||
						!navigation.Init(ch->GetMapIndex()) || !navigation.CanReach(ch->GetX(), ch->GetY(), portal->x, portal->y)))
				{
					sys_log(0, "PLAYERBOT_SUNGMA: portal far, warp pid=%u name=%s map=%ld to=%ld portal=(%ld,%ld) pos=(%ld,%ld) dist=%d",
							ch->GetPlayerID(), ch->GetName(), here, toMap, portal->x, portal->y, ch->GetX(), ch->GetY(), d);
					++s_aPlayerBotSungmaStats[from].portalWarps;
					portal = NULL;
				}
			}
		}
		if (portal && DISTANCE_APPROX(ch->GetX() - portal->x, ch->GetY() - portal->y) > PLAYERBOT_SUNGMA_PORTAL_USE)
		{
			if (b.dwWalkSince == 0)
			{
				b.dwWalkSince = dwNow ? dwNow : 1;
				++s_aPlayerBotSungmaStats[from].portalWalks;	// MT2009_PLUS_BOT_YOHARA_MAPS_V2
				sys_log(0, "PLAYERBOT_SUNGMA: to the portal pid=%u name=%s map=%ld to=%ld portal=(%ld,%ld) pos=(%ld,%ld)",
						ch->GetPlayerID(), ch->GetName(), here, toMap, portal->x, portal->y, ch->GetX(), ch->GetY());
			}
			if (dwNow - b.dwWalkSince < PLAYERBOT_SUNGMA_PORTAL_WALK_MS)
			{
				state.dwTargetVID = 0;
				ch->SetVictim(NULL);
				SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
				MovePlayerBot(ch, portal->x, portal->y, dwNow, 6, true, false, false, false);
				return 1;
			}
			PlayerBotLogThrottled("sungma_portal_walk", dwNow, "PLAYERBOT_SUNGMA: portal walk too long pid=%u name=%s map=%ld to=%ld pos=(%ld,%ld) after_s=%u",
					ch->GetPlayerID(), ch->GetName(), here, toMap, ch->GetX(), ch->GetY(), (dwNow - b.dwWalkSince) / 1000);
			if (from >= 0)
				++s_aPlayerBotSungmaStats[from].navFail;
		}
		b.dwWalkSince = 0;
		// MT2009_PLUS_BOT_SUNGMA_NEST_V1: landed on the cleanest ground by the map's safe point when the arrival is crowded
		// (the arrival and the safe point stand 0-3 000 apart; Wawoz's arrival 3 611 from a spawn, Namgan's 2 815).
		{
			long cx = 0, cy = 0;
			int ground = 0;
			const int arrivalGround = IsPlayerBotMapHostedHere(toMap) ? ScorePlayerBotSungmaGround(toMap, ax, ay) : 0;
			if (arrivalGround > 0 && GetPlayerBotSungmaCleanPoint(toMap, cx, cy, &ground) && ground < arrivalGround)
			{
				ax = cx;
				ay = cy;
				if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(toMap))
					++st->nestMoves;
			}
		}
		const bool ok = TransitionPlayerBotMap(ch, state, toMap, ax, ay, dwNow,
				portal ? "sungma_portal" : (b.bFlee ? "sungma_flee" : "sungma_move"));
		if (ok)
			b.bFlee = false;
		if (!ok)
		{
			if (from >= 0)
				++s_aPlayerBotSungmaStats[from].navFail;
			PlayerBotLogThrottled("sungma_move_failed", dwNow, "PLAYERBOT_SUNGMA: move failed pid=%u name=%s map=%ld to=%ld refusal=%s",
					ch->GetPlayerID(), ch->GetName(), here, toMap, s_szPlayerBotTransitionRefusal ? s_szPlayerBotTransitionRefusal : "-");
		}
		return ok ? 1 : 0;
	}

	// Zejscie's rooms: another room's spot (one this bot may take), the warp there - the room's portal for the bot.
	bool HopPlayerBotSungmaChamber(LPCHARACTER ch, int slot, TPlayerBotSungmaBot& b, DWORD dwNow, const char* why)
	{
		const TPlayerBotSungmaMap& m = PLAYERBOT_SUNGMA_MAPS[slot];
		CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(m.lMap);
		if (!navigation.Init(m.lMap))
			return false;
		std::vector<size_t> choice;
		const int hubLevel = 100 + GetPlayerBotChampionLevel(ch);
		for (size_t i = 0; i < m.uHubs; ++i)
			if (!m.pHubs[i].bNeedsParty && hubLevel >= (int)m.pHubs[i].bMinLevel &&
					!navigation.CanReach(ch->GetX(), ch->GetY(), m.pHubs[i].x, m.pHubs[i].y))
				choice.push_back(i);
		b.dwChamberSince = dwNow ? dwNow : 1;
		if (choice.empty())
			return false;
		const TPlayerBotHuntingHub& h = m.pHubs[choice[number(0, (int)choice.size() - 1)]];
		sys_log(0, "PLAYERBOT_SUNGMA: chamber hop pid=%u name=%s map=%ld from=(%ld,%ld) to=(%ld,%ld) why=%s",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), ch->GetX(), ch->GetY(), h.x, h.y, why);
		++s_aPlayerBotSungmaStats[slot].hops;
		ch->Stop();
		ch->Show(ch->GetMapIndex(), h.x, h.y, 0);
		return true;
	}

	// ------------------------------------------------------------ MT2009_PLUS_BOT_YOHARA_MAPS_V2: the revival, Dongan's errand

	bool IsPlayerBotSungmaResidentPID(DWORD pid)
	{
		const TPlayerBotYoharaResident* r = FindPlayerBotYoharaResident(pid);
		return r && r->iPurpose == YOHARA_PURPOSE_SUNGMA;
	}

	// HandleDeath (playerbot_survival.h), the bot just stood up: a Sung Ma resident is put at its map's safe point by the
	// arrival (PLAYERBOT_SUNGMA_SAFE_POINTS; Zejscie's in its first room), a person's "restart in town" there. True when
	// moved.
	bool MovePlayerBotSungmaRevived(LPCHARACTER ch)
	{
		if (!ch || ch->IsDead() || !IsPlayerBotSungmaResidentPID(ch->GetPlayerID()))
			return false;
		const long mapIndex = ch->GetMapIndex();
		const int slot = GetPlayerBotSungmaSlot(mapIndex);
		if (slot < 0 || mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN)
			return false;
		long ax = 0, ay = 0;
		if (!GetPlayerBotSungmaSafePoint(mapIndex, ax, ay) && !GetPlayerBotSungmaArrival(mapIndex, ax, ay))
			return false;
		// a party's fight goes on where it is (its members stand by it)
		// MT2009_PLUS_BOT_YOHARA_FIGHT_V1: only with two of them alive beside it and no pack awake on the spot (the revive
		// help); else the safe point, and the follow brings it back to its leader.
		if (IsPlayerBotSungmaRevivedInParty(ch))
		{
			if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(mapIndex))
				++st->revivesInParty;
			sys_log(0, "PLAYERBOT_SUNGMA: revived by its party pid=%u name=%s map=%ld pos=(%ld,%ld) party_near=%d",
					ch->GetPlayerID(), ch->GetName(), mapIndex, ch->GetX(), ch->GetY(),
					CountPlayerBotSungmaPartyNear(ch, PLAYERBOT_SUNGMA_REVIVE_PARTY_RADIUS));
			return false;
		}
		// MT2009_PLUS_BOT_SUNGMA_NEST_V1: the cleanest ground by the safe point (playerbot_sungma_fight.h) - the safe point
		// itself while nothing stands round it.
		int ground = 0, safeGround = 0;
		long cx = 0, cy = 0;
		if (GetPlayerBotSungmaCleanPoint(mapIndex, cx, cy, &ground, &safeGround))
		{
			if (cx != ax || cy != ay)
				if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(mapIndex))
					++st->nestMoves;
			ax = cx;
			ay = cy;
		}
		long ox = 0, oy = 0;
		GetPlayerBotStableOffset(ch->GetPlayerID(), 0x53524556U, 50, 250, ox, oy);
		sys_log(0, "PLAYERBOT_SUNGMA: revived at the safe point pid=%u name=%s map=%ld from=(%ld,%ld) to=(%ld,%ld) champion=%d ground=%d safe_ground=%d",
				ch->GetPlayerID(), ch->GetName(), mapIndex, ch->GetX(), ch->GetY(), ax + ox, ay + oy, GetPlayerBotChampionLevel(ch),
				ground, safeGround);
		++s_aPlayerBotSungmaStats[slot].revives;
		ch->Stop();
		ch->Show(mapIndex, ax + ox, ay + oy, 0);
		return true;
	}

	// MT2009_PLUS_BOT_SUNGMA_TRIPS_V1 (the owner, 31 October 2026 - boty-decyzje-2026-10-31.md, points 2 and 3: "Wszystkie
	// boty sprzedaja smieci zdalnie, na miejscu. Do Dongan wracaja tylko: po mikstury, do Dozorcy, ulepszac EQ. Do M1 na
	// CH1 boty wracaja wylacznie na zakupy na straganach"):
	//   * a full bag is no reason for any trip: every resident sells its junk where it stands (the merchants' price, the
	//     town visit's rule - SellPlayerBotJunkAtMerchant, the bag and the extra inventory) once in
	//     PLAYERBOT_SUNGMA_TIDY_MS while its bag has no free column of three or fewer than PLAYERBOT_SUNGMA_TIDY_FREE cells
	//     ("bag tidied", was a party member's only); Dongan's "+bag" errand is gone (need 2 never set) and so is the trade
	//     trip's "bag";
	//   * Dongan's errand: the potions (1) and Handlarka's elixirs (4 - potions too: the hunt element's resistance and
	//     power); the glove, jade and talisman refines at Dongan's smith / Mistrz Chi are playerbot_yohara_chi.h's own
	//     order trips (equipment upgrades). No Dozorca stands in Dongan (it is in the six villages) - no errand of it here;
	//   * the trip home to the first village (M1 of the first channel - StartPlayerBotSungmaTradeTrip) only to buy at the
	//     stands ("buy": the G0 dust, a refine or craft material, Handlarka's inputs, a Loch ticket on a counter). Its
	//     other reasons (bag, craft, goods, shop, routine) are counted ("m1_refused") and make no trip. The counter: a
	//     Sung Ma bot's offline counter stands in its first village and is served there only (the service walks to the
	//     stand, BotOfflineService - the core of the stand's channel and map); the shopping trip still serves it on
	//     arrival (ManagePlayerBotSungmaTradeHomes: the counter's service and the stands' browse nudged at once), its
	//     goods brought from the extra inventory first (PlayerBotEkwFetchGoods), and a craft that waits for Jaharr or
	//     Seon-Pyeong is done on such a stay (the gear2 pass asks IsPlayerBotSungmaTradeVisitor).
	// Census: "PLAYERBOT_SUNGMA: trips" with the summary (errands by need, the tidies and what they freed, the M1 trips
	// by reason and the reasons refused).
	const DWORD PLAYERBOT_SUNGMA_TIDY_MS = 5 * 60 * 1000;
	const int PLAYERBOT_SUNGMA_TIDY_FREE = 20;

	struct TPlayerBotSungmaTripStats
	{
		unsigned int errandPotions = 0, errandElixirs = 0;
		unsigned int tidies = 0, tidySold = 0, tidyStillFull = 0;
		int tidyFreed = 0;
		unsigned int m1Buy = 0, m1Counter = 0;
		unsigned int m1Refused[5] = {};	// bag, craft, goods, shop, routine (looks that would have gone)
	};
	TPlayerBotSungmaTripStats s_kPlayerBotSungmaTrips;
	const char* const PLAYERBOT_SUNGMA_M1_REFUSED[5] = { "bag", "craft", "goods", "shop", "routine" };

	// What the bot lacks that Dongan sells: 1 potions, (2 room in the bag - no more, MT2009_PLUS_BOT_SUNGMA_TRIPS_V1),
	// 4 Handlarka's elixirs.
	int GetPlayerBotSungmaErrandNeed(LPCHARACTER ch, const TPlayerBotSungmaBot& b, DWORD dwNow)
	{
		(void)b;
		if (!ch || !ch->IsItemLoaded())
			return 0;
		int need = 0;
		size_t red = 0, blue = 0;
		CountPlayerBotPotions(ch, red, blue);
		const bool caster = ch->GetJob() == JOB_SHAMAN || ch->GetJob() == JOB_SURA;
		if (red < PLAYERBOT_SUNGMA_ERRAND_RED || (caster && blue < PLAYERBOT_SUNGMA_ERRAND_BLUE))
			need |= 1;
		// MT2009_PLUS_BOT_YOHARA_SHOP_V1: 4 - elixirs at Handlarka Roznosci's exchange (playerbot_yohara_shop.h)
		if (PlayerBotYoharaShopWantsErrand(ch, dwNow))
			need |= 4;
		return need;
	}

	// MT2009_PLUS_BOT_SUNGMA_TRIPS_V1: the junk sold where the bot stands. True when it sold something.
	bool TidyPlayerBotSungmaBag(LPCHARACTER ch, TPlayerBotSungmaBot& b, DWORD dwNow)
	{
		if (!ch->IsItemLoaded() || ch->IsDead() || !ch->CanHandleItem() || ch->GetExchange() || ch->GetMyShop())
			return false;
		if (b.dwLastBagErrand != 0 && dwNow - b.dwLastBagErrand < PLAYERBOT_SUNGMA_TIDY_MS)
			return false;
		const int freeBefore = CountPlayerBotFreeInventoryCells(ch);
		if (ch->GetEmptyInventory(3) >= 0 && freeBefore >= PLAYERBOT_SUNGMA_TIDY_FREE)
			return false;
		b.dwLastBagErrand = dwNow ? dwNow : 1;	// the tidy's clock (the bag errand's, which is gone)
		if (!HasPlayerBotJunkForMerchant(ch, BOT_MERCHANT_MISC) && !HasPlayerBotJunkForMerchant(ch, BOT_MERCHANT_WEAPON) &&
				!HasPlayerBotJunkForMerchant(ch, BOT_MERCHANT_ARMOR))
		{
			if (ch->GetEmptyInventory(3) < 0)
				++s_kPlayerBotSungmaTrips.tidyStillFull;
			return false;
		}
		bool sold = SellPlayerBotJunkAtMerchant(ch, BOT_MERCHANT_MISC, "sungma_tidy_misc");
		sold = SellPlayerBotJunkAtMerchant(ch, BOT_MERCHANT_WEAPON, "sungma_tidy_weapon") || sold;
		sold = SellPlayerBotJunkAtMerchant(ch, BOT_MERCHANT_ARMOR, "sungma_tidy_armor") || sold;
		const int freeAfter = CountPlayerBotFreeInventoryCells(ch);
		++s_kPlayerBotSungmaTrips.tidies;
		if (sold)
			++s_kPlayerBotSungmaTrips.tidySold;
		s_kPlayerBotSungmaTrips.tidyFreed += freeAfter - freeBefore;
		if (ch->GetEmptyInventory(3) < 0)
			++s_kPlayerBotSungmaTrips.tidyStillFull;
		if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(ch->GetMapIndex()))
			++st->bagTidied;
		sys_log(0, "PLAYERBOT_SUNGMA: bag tidied pid=%u name=%s map=%ld members=%u free_cells=%d->%d free3=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(),
				ch->GetParty() ? (unsigned int)ch->GetParty()->GetMemberCount() : 0,
				freeBefore, freeAfter, ch->GetEmptyInventory(3) >= 0 ? 1 : 0);
		return sold;
	}

	// MT2009_PLUS_BOT_YOHARA_FIGHT_V1: where the bot stands to trade with a Dongan merchant - the pid's own place round it
	// (GetPlayerBotNpcApproach) when the arrival's ground reaches it, else the first of sixteen round the merchant that it
	// does. The test of 22 October (19:44-20:15): the weapon merchant's places (y 502 260-502 420, south of 9001) were
	// walled - eight "destination given up ... unreachable" after 600 s, the errand's four minutes gone and the fallback's
	// restock instead, and twelve of Dongan's "stuck" there.
	bool GetPlayerBotSungmaMerchantApproach(DWORD pid, const TPlayerBotSungmaMerchant& m, int stop, long& ax, long& ay)
	{
		GetPlayerBotNpcApproach(pid, m.x, m.y, 0x444f4e47U + (DWORD)stop, ax, ay);
		long fromX = 0, fromY = 0;
		CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(PLAYERBOT_MAP_SUNGMA_DONGAN);
		if (!GetPlayerBotSungmaArrival(PLAYERBOT_MAP_SUNGMA_DONGAN, fromX, fromY) || !navigation.Init(PLAYERBOT_MAP_SUNGMA_DONGAN) ||
				navigation.CanReach(fromX, fromY, ax, ay))
			return true;
		for (int r = 200; r <= 400; r += 100)
			for (int i = 0; i < 16; ++i)
			{
				float fx = 0.0f, fy = 0.0f;
				GetDeltaByDegree((float)(i * 360 / 16 + (int)(pid % 23U)), (float)r, &fx, &fy);
				const long x = m.x + (long)fx, y = m.y + (long)fy;
				if (navigation.CanReach(fromX, fromY, x, y))
				{
					ax = x;
					ay = y;
					return true;
				}
			}
		return false;
	}

	// The errand given up (too long, a warp refused, Dongan off): the belt kept full where it stands for a while.
	void FailPlayerBotSungmaErrand(LPCHARACTER ch, TPlayerBotYoharaResident& res, TPlayerBotSungmaBot& b, DWORD dwNow, const char* why)
	{
		const int slot = GetPlayerBotSungmaSlot(res.lMap);
		if (slot >= 0)
			++s_aPlayerBotSungmaStats[slot].errandFallbacks;
		PlayerBotLogThrottled("sungma_errand_fallback", dwNow, "PLAYERBOT_SUNGMA: errand fallback pid=%u name=%s map=%ld home_map=%ld why=%s after_s=%u",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), res.lMap, why,
				b.dwErrandSince ? (dwNow - b.dwErrandSince) / 1000 : 0);
		b.bErrand = false;
		b.dwErrandBackSince = dwNow ? dwNow : 1;	// MT2009_PLUS_BOT_SUNGMA_PARTY_KEEP_V1: the way back keeps the party
		b.dwErrandFallbackUntil = dwNow + PLAYERBOT_SUNGMA_ERRAND_FALLBACK_MS;
		res.dwNextRestock = 0;
		RestockPlayerBotYohara(ch, res, dwNow);
	}

	// Dongan's errand: -1 not on one (hunt on), 1 this tick is the errand's. Before the map's pick: on Dongan for an
	// errand a bot is not "off its map".
	int ManagePlayerBotSungmaErrand(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotYoharaResident& res,
			TPlayerBotSungmaBot& b, long base, DWORD dwNow)
	{
		// an errand of an earlier stay (the bot went home and came back) is over
		if (b.bErrand && (int)(res.dwArrived - b.dwErrandSince) > 0)
			b.bErrand = false;
		if (!b.bErrand)
		{
			if ((int)(dwNow - b.dwNextErrandLook) < 0)
				return -1;
			b.dwNextErrandLook = dwNow + PLAYERBOT_SUNGMA_ERRAND_LOOK_MS;
			// MT2009_PLUS_BOT_SUNGMA_PARTY_KEEP_V1: a party's member with no free column of three sells its junk where it
			// stands instead of the bag's errand.
			// MT2009_PLUS_BOT_SUNGMA_TRIPS_V1: every resident, party or not - the bag's errand is gone (see the top).
			TidyPlayerBotSungmaBag(ch, b, dwNow);
			const int need = GetPlayerBotSungmaErrandNeed(ch, b, dwNow);
			if (!need)
				return -1;
			const bool fallback = (int)(b.dwErrandFallbackUntil - dwNow) > 0 ||
					!IsPlayerBotSungmaMapOn(PLAYERBOT_MAP_SUNGMA_DONGAN) || !IsPlayerBotMapHostedHere(PLAYERBOT_MAP_SUNGMA_DONGAN);
			if (fallback)
			{
				res.dwNextRestock = 0;
				RestockPlayerBotYohara(ch, res, dwNow);
				return -1;
			}
			// Not out of a fight, nor half dead, nor off a party's stone: later - but an empty belt now is the fallback's.
			// MT2009_PLUS_BOT_YOHARA_FIGHT_V1: a party's member waits only while the party is on a stone or a boss; else it
			// leaves the party (below) and goes - a party of three never let its members go, and they hunted with
			// an empty belt (the fallback's restock) for the party's whole life.
			const bool busy = state.dwTargetVID != 0 || ch->GetVictim() != NULL || state.bTacticalRetreat ||
					ch->GetHP() * 100 < ch->GetMaxHP() * 40 || IsPlayerBotSungmaPartyOnObjective(ch) ||
					IsPlayerBotOnDungeonRun(ch->GetPlayerID());
			if (busy)
			{
				size_t red = 0, blue = 0;
				CountPlayerBotPotions(ch, red, blue);
				if (red < PLAYERBOT_SUNGMA_ERRAND_EMERGENCY)
				{
					res.dwNextRestock = 0;
					RestockPlayerBotYohara(ch, res, dwNow);
				}
				return -1;
			}
			// MT2009_PLUS_BOT_YOHARA_FIGHT_V1: out of its party cleanly first.
			// MT2009_PLUS_BOT_SUNGMA_PARTY_KEEP_V1: no more - the errand keeps its party (see IsPlayerBotSungmaErrandKeepingParty).
			if (ch->GetParty() && ch->GetParty()->GetMemberCount() >= 2 && !IsPlayerBotHumanLedParty(ch->GetParty()))
				if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(ch->GetMapIndex()))
					++st->errandPartyKept;
			b.bErrand = true;
			b.dwErrandBackSince = 0;
			b.iErrandStop = 0;
			b.iErrandNeed = need;
			b.dwErrandSince = dwNow ? dwNow : 1;
			if (need & 2)
				b.dwLastBagErrand = b.dwErrandSince;
			// MT2009_PLUS_BOT_SUNGMA_TRIPS_V1: the errands by what they are for
			if (need & 1)
				++s_kPlayerBotSungmaTrips.errandPotions;
			if (need & 4)
				++s_kPlayerBotSungmaTrips.errandElixirs;
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V4
			// MT2009_PLUS_BOT_ELEMENT_RESIST_V4: the exchange's gap from the errand that goes, not from the look
			if (need & 4)
				NotePlayerBotYoharaShopErrandStarted(ch, dwNow);
#endif
			const int slot = GetPlayerBotSungmaSlot(res.lMap);
			if (slot >= 0)
				++s_aPlayerBotSungmaStats[slot].errands;
			size_t red = 0, blue = 0;
			CountPlayerBotPotions(ch, red, blue);
			sys_log(0, "PLAYERBOT_SUNGMA: errand to dongan pid=%u name=%s map=%ld need=%s%s%s red=%u blue=%u free3=%d pos=(%ld,%ld) party=%u",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), (need & 1) ? "potions" : "", (need & 2) ? "+bag" : "",
					(need & 4) ? "+shop" : "",
					(unsigned int)red, (unsigned int)blue, ch->GetEmptyInventory(3) >= 0 ? 1 : 0, ch->GetX(), ch->GetY(),
					ch->GetParty() ? (unsigned int)ch->GetParty()->GetMemberCount() : 0);	// MT2009_PLUS_BOT_SUNGMA_PARTY_KEEP_V1
		}
		if (ch->IsDead() || state.bRecoveringAfterDeath)
			return -1;
		if (dwNow - b.dwErrandSince >= PLAYERBOT_SUNGMA_ERRAND_MS)
		{
			FailPlayerBotSungmaErrand(ch, res, b, dwNow, "too_long");
			return -1;
		}
		// the next merchant this errand calls on (the misc one for the potions and its junk, the others for theirs)
		while (b.iErrandStop < PLAYERBOT_SUNGMA_DONGAN_MERCHANT_COUNT)
		{
			const TPlayerBotSungmaMerchant& m = PLAYERBOT_SUNGMA_DONGAN_MERCHANTS[b.iErrandStop];
			if ((m.eCategory == BOT_MERCHANT_MISC && (b.iErrandNeed & 5)) || HasPlayerBotJunkForMerchant(ch, m.eCategory))	// MT2009_PLUS_BOT_YOHARA_SHOP_V1: 4
				break;
			++b.iErrandStop;
		}
		if (b.iErrandStop >= PLAYERBOT_SUNGMA_DONGAN_MERCHANT_COUNT)
		{
			size_t red = 0, blue = 0;
			CountPlayerBotPotions(ch, red, blue);
			sys_log(0, "PLAYERBOT_SUNGMA: errand done pid=%u name=%s back_to=%ld red=%u blue=%u free3=%d gold=%lld took_s=%u",
					ch->GetPlayerID(), ch->GetName(), res.lMap, (unsigned int)red, (unsigned int)blue,
					ch->GetEmptyInventory(3) >= 0 ? 1 : 0, (long long)ch->GetGold(), (dwNow - b.dwErrandSince) / 1000);
			b.bErrand = false;
			b.dwWalkSince = 0;
			b.dwErrandBackSince = dwNow ? dwNow : 1;	// MT2009_PLUS_BOT_SUNGMA_PARTY_KEEP_V1: the way back keeps the party
			return -1;	// the map's pick takes it back to its map (the arrival - by the portal when that is near)
		}
		const TPlayerBotSungmaMerchant& m = PLAYERBOT_SUNGMA_DONGAN_MERCHANTS[b.iErrandStop];
		long ax = 0, ay = 0;
		// MT2009_PLUS_BOT_YOHARA_FIGHT_V1: a stand the arrival's ground reaches (else the merchant is passed over)
		if (!GetPlayerBotSungmaMerchantApproach(ch->GetPlayerID(), m, b.iErrandStop, ax, ay))
		{
			PlayerBotLogThrottled("sungma_errand_unreachable", dwNow, "PLAYERBOT_SUNGMA: errand merchant unreachable pid=%u name=%s merchant=%u",
					ch->GetPlayerID(), ch->GetName(), m.dwRace);
			++b.iErrandStop;
			return 1;
		}
		if (base != PLAYERBOT_MAP_SUNGMA_DONGAN)
		{
			s_szPlayerBotTransitionRefusal = NULL;
			if (!TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_SUNGMA_DONGAN, ax, ay, dwNow, "sungma_errand"))
			{
				FailPlayerBotSungmaErrand(ch, res, b, dwNow, s_szPlayerBotTransitionRefusal ? s_szPlayerBotTransitionRefusal : "warp_refused");
				return -1;
			}
			return 1;
		}
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		if (DISTANCE_APPROX(ch->GetX() - ax, ch->GetY() - ay) > PLAYERBOT_SUNGMA_ERRAND_REACH)
		{
			SetPlayerBotAction(state, BOT_ACTION_SHOP, dwNow);
			MovePlayerBot(ch, ax, ay, dwNow, 6, true, false, false, false);
			return 1;
		}
		// at the merchant: its junk sold; at Handlarka Roznosci the belt bought too
		ch->Stop();
		SellPlayerBotJunkAtMerchant(ch, m.eCategory, m.szTag);
		if (m.eCategory == BOT_MERCHANT_MISC)
		{
			int boughtRed = 0, boughtBlue = 0;
			BuyPlayerBotYoharaBelt(ch, PLAYERBOT_SUNGMA_ERRAND_FILL, PLAYERBOT_SUNGMA_ERRAND_FILL, boughtRed, boughtBlue);
			RunPlayerBotYoharaShopExchange(ch, m.dwRace);	// MT2009_PLUS_BOT_YOHARA_SHOP_V1: the bots' exchange (playerbot_yohara_shop.h)
			// MT2009_PLUS_BOT_ELEMENT_RESIST_V1: the costume's reagents (70063/70064) off the same counter - rolled from
			// the bag out of a fight (ManagePlayerBotBonusReroll).
			if (IsPlayerBotYoharaBonusMember(ch))
				BuyPlayerBotCostumeReagent(ch, state);
			sys_log(0, "PLAYERBOT_SUNGMA: errand bought pid=%u name=%s merchant=%u bought_red=%d bought_blue=%d gold=%lld",
					ch->GetPlayerID(), ch->GetName(), m.dwRace, boughtRed, boughtBlue, (long long)ch->GetGold());
			// no cell for them even after its junk went (a bag of keepsakes): not the errand's again for a while - the
			// fallback makes a cell for a cohort's member where it stands
			if (b.iErrandNeed & 1)
			{
				size_t red = 0, blue = 0;
				CountPlayerBotPotions(ch, red, blue);
				const bool caster = ch->GetJob() == JOB_SHAMAN || ch->GetJob() == JOB_SURA;
				if (red < PLAYERBOT_SUNGMA_ERRAND_RED || (caster && blue < PLAYERBOT_SUNGMA_ERRAND_BLUE))
				{
					FailPlayerBotSungmaErrand(ch, res, b, dwNow, "no_room");
					return -1;
				}
			}
		}
		++b.iErrandStop;
		return 1;
	}

	// ------------------------------------------------------------ MT2009_PLUS_BOT_YOHARA_TRADE_TRIP_V1: the trade trip home

	// The goods of its bag a counter would take (CollectPlayerBotShopItems - what the bot can part with, best first).
	int CountPlayerBotSungmaTradeGoods(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		std::vector<std::pair<int, WORD> > scored;
		CollectPlayerBotShopItems(ch, scored, IsPlayerBotStallKeeper(state));
		int lines = 0;
		for (size_t i = 0; i < scored.size(); ++i)
			lines += scored[i].first > 0 ? 1 : 0;
		return lines;
	}

	// Its offline counter (the first channel's stands, on the home core's maps): none, run out, or nearly empty.
	bool IsPlayerBotSungmaCounterStale(LPCHARACTER ch)
	{
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		auto shop = ikashop::GetManager().GetShopByOwnerID(ch->GetPlayerID());
		return !shop || shop->GetDuration() == 0 || (int)shop->GetItems().size() < PLAYERBOT_SUNGMA_TRADE_SHOP_LINES;
#else
		(void)ch;
		return false;
#endif
	}

	bool HasPlayerBotSungmaCounter(LPCHARACTER ch)
	{
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		return HasPlayerBotOfflineShop(ch);
#else
		return ch && ch->GetMyShop() != NULL;
#endif
	}

	// Why the bot goes home to trade now (NULL: not now). The gaps count from the stay's start or the last trip, whichever
	// is later (a trip refused by its counter's room does not call the bot round in circles).
	// MT2009_PLUS_BOT_SUNGMA_TRIPS_V1: "buy" only - to the stands (see GetPlayerBotSungmaErrandNeed's note); the reasons
	// that used to send it too (bag, craft, goods, shop, routine) are counted and send it nowhere.
	const char* GetPlayerBotSungmaTradeReason(LPCHARACTER ch, const TPlayerBotAIState& state, const TPlayerBotYoharaResident& res,
			DWORD dwNow, int& goods)
	{
		goods = -1;
		// MT2009_PLUS_BOT_MELEY_RUNS_V1 (playerbot_dgrun_meley.h): its helmet waits for Schronienie Meley's materials -
		// home to game1 for the lair, its own gap and cap (not the trade trips').
		if (WantsPlayerBotMeleyTrip(ch, res.dwArrived, dwNow))
		{
			goods = CountPlayerBotSungmaTradeGoods(ch, state);
			return "meley";
		}
		std::map<DWORD, DWORD>::const_iterator last = s_mapPlayerBotSungmaTradeLast.find(ch->GetPlayerID());
		const DWORD from = last != s_mapPlayerBotSungmaTradeLast.end() && (int)(last->second - res.dwArrived) > 0
				? last->second : res.dwArrived;
		const DWORD gap = dwNow - from;
		if (gap < PLAYERBOT_SUNGMA_TRADE_BAG_GAP_MS)
			return NULL;
		// What it buys there: the dust of its G0 package, a refine material its gear waits for.
		// MT2009_PLUS_BOT_YOHARA_GEAR2_V1: and a craft's material a counter holds (the helmets' / armours' recipes too).
		// MT2009_PLUS_BOT_DUST_MARKET_V1: the G0's dust only while a counter holds some (WantsPlayerBotG0DustFromMarket,
		// the ledger) - the second G0's savers are more now (MT2009_PLUS_BOT_G0_DUST_RULE_V2), and a trip home to an
		// empty market is an errand out of the party for nothing.
		if (gap >= PLAYERBOT_SUNGMA_TRADE_BUY_GAP_MS && (
#ifdef MT2009_PLUS_BOT_DUST_MARKET_V1
				WantsPlayerBotG0DustFromMarket(ch) ||
#else
				IsPlayerBotG0DustHunter(ch) ||
#endif
				PlayerBotNeedsAnyRefineMaterial(ch) ||
				PlayerBotYoharaShopWantsMarket(ch) ||	// MT2009_PLUS_BOT_YOHARA_SHOP_V1: inputs of Dongan's exchange
#ifdef MT2009_PLUS_BOT_YOHARA_GUIDES_V1
				WantsPlayerBotLochTicketFromMarket(ch) ||	// MT2009_PLUS_BOT_YOHARA_GUIDES_V1: a Loch ticket on a counter
#endif
#ifdef MT2009_PLUS_BOT_SM_COUPON_MARKET_V1
				WantsPlayerBotSmCouponFromMarket(ch) ||	// MT2009_PLUS_BOT_SM_COUPON_MARKET_V1: a Kupon SM for a need's purchase
#endif
				PlayerBotWantsCraftFromMarket(ch)))
		{
			goods = CountPlayerBotSungmaTradeGoods(ch, state);
			return "buy";
		}
		// MT2009_PLUS_BOT_SUNGMA_TRIPS_V1: the old reasons, in their old order - counted, no trip. The bag's: no free
		// column of three, nothing Dongan's merchants take, and goods a counter would.
		goods = CountPlayerBotSungmaTradeGoods(ch, state);
		int refused = -1;
		if (goods >= PLAYERBOT_SUNGMA_TRADE_BAG_GOODS && ch->GetEmptyInventory(3) < 0 &&
				!HasPlayerBotJunkForMerchant(ch, BOT_MERCHANT_MISC) && !HasPlayerBotJunkForMerchant(ch, BOT_MERCHANT_WEAPON) &&
				!HasPlayerBotJunkForMerchant(ch, BOT_MERCHANT_ARMOR))
			refused = 0;
		else if (gap < PLAYERBOT_SUNGMA_TRADE_GOODS_GAP_MS)
			refused = -1;
		else if (WantsPlayerBotGear2TradeTrip(ch))	// MT2009_PLUS_BOT_YOHARA_GEAR2_V1: Jaharr's / Seon-Pyeong's work ready
			refused = 1;
		else if (goods >= PLAYERBOT_SUNGMA_TRADE_GOODS)
			refused = 2;
		else if (goods >= PLAYERBOT_SUNGMA_TRADE_SHOP_GOODS && IsPlayerBotSungmaCounterStale(ch))
			refused = 3;
		else if (gap >= (DWORD)GetPlayerBotYoharaConfig().sungmaStayMin * 60000U &&
				(goods > 0 || HasPlayerBotSungmaCounter(ch) || ch->GetGold() > 0))
			refused = 4;
		// MT2009_PLUS_BOT_SUNGMA_TRIPS_V2 (the owner, 31 October 2026: "niech normalnie chodza obslugiwac swoje stragany"):
		// the counter's reasons send it home again as before - its goods for the counter (bag 0, goods 2), the counter
		// gone or stale (shop 3) and the round of its sales and stock (routine 4). Only the craft's (1, Jaharr's /
		// Seon-Pyeong's work) stays counted and refused - it is done on a stay anyway.
		static const char* const s_apszCounterWhy[] = { "bag", NULL, "goods", "shop", "routine" };
		if (refused >= 0 && s_apszCounterWhy[refused])
			return s_apszCounterWhy[refused];
		if (refused >= 0)
			++s_kPlayerBotSungmaTrips.m1Refused[refused];
		return NULL;
	}

	// The trips of this core's residents out to their homes and not back yet (all the Sung Ma maps of a channel are on
	// one core: the channel's count). A trip lost on the way (a log-out at home) is forgotten after a while.
	int CountPlayerBotSungmaTradeAway(DWORD dwNow)
	{
		for (std::map<DWORD, TPlayerBotSungmaTradeOut>::iterator i = s_mapPlayerBotSungmaTradeOut.begin();
				i != s_mapPlayerBotSungmaTradeOut.end();)
		{
			if (dwNow - i->second.dwAt >= PLAYERBOT_SUNGMA_TRADE_LOST_MS)
			{
				sys_log(0, "PLAYERBOT_SUNGMA: trade trip lost pid=%u back_to=%ld away_s=%u", i->first, i->second.lMap,
						(dwNow - i->second.dwAt) / 1000);
				s_mapPlayerBotSungmaTradeOut.erase(i++);
				continue;
			}
			++i;
		}
		return (int)s_mapPlayerBotSungmaTradeOut.size();
	}

	// The trip out: its first village's ring of stands by the handover (purpose "home" - no Sung Ma room held while it is
	// there), its map and reason in the row's reason for the home core ("sungma_trade:<map>:<why>"). 1 gone, -1 not now.
	int StartPlayerBotSungmaTradeTrip(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotYoharaResident& res,
			TPlayerBotSungmaBot& b, DWORD dwNow)
	{
		if ((int)(dwNow - b.dwNextTradeLook) < 0)
			return -1;
		b.dwNextTradeLook = dwNow + PLAYERBOT_SUNGMA_TRADE_LOOK_MS;
		const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
		if (cfg.sungmaTradeMax <= 0 || !IsPlayerBotYoharaOn() || !ch->IsItemLoaded() || b.bErrand)
			return -1;
		// not out of a fight, half dead, a party's stone or a run (Dongan's errand's rule)
		// MT2009_PLUS_BOT_YOHARA_FIGHT_V1: a party's member - only while the party is on a stone or a boss (it leaves the
		// party at the start below)
		if (state.dwTargetVID != 0 || ch->GetVictim() != NULL || state.bTacticalRetreat || ch->IsDead() ||
				state.bRecoveringAfterDeath || ch->GetHP() * 100 < ch->GetMaxHP() * 40 ||
				IsPlayerBotSungmaPartyOnObjective(ch) || IsPlayerBotOnDungeonRun(ch->GetPlayerID()))
			return -1;
		int goods = -1;
		const char* why = GetPlayerBotSungmaTradeReason(ch, state, res, dwNow, goods);
		if (!why)
			return -1;
		const int away = CountPlayerBotSungmaTradeAway(dwNow);
		// MT2009_PLUS_BOT_MELEY_RUNS_V1: the lair's trips keep to their own cap (WantsPlayerBotMeleyTrip) and leave the
		// trade trips' to the trade.
		const bool meley = !strcmp(why, "meley");
		if (!meley && away - std::min(away, CountPlayerBotMeleyTripsOut(dwNow)) >= cfg.sungmaTradeMax)
		{
			PlayerBotLogThrottled("sungma_trade_cap", dwNow, "PLAYERBOT_SUNGMA: trade trip waits pid=%u name=%s why=%s away=%d max=%d",
					ch->GetPlayerID(), ch->GetName(), why, away, cfg.sungmaTradeMax);
			return -1;
		}
		long home = 0, x = 0, y = 0;
		if (!GetPlayerBotVillageReturn(ch, playerbot_empire_rules::MAP_ROLE_M1, home, x, y) || IsPlayerBotMapHostedHere(home))
			return -1;
		long ox = 0, oy = 0;
		GetPlayerBotStableOffset(ch->GetPlayerID(), 0x54524144U, PLAYERBOT_SHOP_RING_MIN, PLAYERBOT_SHOP_RING_RADIUS, ox, oy);
		if (goods < 0)
			goods = CountPlayerBotSungmaTradeGoods(ch, state);
		const long backMap = res.lMap;
		const int slot = GetPlayerBotSungmaSlot(backMap);
		char reason[48];
		snprintf(reason, sizeof(reason), "sungma_trade:%ld:%s", backMap, why);
		const DWORD pid = ch->GetPlayerID();
		const long long gold = (long long)ch->GetGold();
		const int free3 = ch->GetEmptyInventory(3) >= 0 ? 1 : 0;
		const unsigned int stayS = (dwNow - res.dwArrived) / 1000;
		LeavePlayerBotSungmaParty(ch, "trade_trip", true);	// MT2009_PLUS_BOT_YOHARA_FIGHT_V1: out of its party cleanly first
		if (!RequestPlayerBotYoharaHandover(ch, state, home, x + ox, y + oy, YOHARA_PURPOSE_HOME, reason, dwNow))
			return -1;
		TPlayerBotSungmaTradeOut& out = s_mapPlayerBotSungmaTradeOut[pid];
		out.dwAt = dwNow ? dwNow : 1;
		out.lMap = backMap;
		s_mapPlayerBotSungmaTradeLast[pid] = out.dwAt;
		if (slot >= 0)
		{
			++s_aPlayerBotSungmaStats[slot].tradeTrips;
			--s_aiPlayerBotSungmaMapCensus[slot];	// the poll counts the rows again
		}
		if (meley)
			NotePlayerBotMeleyTripOut(ch, dwNow);	// MT2009_PLUS_BOT_MELEY_RUNS_V1
		else if (!strcmp(why, "buy"))
			++s_kPlayerBotSungmaTrips.m1Buy;	// MT2009_PLUS_BOT_SUNGMA_TRIPS_V1
		else
			++s_kPlayerBotSungmaTrips.m1Counter;	// MT2009_PLUS_BOT_SUNGMA_TRIPS_V2: the counter's trips
		sys_log(0, "PLAYERBOT_SUNGMA: trade trip start pid=%u name=%s map=%ld home=%ld why=%s goods=%d free3=%d gold=%lld "
				"champion=%d member=%d stay_s=%u away=%d",
				pid, ch->GetName(), backMap, home, why, goods, free3, gold, GetPlayerBotChampionLevel(ch),
				IsPlayerBotYoharaCohortPID(pid) ? 1 : 0, stayS, away + 1);
		return 1;
	}

	// The home core's reading of a row's reason: the map the trip goes back to, and why it was made.
	bool ParsePlayerBotSungmaTradeReason(const char* reason, long& backMap, char* why, size_t whySize)
	{
		backMap = 0;
		if (whySize)
			why[0] = '\0';
		static const char s_aPrefix[] = "sungma_trade:";
		if (!reason || strncmp(reason, s_aPrefix, sizeof(s_aPrefix) - 1) != 0)
			return false;
		const char* p = reason + sizeof(s_aPrefix) - 1;
		backMap = atol(p);
		const char* colon = strchr(p, ':');
		if (colon && whySize)
			strlcpy(why, colon + 1, whySize);
		return backMap > 0;
	}

	bool IsPlayerBotSungmaTradeVisitor(DWORD pid)
	{
		return s_mapPlayerBotSungmaTradeHome.count(pid) != 0;
	}

	// The home core: a trade trip's bot stands in its first village (SettlePlayerBotYoharaArrivals) - no cooldown, no draw,
	// no dispatch; ManagePlayerBotSungmaTradeHomes sends it back.
	void StartPlayerBotSungmaTradeHome(LPCHARACTER ch, long backMap, const char* why, DWORD dwNow)
	{
		const DWORD pid = ch->GetPlayerID();
		TPlayerBotSungmaTradeHome& v = s_mapPlayerBotSungmaTradeHome[pid];
		v = TPlayerBotSungmaTradeHome();
		v.lBackMap = backMap;
		v.dwSince = dwNow ? dwNow : 1;
		v.llGold = (long long)ch->GetGold();
		strlcpy(v.szWhy, why && *why ? why : "-", sizeof(v.szWhy));
		++s_uPlayerBotSungmaTradeHomeArrived;
		if (!strcmp(v.szWhy, "meley"))	// MT2009_PLUS_BOT_MELEY_RUNS_V1: a visitor for Schronienie Meley
			NotePlayerBotMeleyVisitorHome(ch, dwNow);
		sys_log(0, "PLAYERBOT_SUNGMA: trade trip home pid=%u name=%s map=%ld pos=(%ld,%ld) back_to=%ld why=%s gold=%lld member=%d",
				pid, ch->GetName(), ch->GetMapIndex(), ch->GetX(), ch->GetY(), backMap, v.szWhy, v.llGold,
				IsPlayerBotYoharaCohortPID(pid) ? 1 : 0);
	}

	// The game3 side: a trade trip's bot is back on its Sung Ma map (SettlePlayerBotYoharaArrivals).
	void NotePlayerBotSungmaTradeLanded(LPCHARACTER ch, DWORD dwNow)
	{
		std::map<DWORD, TPlayerBotSungmaTradeOut>::iterator out = s_mapPlayerBotSungmaTradeOut.find(ch->GetPlayerID());
		if (out == s_mapPlayerBotSungmaTradeOut.end())
			return;
		const int slot = GetPlayerBotSungmaSlot(ch->GetMapIndex());
		if (slot >= 0)
			++s_aPlayerBotSungmaStats[slot].tradeBacks;
		sys_log(0, "PLAYERBOT_SUNGMA: trade trip landed pid=%u name=%s map=%ld left=%ld away_s=%u gold=%lld",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), out->second.lMap, (dwNow - out->second.dwAt) / 1000,
				(long long)ch->GetGold());
		s_mapPlayerBotSungmaTradeOut.erase(out);
	}

	// The errand at home done: its counter served since it came (or none to serve), no purchase or visit under way.
	bool IsPlayerBotSungmaTradeHomeDone(LPCHARACTER ch, const TPlayerBotAIState& state, const TPlayerBotSungmaTradeHome& v,
			DWORD dwNow)
	{
		const DWORD el = dwNow - v.dwSince;
		// MT2009_PLUS_BOT_MELEY_RUNS_V1: a visitor for Schronienie Meley stays for its run (playerbot_dgrun_meley.h).
		if (IsPlayerBotMeleyVisitHeld(ch, dwNow))
			return false;
		if (el >= PLAYERBOT_SUNGMA_TRADE_HOME_MAX_MS)
			return true;
		if (el < PLAYERBOT_SUNGMA_TRADE_HOME_MIN_MS || state.bVisitingShop || state.bMarketTrip)
			return false;
		// MT2009_PLUS_BOT_YOHARA_GEAR2_V1: at Jaharr or Seon-Pyeong (playerbot_yohara_gear2.h), or still to go there.
		if (IsPlayerBotGear2ErrandBusy(ch->GetPlayerID()) || WantsPlayerBotGear2TradeTrip(ch))
			return false;
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		const playerbot_offline::State& o = state.offlineShop;
		if (o.visiting || o.buyOwner || playerbot_offline::requests.count(ch->GetPlayerID()))
			return false;
		const bool served = o.lastServedAt != 0 && (int)(o.lastServedAt - v.dwSince) >= 0;
		if (!served && HasPlayerBotOfflineShop(ch) && el < PLAYERBOT_SUNGMA_TRADE_HOME_SERVE_MS)
			return false;
#endif
		return true;
	}

	// The home core's poll (ManagePlayerBotYoharaHandover): the errand's clocks set going once, and the way back - to the
	// map it left (the pick's when that one has no room) by a new handover, its purpose "yohara", no draw or cooldown.
	void ManagePlayerBotSungmaTradeHomes(DWORD dwNow)
	{
		for (std::map<DWORD, TPlayerBotSungmaTradeHome>::iterator i = s_mapPlayerBotSungmaTradeHome.begin();
				i != s_mapPlayerBotSungmaTradeHome.end();)
		{
			const DWORD pid = i->first;
			TPlayerBotSungmaTradeHome& v = i->second;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
			TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(pid);
			if (!ch || st == s_mapPlayerBotAIStates.end() || IsPlayerBotYoharaLeaving(pid))
			{
				if (!ch)
					sys_log(0, "PLAYERBOT_SUNGMA: trade trip ends at home pid=%u why=logged_out after_s=%u", pid,
							(dwNow - v.dwSince) / 1000);
				s_mapPlayerBotSungmaTradeHome.erase(i++);
				continue;
			}
			TPlayerBotAIState& state = st->second;
			if (!v.bNudged && ch->IsItemLoaded())
			{
				// the counter's service, the browse of the stands and a counter's opening - now, not on their rounds
				// (the first thirty seconds after a load are the shop list's)
				v.bNudged = true;
				state.dwNextShopKeepTime = 0;
				state.dwNextShoppingTime = dwNow;
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
				if (!state.offlineShop.visiting)
					state.offlineShop.nextService = dwNow + 30000;
				state.offlineShop.nextBrowse = dwNow + 30000;
#endif
			}
			const DWORD el = dwNow - v.dwSince;
			if (!IsPlayerBotSungmaTradeHomeDone(ch, state, v, dwNow) || ch->IsDead() || IsPlayerBotOnDungeonRun(pid))
			{
				++i;
				continue;
			}
			const char* stuck = NULL;
			if (!IsPlayerBotYoharaOn())
				stuck = "handover_off";
			else if (GetPlayerBotChampionLevel(ch) < 1 || (int)ch->GetLevel() < gPlayerMaxLevel)
				stuck = "not_champion";
			if (stuck)
			{
				sys_log(0, "PLAYERBOT_SUNGMA: trade trip ends at home pid=%u name=%s why=%s after_s=%u", pid, ch->GetName(), stuck,
						el / 1000);
				s_mapPlayerBotSungmaTradeHome.erase(i++);
				continue;
			}
			// the map it left, while it has room - else the pick's (from home every map is a step up)
			long map = v.lBackMap;
			int slot = GetPlayerBotSungmaSlot(map);
			if (slot < 0 || !IsPlayerBotSungmaMapOn(map) || !HasPlayerBotSungmaRoom(slot, 0))
			{
				map = PickPlayerBotSungmaMap(ch, 0);
				slot = GetPlayerBotSungmaSlot(map);
			}
			long x = 0, y = 0;
			const bool room = slot >= 0 && HasPlayerBotSungmaRoom(slot, 0) &&
					s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_SUNGMA] < GetPlayerBotYoharaCap(YOHARA_PURPOSE_SUNGMA);
			const bool eligible = IsPlayerBotYoharaEligible(ch) || IsPlayerBotYoharaCohortPID(pid);
			if (!room || !eligible || !GetPlayerBotFrontierArrival(map, x, y))
			{
				if (el >= PLAYERBOT_SUNGMA_TRADE_HOME_MAX_MS + PLAYERBOT_SUNGMA_TRADE_STRANDED_MS)
				{
					++s_uPlayerBotSungmaTradeStranded;
					sys_log(0, "PLAYERBOT_SUNGMA: trade trip ends at home pid=%u name=%s why=%s back_to=%ld after_s=%u",
							pid, ch->GetName(), !eligible ? "not_eligible" : "no_room", map, el / 1000);
					s_mapPlayerBotSungmaTradeHome.erase(i++);
					continue;
				}
				PlayerBotLogThrottled("sungma_trade_back_wait", dwNow, "PLAYERBOT_SUNGMA: trade trip back waits pid=%u name=%s back_to=%ld "
						"room=%d eligible=%d census=%d/%d", pid, ch->GetName(), map, room ? 1 : 0, eligible ? 1 : 0,
						s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_SUNGMA], GetPlayerBotYoharaCap(YOHARA_PURPOSE_SUNGMA));
				++i;
				continue;
			}
			const long long gold = (long long)ch->GetGold();
			int served = 0;
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
			served = state.offlineShop.lastServedAt != 0 && (int)(state.offlineShop.lastServedAt - v.dwSince) >= 0 ? 1 : 0;
#endif
			const int goods = CountPlayerBotSungmaTradeGoods(ch, state);
			const bool counter = HasPlayerBotSungmaCounter(ch);
			if (!RequestPlayerBotYoharaHandover(ch, state, map, x, y, YOHARA_PURPOSE_SUNGMA, "sungma_trade_back", dwNow))
			{
				++i;
				continue;
			}
			++s_aiPlayerBotSungmaMapCensus[slot];
			++s_uPlayerBotSungmaTradeHomeBack;
			sys_log(0, "PLAYERBOT_SUNGMA: trade trip back pid=%u name=%s from=%ld to=%ld why=%s took_s=%u served=%d counter=%d "
					"goods_left=%d gold=%lld->%lld done=%s",
					pid, ch->GetName(), ch->GetMapIndex(), map, v.szWhy, el / 1000, served, counter ? 1 : 0, goods, v.llGold, gold,
					el >= PLAYERBOT_SUNGMA_TRADE_HOME_MAX_MS ? "timeout" : "served");
			s_mapPlayerBotSungmaTradeHome.erase(i++);
		}
	}

	// MT2009_PLUS_BOT_TRAINER_REARM_V1: the best weapon of the bag this bot may wear (FindPlayerBotBestBagWeapon's rules),
	// else the highest one of its class it can put on at all; true when the hand holds a weapon after it.
	unsigned int s_uPlayerBotTrainerRearmed = 0, s_uPlayerBotTrainerRearmFailed = 0;
	const DWORD PLAYERBOT_TRAINER_REARM_GRACE_MS = 60 * 1000;
	bool RearmPlayerBotFromBag(LPCHARACTER ch, TPlayerBotAIState& state, const char* where)
	{
		if (!ch || !ch->IsItemLoaded() || ch->GetWear(WEAR_WEAPON) != NULL)
			return false;
		static std::map<DWORD, DWORD> s_mapNextTry;
		const DWORD dwNow = get_dword_time();
		DWORD& next = s_mapNextTry[ch->GetPlayerID()];
		if (next != 0 && (int)(dwNow - next) < 0)
			return false;
		next = dwNow + 5000;
		LPITEM weapon = FindPlayerBotBestBagWeapon(ch, NULL, NULL);
		const char* how = "best";
		if (!weapon)
		{
			how = "any";
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				if (!item || item->GetCell() != cell || item->IsEquipped() || item->GetType() != ITEM_WEAPON ||
						item->GetSubType() == WEAPON_ARROW || item->GetLevelLimit() > ch->GetLevel() ||
						item->FindEquipCell(ch) != WEAR_WEAPON || !ch->CanEquipNow(item))
					continue;
				if (!weapon || item->GetLevelLimit() > weapon->GetLevelLimit() ||
						(item->GetLevelLimit() == weapon->GetLevelLimit() && item->GetRefineLevel() > weapon->GetRefineLevel()))
					weapon = item;
			}
		}
		if (!weapon)
		{
			++s_uPlayerBotTrainerRearmFailed;
			PlayerBotLogThrottled("trainer_rearm_none", get_dword_time(), "PLAYERBOT_TRAINER: rearm none pid=%u name=%s where=%s map=%ld",
					ch->GetPlayerID(), ch->GetName(), where, ch->GetMapIndex());
			return false;
		}
		const DWORD vnum = weapon->GetVnum();
		// what the engine would say, before the put-on (the log's why)
		const bool canNow = ch->CanEquipNow(weapon);
		const bool busy = ch->IsBusy(), stun = ch->IsStun(), locked = weapon->isLocked(), poly = ch->IsPolymorphed();
		const int cellFor = weapon->FindEquipCell(ch);
		const bool ok = PlayerBotEquipItem(ch, weapon) && ch->GetWear(WEAR_WEAPON) != NULL;
		state.bEquipPending = true;
		state.dwNextEquipmentCheckTime = 0;
		if (ok)
			++s_uPlayerBotTrainerRearmed;
		else
			++s_uPlayerBotTrainerRearmFailed;
		sys_log(0, "PLAYERBOT_TRAINER: rearm %s pid=%u name=%s where=%s map=%ld vnum=%u how=%s can_now=%d busy=%d stun=%d locked=%d "
				"poly=%d cell=%d window=%d pos=%d costume_weapon=%u rearmed=%u failed=%u",
				ok ? "ok" : (canNow ? "pending" : "refused"), ch->GetPlayerID(), ch->GetName(), where, ch->GetMapIndex(), vnum, how, canNow ? 1 : 0,
				busy ? 1 : 0, stun ? 1 : 0, locked ? 1 : 0, poly ? 1 : 0, cellFor, (int)weapon->GetWindow(), (int)weapon->GetCell(),
				ch->GetWear(WEAR_COSTUME_WEAPON) ? ch->GetWear(WEAR_COSTUME_WEAPON)->GetVnum() : 0,
				s_uPlayerBotTrainerRearmed, s_uPlayerBotTrainerRearmFailed);
		return ok;
	}

	// The travel pass's part for a resident of purpose "yohara" (ManagePlayerBotYoharaTravel): -1 hunt on, 0/1 its answer.
	int ManagePlayerBotSungmaResident(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotYoharaResident& res, DWORD dwNow)
	{
		const DWORD pid = ch->GetPlayerID();
		const long base = ch->GetMapIndex() >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? ch->GetMapIndex() / 10000 : ch->GetMapIndex();
		TPlayerBotSungmaBot& b = s_mapPlayerBotSungma[pid];
		const TPlayerBotYoharaConfig& cfg = GetPlayerBotYoharaConfig();
		if (GetPlayerBotChampionLevel(ch) < 1 || (int)ch->GetLevel() < gPlayerMaxLevel)
			return LeavePlayerBotSungma(ch, state, dwNow, "sungma_not_champion");
		if (res.iDeaths >= PLAYERBOT_SUNGMA_DEATHS_STAY)
			return LeavePlayerBotSungma(ch, state, dwNow, "sungma_deaths");
		const bool member = IsPlayerBotYoharaCohortPID(pid);
		// MT2009_PLUS_BOT_YOHARA_TRADE_TRIP_V1: its stay's end is no way home any more - its round of trade is (the
		// trade trip below, "routine"); only with the trips switched off (PLAYERBOT_SUNGMA_TRADE_MAX=0) the old way home.
		if (!member && cfg.sungmaTradeMax <= 0 && dwNow - res.dwArrived >= (DWORD)cfg.sungmaStayMin * 60000U)
			return LeavePlayerBotSungma(ch, state, dwNow, "sungma_stay_over");
		if (member && dwNow - res.dwArrived >= (DWORD)cfg.cohortStayMin * 60000U)
			return LeavePlayerBotSungma(ch, state, dwNow, "sungma_stay_over");
		if (IsPlayerBotYoharaFightStopped(ch, res, dwNow))
		{
			// MT2009_PLUS_BOT_TRAINER_REARM_V1: a resident whose hand is empty with a weapon of its own in the bag (51 of the
			// 900 on 3 November - a piece taken off for an anvil, a Seon-Hae or a 6/7 roll and the bot logged out before the
			// equipment pass put it back) arms itself here: it was sent home at its first tick on the map, came back ten
			// minutes later, and was sent home again - ~2 800 handovers a day for nothing.
			if (ch->GetWear(WEAR_WEAPON) == NULL && RearmPlayerBotFromBag(ch, state, "sungma"))
				return 0;
			// the engine refuses a put-on in the first moments of a load (the equip pulse, a busy state): the hand's
			// weapon is tried again for PLAYERBOT_TRAINER_REARM_GRACE_MS before the way home
			if (ch->GetWear(WEAR_WEAPON) == NULL && dwNow - res.dwArrived < PLAYERBOT_TRAINER_REARM_GRACE_MS &&
					FindPlayerBotBestBagWeapon(ch, NULL, NULL) != NULL)
				return 0;
			return LeavePlayerBotSungma(ch, state, dwNow, "sungma_blocked");
		}
		SpendPlayerBotSungmaPoints(ch, b, dwNow);
#ifdef MT2009_PLUS_BOT_YOHARA_GUIDES_V1
		// MT2009_PLUS_BOT_YOHARA_GUIDES_V1: the Sung Ma buffs, the boosters, Tajemniczy Loch's excursion (its own answer)
		{
			const int guides = ManagePlayerBotYoharaGuides(ch, state, res, b, base, dwNow);
			if (guides != -2)
				return guides;
		}
#endif
		// MT2009_PLUS_BOT_YOHARA_MAPS_V2: Dongan's merchants, not home.
		if (ManagePlayerBotSungmaErrand(ch, state, res, b, base, dwNow) > 0)
			return 1;
		// MT2009_PLUS_BOT_YOHARA_CHI_V1: the orders at Mistrz Chi and the smith of Dongan (playerbot_yohara_chi.h).
		if (ManagePlayerBotYoharaChi(ch, state, base, dwNow) > 0)
			return 1;
		// MT2009_PLUS_BOT_YOHARA_TRADE_TRIP_V1: home to its first village only to trade, and back.
		if (StartPlayerBotSungmaTradeTrip(ch, state, res, b, dwNow) > 0)
			return 1;
		// Its deaths: a step down a map, this one "not now" for two hours.
		if (res.iDeathsWindowed >= PLAYERBOT_YOHARA_DEATHS_WINDOWED && GetPlayerBotSungmaSlot(res.lMap) >= 0)
		{
			b.mapNotNow[res.lMap] = dwNow + PLAYERBOT_SUNGMA_NOT_NOW_MS;
			b.bFlee = true;	// MT2009_PLUS_BOT_SUNGMA_DEATHS_V1
			res.iDeathsWindowed = 0;
			res.dwWindowStart = 0;
			b.dwNextPick = 0;
			++s_aPlayerBotSungmaStats[GetPlayerBotSungmaSlot(res.lMap)].stepsDown;
			sys_log(0, "PLAYERBOT_SUNGMA: step down pid=%u name=%s map=%ld deaths=%d champion=%d", pid, ch->GetName(), res.lMap,
					res.iDeaths, GetPlayerBotChampionLevel(ch));
		}
		// The map: looked at now and then once settled (at once when it does not fit any more).
		if (base != b.lMapSeen)
		{
			b.lMapSeen = base;
			b.dwOnMapSince = dwNow ? dwNow : 1;
			b.dwChamberSince = dwNow ? dwNow : 1;
		}
		const int slotNow = GetPlayerBotSungmaSlot(res.lMap);
		// MT2009_PLUS_BOT_YOHARA_MAPS_V2: the Will and the band judged once the items are in and the bot has stood here
		// PLAYERBOT_SUNGMA_FIT_SETTLE_MS (its glove's Will read 0 at the load); the deaths' "not now" at once.
		const bool judged = ch->IsItemLoaded() && dwNow - b.dwOnMapSince >= PLAYERBOT_SUNGMA_FIT_SETTLE_MS;
		// MT2009_PLUS_BOT_SUNGMA_NEST_V1: the health judged on its own map only, out of the Alchemist's visit (its dragon
		// stones off there) - the cohort's bulk alchemists stand in Dongan a minute or two every few minutes.
		const bool judgeHp = judged && base == res.lMap && !state.bVisitingDsAlchemist;
		const bool fitsNow = slotNow >= 0 && IsPlayerBotSungmaMapOn(res.lMap) && b.mapNotNow.count(res.lMap) == 0 &&
				(!judged || (IsPlayerBotSungmaWillEnough(ch, slotNow) &&
				 GetPlayerBotChampionLevel(ch) >= (int)PLAYERBOT_SUNGMA_MAPS[slotNow].bChampionMin &&
				 (!judgeHp || IsPlayerBotSungmaHpEnough(ch, slotNow, true))));	// MT2009_PLUS_BOT_SUNGMA_NEST_V1
		if (!fitsNow || ((int)(dwNow - b.dwNextPick) >= 0 && dwNow - b.dwOnMapSince >= PLAYERBOT_SUNGMA_SETTLE_MS))
		{
			b.dwNextPick = dwNow + PLAYERBOT_SUNGMA_PICK_MS;
			for (std::map<long, DWORD>::iterator nn = b.mapNotNow.begin(); nn != b.mapNotNow.end();)
			{
				if ((int)(nn->second - dwNow) <= 0)
					b.mapNotNow.erase(nn++);
				else
					++nn;
			}
			const long pick = PickPlayerBotSungmaMap(ch, res.lMap, judgeHp);
			if (pick == 0)
				return LeavePlayerBotSungma(ch, state, dwNow, "sungma_no_map");
			if (pick != res.lMap)
			{
				const int a = GetPlayerBotSungmaSlot(res.lMap), z = GetPlayerBotSungmaSlot(pick);
				sys_log(0, "PLAYERBOT_SUNGMA: move pid=%u name=%s champion=%d will=%d/%d/%d/%d from=%ld to=%ld why=%s",
						pid, ch->GetName(), GetPlayerBotChampionLevel(ch), GetPlayerBotSungmaWill(ch, 0), GetPlayerBotSungmaWill(ch, 1),
						GetPlayerBotSungmaWill(ch, 2), GetPlayerBotSungmaWill(ch, 3), res.lMap, pick,
						!fitsNow ? "unfit" : (z > a ? "up" : "down"));
				if (a >= 0)
				{
					++s_aPlayerBotSungmaStats[a].movesOut;
					--s_aiPlayerBotSungmaMapCensus[a];	// the poll counts the rows again
				}
				if (z >= 0)
				{
					++s_aPlayerBotSungmaStats[z].movesIn;
					++s_aiPlayerBotSungmaMapCensus[z];
				}
				// MT2009_PLUS_BOT_ELEMENT_RESIST_V1: the new map's element prepared before the move - it may wait when it
				// still fits where it stands and is not stepping down after its deaths (playerbot_element_resist.h).
				StartPlayerBotElementPrep(ch, res.lMap, pick, fitsNow && !b.bFlee && GetPlayerBotSungmaSlot(base) >= 0, dwNow);
				res.lMap = pick;
				b.dwWalkSince = 0;
				LeavePlayerBotSungmaParty(ch, "map_move", false);	// MT2009_PLUS_BOT_YOHARA_FIGHT_V1
				char q[160];
				snprintf(q, sizeof(q), "UPDATE common.playerbot_core_handover SET target_map = %ld WHERE pid = %u AND state = 2", pick, pid);
				RunPlayerBotYoharaSql(q);
			}
			else
				b.bFlee = false;	// MT2009_PLUS_BOT_SUNGMA_DEATHS_V1: nowhere lower - a later move walks
		}
		if (base != res.lMap)
		{
			if (!IsPlayerBotMapHostedHere(res.lMap))
				return LeavePlayerBotSungma(ch, state, dwNow, "sungma_not_hosted");
			// MT2009_PLUS_BOT_ELEMENT_RESIST_V1: its gear for the new element first (at most
			// PLAYERBOT_ELEMENT_PREP_MAX_MS, fighting on here meanwhile), then the elixir, then the way.
			if (b.dwWalkSince == 0 && HoldPlayerBotElementPrep(ch, res.lMap, dwNow))
				return 0;	// the fight where it stands (as a loot run's 0), no frontier travel
			return MovePlayerBotSungma(ch, state, b, res.lMap, dwNow);
		}
		b.dwWalkSince = 0;
		b.dwErrandBackSince = 0;	// MT2009_PLUS_BOT_SUNGMA_PARTY_KEEP_V1: back on its map
		// Zejscie: the next room now and then.
		const int slot = GetPlayerBotSungmaSlot(base);
		if (slot >= 0 && PLAYERBOT_SUNGMA_MAPS[slot].bChambered && !ch->GetParty() &&
				dwNow - b.dwChamberSince >= PLAYERBOT_SUNGMA_CHAMBER_MS && state.dwTargetVID == 0 &&
				HopPlayerBotSungmaChamber(ch, slot, b, dwNow, "time"))
			return 1;
		// MT2009_PLUS_BOT_YOHARA_FIGHT_V1: a party's leader with nothing to fight waits for its members to come up.
		if (HoldPlayerBotSungmaRegroup(ch, state, dwNow))
			return 1;
#ifdef MT2009_PLUS_BOT_YOHARA_GUIDES_V1
		if (ManagePlayerBotYoharaBossRoute(ch, state, dwNow) > 0)	// a strong party's leader: the bosses' route
			return 1;
#endif
		return -1;	// the spots (the frontier's hunting)
	}

	// ------------------------------------------------------------ the census

	void LogPlayerBotSungmaCensus(DWORD dwNow)
	{
#ifdef MT2009_PLUS_BOT_YOHARA_GUIDES_V1
		LogPlayerBotYoharaGuidesCensus(dwNow);	// its own clock (half an hour)
#endif
		int here[9] = { 0 }, champSum[9] = { 0 };
		int inParty[9] = { 0 }, lone[9] = { 0 };	// MT2009_PLUS_BOT_YOHARA_FIGHT_V1
		std::set<DWORD> leaders[9];
		int members = 0, membersResting = 0;
		for (std::map<DWORD, TPlayerBotYoharaCohortMember>::const_iterator i = s_mapPlayerBotYoharaCohort.begin();
				i != s_mapPlayerBotYoharaCohort.end(); ++i)
			if (i->second.iPurpose == YOHARA_PURPOSE_SUNGMA)
			{
				++members;
				membersResting += i->second.bResting ? 1 : 0;
			}
		int residents = 0;
		for (std::map<DWORD, TPlayerBotYoharaResident>::const_iterator r = s_mapPlayerBotYoharaResident.begin();
				r != s_mapPlayerBotYoharaResident.end(); ++r)
		{
			if (r->second.iPurpose != YOHARA_PURPOSE_SUNGMA)
				continue;
			++residents;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(r->first);
			const int slot = ch ? GetPlayerBotSungmaSlot(ch->GetMapIndex()) : -1;
			if (slot < 0)
				continue;
			++here[slot];
			champSum[slot] += GetPlayerBotChampionLevel(ch);
			// MT2009_PLUS_BOT_YOHARA_FIGHT_V1: in a party (its leader counted once) or alone
			if (ch->GetParty() && ch->GetParty()->GetMemberCount() >= 2)
			{
				++inParty[slot];
				leaders[slot].insert(ch->GetParty()->GetLeaderPID());
			}
			else
				++lone[slot];
		}
		const bool any = members > 0 || residents > 0 || !s_mapPlayerBotSungmaTradeHome.empty();
		const DWORD span = s_dwPlayerBotSungmaLastCensus ? dwNow - s_dwPlayerBotSungmaLastCensus : 0;
		s_dwPlayerBotSungmaLastCensus = dwNow;
		if (!any)
			return;
		sys_log(0, "PLAYERBOT_SUNGMA: summary channel=%u members=%d resting=%d residents_here=%d channel_census=%d/%d map_max=%d "
				"maps_on=%u trade_away=%d trade_max=%d trade_home=%u trade_home_arrived=%u trade_home_back=%u trade_stranded=%u "
				"exp_rate_bot=%d",
				(unsigned int)g_bChannel, members, membersResting, residents, s_aiPlayerBotYoharaCensus[YOHARA_PURPOSE_SUNGMA],
				GetPlayerBotYoharaConfig().sungmaMax, GetPlayerBotYoharaConfig().sungmaMapMax,
				(unsigned int)GetPlayerBotYoharaConfig().sungmaMaps.size(),
				CountPlayerBotSungmaTradeAway(dwNow), GetPlayerBotYoharaConfig().sungmaTradeMax,	// MT2009_PLUS_BOT_YOHARA_TRADE_TRIP_V1
				(unsigned int)s_mapPlayerBotSungmaTradeHome.size(), s_uPlayerBotSungmaTradeHomeArrived,
				s_uPlayerBotSungmaTradeHomeBack, s_uPlayerBotSungmaTradeStranded,
#ifdef ENABLE_CONQUEROR_LEVEL
				champion::BotExpRatePct()
#else
				0
#endif
				);
		// MT2009_PLUS_BOT_SUNGMA_TRIPS_V1: the trips by what they were for, since the last census
		{
			TPlayerBotSungmaTripStats& t = s_kPlayerBotSungmaTrips;
			sys_log(0, "PLAYERBOT_SUNGMA: trips channel=%u dongan_potions=%u dongan_elixirs=%u tidies=%u tidy_sold=%u "
					"tidy_freed_cells=%d tidy_still_full=%u m1_buy=%u m1_counter=%u m1_refused_%s=%u m1_refused_%s=%u m1_refused_%s=%u "
					"m1_refused_%s=%u m1_refused_%s=%u", (unsigned int)g_bChannel, t.errandPotions, t.errandElixirs, t.tidies,
					t.tidySold, t.tidyFreed, t.tidyStillFull, t.m1Buy, t.m1Counter,
					PLAYERBOT_SUNGMA_M1_REFUSED[0], t.m1Refused[0], PLAYERBOT_SUNGMA_M1_REFUSED[1], t.m1Refused[1],
					PLAYERBOT_SUNGMA_M1_REFUSED[2], t.m1Refused[2], PLAYERBOT_SUNGMA_M1_REFUSED[3], t.m1Refused[3],
					PLAYERBOT_SUNGMA_M1_REFUSED[4], t.m1Refused[4]);
			t = TPlayerBotSungmaTripStats();
		}
		for (int i = 0; i < PLAYERBOT_SUNGMA_MAP_COUNT; ++i)
		{
			TPlayerBotSungmaStats& st = s_aPlayerBotSungmaStats[i];
			if (here[i] == 0 && s_aiPlayerBotSungmaMapCensus[i] == 0 && st.kills == 0 && st.movesIn == 0)
				continue;
			const long long killsH = span > 0 ? (long long)(st.kills - st.killsAtCensus) * 3600000LL / (long long)span : 0;
			const long long expH = span > 0 ? (st.exp - st.expAtCensus) * 3600000LL / (long long)span : 0;
			const long long championExpH = span > 0 ? (st.championExp - st.championExpAtCensus) * 3600000LL / (long long)span : 0;
			sys_log(0, "PLAYERBOT_SUNGMA: census channel=%u map=%ld name=%s here=%d channel_rows=%d avg_champion=%d kills=%u kills_h=%lld "
					"exp=%lld exp_h=%lld champion_exp=%lld champion_exp_h=%lld deaths=%u stuck=%u nav_fail=%u level_ups=%u "
					"champion_ups=%u moves_in=%u moves_out=%u steps_down=%u hops=%u portal_walks=%u portal_warps=%u revives=%u "
					"errands=%u errand_fallbacks=%u trade_trips=%u trade_backs=%u",
					(unsigned int)g_bChannel, PLAYERBOT_SUNGMA_MAPS[i].lMap, PLAYERBOT_SUNGMA_MAPS[i].szKey, here[i],
					s_aiPlayerBotSungmaMapCensus[i], here[i] ? champSum[i] / here[i] : 0, st.kills, killsH, st.exp, expH,
					st.championExp, championExpH, st.deaths, st.stuck, st.navFail, st.levelUps, st.championUps, st.movesIn,
					st.movesOut, st.stepsDown, st.hops, st.portalWalks, st.portalWarps, st.revives, st.errands, st.errandFallbacks,
					st.tradeTrips, st.tradeBacks);
			// MT2009_PLUS_BOT_YOHARA_FIGHT_V1: the map's parties, retreats and deaths by cause
			LogPlayerBotSungmaFightCensus(i, PLAYERBOT_SUNGMA_MAPS[i].lMap, PLAYERBOT_SUNGMA_MAPS[i].szKey, (int)leaders[i].size(),
					inParty[i], lone[i], here[i], st.kills, st.deaths);	// MT2009_PLUS_BOT_SUNGMA_FIGHT2_V1: the fight2 line
			NotePlayerBotSungmaRate(i, st.championExp - st.championExpAtCensus, (long long)here[i] * (long long)span);	// MT2009_PLUS_BOT_TRAINER_MAP_PICK_V1
			st.killsAtCensus = st.kills;
			st.expAtCensus = st.exp;
			st.championExpAtCensus = st.championExp;
		}
		// MT2009_PLUS_BOT_TRAINER_MAP_PICK_V1: the rates the pick reads (champion experience a bot-hour, the window's
		// bot-hours) and the picks they made (down: a lower map than the highest that fits; held: its own map kept)
		{
			char buf[512];
			size_t used = 0;
			for (int i = 0; i < PLAYERBOT_SUNGMA_MAP_COUNT && used + 64 < sizeof(buf); ++i)
			{
				double bh = 0.0;
				const long long rate = GetPlayerBotSungmaRate(i, &bh);
				used += snprintf(buf + used, sizeof(buf) - used, " %s=%lld/%.1fbh/d%u/h%u", PLAYERBOT_SUNGMA_MAPS[i].szKey, rate, bh,
						s_aPlayerBotSungmaRate[i].picksDown, s_aPlayerBotSungmaRate[i].picksHeld);
			}
			sys_log(0, "PLAYERBOT_TRAINER: map rates channel=%u on=%d rearmed=%u rearm_failed=%u revive_busy_refused=%u%s",
					(unsigned int)g_bChannel, IsPlayerBotSungmaRateOff() ? 0 : 1, s_uPlayerBotTrainerRearmed,
					s_uPlayerBotTrainerRearmFailed, s_uPlayerBotTrainerReviveBusyRefused, buf);
		}
	}

#endif
