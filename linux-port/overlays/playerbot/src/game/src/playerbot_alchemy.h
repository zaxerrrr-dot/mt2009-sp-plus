#ifndef __INC_METIN2_PLAYERBOT_ALCHEMY_H__
#define __INC_METIN2_PLAYERBOT_ALCHEMY_H__

// Alchemy (Dragon Soul) for bots (MT2009 Plus, operator, 26 September 2026).
//
// Every bot of 30 and more does the Alchemist's daily errand the players do
// (dragon_soul.quest, state_farming): a monster it kills drops a Dragon Stone
// Shard one time in ten (drop_gamble_with_flag("ds_drop"), 10% unless the
// flag says otherwise), ten shards are a Cor Draconis, five Cors a day
// unless the flag ds_cor_day says otherwise. The
// quest skips bots (pc.is_bot), so the pass counts the shards itself instead
// of filling a bag with them.
//
//   * Half the bots (PLAYERBOT_ALCHEMY_PERCENT, by player id) use alchemy:
//     qualified the way a player is, they keep their Cors and buy more off
//     the counters, open them, wear the best stone of each of the seven kinds
//     (deck 0), switch the deck on for fights only, refine at the
//     Alchemist (grade and step from two stones, strength with a Green
//     Dragon Bean) up to what their level asks, buy the Time Elixir when the
//     kind's stone runs low or out (MT2009_PLUS_BOT_DS_EXTEND_V1), and
//     sell what they have no use for: a spare kind, a worse copy, or a
//     stone whose bonuses are nothing to their class.
//   * The other half sells its Cors on its counters, five and more a line.
//
// Every engine step is the one the player's window calls (DSManager's
// DoRefineGrade / DoRefineStep / DoRefineStrength, EquipItem, PullOut,
// UseItem), so odds, fees and results are the players'.

#include "DragonSoul.h"

namespace
{
	// Three bots in four since 28 September: with half, 448 Cors stood on the
	// counters and 1878 more in the bags of the sellers, while the users that
	// could have opened them were a few hundred (the operator: "boty chetniej
	// to kupowaly ... i klikaly alchemie").
	const int PLAYERBOT_ALCHEMY_PERCENT = 75;
	const int PLAYERBOT_ALCHEMY_MIN_LEVEL = 30;
	const DWORD PLAYERBOT_DS_SHARD_VNUM = 30270;
	const int PLAYERBOT_DS_SHARDS_PER_COR = 10;
	// Cors a day: the players' event flag ds_cor_day (dragon_soul.quest, the
	// admin panel's alchemy page; 1-20), this when it is unset or out of range.
	const int PLAYERBOT_DS_CORS_PER_DAY = 5;
	const DWORD PLAYERBOT_COR_ROUGH_VNUM = 50255;
	const int PLAYERBOT_COR_LINE_MIN_UNITS = 5;
	const DWORD PLAYERBOT_DS_TIME_ELIXIR_VNUM = 100002;
	const DWORD PLAYERBOT_DS_GREEN_BEAN_VNUM = 100300;
	// MT2009_PLUS_BOT_DS_ALCHEMY_GUIDE_V1: the blue and pink beans (MATERIAL_DS_REFINE_BLESSED / _HOLLY,
	// RefineStrengthTables 100/88/77/55/33/22 and 100/90/80/60/40/30, fee 20 000 / 30 000; no shop sells them) and
	// the Alchemist's Tongs of Time (100200, EXTRACT_DRAGON_HEART, 500 000) with the Dragon Heart they make (100000).
	const DWORD PLAYERBOT_DS_BLUE_BEAN_VNUM = 100400;
	const DWORD PLAYERBOT_DS_PINK_BEAN_VNUM = 100500;
	const DWORD PLAYERBOT_DS_TIME_TONGS_VNUM = 100200;
	const DWORD PLAYERBOT_DS_DRAGON_HEART_VNUM = 100000;
	const DWORD PLAYERBOT_DS_ALCHEMIST_VNUM = 20001;
	// A worn stone with less than this left gets an elixir.
	const int PLAYERBOT_DS_ELIXIR_BELOW_SEC = 2 * 60 * 60;
	// Unworn stones of one kind kept as refine material.
	// Eight: a rare stone takes about nine ordinary ones.
	const int PLAYERBOT_DS_MATERIAL_KEEP = 8;
	// Dragon Stone lines one counter shows (playerbot_offline_shop.h).
	// Eight, not four: 43 000 unworn stones stood in the bags of 800 users on
	// the test world (26 September 2026), four lines at a time.
	const int PLAYERBOT_DS_COUNTER_LINES = 8;
	// Cors a user keeps in the bag before it stops buying them.
	const int PLAYERBOT_DS_COR_KEEP = 25;
	const DWORD PLAYERBOT_ALCHEMY_CHECK_MIN_MS = 3 * 60 * 1000;
	const DWORD PLAYERBOT_ALCHEMY_CHECK_MAX_MS = 6 * 60 * 1000;
	const DWORD PLAYERBOT_ALCHEMY_LOCAL_MS = 20000;
	const int PLAYERBOT_ALCHEMY_VISIT_MAX_STEPS = 20;
	// Cors opened a pass (every PLAYERBOT_ALCHEMY_LOCAL_MS), in a fight too:
	// three a pass out of combat left 2300 Cors in the bags of 31 users.
	const int PLAYERBOT_DS_COR_OPEN_PER_PASS = 10;
	// What a refine leaves over its fee: a million kept the poorer users, the
	// ones that opened their Cors, away from the Alchemist for good.
	const long long PLAYERBOT_DS_REFINE_SPARE = 300000LL;
	// A Cor off a counter: at most this many times the price the bots ask for
	// one (ScalePlayerBotIwakuraPrice(PLAYERBOT_COR_DRACONIS_PRICE)). The old
	// cap was twice the unscaled 100 000 - under every Cor on every counter
	// (680 000 - 1 025 000 on the test world), so no bot ever bought one.
	const int PLAYERBOT_DS_COR_BUY_MULT = 5;
	// MT2009_PLUS_MARKET_SINK_V1: 50+ pages of Cors (lines of 50-67) on the
	// supporters' world and no buyer - a line of 67 at 100 000 was over the
	// 40% of every user's purse, and a user stopped at 25. With this many
	// Cors on the counters the market is plentiful: a user keeps up to
	// PLAYERBOT_DS_COR_KEEP_PLENTY, pays out of PLAYERBOT_DS_COR_PLENTY_PURSE
	// percent of its spare purse, and buys a line no bigger than what it
	// misses and PLAYERBOT_COR_LINE_MAX_UNITS more (the lines are cut to that,
	// playerbot_offline_shop.h).
	const DWORD PLAYERBOT_COR_MARKET_PLENTY_UNITS = 150;
	const int PLAYERBOT_DS_COR_KEEP_PLENTY = 60;
	const int PLAYERBOT_DS_COR_PLENTY_PURSE = 60;
	const char* PLAYERBOT_DS_SHARDS_FLAG = "playerbot.ds_shards";
	const char* PLAYERBOT_DS_DAY_FLAG = "playerbot.ds_day";
	const char* PLAYERBOT_DS_LEFT_FLAG = "playerbot.ds_left";

	// MT2009_PLUS_BOT_DS_YOHARA800_V1 - the bulk alchemists (the owner, 27 October 2026: "Daj im rowniez cor
	// draconis legendarne 400 sztuk - naucz je otwierac legendarne cory ... Niech z tych 400 sztuk zrobia mityczna
	// wyborna alchemie ... Naucz je perf bonusow na yohare w alchemii. Daj im rowniez po 400 zielonych smoczych
	// fasol"). A bot is a bulk alchemist while it is a member of a Yohara cohort (common.playerbot_yohara_cohort,
	// any purpose) or once it held PLAYERBOT_DS_BULK_COR_MIN legendary Cors (50259/51510) - the flag stays, so its
	// stones stay material and are never goods. A bulk alchemist:
	//   * opens every Cor that opens into stones (IsPlayerBotOpenableCorVnum), while the page of the stone's kind and
	//     grade has room (the alchemy bag is 32 cells a kind and grade - a stone with no room falls on the ground);
	//   * refines within a kind: every grade pair up to Mythic (2 stones, 50/50 in the live table), then the Mythic
	//     steps two by two up to Highest ("wyborny"; 70/30 a step), the highest pairs first - and stops a kind's
	//     grade and step work once the kind has a Mythic Highest stone (worn or in the bag): a second one would only
	//     be a duplicate of a filled slot, the rest stays as spare material;
	//   * then puts the Green Dragon Beans into the kind's final stone (the best by grade and step, then by its
	//     Yohara lines) up to the cap the WeightTables allow (Mythic/Legendary Highest +6, High +5, the rest +4) -
	//     the beans spread over the kinds lowest strength first (a +5->+6 is 20% and costs ~56 beans on average,
	//     so every kind gets its cheap levels before any gets the dear ones); a bean is bought only for the level
	//     target of an ordinary user (GetPlayerBotDsTarget), never for the gamble over it;
	//   * wears a kind's stone only when the kind's work is done (a worn stone cannot be refined and a pull-out
	//     keeps a Mythic one 15% of the time), a Mythic one too, and ranks by the stone's real power - the
	//     WeightTables' percent (Mythic Highest +6 = 160, Mythic High +5 = Legendary Highest +6 = 120, Mythic
	//     Highest +0 = 75) - then by its lines for Yohara (GetPlayerBotDsYoharaLinePref);
	//   * sells nothing of it: no stone is surplus, and its Cors, beans and bonus stones (71084/71085) are never
	//     the merchant's or a counter's (IsPlayerBotKeptAlchemyGoods);
	//   * goes to the Alchemist more often and does more a visit (PLAYERBOT_DS_BULK_*): ~270 grade tries, ~100 step
	//     tries and up to 400 beans a bot take a few hours, in visits of PLAYERBOT_DS_BULK_VISIT_MAX_STEPS refines
	//     PLAYERBOT_DS_BULK_STEP_MIN_MS..MAX_MS apart - a refine every couple of seconds a bot at most.
	// The material, from 400 legendary Cors (~57 a kind): a grade try takes 2 legendary and gives 1 legendary or 1
	// Mythic, so ~3 legendary a Mythic (~19 a kind); a step takes ~2.43 stones of the step under it, so a Mythic
	// Highest takes ~35 Mythic Lowest - so a kind gets one about one time in twelve, the others end at Mythic High
	// or Mid and take their beans to +5/+4. A grade refine ignores the step, so no legendary stone is stepped first.
	// The route was chosen by simulation (27 October 2026, 4000 bots of 400 Cors over the 7 kinds and 400 beans,
	// the live odds; power = the worn stones' WeightTables percent summed over the 7 kinds):
	//   every kind the Mythic way (this)                     810  (0.57 Mythic Highest a bot)
	//   every kind the Legendary way (steps to Highest, +6)  769  (0)
	//   Legendary under 50 stones of a kind, Mythic over     814  (0.55) - within the noise, fewer Mythic Highest
	//   beans by best gain a bean instead of lowest first    810 vs 808 - the same
	// so: the Mythic way everywhere, the most Mythic Highest for the same power; a kind that does not reach Highest
	// wears what it reaches (Mythic High +5 = 120, Mid +4 = 80, or its best Legendary) - every kind's slot is filled
	// when its work is done, and a stand-in fills it meanwhile (PlacePlayerBotDsInterim).
	// The Alchemist of Dongan (373, npc.txt cell 569,714) serves the Yohara maps of the core (game3 hosts no first
	// village); the progress line is PLAYERBOT_ALCHEMY: progress (every PLAYERBOT_DS_PROGRESS_LOG_MS a bot).
	const DWORD PLAYERBOT_COR_LEGENDARY_VNUM = 50259;
	const DWORD PLAYERBOT_COR_LEGENDARY_515_VNUM = 51510;
	const int PLAYERBOT_DS_BULK_COR_MIN = 20;
	const char* PLAYERBOT_DS_BULK_FLAG = "playerbot.ds_bulk";
	const char* PLAYERBOT_DS_OPENED_FLAG = "playerbot.ds_opened";
	const int PLAYERBOT_DS_BULK_COR_OPEN_PER_PASS = 20;
	const int PLAYERBOT_DS_BULK_VISIT_MAX_STEPS = 30;
	const DWORD PLAYERBOT_DS_BULK_STEP_MIN_MS = 1500;
	const DWORD PLAYERBOT_DS_BULK_STEP_MAX_MS = 3000;
	const DWORD PLAYERBOT_DS_BULK_CHECK_MIN_MS = 60 * 1000;
	const DWORD PLAYERBOT_DS_BULK_CHECK_MAX_MS = 120 * 1000;
	// A bulk alchemist the fight kept from the Alchemist looks again this soon (Dongan is a hunting map).
	const DWORD PLAYERBOT_DS_BULK_BUSY_RETRY_MIN_MS = 10 * 1000;
	const DWORD PLAYERBOT_DS_BULK_BUSY_RETRY_MAX_MS = 20 * 1000;
	const DWORD PLAYERBOT_DS_PROGRESS_LOG_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_DS_BULK_HOLDER_LOOK_MS = 5 * 60 * 1000;
	// The Alchemist of Dongan (metin2_map_eastplain_01, base 1049600/435200, npc.txt 20001 at cell 569,714) and the
	// map's arrival (Town.txt) a bot of another Yohara map travels to.
	const long PLAYERBOT_DS_DONGAN_ALCHEMIST_X = 1106500;
	const long PLAYERBOT_DS_DONGAN_ALCHEMIST_Y = 506600;
	const long PLAYERBOT_DS_DONGAN_ARRIVAL_X = 1102450;
	const long PLAYERBOT_DS_DONGAN_ARRIVAL_Y = 506850;
	// WeightTables of dragon_soul_table.txt (the same in both bonus modes, 27 October 2026): a stone's power in
	// percent of its kind's base values, by grade, step and strength; 0 - the strength cannot be had
	// (DoRefineStrength refuses it).
	const BYTE PLAYERBOT_DS_WEIGHT[6][5][7] = {
		{ { 1, 2, 3, 0, 0, 0, 0 }, { 2, 3, 4, 0, 0, 0, 0 }, { 3, 4, 5, 6, 0, 0, 0 }, { 4, 5, 6, 7, 0, 0, 0 }, { 5, 6, 7, 8, 10, 0, 0 } },
		{ { 3, 4, 5, 6, 0, 0, 0 }, { 4, 5, 6, 8, 0, 0, 0 }, { 5, 6, 8, 10, 0, 0, 0 }, { 6, 8, 10, 12, 15, 0, 0 }, { 8, 10, 12, 15, 20, 0, 0 } },
		{ { 6, 7, 9, 11, 15, 0, 0 }, { 7, 9, 11, 15, 20, 0, 0 }, { 9, 11, 15, 20, 25, 0, 0 }, { 11, 15, 20, 25, 30, 0, 0 }, { 15, 20, 25, 30, 40, 0, 0 } },
		{ { 10, 12, 15, 18, 20, 0, 0 }, { 12, 15, 18, 20, 25, 0, 0 }, { 15, 18, 20, 25, 35, 0, 0 }, { 18, 20, 25, 35, 40, 0, 0 }, { 20, 25, 35, 40, 60, 80, 0 } },
		{ { 30, 35, 40, 45, 50, 0, 0 }, { 35, 40, 45, 50, 55, 0, 0 }, { 40, 45, 50, 55, 65, 0, 0 }, { 45, 50, 55, 65, 75, 90, 0 }, { 50, 55, 65, 75, 90, 105, 120 } },
		{ { 35, 40, 45, 50, 55, 0, 0 }, { 45, 50, 55, 60, 65, 0, 0 }, { 50, 55, 60, 70, 80, 0, 0 }, { 65, 75, 85, 95, 105, 120, 0 }, { 75, 85, 95, 105, 120, 135, 160 } },
	};

	// ------------------------------------------------------------ prices
	//
	// A stone's price is what it costs to make, on average, from Cors at
	// PLAYERBOT_COR_DRACONIS_PRICE, plus PLAYERBOT_DS_PRICE_MARGIN_PERCENT
	// (operator, 26 September 2026). From the engine's tables
	// (dragon_soul_table.txt, DoRefineGrade/Step/Strength):
	//   grade: two stones of a grade -> one of the next (50%) or of the same
	//     (50%), step 0: 2 tries on average, 3 stones net, fee a try;
	//   step: two of a grade and step -> the next step (70%) or the same (30%):
	//     1/0.7 tries, 2 + (1/0.7 - 1) stones net, fee a try;
	//   strength: a Green Dragon Bean a try (100/80/70/50/30/20%), a failure
	//     one strength down: E(k) = (1 + (1 - p(k)) * E(k-1)) / p(k) tries for
	//     the step from k to k+1.
	const int PLAYERBOT_DS_PRICE_MARGIN_PERCENT = 25;
	const long long PLAYERBOT_DS_GRADE_FEES[5] = { 30000, 50000, 70000, 100000, 150000 };
	const long long PLAYERBOT_DS_STEP_FEES[4] = { 20000, 30000, 40000, 50000 };
	const double PLAYERBOT_DS_STRENGTH_PCT[6] = { 1.0, 0.8, 0.7, 0.5, 0.3, 0.2 };
	const long long PLAYERBOT_DS_BEAN_COST = 1000000 + 10000;

	long long GetPlayerBotDragonSoulBaseCost(BYTE grade, BYTE step, BYTE strength)
	{
		static bool s_built = false;
		static double s_cost[6][5];
		static double s_strength[7];
		if (!s_built)
		{
			s_built = true;
			double g = (double)PLAYERBOT_COR_DRACONIS_PRICE;
			for (int gi = 0; gi < 6; ++gi)
			{
				double s = g;
				s_cost[gi][0] = s;
				for (int si = 0; si < 4; ++si)
				{
					s = (2.0 + (1.0 / 0.7 - 1.0)) * s + (1.0 / 0.7) * (double)PLAYERBOT_DS_STEP_FEES[si];
					s_cost[gi][si + 1] = s;
				}
				if (gi < 5)
					g = 3.0 * g + 2.0 * (double)PLAYERBOT_DS_GRADE_FEES[gi];
			}
			double e = 1.0, sum = 0.0;
			s_strength[0] = 0.0;
			for (int k = 0; k < 6; ++k)
			{
				if (k > 0)
					e = (1.0 + (1.0 - PLAYERBOT_DS_STRENGTH_PCT[k]) * e) / PLAYERBOT_DS_STRENGTH_PCT[k];
				sum += e;
				s_strength[k + 1] = sum;
			}
		}
		grade = std::min<BYTE>(grade, 5);
		step = std::min<BYTE>(step, 4);
		strength = std::min<BYTE>(strength, 6);
		return (long long)(s_cost[grade][step] + s_strength[strength] * (double)PLAYERBOT_DS_BEAN_COST);
	}

	DWORD GetPlayerBotDragonSoulPrice(LPITEM item)
	{
		if (!item || !item->IsDragonSoul())
			return 0;
		const DWORD vnum = item->GetVnum();
		const long long cost = GetPlayerBotDragonSoulBaseCost((BYTE)((vnum / 1000) % 10),
				(BYTE)((vnum / 100) % 10), (BYTE)((vnum / 10) % 10));
		long long price = cost * (100 + PLAYERBOT_DS_PRICE_MARGIN_PERCENT) / 100;
		// On the world's yang rate and inflation, like the rest of the bots'
		// goods (ScalePlayerBotIwakuraPrice; operator, 26 September 2026): the
		// table is the price at the curve's base.
		price = (long long)ScalePlayerBotIwakuraPrice((DWORD)std::min<long long>(price, 0xFFFFFFFFLL));
		price = (price + 500) / 1000 * 1000;
		return (DWORD)std::min<long long>(std::max<long long>(price, 1000), PLAYERBOT_GOLD_MAX - 1000); // MT2009_PLUS_YANG_LIMITS_V1
	}

	// ------------------------------------------------------------ who

	bool ArePlayerBotAlchemyOff()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_alchemy_off") != 0;
	}

	// The players' daily Cor count (dragon_soul.quest reads the same flag).
	int GetPlayerBotDragonCorsPerDay()
	{
		const int n = quest::CQuestManager::instance().GetEventFlag("ds_cor_day");
		return (n >= 1 && n <= 20) ? n : PLAYERBOT_DS_CORS_PER_DAY;
	}

	// The share scaled by the panel's ALCHEMY will (playerbot_config.h; 100 =
	// the build's 75%), by player id, so the same bots come back when raised.
	bool IsPlayerBotAlchemyUserPID(DWORD pid)
	{
		const DWORD h = (pid * 3266489917U) ^ 0x414c4348U;
		return (int)((h >> 15) % 100) < PLAYERBOT_ALCHEMY_PERCENT * s_iPlayerBotAlchemyPercent / 100;
	}

	bool IsPlayerBotAlchemyUser(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC() || ch->GetLevel() < PLAYERBOT_ALCHEMY_MIN_LEVEL || ArePlayerBotAlchemyOff())
			return false;
		const DWORD pid = ch->GetPlayerID();
		// MT2009_PLUS_BOT_YOHARA_COHORT_V1: a member of the night's cohorts wears its stones, always.
		// MT2009_PLUS_BOT_DS_YOHARA800_V1: and so does a bulk alchemist (a holder of legendary Cors).
		return (IsPlayerBotAlchemyUserPID(pid) || IsPlayerBotYoharaCohortPID(pid) ||
				ch->GetQuestFlag(PLAYERBOT_DS_BULK_FLAG) != 0) && !IsPlayerBotSidekickPID(pid) &&
				!CPlayerBotManager::instance().IsMedalDropperCohortPID(pid);
	}

	// MT2009_PLUS_BOT_DS_YOHARA800_V1: a bulk alchemist (the comment at PLAYERBOT_COR_LEGENDARY_VNUM) - any member of
	// a Yohara cohort (the 'yohara' hundred, the 'yohara800' ones, the Hydra's), or a bot that held legendary Cors.
	bool IsPlayerBotDsBulk(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && (IsPlayerBotYoharaCohortPID(ch->GetPlayerID()) ||
				ch->GetQuestFlag(PLAYERBOT_DS_BULK_FLAG) != 0);
	}

	// A stone's power (the WeightTables' percent), its strength cap, and the Mythic Highest test.
	int GetPlayerBotDsWeight(BYTE grade, BYTE step, BYTE strength)
	{
		return (grade < 6 && step < 5 && strength < 7) ? PLAYERBOT_DS_WEIGHT[grade][step][strength] : 0;
	}

	BYTE GetPlayerBotDsStrengthCap(BYTE grade, BYTE step)
	{
		BYTE cap = 0;
		for (BYTE s = 1; s < 7; ++s)
			if (GetPlayerBotDsWeight(grade, step, s) > 0)
				cap = s;
		return cap;
	}

	// The preference of a Dragon Stone line for the Yohara maps, 0-10 a line (MT2009_PLUS_BOT_DS_YOHARA800_V1,
	// "perf bonusy na Yohare"). What the choice rests on (27 October 2026):
	//   * the bonus mode is a switch (M2_BONUS_MODE; the test world runs 'global': dragon_soul_applys.global.txt -
	//     the elements, the stats and Sung Ma on the basic lines; 'mt2009': dragon_soul_applys.mt2009plus.txt - race
	//     bonuses on the basic lines, crit/pierce on the Amethyst), so the table covers the lines of both;
	//   * the basic lines are the kind's own (every stone of a kind has them), so they only order the KINDS (which
	//     kind's stone gets the beans first on a tie); the choice between two stones of a kind is their
	//     additional lines, rolled when the stone is made (a grade or step refine makes a new stone; a strength
	//     refine keeps the lines);
	//   * the Sung Ma maps ask Sung Ma Strength / Vitality / Resistance / Intelligence of whoever enters
	//     (sungma_table.txt; playerbot_yohara_sungma.h) - a line of them is worth the most;
	//   * the ordinary monsters of the Sung Ma maps (mob_proto 6686-6900, level 115+): races DEVIL 37, HUMAN 24,
	//     ANIMAL 13 (the rest DESERT/SAVAGE, which no stone line hits), elements ice 44, dark 39, earth 29,
	//     lightning (SAVAGE) 21, wind (TEMPLE) 16, fire 8 - ATTBONUS_MONSTER hits them all, ORC/UNDEAD/MILGYO
	//     next to none; an element's power (ENCHANT_*) and resistance by those shares (MT2009_PLUS_ELEMENTS_V1);
	//   * a Champion's fight is long and against monsters and bosses: HP (%), steal HP, defence against normal
	//     hits, crit and pierce for the physical classes, magic attack for the magic ones (Sura of the black
	//     magic, the Shamans); the PvP lines (strong against / resistance to a class) are worth nothing there.
	// MT2009_PLUS_BOT_DS_ALCHEMY_GUIDE_V1 (the owner, 27 October 2026: "Naucz botow nastepujacych informacji:
	// m2-helper.com/en/dragon-alchemy" - cache/yohara/m2helper-dragon-alchemy.md; its kinds are our 'global' table,
	// dragon_soul_applys.global.txt), checked against this world, per kind (basic | additional lines):
	//   Ametyst  Strong vs Devils, Precision, Sung Ma Vitality | Sung Ma Strength/Resistance/Intelligence, vs Metin -
	//            the first kind on Yohara: Devils are the Sung Ma maps' main race and the Will gates the maps
	//            (Strength under the map's halves the blows, ChampionDamage). Precision (HIT_PCT) is NOTHING to a
	//            bot: every bot counts as one of the top Precision ("Ten system ich nie dotyczy", the owner, 22
	//            October; ChampionDamage skips the miss for bots) - 0 here;
	//   Jadeit   SP, wind | max HP, HP %, HP absorb (steal), HP regen, HP restore on a kill - the Champion's
	//            survival, second after the Amethyst for every class;
	//   Granat   max HP, lightning | SP lines - its basic HP counts, its additional lines little (bots drink);
	//   Rubin    STR, fire | attack value, average (normal hit) damage, defence, normal hit resistance - the
	//            physical classes' damage stone;
	//   Diament  INT, ice | skill damage, magic attack, skill resistance, magic defence - the casters' (black
	//            magic Sura, Shamans) and every skill user's; the bots fight with their skills, so skill damage
	//            is high for all, magic attack for the casters only;
	//   Onyks    VIT, dark | block, arrow dodge, crit/pierce resistance, melee reflect - defensive, middle;
	//   Szafir   DEX, earth | strong against / resistance to a class - PvP only, nothing on the Sung Ma maps.
	//   The elements of a kind's basic lines (power and resistance) by the Sung Ma maps' shares above.
	// The 'mt2009' mode's lines (race bonuses on the basic lines, crit/pierce on the Amethyst) keep their values.
	// Not taught (not in this world or worth nothing to a bot): the set bonus - the engine gives an all-7-of-one-
	// grade (Legendary or Mythic) deck only an affect with no point (char_dragonsoul.cpp DragonSoul_SetBonus,
	// AFFECT_DS_SET, POINT_NONE), so no stone is chosen for a set; the Dragon Flame (100700, a Mythic stone's lines
	// rerolled for 1/3/9/27/81 flames) - no shop sells it, a bot gets one from a goblin's box now and then, and a
	// Highest stone's reroll takes 81; the Dragon Tongs (100100: no shop sells them; 100101 Tongs+ at the
	// Alchemist, 100 000 000 a pull-out) - a bulk alchemist pulls out only a stand-in or a stone a strictly better
	// one replaces, which is no loss worth that; the Change Stone (100600) - the ItemShop's.
	// Taught besides the lines: the blue and pink beans (PickPlayerBotDsBean), the bean break-even
	// (IsPlayerBotDsStrengthWorthTrying) and the Tongs of Time (MakePlayerBotDragonHeart).
	int GetPlayerBotDsYoharaLinePref(WORD type, LPCHARACTER ch) // MT2009_PLUS_WIDE_ATTR_V1
	{
		const BYTE job = ch ? ch->GetJob() : JOB_WARRIOR;
		const BYTE group = ch ? ch->GetSkillGroup() : 0;
		const bool magic = (job == JOB_SURA && group == 2) || job == JOB_SHAMAN;
		const bool archer = job == JOB_ASSASSIN && group == 2;
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V1 (the owner, 28 October 2026): a bot with a hunt element wants that element's
		// power and resistance lines and no other element's; the Onyx's lines (melee block, arrow dodge, crit and pierce
		// resistance - "the most important dragon stone on Yohara") over the old middle.
		const int hunt = (int)GetPlayerBotHuntElement(ch) - 1;
		if (hunt >= 0)
		{
			const int resistE = GetPlayerBotResistLineElement(type);
			if (resistE >= 0)
				return resistE == hunt ? 10 : 1;
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_ELEMENTS_V1)
			if (type >= POINT_ENCHANT_ELECT && type <= POINT_ENCHANT_DARK)
				return type - POINT_ENCHANT_ELECT == hunt ? 9 : 1;
#endif
			switch (type)
			{
				case POINT_BLOCK: return 9;
				case POINT_DODGE: return 8;
				case POINT_RESIST_PENETRATE: return 8;
				case POINT_RESIST_CRITICAL: return 7;
				default: break;
			}
		}
		switch (type)
		{
			case POINT_SUNGMA_STR: return 10;
			case POINT_SUNGMA_HP: return 9;
			case POINT_SUNGMA_MOVE: return 9;
			case POINT_SUNGMA_IMMUNE: return 6;
			case POINT_ATTBONUS_MONSTER: return 8;
			case POINT_ATTBONUS_DEVIL: return 9;
			case POINT_ATTBONUS_HUMAN: return 7;
			case POINT_ATTBONUS_ANIMAL: return 5;
			case POINT_ATTBONUS_STONE: return 4;
			case POINT_ATTBONUS_ORC: return 1;
			case POINT_ATTBONUS_UNDEAD: return 1;
			case POINT_ATTBONUS_MILGYO: return 1;
			case POINT_ENCHANT_ICE: return 7;
			case POINT_ENCHANT_DARK: return 7;
			case POINT_ENCHANT_EARTH: return 5;
			case POINT_ENCHANT_ELECT: return 4;
			case POINT_ENCHANT_WIND: return 3;
			case POINT_ENCHANT_FIRE: return 2;
			case POINT_RESIST_ICE: return 5;
			case POINT_RESIST_DARK: return 5;
			case POINT_RESIST_EARTH: return 4;
			case POINT_RESIST_ELEC: return 3;
			case POINT_RESIST_WIND: return 2;
			case POINT_RESIST_FIRE: return 1;
			case POINT_CRITICAL_PCT: return magic ? 4 : 8;
			case POINT_PENETRATE_PCT: return magic ? 4 : 8;
			case POINT_ATT_GRADE_BONUS: return magic ? 3 : 8;
			case POINT_MAGIC_ATT_GRADE_BONUS: return magic ? 9 : 1;
			case POINT_SKILL_DAMAGE_BONUS: return magic ? 9 : 7;
			case POINT_NORMAL_HIT_DAMAGE_BONUS: return magic ? 1 : (archer ? 8 : 7);
			case POINT_MAX_HP_PCT: return 9;
			case POINT_MAX_HP: return 7;
			case POINT_STEAL_HP:
			{
				// MT2009_PLUS_STEAL_CAP_V1: the engine takes at most 50% - the gear near it leaves the stones little room.
				const int gear = ch ? GetPlayerBotGearStealHp(ch, -1) : 0;
				return gear >= 50 ? 0 : (gear >= 35 ? 3 : 7);
			}
			case POINT_KILL_HP_RECOVERY: return 4;
			case POINT_HP_REGEN: return 4;
			case POINT_NORMAL_HIT_DEFEND_BONUS: return 6;
			case POINT_DEF_GRADE_BONUS: return 5;
			case POINT_SKILL_DEFEND_BONUS: return 4;
			case POINT_MAGIC_DEF_GRADE_BONUS: return 3;
			case POINT_BLOCK: return 5;
			case POINT_DODGE: return 3;	// arrows only (the guide: "unik strzal")
			case POINT_REFLECT_MELEE: return 4;
			case POINT_RESIST_CRITICAL: return 4;
			case POINT_RESIST_PENETRATE: return 4;
			case POINT_HIT_PCT: return 0;	// Precision: a bot never misses (above)
			case POINT_ST: return (job == JOB_WARRIOR || (job == JOB_SURA && group != 2)) ? 6 : 1;
			case POINT_DX: return job == JOB_ASSASSIN ? 6 : 1;
			case POINT_IQ: return magic ? 6 : 1;
			case POINT_HT: return 4;
			case POINT_MAX_SP: case POINT_SP_REGEN: case POINT_STEAL_SP: case POINT_KILL_SP_RECOVER: case POINT_MAX_SP_PCT:
				return job == JOB_SHAMAN ? 3 : 2;
			default: return 0;	// the PvP lines and anything else: nothing on Yohara
		}
	}

	// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: a stone of the kind whose basic line is the hunt element's resistance.
	// MT2009_PLUS_BOT_ELEMENT_PET_V1 (ds kind): with the global table (m2_bonus_global) by the stone's kind too - a stone
	// below Ancient has one basic line only (ApplyNumSettings basis 1 1 1 2 2 3), so a Normal, Brilliant or Rare stone
	// of the hunt kind had no resistance line yet and its grade work never went first.
	int GetPlayerBotDsKindElement(LPITEM stone)
	{
		// Diament ice, Rubin fire, Jadeit wind, Szafir earth, Granat lightning, Onyks dark (the element index: lightning 0,
		// fire 1, ice 2, wind 3, earth 4, dark 5); the Ametyst none
		static const int s_aiKindElement[6] = { 2, 1, 3, 4, 0, 5 };
		const int kind = stone ? (int)(stone->GetVnum() / 10000) - 11 : -1;
		return kind >= 0 && kind < 6 ? s_aiKindElement[kind] : -1;
	}

	bool IsPlayerBotDsHuntKindStone(LPCHARACTER ch, LPITEM stone)
	{
		const int hunt = (int)GetPlayerBotHuntElement(ch) - 1;
		if (stone && hunt >= 0 && stone->IsDragonSoul() && GetPlayerBotDsKindElement(stone) == hunt &&
				quest::CQuestManager::instance().GetEventFlag("m2_bonus_global") != 0)
			return true;
		for (int i = 0; stone && hunt >= 0 && i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			if (stone->GetAttributeType(i) != 0 && GetPlayerBotResistLineElement(stone->GetAttributeType(i)) == hunt)
				return true;
		return false;
	}

	struct TPlayerBotAlchemyStats
	{
		unsigned shards, cors, opened, equipped, refinesGrade, refinesStep, refinesStrength, refineFails,
				elixirs, beans, listed, trips;
		// MT2009_PLUS_MARKET_SINK_V1: Cors off the counters.
		unsigned corLinesBought;
		unsigned long long corUnitsBought, corYang;
		// MT2009_PLUS_BOT_DS_EXTEND_V1: stones recharged (an elixir on an
		// expired or running-out stone worth keeping), expired good stones
		// kept in the deck for the Alchemist, deck switches.
		unsigned recharged, keptExpired, deckOn, deckOff;
		// MT2009_PLUS_BOT_DS_KEEP_WORN_V1: pull-outs (only for a strict
		// upgrade) and the ones the engine's odds destroyed.
		unsigned pulledOut, pullOutDestroyed;
		// MT2009_PLUS_BOT_DS_YOHARA800_V1: the bulk alchemists - Cors opened, Mythic stones made (a legendary
		// pair that took), Mythic Highest made, stones taken to their cap (+6 on a Highest), beans spent.
		unsigned bulkOpened, bulkMythMade, bulkHighestMade, bulkCapMade, bulkBeans;
	};
	TPlayerBotAlchemyStats s_kPlayerBotAlchemyStats = { 0 };

	// ------------------------------------------------------------ the daily Cors

	// Called on every monster a bot kills (NotePlayerBotBattleHorseKill).
	void NotePlayerBotDragonShardKill(LPCHARACTER ch, LPCHARACTER victim)
	{
		if (!ch || ch->GetLevel() < PLAYERBOT_ALCHEMY_MIN_LEVEL || ArePlayerBotAlchemyOff())
			return;
		// The player's rule (dragon_soul.quest): only a monster at most 15
		// levels under the killer, or any higher (operator, 27 September 2026).
		if (!victim || (int)victim->GetLevel() < (int)ch->GetLevel() - 15)
			return;
		const int today = (int)(get_global_time() / 86400);
		if (ch->GetQuestFlag(PLAYERBOT_DS_DAY_FLAG) != today)
		{
			ch->SetQuestFlag(PLAYERBOT_DS_DAY_FLAG, today);
			ch->SetQuestFlag(PLAYERBOT_DS_LEFT_FLAG, GetPlayerBotDragonCorsPerDay());
		}
		const int left = ch->GetQuestFlag(PLAYERBOT_DS_LEFT_FLAG);
		if (left <= 0)
			return;
		int chance = quest::CQuestManager::instance().GetEventFlag("ds_drop");
		if (chance < 1 || chance > 100)
			chance = 10;
		if (number(1, 100) > chance)
			return;
		++s_kPlayerBotAlchemyStats.shards;
		const int shards = ch->GetQuestFlag(PLAYERBOT_DS_SHARDS_FLAG) + 1;
		if (shards < PLAYERBOT_DS_SHARDS_PER_COR)
		{
			ch->SetQuestFlag(PLAYERBOT_DS_SHARDS_FLAG, shards);
			return;
		}
		if (ch->GetEmptyInventory(1) < 0 || !ch->AutoGiveItem(PLAYERBOT_COR_ROUGH_VNUM, 1, -1, false))
		{
			// No room: the shards wait, as a player's would in the bag.
			ch->SetQuestFlag(PLAYERBOT_DS_SHARDS_FLAG, shards);
			return;
		}
		ch->SetQuestFlag(PLAYERBOT_DS_SHARDS_FLAG, 0);
		ch->SetQuestFlag(PLAYERBOT_DS_LEFT_FLAG, left - 1);
		++s_kPlayerBotAlchemyStats.cors;
		sys_log(0, "PLAYERBOT_ALCHEMY: daily cor pid=%u name=%s left_today=%d user=%d",
				ch->GetPlayerID(), ch->GetName(), left - 1, IsPlayerBotAlchemyUser(ch) ? 1 : 0);
	}

	bool IsPlayerBotCorVnum(DWORD vnum)
	{
		return vnum == PLAYERBOT_COR_ROUGH_VNUM || vnum == 50260;
	}

	// MT2009_PLUS_BOT_DS_YOHARA800_V1: every Cor that opens into Dragon Stones (special_item_group.txt 50255 and
	// special_item_group.cors.txt): the 5025x grades (cut, rare, antique, legendary) and the 515xx series - the plain,
	// ranked, coloured and "+" ones (51501-51638). Not the Smocza Skrzynia chests (51639-51646, Cors into the bag)
	// nor 50252. IsPlayerBotCorVnum stays the rough Cor of the market's lines.
	bool IsPlayerBotOpenableCorVnum(DWORD vnum)
	{
		return (vnum >= PLAYERBOT_COR_ROUGH_VNUM && vnum <= 50260) || (vnum >= 51501 && vnum <= 51638);
	}

	// A user's Cors are its own; everybody else's are goods, a line of at
	// least PLAYERBOT_COR_LINE_MIN_UNITS.
	// MT2009_PLUS_BOT_DS_YOHARA800_V1: every Cor it opens (not only the rough one).
	bool IsPlayerBotKeptCor(LPCHARACTER ch, LPITEM item)
	{
		return ch && item && IsPlayerBotOpenableCorVnum(item->GetVnum()) && IsPlayerBotAlchemyUser(ch);
	}

	// MT2009_PLUS_BOT_DS_YOHARA800_V1 (point 4 of the order): what an alchemy user still needs is never the
	// merchant's or a counter's - its Cors (above), its Green Dragon Beans, and, for a bulk alchemist (the Yohara
	// cohorts the owner handed 400 Wzmocnienie and 800 Zaczarowanie Przedmiotu), the bonus stones 71084/71085
	// (ANTI_SELL/ANTI_MYSHOP anyway; this holds them against an operator's "merchant" word too). Asked first by
	// IsPlayerBotJunkItem (playerbot_economy.h) and ScorePlayerBotShopStockRules (playerbot_town.h).
	bool IsPlayerBotKeptAlchemyGoods(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item)
			return false;
		const DWORD vnum = item->GetVnum();
		if (IsPlayerBotOpenableCorVnum(vnum))
			return IsPlayerBotKeptCor(ch, item);
		if (vnum == PLAYERBOT_DS_GREEN_BEAN_VNUM || vnum == PLAYERBOT_DS_BLUE_BEAN_VNUM ||
				vnum == PLAYERBOT_DS_PINK_BEAN_VNUM)	// MT2009_PLUS_BOT_DS_ALCHEMY_GUIDE_V1: the blue and pink too
			return IsPlayerBotAlchemyUser(ch);
		// MT2009_PLUS_BOT_DS_ALCHEMY_GUIDE_V1: a bulk alchemist's Tongs of Time and Dragon Hearts (its stones' time).
		if (vnum == PLAYERBOT_DS_TIME_TONGS_VNUM || vnum == PLAYERBOT_DS_DRAGON_HEART_VNUM)
			return IsPlayerBotDsBulk(ch);
		if (vnum == PLAYERBOT_BONUS_CHANGE_VNUM || vnum == PLAYERBOT_BONUS_ADD_VNUM)
			return IsPlayerBotDsBulk(ch);
		return false;
	}

	int CountPlayerBotLegendaryCors(LPCHARACTER ch)
	{
		return ch ? (int)ch->CountSpecifyItem(PLAYERBOT_COR_LEGENDARY_VNUM) + (int)ch->CountSpecifyItem(PLAYERBOT_COR_LEGENDARY_515_VNUM) : 0;
	}

	// A bot that is no alchemy user yet but holds PLAYERBOT_DS_BULK_COR_MIN legendary Cors becomes a bulk alchemist
	// for good (the flag), looked at every PLAYERBOT_DS_BULK_HOLDER_LOOK_MS.
	void NotePlayerBotDsBulkHolder(LPCHARACTER ch, DWORD dwNow)
	{
		static std::map<DWORD, DWORD> s_next;
		if (!ch || !ch->IsPC() || ch->GetLevel() < PLAYERBOT_ALCHEMY_MIN_LEVEL || ArePlayerBotAlchemyOff() ||
				!ch->IsItemLoaded() || ch->GetQuestFlag(PLAYERBOT_DS_BULK_FLAG) != 0)
			return;
		DWORD& next = s_next[ch->GetPlayerID()];
		if (next != 0 && (int)(dwNow - next) < 0)
			return;
		next = dwNow + PLAYERBOT_DS_BULK_HOLDER_LOOK_MS;
		const DWORD pid = ch->GetPlayerID();
		if (IsPlayerBotSidekickPID(pid) || CPlayerBotManager::instance().IsMedalDropperCohortPID(pid))
			return;
		const int legendary = CountPlayerBotLegendaryCors(ch);
		if (legendary < PLAYERBOT_DS_BULK_COR_MIN)
			return;
		ch->SetQuestFlag(PLAYERBOT_DS_BULK_FLAG, 1);
		sys_log(0, "PLAYERBOT_ALCHEMY: bulk alchemist pid=%u name=%s lv=%d legendary_cors=%d cohort=%d",
				pid, ch->GetName(), ch->GetLevel(), legendary, IsPlayerBotYoharaCohortPID(pid) ? 1 : 0);
	}

	bool IsPlayerBotCorStackShort(LPCHARACTER ch, LPITEM item)
	{
		return ch && item && IsPlayerBotCorVnum(item->GetVnum()) &&
				(int)ch->CountSpecifyItem(item->GetVnum()) < PLAYERBOT_COR_LINE_MIN_UNITS;
	}

	// ------------------------------------------------------------ the stones

	struct TPlayerBotDsTarget
	{
		BYTE grade, step, strength;
	};

	// What a user's stones should come to at its level: the refining stops
	// there, and a stone past it is only worn.
	//
	// The grade first - the operator's table (26 September 2026):
	//   Zwykly, Blyszczacy  - never worn, only material;
	//   Rzadki              - worn at low levels (30-54);
	//   Starozytny          - at middle levels (55-74);
	//   Legendarny          - gladly (75-89), and stepped up after it;
	//   Mityczny            - worn by anybody who has one, even unstepped;
	//                         only the end game (90+) makes and steps it.
	// "Wszystkie kamienie alchemii przed wlozeniem powinny byc ulepszane do
	// maksymalnego dostepnego poziomu": a kind is refined as far as the bag
	// allows before its stone goes on (EquipPlayerBotBestDragonSouls), and the
	// stones of the target grade left over are stepped to the highest step. A
	// grade refine gives step 0 and strength 0 (DSManager::DoRefineGrade), so
	// the steps come after the grade.
	const BYTE PLAYERBOT_DS_MIN_WORN_GRADE = 2;
	const BYTE PLAYERBOT_DS_MYTH_GRADE = 5;
	const int PLAYERBOT_DS_END_GAME_LEVEL = 90;

	TPlayerBotDsTarget GetPlayerBotDsTarget(LPCHARACTER ch)
	{
		TPlayerBotDsTarget t = { 0, 0, 0 };
		const int level = ch ? ch->GetLevel() : 0;
		if (level >= PLAYERBOT_DS_END_GAME_LEVEL) { t.grade = 5; t.step = 4; t.strength = 4; }
		else if (level >= 75) { t.grade = 4; t.step = 4; t.strength = 2; }
		else if (level >= 55) { t.grade = 3; t.step = 4; t.strength = 1; }
		else if (level >= PLAYERBOT_ALCHEMY_MIN_LEVEL) { t.grade = 2; t.step = 4; t.strength = 0; }
		return t;
	}

	BYTE GetPlayerBotDsGrade(LPITEM item) { return item ? (BYTE)((item->GetVnum() / 1000) % 10) : 0; }
	BYTE GetPlayerBotDsStep(LPITEM item) { return item ? (BYTE)((item->GetVnum() / 100) % 10) : 0; }
	BYTE GetPlayerBotDsStrength(LPITEM item) { return item ? (BYTE)((item->GetVnum() / 10) % 10) : 0; }

	// What the stone's lines are worth to this character (the gear's own
	// scale); nothing at all for a stone of a kind it gets nothing from.
	long long ScorePlayerBotDsLines(LPCHARACTER ch, LPITEM item)
	{
		long long score = 0;
		for (int i = 0; item && i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			if (item->GetAttributeType(i) != 0)
				score += ScorePlayerBotApplyTiered(item->GetAttributeType(i), item->GetAttributeValue(i), ch);
		return score;
	}

	// MT2009_PLUS_BOT_DS_YOHARA800_V1: the stone's lines for Yohara (GetPlayerBotDsYoharaLinePref): the sum of its
	// lines' preferences - the line's kind, not its size, which only the grade, step and strength set (and those
	// rank first).
	long long ScorePlayerBotDsYoharaLines(LPCHARACTER ch, LPITEM item)
	{
		long long score = 0;
		for (int i = 0; item && i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			if (item->GetAttributeType(i) != 0 && item->GetAttributeValue(i) > 0)
				score += GetPlayerBotDsYoharaLinePref(item->GetAttributeType(i), ch);
		return score;
	}

	// What a stone's lines are worth to this bot: a bulk alchemist's by Yohara's preference, anybody else's by the
	// gear's scale (MT2009_PLUS_BOT_DS_YOHARA800_V1).
	long long ScorePlayerBotDsWorth(LPCHARACTER ch, LPITEM item)
	{
		return IsPlayerBotDsBulk(ch) ? ScorePlayerBotDsYoharaLines(ch, item) : ScorePlayerBotDsLines(ch, item);
	}

	bool IsPlayerBotDsMythHighest(LPITEM item)
	{
		return item && GetPlayerBotDsGrade(item) >= PLAYERBOT_DS_MYTH_GRADE && GetPlayerBotDsStep(item) >= 4;
	}

	// Which of two stones of a kind to wear: grade, then step, then strength,
	// then the lines.
	// MT2009_PLUS_BOT_DS_YOHARA800_V1: a bulk alchemist's by the stone's power first (the WeightTables' percent:
	// a Mythic High +5 is a Mythic Highest +0 and a half), then grade, step, strength and the Yohara lines.
	long long RankPlayerBotDs(LPCHARACTER ch, LPITEM item)
	{
		if (!item)
			return -1;
		if (IsPlayerBotDsBulk(ch))
		{
			const BYTE grade = GetPlayerBotDsGrade(item), step = GetPlayerBotDsStep(item), strength = GetPlayerBotDsStrength(item);
			return (long long)GetPlayerBotDsWeight(grade, step, strength) * 10000000000LL + (long long)grade * 1000000000LL +
					(long long)step * 100000000LL + (long long)strength * 10000000LL +
					std::min<long long>(std::max<long long>(ScorePlayerBotDsYoharaLines(ch, item), 0), 9999999);
		}
		const long long lines = std::min<long long>(std::max<long long>(ScorePlayerBotDsLines(ch, item), 0), 99999);
		return (long long)GetPlayerBotDsGrade(item) * 10000000000LL + (long long)GetPlayerBotDsStep(item) * 1000000000LL +
				(long long)GetPlayerBotDsStrength(item) * 100000000LL + lines;
	}

	bool HasPlayerBotDsTime(LPITEM item)
	{
		return item && DSManager::instance().IsTimeLeftDragonSoul(item);
	}

	// MT2009_PLUS_BOT_DS_EXTEND_V1: a good stone is recharged, not swapped
	// ("Boty nie przedluzaja alchemii ... po skonczeniu jej czasu nie
	// przedluzyl, tylko wyjal ja i zmienil na jakies rzadkie", players,
	// 3 October 2026). Every stone lasts a day of active deck (item_proto
	// limit 9 = 86400 s); the player's way to give it more is the Time
	// Elixir (D) of the Alchemist's shop (shop 13, 100002, USE_TIME_CHARGE_FIX
	// +30000 s, 5 000 000 yang) used on the stone, worn or in the bag
	// (CItem::GiveMoreTime_Fix, an expired stone too). The (M) and (S) ones
	// are not on any shop.
	//
	// A stone is worth the elixir when it is Ancient or over, or when making
	// it again would cost at least two elixirs (a well stepped Rare one);
	// such a stone keeps its place by grade, step, strength and lines with
	// no time left, and the Alchemist recharges it.
	const BYTE PLAYERBOT_DS_KEEP_GRADE = 3;

	long long GetPlayerBotDsElixirPrice()
	{
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(PLAYERBOT_DS_TIME_ELIXIR_VNUM);
		return proto && proto->dwGold ? (long long)proto->dwGold : 0;
	}

	bool IsPlayerBotDsRechargeWorthy(LPITEM item)
	{
		if (!item || !item->IsDragonSoul() || GetPlayerBotDsGrade(item) < PLAYERBOT_DS_MIN_WORN_GRADE)
			return false;
		if (GetPlayerBotDsGrade(item) >= PLAYERBOT_DS_KEEP_GRADE)
			return true;
		const long long elixir = GetPlayerBotDsElixirPrice();
		return elixir > 0 && GetPlayerBotDragonSoulBaseCost(GetPlayerBotDsGrade(item), GetPlayerBotDsStep(item),
				GetPlayerBotDsStrength(item)) >= 2 * elixir;
	}

	// An elixir it can pay for now: one elixir and the refine spare over it.
	// MT2009_PLUS_BOT_DS_KEEP_WORN_V1: the same for every stone - a worn
	// stone is never swapped for a fresh copy (taking it off may destroy
	// it), so an elixir is its only way back.
	bool CanPlayerBotAffordDsElixir(LPCHARACTER ch)
	{
		const long long elixir = GetPlayerBotDsElixirPrice();
		if (!ch || elixir <= 0)
			return false;
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch);
		return spare >= elixir + PLAYERBOT_DS_REFINE_SPARE;
	}

	void CollectPlayerBotDragonSouls(LPCHARACTER ch, std::vector<LPITEM>& out, int kind = -1)
	{
		out.clear();
		if (!ch || !ch->IsItemLoaded())
			return;
		for (int cell = 0; cell < DRAGON_SOUL_INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetItem(TItemPos(DRAGON_SOUL_INVENTORY, cell));
			if (!item || item->GetCell() != cell || !item->IsDragonSoul() || item->isLocked() || item->IsExchanging())
				continue;
			if (kind >= 0 && item->GetSubType() != kind)
				continue;
			out.push_back(item);
		}
	}

	LPITEM GetPlayerBotWornDs(LPCHARACTER ch, int kind)
	{
		if (!ch || kind < 0 || kind >= DS_SLOT_MAX)
			return NULL;
		return ch->GetItem(TItemPos(INVENTORY, DRAGON_SOUL_EQUIP_SLOT_START + kind));
	}

	// MT2009_PLUS_BOT_DS_EXTEND_V1: the stone the kind's slot is for - the
	// best by grade, step, strength and lines of the worn one and the bag's,
	// of the rare grade and over, with lines worth something, and with time
	// left or worth an elixir. Time does not rank: an expired perfect mythic
	// stone stays the kind's stone over a fresh rare one.
	LPITEM GetPlayerBotDsIntended(LPCHARACTER ch, int kind)
	{
		std::vector<LPITEM> stones;
		CollectPlayerBotDragonSouls(ch, stones, kind);
		LPITEM worn = GetPlayerBotWornDs(ch, kind);
		if (worn)
			stones.push_back(worn);
		LPITEM best = NULL;
		for (size_t i = 0; i < stones.size(); ++i)
		{
			LPITEM s = stones[i];
			// The worn stone always counts (MT2009_PLUS_BOT_DS_KEEP_WORN_V1:
			// it stays on until a strictly better one is ready).
			if (s != worn && (GetPlayerBotDsGrade(s) < PLAYERBOT_DS_MIN_WORN_GRADE || ScorePlayerBotDsWorth(ch, s) <= 0 ||
					(!HasPlayerBotDsTime(s) && !IsPlayerBotDsRechargeWorthy(s))))
				continue;
			if (!best || RankPlayerBotDs(ch, s) > RankPlayerBotDs(ch, best) ||
					(RankPlayerBotDs(ch, s) == RankPlayerBotDs(ch, best) && s == worn))
				best = s;
		}
		return best;
	}

	// The stone of a kind the Alchemist should put an elixir on: the kind's
	// stone (the worn one, unless a strictly better one waits in the bag)
	// when it runs low, while the purse allows.
	LPITEM GetPlayerBotDsRechargeTarget(LPCHARACTER ch, int kind)
	{
		LPITEM intended = GetPlayerBotDsIntended(ch, kind);
		if (intended && intended->GetSocket(ITEM_SOCKET_REMAIN_SEC) < PLAYERBOT_DS_ELIXIR_BELOW_SEC &&
				!IsPlayerBotSidekickLockedItem(ch, intended) && CanPlayerBotAffordDsElixir(ch))
			return intended;
		return NULL;
	}

	// Surplus - the counter's: every unworn stone of a bot that does not use
	// alchemy; for a user, a stone its kind's best already beats and the
	// refining cannot use (over its target, or past the material it keeps),
	// or one whose lines give its class nothing and that is no material.
	bool IsPlayerBotSurplusDragonSoul(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !item->IsDragonSoul() || item->IsEquipped() || item->isLocked())
			return false;
		// An ordinary or brilliant stone is never goods: nobody buys one, and
		// it is the material of the rare grade ("boty niech nie wystawiaja
		// surowej smoczej alchemii ... dopiero od 3 poziomu", operator, 26
		// September 2026).
		if (GetPlayerBotDsGrade(item) < PLAYERBOT_DS_MIN_WORN_GRADE)
			return false;
		if (!IsPlayerBotAlchemyUser(ch))
			return true;
		// MT2009_PLUS_BOT_DS_YOHARA800_V1: a bulk alchemist's stones are all material or spares, never goods.
		if (IsPlayerBotDsBulk(ch))
			return false;
		const int kind = item->GetSubType();
		// MT2009_PLUS_BOT_DS_EXTEND_V1: the kind's stone, expired or not,
		// is never goods.
		if (GetPlayerBotDsIntended(ch, kind) == item)
			return false;
		LPITEM worn = GetPlayerBotWornDs(ch, kind);
		const TPlayerBotDsTarget t = GetPlayerBotDsTarget(ch);
		const BYTE grade = GetPlayerBotDsGrade(item);
		// Material: under the target grade, one of the first
		// PLAYERBOT_DS_MATERIAL_KEEP of its kind and grade.
		if (grade < t.grade || (grade == t.grade && GetPlayerBotDsStep(item) < t.step))
		{
			std::vector<LPITEM> same;
			CollectPlayerBotDragonSouls(ch, same, kind);
			int ahead = 0;
			for (size_t i = 0; i < same.size(); ++i)
				if (same[i] != item && GetPlayerBotDsGrade(same[i]) == grade && same[i]->GetCell() < item->GetCell())
					++ahead;
			return ahead >= PLAYERBOT_DS_MATERIAL_KEEP;
		}
		if (ScorePlayerBotDsLines(ch, item) <= 0)
			return true;
		return worn && RankPlayerBotDs(ch, worn) >= RankPlayerBotDs(ch, item);
	}

	// ------------------------------------------------------------ the market

	// A user buys Cors while it holds fewer than PLAYERBOT_DS_COR_KEEP, and a
	// stone of a kind it wears nothing of or a worse one of, up to its target
	// grade, with lines worth something to it.
	// MT2009_PLUS_MARKET_SINK_V1: the Cors on the counters of the world.
	bool IsPlayerBotCorMarketPlentiful()
	{
		return GetPlayerBotOperatorGoodsSupply(PLAYERBOT_COR_ROUGH_VNUM) >= PLAYERBOT_COR_MARKET_PLENTY_UNITS;
	}

	int GetPlayerBotCorKeep()
	{
		return IsPlayerBotCorMarketPlentiful() ? PLAYERBOT_DS_COR_KEEP_PLENTY : PLAYERBOT_DS_COR_KEEP;
	}

	bool WantsPlayerBotAlchemyOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!ch || !offer || !IsPlayerBotAlchemyUser(ch))
			return false;
		if (IsPlayerBotCorVnum(offer->GetVnum()))
		{
			const int have = (int)ch->CountSpecifyItem(offer->GetVnum());
			const int keep = GetPlayerBotCorKeep();
			return have < keep && (int)offer->GetCount() <= keep - have + PLAYERBOT_COR_LINE_MAX_UNITS;
		}
		if (!offer->IsDragonSoul())
			return false;
		// A stone it would wear: of the rare grade and over, up to its target
		// (a mythic one whatever the target).
		const TPlayerBotDsTarget t = GetPlayerBotDsTarget(ch);
		const BYTE grade = GetPlayerBotDsGrade(offer);
		if (grade < PLAYERBOT_DS_MIN_WORN_GRADE || (grade > t.grade && grade < PLAYERBOT_DS_MYTH_GRADE) ||
				ScorePlayerBotDsWorth(ch, offer) <= 0)
			return false;
		LPITEM worn = GetPlayerBotWornDs(ch, offer->GetSubType());
		return !worn || RankPlayerBotDs(ch, offer) > RankPlayerBotDs(ch, worn);
	}

	bool CanPlayerBotPayForAlchemyOffer(LPCHARACTER ch, LPITEM item, long long price)
	{
		if (!ch || !item || price <= 0)
			return false;
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) -
				(long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		if (IsPlayerBotCorVnum(item->GetVnum()))
		{
			const long long unit = price / std::max<long long>(1, (long long)item->GetCount());
			// MT2009_PLUS_OWNER_PRICES_V2: and the higher the user, the more
			// (GetPlayerBotOperatorLevelPercent, playerbot_town.h).
			const int purse = IsPlayerBotCorMarketPlentiful() ? PLAYERBOT_DS_COR_PLENTY_PURSE : 40;
			return unit <= (long long)ScalePlayerBotIwakuraPrice(GetPlayerBotCorDraconisPrice(item->GetVnum())) * PLAYERBOT_DS_COR_BUY_MULT *	// MT2009_PLUS_COR_GRADE_PRICE_V1
						GetPlayerBotOperatorLevelPercent((int)ch->GetLevel()) / 100 &&
					price <= spare * purse / 100;
		}
		return price <= (long long)GetPlayerBotDragonSoulPrice(item) * 12 / 10 && price <= spare * 25 / 100;
	}

	bool PlayerBotWantsAlchemyFromMarket(LPCHARACTER ch)
	{
		if (!IsPlayerBotAlchemyUser(ch) || (int)ch->CountSpecifyItem(PLAYERBOT_COR_ROUGH_VNUM) >= GetPlayerBotCorKeep())
			return false;
		const TPlayerBotMarketLedgerEntry* cors = GetPlayerBotMarketLedgerEntry(PLAYERBOT_COR_ROUGH_VNUM);
		return cors && cors->dwSupplyUnits > 0 &&
				(long long)ch->GetGold() - GetPlayerBotReservedGold(ch) > 1000000LL;
	}

	// ------------------------------------------------------------ in the field

	// Qualified the way the Alchemist's first errand qualifies a player.
	void EnsurePlayerBotAlchemyQualified(LPCHARACTER ch)
	{
		if (ch && !ch->DragonSoul_IsQualified())
		{
			ch->DragonSoul_GiveQualification();
			sys_log(0, "PLAYERBOT_ALCHEMY: qualified pid=%u name=%s", ch->GetPlayerID(), ch->GetName());
		}
	}

	// MT2009_PLUS_BOT_COR_ROOM_V1: the alchemy bag is a page of 32 cells for
	// every kind and grade (DSManager::GetBasePosition), and a Cor gives a
	// rough stone of a RANDOM kind - the bag's total said "room" while the
	// page of the kind that came out was full, and the stone fell on the
	// ground, where nobody picks it up (players, 2 October). A Cor is opened
	// only while every kind's rough page has a free cell.
	bool PlayerBotHasRoomForEveryRoughKind(LPCHARACTER ch)
	{
		if (!ch || !ch->DragonSoul_IsQualified())
			return false;
		for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
		{
			const int base = kind * DRAGON_SOUL_GRADE_MAX * DRAGON_SOUL_BOX_SIZE;
			bool room = false;
			for (int i = 0; i < DRAGON_SOUL_BOX_SIZE && !room; ++i)
				room = ch->IsEmptyItemGrid(TItemPos(DRAGON_SOUL_INVENTORY, (WORD)(base + i)), 1);
			if (!room)
				return false;
		}
		return true;
	}

	// MT2009_PLUS_BOT_DS_YOHARA800_V1: the alchemy bag's page of one kind and grade has a free cell.
	bool PlayerBotDsPageHasRoom(LPCHARACTER ch, int kind, int grade)
	{
		if (!ch || kind < 0 || kind >= DS_SLOT_MAX || grade < 0 || grade >= DRAGON_SOUL_GRADE_MAX)
			return false;
		const int base = kind * DRAGON_SOUL_GRADE_MAX * DRAGON_SOUL_BOX_SIZE + grade * DRAGON_SOUL_BOX_SIZE;
		for (int i = 0; i < DRAGON_SOUL_BOX_SIZE; ++i)
			if (ch->IsEmptyItemGrid(TItemPos(DRAGON_SOUL_INVENTORY, (WORD)(base + i)), 1))
				return true;
		return false;
	}

	// MT2009_PLUS_BOT_DS_YOHARA800_V1: room for whatever this Cor may give - every page (kind, grade) of a stone of
	// its group (special_item_group: a 5025x/51510 Cor one grade of a random kind, a ranked 515xx one several grades,
	// a coloured one its own kind). A group the table does not know: the rough rule.
	bool PlayerBotHasRoomForCor(LPCHARACTER ch, DWORD corVnum)
	{
		if (!ch || !ch->DragonSoul_IsQualified())
			return false;
		const CSpecialItemGroup* group = ITEM_MANAGER::instance().GetSpecialItemGroup(corVnum);
		if (!group)
			return PlayerBotHasRoomForEveryRoughKind(ch);
		const std::vector<CSpecialItemGroup::CSpecialItemInfo> items = group->GetItems();
		bool any = false;
		for (size_t i = 0; i < items.size(); ++i)
		{
			const DWORD v = items[i].vnum;
			if (v < 110000 || v > 179999)
				continue;
			any = true;
			if (!PlayerBotDsPageHasRoom(ch, (int)((v / 10000) % 10) - 1, (int)((v / 1000) % 10)))
				return false;
		}
		return any || PlayerBotHasRoomForEveryRoughKind(ch);
	}

	// MT2009_PLUS_BOT_EKW_PAGES_V1: the bag and the extra inventory's pages.
	int CountPlayerBotOpenableCors(LPCHARACTER ch)
	{
		int n = 0;
		std::vector<LPITEM> owned;
		CollectPlayerBotOwnedItems(ch, owned);
		for (size_t i = 0; i < owned.size(); ++i)
			if (IsPlayerBotOpenableCorVnum(owned[i]->GetVnum()))
				n += (int)owned[i]->GetCount();
		return n;
	}

	// MT2009_PLUS_BOT_EKW_PAGES_V1: a Cor of the extra inventory the pass may open (OpenPlayerBotCors's own tests).
	bool MatchPlayerBotOpenableCor(LPCHARACTER ch, LPITEM item, const void*)
	{
		return IsPlayerBotOpenableCorVnum(item->GetVnum()) && !item->isLocked() && !IsPlayerBotSidekickKeptForOwner(ch, item) &&
				PlayerBotHasRoomForCor(ch, item->GetVnum());
	}

	// Its Cors opened while the alchemy bag has room: the Cor's group is one
	// rough stone of a random kind (special_item_group.txt, 50255).
	// MT2009_PLUS_BOT_DS_YOHARA800_V1: every Cor that opens into stones (IsPlayerBotOpenableCorVnum), by the
	// engine's own use (UseItem: the giftbox path, its own 60-in-500-ms budget), each while the pages it may
	// fill have room - a full legendary page waits for the Alchemist to turn its pairs into Mythic stones.
	int OpenPlayerBotCors(LPCHARACTER ch)
	{
		int opened = 0;
		const bool bulk = IsPlayerBotDsBulk(ch);
		const int perPass = bulk ? PLAYERBOT_DS_BULK_COR_OPEN_PER_PASS : PLAYERBOT_DS_COR_OPEN_PER_PASS;
		// A user that holds legendary Cors in number is a bulk alchemist from now on.
		if (!bulk && ch->GetQuestFlag(PLAYERBOT_DS_BULK_FLAG) == 0 && CountPlayerBotLegendaryCors(ch) >= PLAYERBOT_DS_BULK_COR_MIN)
		{
			ch->SetQuestFlag(PLAYERBOT_DS_BULK_FLAG, 1);
			sys_log(0, "PLAYERBOT_ALCHEMY: bulk alchemist pid=%u name=%s lv=%d legendary_cors=%d cohort=%d", ch->GetPlayerID(),
					ch->GetName(), ch->GetLevel(), CountPlayerBotLegendaryCors(ch), IsPlayerBotYoharaCohortPID(ch->GetPlayerID()) ? 1 : 0);
		}
		// MT2009_PLUS_BOT_EKW_PAGES_V1: the bag holding none, a stack from the extra inventory (opened from the bag)
		PlayerBotEkwFetchMatching(ch, MatchPlayerBotOpenableCor, NULL, 1);
		std::set<DWORD> noRoom;
		for (int cell = 0; cell < PLAYERBOT_BAG_CELLS && opened < perPass; ++cell)
		{
			LPITEM item = ch->GetInventoryItem((WORD)cell);
			if (!item || item->GetCell() != cell || !IsPlayerBotOpenableCorVnum(item->GetVnum()) || item->isLocked())
				continue;
			if (noRoom.count(item->GetVnum()))
				continue;
			// MT2009_PLUS_SIDEKICK_KEEP_VALUABLES_V1: a companion opens only a
			// Cor its owner handed it; the ones off the owner's kills are the
			// owner's.
			if (IsPlayerBotSidekickKeptForOwner(ch, item))
				continue;
			std::vector<LPITEM> stones;
			CollectPlayerBotDragonSouls(ch, stones);
			if ((int)stones.size() >= DRAGON_SOUL_INVENTORY_MAX_NUM - 8)
				break;
			// MT2009_PLUS_BOT_COR_ROOM_V1; MT2009_PLUS_BOT_DS_YOHARA800_V1: the pages this Cor may fill.
			if (!PlayerBotHasRoomForCor(ch, item->GetVnum()))
			{
				PlayerBotLogThrottled("alchemy_cor_room", get_dword_time(),
						"PLAYERBOT_ALCHEMY: cor kept, its page is full pid=%u name=%s vnum=%u", ch->GetPlayerID(), ch->GetName(),
						item->GetVnum());
				noRoom.insert(item->GetVnum());
				continue;
			}
			if (!ch->UseItem(TItemPos(INVENTORY, (WORD)cell)))
				break;
			++opened;
			++s_kPlayerBotAlchemyStats.opened;
			if (bulk)
				++s_kPlayerBotAlchemyStats.bulkOpened;
			--cell;	// the stack may still be there
		}
		if (opened)
		{
			ch->SetQuestFlag(PLAYERBOT_DS_OPENED_FLAG, ch->GetQuestFlag(PLAYERBOT_DS_OPENED_FLAG) + opened);
			sys_log(0, "PLAYERBOT_ALCHEMY: opened pid=%u name=%s cors=%d left=%d", ch->GetPlayerID(), ch->GetName(),
					opened, CountPlayerBotOpenableCors(ch));
		}
		return opened;
	}

	bool PullOutPlayerBotDs(LPCHARACTER ch, LPITEM item)
	{
		if (!item || !item->IsEquipped())
			return true;
		// MT2009_PLUS_SIDEKICK_EQUIP_LOCK_V1: a locked companion's stays on.
		if (IsPlayerBotSidekickLockedItem(ch, item))
			return false;
		const int cell = ch->GetEmptyDragonSoulInventory(item);
		if (cell < 0)
			return false;
		// MT2009_PLUS_BOT_DS_KEEP_WORN_V1: a pull-out without an extractor
		// keeps the stone only DragonSoulExtTables' share of the time (rare
		// and ancient 30%, legendary 20%, mythic 15%) and destroys it
		// otherwise (DSManager::PullOut, DS_PULL_OUT_FAILED; 2531 failed
		// against 1014 kept on the supporters' world, 30 September - 3
		// October). Only a strict upgrade calls this (EquipPlayerBotBestDragonSouls).
		const DWORD vnum = item->GetVnum();
		LPITEM moved = item;
		const bool ok = DSManager::instance().PullOut(ch, TItemPos(DRAGON_SOUL_INVENTORY, (WORD)cell), moved);
		++s_kPlayerBotAlchemyStats.pulledOut;
		if (!moved)
		{
			++s_kPlayerBotAlchemyStats.pullOutDestroyed;
			sys_log(0, "PLAYERBOT_DS: pull-out destroyed pid=%u name=%s vnum=%u", ch->GetPlayerID(), ch->GetName(), vnum);
			return false;
		}
		return ok && !moved->IsEquipped();
	}

	int FindPlayerBotDsRefine(LPCHARACTER ch, int kind, LPITEM& a, LPITEM& b);

	// MT2009_PLUS_BOT_DS_YOHARA800_V1: while a bulk alchemist's kind is still refined (hours), its empty deck slot
	// holds a stand-in: the best non-Mythic stone of the kind (Rare, Ancient or Legendary) that is not in the refine
	// at hand. A stand-in costs one stone of material (a pull-out keeps a Legendary one 20%, an Ancient or Rare one
	// 30% - DragonSoulExtTables), about 1% of the ~104 legendary stones a Mythic Highest takes, for 30-50% of the
	// kind's power meanwhile (a Legendary at 30-50 of the WeightTables' percent against nothing). A Mythic stone is
	// never a stand-in: a Mythic Lowest is ~3% of a Mythic Highest's material and comes back 15% of the time; the
	// Mythic step work of a kind is a few minutes once its legendary pairs are done. When the kind is finished,
	// the final stone takes the slot as a strict upgrade (EquipPlayerBotBestDragonSouls).
	bool PlacePlayerBotDsInterim(LPCHARACTER ch, int kind, const std::vector<LPITEM>& stones, LPITEM a, LPITEM b)
	{
		LPITEM pick = NULL;
		for (size_t i = 0; i < stones.size(); ++i)
		{
			LPITEM s = stones[i];
			if (s == a || s == b || !HasPlayerBotDsTime(s) || GetPlayerBotDsGrade(s) < PLAYERBOT_DS_MIN_WORN_GRADE ||
					GetPlayerBotDsGrade(s) >= PLAYERBOT_DS_MYTH_GRADE || IsPlayerBotSidekickLockedItem(ch, s))
				continue;
			if (!pick || RankPlayerBotDs(ch, s) > RankPlayerBotDs(ch, pick))
				pick = s;
		}
		if (!pick || !PlayerBotEquipItem(ch, pick))
			return false;
		++s_kPlayerBotAlchemyStats.equipped;
		sys_log(0, "PLAYERBOT_ALCHEMY: wear interim pid=%u name=%s vnum=%u kind=%d", ch->GetPlayerID(), ch->GetName(),
				pick->GetVnum(), kind);
		return true;
	}

	// The best stone with time left of every kind into deck 0: of the rare
	// grade and over, and only once the kind has no refine left to do (the
	// Alchemist does it first) - but a mythic stone goes on as it is.
	//
	// MT2009_PLUS_BOT_DS_KEEP_WORN_V1: taking a stone off may destroy it
	// (PullOutPlayerBotDs). A worn stone - expired or not, of any grade -
	// comes off only for a stone of the bag with time left that ranks
	// strictly higher (grade, step, strength, lines; time does not rank).
	// An expired one stays on until the Alchemist recharges it ("Dobrych
	// kamieni nie powinien sciagac nigdy ... tylko wtedy, gdy ma lepszy
	// gotowy do wstawienia na jego miejsce", the operator, 3 October 2026).
	// MT2009_PLUS_BOT_DS_CLEARLY_BETTER_V1 (EquipPlayerBotBestDragonSouls): grades over the worn stone that put a
	// stone on at once; counted (the census's "ds_clearly_better").
	const int PLAYERBOT_DS_CLEARLY_BETTER_GRADES = 2;
	unsigned int s_uPlayerBotDsClearlyBetter = 0;

	int EquipPlayerBotBestDragonSouls(LPCHARACTER ch)
	{
		int changed = 0;
		for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
		{
			LPITEM worn = GetPlayerBotWornDs(ch, kind);
			std::vector<LPITEM> stones;
			CollectPlayerBotDragonSouls(ch, stones, kind);
			LPITEM best = NULL;
			for (size_t i = 0; i < stones.size(); ++i)
				if (HasPlayerBotDsTime(stones[i]) && ScorePlayerBotDsWorth(ch, stones[i]) > 0 &&
						GetPlayerBotDsGrade(stones[i]) >= PLAYERBOT_DS_MIN_WORN_GRADE &&
						(!best || RankPlayerBotDs(ch, stones[i]) > RankPlayerBotDs(ch, best)))
					best = stones[i];
			// MT2009_PLUS_BOT_DS_YOHARA800_V1: a bulk alchemist's Mythic stone waits for the kind's work too (its
			// steps and beans; a pull-out keeps a Mythic stone 15% of the time) - but an empty slot does not wait
			// empty: PlacePlayerBotDsInterim.
			// MT2009_PLUS_BOT_DS_CLEARLY_BETTER_V1 (the owner, 3 November 2026: "Bot wczesniej zaklada Smoczy Kamien
			// lepszy o min. 2 klasy (zdjecie jak u gracza - stary moze sie zniszczyc)"): a stone of the bag at least
			// PLAYERBOT_DS_CLEARLY_BETTER_GRADES grades over the worn one goes on now - not after the kind's refine
			// work, not after the worn one's time ran out (an expired one is kept on only against a stone it matches).
			// The worn one comes off the player's way (PullOutPlayerBotDs: the engine's odds may destroy it).
			const bool clearlyBetter = best && worn &&
					(int)GetPlayerBotDsGrade(best) >= (int)GetPlayerBotDsGrade(worn) + PLAYERBOT_DS_CLEARLY_BETTER_GRADES &&
					!IsPlayerBotSidekickLockedItem(ch, worn);
			if (clearlyBetter)
				++s_uPlayerBotDsClearlyBetter;
			if (best && !clearlyBetter && (GetPlayerBotDsGrade(best) < PLAYERBOT_DS_MYTH_GRADE || IsPlayerBotDsBulk(ch)))
			{
				LPITEM a = NULL, b = NULL;
				if (FindPlayerBotDsRefine(ch, kind, a, b) != 0)	// PLAYERBOT_DS_WORK_NONE
				{
					if (!worn && IsPlayerBotDsBulk(ch) && PlacePlayerBotDsInterim(ch, kind, stones, a, b))
						++changed;
					continue;
				}
			}
			if (worn && !HasPlayerBotDsTime(worn) && (!best || RankPlayerBotDs(ch, worn) >= RankPlayerBotDs(ch, best)))
			{
				++s_kPlayerBotAlchemyStats.keptExpired;
				PlayerBotLogThrottled("ds_kept_expired", get_dword_time(),
						"PLAYERBOT_DS: kept expired pid=%u name=%s vnum=%u kind=%d gold=%lld (stays on, waits for an elixir)",
						ch->GetPlayerID(), ch->GetName(), worn->GetVnum(), kind, (long long)ch->GetGold());
				continue;
			}
			if (!best || (worn && RankPlayerBotDs(ch, worn) >= RankPlayerBotDs(ch, best)))
				continue;
			// A locked companion's stone stays (PullOutPlayerBotDs refuses).
			if (worn && IsPlayerBotSidekickLockedItem(ch, worn))
				continue;
			const DWORD oldVnum = worn ? worn->GetVnum() : 0;
			if (worn && !PullOutPlayerBotDs(ch, worn))
			{
				// Destroyed by the engine's odds: the slot is free for the
				// better stone; refused (no room): nothing changes.
				if (GetPlayerBotWornDs(ch, kind) != NULL)
					continue;
				worn = NULL;
			}
			if (PlayerBotEquipItem(ch, best))
			{
				++changed;
				++s_kPlayerBotAlchemyStats.equipped;
				sys_log(0, "PLAYERBOT_ALCHEMY: wear pid=%u name=%s vnum=%u kind=%d old=%u", ch->GetPlayerID(),
						ch->GetName(), best->GetVnum(), kind, oldVnum);
			}
			else if (worn && !worn->IsEquipped())
				PlayerBotEquipItem(ch, worn);
		}
		return changed;
	}

	int CountPlayerBotWornDs(LPCHARACTER ch, bool withTime)
	{
		int n = 0;
		for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
		{
			LPITEM worn = GetPlayerBotWornDs(ch, kind);
			if (worn && (!withTime || HasPlayerBotDsTime(worn)))
				++n;
		}
		return n;
	}

	// MT2009_PLUS_BOT_DS_EXTEND_V1: the deck is on only for a fight. It was
	// on everywhere outside the safe zones - fishing, mining, picking herbs,
	// travelling, standing at a counter - and a stone spends its day only
	// while the deck is on ("aby wylaczal alchemie, gdy np. lowi ryby albo
	// idzie do miasta", players, 3 October 2026). On at the first blow or
	// skill on a monster, a metin, a boss or a player
	// (state.dwLastCombatActionTime, set by every attack path), off a minute
	// after the last one, at once in a safe zone, at a counter, in a trade or
	// fishing. The engine has no switch cooldown (do_dragon_soul), but every
	// switch writes an item log per stone: PLAYERBOT_DS_DECK_MIN_TOGGLE_MS
	// keeps a fight with pauses from flickering it.
	const DWORD PLAYERBOT_DS_DECK_TICK_MS = 2000;
	const DWORD PLAYERBOT_DS_COMBAT_START_MS = 5000;
	const DWORD PLAYERBOT_DS_COMBAT_HOLD_MS = 60000;
	const DWORD PLAYERBOT_DS_DECK_MIN_TOGGLE_MS = 20000;

	// MT2009_PLUS_SIDEKICK_ALCHEMY_ACTIVE_V1 ("Jesli towarzysz ma dana
	// alchemie i walczy, to ma miec ja wlaczona - teraz nie wlacza alchemii
	// ani jej nie przedluza", the owner, 6 October 2026). A companion is no
	// alchemy user (IsPlayerBotAlchemyUser: it never buys, opens, refines or
	// swaps a stone), so nothing ever recharged its stones - once a day of
	// deck was spent they stayed dead and the deck never went on again - and
	// a stone its owner handed into its Alchemy sat there. The companion's
	// own small pass, on the bots' local clock: qualified once it has a
	// stone; an owner's stone from its Alchemy onto a free place of the deck
	// it uses (never one its owner took off, never by pulling another out);
	// and a worn stone of that deck under PLAYERBOT_DS_ELIXIR_BELOW_SEC
	// recharged with a time elixir of its bag (the Alchemist's (D), any
	// USE_TIME_CHARGE_FIX/PER one) - since MT2009_PLUS_SIDEKICK_DS_ELIXIRS_V2
	// any of its bag, not only the ones its owner gave it, the equipment lock
	// or not; the owner's drop it holds for the owner is never spent. It buys
	// none: the elixir is the Alchemist's, a counter no companion errand
	// visits.

	// The deck a companion's stones are on: the one with more stones with
	// time left (withTime) or worn at all; the first on a tie.
	int GetPlayerBotSidekickDsDeck(LPCHARACTER ch, bool withTime)
	{
		int count[DRAGON_SOUL_DECK_MAX_NUM] = {};
		for (int deck = 0; deck < DRAGON_SOUL_DECK_MAX_NUM; ++deck)
			for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
			{
				LPITEM worn = ch->GetItem(TItemPos(INVENTORY,
						(WORD)((int)DRAGON_SOUL_EQUIP_SLOT_START + deck * (int)DS_SLOT_MAX + kind)));
				if (worn && (!withTime || HasPlayerBotDsTime(worn)))
					++count[deck];
			}
		int best = DRAGON_SOUL_DECK_0;
		for (int deck = 1; deck < DRAGON_SOUL_DECK_MAX_NUM; ++deck)
			if (count[deck] > count[best])
				best = deck;
		return best;
	}

	// MT2009_PLUS_SIDEKICK_DS_ELIXIRS_V2 ("Towarzyszka nie chce uzywac
	// eliksirow co przedluzaja alchemie. Ma kilka w ekwipunku ... uzyla tylko
	// jednego, a ma caly krag alchemii", the owner, 8 October 2026). Two
	// gates held the rest of the bag back. Only an elixir its owner handed
	// over the trade window or the bag window was ever spent: everything else
	// counted as kept for its owner (IsPlayerBotSidekickKeptForOwner) - the
	// elixirs it looted on its own while let off the leash, the ones its box
	// sweep brought back from its storekeeper, any that came another way -
	// and they lay there for good. And the pass took one stone at a time and
	// stuck to the first elixir of the bag: one the engine refused (a Dragon
	// Heart with nothing in it, a stone already full) was tried again on
	// every pass and the next one in the bag never came up. Now every time
	// elixir of its bag is the deck's - only the owner's drop it holds for the
	// owner (IsPlayerBotSidekickHeld), a locked one and one in a trade stay -
	// and one pass recharges every worn stone of the deck in use that is
	// under PLAYERBOT_DS_ELIXIR_BELOW_SEC or out of time, the emptiest first,
	// with an elixir each (another while one still leaves it under the mark),
	// past any elixir the engine turned down.
	const int PLAYERBOT_SIDEKICK_DS_ELIXIRS_PER_PASS = 4;	// the engine's 5 uses in 500 ms, one for a potion

	bool IsPlayerBotSidekickDsElixir(LPCHARACTER ch, LPITEM item)
	{
		return item && item->GetType() == ITEM_USE &&
				(item->GetSubType() == USE_TIME_CHARGE_FIX || item->GetSubType() == USE_TIME_CHARGE_PER) &&
				!item->isLocked() && !item->IsExchanging() && !IsPlayerBotSidekickHeld(ch, item);
	}

	// The first time elixir of its bag that this pass has not seen the engine
	// refuse.
	int FindPlayerBotSidekickDsElixir(LPCHARACTER ch, const std::set<DWORD>& refused)
	{
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && IsPlayerBotSidekickDsElixir(ch, item) &&
					refused.find(item->GetID()) == refused.end())
				return cell;
		}
		return -1;
	}

	void ManagePlayerBotSidekickDs(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (dwNow < state.dwNextDsLocalTime || ch->IsDead() || ch->GetExchange() || !ch->IsItemLoaded())
			return;
		state.dwNextDsLocalTime = dwNow + PLAYERBOT_ALCHEMY_LOCAL_MS;
		std::vector<LPITEM> bag;
		CollectPlayerBotDragonSouls(ch, bag);
		const int deck = ch->DragonSoul_GetActiveDeck() >= 0 ? ch->DragonSoul_GetActiveDeck()
				: GetPlayerBotSidekickDsDeck(ch, false);
		const int base = (int)DRAGON_SOUL_EQUIP_SLOT_START + deck * (int)DS_SLOT_MAX;
		bool any = !bag.empty();
		for (int i = 0; i < (int)DS_SLOT_MAX * (int)DRAGON_SOUL_DECK_MAX_NUM && !any; ++i)
			any = ch->GetItem(TItemPos(INVENTORY, (WORD)((int)DRAGON_SOUL_EQUIP_SLOT_START + i))) != NULL;
		if (!any)
			return;
		EnsurePlayerBotAlchemyQualified(ch);
		// The owner's stones of its Alchemy onto the deck's free places - the
		// best of a kind with time left; EquipItem refuses within a second
		// and a half of a blow, as for the bots' own pass.
		if (!bag.empty() && ch->GetVictim() == NULL &&
				dwNow - ch->GetLastAttackTime() > PLAYERBOT_EQUIPMENT_COMBAT_DELAY &&
				(state.dwLastBotSkillTime == 0 || dwNow - state.dwLastBotSkillTime > PLAYERBOT_EQUIPMENT_COMBAT_DELAY))
			for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
			{
				const int wear = WEAR_MAX_NUM + deck * DS_SLOT_MAX + kind;
				if (ch->GetItem(TItemPos(INVENTORY, (WORD)(base + kind))))
					continue;
				LPITEM best = NULL;
				for (size_t i = 0; i < bag.size(); ++i)
				{
					LPITEM s = bag[i];
					if (s->GetSubType() != kind || !HasPlayerBotDsTime(s) || !IsPlayerBotSidekickGift(ch, s) ||
							IsPlayerBotSidekickHeld(ch, s) || IsPlayerBotSidekickUnwanted(ch, s) ||
							s->FindEquipCell(ch, wear) != wear)
						continue;
					if (!best || RankPlayerBotDs(ch, s) > RankPlayerBotDs(ch, best))
						best = s;
				}
				if (best && PlayerBotEquipItem(ch, best, wear) && best->IsEquipped())
					sys_log(0, "PLAYERBOT_SIDEKICK: ds worn pid=%u name=%s vnum=%u deck=%d kind=%d", ch->GetPlayerID(),
							ch->GetName(), best->GetVnum(), deck + 1, kind);
			}
		// MT2009_PLUS_SIDEKICK_DS_ELIXIRS_V2: every stone of the deck in use
		// that runs low or is out, the emptiest first.
		std::vector<LPITEM> low;
		for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
		{
			LPITEM stone = ch->GetItem(TItemPos(INVENTORY, (WORD)(base + kind)));
			if (stone && stone->IsDragonSoul() && stone->GetSocket(ITEM_SOCKET_REMAIN_SEC) < PLAYERBOT_DS_ELIXIR_BELOW_SEC &&
					!IsPlayerBotSidekickHeld(ch, stone))
				low.push_back(stone);
		}
		if (low.empty())
			return;
		for (size_t i = 1; i < low.size(); ++i)
			for (size_t j = i; j > 0 && low[j]->GetSocket(ITEM_SOCKET_REMAIN_SEC) < low[j - 1]->GetSocket(ITEM_SOCKET_REMAIN_SEC); --j)
				std::swap(low[j], low[j - 1]);
		std::set<DWORD> refused;
		int uses = 0;
		size_t done = 0;
		for (size_t i = 0; i < low.size() && uses < PLAYERBOT_SIDEKICK_DS_ELIXIRS_PER_PASS; )
		{
			LPITEM stone = low[i];
			const int cell = FindPlayerBotSidekickDsElixir(ch, refused);
			if (cell < 0)
			{
				PlayerBotLogThrottled("sidekick_ds_no_elixir", dwNow,
						"PLAYERBOT_SIDEKICK: ds low, no elixir pid=%u name=%s vnum=%u sec=%ld low=%u done=%u",
						ch->GetPlayerID(), ch->GetName(), stone->GetVnum(), (long)stone->GetSocket(ITEM_SOCKET_REMAIN_SEC),
						(unsigned int)low.size(), (unsigned int)done);
				return;
			}
			LPITEM elixir = ch->GetInventoryItem((WORD)cell);
			const DWORD elixirId = elixir->GetID();
			const DWORD elixirVnum = elixir->GetVnum();
			const long before = (long)stone->GetSocket(ITEM_SOCKET_REMAIN_SEC);
			const bool ok = ch->UseItem(TItemPos(INVENTORY, (WORD)cell), TItemPos(stone->GetWindow(), stone->GetCell()));
			const long after = (long)stone->GetSocket(ITEM_SOCKET_REMAIN_SEC);
			++uses;
			// An expired stone of the deck that is on was left off by the deck's
			// switch: on with its new time.
			if (ok && after > 0 && ch->DragonSoul_GetActiveDeck() == deck && !DSManager::instance().IsActiveDragonSoul(stone))
				DSManager::instance().ActivateDragonSoul(stone);
			if (ok && after > before)
				++s_kPlayerBotAlchemyStats.recharged;
			sys_log(0, "PLAYERBOT_SIDEKICK: ds recharged pid=%u name=%s vnum=%u elixir=%u ok=%d sec=%ld->%ld deck=%d "
					"stone=%u/%u", ch->GetPlayerID(), ch->GetName(), stone->GetVnum(), elixirVnum, ok ? 1 : 0, before, after,
					deck + 1, (unsigned int)(i + 1), (unsigned int)low.size());
			if (!ok || after <= before)
			{
				// Refused: the next elixir of the bag for the same stone - unless
				// the stone itself is full (the engine refuses every elixir then).
				refused.insert(elixirId);
				if (after >= (long)DSManager::instance().GetDuration(stone))
					++i;
				continue;
			}
			// Still under the mark (a small (M) on an empty stone): another.
			if (after >= PLAYERBOT_DS_ELIXIR_BELOW_SEC)
			{
				++done;
				++i;
			}
		}
	}

	void ManagePlayerBotDsDeckTick(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || dwNow < state.dwNextDsDeckTime)
			return;
		state.dwNextDsDeckTime = dwNow + PLAYERBOT_DS_DECK_TICK_MS;
		// MT2009_PLUS_SIDEKICK_ALCHEMY_ACTIVE_V1: a companion's stones put on
		// and recharged (above), before the deck asks for its qualification.
		const bool sidekick = IsPlayerBotSidekickPID(ch->GetPlayerID());
		if (sidekick && !ArePlayerBotAlchemyOff())
			ManagePlayerBotSidekickDs(ch, state, dwNow);
		// The Alchemist's visit switches it off itself (ManagePlayerBotAlchemy).
		if (ch->IsDead() || state.bVisitingDsAlchemist || !ch->DragonSoul_IsQualified())
			return;
		const bool active = ch->DragonSoul_GetActiveDeck() >= 0;
		// MT2009_PLUS_SIDEKICK_PANELS_V1: a companion is no alchemy user (it
		// never buys, opens, refines or swaps a stone), but the stones its
		// owner put on it in the companion's Alchemy window switch on for its
		// fights like everybody's.
		if (!active && !IsPlayerBotAlchemyUser(ch) &&
				!(IsPlayerBotSidekickPID(ch->GetPlayerID()) && !ArePlayerBotAlchemyOff()))
			return;
		DWORD last = state.dwLastCombatActionTime;
		// MT2009_PLUS_SIDEKICK_ALCHEMY_ACTIVE_V1: a companion fights beside its
		// owner - a Shaman's buffs and heals, a passive stance, the walk to the
		// foe never stamped the clock above, and its deck stayed off through
		// most of its owner's hunt. Its fight, or its owner's it saw, counts.
		if (sidekick)
		{
			const DWORD seen = GetPlayerBotSidekickFightSeenAt(ch->GetPlayerID());
			if (seen != 0 && dwNow >= seen && (last == 0 || seen - last < 0x80000000U))
				last = seen;
		}
		// MT2009_PLUS_BOT_ELEMENT_PET_V1 (deck): a Yohara bot with a hunt element holds the deck on while it is on a Sung
		// Ma map. The clock above is stamped by the bot's own blow or skill only, never by a blow taken, and the tick is
		// 2 s - the map's monsters come at the bot first, and their opening hits (after a walk, or within the 20 s after a
		// switch-off) fell on a deck that was off: the hunt kind's resistance line (the global table's 2nd basic line)
		// was not there when the damage came. On the map the bot is in or near a fight all the time anyway.
		const bool elementMap = GetPlayerBotHuntElement(ch) > 0 && GetPlayerBotYoharaElementSlot(ch->GetMapIndex()) >= 0;
		const bool fightingNow = elementMap || (last != 0 && dwNow - last < PLAYERBOT_DS_COMBAT_START_MS);
		const bool foughtLately = elementMap || (last != 0 && dwNow - last < PLAYERBOT_DS_COMBAT_HOLD_MS);
		const char* quiet = NULL;
		if (IsPlayerBotSafeZone(ch->GetMapIndex(), ch->GetX(), ch->GetY()))
			quiet = "safe_zone";
		else if (ch->GetMyShop())
			quiet = "counter";
		else if (ch->GetExchange())
			quiet = "trade";
		else if (state.bFishingSession)
			quiet = "fishing";
		const bool settled = state.dwLastDsDeckToggle == 0 || dwNow - state.dwLastDsDeckToggle >= PLAYERBOT_DS_DECK_MIN_TOGGLE_MS;
		if (!active)
		{
			// MT2009_PLUS_SIDEKICK_PANELS_V1: a companion's owner may have put
			// its stones on the second deck: the deck with more of them goes on.
			int deck = DRAGON_SOUL_DECK_0;
			int live = CountPlayerBotWornDs(ch, true);
			if (sidekick)
			{
				int second = 0;
				for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
				{
					LPITEM worn = ch->GetItem(TItemPos(INVENTORY, (int)DRAGON_SOUL_EQUIP_SLOT_START + (int)DS_SLOT_MAX + kind));
					if (worn && HasPlayerBotDsTime(worn))
						++second;
				}
				if (second > live)
				{
					deck = DRAGON_SOUL_DECK_1;
					live = second;
				}
			}
			if (!fightingNow || quiet || !settled || live == 0)
				return;
			if (!ch->DragonSoul_ActivateDeck(deck))
				return;
			state.dwLastDsDeckToggle = dwNow;
			++s_kPlayerBotAlchemyStats.deckOn;
			PlayerBotLogThrottled("ds_deck_on", dwNow, "PLAYERBOT_DS: deck on pid=%u name=%s lv=%d map=%ld worn_live=%d why=%s",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), ch->GetMapIndex(), CountPlayerBotWornDs(ch, true),
					elementMap ? "element_map" : "fight");
			return;
		}
		if (!quiet && foughtLately)
			return;
		if (!quiet && !settled)
			return;
		ch->DragonSoul_DeactivateAll();
		state.dwLastDsDeckToggle = dwNow;
		++s_kPlayerBotAlchemyStats.deckOff;
		PlayerBotLogThrottled("ds_deck_off", dwNow, "PLAYERBOT_DS: deck off pid=%u name=%s lv=%d map=%ld why=%s idle_ms=%u",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), ch->GetMapIndex(), quiet ? quiet : "no_fight",
				last ? (unsigned int)(dwNow - last) : 0U);
	}

	// ------------------------------------------------------------ at the Alchemist

	bool PlayerBotDsRefineGrid(TItemPos (&grid)[DRAGON_SOUL_REFINE_GRID_SIZE], LPITEM a, LPITEM b)
	{
		for (int i = 0; i < DRAGON_SOUL_REFINE_GRID_SIZE; ++i)
			grid[i] = NPOS;
		if (!a || !b)
			return false;
		grid[0] = TItemPos(a->GetWindow(), a->GetCell());
		grid[1] = TItemPos(b->GetWindow(), b->GetCell());
		return true;
	}

	enum { PLAYERBOT_DS_WORK_NONE, PLAYERBOT_DS_WORK_GRADE, PLAYERBOT_DS_WORK_STEP, PLAYERBOT_DS_WORK_STRENGTH };

	// The next refine for one kind: two stones of a grade under the target;
	// else two of the target grade and a step under the target; else the
	// best one's strength with a bean. The two cheapest go.
	// MT2009_PLUS_BOT_DS_KEEP_WORN_V1: never the worn one - the refine
	// window wants it pulled out, which may destroy it (PullOutPlayerBotDs);
	// a better stone made in the bag replaces it as a strict upgrade.
	// MT2009_PLUS_BOT_DS_YOHARA800_V1: a bulk alchemist's final stone of a kind - the one the beans go into and that
	// goes on: the most power it can reach (the WeightTables' percent at its strength cap - a Legendary Highest,
	// cap +6 = 120, before a Mythic Mid, cap +4 = 80), then grade and step, then the Yohara lines, then the strength
	// it already has. So the beans go to the stone the kind will wear (EquipPlayerBotBestDragonSouls ranks by the
	// power it has).
	long long GetPlayerBotDsFinalKey(LPCHARACTER ch, LPITEM item)
	{
		const BYTE grade = GetPlayerBotDsGrade(item), step = GetPlayerBotDsStep(item);
		return (long long)GetPlayerBotDsWeight(grade, step, GetPlayerBotDsStrengthCap(grade, step)) * 100000000000LL +
				((long long)grade * 10 + step) * 1000000000LL +
				std::min<long long>(std::max<long long>(ScorePlayerBotDsYoharaLines(ch, item), 0), 999999) * 100 +
				GetPlayerBotDsStrength(item);
	}

	// MT2009_PLUS_BOT_DS_ALCHEMY_GUIDE_V1: the beans of the bag - green, blue, pink - and the one a strength refine
	// from this strength takes: the best (pink, then blue) for +3 and over, where their odds help most (+3->+4 50/55/60,
	// +4->+5 30/33/40, +5->+6 20/22/30), the plain green under it (100/80/70 - all but the same), whatever there is
	// else. -1: none.
	int CountPlayerBotDsBeans(LPCHARACTER ch)
	{
		return ch ? (int)ch->CountSpecifyItem(PLAYERBOT_DS_GREEN_BEAN_VNUM) + (int)ch->CountSpecifyItem(PLAYERBOT_DS_BLUE_BEAN_VNUM) +
				(int)ch->CountSpecifyItem(PLAYERBOT_DS_PINK_BEAN_VNUM) : 0;
	}

	int PickPlayerBotDsBean(LPCHARACTER ch, BYTE strength)
	{
		static const DWORD s_high[3] = { PLAYERBOT_DS_PINK_BEAN_VNUM, PLAYERBOT_DS_BLUE_BEAN_VNUM, PLAYERBOT_DS_GREEN_BEAN_VNUM };
		static const DWORD s_low[3] = { PLAYERBOT_DS_GREEN_BEAN_VNUM, PLAYERBOT_DS_BLUE_BEAN_VNUM, PLAYERBOT_DS_PINK_BEAN_VNUM };
		const DWORD* order = strength >= 3 ? s_high : s_low;
		// MT2009_PLUS_BOT_EKW_PAGES_V1: a second look after the beans came back from the extra inventory
		for (int pass = 0; pass < 2; ++pass)
		{
			for (int o = 0; o < 3; ++o)
				for (WORD cell = 0; ch && cell < PLAYERBOT_BAG_CELLS; ++cell)
				{
					LPITEM item = ch->GetInventoryItem(cell);
					if (item && item->GetCell() == cell && item->GetVnum() == order[o] && !item->isLocked())
						return cell;
				}
			bool fetched = false;
			for (int o = 0; pass == 0 && o < 3 && !fetched; ++o)
				fetched = PlayerBotEkwFetchVnum(ch, order[o]);
			if (!fetched)
				break;
		}
		return -1;
	}

	// MT2009_PLUS_BOT_DS_ALCHEMY_GUIDE_V1: a failed strength refine takes the stone a level down (DoRefineStrength;
	// the guide's "Porazka: poziom -1"). With beans enough to climb back (the expected beans of the step, green
	// odds: 1, 1.5, 2.1, 4.1, 12.8, 56.3 from +0..+5) the try pays; with fewer it is a single throw, made only while
	// its expected power is not negative: p x (the level's gain) >= (1 - p) x (the level's loss) in the WeightTables
	// percent - e.g. a Mythic Highest +5 with the last green bean: 0.2 x 25 < 0.8 x 15, kept at +5.
	bool IsPlayerBotDsStrengthWorthTrying(BYTE grade, BYTE step, BYTE strength, int beans, bool pinkOrBlue)
	{
		static const double s_expected[6] = { 1.0, 1.5, 2.07, 4.07, 12.83, 56.3 };
		if (strength >= 6)
			return false;
		if (strength == 0 || beans >= (int)(s_expected[strength] + 0.999))
			return true;
		const double p = PLAYERBOT_DS_STRENGTH_PCT[strength] + (pinkOrBlue ? 0.1 : 0.0);
		const int gain = GetPlayerBotDsWeight(grade, step, strength + 1) - GetPlayerBotDsWeight(grade, step, strength);
		const int loss = GetPlayerBotDsWeight(grade, step, strength) - GetPlayerBotDsWeight(grade, step, strength - 1);
		return p * gain >= (1.0 - p) * loss;
	}

	// MT2009_PLUS_BOT_DS_YOHARA800_V1: the next refine of a kind for a bulk alchemist (the comment at
	// PLAYERBOT_COR_LEGENDARY_VNUM): grade pairs up to Mythic (where the next grade's page has room), then the
	// Mythic step pairs from the highest down - none of the two once the kind has a Mythic Highest stone - then
	// the final stone's strength up to its cap with the beans of its bag (one bought only under the ordinary
	// user's strength target). Never the worn stone; the final stone only when it would beat the worn one.
	int FindPlayerBotDsRefineBulk(LPCHARACTER ch, int kind, LPITEM& a, LPITEM& b)
	{
		a = b = NULL;
		std::vector<LPITEM> stones;
		CollectPlayerBotDragonSouls(ch, stones, kind);
		for (size_t i = stones.size(); i-- > 0;)
			if (IsPlayerBotSidekickLockedItem(ch, stones[i]))
				stones.erase(stones.begin() + i);
		LPITEM worn = GetPlayerBotWornDs(ch, kind);
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch);
		bool done = IsPlayerBotDsMythHighest(worn);
		for (size_t i = 0; i < stones.size() && !done; ++i)
			done = IsPlayerBotDsMythHighest(stones[i]);
		if (!done)
		{
			for (BYTE grade = 0; grade < PLAYERBOT_DS_MYTH_GRADE; ++grade)
			{
				std::vector<LPITEM> pick;
				for (size_t i = 0; i < stones.size(); ++i)
					if (GetPlayerBotDsGrade(stones[i]) == grade)
						pick.push_back(stones[i]);
				// The fee, and the page a success fills (a failure gives one stone back into the page it took two from).
				if (pick.size() < 2 || spare < PLAYERBOT_DS_GRADE_FEES[grade] + PLAYERBOT_DS_REFINE_SPARE ||
						!PlayerBotDsPageHasRoom(ch, kind, grade + 1))
					continue;
				std::sort(pick.begin(), pick.end(), [&](LPITEM x, LPITEM y) { return RankPlayerBotDs(ch, x) < RankPlayerBotDs(ch, y); });
				a = pick[0];
				b = pick[1];
				return PLAYERBOT_DS_WORK_GRADE;
			}
			for (int step = 3; step >= 0; --step)
			{
				std::vector<LPITEM> pick;
				for (size_t i = 0; i < stones.size(); ++i)
					if (GetPlayerBotDsGrade(stones[i]) == PLAYERBOT_DS_MYTH_GRADE && GetPlayerBotDsStep(stones[i]) == step)
						pick.push_back(stones[i]);
				if (pick.size() < 2 || spare < PLAYERBOT_DS_STEP_FEES[step] + PLAYERBOT_DS_REFINE_SPARE)
					continue;
				std::sort(pick.begin(), pick.end(), [&](LPITEM x, LPITEM y) { return RankPlayerBotDs(ch, x) < RankPlayerBotDs(ch, y); });
				a = pick[0];
				b = pick[1];
				return PLAYERBOT_DS_WORK_STEP;
			}
		}
		LPITEM best = NULL;
		for (size_t i = 0; i < stones.size(); ++i)
			if (GetPlayerBotDsGrade(stones[i]) >= PLAYERBOT_DS_MIN_WORN_GRADE &&
					(!best || GetPlayerBotDsFinalKey(ch, stones[i]) > GetPlayerBotDsFinalKey(ch, best)))
				best = stones[i];
		if (!best)
			return PLAYERBOT_DS_WORK_NONE;
		const BYTE grade = GetPlayerBotDsGrade(best), step = GetPlayerBotDsStep(best), strength = GetPlayerBotDsStrength(best);
		// The worn stone stays unless this one, at its cap, beats it (a pull-out may destroy the worn one, and a
		// stone that will never go on gets no beans).
		if (worn && GetPlayerBotDsWeight(grade, step, GetPlayerBotDsStrengthCap(grade, step)) <= RankPlayerBotDs(ch, worn) / 10000000000LL)
			return PLAYERBOT_DS_WORK_NONE;
		if (strength >= GetPlayerBotDsStrengthCap(grade, step) || spare < 10000 + PLAYERBOT_DS_REFINE_SPARE)
			return PLAYERBOT_DS_WORK_NONE;
		// MT2009_PLUS_BOT_DS_ALCHEMY_GUIDE_V1: any bean of the bag, while the try pays (a bought one is no limit).
		const int beanCount = CountPlayerBotDsBeans(ch);
		const bool better = ch->CountSpecifyItem(PLAYERBOT_DS_PINK_BEAN_VNUM) + ch->CountSpecifyItem(PLAYERBOT_DS_BLUE_BEAN_VNUM) > 0;
		const bool beans = beanCount > 0 && IsPlayerBotDsStrengthWorthTrying(grade, step, strength, beanCount, better && strength >= 3);
		const bool buy = strength < GetPlayerBotDsTarget(ch).strength && spare >= PLAYERBOT_DS_BEAN_COST * 3;
		if (!beans && !buy)
			return PLAYERBOT_DS_WORK_NONE;
		a = best;
		return PLAYERBOT_DS_WORK_STRENGTH;
	}

	int FindPlayerBotDsRefine(LPCHARACTER ch, int kind, LPITEM& a, LPITEM& b)
	{
		a = b = NULL;
		if (IsPlayerBotDsBulk(ch))	// MT2009_PLUS_BOT_DS_YOHARA800_V1
			return FindPlayerBotDsRefineBulk(ch, kind, a, b);
		const TPlayerBotDsTarget t = GetPlayerBotDsTarget(ch);
		std::vector<LPITEM> stones;
		CollectPlayerBotDragonSouls(ch, stones, kind);
		LPITEM worn = NULL;
		// MT2009_PLUS_SIDEKICK_EQUIP_LOCK_V1: nothing a locked companion wears
		// or was given goes to the Alchemist.
		for (size_t i = stones.size(); i-- > 0;)
			if (IsPlayerBotSidekickLockedItem(ch, stones[i]))
				stones.erase(stones.begin() + i);
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch);
		for (BYTE grade = 0; grade < t.grade; ++grade)
		{
			std::vector<LPITEM> pick;
			for (size_t i = 0; i < stones.size(); ++i)
				if (GetPlayerBotDsGrade(stones[i]) == grade)
					pick.push_back(stones[i]);
			if (pick.size() < 2 || spare < PLAYERBOT_DS_GRADE_FEES[grade] + PLAYERBOT_DS_REFINE_SPARE)
				continue;
			std::sort(pick.begin(), pick.end(), [&](LPITEM x, LPITEM y) {
				return (x == worn ? 1 : 0) < (y == worn ? 1 : 0) ||
						((x == worn) == (y == worn) && RankPlayerBotDs(ch, x) < RankPlayerBotDs(ch, y)); });
			a = pick[0];
			b = pick[1];
			return PLAYERBOT_DS_WORK_GRADE;
		}
		// The steps: at the highest grade it has a pair of, the target's or
		// over it (a stone bought or made before).
		for (int grade = 5; grade >= (int)t.grade; --grade)
		for (BYTE step = 0; step < t.step; ++step)
		{
			// A mythic stone is stepped only by the end game.
			if (grade >= PLAYERBOT_DS_MYTH_GRADE && ch->GetLevel() < PLAYERBOT_DS_END_GAME_LEVEL)
				break;
			std::vector<LPITEM> pick;
			for (size_t i = 0; i < stones.size(); ++i)
				if (GetPlayerBotDsGrade(stones[i]) == grade && GetPlayerBotDsStep(stones[i]) == step)
					pick.push_back(stones[i]);
			if (pick.size() < 2 || spare < PLAYERBOT_DS_STEP_FEES[step] + PLAYERBOT_DS_REFINE_SPARE)
				continue;
			std::sort(pick.begin(), pick.end(), [&](LPITEM x, LPITEM y) {
				return (x == worn ? 1 : 0) < (y == worn ? 1 : 0) ||
						((x == worn) == (y == worn) && RankPlayerBotDs(ch, x) < RankPlayerBotDs(ch, y)); });
			a = pick[0];
			b = pick[1];
			return PLAYERBOT_DS_WORK_STEP;
		}
		LPITEM best = NULL;
		for (size_t i = 0; i < stones.size(); ++i)
			if (GetPlayerBotDsGrade(stones[i]) >= t.grade && GetPlayerBotDsStep(stones[i]) >= t.step &&
					(!best || RankPlayerBotDs(ch, stones[i]) > RankPlayerBotDs(ch, best)))
				best = stones[i];
		if (best && GetPlayerBotDsStrength(best) < t.strength && ScorePlayerBotDsLines(ch, best) > 0 &&
				spare >= PLAYERBOT_DS_BEAN_COST * 3)
		{
			a = best;
			return PLAYERBOT_DS_WORK_STRENGTH;
		}
		return PLAYERBOT_DS_WORK_NONE;
	}

	// MT2009_PLUS_BOT_DS_EXTEND_V1: the kind's stone, worn or in the bag
	// (GetPlayerBotDsRechargeTarget), not only the worn one.
	bool PlayerBotNeedsDsElixir(LPCHARACTER ch)
	{
		for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
			if (GetPlayerBotDsRechargeTarget(ch, kind))
				return true;
		return false;
	}

	bool HasPlayerBotAlchemistWork(LPCHARACTER ch)
	{
		if (PlayerBotNeedsDsElixir(ch))
			return true;
		for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
		{
			LPITEM a = NULL, b = NULL;
			if (FindPlayerBotDsRefine(ch, kind, a, b) != PLAYERBOT_DS_WORK_NONE)
				return true;
		}
		return false;
	}

	// The shop's own price (item_proto gold), the way a player pays it.
	LPITEM BuyPlayerBotAlchemistItem(LPCHARACTER ch, DWORD vnum)
	{
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		if (!proto || proto->dwGold == 0 || (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) < (long long)proto->dwGold ||
				ch->GetEmptyInventory(1) < 0)
			return NULL;
		PlayerBotChangeGold(ch, -(long long)proto->dwGold);
		LPITEM item = ch->AutoGiveItem(vnum, 1, -1, false);
		if (vnum == PLAYERBOT_DS_TIME_ELIXIR_VNUM)
			++s_kPlayerBotAlchemyStats.elixirs;
		else if (vnum == PLAYERBOT_DS_GREEN_BEAN_VNUM)
			++s_kPlayerBotAlchemyStats.beans;
		return item;
	}

	int FindPlayerBotBagItem(LPCHARACTER ch, DWORD vnum)
	{
		// MT2009_PLUS_BOT_EKWIPUNEK_V1: a second look after the kind came back from the extra inventory
		for (int pass = 0; pass < 2; ++pass)
		{
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				if (item && item->GetCell() == cell && item->GetVnum() == vnum && !item->isLocked())
					return cell;
			}
			if (pass == 0 && !PlayerBotEkwFetchVnum(ch, vnum))
				break;
		}
		return -1;
	}

	// MT2009_PLUS_BOT_DS_YOHARA800_V1: the stones of one vnum in a kind's pages of the alchemy bag.
	int CountPlayerBotDsVnum(LPCHARACTER ch, int kind, DWORD vnum)
	{
		std::vector<LPITEM> stones;
		CollectPlayerBotDragonSouls(ch, stones, kind);
		int n = 0;
		for (size_t i = 0; i < stones.size(); ++i)
			if (stones[i]->GetVnum() == vnum)
				++n;
		return n;
	}

	// MT2009_PLUS_BOT_DS_ALCHEMY_GUIDE_V1: the guide's "Eliksir Czasu z kamienia Szczypcami Czasu". The Alchemist's
	// Tongs of Time (100200, 500 000) on a stone of the bag turn it into a Dragon Heart (DSManager::ExtractDragonHeart,
	// DragonHeartExtTables): a Legendary or Mythic stone always gives one of 100% - a whole day of the stone it is used
	// on (USE_TIME_CHARGE_PER, up to the stone's full duration), against the Time Elixir (D)'s 30 000 s for
	// 5 000 000. MT2009_PLUS_BOT_DS_TONGS_WEAK_V1 (the owner, 27.10.2026): the tongs go on the weakest stones only -
	// Zwykly / Blyszczacy (grade 0-1), of a kind with no refine left to do, not the kind's stone
	// (GetPlayerBotDsIntended); never a Rare or better - a Legendary or Mythic stone is worth more than the
	// 5 000 000 elixir. With no such stone the bot buys the elixir. The worst spare goes first.
	// Returns the bag cell of a Dragon Heart, made now if need be, or -1.
	int MakePlayerBotDragonHeart(LPCHARACTER ch)
	{
		int heart = FindPlayerBotBagItem(ch, PLAYERBOT_DS_DRAGON_HEART_VNUM);
		if (heart >= 0 || !IsPlayerBotDsBulk(ch) || ch->GetEmptyInventory(1) < 0)
			return heart;
		LPITEM spare = NULL;
		for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
		{
			LPITEM a = NULL, b = NULL;
			if (FindPlayerBotDsRefine(ch, kind, a, b) != PLAYERBOT_DS_WORK_NONE)
				continue;
			LPITEM intended = GetPlayerBotDsIntended(ch, kind);
			std::vector<LPITEM> stones;
			CollectPlayerBotDragonSouls(ch, stones, kind);
			for (size_t i = 0; i < stones.size(); ++i)
				if (stones[i] != intended && GetPlayerBotDsGrade(stones[i]) <= 1 && !IsPlayerBotSidekickLockedItem(ch, stones[i]) &&
						(!spare || RankPlayerBotDs(ch, stones[i]) < RankPlayerBotDs(ch, spare)))
					spare = stones[i];
		}
		if (!spare)
			return -1;
		int tongs = FindPlayerBotBagItem(ch, PLAYERBOT_DS_TIME_TONGS_VNUM);
		if (tongs < 0 && BuyPlayerBotAlchemistItem(ch, PLAYERBOT_DS_TIME_TONGS_VNUM))
			tongs = FindPlayerBotBagItem(ch, PLAYERBOT_DS_TIME_TONGS_VNUM);
		if (tongs < 0)
			return -1;
		const DWORD spareVnum = spare->GetVnum();
		const bool ok = ch->UseItem(TItemPos(INVENTORY, (WORD)tongs), TItemPos(spare->GetWindow(), spare->GetCell()));
		heart = FindPlayerBotBagItem(ch, PLAYERBOT_DS_DRAGON_HEART_VNUM);
		LPITEM h = heart >= 0 ? ch->GetInventoryItem((WORD)heart) : NULL;
		sys_log(0, "PLAYERBOT_ALCHEMY: dragon heart pid=%u name=%s from=%u ok=%d charge=%ld gold=%lld", ch->GetPlayerID(),
				ch->GetName(), spareVnum, ok ? 1 : 0, h ? (long)h->GetSocket(ITEM_SOCKET_CHARGING_AMOUNT_IDX) : 0L,
				(long long)ch->GetGold());
		return heart;
	}

	// One step at the Alchemist: an elixir for a stone running out, else one
	// refine. True when something was done.
	bool DoPlayerBotAlchemistStep(LPCHARACTER ch)
	{
		for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
		{
			// MT2009_PLUS_BOT_DS_EXTEND_V1: the kind's stone, worn or in the bag.
			LPITEM stone = GetPlayerBotDsRechargeTarget(ch, kind);
			if (!stone)
				continue;
			// MT2009_PLUS_BOT_DS_ALCHEMY_GUIDE_V1: a Dragon Heart from a spare stone first (a bulk alchemist).
			int cell = MakePlayerBotDragonHeart(ch);
			if (cell < 0)
				cell = FindPlayerBotBagItem(ch, PLAYERBOT_DS_TIME_ELIXIR_VNUM);
			if (cell < 0 && BuyPlayerBotAlchemistItem(ch, PLAYERBOT_DS_TIME_ELIXIR_VNUM))
				cell = FindPlayerBotBagItem(ch, PLAYERBOT_DS_TIME_ELIXIR_VNUM);
			if (cell < 0)
				return false;
			const long before = stone->GetSocket(ITEM_SOCKET_REMAIN_SEC);
			const bool equipped = stone->IsEquipped();
			const bool ok = ch->UseItem(TItemPos(INVENTORY, (WORD)cell), TItemPos(stone->GetWindow(), stone->GetCell()));
			const long after = (long)stone->GetSocket(ITEM_SOCKET_REMAIN_SEC);
			sys_log(0, "PLAYERBOT_ALCHEMY: elixir pid=%u name=%s vnum=%u ok=%d sec=%ld->%ld gold=%lld", ch->GetPlayerID(),
					ch->GetName(), stone->GetVnum(), ok ? 1 : 0, before, after, (long long)ch->GetGold());
			if (ok && after > before)
			{
				++s_kPlayerBotAlchemyStats.recharged;
				sys_log(0, "PLAYERBOT_DS: recharged pid=%u name=%s lv=%d vnum=%u kind=%d worn=%d sec=%ld->%ld gold=%lld",
						ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), stone->GetVnum(), kind, equipped ? 1 : 0,
						before, after, (long long)ch->GetGold());
			}
			return ok;
		}
		// MT2009_PLUS_BOT_DS_YOHARA800_V1: a bulk alchemist does any kind's grade or step work first, then spreads
		// its beans - the kind whose final stone has the lowest strength, the better Yohara lines on a tie.
		// MT2009_PLUS_BOT_ELEMENT_RESIST_V2: the kind whose stone carries the hunt element's resistance (its basic line -
		// Diament ice, Rubin fire, Jadeit wind, Szafir earth, Granat lightning, Onyks dark) goes first: its grades,
		// steps and beans before any other kind's (pass 0), the rest as before (pass 1).
		const bool bulk = IsPlayerBotDsBulk(ch);
		int chosenKind = -1, chosenWork = PLAYERBOT_DS_WORK_NONE;
		LPITEM chosenA = NULL, chosenB = NULL;
		for (int pass = bulk && GetPlayerBotHuntElement(ch) > 0 ? 0 : 1; pass < 2 && chosenKind < 0; ++pass)
		for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
		{
			LPITEM a = NULL, b = NULL;
			const int work = FindPlayerBotDsRefine(ch, kind, a, b);
			if (work == PLAYERBOT_DS_WORK_NONE)
				continue;
			if (pass == 0 && !IsPlayerBotDsHuntKindStone(ch, a))
				continue;
			if (!bulk || work != PLAYERBOT_DS_WORK_STRENGTH)
			{
				chosenKind = kind; chosenWork = work; chosenA = a; chosenB = b;
				break;
			}
			if (chosenKind < 0 || GetPlayerBotDsStrength(a) < GetPlayerBotDsStrength(chosenA) ||
					(GetPlayerBotDsStrength(a) == GetPlayerBotDsStrength(chosenA) &&
					 ScorePlayerBotDsYoharaLines(ch, a) > ScorePlayerBotDsYoharaLines(ch, chosenA)))
			{
				chosenKind = kind; chosenWork = work; chosenA = a; chosenB = b;
			}
		}
		if (chosenKind >= 0)
		{
			const int kind = chosenKind;
			const int work = chosenWork;
			LPITEM a = chosenA, b = chosenB;
			const BYTE gradeA = GetPlayerBotDsGrade(a), stepA = GetPlayerBotDsStep(a), strengthA = GetPlayerBotDsStrength(a);
			// A strength refine returns true either way: whether it took is the next strength's count going up.
			const int upBefore = work == PLAYERBOT_DS_WORK_STRENGTH ? CountPlayerBotDsVnum(ch, kind, a->GetVnum() + 10) : 0;
			// MT2009_PLUS_BOT_DS_KEEP_WORN_V1: a worn stone is never refine
			// material (FindPlayerBotDsRefine); nothing is pulled out here.
			if (a->IsEquipped() || (b && b->IsEquipped()))
				return false;
			TItemPos grid[DRAGON_SOUL_REFINE_GRID_SIZE];
			const DWORD vnumA = a->GetVnum();
			const long long goldBefore = ch->GetGold();
			if (work == PLAYERBOT_DS_WORK_STRENGTH)
			{
				// MT2009_PLUS_BOT_DS_ALCHEMY_GUIDE_V1: a bulk alchemist's best bean for the level.
				int bean = bulk ? PickPlayerBotDsBean(ch, strengthA) : FindPlayerBotBagItem(ch, PLAYERBOT_DS_GREEN_BEAN_VNUM);
				if (bean < 0 && BuyPlayerBotAlchemistItem(ch, PLAYERBOT_DS_GREEN_BEAN_VNUM))
					bean = FindPlayerBotBagItem(ch, PLAYERBOT_DS_GREEN_BEAN_VNUM);
				if (bean < 0)
					return false;
				PlayerBotDsRefineGrid(grid, a, ch->GetInventoryItem((WORD)bean));
			}
			else
				PlayerBotDsRefineGrid(grid, a, b);
			ch->DragonSoul_RefineWindow_Open(ch);
			bool ok = false;
			if (work == PLAYERBOT_DS_WORK_GRADE)
				ok = DSManager::instance().DoRefineGrade(ch, grid);
			else if (work == PLAYERBOT_DS_WORK_STEP)
				ok = DSManager::instance().DoRefineStep(ch, grid);
			else
				ok = DSManager::instance().DoRefineStrength(ch, grid);
			ch->DragonSoul_RefineWindow_Close();
			const char* what = work == PLAYERBOT_DS_WORK_GRADE ? "grade" : work == PLAYERBOT_DS_WORK_STEP ? "step" : "strength";
			if (work == PLAYERBOT_DS_WORK_GRADE) ++s_kPlayerBotAlchemyStats.refinesGrade;
			else if (work == PLAYERBOT_DS_WORK_STEP) ++s_kPlayerBotAlchemyStats.refinesStep;
			else ++s_kPlayerBotAlchemyStats.refinesStrength;
			// MT2009_PLUS_BOT_DS_YOHARA800_V1: whether it took (a strength refine by the count above).
			const bool took = work == PLAYERBOT_DS_WORK_STRENGTH ? CountPlayerBotDsVnum(ch, kind, vnumA + 10) > upBefore : ok;
			if (!took)
				++s_kPlayerBotAlchemyStats.refineFails;
			if (bulk)
			{
				if (work == PLAYERBOT_DS_WORK_GRADE && took && gradeA + 1 == PLAYERBOT_DS_MYTH_GRADE)
					++s_kPlayerBotAlchemyStats.bulkMythMade;
				else if (work == PLAYERBOT_DS_WORK_STEP && took && gradeA == PLAYERBOT_DS_MYTH_GRADE && stepA == 3)
					++s_kPlayerBotAlchemyStats.bulkHighestMade;
				else if (work == PLAYERBOT_DS_WORK_STRENGTH)
				{
					++s_kPlayerBotAlchemyStats.bulkBeans;
					if (took && strengthA + 1 == GetPlayerBotDsStrengthCap(gradeA, stepA))
						++s_kPlayerBotAlchemyStats.bulkCapMade;
				}
			}
			sys_log(0, "PLAYERBOT_ALCHEMY: refine %s pid=%u name=%s lv=%d kind=%d vnum=%u done=%d took=%d paid=%lld bulk=%d", what,
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), kind, vnumA, ok ? 1 : 0, took ? 1 : 0,
					goldBefore - (long long)ch->GetGold(), bulk ? 1 : 0);
			return ok || goldBefore != (long long)ch->GetGold();
		}
		return false;
	}

	// MT2009_PLUS_BOT_DS_YOHARA800_V1: a bulk alchemist looks for the Alchemist's work more often.
	DWORD GetPlayerBotDsCheckDelay(LPCHARACTER ch)
	{
		return IsPlayerBotDsBulk(ch) ? (DWORD)number(PLAYERBOT_DS_BULK_CHECK_MIN_MS, PLAYERBOT_DS_BULK_CHECK_MAX_MS)
				: (DWORD)number(PLAYERBOT_ALCHEMY_CHECK_MIN_MS, PLAYERBOT_ALCHEMY_CHECK_MAX_MS);
	}

	void EndPlayerBotAlchemistVisit(TPlayerBotAIState& state, DWORD dwNow, LPCHARACTER ch = NULL)
	{
		state.bVisitingDsAlchemist = false;
		state.dwNextDsActionTime = 0;
		state.dwNextDsCheckTime = dwNow + GetPlayerBotDsCheckDelay(ch);
		ClearPlayerBotRoute(state, true);
	}

	// MT2009_PLUS_BOT_DS_YOHARA800_V1: the Alchemist of a map - a first village's, or Dongan's for the Yohara maps.
	// Dongan's for a bulk alchemist only: an ordinary user keeps the first villages' Alchemists, as before.
	bool GetPlayerBotDsAlchemist(LPCHARACTER ch, long mapIndex, playerbot_empire_rules::TPoint& out)
	{
		if (playerbot_empire_rules::GetAlchemist(mapIndex, out))
			return true;
		if (mapIndex != PLAYERBOT_MAP_SUNGMA_DONGAN || !IsPlayerBotDsBulk(ch))
			return false;
		out.x = PLAYERBOT_DS_DONGAN_ALCHEMIST_X;
		out.y = PLAYERBOT_DS_DONGAN_ALCHEMIST_Y;
		return true;
	}

	// MT2009_PLUS_BOT_DS_YOHARA800_V1: the progress line of a bulk alchemist, for the coordinator - every
	// PLAYERBOT_DS_PROGRESS_LOG_MS a bot (and at the end of a visit that did something, as often):
	//   cors_left (every Cor that opens), opened (all its life), legendary / mythic stones it holds (bag and worn),
	//   highest - Mythic Highest ones, capped - stones at their strength cap, str - the worn stones' strengths
	//   (one digit a kind, '-' none), worn - a kind's letter (D Diament, R Rubin, J Jadeit, S Szafir, G Granat,
	//   O Onyks, A Ametyst) and grade.step+strength ("D5.4+6"), done - kinds with nothing left to refine.
	void LogPlayerBotDsProgress(LPCHARACTER ch, DWORD dwNow, const char* why, bool force)
	{
		static std::map<DWORD, DWORD> s_last;
		if (!ch || !IsPlayerBotDsBulk(ch))
			return;
		DWORD& last = s_last[ch->GetPlayerID()];
		if (!force && last != 0 && dwNow - last < PLAYERBOT_DS_PROGRESS_LOG_MS)
			return;
		if (force && last != 0 && dwNow - last < 60000)
			return;
		last = dwNow;
		static const char s_kindLetter[] = "DRJSGOA";
		int legendary = 0, mythic = 0, highest = 0, capped = 0, done = 0;
		std::string worn, strengths;
		for (int kind = 0; kind < DS_SLOT_MAX; ++kind)
		{
			std::vector<LPITEM> stones;
			CollectPlayerBotDragonSouls(ch, stones, kind);
			LPITEM w = GetPlayerBotWornDs(ch, kind);
			if (w)
				stones.push_back(w);
			for (size_t i = 0; i < stones.size(); ++i)
			{
				const BYTE g = GetPlayerBotDsGrade(stones[i]);
				if (g == 4) ++legendary;
				if (g >= PLAYERBOT_DS_MYTH_GRADE) ++mythic;
				if (IsPlayerBotDsMythHighest(stones[i])) ++highest;
				if (g >= PLAYERBOT_DS_MIN_WORN_GRADE &&
						GetPlayerBotDsStrength(stones[i]) >= GetPlayerBotDsStrengthCap(g, GetPlayerBotDsStep(stones[i])))
					++capped;
			}
			LPITEM a = NULL, b = NULL;
			if (FindPlayerBotDsRefine(ch, kind, a, b) == PLAYERBOT_DS_WORK_NONE)
				++done;
			char buf[32];
			if (w)
			{
				snprintf(buf, sizeof(buf), "%s%c%u.%u+%u", worn.empty() ? "" : ",", kind < 7 ? s_kindLetter[kind] : '?',
						(unsigned)GetPlayerBotDsGrade(w), (unsigned)GetPlayerBotDsStep(w), (unsigned)GetPlayerBotDsStrength(w));
				worn += buf;
				strengths += (char)('0' + std::min<int>(9, GetPlayerBotDsStrength(w)));
			}
			else
				strengths += '-';
		}
		sys_log(0, "PLAYERBOT_ALCHEMY: progress pid=%u name=%s lv=%d job=%d why=%s cohort=%d cors_left=%d legendary_cors=%d "
				"opened=%d legendary=%d mythic=%d highest=%d capped=%d done_kinds=%d/%d str=%s worn=%s beans=%d gold=%lld map=%ld",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), (int)ch->GetJob(), why,
				IsPlayerBotYoharaCohortPID(ch->GetPlayerID()) ? 1 : 0, CountPlayerBotOpenableCors(ch),
				CountPlayerBotLegendaryCors(ch), ch->GetQuestFlag(PLAYERBOT_DS_OPENED_FLAG), legendary, mythic, highest,
				capped, done, (int)DS_SLOT_MAX, strengths.c_str(), worn.empty() ? "none" : worn.c_str(),
				CountPlayerBotDsBeans(ch), (long long)ch->GetGold(), ch->GetMapIndex());
	}

	// The tick: the local work (qualification, Cors, stones, deck) on a short
	// clock anywhere; the Alchemist's (elixir, refine) walked to in a first
	// village, travelled to when there is any.
	bool ManagePlayerBotAlchemy(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !IsPlayerBotAlchemyUser(ch))
		{
			if (ch && state.bVisitingDsAlchemist)
				EndPlayerBotAlchemistVisit(state, dwNow, ch);
			// MT2009_PLUS_BOT_DS_YOHARA800_V1: a holder of legendary Cors becomes a bulk alchemist.
			if (ch && !ch->IsDead())
				NotePlayerBotDsBulkHolder(ch, dwNow);
			return false;
		}
		const bool bulk = IsPlayerBotDsBulk(ch);
		if (dwNow >= state.dwNextDsLocalTime && !ch->IsDead() && !ch->GetExchange())
		{
			state.dwNextDsLocalTime = dwNow + PLAYERBOT_ALCHEMY_LOCAL_MS;
			EnsurePlayerBotAlchemyQualified(ch);
			// A Cor is a use of an item, which a fight does not refuse: opened
			// on every pass, not only between the blows.
			OpenPlayerBotCors(ch);
			// EquipItem refuses within a second and a half of a blow or a cast
			// ("You have to stand still"): the gear pass's own wait.
			if (ch->GetVictim() == NULL &&
					dwNow - ch->GetLastAttackTime() > PLAYERBOT_EQUIPMENT_COMBAT_DELAY &&
					(state.dwLastBotSkillTime == 0 || dwNow - state.dwLastBotSkillTime > PLAYERBOT_EQUIPMENT_COMBAT_DELAY))
				EquipPlayerBotBestDragonSouls(ch);
			// The deck: ManagePlayerBotDsDeckTick, every bot's tick
			// (MT2009_PLUS_BOT_DS_EXTEND_V1).
			if (bulk)
				LogPlayerBotDsProgress(ch, dwNow, "pass", false);
		}
		if (state.bVisitingShop || state.bVisitingBiologist || state.bVisitingHerbalist || state.bVisitingStable ||
				state.bVisitingAlchemist || state.bVisitingUriel || state.bCraftErrand != 0 ||
				state.bFishingSession || state.bMarketTrip)
			return false;
		if (!state.bVisitingDsAlchemist && dwNow < state.dwNextDsCheckTime)
			return false;
		if ((ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())) || IsPlayerBotHeldForCompany(ch) ||
				ch->GetMyShop() != NULL)
		{
			if (state.bVisitingDsAlchemist)
				EndPlayerBotAlchemistVisit(state, dwNow, ch);
			else
				state.dwNextDsCheckTime = dwNow + GetPlayerBotDsCheckDelay(ch);
			return false;
		}

		playerbot_empire_rules::TPoint alchemist;
		if (!state.bVisitingDsAlchemist)
		{
			state.dwNextDsCheckTime = dwNow + GetPlayerBotDsCheckDelay(ch);
			if (ch->GetVictim() != NULL || state.dwTargetVID != 0)
			{
				// MT2009_PLUS_BOT_DS_YOHARA800_V1: a bulk alchemist hunts where it refines (Dongan): it looks again
				// between two pulls, not a minute or two later.
				if (bulk)
					state.dwNextDsCheckTime = dwNow + number(PLAYERBOT_DS_BULK_BUSY_RETRY_MIN_MS, PLAYERBOT_DS_BULK_BUSY_RETRY_MAX_MS);
				return false;
			}
			if (!HasPlayerBotAlchemistWork(ch))
				return false;
			if (!GetPlayerBotDsAlchemist(ch, ch->GetMapIndex(), alchemist))
			{
				long homeMap = 0, homeX = 0, homeY = 0;
				// MT2009_PLUS_BOT_DS_YOHARA800_V1: from a Yohara map, Dongan's Alchemist (its core hosts no first
				// village); from anywhere else the first village's, as before.
				if (bulk && IsPlayerBotSungmaBotMap(ch->GetMapIndex()) && IsPlayerBotMapHostedHere(PLAYERBOT_MAP_SUNGMA_DONGAN))
				{
					homeMap = PLAYERBOT_MAP_SUNGMA_DONGAN;
					homeX = PLAYERBOT_DS_DONGAN_ARRIVAL_X;
					homeY = PLAYERBOT_DS_DONGAN_ARRIVAL_Y;
				}
				else if (!GetPlayerBotVillageReturn(ch, playerbot_empire_rules::MAP_ROLE_M1, homeMap, homeX, homeY) ||
						!IsPlayerBotMapHostedHere(homeMap) || !playerbot_empire_rules::GetAlchemist(homeMap, alchemist))
					return false;
				SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
				if (!TransitionPlayerBotMap(ch, state, homeMap, homeX, homeY, dwNow, "alchemy_to_alchemist"))
					return false;
				++s_kPlayerBotAlchemyStats.trips;
				state.dwNextDsCheckTime = 0;
				return true;
			}
			state.bVisitingDsAlchemist = true;
			state.dwNextDsActionTime = 0;
			state.bDsVisitSteps = 0;
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ch->Stop();
			ClearPlayerBotRoute(state, true);
			sys_log(0, "PLAYERBOT_ALCHEMY: going to the Alchemist pid=%u name=%s lv=%d gold=%lld",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), (long long)ch->GetGold());
		}
		if (!GetPlayerBotDsAlchemist(ch, ch->GetMapIndex(), alchemist))
		{
			EndPlayerBotAlchemistVisit(state, dwNow, ch);
			return false;
		}
		SetPlayerBotAction(state, BOT_ACTION_SHOP, dwNow);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		long approachX = 0, approachY = 0;
		GetPlayerBotNpcApproach(ch->GetPlayerID(), alchemist.x, alchemist.y, 0x44534f55U, approachX, approachY);
		if (DISTANCE_APPROX(ch->GetX() - approachX, ch->GetY() - approachY) > PLAYERBOT_STABLE_ARRIVE_DISTANCE)
		{
			if (!MovePlayerBotTownLeg(ch, state, dwNow, approachX, approachY, PLAYERBOT_STABLE_ARRIVE_DISTANCE) &&
					state.bStuckCounter >= 6)
			{
				sys_err("PLAYERBOT_ALCHEMY: route failed pid=%u name=%s map=%ld from=(%ld,%ld)",
						ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), ch->GetX(), ch->GetY());
				EndPlayerBotAlchemistVisit(state, dwNow, ch);
				return false;
			}
			return true;
		}
		ch->Stop();
		ch->SetPosition(POS_STANDING);
		if (state.dwNextDsActionTime == 0)
		{
			state.dwNextDsActionTime = dwNow + number(3000, 7000);
			return true;
		}
		if (dwNow < state.dwNextDsActionTime)
			return true;
		if (ch->DragonSoul_GetActiveDeck() >= 0)
			ch->DragonSoul_DeactivateAll();
		// MT2009_PLUS_BOT_DS_YOHARA800_V1: a bulk alchemist does more a visit, a little faster.
		const int maxSteps = bulk ? PLAYERBOT_DS_BULK_VISIT_MAX_STEPS : PLAYERBOT_ALCHEMY_VISIT_MAX_STEPS;
		if (state.bDsVisitSteps < maxSteps && DoPlayerBotAlchemistStep(ch))
		{
			++state.bDsVisitSteps;
			state.dwNextDsActionTime = dwNow + (bulk ? number(PLAYERBOT_DS_BULK_STEP_MIN_MS, PLAYERBOT_DS_BULK_STEP_MAX_MS)
					: number(2500, 5000));
			return true;
		}
		EquipPlayerBotBestDragonSouls(ch);
		sys_log(0, "PLAYERBOT_ALCHEMY: visit over pid=%u name=%s lv=%d steps=%d worn=%d gold=%lld", ch->GetPlayerID(),
				ch->GetName(), ch->GetLevel(), (int)state.bDsVisitSteps, CountPlayerBotWornDs(ch, false),
				(long long)ch->GetGold());
		if (bulk && state.bDsVisitSteps > 0)
			LogPlayerBotDsProgress(ch, dwNow, "visit", true);
		EndPlayerBotAlchemistVisit(state, dwNow, ch);
		return false;
	}

	// MT2009_PLUS_MARKET_SINK_V1: a line of Cors asked for off a counter.
	void NotePlayerBotCorBought(LPCHARACTER ch, DWORD vnum, long long price, DWORD count)
	{
		if (!IsPlayerBotCorVnum(vnum))
			return;
		++s_kPlayerBotAlchemyStats.corLinesBought;
		s_kPlayerBotAlchemyStats.corUnitsBought += count;
		s_kPlayerBotAlchemyStats.corYang += (unsigned long long)std::max<long long>(0, price);
		sys_log(0, "PLAYERBOT_ALCHEMY: cor bought pid=%u name=%s units=%u price=%lld have=%d keep=%d supply=%u plentiful=%d",
				ch ? ch->GetPlayerID() : 0, ch ? ch->GetName() : "", (unsigned int)count, price,
				ch ? (int)ch->CountSpecifyItem(vnum) : 0, GetPlayerBotCorKeep(),
				(unsigned int)GetPlayerBotOperatorGoodsSupply(PLAYERBOT_COR_ROUGH_VNUM),
				IsPlayerBotCorMarketPlentiful() ? 1 : 0);
	}

	void LogPlayerBotAlchemyCensus()
	{
		const TPlayerBotAlchemyStats& s = s_kPlayerBotAlchemyStats;
		sys_log(0, "PLAYERBOT_DS: census recharged=%u kept_expired_passes=%u deck_on=%u deck_off=%u pulled_out=%u pull_out_destroyed=%u elixir_price=%lld",
				s.recharged, s.keptExpired, s.deckOn, s.deckOff, s.pulledOut, s.pullOutDestroyed, GetPlayerBotDsElixirPrice());
		sys_log(0, "PLAYERBOT_ALCHEMY: census shards=%u daily_cors=%u opened=%u worn_changes=%u grade=%u step=%u strength=%u refine_fails=%u elixirs=%u beans=%u listed=%u trips=%u cor_lines_bought=%u cor_units_bought=%llu cor_yang=%llu cor_supply=%u plentiful=%d",
				s.shards, s.cors, s.opened, s.equipped, s.refinesGrade, s.refinesStep, s.refinesStrength,
				s.refineFails, s.elixirs, s.beans, s.listed, s.trips, s.corLinesBought, s.corUnitsBought, s.corYang,
				(unsigned int)GetPlayerBotOperatorGoodsSupply(PLAYERBOT_COR_ROUGH_VNUM),
				IsPlayerBotCorMarketPlentiful() ? 1 : 0);
		// MT2009_PLUS_BOT_DS_YOHARA800_V1: the bulk alchemists, since the core's start.
		sys_log(0, "PLAYERBOT_ALCHEMY: census bulk opened=%u myth_made=%u highest_made=%u capped_made=%u beans_used=%u",
				s.bulkOpened, s.bulkMythMade, s.bulkHighestMade, s.bulkCapMade, s.bulkBeans);
	}
}

#endif
