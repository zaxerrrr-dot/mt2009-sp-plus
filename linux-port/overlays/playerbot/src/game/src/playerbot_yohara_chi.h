#ifndef __INC_METIN2_PLAYERBOT_YOHARA_CHI_H__
#define __INC_METIN2_PLAYERBOT_YOHARA_CHI_H__

// MT2009_PLUS_BOT_YOHARA_CHI_V1 - the bot Champions' orders at Mistrz Chi (20823) and the smith (20016) of Dongan (373):
// the plan cache/yohara/plan-boty-yohara.md 6.1/6.2 and the list boty-yohara-lista.md items 18-20; the owner, 22 October
// 2026: "zlecenia u Mistrza Chi: rekawice +6 / +9, bizuteria z jadeitu, Kamienie Mocy Demonow; Gaya zastapiona Yangami
// (D6)", "Kamienie Demonow w rekawicach: wkladanie (30%), zbieranie z dropu", "Ulepszanie Talizmanu Woli Topazem u
// kowala w Dongan".
//
// The progression (6.1): G0 (+3, the package) -> G1 (+6) from Champion PLAYERBOT_CHI_G1_CHAMPION -> G2 (+9 and three
// Kamienie Demonow) from PLAYERBOT_CHI_G2_CHAMPION - the target plus of the glove (WEAR_GLOVE), the three pieces of jade
// jewellery worn and the Talizman Woli (worn, else the best one owned).
//
// The recipes are the players' own, read where the players' are:
//   * the anvil (refine_proto of item_proto.refine_set, CRefineManager - refine_global.sql today): the gloves +N -> +N+1
//     Utwardzacz Skory 31251 (10..200), Utwardzacz Skory+ 31252, Biala/Niebieska/Krwawa Perla 27992-27994, Kamien
//     Ksiezycowy 30618, 250 000 .. 650 000 Yang, 80..5%; the jade the same rows of Plyta z Surowego Metalu 31216 / Rog
//     Trolla 31217 (+3..+5), Plyta ze Stali Kuzniczej 31218 / Ozdobnej 31224 and the pearls (+6..+8); the Talizman Woli
//     +N Topaz Woli 72353 x 6(N+1) and a second Talizman Woli +N of its kind, 1 .. 5 mln Yang, 70..20%. Every step is
//     the engine's (DoRefine, or DoRefineWithScroll with a scroll from the bag): its fee, its materials, its roll, and
//     CItem::CopyAttributeTo - the glove's Will and its stones, the jade's lines and the account binding of a G0 piece
//     (MT2009_PLUS_ITEM_ACCOUNT_BOUND_V1) go over to the new item as for anybody. A step under PLAYERBOT_CHI_PLAIN_MIN_PROB
//     on the worn piece (the talisman's project) is a scroll's or waits (the plain anvil burns what it fails);
//   * Mistrz Chi (quest rekawice, MT2009_PLUS_GLOVES_V1 / MT2009_PLUS_DEMON_STONES_V1, and yohara_mapy4,
//     MT2009_PLUS_YOHARA_ITEMS4_V1 / MT2009_PLUS_JADE_JEWELLERY_V1 - the numbers copied below; a change there is a change
//     here): Rekawice Mocy +0 (23000) of 10 Czerwonych Run SungMa 31247, 25 Twardej Skory 31245, 5 Wzorow Rekawicy 31246,
//     a Kamien Runiczny 31225, 100 Gaya and 10 mln Yang, 75%; Obrecz / Kolia / Klipsy Jadeitu +0 of 10 jade of the kind,
//     25/30 Plyt z Surowego Metalu 31216 (Nocy 5 Klow Argosa 31227, Dymu 10 Lusek Argosa 31228), 100/300/400 Gaya and
//     1 mln Yang, 30%; Kamien Mocy Demonow +N (28047+100N) of a Kamien Demonow +N (28046+100N), N+1 Jadeitow Slonca 50661
//     and 0.3 / 0.5 / 0.7 / 0.9 / 1.2 mln Yang, 30%. The quest's NPC talk is skipped (as the bots' other errands do):
//     the same materials go, the same Yang, the same chance.
//
// Gaya (D6): a bot has none (it is no trade good - Statua Wojownika grinds it out of Kamyki), so it pays the Gaya of a
// recipe in Yang: PLAYERBOT_CHI_GAYA_YANG a Gaya (event flag bot_chi_gaya_yang overrides). The rate is the grinding's
// cost: 15 000 Yang, a Kamien Duszy +0..+3 (~ the 32 000 the bots price a dust at) and 30 Kamyki (no counter takes them)
// give 3 Gaya at 70% - (15 000 + 32 000) / 2.1 = ~22 400, rounded to 25 000 (100 Gaya: 2.5 mln Yang).
//
// The Kamienie Demonow (item 19): from the drop of the Yohara Metins, chiefs and chests (the loot pass as for anything)
// and the market; one of +PLAYERBOT_CHI_STONE_MIN_LEVEL or more goes into a free socket of the glove where the bot
// stands (out of a fight, the glove taken off and put back on) by the engine's own use of a stone
// (Mt2009GloveUseStone - glove_stone_pct, 30% as for players; a failure leaves a Pekniety Kamien in the socket). A
// Kamien Mocy Demonow first, then the highest. Plain stones over the free sockets are Mistrz Chi's Kamien Mocy
// Demonow, when the Jadeit Slonca is in the bag (never bought for that).
//
// Where: Dongan, from the Sung Ma stay (ManagePlayerBotSungmaResident, after Dongan's own errand of potions and junk):
// with an order it can do now (the materials, the Yang over PLAYERBOT_CHI_GOLD_FLOOR and its reserve; a scroll where one
// is needed) and not in a fight, the bot warps to Dongan as that errand does, walks to Mistrz Chi (the crafts) and to
// the smith beside him (the steps), at most PLAYERBOT_CHI_VISIT_ACTIONS orders a visit, PLAYERBOT_CHI_VISIT_GAP_MS
// between visits, and goes back to its map (the map's pick). What it lacks comes from the drop and the market: the
// crafts' keep (playerbot_workshop.h GetPlayerBotCraftMaterialKeep - not on a counter, not to the merchant) and the
// market's wants (WantsPlayerBotCraftOffer, CollectPlayerBotCraftMissing - the bots' stalls, the bots' and the players'
// offline shops on its trade trips home) ask this file. The G0 dust (playerbot_yohara_g0.h) is never touched here.
//
// The log: PLAYERBOT_CHI (order go / done with the cost and the materials, refine SUCCESS / FAILED / BURNED, craft, stone
// in, waits for a scroll, bought, visit over, census every ten minutes). The operator's file playerbot_chi_test in the
// core's directory: "status" logs every Champion's plan, "now" lets the next look start a visit. Event flag
// m2_bot_chi_off stops it all.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_yohara_g0.h (the Sung Ma stay, the
// Champion's helpers, the G0 kinds), in the anonymous namespace; declared ahead in playerbot_types.h.

// playerbot_yohara_gear.cpp: a Kamien Demonow into a glove, the engine's own use of a stone (CHARACTER::UseItemEx).
bool Mt2009GloveUseStone(LPCHARACTER ch, LPITEM stone, LPITEM glove);

namespace
{
	const DWORD PLAYERBOT_CHI_NPC = 20823;			// Mistrz Chi
	const DWORD PLAYERBOT_CHI_SMITH = 20016;		// the smith of Dongan
	// npc.txt of metin2_map_eastplain_01 (base 1049600,435200): 20823 (505,748), 20016 (498,738)
	const long PLAYERBOT_CHI_NPC_X = 1100100, PLAYERBOT_CHI_NPC_Y = 510000;
	const long PLAYERBOT_CHI_SMITH_X = 1099400, PLAYERBOT_CHI_SMITH_Y = 509000;
	const int PLAYERBOT_CHI_REACH = 350;

	const int PLAYERBOT_CHI_G1_CHAMPION = 10;
	const int PLAYERBOT_CHI_G2_CHAMPION = 20;
	const int PLAYERBOT_CHI_PLAIN_MIN_PROB = 60;	// a worn piece's step under it: a scroll's
	const int PLAYERBOT_CHI_STONE_MIN_LEVEL = 2;	// +2 .. +4: a Will of 6 / 9 / 15
	const int PLAYERBOT_CHI_TALISMAN_SPARES_MAX = 6;
	const long long PLAYERBOT_CHI_GAYA_YANG = 25000;
	const long long PLAYERBOT_CHI_GOLD_FLOOR = 2000000;
	const int PLAYERBOT_CHI_BUY_PURSE_PCT = 20;		// a material line: at most this per cent of the spare purse
	const DWORD PLAYERBOT_CHI_LOOK_MS = 60 * 1000;
	const DWORD PLAYERBOT_CHI_NEEDS_MS = 30 * 1000;
	const DWORD PLAYERBOT_CHI_VISIT_GAP_MS = 20 * 60 * 1000;
	const DWORD PLAYERBOT_CHI_VISIT_MS = 5 * 60 * 1000;
	const int PLAYERBOT_CHI_VISIT_ACTIONS = 6;
	const DWORD PLAYERBOT_CHI_CENSUS_MS = 10 * 60 * 1000;
	const char* const PLAYERBOT_CHI_TEST_FILE = "playerbot_chi_test";

	// ---- the recipes of Mistrz Chi (quests rekawice and yohara_mapy4)
	const DWORD PLAYERBOT_CHI_GLOVE_VNUM = 23000;	// Rekawice Mocy+0 (Sila - the G0 glove's kind)
	const DWORD PLAYERBOT_CHI_GLOVE_RUNE = 31247;	// Czerwona Runa SungMa
	const DWORD PLAYERBOT_CHI_LEATHER = 31245, PLAYERBOT_CHI_PATTERN = 31246, PLAYERBOT_CHI_RUNESTONE = 31225;
	const int PLAYERBOT_CHI_GLOVE_RUNES = 10, PLAYERBOT_CHI_GLOVE_LEATHER = 25, PLAYERBOT_CHI_GLOVE_PATTERNS = 5;
	const int PLAYERBOT_CHI_GLOVE_GAYA = 100, PLAYERBOT_CHI_GLOVE_PCT = 75;
	const long long PLAYERBOT_CHI_GLOVE_FEE = 10000000;
	struct TPlayerBotChiJadeRecipe { DWORD jade; int plates; DWORD extra; int extraN; int gaya; int offset; };
	// by the Will kind (0 Sila, 1 Witalnosc, 2 Odpornosc): Dymu, Nocy, Mgly (Slonca - Inteligencja - is no bot's)
	const TPlayerBotChiJadeRecipe PLAYERBOT_CHI_JADE[3] = {
		{ 50663, 30, 31228, 10, 400, 30 },	// Jadeit Dymu, Luski Argosa
		{ 50662, 25, 31227, 5, 300, 20 },	// Jadeit Nocy, Kly Argosa
		{ 50664, 25, 0, 0, 100, 0 },		// Jadeit Mgly
	};
	const DWORD PLAYERBOT_CHI_JADE_FIRST[3] = { 14580, 16580, 17570 };	// Obrecz, Kolia, Klipsy Jadeitu (+0, Mgly)
	const BYTE PLAYERBOT_CHI_JADE_WEAR[3] = { WEAR_WRIST, WEAR_NECK, WEAR_EAR };
	const char* const PLAYERBOT_CHI_JADE_NAMES[3] = { "bracelet", "necklace", "earrings" };
	const DWORD PLAYERBOT_CHI_PLATES = 31216;
	const int PLAYERBOT_CHI_JADE_N = 10, PLAYERBOT_CHI_JADE_PCT = 30;
	const long long PLAYERBOT_CHI_JADE_FEE = 1000000;
	const DWORD PLAYERBOT_CHI_STONE = 28046;		// Kamien Demonow+0; +N 28046+100N
	const DWORD PLAYERBOT_CHI_POWER_STONE = 28047;	// Kamien Mocy Demonow+0; +N 28047+100N
	const DWORD PLAYERBOT_CHI_SUN_JADE = 50661;		// Jadeit Slonca
	const long long PLAYERBOT_CHI_POWER_FEE[5] = { 300000, 500000, 700000, 900000, 1200000 };
	const int PLAYERBOT_CHI_POWER_PCT = 30;
	const DWORD PLAYERBOT_CHI_TOPAZ = 72353;		// Topaz Woli
	const DWORD PLAYERBOT_CHI_WILL_TALISMAN_BASE[3] = { 81000, 81300, 81250 };	// SILA, WIT, ODP

	enum { CHI_PHASE_NONE, CHI_PHASE_MASTER, CHI_PHASE_SMITH };

	struct TPlayerBotChi
	{
		DWORD dwNextLook, dwVisitSince, dwNextAction, dwLastVisitEnd;
		BYTE bPhase;
		int iActions;
		long long llSpent;
		long lStandX, lStandY;	// the phase's stand by its NPC (0: not chosen yet)
		TPlayerBotChi() : dwNextLook(0), dwVisitSince(0), dwNextAction(0), dwLastVisitEnd(0), bPhase(CHI_PHASE_NONE), iActions(0),
			llSpent(0), lStandX(0), lStandY(0) {}
	};
	std::map<DWORD, TPlayerBotChi> s_mapPlayerBotChi;

	// What a Champion keeps and lacks for its next orders, refreshed every PLAYERBOT_CHI_NEEDS_MS.
	struct TPlayerBotChiNeeds
	{
		DWORD dwAt;
		std::map<DWORD, int> keep, missing;
		int iTalismanKind, iTalismanPlus;	// the talisman worked on (-1 none) and its plus - the spares wanted
		int iStonesWanted;					// demon stones of the minimum level or more the glove's sockets wait for
		TPlayerBotChiNeeds() : dwAt(0), iTalismanKind(-1), iTalismanPlus(0), iStonesWanted(0) {}
	};
	std::map<DWORD, TPlayerBotChiNeeds> s_mapPlayerBotChiNeeds;

	struct TPlayerBotChiStats
	{
		unsigned int visits, refines, refineOk, refineFail, refineBurn, crafts, craftOk, stones, stonesOk, power, powerOk, bought;
		unsigned int scrollWaits;
		long long spent, gayaYang, boughtYang;
		DWORD dwLastCensus, dwLastTestLook;
		TPlayerBotChiStats() : visits(0), refines(0), refineOk(0), refineFail(0), refineBurn(0), crafts(0), craftOk(0), stones(0),
			stonesOk(0), power(0), powerOk(0), bought(0), scrollWaits(0), spent(0), gayaYang(0), boughtYang(0), dwLastCensus(0),
			dwLastTestLook(0) {}
	};
	TPlayerBotChiStats s_kPlayerBotChiStats;

	// ------------------------------------------------------------ the families

	bool IsPlayerBotChiGloveVnum(DWORD vnum) { return vnum >= 23000 && vnum <= 23039; }

	// 0 bracelet, 1 necklace, 2 earrings; -1 no jade
	int GetPlayerBotChiJadeSlot(DWORD vnum)
	{
		if (vnum >= 14580 && vnum <= 14619) return 0;
		if (vnum >= 16580 && vnum <= 16619) return 1;
		if (vnum >= 17570 && vnum <= 17609) return 2;
		return -1;
	}

	bool IsPlayerBotChiStoneVnum(DWORD vnum, int& level, bool& power)
	{
		if (vnum < PLAYERBOT_CHI_STONE || vnum > PLAYERBOT_CHI_POWER_STONE + 400 || (vnum - PLAYERBOT_CHI_STONE) % 100 > 1)
			return false;
		level = (int)((vnum - PLAYERBOT_CHI_STONE) / 100);
		power = (vnum - PLAYERBOT_CHI_STONE) % 100 == 1;
		return true;
	}

	// The gear this file raises (the generic anvil leaves it alone: GetPlayerBotRefineTargetOwn).
	bool IsPlayerBotChiGear(LPITEM item)
	{
		return item && Mt2009AccountBoundFamily(item->GetVnum());
	}

	bool IsPlayerBotChiOff()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_bot_chi_off") != 0;
	}

	long long GetPlayerBotChiGayaYang()
	{
		const int flag = quest::CQuestManager::instance().GetEventFlag("bot_chi_gaya_yang");
		return flag > 0 ? (long long)flag : PLAYERBOT_CHI_GAYA_YANG;
	}

	int GetPlayerBotChiTarget(LPCHARACTER ch)
	{
		const int champion = GetPlayerBotChampionLevel(ch);
		return champion >= PLAYERBOT_CHI_G2_CHAMPION ? 9 : champion >= PLAYERBOT_CHI_G1_CHAMPION ? 6 : 3;
	}

	long long GetPlayerBotChiSpare(LPCHARACTER ch)
	{
		return (long long)ch->GetGold() - (long long)GetPlayerBotReservedGold(ch) - PLAYERBOT_CHI_GOLD_FLOOR;
	}

	bool IsPlayerBotChiUser(LPCHARACTER ch)
	{
		return IsPlayerBotSungmaWillUser(ch) && ch->IsItemLoaded() && !IsPlayerBotSidekickServing(ch) && !IsPlayerBotChiOff();
	}

	// ------------------------------------------------------------ what the bot has

	// The glove it wears, else the best one in the bag.
	LPITEM FindPlayerBotChiGlove(LPCHARACTER ch)
	{
		LPITEM worn = ch->GetWear(WEAR_GLOVE);
		if (worn && IsPlayerBotChiGloveVnum(worn->GetVnum()))
			return worn;
		LPITEM best = NULL;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && IsPlayerBotChiGloveVnum(item->GetVnum()) &&
					(!best || item->GetVnum() % 10 > best->GetVnum() % 10))
				best = item;
		}
		return best;
	}

	// The jade piece of a slot: the worn one, else the best of the bag.
	LPITEM FindPlayerBotChiJade(LPCHARACTER ch, int slot)
	{
		LPITEM worn = ch->GetWear(PLAYERBOT_CHI_JADE_WEAR[slot]);
		if (worn && GetPlayerBotChiJadeSlot(worn->GetVnum()) == slot)
			return worn;
		LPITEM best = NULL;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && GetPlayerBotChiJadeSlot(item->GetVnum()) == slot &&
					(!best || item->GetVnum() % 10 > best->GetVnum() % 10))
				best = item;
		}
		return best;
	}

	// The Talizman Woli worked on: the worn one, else the highest owned (Sila / Witalnosc / Odpornosc only).
	LPITEM FindPlayerBotChiTalisman(LPCHARACTER ch)
	{
		LPITEM worn = ch->GetWear(WEAR_PENDANT);
		if (worn)
		{
			const int kind = GetPlayerBotWillTalismanKind(worn->GetVnum());
			if (kind >= 0 && kind <= 2)
				return worn;
		}
		LPITEM best = NULL;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell)
				continue;
			const int kind = GetPlayerBotWillTalismanKind(item->GetVnum());
			if (kind >= 0 && kind <= 2 && (!best || item->GetVnum() % 10 > best->GetVnum() % 10))
				best = item;
		}
		return best;
	}

	// Talizmany Woli of a kind and a plus in the bag (never the worn one, never `except`).
	LPITEM FindPlayerBotChiTalismanAt(LPCHARACTER ch, int kind, int plus, LPITEM except, int* count)
	{
		LPITEM first = NULL;
		int n = 0;
		const DWORD vnum = PLAYERBOT_CHI_WILL_TALISMAN_BASE[kind] + plus;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || item == except || item->GetVnum() != vnum || item->isLocked() ||
					item->IsExchanging())
				continue;
			++n;
			if (!first)
				first = item;
		}
		if (count)
			*count = n;
		return first;
	}

	int CountPlayerBotChiFreeSockets(LPITEM glove)
	{
		int free = 0;
		for (int i = 0; glove && i < ITEM_SOCKET_MAX_NUM; ++i)
			if (glove->GetSocket(i) >= 1 && glove->GetSocket(i) <= 2)
				++free;
		return free;
	}

	// The sockets holding a Sung Ma stone's Will.
	int CountPlayerBotChiWillSockets(LPITEM glove)
	{
		int n = 0;
		for (int i = 0; glove && i < ITEM_SOCKET_MAX_NUM; ++i)
		{
			BYTE point;
			int value;
			if (yohara_gear::DecodeSungmaSocket(glove->GetSocket(i), point, value))
				++n;
		}
		return n;
	}

	// The stones worth a socket in the bag (power ones and plain ones of the minimum level or more).
	int CountPlayerBotChiStones(LPCHARACTER ch, bool plainOnly)
	{
		int n = 0;
		for (int level = PLAYERBOT_CHI_STONE_MIN_LEVEL; level <= 4; ++level)
		{
			n += (int)ch->CountSpecifyItem(PLAYERBOT_CHI_STONE + 100 * level);
			if (!plainOnly)
				n += (int)ch->CountSpecifyItem(PLAYERBOT_CHI_POWER_STONE + 100 * level);
		}
		return n;
	}

	// The Will kind the bot lacks most for the map of its band (0 Sila, 1 Witalnosc, 2 Odpornosc); -1 nothing lacking.
	int GetPlayerBotChiShortKind(LPCHARACTER ch)
	{
		const int slot = GetPlayerBotG0BandSlot(ch);
		if (slot < 0)
			return -1;
		int best = -1, bestNeed = 0;
		for (int i = 0; i < 3; ++i)
		{
			const int need = GetPlayerBotSungmaReq(slot, i) - GetPlayerBotSungmaWill(ch, i);
			if (need > bestNeed)
			{
				bestNeed = need;
				best = i;
			}
		}
		return best;
	}

	// ------------------------------------------------------------ a step at the anvil

	// The engine's refine of the piece is possible now: its materials (a material of its own vnum counted without it),
	// the fee over the floor, and - a worn piece's (the project's) step under PLAYERBOT_CHI_PLAIN_MIN_PROB - a scroll.
	// scrollCell: the scroll to use (-1 the plain anvil). why: what is missing.
	bool CanPlayerBotChiRefine(LPCHARACTER ch, LPITEM item, bool project, int& scrollCell, const char*& why)
	{
		scrollCell = -1;
		why = "none";
		const TRefineTable* recipe = item ? CRefineManager::instance().GetRefineRecipe(item->GetRefineSet()) : NULL;
		if (!recipe || item->GetRefinedVnum() == 0)
		{
			why = "no_recipe";
			return false;
		}
		for (int m = 0; m < recipe->material_count; ++m)
			if (recipe->materials[m].vnum && (int)ElementsRefineMaterialCount(ch, item, recipe->materials[m].vnum) < (int)recipe->materials[m].count)
			{
				why = "materials";
				return false;
			}
		if (GetPlayerBotChiSpare(ch) < (long long)ch->ComputeRefineFee(recipe->cost))
		{
			why = "yang";
			return false;
		}
		// MT2009_PLUS_BOT_HIGH_GEAR_SCROLLS_V1: every piece here is of level 105 - the owner's ladder alone (Zwoj Wojny
		// under +4, the Blessing Scroll to +6, Boga Smokow / Podrecznik over), the plain anvil only at 100%, the spares too
		if (IsPlayerBotHighGear(item))
		{
			if (playerbot_high_gear::StepNeedsScroll((int)recipe->prob))
			{
				scrollCell = FindPlayerBotHighGearScrollCell(ch, item->GetRefineLevel());
				if (scrollCell < 0)
				{
					NotePlayerBotHighGearWait(ch, item, (int)recipe->prob, "chi");
					why = "scroll";
					return false;
				}
			}
			return true;
		}
		if (project && (int)recipe->prob < PLAYERBOT_CHI_PLAIN_MIN_PROB)
		{
			scrollCell = FindPlayerBotRefineScrollCell(ch, (BYTE)(item->GetVnum() % 10), (int)recipe->prob);
			if (scrollCell < 0)
			{
				why = "scroll";
				return false;
			}
		}
		return true;
	}

	void AddPlayerBotChiRecipeNeeds(LPCHARACTER ch, LPITEM item, bool project, std::map<DWORD, int>& keep, std::map<DWORD, int>& missing)
	{
		const TRefineTable* recipe = item ? CRefineManager::instance().GetRefineRecipe(item->GetRefineSet()) : NULL;
		if (!recipe || item->GetRefinedVnum() == 0)
			return;
		for (int m = 0; m < recipe->material_count; ++m)
		{
			const DWORD vnum = recipe->materials[m].vnum;
			const int count = (int)recipe->materials[m].count;
			if (!vnum || count <= 0 || vnum == item->GetVnum())
				continue;	// the talisman's spare is the ladder's (below)
			keep[vnum] += count * 2;
			const int have = (int)ch->CountSpecifyItem(vnum);
			if (have < count)
				missing[vnum] += count - have;
		}
		// MT2009_PLUS_BOT_HIGH_GEAR_SCROLLS_V1: the ladder's scroll the step lacks, by its tradeable vnum (the market)
		if (IsPlayerBotHighGear(item))
		{
			if (playerbot_high_gear::StepNeedsScroll((int)recipe->prob) &&
					FindPlayerBotHighGearScrollCell(ch, item->GetRefineLevel()) < 0)
				missing[GetPlayerBotHighGearMarketScroll(item->GetRefineLevel())] += 1;
			return;
		}
		if (project && (int)recipe->prob < PLAYERBOT_CHI_PLAIN_MIN_PROB &&
				FindPlayerBotRefineScrollCell(ch, (BYTE)(item->GetVnum() % 10), (int)recipe->prob) < 0)
			missing[PLAYERBOT_BLESSING_SCROLL_VNUM] += 1;
	}

	// ------------------------------------------------------------ the needs: keep and missing

	const TPlayerBotChiNeeds& GetPlayerBotChiNeeds(LPCHARACTER ch)
	{
		static const TPlayerBotChiNeeds s_kNone;
		if (!ch || !IsPlayerBotChiUser(ch))
			return s_kNone;
		const DWORD dwNow = get_dword_time();
		TPlayerBotChiNeeds& n = s_mapPlayerBotChiNeeds[ch->GetPlayerID()];
		if (n.dwAt != 0 && (int)(dwNow - n.dwAt) < (int)PLAYERBOT_CHI_NEEDS_MS)
			return n;
		n.dwAt = dwNow ? dwNow : 1;
		n.keep.clear();
		n.missing.clear();
		n.iTalismanKind = -1;
		n.iTalismanPlus = 0;
		n.iStonesWanted = 0;
		const int target = GetPlayerBotChiTarget(ch);
		const int shortKind = GetPlayerBotChiShortKind(ch);

		// The glove: Mistrz Chi's when there is none, the anvil's under the target.
		LPITEM glove = FindPlayerBotChiGlove(ch);
		if (!glove)
		{
			const DWORD v[4] = { PLAYERBOT_CHI_GLOVE_RUNE, PLAYERBOT_CHI_LEATHER, PLAYERBOT_CHI_PATTERN, PLAYERBOT_CHI_RUNESTONE };
			const int c[4] = { PLAYERBOT_CHI_GLOVE_RUNES, PLAYERBOT_CHI_GLOVE_LEATHER, PLAYERBOT_CHI_GLOVE_PATTERNS, 1 };
			for (int i = 0; i < 4; ++i)
			{
				n.keep[v[i]] += c[i];
				const int have = (int)ch->CountSpecifyItem(v[i]);
				if (have < c[i])
					n.missing[v[i]] += c[i] - have;
			}
		}
		else
		{
			if ((int)(glove->GetVnum() % 10) < target)
				AddPlayerBotChiRecipeNeeds(ch, glove, true, n.keep, n.missing);
			// The stones: the free sockets' worth kept and wanted.
			const int free = CountPlayerBotChiFreeSockets(glove);
			const int held = CountPlayerBotChiStones(ch, false);
			n.iStonesWanted = std::max(0, free - held);
			if (n.iStonesWanted > 0)
				n.missing[PLAYERBOT_CHI_STONE + 100 * PLAYERBOT_CHI_STONE_MIN_LEVEL] += n.iStonesWanted;
			int keepLeft = free + 1;
			for (int level = 4; level >= PLAYERBOT_CHI_STONE_MIN_LEVEL && keepLeft > 0; --level)
				for (int p = 1; p >= 0 && keepLeft > 0; --p)
				{
					const DWORD vnum = (p ? PLAYERBOT_CHI_POWER_STONE : PLAYERBOT_CHI_STONE) + 100 * level;
					const int have = std::min(keepLeft, (int)ch->CountSpecifyItem(vnum));
					if (have > 0)
					{
						n.keep[vnum] += have;
						keepLeft -= have;
					}
				}
		}

		// The jade: an empty slot crafted (only while the bot lacks Will for its band's map), a piece under the target raised.
		bool crafting = false;
		for (int s = 0; s < 3; ++s)
		{
			LPITEM jade = FindPlayerBotChiJade(ch, s);
			if (!jade)
			{
				if (crafting || shortKind < 0)
					continue;
				crafting = true;	// one craft's materials at a time
				const TPlayerBotChiJadeRecipe& r = PLAYERBOT_CHI_JADE[shortKind];
				const DWORD v[3] = { r.jade, PLAYERBOT_CHI_PLATES, r.extra };
				const int c[3] = { PLAYERBOT_CHI_JADE_N, r.plates, r.extraN };
				for (int i = 0; i < 3; ++i)
				{
					if (!v[i] || c[i] <= 0)
						continue;
					n.keep[v[i]] += c[i];
					const int have = (int)ch->CountSpecifyItem(v[i]);
					if (have < c[i])
						n.missing[v[i]] += c[i] - have;
				}
				continue;
			}
			if ((int)(jade->GetVnum() % 10) < target)
				AddPlayerBotChiRecipeNeeds(ch, jade, true, n.keep, n.missing);
		}

		// The Talizman Woli: the Topaz of the next step, and the spares of its kind (the ladder) kept and wanted.
		LPITEM talisman = FindPlayerBotChiTalisman(ch);
		if (talisman && (int)(talisman->GetVnum() % 10) < target)
		{
			n.iTalismanKind = GetPlayerBotWillTalismanKind(talisman->GetVnum());
			n.iTalismanPlus = (int)(talisman->GetVnum() % 10);
			AddPlayerBotChiRecipeNeeds(ch, talisman, true, n.keep, n.missing);
			int spares = 0;
			for (int p = 0; p <= n.iTalismanPlus; ++p)
			{
				int c = 0;
				FindPlayerBotChiTalismanAt(ch, n.iTalismanKind, p, talisman, &c);
				if (c > 0)
					n.keep[PLAYERBOT_CHI_WILL_TALISMAN_BASE[n.iTalismanKind] + p] += c;
				spares += c;
			}
			if (FindPlayerBotChiTalismanAt(ch, n.iTalismanKind, n.iTalismanPlus, talisman, NULL) == NULL &&
					spares < PLAYERBOT_CHI_TALISMAN_SPARES_MAX)
				n.missing[PLAYERBOT_CHI_WILL_TALISMAN_BASE[n.iTalismanKind]] += 1;
			// the ladder's Topaz: a step of the lowest pair below the project
			n.keep[PLAYERBOT_CHI_TOPAZ] += 6 * (n.iTalismanPlus + 1);
		}
		return n;
	}

	// ------------------------------------------------------------ the hooks (playerbot_workshop.h)

	int GetPlayerBotChiMaterialKeep(LPCHARACTER ch, DWORD vnum)
	{
		if (!ch || vnum == 0)
			return 0;
		const TPlayerBotChiNeeds& n = GetPlayerBotChiNeeds(ch);
		std::map<DWORD, int>::const_iterator it = n.keep.find(vnum);
		return it != n.keep.end() ? it->second : 0;
	}

	bool WantsPlayerBotChiOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer || Mt2009AccountBound(offer))
			return false;
		const TPlayerBotChiNeeds& n = GetPlayerBotChiNeeds(ch);
		if (n.missing.empty())
			return false;
		const DWORD vnum = offer->GetVnum();
		int level = 0;
		bool power = false;
		if (IsPlayerBotChiStoneVnum(vnum, level, power))
			return n.iStonesWanted > 0 && level >= PLAYERBOT_CHI_STONE_MIN_LEVEL && (int)offer->GetCount() <= n.iStonesWanted;
		const int kind = GetPlayerBotWillTalismanKind(vnum);
		if (kind >= 0)
			return kind == n.iTalismanKind && (int)(vnum % 10) <= n.iTalismanPlus &&
					n.missing.count(PLAYERBOT_CHI_WILL_TALISMAN_BASE[kind]) != 0;
		std::map<DWORD, int>::const_iterator it = n.missing.find(vnum);
		// not a stack many times what is missing (the rest would go on its counter again)
		return it != n.missing.end() && (int)offer->GetCount() <= std::max(it->second * 2, it->second + 10);
	}

	bool CanPlayerBotPayForChiOffer(LPCHARACTER ch, LPITEM offer, long long price)
	{
		if (!ch || !offer || price <= 0)
			return false;
		const long long count = std::max<long long>(1, (long long)offer->GetCount());
		const long long fair = (long long)GetPlayerBotShopAskingPrice(offer);
		const long long cap = std::max<long long>(fair * 2, 20000LL * count);
		return price <= cap && price <= GetPlayerBotChiSpare(ch) * PLAYERBOT_CHI_BUY_PURSE_PCT / 100;
	}

	void CollectPlayerBotChiMissing(LPCHARACTER ch, std::map<DWORD, int>& missing)
	{
		if (!ch)
			return;
		const TPlayerBotChiNeeds& n = GetPlayerBotChiNeeds(ch);
		for (std::map<DWORD, int>::const_iterator it = n.missing.begin(); it != n.missing.end(); ++it)
			missing[it->first] += it->second;
	}

	void NotePlayerBotChiBought(LPCHARACTER ch, DWORD vnum, long long price)
	{
		if (!ch)
			return;
		std::map<DWORD, TPlayerBotChiNeeds>::iterator it = s_mapPlayerBotChiNeeds.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotChiNeeds.end() || it->second.missing.empty())
			return;
		int level = 0;
		bool power = false;
		const bool stone = IsPlayerBotChiStoneVnum(vnum, level, power);
		const int kind = GetPlayerBotWillTalismanKind(vnum);
		if (!it->second.missing.count(vnum) && !(stone && it->second.iStonesWanted > 0) &&
				!(kind >= 0 && kind == it->second.iTalismanKind))
			return;
		it->second.dwAt = 0;	// counted again at the next ask
		++s_kPlayerBotChiStats.bought;
		s_kPlayerBotChiStats.boughtYang += std::max<long long>(0, price);
		sys_log(0, "PLAYERBOT_CHI: bought pid=%u name=%s vnum=%u price=%lld gold=%lld", ch->GetPlayerID(), ch->GetName(), vnum, price,
				(long long)ch->GetGold());
	}

	// ------------------------------------------------------------ the orders

	// A step at the smith on the piece; true when the engine tried it (the step done, won or lost).
	bool RefinePlayerBotChiPiece(LPCHARACTER ch, TPlayerBotAIState& state, LPITEM item, bool project, const char* what)
	{
		int scrollCell = -1;
		const char* why = NULL;
		if (!CanPlayerBotChiRefine(ch, item, project, scrollCell, why))
			return false;
		const bool wasWorn = item->IsEquipped();
		if (wasWorn && (ch->GetEmptyInventory(item->GetSize()) < 0 || !ch->UnequipItem(item) || item->IsEquipped()))
			return false;
		if (item->GetOwner() != ch || item->GetWindow() != INVENTORY || item->GetCell() >= PLAYERBOT_BAG_CELLS)
			return false;
		const TRefineTable* recipe = CRefineManager::instance().GetRefineRecipe(item->GetRefineSet());
		char materials[160] = "none";
		size_t used = 0;
		for (int m = 0; recipe && m < recipe->material_count && used + 24 < sizeof(materials); ++m)
			used += snprintf(materials + used, sizeof(materials) - used, "%s%u:%d/%d", m ? "," : "",
					(unsigned int)recipe->materials[m].vnum, (int)recipe->materials[m].count,
					(int)ElementsRefineMaterialCount(ch, item, recipe->materials[m].vnum));
		const DWORD oldVnum = item->GetVnum(), nextVnum = item->GetRefinedVnum();
		const bool bound = Mt2009AccountBound(item);
		const WORD cell = item->GetCell();
		const int before = (int)ch->CountSpecifyItem(nextVnum);
		const long long goldBefore = (long long)ch->GetGold();
		LPITEM scroll = scrollCell >= 0 ? ch->GetInventoryItem(scrollCell) : NULL;
		const DWORD scrollVnum = scroll ? scroll->GetVnum() : 0;
		const bool highGear = IsPlayerBotHighGear(item);	// MT2009_PLUS_BOT_HIGH_GEAR_SCROLLS_V1
		const playerbot_high_gear::EScrollKind hgKind = GetPlayerBotScrollKind(scroll);
		const int plusBefore = (int)item->GetRefineLevel();
		bool attempted;
		if (scrollCell >= 0)
		{
			ch->SetRefineMode(scrollCell);
			attempted = ch->DoRefineWithScroll(item);
			ch->ClearRefineMode();
		}
		else
			attempted = ch->DoRefine(item, false);
		LPITEM after = ch->GetInventoryItem(cell);
		if (wasWorn && after && !after->IsEquipped())
			ch->EquipItem(after);
		state.bEquipPending = true;
		state.dwNextEquipmentCheckTime = 0;
		if (!attempted)
		{
			sys_log(0, "PLAYERBOT_CHI: refine refused pid=%u name=%s what=%s vnum=%u materials=%s", ch->GetPlayerID(), ch->GetName(),
					what, oldVnum, materials);
			return false;
		}
		const bool success = (int)ch->CountSpecifyItem(nextVnum) > before;
		const bool burned = !success && (!after || (after->GetVnum() != oldVnum && after->GetVnum() + 1 != oldVnum));
		if (highGear)
			NotePlayerBotHighGearStep(ch, hgKind, plusBefore, recipe ? (int)recipe->prob : 100, success);
		const long long paid = goldBefore - (long long)ch->GetGold();
		++s_kPlayerBotChiStats.refines;
		if (success)
			++s_kPlayerBotChiStats.refineOk;
		else if (burned)
			++s_kPlayerBotChiStats.refineBurn;
		else
			++s_kPlayerBotChiStats.refineFail;
		s_kPlayerBotChiStats.spent += std::max<long long>(0, paid);
		s_mapPlayerBotChi[ch->GetPlayerID()].llSpent += std::max<long long>(0, paid);
		sys_log(0, "PLAYERBOT_CHI: refine %s pid=%u name=%s champion=%d what=%s %u -> %u (now %u) cost=%lld materials=%s scroll=%u "
				"prob=%d bound=%d->%d worn=%d gold=%lld",
				success ? "SUCCESS" : (burned ? "BURNED" : "FAILED"), ch->GetPlayerID(), ch->GetName(), GetPlayerBotChampionLevel(ch),
				what, oldVnum, nextVnum, after ? after->GetVnum() : 0, paid, materials, scrollVnum, recipe ? (int)recipe->prob : 0,
				bound ? 1 : 0, after && Mt2009AccountBound(after) ? 1 : 0, after && after->IsEquipped() ? 1 : 0, (long long)ch->GetGold());
		return true;
	}

	// The next step at the smith (one a call): the glove, the jade, the talisman (the project with its spare, else the
	// ladder's lowest pair below it).
	bool RunPlayerBotChiSmithStep(LPCHARACTER ch, TPlayerBotAIState& state)
	{
		const int target = GetPlayerBotChiTarget(ch);
		LPITEM glove = FindPlayerBotChiGlove(ch);
		if (glove && (int)(glove->GetVnum() % 10) < target && RefinePlayerBotChiPiece(ch, state, glove, true, "glove"))
			return true;
		for (int s = 0; s < 3; ++s)
		{
			LPITEM jade = FindPlayerBotChiJade(ch, s);
			if (jade && (int)(jade->GetVnum() % 10) < target && RefinePlayerBotChiPiece(ch, state, jade, true, PLAYERBOT_CHI_JADE_NAMES[s]))
				return true;
		}
		LPITEM talisman = FindPlayerBotChiTalisman(ch);
		if (!talisman || (int)(talisman->GetVnum() % 10) >= target)
			return false;
		const int kind = GetPlayerBotWillTalismanKind(talisman->GetVnum());
		const int plus = (int)(talisman->GetVnum() % 10);
		if (FindPlayerBotChiTalismanAt(ch, kind, plus, talisman, NULL) && RefinePlayerBotChiPiece(ch, state, talisman, true, "talisman"))
			return true;
		// the ladder: two spares of a lower plus make one of the next (the plain anvil - they are spares)
		for (int p = 0; p < plus; ++p)
		{
			int count = 0;
			LPITEM spare = FindPlayerBotChiTalismanAt(ch, kind, p, talisman, &count);
			if (spare && count >= 2 && RefinePlayerBotChiPiece(ch, state, spare, false, "talisman_spare"))
				return true;
		}
		return false;
	}

	bool HasPlayerBotChiSmithWork(LPCHARACTER ch)
	{
		// MT2009_PLUS_BOT_HIGH_GEAR_SCROLLS_V1: the Blacksmith's scrolls of the ladder (Zwoj Wojny, Boga Smokow, Podrecznik)
		// are made at this smith too - a Sung Ma bot sees no other Kowal
		if (PlayerBotWantsSmithScrollCraft(ch))
			return true;
		const int target = GetPlayerBotChiTarget(ch);
		int scrollCell;
		const char* why;
		LPITEM glove = FindPlayerBotChiGlove(ch);
		if (glove && (int)(glove->GetVnum() % 10) < target && CanPlayerBotChiRefine(ch, glove, true, scrollCell, why))
			return true;
		for (int s = 0; s < 3; ++s)
		{
			LPITEM jade = FindPlayerBotChiJade(ch, s);
			if (jade && (int)(jade->GetVnum() % 10) < target && CanPlayerBotChiRefine(ch, jade, true, scrollCell, why))
				return true;
		}
		LPITEM talisman = FindPlayerBotChiTalisman(ch);
		if (!talisman || (int)(talisman->GetVnum() % 10) >= target)
			return false;
		const int kind = GetPlayerBotWillTalismanKind(talisman->GetVnum());
		const int plus = (int)(talisman->GetVnum() % 10);
		if (FindPlayerBotChiTalismanAt(ch, kind, plus, talisman, NULL) && CanPlayerBotChiRefine(ch, talisman, true, scrollCell, why))
			return true;
		for (int p = 0; p < plus; ++p)
		{
			int count = 0;
			LPITEM spare = FindPlayerBotChiTalismanAt(ch, kind, p, talisman, &count);
			if (spare && count >= 2 && CanPlayerBotChiRefine(ch, spare, false, scrollCell, why))
				return true;
		}
		return false;
	}

	// Mistrz Chi's orders the bag and the purse allow now: 1 the glove, 2 a jade piece (its slot in *jadeSlot, its kind in
	// *jadeKind), 4 a Kamien Mocy Demonow (its level in *stoneLevel).
	int GetPlayerBotChiMasterWork(LPCHARACTER ch, int* jadeSlot, int* jadeKind, int* stoneLevel)
	{
		int work = 0;
		const long long spare = GetPlayerBotChiSpare(ch);
		const long long gaya = GetPlayerBotChiGayaYang();
		LPITEM glove = FindPlayerBotChiGlove(ch);
		if (!glove && (int)ch->CountSpecifyItem(PLAYERBOT_CHI_GLOVE_RUNE) >= PLAYERBOT_CHI_GLOVE_RUNES &&
				(int)ch->CountSpecifyItem(PLAYERBOT_CHI_LEATHER) >= PLAYERBOT_CHI_GLOVE_LEATHER &&
				(int)ch->CountSpecifyItem(PLAYERBOT_CHI_PATTERN) >= PLAYERBOT_CHI_GLOVE_PATTERNS &&
				ch->CountSpecifyItem(PLAYERBOT_CHI_RUNESTONE) >= 1 &&
				spare >= PLAYERBOT_CHI_GLOVE_FEE + PLAYERBOT_CHI_GLOVE_GAYA * gaya)
			work |= 1;
		const int shortKind = GetPlayerBotChiShortKind(ch);
		for (int s = 0; s < 3 && shortKind >= 0; ++s)
		{
			if (FindPlayerBotChiJade(ch, s))
				continue;
			const TPlayerBotChiJadeRecipe& r = PLAYERBOT_CHI_JADE[shortKind];
			if ((int)ch->CountSpecifyItem(r.jade) >= PLAYERBOT_CHI_JADE_N && (int)ch->CountSpecifyItem(PLAYERBOT_CHI_PLATES) >= r.plates &&
					(!r.extra || (int)ch->CountSpecifyItem(r.extra) >= r.extraN) && spare >= PLAYERBOT_CHI_JADE_FEE + r.gaya * gaya)
			{
				work |= 2;
				if (jadeSlot)
					*jadeSlot = s;
				if (jadeKind)
					*jadeKind = shortKind;
			}
			break;	// one slot at a time (the needs' order)
		}
		// a plain stone over what the glove's free sockets take, the Jadeit Slonca for it in the bag
		if (glove)
		{
			const int surplus = CountPlayerBotChiStones(ch, false) - CountPlayerBotChiFreeSockets(glove);
			for (int level = 4; level >= PLAYERBOT_CHI_STONE_MIN_LEVEL && surplus > 0; --level)
				if (ch->CountSpecifyItem(PLAYERBOT_CHI_STONE + 100 * level) > 0 &&
						(int)ch->CountSpecifyItem(PLAYERBOT_CHI_SUN_JADE) >= level + 1 && spare >= PLAYERBOT_CHI_POWER_FEE[level])
				{
					work |= 4;
					if (stoneLevel)
						*stoneLevel = level;
					break;
				}
		}
		return work;
	}

	// Mistrz Chi's craft, as the quest does it: the materials go, the Yang (the Gaya's in Yang too), the roll.
	bool CraftPlayerBotChi(LPCHARACTER ch, const char* what, const DWORD* vnums, const int* counts, int n, long long fee, int gayaN,
			int pct, DWORD result)
	{
		if (ch->GetEmptyInventory(1) < 0)
			return false;
		const long long gayaYang = (long long)gayaN * GetPlayerBotChiGayaYang();
		const long long cost = fee + gayaYang;
		if (GetPlayerBotChiSpare(ch) < cost)
			return false;
		char materials[160] = "";
		size_t used = 0;
		for (int i = 0; i < n; ++i)
		{
			if (!vnums[i] || counts[i] <= 0)
				continue;
			if ((int)ch->CountSpecifyItem(vnums[i]) < counts[i])
				return false;
			used += snprintf(materials + used, sizeof(materials) - used, "%s%u:%d", used ? "," : "", vnums[i], counts[i]);
		}
		for (int i = 0; i < n; ++i)
			if (vnums[i] && counts[i] > 0)
				ch->RemoveSpecifyItem(vnums[i], counts[i]);
		PlayerBotChangeGold(ch, -cost);
		const bool ok = number(1, 100) <= pct;
		LPITEM made = ok ? ch->AutoGiveItem(result, 1, -1, false) : NULL;
		if (made)
			LogManager::instance().ItemLog(ch, made, "PLAYERBOT_CHI", what);
		s_kPlayerBotChiStats.spent += cost;
		s_kPlayerBotChiStats.gayaYang += gayaYang;
		s_mapPlayerBotChi[ch->GetPlayerID()].llSpent += cost;
		sys_log(0, "PLAYERBOT_CHI: craft %s pid=%u name=%s champion=%d what=%s result=%u cost=%lld (fee=%lld gaya=%d gaya_yang=%lld) "
				"materials=%s pct=%d gold=%lld",
				made ? "SUCCESS" : "FAILED", ch->GetPlayerID(), ch->GetName(), GetPlayerBotChampionLevel(ch), what, result, cost, fee,
				gayaN, gayaYang, materials, pct, (long long)ch->GetGold());
		return true;
	}

	bool RunPlayerBotChiMasterStep(LPCHARACTER ch, TPlayerBotAIState& state)
	{
		int jadeSlot = -1, jadeKind = -1, stoneLevel = -1;
		const int work = GetPlayerBotChiMasterWork(ch, &jadeSlot, &jadeKind, &stoneLevel);
		bool done = false;
		if (work & 1)
		{
			const DWORD v[4] = { PLAYERBOT_CHI_GLOVE_RUNE, PLAYERBOT_CHI_LEATHER, PLAYERBOT_CHI_PATTERN, PLAYERBOT_CHI_RUNESTONE };
			const int c[4] = { PLAYERBOT_CHI_GLOVE_RUNES, PLAYERBOT_CHI_GLOVE_LEATHER, PLAYERBOT_CHI_GLOVE_PATTERNS, 1 };
			done = CraftPlayerBotChi(ch, "glove", v, c, 4, PLAYERBOT_CHI_GLOVE_FEE, PLAYERBOT_CHI_GLOVE_GAYA, PLAYERBOT_CHI_GLOVE_PCT,
					PLAYERBOT_CHI_GLOVE_VNUM);
		}
		else if ((work & 2) && jadeSlot >= 0 && jadeKind >= 0)
		{
			const TPlayerBotChiJadeRecipe& r = PLAYERBOT_CHI_JADE[jadeKind];
			const DWORD v[3] = { r.jade, PLAYERBOT_CHI_PLATES, r.extra };
			const int c[3] = { PLAYERBOT_CHI_JADE_N, r.plates, r.extraN };
			done = CraftPlayerBotChi(ch, PLAYERBOT_CHI_JADE_NAMES[jadeSlot], v, c, 3, PLAYERBOT_CHI_JADE_FEE, r.gaya, PLAYERBOT_CHI_JADE_PCT,
					PLAYERBOT_CHI_JADE_FIRST[jadeSlot] + r.offset);
		}
		else if ((work & 4) && stoneLevel >= 0)
		{
			const DWORD v[2] = { PLAYERBOT_CHI_STONE + 100 * (DWORD)stoneLevel, PLAYERBOT_CHI_SUN_JADE };
			const int c[2] = { 1, stoneLevel + 1 };
			done = CraftPlayerBotChi(ch, "power_stone", v, c, 2, PLAYERBOT_CHI_POWER_FEE[stoneLevel], 0, PLAYERBOT_CHI_POWER_PCT,
					PLAYERBOT_CHI_POWER_STONE + 100 * (DWORD)stoneLevel);
			if (done)
				++s_kPlayerBotChiStats.power;
		}
		if (done && !(work & 4))
			++s_kPlayerBotChiStats.crafts;
		if (done)
		{
			state.bEquipPending = true;
			state.dwNextEquipmentCheckTime = 0;
		}
		return done;
	}

	// ------------------------------------------------------------ the stones (where the bot stands)

	// One stone into the glove's free socket: a Kamien Mocy Demonow first, the highest level first. The glove off and on
	// again (the engine takes no stone into a worn glove).
	bool SocketPlayerBotChiStone(LPCHARACTER ch, TPlayerBotAIState& state)
	{
		LPITEM glove = FindPlayerBotChiGlove(ch);
		if (!glove || CountPlayerBotChiFreeSockets(glove) == 0 || glove->isLocked() || glove->IsExchanging())
			return false;
		LPITEM stone = NULL;
		for (int level = 4; level >= PLAYERBOT_CHI_STONE_MIN_LEVEL && !stone; --level)
			for (int p = 1; p >= 0 && !stone; --p)
			{
				const DWORD vnum = (p ? PLAYERBOT_CHI_POWER_STONE : PLAYERBOT_CHI_STONE) + 100 * level;
				for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS && !stone; ++cell)
				{
					LPITEM item = ch->GetInventoryItem(cell);
					if (item && item->GetCell() == cell && item->GetVnum() == vnum && !item->isLocked() && !item->IsExchanging())
						stone = item;
				}
			}
		if (!stone)
			return false;
		const bool wasWorn = glove->IsEquipped();
		if (wasWorn && (ch->GetEmptyInventory(glove->GetSize()) < 0 || !ch->UnequipItem(glove) || glove->IsEquipped()))
			return false;
		const DWORD stoneVnum = stone->GetVnum();
		const int freeBefore = CountPlayerBotChiFreeSockets(glove);
		const int willBefore = CountPlayerBotChiWillSockets(glove);
		long sockets[3] = { 0, 0, 0 };
		const bool used = Mt2009GloveUseStone(ch, stone, glove);
		for (int i = 0; i < 3 && i < ITEM_SOCKET_MAX_NUM; ++i)
			sockets[i] = glove->GetSocket(i);
		if (wasWorn && !glove->IsEquipped())
			ch->EquipItem(glove);
		state.bEquipPending = true;
		state.dwNextEquipmentCheckTime = 0;
		if (!used)
			return false;
		const bool ok = CountPlayerBotChiWillSockets(glove) > willBefore;
		++s_kPlayerBotChiStats.stones;
		if (ok)
			++s_kPlayerBotChiStats.stonesOk;
		sys_log(0, "PLAYERBOT_CHI: stone in %s pid=%u name=%s champion=%d glove=%u stone=%u free=%d->%d sockets=%ld,%ld,%ld worn=%d",
				ok ? "SUCCESS" : "FAILED", ch->GetPlayerID(), ch->GetName(), GetPlayerBotChampionLevel(ch), glove->GetVnum(), stoneVnum,
				freeBefore, CountPlayerBotChiFreeSockets(glove), sockets[0], sockets[1], sockets[2], glove->IsEquipped() ? 1 : 0);
		return true;
	}

	// ------------------------------------------------------------ the operator's test file, the census

	void LogPlayerBotChiPlan(LPCHARACTER ch, const char* why)
	{
		const TPlayerBotChiNeeds& n = GetPlayerBotChiNeeds(ch);
		LPITEM glove = FindPlayerBotChiGlove(ch);
		LPITEM talisman = FindPlayerBotChiTalisman(ch);
		LPITEM jade[3] = { FindPlayerBotChiJade(ch, 0), FindPlayerBotChiJade(ch, 1), FindPlayerBotChiJade(ch, 2) };
		char missing[256] = "";
		size_t used = 0;
		for (std::map<DWORD, int>::const_iterator it = n.missing.begin(); it != n.missing.end() && used + 16 < sizeof(missing); ++it)
			used += snprintf(missing + used, sizeof(missing) - used, "%s%u:%d", used ? "," : "", it->first, it->second);
		int js = -1, jk = -1, sl = -1;
		sys_log(0, "PLAYERBOT_CHI: %s pid=%u name=%s champion=%d target=+%d glove=%u free_sockets=%d stones=%d bracelet=%u necklace=%u "
				"earrings=%u talisman=%u master_work=%d smith_work=%d missing=%s gold=%lld spare=%lld",
				why, ch->GetPlayerID(), ch->GetName(), GetPlayerBotChampionLevel(ch), GetPlayerBotChiTarget(ch), glove ? glove->GetVnum() : 0,
				CountPlayerBotChiFreeSockets(glove), CountPlayerBotChiStones(ch, false), jade[0] ? jade[0]->GetVnum() : 0,
				jade[1] ? jade[1]->GetVnum() : 0, jade[2] ? jade[2]->GetVnum() : 0, talisman ? talisman->GetVnum() : 0,
				GetPlayerBotChiMasterWork(ch, &js, &jk, &sl), HasPlayerBotChiSmithWork(ch) ? 1 : 0, used ? missing : "none",
				(long long)ch->GetGold(), GetPlayerBotChiSpare(ch));
	}

	void RunPlayerBotChiTestFile(DWORD dwNow)
	{
		if (dwNow - s_kPlayerBotChiStats.dwLastTestLook < 10000)
			return;
		s_kPlayerBotChiStats.dwLastTestLook = dwNow;
		FILE* fp = fopen(PLAYERBOT_CHI_TEST_FILE, "r");
		if (!fp)
			return;
		char line[128];
		std::vector<std::string> lines;
		while (fgets(line, sizeof(line), fp))
			lines.push_back(line);
		fclose(fp);
		char done[128];
		snprintf(done, sizeof(done), "%s.done", PLAYERBOT_CHI_TEST_FILE);
		rename(PLAYERBOT_CHI_TEST_FILE, done);
		for (size_t l = 0; l < lines.size(); ++l)
		{
			char cmd[32] = "";
			if (sscanf(lines[l].c_str(), "%31s", cmd) < 1)
				continue;
			int looked = 0;
			for (TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.begin(); st != s_mapPlayerBotAIStates.end(); ++st)
			{
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(st->first);
				if (!ch || !IsPlayerBotChiUser(ch))
					continue;
				++looked;
				if (!strcmp(cmd, "status"))
				{
					s_mapPlayerBotChiNeeds.erase(ch->GetPlayerID());
					LogPlayerBotChiPlan(ch, "test status");
				}
				else if (!strcmp(cmd, "now"))
				{
					TPlayerBotChi& c = s_mapPlayerBotChi[ch->GetPlayerID()];
					c.dwLastVisitEnd = 0;
					c.dwNextLook = 0;
				}
			}
			sys_log(0, "PLAYERBOT_CHI: test %s champions_here=%d", cmd, looked);
		}
	}

	void LogPlayerBotChiCensus(DWORD dwNow)
	{
		if (s_kPlayerBotChiStats.dwLastCensus != 0 && dwNow - s_kPlayerBotChiStats.dwLastCensus < PLAYERBOT_CHI_CENSUS_MS)
			return;
		s_kPlayerBotChiStats.dwLastCensus = dwNow;
		const TPlayerBotChiStats& s = s_kPlayerBotChiStats;
		sys_log(0, "PLAYERBOT_CHI: census visits=%u refines=%u ok=%u failed=%u burned=%u scroll_waits=%u crafts=%u power_stones=%u "
				"stones_in=%u stones_ok=%u bought=%u bought_yang=%lld spent=%lld gaya_yang=%lld",
				s.visits, s.refines, s.refineOk, s.refineFail, s.refineBurn, s.scrollWaits, s.crafts, s.power, s.stones, s.stonesOk,
				s.bought, s.boughtYang, s.spent, s.gayaYang);
	}

	// ------------------------------------------------------------ the errand

	int EndPlayerBotChiVisit(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotChi& c, DWORD dwNow, const char* why)
	{
		if (c.bPhase != CHI_PHASE_NONE)
			sys_log(0, "PLAYERBOT_CHI: visit over pid=%u name=%s why=%s actions=%d spent=%lld took_s=%u gold=%lld", ch->GetPlayerID(),
					ch->GetName(), why, c.iActions, c.llSpent, (dwNow - c.dwVisitSince) / 1000, (long long)ch->GetGold());
		c.bPhase = CHI_PHASE_NONE;
		c.dwLastVisitEnd = dwNow ? dwNow : 1;
		c.dwNextAction = 0;
		state.bEquipPending = true;
		state.dwNextEquipmentCheckTime = 0;
		std::map<DWORD, TPlayerBotSungmaBot>::iterator b = s_mapPlayerBotSungma.find(ch->GetPlayerID());
		if (b != s_mapPlayerBotSungma.end())
			b->second.dwWalkSince = 0;	// the map's pick takes it back (as after Dongan's errand)
		s_mapPlayerBotChiNeeds.erase(ch->GetPlayerID());
		return -1;
	}

	// ManagePlayerBotSungmaResident, after Dongan's own errand: -1 not on a visit (the stay goes on), 1 this tick is the
	// visit's. base: the map it stands on (an instance's base).
	int ManagePlayerBotYoharaChi(LPCHARACTER ch, TPlayerBotAIState& state, long base, DWORD dwNow)
	{
		RunPlayerBotChiTestFile(dwNow);
		LogPlayerBotChiCensus(dwNow);
		if (!ch || ch->IsDead() || state.bRecoveringAfterDeath || !IsPlayerBotChiUser(ch))
			return -1;
		TPlayerBotChi& c = s_mapPlayerBotChi[ch->GetPlayerID()];
		std::map<DWORD, TPlayerBotSungmaBot>::const_iterator sb = s_mapPlayerBotSungma.find(ch->GetPlayerID());
		const bool donganErrand = sb != s_mapPlayerBotSungma.end() && sb->second.bErrand;
		const bool busy = state.dwTargetVID != 0 || ch->GetVictim() != NULL || state.bTacticalRetreat ||
				ch->GetHP() * 100 < ch->GetMaxHP() * 40 || (ch->GetParty() && ch->GetParty()->GetMemberCount() >= 3) ||
				IsPlayerBotOnDungeonRun(ch->GetPlayerID()) || ch->GetExchange() || ch->GetMyShop() || donganErrand;
		if (c.bPhase == CHI_PHASE_NONE)
		{
			if ((int)(dwNow - c.dwNextLook) < 0)
				return -1;
			c.dwNextLook = dwNow + PLAYERBOT_CHI_LOOK_MS + number(0, 15000);
			if (busy)
				return -1;
			// item 19: a stone into the glove where the bot stands
			SocketPlayerBotChiStone(ch, state);
			if (c.dwLastVisitEnd != 0 && dwNow - c.dwLastVisitEnd < PLAYERBOT_CHI_VISIT_GAP_MS)
				return -1;
			if (!IsPlayerBotMapHostedHere(PLAYERBOT_MAP_SUNGMA_DONGAN))
				return -1;
			const int master = GetPlayerBotChiMasterWork(ch, NULL, NULL, NULL);
			const bool smith = HasPlayerBotChiSmithWork(ch);
			if (!master && !smith)
			{
				// a worn piece's step waiting for a scroll: once in a while in the log
				LPITEM glove = FindPlayerBotChiGlove(ch);
				int cell;
				const char* why = NULL;
				if (glove && (int)(glove->GetVnum() % 10) < GetPlayerBotChiTarget(ch) && !CanPlayerBotChiRefine(ch, glove, true, cell, why) &&
						why && !strcmp(why, "scroll"))
				{
					++s_kPlayerBotChiStats.scrollWaits;
					PlayerBotLogThrottled("chi_scroll_wait", dwNow, "PLAYERBOT_CHI: waits for a scroll pid=%u name=%s glove=%u",
							ch->GetPlayerID(), ch->GetName(), glove->GetVnum());
				}
				return -1;
			}
			c.bPhase = master ? CHI_PHASE_MASTER : CHI_PHASE_SMITH;
			c.dwVisitSince = dwNow ? dwNow : 1;
			c.dwNextAction = 0;
			c.iActions = 0;
			c.llSpent = 0;
			c.lStandX = c.lStandY = 0;
			++s_kPlayerBotChiStats.visits;
			LogPlayerBotChiPlan(ch, "order go");
		}
		if (busy)
			return EndPlayerBotChiVisit(ch, state, c, dwNow, donganErrand ? "dongan_errand" : "busy");
		if (dwNow - c.dwVisitSince >= PLAYERBOT_CHI_VISIT_MS)
			return EndPlayerBotChiVisit(ch, state, c, dwNow, "timeout");
		const bool atMaster = c.bPhase == CHI_PHASE_MASTER;
		// the stand by the NPC the arrival's ground reaches (MT2009_PLUS_BOT_YOHARA_FIGHT_V1's rule for Dongan's merchants)
		if (c.lStandX == 0)
		{
			const TPlayerBotSungmaMerchant npc = { atMaster ? PLAYERBOT_CHI_NPC : PLAYERBOT_CHI_SMITH,
					atMaster ? PLAYERBOT_CHI_NPC_X : PLAYERBOT_CHI_SMITH_X, atMaster ? PLAYERBOT_CHI_NPC_Y : PLAYERBOT_CHI_SMITH_Y,
					BOT_MERCHANT_MISC, atMaster ? "dongan_chi" : "dongan_smith" };
			if (!GetPlayerBotSungmaMerchantApproach(ch->GetPlayerID(), npc, atMaster ? 10 : 11, c.lStandX, c.lStandY))
				return EndPlayerBotChiVisit(ch, state, c, dwNow, "unreachable");
		}
		const long ax = c.lStandX, ay = c.lStandY;
		if (base != PLAYERBOT_MAP_SUNGMA_DONGAN)
		{
			s_szPlayerBotTransitionRefusal = NULL;
			if (!TransitionPlayerBotMap(ch, state, PLAYERBOT_MAP_SUNGMA_DONGAN, ax, ay, dwNow, "sungma_chi"))
				return EndPlayerBotChiVisit(ch, state, c, dwNow, s_szPlayerBotTransitionRefusal ? s_szPlayerBotTransitionRefusal : "warp_refused");
			return 1;
		}
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		if (DISTANCE_APPROX(ch->GetX() - ax, ch->GetY() - ay) > PLAYERBOT_CHI_REACH)
		{
			SetPlayerBotAction(state, BOT_ACTION_SHOP, dwNow);
			MovePlayerBot(ch, ax, ay, dwNow, 6, true, false, false, false);
			return 1;
		}
		ch->Stop();
		if (c.dwNextAction == 0)
		{
			c.dwNextAction = dwNow + number(2500, 5000);
			return 1;
		}
		if ((int)(dwNow - c.dwNextAction) < 0)
			return 1;
		c.dwNextAction = dwNow + number(2500, 5000);
		const bool did = c.iActions < PLAYERBOT_CHI_VISIT_ACTIONS &&
				(atMaster ? RunPlayerBotChiMasterStep(ch, state)
					: (CraftPlayerBotSmithScrolls(ch, "chi") > 0 || RunPlayerBotChiSmithStep(ch, state)));	// MT2009_PLUS_BOT_HIGH_GEAR_SCROLLS_V1
		if (did)
		{
			++c.iActions;
			s_mapPlayerBotChiNeeds.erase(ch->GetPlayerID());
			return 1;
		}
		if (atMaster && c.iActions < PLAYERBOT_CHI_VISIT_ACTIONS && HasPlayerBotChiSmithWork(ch))
		{
			c.bPhase = CHI_PHASE_SMITH;
			c.dwNextAction = 0;
			c.lStandX = c.lStandY = 0;
			return 1;
		}
		// the stone a craft made, into the glove before the way back
		SocketPlayerBotChiStone(ch, state);
		return EndPlayerBotChiVisit(ch, state, c, dwNow, "done");
	}
}

#endif
