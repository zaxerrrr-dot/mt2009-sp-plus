#ifndef __INC_METIN2_PLAYERBOT_RUNES_H__
#define __INC_METIN2_PLAYERBOT_RUNES_H__

// MT2009_PLUS_BOT_RUNES_V1 - the bots and the Runy Wykuwania (MT2009_PLUS_RUNY_WYKUWANIA_V1, tools/runy/gen_runy.py;
// the owner's decision of 5 November 2026: "teach the playerbots the rune system").
//
// What a rune is (the players' own numbers, copied - a change there is a change here): 79605-79659, 11 kinds x 1*..5*,
// vnum = 79605 + kind * 5 + grade - 1; in the crafting window's "Podwyzsz szanse" slot it adds +1 / +2 / +5 / +10 / +20 %
// to a recipe of its category (game/cube_improve.txt, cube.cpp's categories) and one goes with every attempt. Yu-Hwan
// (20017, the second villages 3 / 23 / 43) turns two runes of a grade into one of the next: 40 %, 2 / 4 / 6 / 10 Gaya and
// 200 000 / 400 000 / 600 000 / 1 000 000 Yang (game/cube.runy.txt) - a recipe of the "pozostale" category (5), so the
// Runa Wyk. Poz. Prz. raises it (the owner: rune upgrades stay "pozostale").
//
// What a bot does with them:
//   * keeps them - never the merchant's, never a counter's, never the Dozorca's (IsPlayerBotKeptCraftGoods,
//     IsPlayerBotJunkItem ask IsPlayerBotRuneVnum);
//   * uses the right one where the players can: a crafting-window recipe of the rune's category - the belts at Mistrz
//     (category 3, Runa Wykuwania Pasow, playerbot_belts.h) and the helmets of Jaharr / the armours of Kawuco (category
//     0, Runa Wykuwania Zbroi, playerbot_yohara_gear2.h) - UsePlayerBotCraftRune: of the runes of that category in the
//     bag the lowest grade that takes the chance to 100 %, else the highest, never above the craft's own cap (a 5* is
//     not spent on a level-50 belt); none when the chance is 100 % already. Angmur's (a quest) and Seon-Pyeong's (the
//     anvil, 100 %) take no rune - the players' window takes none there either;
//   * upgrades them at Yu-Hwan (the errand below): a pair of one kind and grade over its keep (one of every grade of a
//     kind it crafts with stays for the next craft; none of other kinds), its Yang over PLAYERBOT_RUNE_UPGRADE_PURSE_PCT
//     of the spare purse, the Gaya from its own Gaya, else in Yang at the bots' grinding rate (GetPlayerBotChiGayaYang,
//     25 000 a Gaya - a bot has no Gaya shop to go to, as Mistrz Chi's orders); a Runa Wyk. Poz. Prz. of a lower grade
//     than the result goes into the slot (the cube's roll - the runes, the Yang and the Gaya go whatever it says);
//   * values them (GetPlayerBotRuneValue: what one costs to make - the Gaya at the same rate, Yu-Hwan's 40 % - times
//     PLAYERBOT_RUNE_VALUE_PCT, never under the NPC's price): the bots' asking price of a rune (the market, the chat
//     deals, the trade window - GetPlayerBotShopAskingPriceRaw), and what it pays for a 5* (the only grade that trades)
//     on a counter: a 5* of a kind it crafts with, while it holds none, at most the value, out of
//     PLAYERBOT_RUNE_BUY_PURSE_PCT of the spare purse.
//
// Where they come from (besides the Kolo Losu's 5* and the counters), two paths the owner wants, both prepared and OFF:
//   (a) a challenge's reward: Mt2009PlayerBotRuneReward(bot, kind, grade, count, reason, force) - kind -1: the kind
//       the bot crafts with (its "auto" kind: a belt maker's Pasow, a level-66+ bot's Zbroi, else Poz. Prz.); does
//       nothing while the event flag m2_bot_rune_rewards_on is 0 unless forced. The GM command (game master level
//       GM_HIGH_WIZARD, server-patches/runyboty):
//         /bot_runa                                           the switches and the census of this core
//         /bot_runa daj <bot name|pid> <rune> [count]         to one bot
//         /bot_runa wszystkim <rune> [count] [lv_min] [lv_max] [empire 1-3, 0 all] [limit, 0 all]
//       <rune>: a vnum 79605-79659, or <kind>:<grade> - pasy bron zbroja pozostale akcesoria ksiegi zestbron
//       zesthelm zestzbroja rekawice zwierzaki, or auto (each bot's own kind); the command always gives (forced).
//   (b) the bots' exchange at Yu-Hwan (bots only - no NPC window, nothing a person sees; event flag
//       m2_bot_rune_exchange_on, default 0 = OFF): on the Yu-Hwan visit a bot changes a table line's input for a rune
//       of a kind it crafts with, while it holds fewer than PLAYERBOT_RUNE_EXCHANGE_KIND_CAP runes of that kind, at
//       most PLAYERBOT_RUNE_EXCHANGE_PER_VISIT a visit, the Yang out of PLAYERBOT_RUNE_EXCHANGE_PURSE_PCT of the spare
//       purse. The table: the file playerbot_rune_exchange.txt in the core's directory (read again every five
//       minutes; lines "<input vnum> <input count> <yang|gaya> <rune> [rune count]", input vnum 0 - Yang only,
//       "gaya" - the rune's Portowy Sklep Gaya price at the bots' Gaya rate; # comments), else the defaults:
//         0      0    gaya  auto:1     the 1* of its kind for its Gaya-shop price in Yang (10 Gaya = 250 000)
//         95926  150  0     auto:1     150 Kamyki (what the Statua Wojownika grinds ~10 Gaya out of) for one 1*
//
// The errand (ManagePlayerBotRunes, the AI's tick beside the gear2 errand): with an upgrade or an exchange to do, the bot
// goes to the second village of its kingdom (on the same core - TransitionPlayerBotMap, as Jaharr's errand goes to the
// first), walks to Yu-Hwan, at most PLAYERBOT_RUNE_VISIT_ACTIONS steps a visit, PLAYERBOT_RUNE_CHECK_* between looks. A
// Sung Ma bot does not leave its map for it (its trade trip home does not wait for runes).
//
// The log: PLAYERBOT_RUNES (used / upgrade SUCCESS / FAILED / exchange / reward / bought / going / visit over / census
// every ten minutes). Event flag m2_bot_runes_off stops all of it but the keep (a rune is never sold off by a bot).
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_yohara_gear2.h, in the anonymous
// namespace; the hooks the earlier fragments call are declared ahead in playerbot_types.h. The command and the reward
// are global (after the namespace).

namespace
{
	const DWORD PLAYERBOT_RUNE_FIRST = 79605;
	const int PLAYERBOT_RUNE_KINDS = 11;
	const int PLAYERBOT_RUNE_GRADES = 5;
	const DWORD PLAYERBOT_RUNE_LAST = PLAYERBOT_RUNE_FIRST + PLAYERBOT_RUNE_KINDS * PLAYERBOT_RUNE_GRADES - 1;	// 79659
	const DWORD PLAYERBOT_RUNE_YU_HWAN = 20017;
	// tools/runy/gen_runy.py: BONUS, UP_GAYA, UP_YANG, UP_PCT and the kinds' categories / 1* Gaya
	const int PLAYERBOT_RUNE_BONUS[PLAYERBOT_RUNE_GRADES + 1] = { 0, 1, 2, 5, 10, 20 };
	const int PLAYERBOT_RUNE_UP_GAYA[PLAYERBOT_RUNE_GRADES + 1] = { 0, 0, 2, 4, 6, 10 };
	const long long PLAYERBOT_RUNE_UP_YANG[PLAYERBOT_RUNE_GRADES + 1] = { 0, 0, 200000, 400000, 600000, 1000000 };
	const int PLAYERBOT_RUNE_UP_PCT = 40;
	const int PLAYERBOT_RUNE_CATEGORY_OTHER = 5;		// cube.cpp MT2009_CUBE_CAT_ETC - Yu-Hwan's upgrades
	enum { PLAYERBOT_RUNE_KIND_BELT = 0, PLAYERBOT_RUNE_KIND_ARMOUR = 2, PLAYERBOT_RUNE_KIND_OTHER = 3 };
	struct TPlayerBotRuneKind { const char* key; int category; int gaya; };
	const TPlayerBotRuneKind PLAYERBOT_RUNE_KIND_TABLE[PLAYERBOT_RUNE_KINDS] = {
		{ "pasy", 3, 10 }, { "bron", 1, 10 }, { "zbroja", 0, 10 }, { "pozostale", 5, 10 }, { "akcesoria", 2, 10 },
		{ "ksiegi", 11, 10 }, { "zestbron", 7, 30 }, { "zesthelm", 9, 10 }, { "zestzbroja", 8, 30 }, { "rekawice", 12, 10 },
		{ "zwierzaki", 10, 30 },
	};

	const DWORD PLAYERBOT_RUNE_CHECK_MIN_MS = 5 * 60 * 1000;
	const DWORD PLAYERBOT_RUNE_CHECK_MAX_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_RUNE_VISIT_MS = 4 * 60 * 1000;
	const DWORD PLAYERBOT_RUNE_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_RUNE_TABLE_MS = 5 * 60 * 1000;
	const int PLAYERBOT_RUNE_VISIT_ACTIONS = 6;
	const int PLAYERBOT_RUNE_REACH = 350;
	const int PLAYERBOT_RUNE_UPGRADE_PURSE_PCT = 50;
	const int PLAYERBOT_RUNE_VALUE_PCT = 60;
	const int PLAYERBOT_RUNE_BUY_PURSE_PCT = 30;
	const int PLAYERBOT_RUNE_EXCHANGE_KIND_CAP = 6;
	const int PLAYERBOT_RUNE_EXCHANGE_PER_VISIT = 2;
	const int PLAYERBOT_RUNE_EXCHANGE_PURSE_PCT = 25;
	const char* const PLAYERBOT_RUNE_EXCHANGE_FILE = "playerbot_rune_exchange.txt";

	// Yu-Hwan in the second villages: npc.txt cells (415,638) of metin2_map_a3 on (307200,819200), (376,318) of
	// metin2_map_b3 on (102400,204800), (384,454) of metin2_map_c3 on (819200,204800).
	struct TPlayerBotRuneSpot { long lMap, lX, lY; };
	const TPlayerBotRuneSpot PLAYERBOT_RUNE_SPOTS[] = {
		{ 3, 348700, 883000 }, { 23, 140000, 236600 }, { 43, 857600, 250200 },
	};
	const int PLAYERBOT_RUNE_SPOT_COUNT = sizeof(PLAYERBOT_RUNE_SPOTS) / sizeof(PLAYERBOT_RUNE_SPOTS[0]);

	// The bag's runes: [kind][grade] (grade 1..5), read in one pass over the bag.
	struct TPlayerBotRuneBag
	{
		int n[PLAYERBOT_RUNE_KINDS][PLAYERBOT_RUNE_GRADES + 1];
		int total;
		TPlayerBotRuneBag() : total(0) { memset(n, 0, sizeof(n)); }
		int Kind(int kind) const
		{
			int s = 0;
			for (int g = 1; g <= PLAYERBOT_RUNE_GRADES; ++g)
				s += n[kind][g];
			return s;
		}
	};

	// An exchange line (the file's or the defaults): kind -1 - the bot's own ("auto").
	struct TPlayerBotRuneExchangeLine
	{
		DWORD dwInput;
		int iInputCount;
		long long llYang;
		bool bGayaPrice;
		int iKind, iGrade, iCount;
	};

	enum { PLAYERBOT_RUNE_PHASE_NONE, PLAYERBOT_RUNE_PHASE_YUHWAN };

	struct TPlayerBotRunes
	{
		DWORD dwNextCheck, dwVisitStart, dwNextAction;
		BYTE bPhase;
		int iSpot, iActions, iExchanges;
		TPlayerBotRunes() : dwNextCheck(0), dwVisitStart(0), dwNextAction(0), bPhase(PLAYERBOT_RUNE_PHASE_NONE), iSpot(-1),
			iActions(0), iExchanges(0) {}
	};
	std::map<DWORD, TPlayerBotRunes> s_mapPlayerBotRunes;

	struct TPlayerBotRuneStats
	{
		unsigned int used[PLAYERBOT_RUNE_GRADES + 1], upgradeOk, upgradeFail, exchanges, rewards, bought, trips, visits;
		long long upgradeYang, gayaYang, exchangeYang, boughtYang;
		DWORD dwLastCensus;
		TPlayerBotRuneStats() : upgradeOk(0), upgradeFail(0), exchanges(0), rewards(0), bought(0), trips(0), visits(0),
			upgradeYang(0), gayaYang(0), exchangeYang(0), boughtYang(0), dwLastCensus(0)
		{
			memset(used, 0, sizeof(used));
		}
	};
	TPlayerBotRuneStats s_kPlayerBotRuneStats;

	std::vector<TPlayerBotRuneExchangeLine> s_vecPlayerBotRuneExchange;
	DWORD s_dwPlayerBotRuneExchangeReadAt = 0;
	bool s_bPlayerBotRuneExchangeFromFile = false;

	// ------------------------------------------------------------ what a rune is

	bool IsPlayerBotRuneVnum(DWORD vnum)
	{
		return vnum >= PLAYERBOT_RUNE_FIRST && vnum <= PLAYERBOT_RUNE_LAST;
	}

	int GetPlayerBotRuneKind(DWORD vnum)
	{
		return IsPlayerBotRuneVnum(vnum) ? (int)((vnum - PLAYERBOT_RUNE_FIRST) / PLAYERBOT_RUNE_GRADES) : -1;
	}

	int GetPlayerBotRuneGrade(DWORD vnum)
	{
		return IsPlayerBotRuneVnum(vnum) ? (int)((vnum - PLAYERBOT_RUNE_FIRST) % PLAYERBOT_RUNE_GRADES) + 1 : 0;
	}

	DWORD GetPlayerBotRuneVnum(int kind, int grade)
	{
		if (kind < 0 || kind >= PLAYERBOT_RUNE_KINDS || grade < 1 || grade > PLAYERBOT_RUNE_GRADES)
			return 0;
		return PLAYERBOT_RUNE_FIRST + (DWORD)(kind * PLAYERBOT_RUNE_GRADES + grade - 1);
	}

	int GetPlayerBotRuneKindOfCategory(int category)
	{
		for (int k = 0; k < PLAYERBOT_RUNE_KINDS; ++k)
			if (PLAYERBOT_RUNE_KIND_TABLE[k].category == category)
				return k;
		return -1;
	}

	bool IsPlayerBotRunesOff()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_bot_runes_off") != 0;
	}

	bool IsPlayerBotRuneExchangeOn()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_bot_rune_exchange_on") != 0;
	}

	bool IsPlayerBotRuneRewardOn()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_bot_rune_rewards_on") != 0;
	}

	bool IsPlayerBotRuneBot(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && ch->GetDesc()->IsBot() && ch->IsItemLoaded() &&
				!IsPlayerBotSidekickPID(ch->GetPlayerID());
	}

	void ReadPlayerBotRuneBag(LPCHARACTER ch, TPlayerBotRuneBag& bag)
	{
		bag = TPlayerBotRuneBag();
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || !IsPlayerBotRuneVnum(item->GetVnum()))
				continue;
			bag.n[GetPlayerBotRuneKind(item->GetVnum())][GetPlayerBotRuneGrade(item->GetVnum())] += (int)item->GetCount();
			bag.total += (int)item->GetCount();
		}
	}

	// The kinds a bot crafts with (a bit a kind): a belt maker's Pasow, a level-66+ bot's Zbroi (Jaharr, Kawuco) - and
	// Poz. Prz. for its own upgrades at Yu-Hwan.
	unsigned int GetPlayerBotRuneKindsUsed(LPCHARACTER ch)
	{
		unsigned int kinds = 1U << PLAYERBOT_RUNE_KIND_OTHER;
		if (IsPlayerBotBeltMaker(ch))
			kinds |= 1U << PLAYERBOT_RUNE_KIND_BELT;
		if (IsPlayerBotGear2Bot(ch))
			kinds |= 1U << PLAYERBOT_RUNE_KIND_ARMOUR;
		return kinds;
	}

	// "auto": the kind of its crafts first.
	int GetPlayerBotRuneOwnKind(LPCHARACTER ch)
	{
		if (IsPlayerBotBeltMaker(ch))
			return PLAYERBOT_RUNE_KIND_BELT;
		if (IsPlayerBotGear2Bot(ch))
			return PLAYERBOT_RUNE_KIND_ARMOUR;
		return PLAYERBOT_RUNE_KIND_OTHER;
	}

	long long GetPlayerBotRuneSpare(LPCHARACTER ch)
	{
		return (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
	}

	// ------------------------------------------------------------ the value

	// What one costs to make: the 1* its Gaya, every grade above two of the one below + its Gaya and Yang, over 40 %.
	long long GetPlayerBotRuneMakeCost(int kind, int grade)
	{
		const long long gayaYang = GetPlayerBotChiGayaYang();
		long long cost = (long long)PLAYERBOT_RUNE_KIND_TABLE[kind].gaya * gayaYang;
		for (int g = 2; g <= grade; ++g)
			cost = (2 * cost + PLAYERBOT_RUNE_UP_GAYA[g] * gayaYang + PLAYERBOT_RUNE_UP_YANG[g]) * 100 / PLAYERBOT_RUNE_UP_PCT;
		return cost;
	}

	long long GetPlayerBotRuneValue(DWORD vnum)
	{
		const int kind = GetPlayerBotRuneKind(vnum);
		if (kind < 0)
			return 0;
		long long value = GetPlayerBotRuneMakeCost(kind, GetPlayerBotRuneGrade(vnum)) * PLAYERBOT_RUNE_VALUE_PCT / 100;
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		if (proto)
			value = std::max<long long>(value, (long long)proto->dwShopBuyPrice / 5);
		return std::min<long long>(value, 0xFFFFFFF0LL);
	}

	// ------------------------------------------------------------ the crafting window's slot

	// A craft of `category` at `basePct`: the rune of that category for it (the lowest grade that takes the chance to
	// 100 %, else the highest, at most maxGrade) goes - its bonus back; 0 with none.
	int UsePlayerBotCraftRune(LPCHARACTER ch, int category, int basePct, int maxGrade, const char* craft, DWORD reward)
	{
		if (!ch || basePct >= 100 || IsPlayerBotRunesOff() || !IsPlayerBotRuneBot(ch))
			return 0;
		const int kind = GetPlayerBotRuneKindOfCategory(category);
		if (kind < 0)
			return 0;
		maxGrade = MINMAX(1, maxGrade, PLAYERBOT_RUNE_GRADES);
		int pick = 0, best = 0;
		for (int g = 1; g <= maxGrade; ++g)
		{
			if ((int)ch->CountSpecifyItem(GetPlayerBotRuneVnum(kind, g)) <= 0)
				continue;
			best = g;
			if (!pick && basePct + PLAYERBOT_RUNE_BONUS[g] >= 100)
				pick = g;
		}
		if (!pick)
			pick = best;
		if (!pick)
			return 0;
		const DWORD vnum = GetPlayerBotRuneVnum(kind, pick);
		ch->RemoveSpecifyItem(vnum, 1);
		++s_kPlayerBotRuneStats.used[pick];
		sys_log(0, "PLAYERBOT_RUNES: used pid=%u name=%s craft=%s reward=%u rune=%u grade=%d chance=%d+%d left=%d",
				ch->GetPlayerID(), ch->GetName(), craft ? craft : "", reward, vnum, pick, basePct, PLAYERBOT_RUNE_BONUS[pick],
				(int)ch->CountSpecifyItem(vnum));
		return PLAYERBOT_RUNE_BONUS[pick];
	}

	// The belts' cap: a 2* on the belts of 50 / 70, a 3* on 85 / 97, a 4* on 100 / 103.
	int GetPlayerBotBeltRuneMaxGrade(int recipeLevel)
	{
		return recipeLevel < 85 ? 2 : recipeLevel < 100 ? 3 : 4;
	}

	// ------------------------------------------------------------ keep, market

	bool WantsPlayerBotRuneOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer || IsPlayerBotRunesOff() || !IsPlayerBotRuneBot(ch) || !IsPlayerBotRuneVnum(offer->GetVnum()))
			return false;
		const int kind = GetPlayerBotRuneKind(offer->GetVnum());
		if (kind == PLAYERBOT_RUNE_KIND_OTHER || !(GetPlayerBotRuneKindsUsed(ch) & (1U << kind)))
			return false;	// Poz. Prz. only lifts its upgrades - not worth a 5* off a counter
		return offer->GetCount() == 1 && (int)ch->CountSpecifyItem(offer->GetVnum()) == 0;
	}

	bool CanPlayerBotPayForRuneOffer(LPCHARACTER ch, LPITEM offer, long long price)
	{
		if (!ch || !offer || price <= 0)
			return false;
		return price <= GetPlayerBotRuneValue(offer->GetVnum()) * (long long)std::max<int>(1, offer->GetCount()) &&
				price <= GetPlayerBotRuneSpare(ch) * PLAYERBOT_RUNE_BUY_PURSE_PCT / 100;
	}

	void NotePlayerBotRuneBought(LPCHARACTER ch, DWORD vnum, long long price)
	{
		if (!ch || !IsPlayerBotRuneVnum(vnum))
			return;
		++s_kPlayerBotRuneStats.bought;
		s_kPlayerBotRuneStats.boughtYang += std::max<long long>(0, price);
		sys_log(0, "PLAYERBOT_RUNES: bought pid=%u name=%s rune=%u price=%lld have=%d", ch->GetPlayerID(), ch->GetName(), vnum,
				price, (int)ch->CountSpecifyItem(vnum));
	}

	// ------------------------------------------------------------ the gift (a challenge's reward)

	int GivePlayerBotRunes(LPCHARACTER ch, int kind, int grade, int count, const char* reason)
	{
		if (!IsPlayerBotRuneBot(ch) || count <= 0)
			return 0;
		if (kind < 0)
			kind = GetPlayerBotRuneOwnKind(ch);
		const DWORD vnum = GetPlayerBotRuneVnum(kind, grade);
		if (!vnum)
			return 0;
		int given = 0;
		while (given < count)
		{
			const int chunk = std::min(count - given, 200);
			LPITEM item = ch->AutoGiveItem(vnum, (ITEM_COUNT)chunk, -1, false);
			if (!item)
				break;
			LogManager::instance().ItemLog(ch, item, "PLAYERBOT_RUNE_REWARD", reason ? reason : "");
			given += chunk;
		}
		if (given > 0)
		{
			s_kPlayerBotRuneStats.rewards += (unsigned int)given;
			sys_log(0, "PLAYERBOT_RUNES: reward pid=%u name=%s rune=%u count=%d reason=%s", ch->GetPlayerID(), ch->GetName(),
					vnum, given, reason ? reason : "");
		}
		return given;
	}

	// "<vnum>" | "<kind>:<grade>" | "auto:<grade>" -> kind (-1 auto) and grade; false - not a rune.
	bool ParsePlayerBotRuneSpec(const char* text, int& kind, int& grade)
	{
		if (!text || !*text)
			return false;
		if (isdigit((unsigned char)text[0]))
		{
			const DWORD vnum = (DWORD)strtoul(text, NULL, 10);
			if (!IsPlayerBotRuneVnum(vnum))
				return false;
			kind = GetPlayerBotRuneKind(vnum);
			grade = GetPlayerBotRuneGrade(vnum);
			return true;
		}
		const char* colon = strchr(text, ':');
		if (!colon || !isdigit((unsigned char)colon[1]))
			return false;
		grade = atoi(colon + 1);
		if (grade < 1 || grade > PLAYERBOT_RUNE_GRADES)
			return false;
		const std::string key(text, colon - text);
		if (key == "auto")
		{
			kind = -1;
			return true;
		}
		for (int k = 0; k < PLAYERBOT_RUNE_KINDS; ++k)
			if (key == PLAYERBOT_RUNE_KIND_TABLE[k].key)
			{
				kind = k;
				return true;
			}
		return false;
	}

	// ------------------------------------------------------------ the exchange's table

	void LoadPlayerBotRuneExchange(DWORD dwNow)
	{
		if (s_dwPlayerBotRuneExchangeReadAt != 0 && dwNow - s_dwPlayerBotRuneExchangeReadAt < PLAYERBOT_RUNE_TABLE_MS)
			return;
		s_dwPlayerBotRuneExchangeReadAt = dwNow ? dwNow : 1;
		std::vector<TPlayerBotRuneExchangeLine> lines;
		bool fromFile = false;
		if (FILE* fp = fopen(PLAYERBOT_RUNE_EXCHANGE_FILE, "r"))
		{
			fromFile = true;
			char buf[256];
			while (fgets(buf, sizeof(buf), fp))
			{
				if (buf[0] == '#' || buf[0] == '\n' || buf[0] == '\r')
					continue;
				unsigned int input = 0;
				int inputCount = 0, count = 1;
				char yang[32] = "", rune[32] = "";
				const int got = sscanf(buf, "%u %d %31s %31s %d", &input, &inputCount, yang, rune, &count);
				TPlayerBotRuneExchangeLine l;
				if (got < 4 || !ParsePlayerBotRuneSpec(rune, l.iKind, l.iGrade) || count <= 0 || inputCount < 0 ||
						(input != 0 && (inputCount <= 0 || !ITEM_MANAGER::instance().GetTable(input))))
				{
					sys_err("PLAYERBOT_RUNES: %s - line skipped: %s", PLAYERBOT_RUNE_EXCHANGE_FILE, buf);
					continue;
				}
				l.dwInput = input;
				l.iInputCount = input ? inputCount : 0;
				l.bGayaPrice = !strcmp(yang, "gaya");
				l.llYang = l.bGayaPrice ? 0 : std::max(0LL, atoll(yang));
				l.iCount = std::min(count, 200);
				if (!l.dwInput && !l.bGayaPrice && l.llYang <= 0)
					continue;	// nothing for something
				lines.push_back(l);
			}
			fclose(fp);
		}
		else
		{
			TPlayerBotRuneExchangeLine gaya = { 0, 0, 0, true, -1, 1, 1 };
			TPlayerBotRuneExchangeLine pebbles = { 95926, 150, 0, false, -1, 1, 1 };	// Kamyki
			lines.push_back(gaya);
			lines.push_back(pebbles);
		}
		if (fromFile != s_bPlayerBotRuneExchangeFromFile || lines.size() != s_vecPlayerBotRuneExchange.size())
			sys_log(0, "PLAYERBOT_RUNES: exchange table lines=%u from=%s on=%d", (unsigned int)lines.size(),
					fromFile ? PLAYERBOT_RUNE_EXCHANGE_FILE : "defaults", IsPlayerBotRuneExchangeOn() ? 1 : 0);
		s_vecPlayerBotRuneExchange.swap(lines);
		s_bPlayerBotRuneExchangeFromFile = fromFile;
	}

	long long GetPlayerBotRuneExchangeYang(const TPlayerBotRuneExchangeLine& l, int kind)
	{
		if (!l.bGayaPrice)
			return l.llYang;
		// the Portowy Sklep Gaya's price is the 1*'s; a higher grade - what it costs to make
		return l.iGrade == 1 ? (long long)PLAYERBOT_RUNE_KIND_TABLE[kind].gaya * GetPlayerBotChiGayaYang() * l.iCount
				: GetPlayerBotRuneMakeCost(kind, l.iGrade) * l.iCount;
	}

	// The first line the bot can and wants to change now (-1 none); kind - the rune's kind for this bot.
	int FindPlayerBotRuneExchange(LPCHARACTER ch, const TPlayerBotRuneBag& bag, int& kind)
	{
		if (!IsPlayerBotRuneExchangeOn())
			return -1;
		LoadPlayerBotRuneExchange(get_dword_time());
		const unsigned int used = GetPlayerBotRuneKindsUsed(ch);
		const long long budget = GetPlayerBotRuneSpare(ch) * PLAYERBOT_RUNE_EXCHANGE_PURSE_PCT / 100;
		for (size_t i = 0; i < s_vecPlayerBotRuneExchange.size(); ++i)
		{
			const TPlayerBotRuneExchangeLine& l = s_vecPlayerBotRuneExchange[i];
			const int k = l.iKind < 0 ? GetPlayerBotRuneOwnKind(ch) : l.iKind;
			if (!(used & (1U << k)) || bag.Kind(k) + l.iCount > PLAYERBOT_RUNE_EXCHANGE_KIND_CAP)
				continue;
			if (l.dwInput && (int)ch->CountSpecifyItem(l.dwInput) < l.iInputCount)
				continue;
			if (GetPlayerBotRuneExchangeYang(l, k) > budget)
				continue;
			kind = k;
			return (int)i;
		}
		return -1;
	}

	bool DoPlayerBotRuneExchange(LPCHARACTER ch, int line, int kind)
	{
		if (line < 0 || line >= (int)s_vecPlayerBotRuneExchange.size() || CountPlayerBotFreeInventoryCells(ch) < 1)
			return false;
		const TPlayerBotRuneExchangeLine l = s_vecPlayerBotRuneExchange[line];
		const long long yang = GetPlayerBotRuneExchangeYang(l, kind);
		const DWORD rune = GetPlayerBotRuneVnum(kind, l.iGrade);
		if (!rune || (long long)ch->GetGold() < yang || (l.dwInput && (int)ch->CountSpecifyItem(l.dwInput) < l.iInputCount))
			return false;
		if (l.dwInput)
			ch->RemoveSpecifyItem(l.dwInput, (ITEM_COUNT)l.iInputCount);
		if (yang > 0)
			PlayerBotChangeGold(ch, -yang);
		LPITEM item = ch->AutoGiveItem(rune, (ITEM_COUNT)l.iCount, -1, false);
		if (item)
			LogManager::instance().ItemLog(ch, item, "PLAYERBOT_RUNE_EXCHANGE", "yu-hwan");
		++s_kPlayerBotRuneStats.exchanges;
		s_kPlayerBotRuneStats.exchangeYang += yang;
		sys_log(0, "PLAYERBOT_RUNES: exchange pid=%u name=%s input=%u x%d yang=%lld rune=%u x%d ok=%d gold=%lld",
				ch->GetPlayerID(), ch->GetName(), l.dwInput, l.iInputCount, yang, rune, l.iCount, item ? 1 : 0,
				(long long)ch->GetGold());
		return true;
	}

	// ------------------------------------------------------------ Yu-Hwan's upgrade

	// The pair to upgrade now: kind / grade of the lower runes (false - none). Over the keep (one of every grade of a
	// kind it crafts with), the Yang and the Gaya within the purse's share.
	bool FindPlayerBotRuneUpgrade(LPCHARACTER ch, const TPlayerBotRuneBag& bag, int& kind, int& grade)
	{
		const unsigned int used = GetPlayerBotRuneKindsUsed(ch);
		const long long budget = GetPlayerBotRuneSpare(ch) * PLAYERBOT_RUNE_UPGRADE_PURSE_PCT / 100;
		const long long gayaYang = GetPlayerBotChiGayaYang();
		// the highest grade first: the pair nearest the 5* goes before the cheap ones
		for (int g = PLAYERBOT_RUNE_GRADES - 1; g >= 1; --g)
		{
			const int next = g + 1;
			const long long gayaCost = ch->GetGaya() >= PLAYERBOT_RUNE_UP_GAYA[next] ? 0 : PLAYERBOT_RUNE_UP_GAYA[next] * gayaYang;
			if (PLAYERBOT_RUNE_UP_YANG[next] + gayaCost > budget)
				continue;
			for (int k = 0; k < PLAYERBOT_RUNE_KINDS; ++k)
			{
				const int keep = (used & (1U << k)) ? 1 : 0;
				if (bag.n[k][g] - keep >= 2)
				{
					kind = k;
					grade = g;
					return true;
				}
			}
		}
		return false;
	}

	// The cube's way (cube.runy.txt): the two runes, the Yang and the Gaya go, a Poz. Prz. rune in the slot, the roll.
	bool UpgradePlayerBotRune(LPCHARACTER ch, int kind, int grade)
	{
		const int next = grade + 1;
		const DWORD lower = GetPlayerBotRuneVnum(kind, grade), upper = GetPlayerBotRuneVnum(kind, next);
		if (!lower || !upper || (int)ch->CountSpecifyItem(lower) < 2 || CountPlayerBotFreeInventoryCells(ch) < 1)
			return false;
		const int gayaN = PLAYERBOT_RUNE_UP_GAYA[next];
		const bool ownGaya = ch->GetGaya() >= gayaN;
		const long long gayaYang = ownGaya ? 0 : (long long)gayaN * GetPlayerBotChiGayaYang();
		const long long fee = PLAYERBOT_RUNE_UP_YANG[next];
		if ((long long)ch->GetGold() < fee + gayaYang)
			return false;
		ch->RemoveSpecifyItem(lower, 2);
		if (ownGaya && gayaN > 0 && !ch->ChangeGaya(-gayaN, "PLAYERBOT_RUNE_UPGRADE"))
		{
			ch->AutoGiveItem(lower, 2, -1, false);
			return false;
		}
		PlayerBotChangeGold(ch, -(fee + gayaYang));
		const int bonus = UsePlayerBotCraftRune(ch, PLAYERBOT_RUNE_CATEGORY_OTHER, PLAYERBOT_RUNE_UP_PCT, grade, "yu-hwan", upper);
		const int chance = std::min(100, PLAYERBOT_RUNE_UP_PCT + bonus);
		const bool success = number(1, 100) <= chance;
		LPITEM made = success ? ch->AutoGiveItem(upper, 1, -1, false) : NULL;
		LogManager::instance().CubeLog(ch->GetPlayerID(), ch->GetX(), ch->GetY(), upper, made ? made->GetID() : 0, made ? 1 : 0,
				made ? 1 : 0);
		if (made)
			++s_kPlayerBotRuneStats.upgradeOk;
		else
			++s_kPlayerBotRuneStats.upgradeFail;
		s_kPlayerBotRuneStats.upgradeYang += fee;
		s_kPlayerBotRuneStats.gayaYang += gayaYang;
		sys_log(0, "PLAYERBOT_RUNES: upgrade %s pid=%u name=%s rune=%u->%u chance=%d yang=%lld gaya=%d%s gold=%lld",
				made ? "SUCCESS" : "FAILED", ch->GetPlayerID(), ch->GetName(), lower, upper, chance, fee + gayaYang, gayaN,
				ownGaya ? "" : "(in yang)", (long long)ch->GetGold());
		return true;
	}

	// ------------------------------------------------------------ the errand

	bool HasPlayerBotRuneWork(LPCHARACTER ch)
	{
		TPlayerBotRuneBag bag;
		ReadPlayerBotRuneBag(ch, bag);
		int kind = 0, grade = 0;
		if (bag.total >= 2 && FindPlayerBotRuneUpgrade(ch, bag, kind, grade))
			return true;
		return FindPlayerBotRuneExchange(ch, bag, kind) >= 0;
	}

	int FindPlayerBotRuneSpotOn(long map)
	{
		for (int i = 0; i < PLAYERBOT_RUNE_SPOT_COUNT; ++i)
			if (PLAYERBOT_RUNE_SPOTS[i].lMap == map)
				return i;
		return -1;
	}

	// Its kingdom's second village (on this core); -1 none from here.
	int ChoosePlayerBotRuneSpot(LPCHARACTER ch, bool& travel)
	{
		travel = false;
		const int here = FindPlayerBotRuneSpotOn(ch->GetMapIndex());
		if (here >= 0)
			return here;
		if (IsPlayerBotSungmaResidentPID(ch->GetPlayerID()) || FindPlayerBotYoharaResident(ch->GetPlayerID()))
			return -1;
		long home = 0, x = 0, y = 0;
		if (!GetPlayerBotVillageReturn(ch, playerbot_empire_rules::MAP_ROLE_M2, home, x, y) || !IsPlayerBotMapHostedHere(home))
			return -1;
		travel = true;
		return FindPlayerBotRuneSpotOn(home);
	}

	void EndPlayerBotRuneVisit(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotRunes& r, DWORD dwNow, const char* why)
	{
		if (r.bPhase != PLAYERBOT_RUNE_PHASE_NONE)
			sys_log(0, "PLAYERBOT_RUNES: visit over pid=%u name=%s why=%s actions=%d exchanges=%d map=%ld gold=%lld",
					ch->GetPlayerID(), ch->GetName(), why, r.iActions, r.iExchanges, ch->GetMapIndex(), (long long)ch->GetGold());
		r.bPhase = PLAYERBOT_RUNE_PHASE_NONE;
		r.iSpot = -1;
		r.dwNextAction = 0;
		r.dwNextCheck = dwNow + number(PLAYERBOT_RUNE_CHECK_MIN_MS, PLAYERBOT_RUNE_CHECK_MAX_MS);
		ClearPlayerBotRoute(state, true);
	}

	// The census: the bots of this core holding runes, the runes by grade, and the counters.
	void LogPlayerBotRuneCensus(DWORD dwNow, bool force, LPCHARACTER to)
	{
		if (!force && s_kPlayerBotRuneStats.dwLastCensus != 0 && dwNow - s_kPlayerBotRuneStats.dwLastCensus < PLAYERBOT_RUNE_CENSUS_MS)
			return;
		s_kPlayerBotRuneStats.dwLastCensus = dwNow ? dwNow : 1;
		unsigned int bots = 0, holders = 0, visiting = 0;
		long long byGrade[PLAYERBOT_RUNE_GRADES + 1] = { 0, 0, 0, 0, 0, 0 };
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!IsPlayerBotRuneBot(ch))
				continue;
			++bots;
			TPlayerBotRuneBag bag;
			ReadPlayerBotRuneBag(ch, bag);
			if (bag.total > 0)
				++holders;
			for (int k = 0; k < PLAYERBOT_RUNE_KINDS; ++k)
				for (int g = 1; g <= PLAYERBOT_RUNE_GRADES; ++g)
					byGrade[g] += bag.n[k][g];
		}
		for (std::map<DWORD, TPlayerBotRunes>::const_iterator it = s_mapPlayerBotRunes.begin(); it != s_mapPlayerBotRunes.end(); ++it)
			if (it->second.bPhase != PLAYERBOT_RUNE_PHASE_NONE)
				++visiting;
		const TPlayerBotRuneStats& s = s_kPlayerBotRuneStats;
		char line[640];
		snprintf(line, sizeof(line),
				"census bots=%u holders=%u runes=%lld/%lld/%lld/%lld/%lld used=%u/%u/%u/%u/%u upgrades=%u ok/%u failed "
				"yang=%lld gaya_yang=%lld exchanges=%u (%lld yang) rewards=%u bought=%u (%lld yang) trips=%u visits=%u "
				"visiting=%u off=%d exchange_on=%d rewards_on=%d table=%s/%u",
				bots, holders, byGrade[1], byGrade[2], byGrade[3], byGrade[4], byGrade[5], s.used[1], s.used[2], s.used[3],
				s.used[4], s.used[5], s.upgradeOk, s.upgradeFail, s.upgradeYang, s.gayaYang, s.exchanges, s.exchangeYang,
				s.rewards, s.bought, s.boughtYang, s.trips, s.visits, visiting, IsPlayerBotRunesOff() ? 1 : 0,
				IsPlayerBotRuneExchangeOn() ? 1 : 0, IsPlayerBotRuneRewardOn() ? 1 : 0,
				s_bPlayerBotRuneExchangeFromFile ? "file" : "defaults", (unsigned int)s_vecPlayerBotRuneExchange.size());
		sys_log(0, "PLAYERBOT_RUNES: %s", line);
		if (to)
			to->ChatPacket(CHAT_TYPE_INFO, "Runy botow: %s", line);
	}

	bool ManagePlayerBotRunes(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		LogPlayerBotRuneCensus(dwNow, false, NULL);
		if (!IsPlayerBotRuneBot(ch) || ch->IsDead())
			return false;
		const DWORD pid = ch->GetPlayerID();
		TPlayerBotRunes& r = s_mapPlayerBotRunes[pid];
		const bool otherErrand = state.bVisitingShop || state.bVisitingBiologist || state.bVisitingHerbalist ||
				state.bVisitingStable || state.bVisitingAlchemist || state.bVisitingUriel || state.bFishingSession ||
				state.bMarketTrip || state.bVisitingYonah || IsPlayerBotGear2ErrandBusy(pid);
		if (otherErrand || IsPlayerBotRunesOff() || (ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())) ||
				IsPlayerBotHeldForCompany(ch) || ch->GetMyShop() != NULL || ch->GetExchange() || IsPlayerBotArezzoHeldHere(ch) ||
				IsPlayerBotOnDungeonRun(pid))
		{
			if (r.bPhase != PLAYERBOT_RUNE_PHASE_NONE)
				EndPlayerBotRuneVisit(ch, state, r, dwNow, "interrupted");
			return false;
		}
		if (r.bPhase == PLAYERBOT_RUNE_PHASE_NONE)
		{
			if (r.dwNextCheck == 0)
				r.dwNextCheck = dwNow + number(PLAYERBOT_RUNE_CHECK_MIN_MS / 4, PLAYERBOT_RUNE_CHECK_MAX_MS);
			if ((int)(dwNow - r.dwNextCheck) < 0)
				return false;
			r.dwNextCheck = dwNow + number(PLAYERBOT_RUNE_CHECK_MIN_MS, PLAYERBOT_RUNE_CHECK_MAX_MS);
			if (!HasPlayerBotRuneWork(ch))
				return false;
			bool travel = false;
			const int spot = ChoosePlayerBotRuneSpot(ch, travel);
			if (spot < 0)
				return false;
			if (ch->GetVictim() != NULL || state.dwTargetVID != 0 || state.bTacticalRetreat || (travel && BlocksPlayerBotTravel(ch)))
			{
				r.dwNextCheck = dwNow + number(20000, 60000);
				return false;
			}
			const TPlayerBotRuneSpot& sp = PLAYERBOT_RUNE_SPOTS[spot];
			if (travel)
			{
				SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
				if (!TransitionPlayerBotMap(ch, state, sp.lMap, sp.lX, sp.lY, dwNow, "rune_upgrade"))
				{
					PlayerBotLogThrottled("rune_travel", dwNow, "PLAYERBOT_RUNES: no way pid=%u name=%s from=%ld to=%ld",
							pid, ch->GetName(), ch->GetMapIndex(), sp.lMap);
					return false;
				}
				++s_kPlayerBotRuneStats.trips;
				sys_log(0, "PLAYERBOT_RUNES: going pid=%u name=%s from=%ld to=%ld", pid, ch->GetName(), ch->GetMapIndex(), sp.lMap);
				r.dwNextCheck = 0;	// straight to Yu-Hwan once it stands on the map
				return true;
			}
			r.bPhase = PLAYERBOT_RUNE_PHASE_YUHWAN;
			r.iSpot = spot;
			r.iActions = 0;
			r.iExchanges = 0;
			r.dwVisitStart = dwNow;
			r.dwNextAction = 0;
			++s_kPlayerBotRuneStats.visits;
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ch->Stop();
			ClearPlayerBotRoute(state, true);
			sys_log(0, "PLAYERBOT_RUNES: going pid=%u name=%s map=%ld npc=yu-hwan gold=%lld", pid, ch->GetName(),
					ch->GetMapIndex(), (long long)ch->GetGold());
		}
		if (r.iSpot < 0 || PLAYERBOT_RUNE_SPOTS[r.iSpot].lMap != ch->GetMapIndex())
		{
			EndPlayerBotRuneVisit(ch, state, r, dwNow, "left_map");
			return false;
		}
		if (dwNow - r.dwVisitStart > PLAYERBOT_RUNE_VISIT_MS)
		{
			EndPlayerBotRuneVisit(ch, state, r, dwNow, "timeout");
			return false;
		}
		SetPlayerBotAction(state, BOT_ACTION_SHOP, dwNow);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		const TPlayerBotRuneSpot& sp = PLAYERBOT_RUNE_SPOTS[r.iSpot];
		long ax = 0, ay = 0;
		GetPlayerBotNpcApproach(pid, sp.lX, sp.lY, 0x52554e45U, ax, ay);
		if (DISTANCE_APPROX(ch->GetX() - ax, ch->GetY() - ay) > PLAYERBOT_RUNE_REACH)
		{
			if (!MovePlayerBot(ch, ax, ay, dwNow, 20, true, true, false, true) && state.bStuckCounter >= 6)
			{
				sys_err("PLAYERBOT_RUNES: route failed pid=%u name=%s map=%ld from=(%ld,%ld) to=(%ld,%ld)", pid, ch->GetName(),
						ch->GetMapIndex(), ch->GetX(), ch->GetY(), ax, ay);
				EndPlayerBotRuneVisit(ch, state, r, dwNow, "route_failed");
				return false;
			}
			return true;
		}
		ch->Stop();
		ch->SetPosition(POS_STANDING);
		if (r.dwNextAction == 0)
		{
			r.dwNextAction = dwNow + number(3000, 7000);
			return true;
		}
		if ((int)(dwNow - r.dwNextAction) < 0)
			return true;
		if (r.iActions >= PLAYERBOT_RUNE_VISIT_ACTIONS)
		{
			EndPlayerBotRuneVisit(ch, state, r, dwNow, "done");
			return false;
		}
		TPlayerBotRuneBag bag;
		ReadPlayerBotRuneBag(ch, bag);
		int kind = 0, grade = 0;
		bool did = false;
		// the exchange first (its runes may make the pair), then the upgrades
		if (r.iExchanges < PLAYERBOT_RUNE_EXCHANGE_PER_VISIT)
		{
			const int line = FindPlayerBotRuneExchange(ch, bag, kind);
			if (line >= 0 && DoPlayerBotRuneExchange(ch, line, kind))
			{
				++r.iExchanges;
				did = true;
			}
		}
		if (!did && FindPlayerBotRuneUpgrade(ch, bag, kind, grade))
			did = UpgradePlayerBotRune(ch, kind, grade);
		if (!did)
		{
			EndPlayerBotRuneVisit(ch, state, r, dwNow, "done");
			return false;
		}
		++r.iActions;
		r.dwNextAction = dwNow + number(2500, 5000);
		return true;
	}
}

// ------------------------------------------------------------ global: a challenge's reward, the GM command

// MT2009_PLUS_BOT_RUNES_V1 (a): runes for a bot as a challenge's reward - kind -1 the kind it crafts with, grade 1..5.
// Nothing while the event flag m2_bot_rune_rewards_on is 0, unless forced (the GM command). The count given back.
int Mt2009PlayerBotRuneReward(LPCHARACTER bot, int kind, int grade, int count, const char* reason, bool force)
{
	if (!bot || (!force && (!IsPlayerBotRuneRewardOn() || IsPlayerBotRunesOff())))
		return 0;
	if (!CPlayerBotManager::instance().IsManaged(bot->GetPlayerID()))
		return 0;
	return GivePlayerBotRunes(bot, kind, grade, count, reason);
}

// "/bot_runa" (GM_HIGH_WIZARD, server-patches/runyboty): the census; "daj <bot> <rune> [count]"; "wszystkim <rune> [count]
// [lv_min] [lv_max] [empire] [limit]" - the bots of this core.
void PlayerBotRuneCommand(LPCHARACTER ch, const char* argument)
{
	if (!ch)
		return;
	char a1[256], a2[256], a3[256], a4[256], a5[256], a6[256], a7[256];
	const char* rest = one_argument(argument, a1, sizeof(a1));
	if (!*a1)
	{
		LogPlayerBotRuneCensus(get_dword_time(), true, ch);
		ch->ChatPacket(CHAT_TYPE_INFO, "/bot_runa daj <bot|pid> <runa> [ile]  |  /bot_runa wszystkim <runa> [ile] [lv_min] [lv_max] "
				"[imperium 0-3] [limit]  - runa: 79605-79659, <rodzaj>:<1-5> albo auto:<1-5>");
		ch->ChatPacket(CHAT_TYPE_INFO, "rodzaje: pasy bron zbroja pozostale akcesoria ksiegi zestbron zesthelm zestzbroja rekawice "
				"zwierzaki; flagi: m2_bot_runes_off, m2_bot_rune_exchange_on, m2_bot_rune_rewards_on");
		return;
	}
	if (!strcmp(a1, "daj"))
	{
		rest = one_argument(rest, a2, sizeof(a2));
		rest = one_argument(rest, a3, sizeof(a3));
		one_argument(rest, a4, sizeof(a4));
		int kind = 0, grade = 0, count = 1;
		if (!*a2 || !ParsePlayerBotRuneSpec(a3, kind, grade))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "/bot_runa daj <bot|pid> <runa> [ile]");
			return;
		}
		if (*a4)
			count = MINMAX(1, atoi(a4), 1000);
		LPCHARACTER bot = isdigit((unsigned char)a2[0]) ? CHARACTER_MANAGER::instance().FindByPID((DWORD)strtoul(a2, NULL, 10))
				: CHARACTER_MANAGER::instance().FindPC(a2);
		if (!bot || !CPlayerBotManager::instance().IsManaged(bot->GetPlayerID()))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Nie ma tu zarzadzanego bota %s.", a2);
			return;
		}
		char reason[64];
		snprintf(reason, sizeof(reason), "gm:%s", ch->GetName());
		const int given = Mt2009PlayerBotRuneReward(bot, kind, grade, count, reason, true);
		ch->ChatPacket(CHAT_TYPE_INFO, "Bot %s dostal %d run (%s).", bot->GetName(), given, a3);
		return;
	}
	if (!strcmp(a1, "wszystkim"))
	{
		rest = one_argument(rest, a2, sizeof(a2));
		rest = one_argument(rest, a3, sizeof(a3));
		rest = one_argument(rest, a4, sizeof(a4));
		rest = one_argument(rest, a5, sizeof(a5));
		rest = one_argument(rest, a6, sizeof(a6));
		one_argument(rest, a7, sizeof(a7));
		int kind = 0, grade = 0;
		if (!ParsePlayerBotRuneSpec(a2, kind, grade))
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "/bot_runa wszystkim <runa> [ile] [lv_min] [lv_max] [imperium 0-3] [limit]");
			return;
		}
		const int count = *a3 ? MINMAX(1, atoi(a3), 1000) : 1;
		const int lvMin = *a4 ? atoi(a4) : 1, lvMax = *a5 ? atoi(a5) : 999, empire = *a6 ? atoi(a6) : 0;
		const int limit = *a7 ? atoi(a7) : 0;
		char reason[64];
		snprintf(reason, sizeof(reason), "gm-all:%s", ch->GetName());
		int bots = 0, runes = 0;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			if (limit > 0 && bots >= limit)
				break;
			LPCHARACTER bot = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!bot || (int)bot->GetLevel() < lvMin || (int)bot->GetLevel() > lvMax || (empire > 0 && bot->GetEmpire() != empire))
				continue;
			const int given = Mt2009PlayerBotRuneReward(bot, kind, grade, count, reason, true);
			if (given > 0)
			{
				++bots;
				runes += given;
			}
		}
		sys_log(0, "PLAYERBOT_RUNES: gm grant by %s rune=%s count=%d level=%d-%d empire=%d bots=%d runes=%d", ch->GetName(), a2,
				count, lvMin, lvMax, empire, bots, runes);
		ch->ChatPacket(CHAT_TYPE_INFO, "Runy (%s) dla %d botow, razem %d.", a2, bots, runes);
		return;
	}
	ch->ChatPacket(CHAT_TYPE_INFO, "/bot_runa [daj|wszystkim] - bez argumentow: stan.");
}

#endif
