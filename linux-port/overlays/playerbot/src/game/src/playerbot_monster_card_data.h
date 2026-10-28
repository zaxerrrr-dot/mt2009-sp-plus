#ifndef __INC_METIN2_PLAYERBOT_MONSTER_CARD_DATA_H__
#define __INC_METIN2_PLAYERBOT_MONSTER_CARD_DATA_H__

// Karty Potworow (the Monster Card System) - the data: the mission pools,
// the teleport points and the sets (MT2009_PLUS_MONSTER_CARDS_V1).
//
// Autor systemu: Digi Rasta (nowy-system v0.25.2, a port of the
// "Official-Monster-Card-System" package by Best Studio). His generator
// (karty_dane.py) built these tables from the package's client table
// monster_card.txt, its MonstercardCoordinates.txt and monster_card_achiev.txt,
// filtered to the monsters our world.mob_proto has and the client has a card
// picture for (56 of 101). The client's twin is root/monstercard_data.py -
// change both together. MT2009_PLUS_MONSTER_CARDS_YOHARA_V1 (28 October 2026): the Yohara cards and the
// global client's 18 levels and 40 sets (below).

namespace mt2009_mcard
{

const int LEVELS = 18;		// mission levels (the global client: 18, then from 1 again; was 15 before Yohara)
const int DECK_SIZE = 16;	// cards a mission level offers

// The monster pool of every mission level (0 = an empty place). MT2009_PLUS_MONSTER_CARDS_YOHARA_V1: the global
// client's monster_card.txt (GF 26.1.11 = the "Official-Monster-Card-System" package's) with our real vnums - its
// En-Tai Guardian 6405 is our 6400 (trent_officer, the Ochao temple, 209) and its Ochao Bodyguard 6392 our 6311
// (lemures_boss2); the monsters our world lacks (6920/6922 Dolina Mroku Ksiezyca, 6937-6939) left out. Levels
// 10-15 got the bosses of the Yohara branch (6116, 6192, 6400, 6311, 6407, 6408, the 12 Zodiac generals),
// 16-18 are Yohara's.
const DWORD LEVEL_POOL[LEVELS][DECK_SIZE] =
{
	{ 151, 153, 152, 154, 391, 155, 393, 191, 5161, 192, 394, 193, 194, 0, 0, 0 },
	{ 151, 153, 152, 154, 391, 155, 393, 191, 5161, 192, 394, 193, 194, 0, 0, 0 },
	{ 151, 153, 152, 154, 391, 155, 393, 191, 5161, 192, 394, 193, 194, 0, 0, 0 },
	{ 431, 491, 432, 433, 434, 492, 435, 493, 436, 591, 494, 533, 534, 5162, 691, 0 },
	{ 431, 491, 432, 433, 434, 492, 435, 493, 436, 591, 494, 533, 534, 5162, 691, 0 },
	{ 431, 491, 432, 433, 434, 492, 435, 493, 436, 591, 494, 533, 534, 5162, 691, 0 },
	{ 791, 5163, 2191, 1901, 2206, 1304, 1091, 1093, 2092, 2402, 2306, 0, 0, 0, 0, 0 },
	{ 791, 5163, 2191, 1901, 2206, 1304, 1091, 1093, 2092, 2402, 2306, 0, 0, 0, 0, 0 },
	{ 791, 5163, 2191, 1901, 2206, 1304, 1091, 1093, 2092, 2402, 2306, 0, 0, 0, 0, 0 },
	{ 1192, 2597, 2492, 3910, 3891, 3491, 3591, 3291, 3091, 6400, 3191, 6311, 3791, 3596, 0, 0 },
	{ 1192, 2597, 2492, 3910, 3891, 3491, 3591, 3291, 3091, 6400, 3191, 6311, 3791, 3596, 0, 0 },
	{ 1192, 2597, 2492, 3910, 3891, 3491, 3591, 3291, 3091, 6400, 3191, 6311, 3791, 3596, 0, 0 },
	{ 1192, 2493, 6400, 6109, 6191, 6116, 6009, 6091, 6407, 6408, 6192, 2752, 2762, 2772, 2782, 0 },
	{ 1192, 2493, 6400, 6109, 6191, 6116, 6009, 6091, 6407, 6408, 6192, 2792, 2802, 2812, 2822, 0 },
	{ 1192, 2493, 6400, 6109, 6191, 6116, 6009, 6091, 6407, 6408, 6192, 2832, 2842, 2852, 2862, 0 },
	{ 6699, 6705, 6706, 6723, 6724, 6749, 6764, 6805, 6815, 6820, 6756, 6776, 6783, 0, 0, 0 },
	{ 6699, 6705, 6706, 6723, 6724, 6749, 6764, 6805, 6815, 6820, 6756, 6776, 6783, 0, 0, 0 },
	{ 6805, 6815, 6820, 6756, 7609, 7610, 7611, 7612, 7613, 7614, 6789, 6797, 6791, 0, 0, 0 },
};

// The 4-star teleport: (monster, map index, x, y in the map's own metres).
// 20 of the 56 monsters have points (the package's coordinates); the rest -
// dungeon bosses and monsters the package gave none - answer "no teleport".
struct STeleport { DWORD dwVnum; long lMap; long lX; long lY; };
const STeleport TELEPORTS[] =
{
	{ 151, 1, 418, 684 }, { 151, 1, 606, 940 }, { 151, 1, 880, 651 },
	{ 152, 1, 457, 976 }, { 152, 1, 924, 843 }, { 152, 1, 921, 222 },
	{ 153, 1, 463, 888 }, { 153, 1, 630, 1028 }, { 153, 1, 224, 531 },
	{ 154, 1, 660, 99 }, { 154, 1, 892, 925 }, { 154, 1, 350, 1005 },
	{ 155, 1, 181, 542 }, { 155, 1, 877, 172 }, { 155, 1, 478, 1100 },
	{ 191, 1, 626, 40 },
	{ 431, 3, 219, 200 }, { 432, 3, 235, 213 }, { 433, 3, 182, 311 }, { 434, 3, 103, 572 },
	{ 435, 3, 797, 207 }, { 436, 3, 841, 301 }, { 533, 3, 229, 561 }, { 534, 3, 322, 682 },
	{ 591, 3, 625, 870 },
	{ 151, 21, 428, 993 }, { 151, 21, 750, 341 }, { 151, 21, 433, 424 },
	{ 152, 21, 287, 516 }, { 152, 21, 338, 1009 }, { 152, 21, 892, 939 },
	{ 153, 21, 436, 1031 }, { 153, 21, 913, 858 }, { 153, 21, 395, 430 },
	{ 154, 21, 269, 365 }, { 154, 21, 617, 269 }, { 154, 21, 555, 1090 },
	{ 155, 21, 660, 1118 }, { 155, 21, 325, 1093 }, { 155, 21, 316, 289 },
	{ 191, 21, 313, 120 },
	{ 431, 23, 566, 161 }, { 432, 23, 642, 209 }, { 433, 23, 663, 230 }, { 434, 23, 351, 269 },
	{ 435, 23, 299, 545 }, { 436, 23, 273, 703 }, { 533, 23, 299, 545 }, { 534, 23, 273, 703 },
	{ 591, 23, 787, 688 },
	{ 191, 41, 75, 934 },
	{ 151, 41, 190, 889 }, { 151, 41, 539, 434 }, { 151, 41, 567, 901 },
	{ 152, 41, 740, 767 }, { 152, 41, 204, 246 }, { 152, 41, 142, 1015 },
	{ 153, 41, 148, 383 }, { 153, 41, 635, 931 }, { 153, 41, 229, 991 },
	{ 154, 41, 719, 1011 }, { 154, 41, 347, 1079 }, { 154, 41, 135, 1073 },
	{ 155, 41, 723, 880 }, { 155, 41, 295, 121 }, { 155, 41, 692, 334 },
	{ 431, 43, 420, 705 }, { 432, 43, 785, 803 }, { 433, 43, 165, 872 }, { 434, 43, 174, 172 },
	{ 435, 43, 167, 234 }, { 436, 43, 168, 436 }, { 533, 43, 219, 656 }, { 534, 43, 420, 705 },
	{ 591, 43, 804, 830 },
	{ 1901, 61, 749, 629 },
	{ 2206, 62, 144, 778 },
	{ 2191, 63, 869, 658 },
	{ 691, 64, 770, 757 }, { 533, 64, 708, 1384 }, { 533, 64, 1300, 509 }, { 534, 64, 1066, 1051 },
	{ 534, 64, 1043, 1111 },
	{ 2402, 72, 631, 92 }, { 2402, 72, 699, 92 }, { 2402, 72, 766, 95 }, { 2402, 72, 258, 96 },
	{ 2402, 72, 1179, 97 }, { 2402, 72, 1124, 98 }, { 2402, 72, 1167, 98 }, { 2402, 72, 442, 99 },
	{ 2402, 72, 316, 102 }, { 2402, 72, 784, 102 }, { 2402, 72, 271, 104 }, { 2402, 72, 425, 104 },
	{ 2402, 72, 613, 104 }, { 2402, 72, 477, 106 }, { 2402, 72, 386, 107 }, { 2402, 72, 627, 109 },
	{ 2402, 72, 657, 110 }, { 2402, 72, 1078, 116 }, { 2402, 72, 653, 118 }, { 2402, 72, 539, 159 },
	{ 2402, 72, 229, 164 }, { 2402, 72, 493, 165 }, { 2402, 72, 380, 168 }, { 2402, 72, 486, 170 },
	{ 2402, 72, 363, 177 }, { 2402, 72, 382, 180 }, { 2402, 72, 285, 186 }, { 2402, 72, 470, 187 },
	{ 2402, 72, 260, 189 }, { 2402, 72, 275, 191 }, { 2402, 72, 463, 191 }, { 2402, 72, 509, 192 },
	{ 2402, 72, 512, 192 }, { 2402, 72, 562, 192 }, { 2402, 72, 551, 193 }, { 2402, 72, 382, 195 },
	{ 2402, 72, 493, 195 }, { 2402, 72, 268, 196 }, { 2402, 72, 370, 198 }, { 2402, 72, 533, 198 },
	{ 2402, 72, 504, 200 }, { 2402, 72, 500, 201 }, { 2402, 72, 397, 204 }, { 2402, 72, 371, 217 },
	{ 2402, 72, 369, 222 }, { 2402, 72, 98, 233 }, { 2402, 72, 98, 301 }, { 2402, 72, 344, 339 },
	{ 2402, 72, 232, 341 }, { 2402, 72, 263, 349 }, { 2402, 72, 234, 355 }, { 2402, 72, 249, 355 },
	{ 2402, 72, 185, 360 }, { 2402, 72, 283, 365 }, { 2402, 72, 161, 366 }, { 2402, 72, 78, 381 },
	{ 2402, 72, 351, 382 }, { 2402, 72, 252, 389 }, { 2402, 72, 230, 390 }, { 2402, 72, 244, 399 },
	{ 2191, 125, 912, 616 },
};

// The sets ("Bonusy zestawow"): 40 of the global client's 42 (monster_card_achiev.txt of GF 26.1.11 = the
// package's) - 41 (Nykos, 6920/6922) and 42 (6937-6939) need monsters our world does not have. A set's bonus
// rank N takes N stars of every monster of the set (and needs at least that many); the bonus goes on as
// AFFECT_COLLECT. iType 0 = a field set (one at a time), 1 = a dungeon set. iRanks: how many of the last of
// the five ranks count (2 = ranks 4 and 5). The values are the global ones in both M2_BONUS_MODE modes (the
// 17 sets of before were already the global values - MT2009_PLUS_MONSTER_CARDS_YOHARA_V1 compared them with the
// global client); the client's applies mapped onto our POINT_* (GF APPLY 239-243 = SUNGMA_STR/HP/MOVE/IMMUNE,
// HIT_PCT; 99-104 = the element powers). The client's twin, root/monstercard_data.py, has the same points as
// numbers - the static_asserts below keep them in line.
struct SAchievement
{
	DWORD dwVnum;
	int iType;
	int iRanks;
	DWORD adwMonsters[8];
	int aiBonus[5];
	int aiPoint[2];
};
const SAchievement ACHIEVEMENTS[] =
{
	{ 1, 0, 5, { 151, 152, 0, 0, 0, 0, 0, 0 }, { 7, 13, 25, 30, 40 }, { POINT_DEF_GRADE_BONUS, 0 } },		// Wilki alfa
	{ 2, 0, 5, { 151, 152, 191, 0, 0, 0, 0, 0 }, { 5, 10, 25, 35, 50 }, { POINT_DEF_GRADE_BONUS, 0 } },	// Przywodca stada
	{ 3, 0, 5, { 191, 192, 193, 194, 0, 0, 0, 0 }, { 5, 10, 15, 20, 25 }, { POINT_ATTBONUS_ANIMAL, 0 } },	// Jedyni w swoim rodzaju
	{ 4, 0, 5, { 153, 154, 155, 0, 0, 0, 0, 0 }, { 15, 30, 55, 75, 100 }, { POINT_ATT_GRADE_BONUS, 0 } },	// Tygrys, niedzwiedz, dzik
	{ 5, 0, 5, { 391, 393, 394, 0, 0, 0, 0, 0 }, { 60, 80, 110, 150, 200 }, { POINT_MAX_HP, 0 } },			// Zemsta Bialej Przysiegi
	{ 6, 0, 5, { 431, 432, 433, 434, 435, 436, 0, 0 }, { 3, 5, 7, 9, 12 }, { POINT_MOV_SPEED, 0 } },		// Zemsta Czarnej Smierci
	{ 7, 0, 5, { 491, 493, 0, 0, 0, 0, 0, 0 }, { 50, 75, 100, 200, 300 }, { POINT_MAX_HP, 0 } },			// Bracia
	{ 8, 0, 5, { 491, 492, 493, 494, 0, 0, 0, 0 }, { 10, 25, 50, 100, 125 }, { POINT_ATT_GRADE_BONUS, 0 } },	// Wiezy rodzinne
	{ 9, 0, 5, { 533, 534, 691, 0, 0, 0, 0, 0 }, { 3, 5, 10, 12, 15 }, { POINT_ATT_SPEED, 0 } },			// Okrutni i bezlitosni
	{ 10, 0, 5, { 591, 494, 0, 0, 0, 0, 0, 0 }, { 80, 160, 240, 320, 400 }, { POINT_MAX_SP, 0 } },			// Prawie nie ludzcy
	{ 11, 0, 2, { 3091, 3291, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 1, 2 }, { POINT_IQ, 0 } },						// Wieczni Straznicy
	{ 12, 0, 2, { 3491, 3591, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 1, 2 }, { POINT_ST, 0 } },						// Straznik Nefrytu
	{ 13, 0, 2, { 3191, 3596, 3791, 0, 0, 0, 0, 0 }, { 0, 0, 0, 1, 2 }, { POINT_HT, 0 } },					// Wladca Gor Gromu
	// MT2009_PLUS_MONSTER_CARDS_YOHARA_V1: the sets whose monsters came with the Yohara branch (6400 = GF 6405, 6311 = GF 6392)
	{ 14, 0, 2, { 3910, 6311, 3891, 6407, 0, 0, 0, 0 }, { 0, 0, 0, 1, 2 }, { POINT_DX, 0 } },				// Klopoty na Zboczu Gautama
	{ 15, 1, 2, { 5161, 5162, 5163, 0, 0, 0, 0, 0 }, { 0, 0, 0, 1, 3 }, { POINT_DODGE, 0 } },				// Bractwo Malp
	{ 16, 1, 2, { 2092, 1192, 2402, 2492, 2597, 0, 0, 0 }, { 0, 0, 0, 1, 3 }, { POINT_MELEE_MAGIC_ATT_BONUS_PER, 0 } },	// Wladca Jaskini
	{ 17, 1, 2, { 1093, 1091, 2597, 0, 0, 0, 0, 0 }, { 0, 0, 0, 1, 3 }, { POINT_KILL_HP_RECOVERY, 0 } },		// Diaboliczni
	{ 18, 1, 2, { 2493, 6116, 6400, 0, 0, 0, 0, 0 }, { 0, 0, 0, 1, 3 }, { POINT_ATTBONUS_MONSTER, 0 } },		// Sludzy Sung Mahi
	{ 19, 1, 2, { 6009, 6109, 6191, 6091, 0, 0, 0, 0 }, { 0, 0, 0, 1, 2 }, { POINT_HT, 0 } },				// Cel uswieca srodki
	{ 20, 1, 2, { 6400, 6408, 6192, 0, 0, 0, 0, 0 }, { 0, 0, 0, 1, 3 }, { POINT_MAX_SP_PCT, 0 } },			// Straznicy Lasu
	{ 21, 1, 2, { 2493, 6191, 6091, 6192, 0, 0, 0, 0 }, { 0, 0, 0, 1, 3 }, { POINT_MAX_HP_PCT, 0 } },		// Generalowie Sung Mahi
	{ 22, 1, 2, { 2822, 2792, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 3, 10 }, { POINT_ENCHANT_ELECT, 0 } },			// Zodiak Blyskawic
	{ 23, 1, 2, { 2862, 2772, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 3, 10 }, { POINT_ENCHANT_FIRE, 0 } },			// Zodiak Ognia
	{ 24, 1, 2, { 2802, 2812, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 3, 10 }, { POINT_ENCHANT_ICE, 0 } },			// Zodiak Lodu
	{ 25, 1, 2, { 2782, 2842, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 3, 10 }, { POINT_ENCHANT_WIND, 0 } },			// Zodiak Wiatru
	{ 26, 1, 2, { 2762, 2832, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 3, 10 }, { POINT_ENCHANT_EARTH, 0 } },			// Zodiak Ziemi
	{ 27, 1, 2, { 2852, 2752, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 3, 10 }, { POINT_ENCHANT_DARK, 0 } },			// Zodiak Mroku
	{ 28, 0, 3, { 6699, 6705, 6706, 0, 0, 0, 0, 0 }, { 0, 0, 1, 3, 10 }, { POINT_SUNGMA_MOVE, 0 } },		// Straznicy Rownin (Odpornosc Sung Ma)
	{ 29, 0, 3, { 6723, 6724, 0, 0, 0, 0, 0, 0 }, { 0, 0, 1, 3, 10 }, { POINT_SUNGMA_IMMUNE, 0 } },			// Myr Sung Mahi (Inteligencja Sung Ma)
	{ 30, 0, 2, { 6749, 6764, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 2, 5 }, { POINT_HIT_PCT, 0 } },				// Polludzcy Wladcy (Precyzja)
	{ 31, 0, 3, { 6776, 6783, 0, 0, 0, 0, 0, 0 }, { 0, 0, 1, 3, 10 }, { POINT_SUNGMA_HP, 0 } },				// Lodowi Straznicy (Witalnosc Sung Ma)
	{ 32, 1, 3, { 6805, 6815, 6820, 0, 0, 0, 0, 0 }, { 0, 0, 1, 3, 10 }, { POINT_BLOCK, 0 } },				// Trio z Jaskin
	{ 33, 1, 2, { 6756, 0, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 2, 5 }, { POINT_SUNGMA_STR, 0 } },				// Trujaca Krolowa (Sila Sung Ma)
	{ 34, 1, 2, { 7609, 0, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 2, 5 }, { POINT_RESIST_FIRE, 0 } },				// Plonaca Wieza
	{ 35, 1, 2, { 7610, 0, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 2, 5 }, { POINT_RESIST_ICE, 0 } },				// Zamarznieta Wieza
	{ 36, 1, 2, { 7611, 0, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 2, 5 }, { POINT_RESIST_ELEC, 0 } },				// Elektryczna Wieza
	{ 37, 1, 2, { 7612, 0, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 2, 5 }, { POINT_RESIST_WIND, 0 } },				// Burzowa Wieza
	{ 38, 1, 2, { 7613, 0, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 2, 5 }, { POINT_RESIST_EARTH, 0 } },				// Niewzruszona Wieza
	{ 39, 1, 2, { 7614, 0, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 2, 5 }, { POINT_RESIST_DARK, 0 } },				// Mroczna Wieza
	{ 40, 1, 3, { 6789, 6797, 6791, 0, 0, 0, 0, 0 }, { 0, 0, 150, 175, 250 }, { POINT_ATT_GRADE_BONUS, 0 } },	// Koniec Alastora
};

// The client (root/monstercard_data.py, OSIAGNIECIA "apply") names the bonus by these numbers.
static_assert(POINT_DX == 14 && POINT_ATTBONUS_MONSTER == 53 && POINT_BLOCK == 67 && POINT_RESIST_FIRE == 75 &&
		POINT_RESIST_ELEC == 76 && POINT_RESIST_WIND == 78 && POINT_ATT_GRADE_BONUS == 95 && POINT_MAX_HP_PCT == 119 &&
		POINT_MAX_SP_PCT == 120 && POINT_RESIST_ICE == 133 && POINT_RESIST_EARTH == 134 && POINT_RESIST_DARK == 135,
		"monster cards: a set's point number differs from monstercard_data.py");
static_assert(POINT_ENCHANT_ELECT == 178 && POINT_ENCHANT_DARK == 183 && POINT_SUNGMA_STR == 184 && POINT_SUNGMA_HP == 185 &&
		POINT_SUNGMA_MOVE == 186 && POINT_SUNGMA_IMMUNE == 187 && POINT_HIT_PCT == 197,
		"monster cards: a Yohara set's point number differs from monstercard_data.py");

}

#endif
