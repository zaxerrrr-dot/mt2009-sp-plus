#ifndef __INC_METIN2_PLAYERBOT_YOHARA_SPOT_ELEMENT_H__
#define __INC_METIN2_PLAYERBOT_YOHARA_SPOT_ELEMENT_H__

// MT2009_PLUS_BOT_YSPOT_ELEMENT_V1 - within a Sung Ma map a bot hunts the spots of the elements it is dressed for (the
// owner, 7 November 2026: "Na roznych mapach rozne spoty sa na rozne odpornosci, wiec niech bot wybiera takie
// expowisko na mapie, pod jaki zywiol jest ubrany").
//
// The spots' elements (PLAYERBOT_YSPOT_MIX_<map>, row for row the hubs of PLAYERBOT_SUNGMA_HUBS_<map>): the test
// world's spawns (rates-spool spawns/base/maps/<map>/regen.txt - m / g / r lines, the groups of group.*.txt and
// group_group.*.txt, a group_group's groups averaged, the line's count), the ordinary monsters only (type 0, rank under
// the boss), their element by world.mob_proto.setRaceFlag bits 11-16 (the engine's RACE_FLAG_ATT_ELEC..DARK - the
// set's "SAVAGE" is bit 11, ATT_ELEC), each spawn line within 3 000 (a square, the hub's own cluster window) of the
// hub; tools/yohara_bot_spot_elements.py, 7 November 2026. A cell's mask holds a monster's every element (Zejscie's
// monsters carry ice and lightning both: the engine counts the better resistance of the two, ElementsAttackBonus).
// The maps with spots of different mixes: Twierdza (dark 57-100 / ice 0-100), Dongan (fire 34-82 / dark), Namgan
// (wind 30-100, a few spots dark / fire / earth heavy), Yilad (dark / earth 36-64 everywhere - little to choose),
// Wawoz (ice-only and lightning-only spots side by side), Rozpadlina (likewise); Seoganland (earth), Schronienie (ice)
// and Zejscie (ice + lightning on every monster) are one mix everywhere - the score changes nothing there.
//
// 1. The score (AdjustPlayerBotYSpotHubScore, from ChoosePlayerBotHuntingHub after the hunt element's live share,
//    AdjustPlayerBotSungmaHubScore): the damage the spot's monsters deal through the bot's resistances, in percent of
//    their unresisted blow - "taken" = sum over the spot's cells of share x (100 - the best of min(resistance, 80) over
//    the cell's elements); a monster of no element 100. The resistance is the steady one of the talisman's rule
//    (GetPlayerBotYResistSteady: no elixir, the dragon stones' best deck), read every PLAYERBOT_YSPOT_RESIST_MS; a party's
//    members (leader or not) score by the party's average on the map, so the party agrees on its spot. The score is
//    multiplied by (best / taken) ^ (weight / 100), best the lowest "taken" of the map's spots for the same
//    resistances - the best spot keeps its score, a spot hitting twice as hard keeps 66% of it at the default weight
//    60; the density, the bots already there (worth / (1 + others)), the band, the party rule, the avoided spots, the
//    distance and the hunt element's live share all stay as they were. The spot the bot holds now gets
//    + PLAYERBOT_YSPOT_HYSTERESIS_PERCENT (the hysteresis): a re-choice moves it only for a clearly better spot.
// 2. The re-choice: the hub choice's own clock (the 4-minute stick, the move on when the spot is fought out - that
//    one leaves the spot held out); and the gear's change - the tick (every PLAYERBOT_YSPOT_TICK_MS) compares the
//    resistances (the party's) of the map's elements with those at the pick: PLAYERBOT_YSPOT_GEAR_DELTA or more in
//    any one, at most once every PLAYERBOT_YSPOT_GEAR_GAP_MS, ends the stick (the hysteresis still holds the spot).
// 3. The talisman and the spot - one direction: the bot DRESSES FOR THE MAP and HUNTS THE SPOTS IT IS DRESSED FOR.
//    The gear and the talisman stay the map's (playerbot_element_resist.h: the hunt element, up the maps only;
//    playerbot_yohara_resist_hp.h: the talisman where its line saves the most on the map's shares, the gate's element
//    on Wawoz) - slow, paid in stones, with their own hysteresis; the spot reads what the bot wears now - cheap, free,
//    every few minutes. The other way round (the talisman for the spots it hunts) locks a bot in: a lightning bot on
//    Wawoz would hunt the lightning spots, see no ice there, keep the talisman off ice and never meet the gate or the
//    ice half of the map; the map's talisman widens what the bot can hunt and spreads the crowd. The spot's score
//    never feeds the talisman's choice; the talisman's change (its reroll) reaches the spot through (2).
//
// Switches (event flags, read every 5 s): m2_bot_yspot_off (1: the spots as before - no score, no re-choice),
// m2_bot_yspot_weight (over 0: the weight in percent, to 200; default 60), m2_bot_yspot_hyst (over 0: the
// hysteresis in percent, to 100; default 20; -1: none).
// The log: PLAYERBOT_YSPOT - "pick" (a bot's new spot, throttled), "gear" (a re-choice by the gear, throttled),
// "census" (every 10 minutes: per map the spots and their mixes, the bots on each, the "taken" of their spots against
// the best of the map for them, and the window's picks, re-picks, gear re-choices and the moves they made).
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_yohara_resist_hp.h, in the anonymous
// namespace; the declarations the earlier fragments use are in playerbot_types.h.

namespace
{
	// An element mask (bit 0 lightning, 1 fire, 2 ice, 3 wind, 4 earth, 5 dark - PLAYERBOT_YOHARA_ELEMENT_NAMES' order)
	// and its percent of the spot's ordinary monsters.
	struct TPlayerBotYSpotMixCell { BYTE bMask; BYTE bPct; };
	struct TPlayerBotYSpotMix { long x, y; TPlayerBotYSpotMixCell a[4]; };	// x 0: a boss row

	// tools/yohara_bot_spot_elements.py (7 November 2026, the test world's spawns and world.mob_proto)
	// map 374 (metin2_map_empirecastle): the whole map dark 67, ice 33
	const TPlayerBotYSpotMix PLAYERBOT_YSPOT_MIX_374[] = {
		{ 534550, 501650, { { 32, 62 }, { 4, 38 }, { 0, 0 }, { 0, 0 } } },	// 0: dark 62, ice 38
		{ 540850, 501650, { { 32, 57 }, { 4, 43 }, { 0, 0 }, { 0, 0 } } },	// 1: dark 57, ice 43
		{ 547850, 504350, { { 32, 88 }, { 4, 12 }, { 0, 0 }, { 0, 0 } } },	// 2: dark 88, ice 12
		{ 525450, 501650, { { 32, 71 }, { 4, 29 }, { 0, 0 }, { 0, 0 } } },	// 3: dark 71, ice 29
		{ 533650, 509550, { { 4, 62 }, { 32, 38 }, { 0, 0 }, { 0, 0 } } },	// 4: ice 62, dark 38
		{ 553150, 499550, { { 32, 86 }, { 4, 14 }, { 0, 0 }, { 0, 0 } } },	// 5: dark 86, ice 14
		{ 542750, 511250, { { 32, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 6: dark 100
		{ 554150, 504450, { { 32, 74 }, { 4, 26 }, { 0, 0 }, { 0, 0 } } },	// 7: dark 74, ice 26
		{ 549850, 511050, { { 32, 80 }, { 4, 20 }, { 0, 0 }, { 0, 0 } } },	// 8: dark 80, ice 20
		{ 560450, 508150, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 9: ice 100
		{ 548850, 523450, { { 32, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 10: dark 100
		{ 524850, 523450, { { 32, 69 }, { 4, 31 }, { 0, 0 }, { 0, 0 } } },	// 11: dark 69, ice 31
		{ 530850, 526750, { { 4, 52 }, { 32, 48 }, { 0, 0 }, { 0, 0 } } },	// 12: ice 52, dark 48
		{ 543650, 528650, { { 32, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 13: dark 100
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 14: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 15: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 16: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 17: a boss
	};
	// map 373 (metin2_map_eastplain_01): the whole map fire 52, dark 48
	const TPlayerBotYSpotMix PLAYERBOT_YSPOT_MIX_373[] = {
		{ 1114550, 507550, { { 2, 65 }, { 32, 35 }, { 0, 0 }, { 0, 0 } } },	// 0: fire 65, dark 35
		{ 1090550, 501950, { { 32, 55 }, { 2, 45 }, { 0, 0 }, { 0, 0 } } },	// 1: dark 55, fire 45
		{ 1101450, 492650, { { 2, 52 }, { 32, 48 }, { 0, 0 }, { 0, 0 } } },	// 2: fire 52, dark 48
		{ 1084250, 515850, { { 2, 51 }, { 32, 49 }, { 0, 0 }, { 0, 0 } } },	// 3: fire 51, dark 49
		{ 1122050, 517050, { { 2, 56 }, { 32, 44 }, { 0, 0 }, { 0, 0 } } },	// 4: fire 56, dark 44
		{ 1080350, 496850, { { 2, 64 }, { 32, 36 }, { 0, 0 }, { 0, 0 } } },	// 5: fire 64, dark 36
		{ 1120350, 524350, { { 2, 74 }, { 32, 26 }, { 0, 0 }, { 0, 0 } } },	// 6: fire 74, dark 26
		{ 1067950, 516050, { { 2, 64 }, { 32, 36 }, { 0, 0 }, { 0, 0 } } },	// 7: fire 64, dark 36
		{ 1124850, 537750, { { 2, 60 }, { 32, 40 }, { 0, 0 }, { 0, 0 } } },	// 8: fire 60, dark 40
		{ 1064450, 500650, { { 32, 60 }, { 2, 40 }, { 0, 0 }, { 0, 0 } } },	// 9: dark 60, fire 40
		{ 1140950, 515950, { { 2, 60 }, { 32, 40 }, { 0, 0 }, { 0, 0 } } },	// 10: fire 60, dark 40
		{ 1061550, 492250, { { 2, 59 }, { 32, 41 }, { 0, 0 }, { 0, 0 } } },	// 11: fire 59, dark 41
		{ 1065050, 529350, { { 32, 50 }, { 2, 50 }, { 0, 0 }, { 0, 0 } } },	// 12: dark 50, fire 50
		{ 1057250, 509650, { { 2, 60 }, { 32, 40 }, { 0, 0 }, { 0, 0 } } },	// 13: fire 60, dark 40
		{ 1074050, 543550, { { 2, 64 }, { 32, 36 }, { 0, 0 }, { 0, 0 } } },	// 14: fire 64, dark 36
		{ 1055950, 517250, { { 2, 82 }, { 32, 18 }, { 0, 0 }, { 0, 0 } } },	// 15: fire 82, dark 18
		{ 1059050, 532250, { { 32, 60 }, { 2, 40 }, { 0, 0 }, { 0, 0 } } },	// 16: dark 60, fire 40
		{ 1064750, 541950, { { 2, 51 }, { 32, 49 }, { 0, 0 }, { 0, 0 } } },	// 17: fire 51, dark 49
		{ 1138350, 544150, { { 2, 62 }, { 32, 38 }, { 0, 0 }, { 0, 0 } } },	// 18: fire 62, dark 38
		{ 1123050, 556350, { { 32, 66 }, { 2, 34 }, { 0, 0 }, { 0, 0 } } },	// 19: dark 66, fire 34
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 20: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 21: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 22: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 23: a boss
	};
	// map 376 (metin2_map_eastplain_02): the whole map earth 100
	const TPlayerBotYSpotMix PLAYERBOT_YSPOT_MIX_376[] = {
		{ 1215650, 504050, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 0: earth 100
		{ 1210050, 497750, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 1: earth 100
		{ 1220050, 509750, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 2: earth 100
		{ 1205650, 511450, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 3: earth 100
		{ 1193550, 495350, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 4: earth 100
		{ 1198850, 509650, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 5: earth 100
		{ 1191950, 487550, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 6: earth 100
		{ 1183750, 484350, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 7: earth 100
		{ 1212750, 533450, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 8: earth 100
		{ 1193650, 528450, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 9: earth 100
		{ 1176150, 484550, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 10: earth 100
		{ 1202050, 535150, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 11: earth 100
		{ 1171650, 491950, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 12: earth 100
		{ 1193950, 535350, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 13: earth 100
		{ 1199650, 542550, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 14: earth 100
		{ 1167250, 487350, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 15: earth 100
		{ 1192850, 542150, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 16: earth 100
		{ 1185250, 538450, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 17: earth 100
		{ 1164550, 507950, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 18: earth 100
		{ 1163950, 542250, { { 16, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 19: earth 100
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 20: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 21: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 22: a boss
	};
	// map 377 (metin2_map_eastplain_03): the whole map wind 83, dark 8, fire 5, earth 4
	const TPlayerBotYSpotMix PLAYERBOT_YSPOT_MIX_377[] = {
		{ 1285850, 443350, { { 8, 42 }, { 32, 29 }, { 2, 29 }, { 0, 0 } } },	// 0: wind 42, dark 29, fire 29
		{ 1273550, 444650, { { 8, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 1: wind 100
		{ 1277850, 450750, { { 8, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 2: wind 100
		{ 1262850, 453550, { { 8, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 3: wind 100
		{ 1293250, 459950, { { 8, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 4: wind 100
		{ 1287550, 463450, { { 8, 88 }, { 16, 12 }, { 0, 0 }, { 0, 0 } } },	// 5: wind 88, earth 12
		{ 1301350, 452950, { { 8, 50 }, { 16, 50 }, { 0, 0 }, { 0, 0 } } },	// 6: wind 50, earth 50
		{ 1255550, 447250, { { 8, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 7: wind 100
		{ 1300250, 461750, { { 8, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 8: wind 100
		{ 1250350, 444150, { { 8, 90 }, { 32, 8 }, { 2, 2 }, { 0, 0 } } },	// 9: wind 90, dark 8, fire 2
		{ 1293750, 468050, { { 8, 91 }, { 16, 9 }, { 0, 0 }, { 0, 0 } } },	// 10: wind 91, earth 9
		{ 1313550, 449750, { { 8, 55 }, { 32, 28 }, { 2, 17 }, { 0, 0 } } },	// 11: wind 55, dark 28, fire 17
		{ 1297150, 472650, { { 8, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 12: wind 100
		{ 1307750, 464050, { { 8, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 13: wind 100
		{ 1254350, 467250, { { 8, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 14: wind 100
		{ 1243150, 443350, { { 8, 71 }, { 16, 18 }, { 2, 6 }, { 32, 5 } } },	// 15: wind 71, earth 18, fire 6, dark 5
		{ 1318250, 456250, { { 32, 51 }, { 8, 30 }, { 2, 19 }, { 0, 0 } } },	// 16: dark 52, wind 30, fire 19
		{ 1247950, 470550, { { 8, 82 }, { 16, 18 }, { 0, 0 }, { 0, 0 } } },	// 17: wind 82, earth 18
		{ 1318050, 463350, { { 8, 76 }, { 32, 17 }, { 2, 7 }, { 0, 0 } } },	// 18: wind 76, dark 17, fire 7
		{ 1323750, 452250, { { 8, 40 }, { 32, 36 }, { 2, 24 }, { 0, 0 } } },	// 19: wind 40, dark 36, fire 24
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 20: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 21: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 22: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 23: a boss
	};
	// map 385 (metin2_map_snakevalley): the whole map dark 50, earth 50
	const TPlayerBotYSpotMix PLAYERBOT_YSPOT_MIX_385[] = {
		{ 44250, 1428250, { { 32, 55 }, { 16, 45 }, { 0, 0 }, { 0, 0 } } },	// 0: dark 55, earth 45
		{ 30550, 1434550, { { 32, 50 }, { 16, 50 }, { 0, 0 }, { 0, 0 } } },	// 1: dark 50, earth 50
		{ 18950, 1431450, { { 16, 52 }, { 32, 48 }, { 0, 0 }, { 0, 0 } } },	// 2: earth 52, dark 48
		{ 48750, 1433450, { { 32, 60 }, { 16, 40 }, { 0, 0 }, { 0, 0 } } },	// 3: dark 60, earth 40
		{ 65450, 1425050, { { 16, 60 }, { 32, 40 }, { 0, 0 }, { 0, 0 } } },	// 4: earth 60, dark 40
		{ 20650, 1451050, { { 16, 60 }, { 32, 40 }, { 0, 0 }, { 0, 0 } } },	// 5: earth 60, dark 40
		{ 68250, 1437250, { { 32, 50 }, { 16, 50 }, { 0, 0 }, { 0, 0 } } },	// 6: dark 50, earth 50
		{ 23450, 1457350, { { 32, 50 }, { 16, 50 }, { 0, 0 }, { 0, 0 } } },	// 7: dark 50, earth 50
		{ 62850, 1448450, { { 16, 56 }, { 32, 44 }, { 0, 0 }, { 0, 0 } } },	// 8: earth 56, dark 44
		{ 42750, 1459450, { { 32, 55 }, { 16, 45 }, { 0, 0 }, { 0, 0 } } },	// 9: dark 55, earth 45
		{ 75150, 1433650, { { 16, 58 }, { 32, 42 }, { 0, 0 }, { 0, 0 } } },	// 10: earth 58, dark 42
		{ 26050, 1464250, { { 16, 50 }, { 32, 50 }, { 0, 0 }, { 0, 0 } } },	// 11: earth 50, dark 50
		{ 84650, 1434150, { { 32, 50 }, { 16, 50 }, { 0, 0 }, { 0, 0 } } },	// 12: dark 50, earth 50
		{ 92450, 1437350, { { 16, 53 }, { 32, 47 }, { 0, 0 }, { 0, 0 } } },	// 13: earth 53, dark 47
		{ 100150, 1437450, { { 32, 56 }, { 16, 44 }, { 0, 0 }, { 0, 0 } } },	// 14: dark 56, earth 44
		{ 98050, 1455450, { { 16, 62 }, { 32, 38 }, { 0, 0 }, { 0, 0 } } },	// 15: earth 62, dark 38
		{ 108550, 1455850, { { 16, 64 }, { 32, 36 }, { 0, 0 }, { 0, 0 } } },	// 16: earth 64, dark 36
		{ 119750, 1435050, { { 16, 54 }, { 32, 46 }, { 0, 0 }, { 0, 0 } } },	// 17: earth 54, dark 46
		{ 117650, 1459850, { { 16, 56 }, { 32, 44 }, { 0, 0 }, { 0, 0 } } },	// 18: earth 56, dark 44
		{ 115250, 1468050, { { 32, 58 }, { 16, 42 }, { 0, 0 }, { 0, 0 } } },	// 19: dark 58, earth 42
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 20: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 21: a boss
	};
	// map 388 (metin2_map_icecrystalcave): the whole map ice 50, lightning 50
	const TPlayerBotYSpotMix PLAYERBOT_YSPOT_MIX_388[] = {
		{ 94950, 1594250, { { 1, 67 }, { 4, 33 }, { 0, 0 }, { 0, 0 } } },	// 0: lightning 67, ice 33
		{ 99450, 1582350, { { 1, 62 }, { 4, 38 }, { 0, 0 }, { 0, 0 } } },	// 1: lightning 62, ice 38
		{ 80650, 1587350, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 2: ice 100
		{ 80950, 1576550, { { 4, 60 }, { 1, 40 }, { 0, 0 }, { 0, 0 } } },	// 3: ice 60, lightning 40
		{ 93550, 1562650, { { 1, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 4: lightning 100
		{ 52650, 1583350, { { 1, 71 }, { 4, 29 }, { 0, 0 }, { 0, 0 } } },	// 5: lightning 71, ice 29
		{ 87950, 1542250, { { 1, 71 }, { 4, 29 }, { 0, 0 }, { 0, 0 } } },	// 6: lightning 71, ice 29
		{ 95850, 1533250, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 7: ice 100
		{ 85950, 1535750, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 8: ice 100
		{ 46450, 1574250, { { 1, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 9: lightning 100
		{ 40850, 1583850, { { 1, 60 }, { 4, 40 }, { 0, 0 }, { 0, 0 } } },	// 10: lightning 60, ice 40
		{ 59450, 1547450, { { 1, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 11: lightning 100
		{ 36450, 1594250, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 12: ice 100
		{ 76650, 1528550, { { 4, 83 }, { 1, 17 }, { 0, 0 }, { 0, 0 } } },	// 13: ice 83, lightning 17
		{ 84450, 1524750, { { 1, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 14: lightning 100
		{ 46550, 1549850, { { 1, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 15: lightning 100
		{ 40350, 1557050, { { 1, 80 }, { 4, 20 }, { 0, 0 }, { 0, 0 } } },	// 16: lightning 80, ice 20
		{ 31150, 1567750, { { 4, 80 }, { 1, 20 }, { 0, 0 }, { 0, 0 } } },	// 17: ice 80, lightning 20
		{ 22750, 1583050, { { 1, 83 }, { 4, 17 }, { 0, 0 }, { 0, 0 } } },	// 18: lightning 83, ice 17
		{ 30450, 1544250, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 19: ice 100
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 20: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 21: a boss
	};
	// map 389 (metin2_map_whitdragonvalley): the whole map ice 56, lightning 44
	const TPlayerBotYSpotMix PLAYERBOT_YSPOT_MIX_389[] = {
		{ 185450, 1565350, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 0: ice 100
		{ 184050, 1557150, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 1: ice 100
		{ 173350, 1557450, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 2: ice 100
		{ 173550, 1546150, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 3: ice 100
		{ 163250, 1549250, { { 1, 75 }, { 4, 25 }, { 0, 0 }, { 0, 0 } } },	// 4: lightning 75, ice 25
		{ 155250, 1556050, { { 1, 67 }, { 4, 33 }, { 0, 0 }, { 0, 0 } } },	// 5: lightning 67, ice 33
		{ 185950, 1540050, { { 1, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 6: lightning 100
		{ 171650, 1538450, { { 1, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 7: lightning 100
		{ 152550, 1546650, { { 4, 67 }, { 1, 33 }, { 0, 0 }, { 0, 0 } } },	// 8: ice 67, lightning 33
		{ 188550, 1533250, { { 1, 50 }, { 4, 50 }, { 0, 0 }, { 0, 0 } } },	// 9: lightning 50, ice 50
		{ 158650, 1538750, { { 4, 87 }, { 1, 13 }, { 0, 0 }, { 0, 0 } } },	// 10: ice 87, lightning 13
		{ 169950, 1531950, { { 1, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 11: lightning 100
		{ 140750, 1553750, { { 4, 80 }, { 1, 20 }, { 0, 0 }, { 0, 0 } } },	// 12: ice 80, lightning 20
		{ 151650, 1536350, { { 1, 67 }, { 4, 33 }, { 0, 0 }, { 0, 0 } } },	// 13: lightning 67, ice 33
		{ 184350, 1524650, { { 4, 71 }, { 1, 29 }, { 0, 0 }, { 0, 0 } } },	// 14: ice 71, lightning 29
		{ 175150, 1521850, { { 4, 67 }, { 1, 33 }, { 0, 0 }, { 0, 0 } } },	// 15: ice 67, lightning 33
		{ 163550, 1522550, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 16: ice 100
		{ 146350, 1528550, { { 4, 75 }, { 1, 25 }, { 0, 0 }, { 0, 0 } } },	// 17: ice 75, lightning 25
		{ 155550, 1522350, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 18: ice 100
		{ 139250, 1528350, { { 1, 60 }, { 4, 40 }, { 0, 0 }, { 0, 0 } } },	// 19: lightning 60, ice 40
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 20: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 21: a boss
	};
	// map 393 (metin2_map_whitedragoncave_01): the whole map ice 100
	const TPlayerBotYSpotMix PLAYERBOT_YSPOT_MIX_393[] = {
		{ 1018650, 1305050, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 0: ice 100
		{ 1039450, 1244350, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 1: ice 100
		{ 1021750, 1224550, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 2: ice 100
		{ 1038650, 1224550, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 3: ice 100
		{ 1044550, 1306050, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 4: ice 100
		{ 1017450, 1321950, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 5: ice 100
		{ 1054150, 1233150, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 6: ice 100
		{ 1069350, 1288550, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 7: ice 100
		{ 1005050, 1336350, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 8: ice 100
		{ 1035250, 1337050, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 9: ice 100
		{ 1082350, 1213450, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 10: ice 100
		{ 1075150, 1336350, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 11: ice 100
		{ 1104050, 1239350, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 12: ice 100
		{ 1087250, 1337150, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 13: ice 100
		{ 1100550, 1322550, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 14: ice 100
		{ 1119950, 1300450, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 15: ice 100
		{ 1119550, 1213650, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 16: ice 100
		{ 1129850, 1227350, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 17: ice 100
		{ 1146650, 1212750, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 18: ice 100
		{ 1146450, 1337250, { { 4, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 19: ice 100
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 20: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 21: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 22: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 23: a boss
	};
	// map 394 (metin2_map_whitedragoncave_02): the whole map lightning+ice 100
	const TPlayerBotYSpotMix PLAYERBOT_YSPOT_MIX_394[] = {
		{ 1161150, 1210550, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 0: lightning+ice 100
		{ 1169850, 1210750, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 1: lightning+ice 100
		{ 1166850, 1236650, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 2: lightning+ice 100
		{ 1184850, 1211150, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 3: lightning+ice 100
		{ 1174250, 1243150, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 4: lightning+ice 100
		{ 1167650, 1247050, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 5: lightning+ice 100
		{ 1191650, 1211050, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 6: lightning+ice 100
		{ 1193550, 1217650, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 7: lightning+ice 100
		{ 1199150, 1220850, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 8: lightning+ice 100
		{ 1191550, 1241950, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 9: lightning+ice 100
		{ 1158950, 1261650, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 10: lightning+ice 100
		{ 1165950, 1261550, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 11: lightning+ice 100
		{ 1173350, 1262650, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 12: lightning+ice 100
		{ 1209150, 1219050, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 13: lightning+ice 100
		{ 1208950, 1211850, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 14: lightning+ice 100
		{ 1210750, 1236150, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 15: lightning+ice 100
		{ 1169950, 1272550, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 16: lightning+ice 100
		{ 1215250, 1209550, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 17: lightning+ice 100
		{ 1214750, 1245850, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 18: lightning+ice 100
		{ 1219050, 1235650, { { 5, 100 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 19: lightning+ice 100
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 20: a boss
		{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },	// 21: a boss
	};

	struct TPlayerBotYSpotMap { long lMap; const TPlayerBotYSpotMix* pRows; int iRows; };
#define PLAYERBOT_YSPOT_MAP(m) { m, PLAYERBOT_YSPOT_MIX_##m, (int)(sizeof(PLAYERBOT_YSPOT_MIX_##m) / sizeof(PLAYERBOT_YSPOT_MIX_##m[0])) }
	const TPlayerBotYSpotMap PLAYERBOT_YSPOT_MAPS[] = {
		PLAYERBOT_YSPOT_MAP(374), PLAYERBOT_YSPOT_MAP(373), PLAYERBOT_YSPOT_MAP(376), PLAYERBOT_YSPOT_MAP(377),
		PLAYERBOT_YSPOT_MAP(385), PLAYERBOT_YSPOT_MAP(388), PLAYERBOT_YSPOT_MAP(389), PLAYERBOT_YSPOT_MAP(393),
		PLAYERBOT_YSPOT_MAP(394),
	};
#undef PLAYERBOT_YSPOT_MAP
	const int PLAYERBOT_YSPOT_MAP_COUNT = (int)(sizeof(PLAYERBOT_YSPOT_MAPS) / sizeof(PLAYERBOT_YSPOT_MAPS[0]));
	// row for row the hubs: a hub table changed without the tool fails here
#define PLAYERBOT_YSPOT_ROWS_MATCH(m) static_assert(sizeof(PLAYERBOT_YSPOT_MIX_##m) / sizeof(PLAYERBOT_YSPOT_MIX_##m[0]) == \
		sizeof(PLAYERBOT_SUNGMA_HUBS_##m) / sizeof(PLAYERBOT_SUNGMA_HUBS_##m[0]), "PLAYERBOT_YSPOT_MIX_" #m " rows != hubs");
	PLAYERBOT_YSPOT_ROWS_MATCH(374) PLAYERBOT_YSPOT_ROWS_MATCH(373) PLAYERBOT_YSPOT_ROWS_MATCH(376)
	PLAYERBOT_YSPOT_ROWS_MATCH(377) PLAYERBOT_YSPOT_ROWS_MATCH(385) PLAYERBOT_YSPOT_ROWS_MATCH(388)
	PLAYERBOT_YSPOT_ROWS_MATCH(389) PLAYERBOT_YSPOT_ROWS_MATCH(393) PLAYERBOT_YSPOT_ROWS_MATCH(394)
#undef PLAYERBOT_YSPOT_ROWS_MATCH

	const int PLAYERBOT_YSPOT_WEIGHT_DEFAULT = 60;
	const int PLAYERBOT_YSPOT_WEIGHT_MAX = 200;
	const int PLAYERBOT_YSPOT_HYSTERESIS_PERCENT = 20;
	const int PLAYERBOT_YSPOT_GEAR_DELTA = 5;
	const DWORD PLAYERBOT_YSPOT_FLAGS_MS = 5000;
	const DWORD PLAYERBOT_YSPOT_RESIST_MS = 20 * 1000;
	const DWORD PLAYERBOT_YSPOT_TICK_MS = 20 * 1000;
	const DWORD PLAYERBOT_YSPOT_GEAR_GAP_MS = 3 * 60 * 1000;
	const DWORD PLAYERBOT_YSPOT_GEAR_MOVE_MS = 60 * 1000;	// a new spot this soon after the gear's re-choice is its move
	const DWORD PLAYERBOT_YSPOT_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_YSPOT_SEEN_MS = 5 * 60 * 1000;

	struct TPlayerBotYSpotFlags
	{
		DWORD dwAt;
		bool bOff;
		int iWeight, iHyst;
		TPlayerBotYSpotFlags() : dwAt(0), bOff(false), iWeight(PLAYERBOT_YSPOT_WEIGHT_DEFAULT), iHyst(PLAYERBOT_YSPOT_HYSTERESIS_PERCENT) {}
	};
	TPlayerBotYSpotFlags s_kPlayerBotYSpotFlags;

	const TPlayerBotYSpotFlags& GetPlayerBotYSpotFlags()
	{
		TPlayerBotYSpotFlags& f = s_kPlayerBotYSpotFlags;
		const DWORD now = get_dword_time();
		if (f.dwAt != 0 && now - f.dwAt < PLAYERBOT_YSPOT_FLAGS_MS)
			return f;
		f.dwAt = now ? now : 1;
		quest::CQuestManager& q = quest::CQuestManager::instance();
		f.bOff = q.GetEventFlag("m2_bot_yspot_off") != 0;
		const int w = q.GetEventFlag("m2_bot_yspot_weight");
		f.iWeight = w > 0 ? std::min(w, PLAYERBOT_YSPOT_WEIGHT_MAX) : PLAYERBOT_YSPOT_WEIGHT_DEFAULT;
		const int h = q.GetEventFlag("m2_bot_yspot_hyst");
		f.iHyst = h > 0 ? std::min(h, 100) : (h < 0 ? 0 : PLAYERBOT_YSPOT_HYSTERESIS_PERCENT);
		return f;
	}

	struct TPlayerBotYSpotBot
	{
		DWORD dwResistAt;
		int aiResist[PLAYERBOT_YOHARA_ELEMENTS];	// own, steady, capped
		DWORD dwNextTick, dwSeen;
		long lSeenMap;
		// the spot held: its map (base), its row; the resistances (the party's) it was picked with
		long lSpotMap;
		int iSpot;
		int aiPick[PLAYERBOT_YOHARA_ELEMENTS];
		DWORD dwPickAt, dwGearAt;
		// the hub choice's round (one dwNow): the resistances it scores with, the best "taken" among its candidates
		DWORD dwRoundAt;
		int aiRound[PLAYERBOT_YOHARA_ELEMENTS];
		int iRoundBest;
		TPlayerBotYSpotBot() : dwResistAt(0), dwNextTick(0), dwSeen(0), lSeenMap(0), lSpotMap(0), iSpot(-1), dwPickAt(0),
			dwGearAt(0), dwRoundAt(0), iRoundBest(101)
		{
			for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
				aiResist[e] = aiPick[e] = aiRound[e] = 0;
		}
	};
	std::map<DWORD, TPlayerBotYSpotBot> s_mapPlayerBotYSpot;

	// The census window's counts, a map a slot.
	struct TPlayerBotYSpotStats
	{
		unsigned int picks, repicks, gearLooks, gearMoves;
		long long sumChosen, sumBest;
		TPlayerBotYSpotStats() : picks(0), repicks(0), gearLooks(0), gearMoves(0), sumChosen(0), sumBest(0) {}
	};
	TPlayerBotYSpotStats s_aPlayerBotYSpotStats[PLAYERBOT_YSPOT_MAP_COUNT];
	DWORD s_dwPlayerBotYSpotCensusAt = 0;

	int GetPlayerBotYSpotSlot(long mapIndex)
	{
		const long base = GetPlayerBotYResistBase(mapIndex);
		for (int i = 0; i < PLAYERBOT_YSPOT_MAP_COUNT; ++i)
			if (PLAYERBOT_YSPOT_MAPS[i].lMap == base)
				return i;
		return -1;
	}

	int FindPlayerBotYSpotRow(int slot, long x, long y)
	{
		if (slot < 0 || (x == 0 && y == 0))
			return -1;
		const TPlayerBotYSpotMap& m = PLAYERBOT_YSPOT_MAPS[slot];
		for (int i = 0; i < m.iRows; ++i)
			if (m.pRows[i].x == x && m.pRows[i].y == y)
				return i;
		return -1;
	}

	// The spot's "taken": percent of the unresisted blow its monsters deal through r (capped); -1 a boss row.
	int GetPlayerBotYSpotTaken(const TPlayerBotYSpotMix& s, const int r[PLAYERBOT_YOHARA_ELEMENTS])
	{
		int sum = 0, total = 0;
		for (int c = 0; c < 4; ++c)
		{
			const int pct = s.a[c].bPct;
			if (pct <= 0)
				continue;
			int best = 0;
			for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
				if (s.a[c].bMask & (1 << e))
					best = std::max(best, std::min(r[e], PLAYERBOT_YRESIST_CAP));
			sum += pct * (100 - best);
			total += pct;
		}
		return total > 0 ? (sum + total / 2) / total : -1;
	}

	// The lowest "taken" of the map's spots for r; 100 none.
	int GetPlayerBotYSpotMapBest(int slot, const int r[PLAYERBOT_YOHARA_ELEMENTS])
	{
		int best = 100;
		const TPlayerBotYSpotMap& m = PLAYERBOT_YSPOT_MAPS[slot];
		for (int i = 0; i < m.iRows; ++i)
		{
			const int t = GetPlayerBotYSpotTaken(m.pRows[i], r);
			if (t >= 0)
				best = std::min(best, t);
		}
		return best;
	}

	// The map's elements (the union of its cells' masks).
	int GetPlayerBotYSpotMapMask(int slot)
	{
		int mask = 0;
		const TPlayerBotYSpotMap& m = PLAYERBOT_YSPOT_MAPS[slot];
		for (int i = 0; i < m.iRows; ++i)
			for (int c = 0; c < 4; ++c)
				if (m.pRows[i].a[c].bPct > 0)
					mask |= m.pRows[i].a[c].bMask;
		return mask;
	}

	// The bot's own steady, capped resistances (re-read every PLAYERBOT_YSPOT_RESIST_MS).
	const int* GetPlayerBotYSpotOwnResist(LPCHARACTER ch, DWORD dwNow)
	{
		TPlayerBotYSpotBot& b = s_mapPlayerBotYSpot[ch->GetPlayerID()];
		if (b.dwResistAt == 0 || dwNow - b.dwResistAt >= PLAYERBOT_YSPOT_RESIST_MS)
		{
			b.dwResistAt = dwNow ? dwNow : 1;
			for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
				b.aiResist[e] = std::min(GetPlayerBotYResistSteady(ch, e), PLAYERBOT_YRESIST_CAP);
		}
		return b.aiResist;
	}

	struct FSumPlayerBotYSpotResist
	{
		DWORD m_now;
		int m_count;
		long m_sum[PLAYERBOT_YOHARA_ELEMENTS];
		explicit FSumPlayerBotYSpotResist(DWORD now) : m_now(now), m_count(0)
		{
			for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
				m_sum[e] = 0;
		}
		void operator()(LPCHARACTER member)
		{
			if (!member || !member->IsPC() || !member->IsItemLoaded())
				return;
			const int* r = GetPlayerBotYSpotOwnResist(member, m_now);
			for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
				m_sum[e] += r[e];
			++m_count;
		}
	};

	// The resistances a spot is scored with: the party's average on the map (two members or more), else the bot's own.
	void GetPlayerBotYSpotResist(LPCHARACTER ch, DWORD dwNow, int out[PLAYERBOT_YOHARA_ELEMENTS])
	{
		LPPARTY party = ch->GetParty();
		if (party && party->GetMemberCount() >= 2)
		{
			FSumPlayerBotYSpotResist f(dwNow);
			party->ForEachOnMapMember(f, ch->GetMapIndex());
			if (f.m_count >= 2)
			{
				for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
					out[e] = (int)(f.m_sum[e] / f.m_count);
				return;
			}
		}
		const int* r = GetPlayerBotYSpotOwnResist(ch, dwNow);
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			out[e] = r[e];
	}

	void FormatPlayerBotYSpotResist(const int r[PLAYERBOT_YOHARA_ELEMENTS], int mask, char* buf, size_t size)
	{
		static const char s_acCode[PLAYERBOT_YOHARA_ELEMENTS] = { 'L', 'F', 'I', 'W', 'E', 'D' };
		size_t n = 0;
		buf[0] = 0;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS && n + 8 < size; ++e)
			if (mask & (1 << e))
				n += snprintf(buf + n, size - n, "%s%c%d", n ? "," : "", s_acCode[e], r[e]);
		if (n == 0)
			snprintf(buf, size, "-");
	}

	void FormatPlayerBotYSpotMix(const TPlayerBotYSpotMix& s, char* buf, size_t size)
	{
		static const char s_acCode[PLAYERBOT_YOHARA_ELEMENTS] = { 'L', 'F', 'I', 'W', 'E', 'D' };
		size_t n = 0;
		buf[0] = 0;
		for (int c = 0; c < 4 && n + 12 < size; ++c)
		{
			if (s.a[c].bPct <= 0)
				continue;
			for (int e = 0, first = 1; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
				if (s.a[c].bMask & (1 << e))
				{
					n += snprintf(buf + n, size - n, "%s%c", first ? "" : "+", s_acCode[e]);
					first = 0;
				}
			if (s.a[c].bMask == 0)
				n += snprintf(buf + n, size - n, "N");
			n += snprintf(buf + n, size - n, "%d", (int)s.a[c].bPct);
		}
	}

	// (1) ChoosePlayerBotHuntingHub's score of an ordinary Sung Ma spot.
	int AdjustPlayerBotYSpotHubScore(LPCHARACTER ch, long x, long y, int score, DWORD dwNow)
	{
		if (!ch || !ch->IsPC() || score <= 0)
			return score;
		const TPlayerBotYSpotFlags& f = GetPlayerBotYSpotFlags();
		if (f.bOff)
			return score;
		const int slot = GetPlayerBotYSpotSlot(ch->GetMapIndex());
		const int row = FindPlayerBotYSpotRow(slot, x, y);
		if (row < 0)
			return score;
		TPlayerBotYSpotBot& b = s_mapPlayerBotYSpot[ch->GetPlayerID()];
		if (b.dwRoundAt != dwNow || dwNow == 0)
		{
			b.dwRoundAt = dwNow;
			b.iRoundBest = 101;
			GetPlayerBotYSpotResist(ch, dwNow, b.aiRound);
		}
		const int taken = GetPlayerBotYSpotTaken(PLAYERBOT_YSPOT_MAPS[slot].pRows[row], b.aiRound);
		if (taken <= 0)
			return score;
		b.iRoundBest = std::min(b.iRoundBest, taken);
		const int best = std::max(1, GetPlayerBotYSpotMapBest(slot, b.aiRound));
		double adjusted = (double)score;
		if (taken > best)
			adjusted *= pow((double)best / (double)taken, (double)f.iWeight / 100.0);
		if (f.iHyst > 0 && b.iSpot == row && b.lSpotMap == PLAYERBOT_YSPOT_MAPS[slot].lMap)
			adjusted *= (100.0 + f.iHyst) / 100.0;
		return (int)std::max(1.0, std::min(adjusted, (double)(INT_MAX / 2)));
	}

	// (1) The hub's change to an ordinary Sung Ma spot (playerbot_wandering.h).
	void NotePlayerBotYSpotChosen(LPCHARACTER ch, long x, long y, DWORD dwNow)
	{
		if (!ch || !ch->IsPC() || GetPlayerBotYSpotFlags().bOff)
			return;
		const int slot = GetPlayerBotYSpotSlot(ch->GetMapIndex());
		const int row = FindPlayerBotYSpotRow(slot, x, y);
		if (row < 0)
			return;
		const TPlayerBotYSpotMap& m = PLAYERBOT_YSPOT_MAPS[slot];
		TPlayerBotYSpotBot& b = s_mapPlayerBotYSpot[ch->GetPlayerID()];
		int r[PLAYERBOT_YOHARA_ELEMENTS];
		if (b.dwRoundAt == dwNow && dwNow != 0)
			for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
				r[e] = b.aiRound[e];
		else
			GetPlayerBotYSpotResist(ch, dwNow, r);
		const int taken = GetPlayerBotYSpotTaken(m.pRows[row], r);
		const int best = b.dwRoundAt == dwNow && b.iRoundBest <= 100 ? std::min(b.iRoundBest, taken) : taken;
		const int mapBest = GetPlayerBotYSpotMapBest(slot, r);
		const bool same = b.lSpotMap == m.lMap && b.iSpot >= 0;
		const int prev = same ? b.iSpot : -1;
		if (same && prev == row)
			return;
		TPlayerBotYSpotStats& st = s_aPlayerBotYSpotStats[slot];
		++st.picks;
		st.repicks += same ? 1 : 0;
		const bool gear = b.dwGearAt != 0 && dwNow - b.dwGearAt < PLAYERBOT_YSPOT_GEAR_MOVE_MS && same;
		st.gearMoves += gear ? 1 : 0;
		st.sumChosen += std::max(0, taken);
		st.sumBest += std::max(0, best);
		char mix[48], res[64];
		FormatPlayerBotYSpotMix(m.pRows[row], mix, sizeof(mix));
		FormatPlayerBotYSpotResist(r, GetPlayerBotYSpotMapMask(slot), res, sizeof(res));
		PlayerBotLogThrottled("yspot_pick", dwNow,
				"PLAYERBOT_YSPOT: pick pid=%u name=%s champion=%d map=%ld spot=%d prev=%d pos=(%ld,%ld) mix=%s resist=%s "
				"taken=%d round_best=%d map_best=%d party=%u why=%s",
				ch->GetPlayerID(), ch->GetName(), (int)ch->GetConquerorLevel(), m.lMap, row, prev, x, y, mix, res, taken, best,
				mapBest, ch->GetParty() ? (unsigned int)ch->GetParty()->GetMemberCount() : 0U,
				gear ? "gear" : (same ? "rotation" : "arrival"));
		b.lSpotMap = m.lMap;
		b.iSpot = row;
		b.dwPickAt = dwNow ? dwNow : 1;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			b.aiPick[e] = r[e];
	}

	// (3) Every PLAYERBOT_YSPOT_CENSUS_MS: per map with bots seen.
	void TickPlayerBotYSpotCensus(DWORD dwNow)
	{
		if (s_dwPlayerBotYSpotCensusAt == 0)
		{
			s_dwPlayerBotYSpotCensusAt = dwNow + PLAYERBOT_YSPOT_CENSUS_MS;
			return;
		}
		if ((int)(dwNow - s_dwPlayerBotYSpotCensusAt) < 0)
			return;
		s_dwPlayerBotYSpotCensusAt = dwNow + PLAYERBOT_YSPOT_CENSUS_MS;
		const TPlayerBotYSpotFlags& f = GetPlayerBotYSpotFlags();
		for (int slot = 0; slot < PLAYERBOT_YSPOT_MAP_COUNT; ++slot)
		{
			const TPlayerBotYSpotMap& m = PLAYERBOT_YSPOT_MAPS[slot];
			std::vector<int> onSpot(m.iRows, 0);
			int bots = 0, held = 0;
			long long sumTaken = 0, sumBest = 0;
			for (std::map<DWORD, TPlayerBotYSpotBot>::const_iterator it = s_mapPlayerBotYSpot.begin(); it != s_mapPlayerBotYSpot.end(); ++it)
			{
				const TPlayerBotYSpotBot& b = it->second;
				if (b.dwSeen == 0 || dwNow - b.dwSeen > PLAYERBOT_YSPOT_SEEN_MS || b.lSeenMap != m.lMap)
					continue;
				++bots;
				if (b.lSpotMap != m.lMap || b.iSpot < 0 || b.iSpot >= m.iRows)
					continue;
				++onSpot[b.iSpot];
				const int t = GetPlayerBotYSpotTaken(m.pRows[b.iSpot], b.aiPick);
				if (t < 0)
					continue;
				++held;
				sumTaken += t;
				sumBest += GetPlayerBotYSpotMapBest(slot, b.aiPick);
			}
			TPlayerBotYSpotStats& st = s_aPlayerBotYSpotStats[slot];
			if (bots == 0 && st.picks == 0)
			{
				st = TPlayerBotYSpotStats();
				continue;
			}
			std::string spots;
			int spotCount = 0;
			for (int i = 0; i < m.iRows; ++i)
			{
				if (m.pRows[i].x == 0)
					continue;
				++spotCount;
				char mix[48], one[72];
				FormatPlayerBotYSpotMix(m.pRows[i], mix, sizeof(mix));
				snprintf(one, sizeof(one), "%s%d:%s/%d", spots.empty() ? "" : " ", i, mix, onSpot[i]);
				spots += one;
			}
			sys_log(0, "PLAYERBOT_YSPOT: census map=%ld on=%d weight=%d hyst=%d bots=%d held=%d taken_avg=%lld best_avg=%lld "
					"window=[picks=%u repicks=%u gear_looks=%u gear_moves=%u chosen_avg=%lld round_best_avg=%lld] spots=%d [%s]",
					m.lMap, f.bOff ? 0 : 1, f.iWeight, f.iHyst, bots, held, held ? sumTaken / held : 0LL, held ? sumBest / held : 0LL,
					st.picks, st.repicks, st.gearLooks, st.gearMoves, st.picks ? st.sumChosen / st.picks : 0LL,
					st.picks ? st.sumBest / st.picks : 0LL, spotCount, spots.c_str());
			st = TPlayerBotYSpotStats();
		}
		// forgotten: unseen for an hour
		for (std::map<DWORD, TPlayerBotYSpotBot>::iterator it = s_mapPlayerBotYSpot.begin(); it != s_mapPlayerBotYSpot.end();)
		{
			if (dwNow - it->second.dwSeen > 60 * 60 * 1000 && dwNow - it->second.dwResistAt > 60 * 60 * 1000)
				s_mapPlayerBotYSpot.erase(it++);
			else
				++it;
		}
	}

	// (2) From the top of every tick: a bot on a Sung Ma map of the table is looked at every PLAYERBOT_YSPOT_TICK_MS.
	void ManagePlayerBotYSpotTick(LPCHARACTER ch, DWORD dwNow)
	{
		TickPlayerBotYSpotCensus(dwNow);
		if (!ch || !ch->IsPC() || !ch->IsItemLoaded() || ch->IsDead())
			return;
		const int slot = GetPlayerBotYSpotSlot(ch->GetMapIndex());
		if (slot < 0)
			return;
		const TPlayerBotYSpotMap& m = PLAYERBOT_YSPOT_MAPS[slot];
		TPlayerBotYSpotBot& b = s_mapPlayerBotYSpot[ch->GetPlayerID()];
		if (b.dwNextTick != 0 && (int)(dwNow - b.dwNextTick) < 0)
			return;
		b.dwNextTick = dwNow + PLAYERBOT_YSPOT_TICK_MS;
		b.dwSeen = dwNow ? dwNow : 1;
		b.lSeenMap = m.lMap;
		if (GetPlayerBotYSpotFlags().bOff || b.lSpotMap != m.lMap || b.iSpot < 0)
			return;
		int r[PLAYERBOT_YOHARA_ELEMENTS];
		GetPlayerBotYSpotResist(ch, dwNow, r);
		const int mask = GetPlayerBotYSpotMapMask(slot);
		int delta = 0;
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			if (mask & (1 << e))
				delta = std::max(delta, abs(r[e] - b.aiPick[e]));
		if (delta < PLAYERBOT_YSPOT_GEAR_DELTA || (b.dwGearAt != 0 && dwNow - b.dwGearAt < PLAYERBOT_YSPOT_GEAR_GAP_MS))
			return;
		// one element-mix on the whole map (Seoganland, Schronienie, Zejscie): nothing to choose - the new values only
		bool mixed = false;
		for (int i = 1; i < m.iRows && !mixed; ++i)
			if (m.pRows[i].x != 0)
				for (int j = 0; j < i && !mixed; ++j)
					if (m.pRows[j].x != 0)
						for (int c = 0; c < 4 && !mixed; ++c)
							mixed = m.pRows[i].a[c].bMask != m.pRows[j].a[c].bMask || m.pRows[i].a[c].bPct != m.pRows[j].a[c].bPct;
		const int before = GetPlayerBotYSpotTaken(m.pRows[b.iSpot], b.aiPick);
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
			b.aiPick[e] = r[e];
		if (!mixed)
			return;
		TPlayerBotAIStateMap::iterator s = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		size_t hubCount = 0;
		const TPlayerBotHuntingHub* hubs = GetPlayerBotYoharaHubs(m.lMap, hubCount);
		if (s == s_mapPlayerBotAIStates.end() || !hubs || s->second.wHuntingHub >= hubCount ||
				hubs[s->second.wHuntingHub].x != m.pRows[b.iSpot].x || hubs[s->second.wHuntingHub].y != m.pRows[b.iSpot].y)
			return;
		s->second.dwHubChosenTime = 0;	// the stick ends: the next wander asks the hub choice again (the hysteresis holds)
		b.dwGearAt = dwNow ? dwNow : 1;
		++s_aPlayerBotYSpotStats[slot].gearLooks;
		char res[64];
		FormatPlayerBotYSpotResist(r, mask, res, sizeof(res));
		PlayerBotLogThrottled("yspot_gear", dwNow,
				"PLAYERBOT_YSPOT: gear pid=%u name=%s map=%ld spot=%d resist=%s delta=%d taken_before=%d taken_now=%d map_best=%d",
				ch->GetPlayerID(), ch->GetName(), m.lMap, b.iSpot, res, delta, before,
				GetPlayerBotYSpotTaken(m.pRows[b.iSpot], r), GetPlayerBotYSpotMapBest(slot, r));
	}
}

#endif
