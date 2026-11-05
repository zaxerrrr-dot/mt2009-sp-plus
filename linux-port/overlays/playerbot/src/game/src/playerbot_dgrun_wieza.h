#ifndef __INC_METIN2_PLAYERBOT_DGRUN_WIEZA_H__
#define __INC_METIN2_PLAYERBOT_DGRUN_WIEZA_H__

// MT2009_PLUS_BOT_WIEZA_V1 - Wieza Sung Mahi (387, wieza_sung_mahi.quest) as a bot's SOLO climb (the owner, night of 5/6
// November 2026: "boty maja tez robic Wieze Sung Mahi - solo, 10 botow ... pelne pozwolenie na zmiany botow i na
// wpuszczenie ich do wiezy; reszta zasad jak dla graczy"). The tower is never made weaker: no monster, boss, time, circle
// or reward of it changed - the bot does what a person does, by the quest's own flags.
//
// The row "wieza_smh" of PLAYERBOT_DGRUN_DEFS (kind DGRUN_KIND_WIEZA): a run of ONE bot (no party - the tower's rule),
// gathered at the dungeon panel's entrance (Wejscie Piekielnej Wiezy, Seoganland 376), never called by the clock - only
// by the training (the file playerbot_wieza_train) and the Dropki row "wieza_smh".
//
// The way in (PreparePlayerBotWiezaEntrant - the hall portal's rules, wieza_sung_mahi.enter()): level 120, a Champion
// level, a weapon and an armour; out of its party, off its mount, out of a polymorph; one Sztandar Czaszki (70401) a
// climb - its own, else bought for PLAYERBOT_WIEZA_BANNER_PRICE (the bots' stand-in for the IS / the Gnoll chests'
// drop; a bot that cannot pay is not called); the floor: the next one after the best of this season (the quest's flags
// wieza_sung_mahi.season / .best, the month of Polish time - PlayerBotWiezaSeason), at most 50. The core makes the
// instance (flag mt2009_dgrun), puts the bot at room A, sets p1 = the bot and the quest's flag start_floor, and the
// quest's timer wieza_sung_mahi_dgrun does the first login's begin_climb (10 s countdown, the floor's Sung Ma).
//
// Inside (ManagePlayerBotWiezaInside), every floor's three rooms by the quest's flags (room, phase, task, wrong, ...):
//   * every room: the ground circles of d.zone_attack (its marker 3975: the medium thorn circle under the bot every 20 s,
//     the bosses' seven circles and line, the dodge task's circles) stepped out of before anything (as Glebie's);
//     the tower's own potions (W) 70390-70395 drunk (the engine refuses any other in the tower) - bought at the run's
//     start at their shop price (Handlarka 9014), as a person buys them in the hall;
//   * room 1 (waves, 4 min) and room 3 (waves, then the floor's bosses, 8 min): what attacks the bot, else the nearest;
//   * room 2, the seven tasks (the quest's pick_task):
//       1 Demon Stone and archers - everything (the stone wakes them; nearest first);
//       2 the right Metin, one chance - the bot picks one of the four at random (no person can tell them apart); a wrong
//         one: every Metin and the waves (the quest's "wrong");
//       3 dodge for 60 s - no attack but on what hits it, the circles dodged, the HP kept full (a hit at full HP leaves 1,
//         a second kills);
//       4 the chessboard - the pair whose two monsters differ (what a person sees: the races of the two pieces of a row)
//         and only it (IsPlayerBotWiezaNoTarget keeps every bot off the others);
//       5 the puzzle key - the waves, the Zagadkowy Klucz (70403) picked up and used (the quest's 30%);
//       6 the seals - the waves, the Kamien Pieczeci (70404) picked up and handed to a seal (4021); a seal that refused
//         it is not tried again for that step (a person's memory);
//       7 the curse - the waves, the Antidotum SungMa (70405) picked up and used at curse step 3 (30% HP a tick);
//   * a room done (phase 1): the loot, then the portal 4020 - the quest's "Dalej" through wieza_sung_mahi_dgrun_next
//     for the bot standing by it; the stairs' portal the same. The climb goes on floor after floor until the bot dies
//     (the quest sends it to the hall), a room's time runs out or floor 50 is won.
// The strength limit: a bot that fails its first floor PLAYERBOT_WIEZA_LIMIT_FAILS climbs in a row rests from the tower
// PLAYERBOT_WIEZA_LIMIT_REST_MIN minutes (its flags wieza_sung_mahi.bot_lim_*), and the training takes the next one.
// The run bonuses (BuffPlayerBotYdgMember and the floor's Sung Ma filled up - the bots stronger, the tower the same) as
// every bots' dungeon run; the event flag m2_bot_wieza_bonus_off 1 takes them away. The floor rewards: the quest puts
// a bot's straight into its bag; the ranking only with wieza_smh_bot_rank 1 (the quest).
//
// Training: the file playerbot_wieza_train in the core's directory (read every 30 s when it changed; kept):
//     solo <n>          keep the n strongest eligible bots of this core climbing (one run each, one after another)
//     bot <pid> ...     these bots as well (fixed)
//     cap <runs>        climbs at once (default: n + fixed)
//     # ...             a comment
// Such a bot is a training member to every other pass (IsPlayerBotYdgTrainee: no clock call, kept on the core). The
// event flag m2_bot_wieza_train_off 1 stops new climbs. The test file playerbot_dungeon_runs_test: "now wieza_smh" (a
// planner pass now), "wieza_status".
//
// The log: BOT_WIEZA lines - entry (floor, best, banner how), start, room (floor, room, task), floor done (seconds),
// died, task fail (kind, why), limit, run end (result, start floor, reached, floors done, each floor's seconds, deaths,
// dodges, keys, seals, antidotes, potions), train (load, pick, called, status) - beside BOT_DGRUN.
//
// An implementation fragment: included at the end of playerbot_dungeon_runs.h (after the YDG and Glebie fragments, whose
// helpers it uses), in the anonymous namespace.

namespace
{
	const long PLAYERBOT_WIEZA_MAP = 387;
	const long PLAYERBOT_WIEZA_HALL = 386;
	const int PLAYERBOT_WIEZA_MIN_LEVEL = 120;
	const int PLAYERBOT_WIEZA_MAX_FLOOR = 50;
	const DWORD PLAYERBOT_WIEZA_BANNER = 70401;		// Sztandar Czaszki
	const DWORD PLAYERBOT_WIEZA_KEY = 70403;		// Zagadkowy Klucz
	const DWORD PLAYERBOT_WIEZA_SEAL_STONE = 70404;		// Kamien Pieczeci Sunga Mahi
	const DWORD PLAYERBOT_WIEZA_ANTIDOTE = 70405;		// Antidotum SungMa
	const DWORD PLAYERBOT_WIEZA_PORTAL = 4020;
	const DWORD PLAYERBOT_WIEZA_SEAL = 4021;
	const DWORD PLAYERBOT_WIEZA_METIN = 7600;
	const DWORD PLAYERBOT_WIEZA_CHESS_MIN = 7615, PLAYERBOT_WIEZA_CHESS_MAX = 7620;
	const DWORD PLAYERBOT_WIEZA_ZONE_MARK = 3975;
	const long long PLAYERBOT_WIEZA_BANNER_PRICE = 5000000LL;
	// cfg(): cells off the map's base
	const long PLAYERBOT_WIEZA_ROOM_A[2] = { 402, 463 };
	const long PLAYERBOT_WIEZA_MID_B[2] = { 448, 129 };
	const long PLAYERBOT_WIEZA_ROOM_C[2] = { 91, 454 };
	const long PLAYERBOT_WIEZA_STAIRS[2] = { 320, 348 };
	// cfg().sungma: SILA, WIT, ODP, INT every five floors
	const int PLAYERBOT_WIEZA_SUNGMA[10][4] = { { 35, 25, 35, 55 }, { 38, 27, 38, 60 }, { 42, 30, 42, 64 }, { 45, 33, 45, 67 },
			{ 48, 36, 48, 70 }, { 52, 40, 52, 73 }, { 56, 44, 56, 77 }, { 60, 48, 60, 81 }, { 65, 53, 65, 85 }, { 70, 58, 70, 90 } };
	// the tower's potions (W): what is bought at the start (vnum, stock wanted) and drunk (below)
	const DWORD PLAYERBOT_WIEZA_POT_RED = 70390, PLAYERBOT_WIEZA_POT_WINE = 70392, PLAYERBOT_WIEZA_POT_LIFE = 70393,
			PLAYERBOT_WIEZA_POT_DRAGON = 70395;
	const DWORD PLAYERBOT_WIEZA_PORTAL_CALL_MS = 3000;
	const DWORD PLAYERBOT_WIEZA_LOOT_MS = 15000;
	const DWORD PLAYERBOT_WIEZA_DODGE_MS = 2500;
	const DWORD PLAYERBOT_WIEZA_TRAIN_FILE_MS = 30000;
	const DWORD PLAYERBOT_WIEZA_TRAIN_PLAN_MS = 10000;
	const DWORD PLAYERBOT_WIEZA_TRAIN_PICK_MS = 5 * 60 * 1000;
	const DWORD PLAYERBOT_WIEZA_STATUS_MS = 10 * 60 * 1000;
	const char* const PLAYERBOT_WIEZA_TRAIN_FILE = "playerbot_wieza_train";
	const char* const PLAYERBOT_WIEZA_RUNS_FILE = "playerbot_wieza_runs.tsv";

	bool IsPlayerBotWiezaInstance(long mapIndex)
	{
		return mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN && mapIndex / 10000 == PLAYERBOT_WIEZA_MAP;
	}

	int GetPlayerBotWiezaEnv(const char* name, int def, int lo, int hi)
	{
		return ReadPlayerBotYoharaEnvInt(name, def, lo, hi);
	}

	// ------------------------------------------------------------ the season and the floors (the quest's flags)

	// The quest's season(): the month of Polish time (Europe/Warsaw, summer time from the last Sunday of March 01:00 UTC
	// to the last Sunday of October 01:00 UTC) - year * 12 + month.
	time_t PlayerBotWiezaLastSunday(int year, int monthAfter0)
	{
		struct tm a;
		memset(&a, 0, sizeof(a));
		a.tm_year = year - 1900;
		a.tm_mon = monthAfter0;	// the first of the next month (0-based: 3 = April)
		a.tm_mday = 1;
		const time_t last = timegm(&a) - 86400;
		struct tm b;
		gmtime_r(&last, &b);
		return last - (time_t)b.tm_wday * 86400;
	}

	int PlayerBotWiezaSeason()
	{
		const time_t t = (time_t)get_global_time();
		struct tm g;
		gmtime_r(&t, &g);
		const int y = g.tm_year + 1900;
		const time_t from = PlayerBotWiezaLastSunday(y, 3) + 3600;
		const time_t to = PlayerBotWiezaLastSunday(y, 10) + 3600;
		const time_t w = t + ((t >= from && t < to) ? 7200 : 3600);
		gmtime_r(&w, &g);
		return (g.tm_year + 1900) * 12 + g.tm_mon + 1;
	}

	int GetPlayerBotWiezaBest(LPCHARACTER ch)
	{
		if (!ch || ch->GetQuestFlag("wieza_sung_mahi.season") != PlayerBotWiezaSeason())
			return 0;
		return std::max(0, std::min(PLAYERBOT_WIEZA_MAX_FLOOR, ch->GetQuestFlag("wieza_sung_mahi.best")));
	}

	int GetPlayerBotWiezaStartFloor(LPCHARACTER ch)
	{
		return std::min(GetPlayerBotWiezaBest(ch) + 1, PLAYERBOT_WIEZA_MAX_FLOOR);
	}

	// ------------------------------------------------------------ the way in

	bool IsPlayerBotWiezaResting(LPCHARACTER ch)
	{
		return ch && ch->GetQuestFlag("wieza_sung_mahi.bot_lim_until") > (int)get_global_time();
	}

	// The hall portal's asks (wieza_sung_mahi.enter()) a bot can meet by itself, and its limit's rest.
	bool IsPlayerBotWiezaFit(LPCHARACTER ch)
	{
		return ch && (int)ch->GetLevel() >= PLAYERBOT_WIEZA_MIN_LEVEL && GetPlayerBotChampionLevel(ch) >= 1 &&
				ch->GetWear(WEAR_WEAPON) && ch->GetWear(WEAR_BODY) && !IsPlayerBotWiezaResting(ch);
	}

	long long GetPlayerBotWiezaBannerPrice()
	{
		return (long long)GetPlayerBotWiezaEnv("PLAYERBOT_WIEZA_BANNER_PRICE", (int)PLAYERBOT_WIEZA_BANNER_PRICE, 0, 2000000000);
	}

	bool CanPlayerBotWiezaPay(LPCHARACTER ch)
	{
		return ch && ch->IsItemLoaded() && (ch->CountSpecifyItem(PLAYERBOT_WIEZA_BANNER) > 0 ||
				(long long)ch->GetGold() >= GetPlayerBotWiezaBannerPrice());
	}

	// Before the jump: the portal's rules (no party, no mount, no polymorph - the quest's guard() would take them
	// anyway), the banner's means, the floor. False: not in.
	bool PreparePlayerBotWiezaEntrant(LPCHARACTER ch, const TPlayerBotDgRun& run)
	{
		if (!ch)
			return false;
		const char* why = NULL;
		if (!IsPlayerBotWiezaFit(ch))
			why = "unfit";
		else if (!CanPlayerBotWiezaPay(ch))
			why = "no_banner";
		if (why)
		{
			sys_log(0, "BOT_WIEZA: entry refused run=%d pid=%u name=%s why=%s level=%d champion=%d gold=%lld", run.iId,
					ch->GetPlayerID(), ch->GetName(), why, (int)ch->GetLevel(), GetPlayerBotChampionLevel(ch), (long long)ch->GetGold());
			return false;
		}
		if (ch->GetParty())
			LeavePlayerBotParty(ch);
		if (ch->IsRiding())
			ch->StopRiding();
		if (ch->IsPolymorphed())
			ch->SetPolymorph(0);
		const int floor = GetPlayerBotWiezaStartFloor(ch);
		ch->SetQuestFlag("wieza_sung_mahi.start_floor", floor);
		return true;
	}

	// After the jump: the bot is the climb's player (p1) - the quest's surface, curse and reward lists.
	void SetPlayerBotWiezaInstance(LPDUNGEON d, LPCHARACTER ch)
	{
		if (!d || !ch)
			return;
		d->SetFlag("p1", (int)ch->GetPlayerID());
	}

	// One Sztandar Czaszki a climb: its own, else bought.
	long long ChargePlayerBotWiezaBanner(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		long long paid = 0;
		const char* how = "let_go";
		if (ch->CountSpecifyItem(PLAYERBOT_WIEZA_BANNER) > 0)
		{
			ch->RemoveSpecifyItem(PLAYERBOT_WIEZA_BANNER, 1);
			how = "own";
		}
		else
		{
			const long long price = GetPlayerBotWiezaBannerPrice();
			if ((long long)ch->GetGold() >= price)
			{
				if (price > 0)
					PlayerBotChangeGold(ch, -price);
				paid = price;
				how = "bought";
			}
		}
		sys_log(0, "BOT_WIEZA: entry pid=%u name=%s floor=%d best=%d season=%d banner=%s price=%lld gold=%lld", ch->GetPlayerID(),
				ch->GetName(), ch->GetQuestFlag("wieza_sung_mahi.start_floor"), GetPlayerBotWiezaBest(ch), PlayerBotWiezaSeason(), how,
				paid, (long long)ch->GetGold());
		return paid;
	}

	// ------------------------------------------------------------ the run's state

	struct TPlayerBotWiezaRun
	{
		DWORD dwPid;
		int iStartFloor, iBestBefore;
		int iFloor, iRoom, iTask, iPhase;	// the last look at the quest's flags
		int iTopFloor, iFloorsDone;
		DWORD dwRoomSince, dwPhase1Since;
		bool bDead, bFailed, bClosed;
		int iDeaths;
		std::string floorSecs, taskFails;
		int iDodges, iKeysUsed, iSealsGiven, iSealsWrong, iAntidotes, iPotions;
		long long llPotionGold, llGoldAt;
		int iItemsAt;
		DWORD dwNextPotion, dwNextCall;
		int iSealN;
		std::set<DWORD> sealTried;
		DWORD dwOddSince;
		int iSungmaFloor;
		TPlayerBotWiezaRun() : dwPid(0), iStartFloor(0), iBestBefore(0), iFloor(0), iRoom(0), iTask(0), iPhase(0), iTopFloor(0),
				iFloorsDone(0), dwRoomSince(0), dwPhase1Since(0), bDead(false), bFailed(false), bClosed(false), iDeaths(0), iDodges(0),
				iKeysUsed(0), iSealsGiven(0), iSealsWrong(0), iAntidotes(0), iPotions(0), llPotionGold(0), llGoldAt(0), iItemsAt(0),
				dwNextPotion(0), dwNextCall(0), iSealN(0), dwOddSince(0), iSungmaFloor(0) {}
	};
	std::map<int, TPlayerBotWiezaRun> s_mapPlayerBotWiezaRuns;
	// instance -> the task's pick: the Metin chosen (task 2), or the odd chess pair (task 4)
	std::map<long, std::pair<DWORD, DWORD> > s_mapPlayerBotWiezaPick;

	struct TPlayerBotWiezaDodge
	{
		long x, y;
		DWORD dwUntil, dwNextMove;
		TPlayerBotWiezaDodge() : x(0), y(0), dwUntil(0), dwNextMove(0) {}
	};
	std::map<DWORD, TPlayerBotWiezaDodge> s_mapPlayerBotWiezaDodge;

	bool IsPlayerBotWiezaBonusOn()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_bot_wieza_bonus_off") == 0;
	}

	// The tower's Will of this floor filled up (the YDG runs' Sung Ma bonus - the instance's own requirement, d.set_sungma).
	void BuffPlayerBotWiezaSungma(LPCHARACTER c, TPlayerBotWiezaRun& w, int floor)
	{
		if (!c || floor < 1 || !IsPlayerBotWiezaBonusOn() || !GetPlayerBotWiezaEnv("PLAYERBOT_WIEZA_SUNGMA", 1, 0, 1))
			return;
		const int band = std::max(0, std::min(9, (floor - 1) / 5));
		if (w.iSungmaFloor == band + 1)
			return;
		w.iSungmaFloor = band + 1;
		std::string added;
		for (int k = 0; k < 4; ++k)
		{
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_SUNGMA[k]);
			const BYTE point = (BYTE)(POINT_SUNGMA_STR + k);
			const int have = yohara_gear::SungmaEffective(c, point);
			const int want = PLAYERBOT_WIEZA_SUNGMA[band][k];
			if (have >= want)
				continue;
			const int pct = MAX(-99, (int)c->GetPoint(POINT_SUNGMA_PER_STR + k));
			const int add = (want - have) * 100 / (100 + pct) + 1;
			c->AddAffect(AFFECT_PLAYERBOT_YDG_SUNGMA[k], point, add, 0, 6 * 3600, 0, true);
			added += (added.empty() ? "" : "/") + std::to_string(k) + "+" + std::to_string(add);
		}
		if (!added.empty())
			sys_log(0, "BOT_WIEZA: sungma pid=%u name=%s floor=%d added=%s", c->GetPlayerID(), c->GetName(), floor, added.c_str());
	}

	// The tower's potions (W), at the shop's price, up to a share of the purse.
	void BuyPlayerBotWiezaPotions(LPCHARACTER ch, TPlayerBotWiezaRun& w)
	{
		static const DWORD vnums[4] = { PLAYERBOT_WIEZA_POT_RED, PLAYERBOT_WIEZA_POT_WINE, PLAYERBOT_WIEZA_POT_LIFE, PLAYERBOT_WIEZA_POT_DRAGON };
		static const int want[4] = { 200, 40, 10, 5 };
		long long budget = (long long)ch->GetGold() * GetPlayerBotWiezaEnv("PLAYERBOT_WIEZA_POTION_PURSE_PCT", 25, 0, 90) / 100;
		std::string bought;
		for (int i = 0; i < 4; ++i)
		{
			const TItemTable* t = ITEM_MANAGER::instance().GetTable(vnums[i]);
			if (!t)
				continue;
			const long long price = std::max<long long>(1, (long long)t->dwGold);
			int n = want[i] - (int)ch->CountSpecifyItem(vnums[i]);
			while (n > 0 && price * n > budget)
				--n;
			if (n <= 0)
				continue;
			if (ch->GetEmptyInventory(1) < 0 && !HasPlayerBotYdgStackRoom(ch, vnums[i]) && !MakePlayerBotYdgRoom(ch, "wieza_potions"))
				break;
			PlayerBotChangeGold(ch, -price * n);
			budget -= price * n;
			w.llPotionGold += price * n;
			while (n > 0)
			{
				const int part = std::min(n, 200);
				ch->AutoGiveItem(vnums[i], (ITEM_COUNT)part, -1, false);
				n -= part;
				bought += (bought.empty() ? "" : ",") + std::to_string(vnums[i]) + "x" + std::to_string(part);
			}
		}
		if (!bought.empty())
			sys_log(0, "BOT_WIEZA: potions bought pid=%u name=%s %s gold=%lld", ch->GetPlayerID(), ch->GetName(), bought.c_str(),
					(long long)ch->GetGold());
	}

	void NotePlayerBotWiezaRunStart(const TPlayerBotDgRun& run)
	{
		TPlayerBotWiezaRun& w = s_mapPlayerBotWiezaRuns[run.iId];
		w = TPlayerBotWiezaRun();
		LPCHARACTER c = run.members.empty() ? NULL : CHARACTER_MANAGER::instance().FindByPID(run.members[0]);
		if (!c)
			return;
		w.dwPid = c->GetPlayerID();
		w.iStartFloor = c->GetQuestFlag("wieza_sung_mahi.start_floor");
		w.iBestBefore = GetPlayerBotWiezaBest(c);
		MakePlayerBotYdgRoom(c, "wieza_start");
		MakePlayerBotYdgRoom(c, "wieza_start");
		BuyPlayerBotWiezaPotions(c, w);
		w.llGoldAt = (long long)c->GetGold();
		w.iItemsAt = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			if (c->GetInventoryItem(cell))
				++w.iItemsAt;
		const bool bonus = IsPlayerBotWiezaBonusOn();
		if (bonus)
			BuffPlayerBotYdgMember(c);
		BuffPlayerBotWiezaSungma(c, w, std::max(1, w.iStartFloor));
		int plus = 0;
		const int gear = GetPlayerBotYdgGearLevel(c, &plus);
		sys_log(0, "BOT_WIEZA: start run=%d instance=%ld pid=%u name=%s job=%u level=%d champion=%d gear=%d+%d hp=%d floor=%d best=%d "
				"bonus=%d sungma=%d/%d/%d/%d potions=%u/%u/%u/%u", run.iId, run.lInstance, c->GetPlayerID(), c->GetName(),
				(unsigned int)c->GetJob(), (int)c->GetLevel(), GetPlayerBotChampionLevel(c), gear, plus, c->GetMaxHP(), w.iStartFloor,
				w.iBestBefore, bonus ? 1 : 0, yohara_gear::SungmaEffective(c, POINT_SUNGMA_STR), yohara_gear::SungmaEffective(c, POINT_SUNGMA_HP),
				yohara_gear::SungmaEffective(c, POINT_SUNGMA_MOVE), yohara_gear::SungmaEffective(c, POINT_SUNGMA_IMMUNE),
				(unsigned int)c->CountSpecifyItem(PLAYERBOT_WIEZA_POT_RED), (unsigned int)c->CountSpecifyItem(PLAYERBOT_WIEZA_POT_WINE),
				(unsigned int)c->CountSpecifyItem(PLAYERBOT_WIEZA_POT_LIFE), (unsigned int)c->CountSpecifyItem(PLAYERBOT_WIEZA_POT_DRAGON));
	}

	// ------------------------------------------------------------ the monitor (UpdatePlayerBotDgRunInside, every second)

	int GetPlayerBotWiezaStage(LPDUNGEON d, int previous)
	{
		if (!d || d->GetFlag("init") != 1)
			return previous;
		return d->GetFlag("floor") * 10 + d->GetFlag("room");
	}

	bool IsPlayerBotWiezaWon(LPDUNGEON d)
	{
		return d && d->GetFlag("floor") >= PLAYERBOT_WIEZA_MAX_FLOOR && d->GetFlag("boss_dead") == 1;
	}

	long long GetPlayerBotWiezaSignature(LPDUNGEON d)
	{
		if (!d)
			return 0;
		static const char* const flags[] = { "init", "countdown", "floor", "room", "phase", "task", "wv_n", "tb_n", "boss_dead",
				"seal_n", "odd_dead", "wrong", "woken", "dg_k", "curse_n", "closed" };
		long long sig = 0;
		for (size_t i = 0; i < sizeof(flags) / sizeof(flags[0]); ++i)
			sig = sig * 31LL + d->GetFlag(flags[i]);
		return sig;
	}

	void UpdatePlayerBotWiezaInside(TPlayerBotDgRun& run, LPDUNGEON d, DWORD dwNow)
	{
		std::map<int, TPlayerBotWiezaRun>::iterator it = s_mapPlayerBotWiezaRuns.find(run.iId);
		if (it == s_mapPlayerBotWiezaRuns.end() || !d)
			return;
		TPlayerBotWiezaRun& w = it->second;
		LPCHARACTER c = CHARACTER_MANAGER::instance().FindByPID(w.dwPid);
		const int floor = d->GetFlag("floor"), room = d->GetFlag("room"), phase = d->GetFlag("phase"), task = d->GetFlag("task");
		const bool closed = d->GetFlag("closed") == 1, failed = d->GetFlag("failed") == 1;
		if (d->GetFlag("init") != 1)
			return;
		// a room's end: the floor done (room 3 -> the stairs, or the 50th's bosses), a task failed (the climb closed in it)
		if (room != w.iRoom || floor != w.iFloor)
		{
			if (w.iRoom == 3 && room == 4)
			{
				w.iTopFloor = std::max(w.iTopFloor, w.iFloor);
				++w.iFloorsDone;
				const int secs = d->GetFlag("fl_secs");
				if (w.floorSecs.size() < 400)
					w.floorSecs += (w.floorSecs.empty() ? "" : ",") + std::to_string(w.iFloor) + ":" + std::to_string(secs);
				sys_log(0, "BOT_WIEZA: floor done run=%d name=%s floor=%d secs=%d floors_done=%d hp=%d%%", run.iId, c ? c->GetName() : "?",
						w.iFloor, secs, w.iFloorsDone, c && c->GetMaxHP() > 0 ? (int)((long long)c->GetHP() * 100 / c->GetMaxHP()) : -1);
			}
			if (room >= 1 && room <= 3)
				sys_log(0, "BOT_WIEZA: room run=%d name=%s floor=%d room=%d task=%d after_s=%u", run.iId, c ? c->GetName() : "?", floor,
						room, room == 2 ? task : 0, (dwNow - run.dwEnteredAt) / 1000);
			w.iRoom = room;
			w.iFloor = floor;
			w.dwRoomSince = dwNow;
			w.sealTried.clear();
			w.iSealN = 0;
			w.dwOddSince = 0;
			s_mapPlayerBotWiezaPick.erase(run.lInstance);
			if (c && floor >= 1)
			{
				BuffPlayerBotWiezaSungma(c, w, floor);
				// the run's bonuses (an hour's) for a long climb
				if (IsPlayerBotWiezaBonusOn() && !c->FindAffect(AFFECT_PLAYERBOT_YDG_MONSTER))
					BuffPlayerBotYdgMember(c);
			}
		}
		// the 50th floor: no stairs - its bosses down is the floor (and the climb) won
		if (room == 3 && floor >= PLAYERBOT_WIEZA_MAX_FLOOR && d->GetFlag("boss_dead") == 1 && w.iTopFloor < floor)
		{
			w.iTopFloor = floor;
			++w.iFloorsDone;
			const int secs = d->GetFlag("fl_secs");
			w.floorSecs += (w.floorSecs.empty() ? "" : ",") + std::to_string(floor) + ":" + std::to_string(secs);
			sys_log(0, "BOT_WIEZA: floor done run=%d name=%s floor=%d secs=%d floors_done=%d - the top", run.iId, c ? c->GetName() : "?",
					floor, secs, w.iFloorsDone);
		}
		w.iTask = task;
		if (phase != w.iPhase)
		{
			w.iPhase = phase;
			if (phase == 1)
				w.dwPhase1Since = dwNow;
		}
		if (c && c->GetMapIndex() == run.lInstance)
		{
			if (c->IsDead() && !w.bDead)
			{
				++w.iDeaths;
				sys_log(0, "BOT_WIEZA: died run=%d name=%s floor=%d room=%d task=%d phase=%d after_room_s=%u", run.iId, c->GetName(),
						floor, room, room == 2 ? task : 0, phase, (dwNow - w.dwRoomSince) / 1000);
			}
			w.bDead = c->IsDead();
		}
		if (closed && !w.bClosed)
		{
			w.bClosed = true;
			w.bFailed = failed;
			if (phase == 0 && room >= 1 && room <= 3)
			{
				const char* why = failed ? "death" : (run.szResult ? run.szResult : "time");
				char buf[48];
				snprintf(buf, sizeof(buf), "%sf%d:r%d:t%d:%s", w.taskFails.empty() ? "" : ",", floor, room, room == 2 ? task : 0, why);
				w.taskFails += buf;
				if (room == 2)
					sys_log(0, "BOT_WIEZA: task fail run=%d name=%s floor=%d kind=%d why=%s room_s=%u wrong=%d seal_n=%d curse=%d", run.iId,
							c ? c->GetName() : "?", floor, task, why, (dwNow - w.dwRoomSince) / 1000, d->GetFlag("wrong"), d->GetFlag("seal_n"),
							d->GetFlag("cs1"));
				else
					sys_log(0, "BOT_WIEZA: room fail run=%d name=%s floor=%d room=%d why=%s room_s=%u bosses=%d", run.iId, c ? c->GetName() : "?",
							floor, room, why, (dwNow - w.dwRoomSince) / 1000, d->GetFlag("tb_n"));
			}
		}
	}

	// ------------------------------------------------------------ the targets

	// The chessboard's odd pair: a row's two pieces (room C: the right side x 103-118, the left 65-80, mirrored round 91.5)
	// whose races differ - what a person sees.
	bool FindPlayerBotWiezaOddPair(long instance, DWORD dwNow, DWORD& a, DWORD& b)
	{
		LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(instance);
		if (!pMap)
			return false;
		const long bx = pMap->m_setting.iBaseX, by = pMap->m_setting.iBaseY;
		const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(instance, dwNow);
		std::vector<const TPlayerBotArzDgFoe*> left, right;
		for (size_t i = 0; i < scan.foes.size(); ++i)
		{
			const TPlayerBotArzDgFoe& f = scan.foes[i];
			if (f.dwRace < PLAYERBOT_WIEZA_CHESS_MIN || f.dwRace > PLAYERBOT_WIEZA_CHESS_MAX)
				continue;
			((f.lX - bx) / 100 >= 92 ? right : left).push_back(&f);
		}
		for (size_t i = 0; i < right.size(); ++i)
		{
			const long rx = (right[i]->lX - bx) / 100, ry = (right[i]->lY - by) / 100;
			const TPlayerBotArzDgFoe* best = NULL;
			long bestD = 1000;
			for (size_t k = 0; k < left.size(); ++k)
			{
				const long lx = (left[k]->lX - bx) / 100, ly = (left[k]->lY - by) / 100;
				const long dd = std::abs(ry - ly) * 4 + std::abs(rx + lx - 183);
				if (std::abs(ry - ly) <= 3 && dd < bestD)
				{
					bestD = dd;
					best = left[k];
				}
			}
			if (best && best->dwRace != right[i]->dwRace)
			{
				a = right[i]->dwVID;
				b = best->dwVID;
				return true;
			}
		}
		return false;
	}

	// A piece of the tower no bot hits now: a Metin of the one-chance task but the chosen one, a chess piece but the odd
	// pair (before a wrong one), the circles' marker.
	bool IsPlayerBotWiezaNoTarget(LPCHARACTER c)
	{
		if (!c || c->IsPC() || !IsPlayerBotWiezaInstance(c->GetMapIndex()))
			return false;
		const DWORD race = c->GetRaceNum();
		if (race == PLAYERBOT_WIEZA_ZONE_MARK)
			return true;
		const bool metin = race == PLAYERBOT_WIEZA_METIN;
		const bool chess = race >= PLAYERBOT_WIEZA_CHESS_MIN && race <= PLAYERBOT_WIEZA_CHESS_MAX;
		if (!metin && !chess)
			return false;
		LPDUNGEON d = CDungeonManager::instance().FindByMapIndex(c->GetMapIndex());
		if (!d || d->GetFlag("room") != 2 || d->GetFlag("wrong") != 0 || d->GetFlag("phase") != 0)
			return false;
		const int task = d->GetFlag("task");
		if ((metin && task != 2) || (chess && task != 4))
			return false;
		std::map<long, std::pair<DWORD, DWORD> >::const_iterator p = s_mapPlayerBotWiezaPick.find(c->GetMapIndex());
		if (p == s_mapPlayerBotWiezaPick.end())
			return true;
		if (p->second.first == 0)
			return false;	// the odd pair not found: a person's guess - any piece
		const DWORD vid = (DWORD)c->GetVID();
		return vid != p->second.first && vid != p->second.second;
	}

	// The task's pick (task 2: one Metin at random; task 4: the odd pair), once a room.
	void PickPlayerBotWiezaTask(TPlayerBotDgRun& run, TPlayerBotWiezaRun& w, LPDUNGEON d, LPCHARACTER ch, DWORD dwNow)
	{
		if (d->GetFlag("room") != 2 || d->GetFlag("wrong") != 0 || s_mapPlayerBotWiezaPick.count(run.lInstance))
			return;
		const int task = d->GetFlag("task");
		if (task == 2)
		{
			std::vector<DWORD> metins;
			const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(run.lInstance, dwNow);
			for (size_t i = 0; i < scan.foes.size(); ++i)
				if (scan.foes[i].dwRace == PLAYERBOT_WIEZA_METIN)
					metins.push_back(scan.foes[i].dwVID);
			if (metins.empty())
				return;
			const DWORD pick = metins[number(0, (int)metins.size() - 1)];
			s_mapPlayerBotWiezaPick[run.lInstance] = std::make_pair(pick, pick);
			sys_log(0, "BOT_WIEZA: metin chosen run=%d name=%s floor=%d of=%u", run.iId, ch->GetName(), d->GetFlag("floor"),
					(unsigned int)metins.size());
		}
		else if (task == 4)
		{
			DWORD a = 0, b = 0;
			if (w.dwOddSince == 0)
				w.dwOddSince = dwNow;
			if (FindPlayerBotWiezaOddPair(run.lInstance, dwNow, a, b))
			{
				s_mapPlayerBotWiezaPick[run.lInstance] = std::make_pair(a, b);
				LPCHARACTER ca = CHARACTER_MANAGER::instance().Find(a), cb = CHARACTER_MANAGER::instance().Find(b);
				sys_log(0, "BOT_WIEZA: odd pair run=%d name=%s floor=%d races=%u/%u", run.iId, ch->GetName(), d->GetFlag("floor"),
						ca ? (unsigned int)ca->GetRaceNum() : 0U, cb ? (unsigned int)cb->GetRaceNum() : 0U);
			}
			else if (dwNow - w.dwOddSince > 60000)
			{
				// the board moved apart (a piece pulled away): the nearest pair is hit - a person's guess
				s_mapPlayerBotWiezaPick[run.lInstance] = std::make_pair(0U, 0U);
				sys_log(0, "BOT_WIEZA: odd pair not found run=%d name=%s floor=%d - guessing", run.iId, ch->GetName(), d->GetFlag("floor"));
			}
		}
	}

	LPCHARACTER PickPlayerBotWiezaFoe(LPCHARACTER ch, TPlayerBotDgRunBot& rb, LPDUNGEON d, int room, int task, DWORD dwNow)
	{
		const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(ch->GetMapIndex(), dwNow);
		const bool dodgeOnly = room == 2 && task == 3;
		const bool guess = room == 2 && task == 4 && d->GetFlag("wrong") == 0 && s_mapPlayerBotWiezaPick.count(ch->GetMapIndex()) &&
				s_mapPlayerBotWiezaPick[ch->GetMapIndex()].first == 0;
		LPCHARACTER threat = NULL, near = NULL;
		int dThreat = INT_MAX, dNear = INT_MAX;
		for (size_t i = 0; i < scan.foes.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().Find(scan.foes[i].dwVID);
			if (!IsPlayerBotPdgFoe(ch, c) || c->GetRaceNum() >= 20000 || c->GetRaceNum() == PLAYERBOT_WIEZA_ZONE_MARK)
				continue;
			if (guess && (c->GetRaceNum() < PLAYERBOT_WIEZA_CHESS_MIN || c->GetRaceNum() > PLAYERBOT_WIEZA_CHESS_MAX))
				continue;
			const int dist = DISTANCE_APPROX(ch->GetX() - c->GetX(), ch->GetY() - c->GetY());
			if (c->GetVictim() == ch && dist <= 1500 && dist < dThreat)
			{
				threat = c;
				dThreat = dist;
			}
			if (dodgeOnly || IsPlayerBotDgRunUnreachable(rb, (DWORD)c->GetVID(), dwNow))
				continue;
			if (dist < dNear)
			{
				near = c;
				dNear = dist;
			}
		}
		// the target in hand kept while it is still a foe here and nothing attacks the bot
		LPCHARACTER hand = ch->GetVictim();
		if (!threat && hand && IsPlayerBotPdgFoe(ch, hand) && hand->GetRaceNum() < 20000 && !dodgeOnly &&
				!IsPlayerBotDgRunUnreachable(rb, (DWORD)hand->GetVID(), dwNow))
			return hand;
		return threat ? threat : near;
	}

	// ------------------------------------------------------------ the bot's tick

	void UsePlayerBotWiezaPotion(LPCHARACTER ch, TPlayerBotWiezaRun& w, bool keepFull, DWORD dwNow)
	{
		if (ch->IsDead() || ch->GetMaxHP() <= 0 || (w.dwNextPotion && (int)(dwNow - w.dwNextPotion) < 0))
			return;
		const int pct = (int)((long long)ch->GetHP() * 100 / ch->GetMaxHP());
		DWORD order[4] = { 0, 0, 0, 0 };
		if (pct < 35)
		{
			order[0] = PLAYERBOT_WIEZA_POT_DRAGON;
			order[1] = PLAYERBOT_WIEZA_POT_LIFE;
			order[2] = PLAYERBOT_WIEZA_POT_WINE;
			order[3] = PLAYERBOT_WIEZA_POT_RED;
		}
		else if (pct < 60)
		{
			order[0] = PLAYERBOT_WIEZA_POT_WINE;
			order[1] = PLAYERBOT_WIEZA_POT_RED;
		}
		else if (pct < (keepFull ? 98 : 80))
		{
			order[0] = keepFull ? PLAYERBOT_WIEZA_POT_WINE : PLAYERBOT_WIEZA_POT_RED;
			order[1] = PLAYERBOT_WIEZA_POT_RED;
		}
		w.dwNextPotion = dwNow + 700;
		for (int i = 0; i < 4 && order[i]; ++i)
		{
			const int cell = FindPlayerBotTowerItemCell(ch, order[i]);
			if (cell < 0)
				continue;
			if (ch->UseItem(TItemPos(INVENTORY, (WORD)cell)))
			{
				++w.iPotions;
				w.dwNextPotion = dwNow + (order[i] == PLAYERBOT_WIEZA_POT_RED ? 1500 : 900);
				return;
			}
		}
	}

	bool DodgePlayerBotWiezaZones(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotWiezaRun& w, long anchorX, long anchorY, DWORD dwNow)
	{
		if (!ch->GetSectree())
			return false;
		const int avoid = GetPlayerBotWiezaEnv("PLAYERBOT_WIEZA_ZONE_AVOID", 650, 0, 1500);
		if (avoid <= 0)
			return false;
		FPlayerBotGlebieMarks marks(ch, 2400);	// the marker race 3975 - the same as Glebie's
		ch->GetSectree()->ForEachAround(marks);
		TPlayerBotWiezaDodge& dg = s_mapPlayerBotWiezaDodge[ch->GetPlayerID()];
		const int here = GetPlayerBotGlebieNearestMark(marks.m_pts, ch->GetX(), ch->GetY());
		if (dg.dwUntil && (int)(dg.dwUntil - dwNow) > 0 && DISTANCE_APPROX(ch->GetX() - dg.x, ch->GetY() - dg.y) > 150 &&
				GetPlayerBotGlebieNearestMark(marks.m_pts, dg.x, dg.y) > avoid)
		{
			if ((int)(dwNow - dg.dwNextMove) >= 0)
			{
				dg.dwNextMove = dwNow + 400;
				MovePlayerBot(ch, dg.x, dg.y, dwNow, 2, true, false);
			}
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
			return true;
		}
		dg.dwUntil = 0;
		if (here > avoid)
			return false;
		static const int dirX[16] = { 1000, 924, 707, 383, 0, -383, -707, -924, -1000, -924, -707, -383, 0, 383, 707, 924 };
		static const int dirY[16] = { 0, 383, 707, 924, 1000, 924, 707, 383, 0, -383, -707, -924, -1000, -924, -707, -383 };
		static const int rings[5] = { 750, 1000, 1300, 1700, 2200 };
		long bx = 0, by = 0;
		long long bestScore = -1;
		for (int r = 0; r < 5; ++r)
			for (int k = 0; k < 16; ++k)
			{
				const long px = ch->GetX() + (long)dirX[k] * (avoid + rings[r] - 620) / 1000;
				const long py = ch->GetY() + (long)dirY[k] * (avoid + rings[r] - 620) / 1000;
				if (!SECTREE_MANAGER::instance().IsMovablePosition(ch->GetMapIndex(), px, py))
					continue;
				if (GetPlayerBotGlebieNearestMark(marks.m_pts, px, py) <= avoid + 120)
					continue;
				const long long score = (long long)DISTANCE_APPROX(px - anchorX, py - anchorY) / 2 + (long long)rings[r];
				if (bestScore < 0 || score < bestScore)
				{
					bestScore = score;
					bx = px;
					by = py;
				}
			}
		if (bestScore < 0)
			return false;
		dg.x = bx;
		dg.y = by;
		dg.dwUntil = dwNow + PLAYERBOT_WIEZA_DODGE_MS;
		dg.dwNextMove = dwNow + 400;
		ch->SetVictim(NULL);
		state.dwTargetVID = 0;
		ClearPlayerBotRoute(state, false);
		MovePlayerBot(ch, bx, by, dwNow, 2, true, false);
		SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
		++w.iDodges;
		PlayerBotLogThrottled("wieza_dodge", dwNow, "BOT_WIEZA: dodge name=%s marks=%u nearest=%d hp=%d%% dodges=%d", ch->GetName(),
				(unsigned int)marks.m_pts.size(), here, ch->GetMaxHP() > 0 ? (int)((long long)ch->GetHP() * 100 / ch->GetMaxHP()) : 0,
				w.iDodges);
		return true;
	}

	void GetPlayerBotWiezaRoomSpot(long instance, int room, int task, long& x, long& y)
	{
		LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(instance);
		const long bx = pMap ? pMap->m_setting.iBaseX : 0, by = pMap ? pMap->m_setting.iBaseY : 0;
		const long* cell = PLAYERBOT_WIEZA_ROOM_A;
		if (room == 2)
			cell = task == 4 ? PLAYERBOT_WIEZA_ROOM_C : PLAYERBOT_WIEZA_MID_B;
		else if (room == 4)
			cell = PLAYERBOT_WIEZA_STAIRS;
		x = bx + cell[0] * 100;
		y = by + cell[1] * 100;
	}

	bool WalkPlayerBotWiezaTo(LPCHARACTER ch, TPlayerBotAIState& state, long x, long y, int near, DWORD dwNow)
	{
		if (DISTANCE_APPROX(ch->GetX() - x, ch->GetY() - y) <= near)
			return false;
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
		if ((int)(dwNow - state.dwNextTowerMoveTime) >= 0)
		{
			state.dwNextTowerMoveTime = dwNow + 800;
			MovePlayerBot(ch, x, y, dwNow, 4, true, false);
		}
		return true;
	}

	// The tasks' items: the keys used, the seal stones handed to the seals, the antidote used; what lies about picked up.
	bool ManagePlayerBotWiezaItems(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDgRun& run, TPlayerBotWiezaRun& w, LPDUNGEON d,
			int task, DWORD dwNow)
	{
		DWORD& next = s_mapPlayerBotYdgItemAt[ch->GetPlayerID()];
		if (next != 0 && (int)(next - dwNow) > 0)
			return false;
		next = dwNow + 700;
		DWORD want = 0;
		if (task == 5)
			want = PLAYERBOT_WIEZA_KEY;
		else if (task == 6)
			want = PLAYERBOT_WIEZA_SEAL_STONE;
		else if (task == 7)
			want = PLAYERBOT_WIEZA_ANTIDOTE;
		if (!want)
			return false;
		const int cell = FindPlayerBotTowerItemCell(ch, want);
		if (cell >= 0 && task == 5)
		{
			const bool ok = ch->UseItem(TItemPos(INVENTORY, (WORD)cell));
			++w.iKeysUsed;
			sys_log(0, "BOT_WIEZA: key used run=%d name=%s floor=%d ok=%d done=%d keys=%d", run.iId, ch->GetName(), d->GetFlag("floor"),
					ok ? 1 : 0, d->GetFlag("phase"), w.iKeysUsed);
			next = dwNow + 1500;
			return true;
		}
		if (cell >= 0 && task == 7 && d->GetFlag("cs1") >= GetPlayerBotWiezaEnv("PLAYERBOT_WIEZA_ANTIDOTE_AT", 3, 1, 10))
		{
			const int before = d->GetFlag("cs1");
			ch->UseItem(TItemPos(INVENTORY, (WORD)cell));
			++w.iAntidotes;
			sys_log(0, "BOT_WIEZA: antidote run=%d name=%s floor=%d curse=%d->%d", run.iId, ch->GetName(), d->GetFlag("floor"), before,
					d->GetFlag("cs1"));
			return true;
		}
		if (cell >= 0 && task == 6)
		{
			const int n = d->GetFlag("seal_n");
			if (n != w.iSealN)
			{
				w.iSealN = n;
				w.sealTried.clear();
			}
			FPlayerBotYdgNpc finder(ch, PLAYERBOT_WIEZA_SEAL, &w.sealTried);
			LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(ch->GetMapIndex());
			if (pMap)
				pMap->for_each(finder);
			LPCHARACTER seal = finder.m_found;
			if (!seal && !w.sealTried.empty())
			{
				w.sealTried.clear();	// all tried (one went back up?) - again
				return false;
			}
			if (seal)
			{
				const int dist = DISTANCE_APPROX(seal->GetX() - ch->GetX(), seal->GetY() - ch->GetY());
				if (dist > PLAYERBOT_YDG_GIVE_DISTANCE)
				{
					next = dwNow + 400;
					return WalkPlayerBotWiezaTo(ch, state, seal->GetX(), seal->GetY(), 300, dwNow) || true;
				}
				if (ch->IsStateMove())
					ch->Stop();
				const DWORD vid = (DWORD)seal->GetVID();
				const bool ok = ch->GiveItem(seal, TItemPos(INVENTORY, (WORD)cell));	// the seal may be gone now (npc.purge)
				const bool right = d->GetFlag("seal_n") != n;
				++w.iSealsGiven;
				if (!right)
				{
					++w.iSealsWrong;
					w.sealTried.insert(vid);
				}
				sys_log(0, "BOT_WIEZA: seal run=%d name=%s floor=%d step=%d ok=%d right=%d tried=%u", run.iId, ch->GetName(), d->GetFlag("floor"),
						n, ok ? 1 : 0, right ? 1 : 0, (unsigned int)w.sealTried.size());
				next = dwNow + 1200;
				return true;
			}
		}
		// what lies about: the task's item (not far from what attacks it)
		FPlayerBotYdgGround ground(ch);
		ground.m_vnums.push_back(want);
		ch->GetSectree()->ForEachAround(ground);
		if (!ground.m_found)
			return false;
		LPCHARACTER v = ch->GetVictim();
		if (ground.m_iBest > 900 && v && !v->IsDead() && v->GetVictim() == ch)
			return false;
		LPITEM item = ground.m_found;
		if (ch->GetEmptyInventory(1) < 0 && !HasPlayerBotYdgStackRoom(ch, item->GetVnum()) && !MakePlayerBotYdgRoom(ch, "wieza_ground"))
			return false;
		if (ground.m_iBest > PLAYERBOT_YDG_PICKUP_DISTANCE)
		{
			next = dwNow + 400;
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
			MovePlayerBot(ch, item->GetX(), item->GetY(), dwNow, 2, true, false);
			return true;
		}
		if (ch->IsStateMove())
			ch->Stop();
		const DWORD vnum = item->GetVnum();
		const bool ok = ch->PickupItem(item->GetVID());
		PlayerBotLogThrottled("wieza_pick", dwNow, "BOT_WIEZA: picked up run=%d name=%s vnum=%u task=%d ok=%d", run.iId, ch->GetName(),
				(unsigned int)vnum, task, ok ? 1 : 0);
		return true;
	}

	bool ManagePlayerBotWiezaInside(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotDgRun& run, TPlayerBotDgRunBot& rb, DWORD dwNow)
	{
		const TPlayerBotDgRunDef& def = PLAYERBOT_DGRUN_DEFS[run.iDef];
		LPDUNGEON d = ch->GetDungeon();
		if (!d)
		{
			d = CDungeonManager::instance().FindByMapIndex(ch->GetMapIndex());
			if (d)
				ch->SetDungeon(d);
		}
		std::map<int, TPlayerBotWiezaRun>::iterator wi = s_mapPlayerBotWiezaRuns.find(run.iId);
		if (!d || wi == s_mapPlayerBotWiezaRuns.end())
			return false;
		TPlayerBotWiezaRun& w = wi->second;
		state.lLastX = ch->GetX();
		state.lLastY = ch->GetY();
		// the quest's jump to another room (d.jump_all) leaves the route of the room before
		if (rb.lLastX != 0 && DISTANCE_APPROX(ch->GetX() - rb.lLastX, ch->GetY() - rb.lLastY) > 3000)
		{
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ClearPlayerBotRoute(state, true);
			if (ch->IsStateMove())
				ch->Stop();
		}
		rb.lLastX = ch->GetX();
		rb.lLastY = ch->GetY();
		if (d->GetFlag("closed") == 1 || d->GetFlag("init") != 1)
		{
			if (ch->IsStateMove())
				ch->Stop();
			SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
			return true;
		}
		if (ch->IsRiding() && SetPlayerBotRidingForTravel(ch, state, false, dwNow, "wieza"))
			return true;
		const int room = d->GetFlag("room"), phase = d->GetFlag("phase"), task = d->GetFlag("task");
		UsePlayerBotWiezaPotion(ch, w, room == 2 && task == 3, dwNow);
		if (d->GetFlag("countdown") > 0)
		{
			if (ch->IsStateMove())
				ch->Stop();
			SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
			return true;
		}
		long spotX = 0, spotY = 0;
		GetPlayerBotWiezaRoomSpot(run.lInstance, room, task, spotX, spotY);
		LPCHARACTER target = ch->GetVictim();
		if (DodgePlayerBotWiezaZones(ch, state, w, target ? target->GetX() : spotX, target ? target->GetY() : spotY, dwNow))
			return true;
		// the room done: the loot a moment, then the portal and its "Dalej"
		if (phase == 1)
		{
			if (dwNow - w.dwPhase1Since < PLAYERBOT_WIEZA_LOOT_MS && HandleLoot(ch, state, dwNow))
				return true;
			FPlayerBotYdgNpc finder(ch, PLAYERBOT_WIEZA_PORTAL, NULL);
			LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(ch->GetMapIndex());
			if (pMap)
				pMap->for_each(finder);
			LPCHARACTER portal = finder.m_found;
			if (!portal)
			{
				SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
				return true;
			}
			if (WalkPlayerBotWiezaTo(ch, state, portal->GetX(), portal->GetY(), 280, dwNow))
				return true;
			if (ch->IsStateMove())
				ch->Stop();
			SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
			if (w.dwNextCall == 0 || (int)(dwNow - w.dwNextCall) >= 0)
			{
				w.dwNextCall = dwNow + PLAYERBOT_WIEZA_PORTAL_CALL_MS;
				CallPlayerBotDgRunTimer(def.szNextTimer, run.lInstance);
				PlayerBotLogThrottled("wieza_portal", dwNow, "BOT_WIEZA: portal run=%d name=%s floor=%d room=%d", run.iId, ch->GetName(),
						d->GetFlag("floor"), room);
			}
			return true;
		}
		if (room == 2)
		{
			PickPlayerBotWiezaTask(run, w, d, ch, dwNow);
			if (ManagePlayerBotWiezaItems(ch, state, run, w, d, task, dwNow))
				return true;
		}
		LPCHARACTER foe = PickPlayerBotWiezaFoe(ch, rb, d, room, task, dwNow);
		if (!foe)
		{
			if (room != 2 || task != 3 || DISTANCE_APPROX(ch->GetX() - spotX, ch->GetY() - spotY) > 1500)
				if (WalkPlayerBotWiezaTo(ch, state, spotX, spotY, 600, dwNow))
					return true;
			if (ch->IsStateMove() && !(room == 2 && task == 3))
				ch->Stop();
			SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
			return true;
		}
		state.bLastNavOutcome = PLAYERBOT_NAV_OUT_NONE;
		const bool fought = FightPlayerBotTowerObjective(ch, state, foe, dwNow);
		if (state.bLastNavOutcome == PLAYERBOT_NAV_OUT_UNREACHABLE)
		{
			state.bLastNavOutcome = PLAYERBOT_NAV_OUT_NONE;
			ClearPlayerBotRoute(state, false);
			state.dwNextNavPlanTime = 0;
			MovePlayerBot(ch, foe->GetX(), foe->GetY(), dwNow, 24, true, false);
			if (state.bLastNavOutcome == PLAYERBOT_NAV_OUT_UNREACHABLE)
			{
				const DWORD race = foe->GetRaceNum();
				// a task's own piece is brought nearer (the cohort's unstick), anything else left alone a while
				if (race == PLAYERBOT_WIEZA_METIN || (race >= PLAYERBOT_WIEZA_CHESS_MIN && race <= PLAYERBOT_WIEZA_CHESS_MAX) || foe->IsStone() ||
						foe->GetMobRank() >= MOB_RANK_BOSS)
					UnstickPlayerBotArzDgFoe(ch, foe, ch->GetX(), ch->GetY(), dwNow);
				else
				{
					rb.unreachable[(DWORD)foe->GetVID()] = dwNow + PLAYERBOT_DGRUN_UNREACHABLE_MS;
					state.dwTargetVID = 0;
					ch->SetVictim(NULL);
				}
			}
		}
		return fought || true;
	}

	// ------------------------------------------------------------ the end

	// The training's own (below).
	void NotePlayerBotWiezaTraineeEnd(DWORD pid, int startFloor, int reached, bool died, const char* result);
	bool IsPlayerBotWiezaTrainee(DWORD pid);

	DWORD NotePlayerBotWiezaRunEnd(const TPlayerBotDgRun& run, const char* result, bool entered, DWORD tookS, DWORD rest)
	{
		std::map<int, TPlayerBotWiezaRun>::iterator it = s_mapPlayerBotWiezaRuns.find(run.iId);
		TPlayerBotWiezaRun w = it != s_mapPlayerBotWiezaRuns.end() ? it->second : TPlayerBotWiezaRun();
		if (it != s_mapPlayerBotWiezaRuns.end())
			s_mapPlayerBotWiezaRuns.erase(it);
		if (run.lInstance)
			s_mapPlayerBotWiezaPick.erase(run.lInstance);
		const DWORD pid = w.dwPid ? w.dwPid : (run.members.empty() ? 0 : run.members[0]);
		LPCHARACTER c = pid ? CHARACTER_MANAGER::instance().FindByPID(pid) : NULL;
		// what the climb was: died, time (a room's limit), top (floor 50), or the core's (abandoned, aborted, offline ...)
		const char* how = !entered ? (result ? result : "-") : (w.bFailed || w.iDeaths > 0 ? "died" :
				(w.iTopFloor >= PLAYERBOT_WIEZA_MAX_FLOOR ? "top" : (w.bClosed ? "time" : (result ? result : "-"))));
		long long gold = 0;
		int items = 0;
		if (c)
		{
			s_mapPlayerBotWiezaDodge.erase(pid);
			// the tower's task items stay in the tower (a person's are worth nothing outside either)
			static const DWORD taskItems[3] = { PLAYERBOT_WIEZA_KEY, PLAYERBOT_WIEZA_SEAL_STONE, PLAYERBOT_WIEZA_ANTIDOTE };
			for (int i = 0; i < 3; ++i)
			{
				const int n = (int)c->CountSpecifyItem(taskItems[i]);
				if (n > 0)
					c->RemoveSpecifyItem(taskItems[i], (ITEM_COUNT)n);
			}
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_POISON);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_BLEED);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_MONSTER);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_HP);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_CRIT);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_PIERCE);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_MOVE);
			c->RemoveAffect(AFFECT_PLAYERBOT_YDG_ATTSPD);
			for (int k = 0; k < 4; ++k)
				c->RemoveAffect(AFFECT_PLAYERBOT_YDG_SUNGMA[k]);
			if (entered && w.dwPid)
			{
				gold = (long long)c->GetGold() - w.llGoldAt;
				for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
					if (c->GetInventoryItem(cell))
						++items;
				items -= w.iItemsAt;
			}
			// the strength limit: the first floor of the climb not won again and again - a rest from the tower
			if (entered && w.dwPid)
			{
				if (w.iTopFloor >= w.iStartFloor)
				{
					c->SetQuestFlag("wieza_sung_mahi.bot_lim_n", 0);
					c->SetQuestFlag("wieza_sung_mahi.bot_lim_f", 0);
				}
				else
				{
					int n = c->GetQuestFlag("wieza_sung_mahi.bot_lim_f") == w.iStartFloor ? c->GetQuestFlag("wieza_sung_mahi.bot_lim_n") + 1 : 1;
					c->SetQuestFlag("wieza_sung_mahi.bot_lim_f", w.iStartFloor);
					c->SetQuestFlag("wieza_sung_mahi.bot_lim_n", n);
					const int fails = GetPlayerBotWiezaEnv("PLAYERBOT_WIEZA_LIMIT_FAILS", 3, 1, 50);
					if (n >= fails)
					{
						const int minutes = GetPlayerBotWiezaEnv("PLAYERBOT_WIEZA_LIMIT_REST_MIN", 120, 0, 24 * 60);
						c->SetQuestFlag("wieza_sung_mahi.bot_lim_until", (int)get_global_time() + minutes * 60);
						c->SetQuestFlag("wieza_sung_mahi.bot_lim_n", 0);
						sys_log(0, "BOT_WIEZA: limit pid=%u name=%s floor=%d fails=%d rest_min=%d best=%d level=%d champion=%d", pid, c->GetName(),
								w.iStartFloor, n, minutes, GetPlayerBotWiezaBest(c), (int)c->GetLevel(), GetPlayerBotChampionLevel(c));
					}
				}
			}
			// out of the hall (the quest's way out) back to the gathering, as long as the run lets the move through
			TPlayerBotAIState* state = GetPlayerBotDgRunState(pid);
			if (state && !c->IsDead() && (c->GetMapIndex() == PLAYERBOT_WIEZA_HALL || IsPlayerBotWiezaInstance(c->GetMapIndex())) &&
					run.place.map > 0)
			{
				const bool ok = TransitionPlayerBotMap(c, *state, run.place.map, run.place.x, run.place.y, get_dword_time(), "dungeon_run_out");
				sys_log(0, "BOT_WIEZA: out of the hall pid=%u name=%s ok=%d", pid, c->GetName(), ok ? 1 : 0);
			}
		}
		sys_log(0, "BOT_WIEZA: run end run=%d name=%s result=%s how=%s entered=%d took_s=%u start_floor=%d best_before=%d reached=%d "
				"floors_done=%d deaths=%d floor_s=%s task_fails=%s dodges=%d keys=%d seals=%d/%d antidotes=%d potions=%d potion_gold=%lld "
				"gold=%lld items=%d", run.iId, c ? c->GetName() : "?", result ? result : "-", how, entered ? 1 : 0, tookS, w.iStartFloor,
				w.iBestBefore, std::max(w.iFloor, w.iTopFloor), w.iFloorsDone, w.iDeaths, w.floorSecs.empty() ? "-" : w.floorSecs.c_str(),
				w.taskFails.empty() ? "-" : w.taskFails.c_str(), w.iDodges, w.iKeysUsed, w.iSealsGiven - w.iSealsWrong, w.iSealsGiven,
				w.iAntidotes, w.iPotions, w.llPotionGold, gold, items);
		FILE* fp = fopen(PLAYERBOT_WIEZA_RUNS_FILE, "a");
		if (fp)
		{
			fprintf(fp, "%ld\t%d\t%s\t%s\t%s\t%u\t%d\t%d\t%d\t%d\t%d\t%s\t%s\t%d\t%lld\t%d\n", (long)time(0), run.iId, c ? c->GetName() : "?",
					result ? result : "-", how, tookS, w.iStartFloor, w.iBestBefore, std::max(w.iFloor, w.iTopFloor), w.iFloorsDone, w.iDeaths,
					w.floorSecs.empty() ? "-" : w.floorSecs.c_str(), w.taskFails.empty() ? "-" : w.taskFails.c_str(), w.iPotions, gold, items);
			fclose(fp);
		}
		if (entered)
			NotePlayerBotWiezaTraineeEnd(pid, w.iStartFloor, std::max(w.iFloor, w.iTopFloor), !strcmp(how, "died"), how);
		// a bot climbing for it rests a moment only
		if (pid && IsPlayerBotWiezaTrainee(pid))
			return 30000 + (DWORD)number(0, 30000);
		return rest;
	}

	// ------------------------------------------------------------ the training (playerbot_wieza_train)

	struct TPlayerBotWiezaTrainBot
	{
		unsigned int runs, deaths, floors;
		int best, lastStart, lastReached;
		std::string last;
		TPlayerBotWiezaTrainBot() : runs(0), deaths(0), floors(0), best(0), lastStart(0), lastReached(0) {}
	};

	struct TPlayerBotWiezaTrain
	{
		bool bFile;
		time_t tMtime;
		int iSolo, iCap;
		std::vector<DWORD> fixed;
		TPlayerBotWiezaTrain() : bFile(false), tMtime(0), iSolo(0), iCap(0) {}
	};
	TPlayerBotWiezaTrain s_kPlayerBotWiezaTrain;
	std::set<DWORD> s_setPlayerBotWiezaTrainees;
	std::map<DWORD, TPlayerBotWiezaTrainBot> s_mapPlayerBotWiezaTrainStats;
	std::map<int, DWORD> s_mapPlayerBotWiezaTrainRuns;	// run -> pid
	DWORD s_dwPlayerBotWiezaNextPick = 0;

	bool IsPlayerBotWiezaTrainee(DWORD pid)
	{
		return !s_setPlayerBotWiezaTrainees.empty() && s_setPlayerBotWiezaTrainees.count(pid) != 0;
	}

	void NotePlayerBotWiezaTraineeEnd(DWORD pid, int startFloor, int reached, bool died, const char* result)
	{
		if (!IsPlayerBotWiezaTrainee(pid))
			return;
		TPlayerBotWiezaTrainBot& s = s_mapPlayerBotWiezaTrainStats[pid];
		++s.runs;
		s.deaths += died ? 1 : 0;
		s.floors += (unsigned int)std::max(0, reached - startFloor + (died ? 0 : 1));
		s.best = std::max(s.best, reached);
		s.lastStart = startFloor;
		s.lastReached = reached;
		s.last = result ? result : "-";
	}

	void LoadPlayerBotWiezaTrainFile()
	{
		struct stat st;
		if (stat(PLAYERBOT_WIEZA_TRAIN_FILE, &st) != 0)
		{
			if (s_kPlayerBotWiezaTrain.bFile)
			{
				sys_log(0, "BOT_WIEZA: train file gone - the trainees free");
				s_setPlayerBotWiezaTrainees.clear();
			}
			s_kPlayerBotWiezaTrain = TPlayerBotWiezaTrain();
			return;
		}
		if (s_kPlayerBotWiezaTrain.bFile && st.st_mtime == s_kPlayerBotWiezaTrain.tMtime)
			return;
		TPlayerBotWiezaTrain t;
		t.bFile = true;
		t.tMtime = st.st_mtime;
		FILE* fp = fopen(PLAYERBOT_WIEZA_TRAIN_FILE, "r");
		if (!fp)
			return;
		char line[512];
		while (fgets(line, sizeof(line), fp))
		{
			std::vector<std::string> w;
			char* save = NULL;
			for (char* tok = strtok_r(line, " \t\r\n", &save); tok; tok = strtok_r(NULL, " \t\r\n", &save))
				w.push_back(tok);
			if (w.empty() || w[0][0] == '#')
				continue;
			if (w[0] == "solo" && w.size() >= 2)
				t.iSolo = std::max(0, std::min(atoi(w[1].c_str()), 60));
			else if (w[0] == "cap" && w.size() >= 2)
				t.iCap = std::max(0, std::min(atoi(w[1].c_str()), 60));
			else if (w[0] == "bot")
				for (size_t i = 1; i < w.size(); ++i)
				{
					const DWORD pid = (DWORD)strtoul(w[i].c_str(), NULL, 10);
					if (pid && std::find(t.fixed.begin(), t.fixed.end(), pid) == t.fixed.end())
						t.fixed.push_back(pid);
				}
			else
				sys_log(0, "BOT_WIEZA: train line unknown: %s", w[0].c_str());
		}
		fclose(fp);
		s_kPlayerBotWiezaTrain = t;
		s_setPlayerBotWiezaTrainees.clear();
		s_dwPlayerBotWiezaNextPick = 0;
		sys_log(0, "BOT_WIEZA: train file loaded solo=%d fixed=%u cap=%d", t.iSolo, (unsigned int)t.fixed.size(), t.iCap);
	}

	// Free for the tower's training: no other role that holds the bot.
	bool IsPlayerBotWiezaTrainCandidate(DWORD pid, LPCHARACTER ch)
	{
		if (!ch || !ch->GetDesc() || !ch->GetDesc()->IsBot() || ch->GetEmpire() < 1 || ch->GetEmpire() > 3)
			return false;
		if (s_setPlayerBotYdgTrainees.count(pid) || IsPlayerBotYoharaHydraResident(pid) || IsPlayerBotErebuTrainee(pid) ||
				IsPlayerBotDropkiActive(pid) || IsPlayerBotMeleyVisitor(pid) || IsPlayerBotYoharaSzcResident(pid))
			return false;
		return IsPlayerBotWiezaFit(ch);
	}

	// The n strongest eligible (ScorePlayerBotYdg) of this core; those climbing now kept.
	void PickPlayerBotWiezaTrainees(DWORD dwNow)
	{
		const TPlayerBotWiezaTrain& t = s_kPlayerBotWiezaTrain;
		std::set<DWORD> keep;
		for (size_t i = 0; i < t.fixed.size(); ++i)
			keep.insert(t.fixed[i]);
		int solo = 0;
		for (std::set<DWORD>::const_iterator it = s_setPlayerBotWiezaTrainees.begin(); it != s_setPlayerBotWiezaTrainees.end(); ++it)
		{
			if (keep.count(*it))
				continue;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(*it);
			const bool climbing = s_mapPlayerBotDgRunBots.count(*it) != 0;
			if (climbing || (ch && ch->GetDesc() && IsPlayerBotWiezaFit(ch)))
			{
				if (solo < t.iSolo)
				{
					keep.insert(*it);
					++solo;
				}
			}
		}
		std::vector<std::pair<long long, DWORD> > pool;
		if (solo < t.iSolo)
			for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
			{
				if (keep.count(it->first))
					continue;
				LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
				if (!IsPlayerBotWiezaTrainCandidate(it->first, ch))
					continue;
				pool.push_back(std::make_pair(ScorePlayerBotYdg(ch), it->first));
			}
		std::sort(pool.begin(), pool.end(), [](const std::pair<long long, DWORD>& a, const std::pair<long long, DWORD>& b)
				{ return a.first > b.first; });
		std::string added;
		for (size_t i = 0; i < pool.size() && solo < t.iSolo; ++i, ++solo)
		{
			keep.insert(pool[i].second);
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pool[i].second);
			char buf[96];
			snprintf(buf, sizeof(buf), "%s%s(%u/%d/c%d/best%d)", added.empty() ? "" : ",", ch ? ch->GetName() : "?", pool[i].second,
					ch ? (int)ch->GetLevel() : 0, ch ? GetPlayerBotChampionLevel(ch) : 0, ch ? GetPlayerBotWiezaBest(ch) : 0);
			added += buf;
		}
		if (keep != s_setPlayerBotWiezaTrainees)
			sys_log(0, "BOT_WIEZA: train pick trainees=%u solo=%d/%d fixed=%u added=%s", (unsigned int)keep.size(), solo, t.iSolo,
					(unsigned int)t.fixed.size(), added.empty() ? "-" : added.c_str());
		s_setPlayerBotWiezaTrainees = keep;
		(void)dwNow;
	}

	int CountPlayerBotWiezaTrainRuns()
	{
		int n = 0;
		for (std::map<int, DWORD>::iterator it = s_mapPlayerBotWiezaTrainRuns.begin(); it != s_mapPlayerBotWiezaTrainRuns.end();)
		{
			if (!s_mapPlayerBotDgRuns.count(it->first))
				s_mapPlayerBotWiezaTrainRuns.erase(it++);
			else
			{
				++n;
				++it;
			}
		}
		return n;
	}

	int GetPlayerBotWiezaDef()
	{
		static int s_iDef = -2;
		if (s_iDef == -2)
		{
			s_iDef = -1;
			for (int i = 0; i < PLAYERBOT_DGRUN_DEF_COUNT; ++i)
				if (PLAYERBOT_DGRUN_DEFS[i].bKind == DGRUN_KIND_WIEZA)
					s_iDef = i;
		}
		return s_iDef;
	}

	void LogPlayerBotWiezaTrainStatus()
	{
		std::string line;
		for (std::set<DWORD>::const_iterator it = s_setPlayerBotWiezaTrainees.begin(); it != s_setPlayerBotWiezaTrainees.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(*it);
			const TPlayerBotWiezaTrainBot& s = s_mapPlayerBotWiezaTrainStats[*it];
			char buf[160];
			snprintf(buf, sizeof(buf), "%s%s:runs%u/deaths%u/floors%u/best%d/season_best%d/last%d-%d:%s%s", line.empty() ? "" : " ",
					ch ? ch->GetName() : "offline", s.runs, s.deaths, s.floors, s.best, ch ? GetPlayerBotWiezaBest(ch) : 0, s.lastStart,
					s.lastReached, s.last.empty() ? "-" : s.last.c_str(), s_mapPlayerBotDgRunBots.count(*it) ? "(climbing)" : "");
			if (line.size() < 1800)
				line += buf;
		}
		sys_log(0, "BOT_WIEZA: train status trainees=%u running=%d solo=%d cap=%d %s", (unsigned int)s_setPlayerBotWiezaTrainees.size(),
				CountPlayerBotWiezaTrainRuns(), s_kPlayerBotWiezaTrain.iSolo, s_kPlayerBotWiezaTrain.iCap, line.empty() ? "-" : line.c_str());
	}

	void PlanPlayerBotWiezaTraining(DWORD dwNow, bool forced)
	{
		static DWORD s_dwNextFile = 0, s_dwNextPlan = 0, s_dwNextStatus = 0;
		if (forced || s_dwNextFile == 0 || (int)(dwNow - s_dwNextFile) >= 0)
		{
			s_dwNextFile = dwNow + PLAYERBOT_WIEZA_TRAIN_FILE_MS;
			LoadPlayerBotWiezaTrainFile();
		}
		if (!s_kPlayerBotWiezaTrain.bFile)
			return;
		if (!forced && s_dwNextPlan != 0 && (int)(dwNow - s_dwNextPlan) < 0)
			return;
		s_dwNextPlan = dwNow + PLAYERBOT_WIEZA_TRAIN_PLAN_MS;
		if (s_dwPlayerBotWiezaNextPick == 0 || (int)(dwNow - s_dwPlayerBotWiezaNextPick) >= 0)
		{
			s_dwPlayerBotWiezaNextPick = dwNow + PLAYERBOT_WIEZA_TRAIN_PICK_MS;
			PickPlayerBotWiezaTrainees(dwNow);
		}
		if (s_dwNextStatus == 0 || (int)(dwNow - s_dwNextStatus) >= 0)
		{
			s_dwNextStatus = dwNow + PLAYERBOT_WIEZA_STATUS_MS;
			LogPlayerBotWiezaTrainStatus();
		}
		const int def = GetPlayerBotWiezaDef();
		if (def < 0 || !IsPlayerBotDgRunOn(dwNow) || quest::CQuestManager::instance().GetEventFlag("m2_bot_wieza_train_off") != 0)
			return;
		const TPlayerBotDgRunDef& info = PLAYERBOT_DGRUN_DEFS[def];
		if (!IsPlayerBotMapHostedHere(info.lMap) || !SECTREE_MANAGER::instance().GetMap(info.lMap))
		{
			PlayerBotLogThrottled("wieza_train_host", dwNow, "BOT_WIEZA: train - the tower (387) is not hosted on this core");
			return;
		}
		const int cap = s_kPlayerBotWiezaTrain.iCap > 0 ? s_kPlayerBotWiezaTrain.iCap :
				s_kPlayerBotWiezaTrain.iSolo + (int)s_kPlayerBotWiezaTrain.fixed.size();
		int running = CountPlayerBotWiezaTrainRuns();
		bool picked = false;
		for (std::set<DWORD>::const_iterator it = s_setPlayerBotWiezaTrainees.begin(); it != s_setPlayerBotWiezaTrainees.end() && running < cap; ++it)
		{
			const DWORD pid = *it;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(pid);
			TPlayerBotAIState* state = GetPlayerBotDgRunState(pid);
			if (!ch || !state || !ch->GetDesc() || !ch->GetDesc()->IsBot() || ch->IsDead() || s_mapPlayerBotDgRunBots.count(pid))
				continue;
			if (!IsPlayerBotWiezaFit(ch))
			{
				if (!picked && !std::count(s_kPlayerBotWiezaTrain.fixed.begin(), s_kPlayerBotWiezaTrain.fixed.end(), pid))
				{
					s_dwPlayerBotWiezaNextPick = dwNow;	// another one for it at the next pass
					picked = true;
				}
				continue;
			}
			std::map<DWORD, DWORD>::const_iterator rest = s_mapPlayerBotDgRunRest.find(pid);
			if (rest != s_mapPlayerBotDgRunRest.end() && (int)(rest->second - dwNow) > 0)
				continue;
			if (!CanPlayerBotWiezaPay(ch))
			{
				PlayerBotLogThrottled("wieza_train_banner", dwNow, "BOT_WIEZA: train waits - no banner and no gold pid=%u name=%s gold=%lld",
						pid, ch->GetName(), (long long)ch->GetGold());
				continue;
			}
			if (const char* refusal = GetPlayerBotDgRunRefusal(ch, *state, dwNow))
			{
				BreakOffPlayerBotDgRunTrainee(ch, *state, refusal, dwNow);
				PlayerBotLogThrottled("wieza_train_refusal", dwNow, "BOT_WIEZA: train waits pid=%u name=%s why=%s", pid, ch->GetName(), refusal);
				continue;
			}
			const BYTE empire = ch->GetEmpire();
			if (empire < 1 || empire > 3)
				continue;
			TPlayerBotDgRunSlot slot;
			slot.lvMin = PLAYERBOT_WIEZA_MIN_LEVEL;
			slot.lvMax = gPlayerMaxLevel;
			slot.partyMin = 1;
			slot.partyMax = 1;
			slot.panel = mt2009_dpanel::FindKey(info.szKey);
			if (!ResolvePlayerBotLfgPlace(info.szKey, 0, empire, PLAYERBOT_WIEZA_MIN_LEVEL, slot.place[empire]))
			{
				PlayerBotLogThrottled("wieza_train_place", dwNow, "BOT_WIEZA: train - no entrance here (the panel's row wieza_smh)");
				return;
			}
			slot.ok = slot.empireOk[empire] = true;
			std::vector<playerbot_dgrun::TCand> one;
			one.push_back(playerbot_dgrun::TCand(pid, ch->GetLevel(), ch->GetJob(), 10, ch->GetJob() == JOB_SHAMAN && ch->GetSkillGroup() != 0));
			const int id = OpenPlayerBotDgRun(def, empire, one, slot, 1, dwNow, "wieza_train");
			if (id == 0)
				continue;
			s_mapPlayerBotWiezaTrainRuns[id] = pid;
			++running;
			sys_log(0, "BOT_WIEZA: train called run=%d pid=%u name=%s level=%d champion=%d best=%d floor=%d running=%d/%d", id, pid,
					ch->GetName(), (int)ch->GetLevel(), GetPlayerBotChampionLevel(ch), GetPlayerBotWiezaBest(ch), GetPlayerBotWiezaStartFloor(ch),
					running, cap);
		}
	}

	bool RunPlayerBotWiezaTestLine(const char* cmd, DWORD dwNow)
	{
		if (!cmd || strcmp(cmd, "wieza_status"))
			return false;
		LogPlayerBotWiezaTrainStatus();
		(void)dwNow;
		return true;
	}
}

#endif
