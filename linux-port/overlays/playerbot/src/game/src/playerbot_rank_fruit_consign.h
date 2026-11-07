#ifndef __INC_METIN2_PLAYERBOT_RANK_FRUIT_CONSIGN_H__
#define __INC_METIN2_PLAYERBOT_RANK_FRUIT_CONSIGN_H__

// MT2009_PLUS_RANK_FRUIT_CONSIGN_V1 - the rank fruits of the bots that have no counter reach one (the owner,
// 7 November 2026: the fruits 80050-80054 visible on the bots' market).
//
// What the test world showed (7 November, 10:30, the census "PLAYERBOT_RANK_FRUIT:" and the bags in player.item):
//   * channel 1 game1: Gruszki owned 2 142, kept 37, surplus 2 105 - and 138 on the counters; Arbuzy surplus 826,
//     92 on the counters; channel 2 game1: Gruszki surplus 3 879, Winogrona 989, Arbuzy 1 246 - and no counter at all
//     (the shops are the first channel's, PlayerBotCanOpenShop);
//   * who holds it: the Arezzo dungeon cohort (playerbot_arezzo_dungeon_bots.h, 47 bots on 365/366): 5 685 of the
//     6 174 Gruszki in all the bots' bags (~5 500 over their keep), 2 754 Winogrona and 3 176 Arbuzy (~1 400 and
//     ~1 600 over their keep), in 2 862 bag lines - and not one of the 47 has an offline counter: they live in their
//     dungeon's lobby for good, never serve a counter, and the economy's rule ("a bot with no counter keeps its
//     surplus for one unless its bag is under pressure", playerbot_economy.h) kept it in the bag. Their Scorpion
//     Metins (9696, level 68) and the Jungle's bosses drop the fruits the rest of the world eats: 1 337 bots under
//     their goal were due a Gruszka.
//
// Now a bot whose fruit can not reach a counter of its own - no counter possible (the second channel, a sidekick
// aside), a member of the Arezzo dungeon cohort, or no counter yet and a bag under pressure - hands its surplus
// (above GetPlayerBotRankFruitKeep: the goal's need, the 5 Jablka, the craft's seven and what it bought for crafts -
// the owner's rules unchanged) to a consignment: player.playerbot_rank_fruit_consign, a row a lot, the bank between
// two cores (a cohort bot on channel 2's game1 and a trader on channel 1 never meet). A trader bot (the MERCHANT
// personality: no rank goal, it lists every fruit) of the first channel with its offline counter takes a lot into
// its bag and pays the courier PLAYERBOT_FRUIT_CONSIGN_PAY_PCT percent of the fruit's list unit
// (GetPlayerBotRankFruitListUnit) - no more than half of what it can spare; the courier collects that yang at its
// next look on whatever core it plays. The trader's counter service lists the fruit like any other it holds.
//
// Item safety: the courier's pieces leave its bag first, the row is written synchronously after; a row that can not
// be written gives the pieces back. The trader claims a row with "UPDATE .. WHERE state=0" (one core wins) and only
// with the room for every piece in its bag.
//
// Switch: event flag m2_bot_fruit_consign_off 1 (no new lot, nothing taken; what is queued waits, the yang owed is
// still collected). m2_bot_fruit_consign_min N: the smallest lot (default 10). m2_bot_fruit_consign_pay_pct N (1-100):
// the trader's price share. Lines: "PLAYERBOT_FRUIT_CONSIGN: census ..." every 10 minutes a core, and throttled
// "PLAYERBOT_FRUIT_CONSIGN: deposit|take|collect ...".
//
// An implementation fragment in the sense playerbot_types.h describes: included once, from playerbot_manager.cpp,
// after playerbot_farmer_link.h (its query helpers) and playerbot_offline_shop.h.

namespace
{
	const int PLAYERBOT_FRUIT_CONSIGN_MIN_LOT = 10;
	const int PLAYERBOT_FRUIT_CONSIGN_MAX_LOT = 200;
	const int PLAYERBOT_FRUIT_CONSIGN_LOTS_A_LOOK = 3;
	const int PLAYERBOT_FRUIT_CONSIGN_PAY_PCT = 50;
	const int PLAYERBOT_FRUIT_CONSIGN_PURSE_PCT = 50;
	const int PLAYERBOT_FRUIT_CONSIGN_TRADER_HOLD = 200;	// a trader takes no more of a fruit while it holds this many
	const int PLAYERBOT_FRUIT_CONSIGN_TRADER_FREE_CELLS = 12;
	const DWORD PLAYERBOT_FRUIT_CONSIGN_COURIER_MIN_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_FRUIT_CONSIGN_COURIER_MAX_MS = 20 * 60 * 1000;
	const DWORD PLAYERBOT_FRUIT_CONSIGN_TRADER_MIN_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_FRUIT_CONSIGN_TRADER_MAX_MS = 4 * 60 * 1000;
	const DWORD PLAYERBOT_FRUIT_CONSIGN_CORE_TAKE_MS = 15000;	// one trader's claim a core this often at most
	const DWORD PLAYERBOT_FRUIT_CONSIGN_CENSUS_MS = 10 * 60 * 1000;

	struct TPlayerBotFruitConsignBot
	{
		DWORD nextLook;
		bool owed;			// a lot of its not yet paid out (its deposit, or the core's list of the owed)
		TPlayerBotFruitConsignBot() : nextLook(0), owed(false) {}
	};
	std::map<DWORD, TPlayerBotFruitConsignBot> s_mapPlayerBotFruitConsign;
	// The couriers with a lot not collected yet, read from the table at a core's start and every census - a courier
	// on another core than the one it deposited on asks only then, every other bot never.
	std::set<DWORD> s_setPlayerBotFruitConsignOwed;
	DWORD s_dwPlayerBotFruitConsignOwedAt = 0;

	bool s_bPlayerBotFruitConsignTable = false;
	DWORD s_dwPlayerBotFruitConsignTableTry = 0;
	DWORD s_dwPlayerBotFruitConsignCoreTake = 0;
	DWORD s_dwPlayerBotFruitConsignCensusAt = 0;
	unsigned long long s_aPlayerBotFruitConsignDeposited[mt2009_rankp::FRUIT_COUNT];
	unsigned long long s_aPlayerBotFruitConsignTaken[mt2009_rankp::FRUIT_COUNT];
	unsigned int s_uPlayerBotFruitConsignLots = 0, s_uPlayerBotFruitConsignTakes = 0, s_uPlayerBotFruitConsignCollects = 0;
	unsigned int s_uPlayerBotFruitConsignFailed = 0, s_uPlayerBotFruitConsignRaced = 0;
	unsigned int s_uPlayerBotFruitConsignCouriers = 0, s_uPlayerBotFruitConsignTraders = 0;
	long long s_llPlayerBotFruitConsignPaid = 0, s_llPlayerBotFruitConsignCollected = 0;

	bool IsPlayerBotFruitConsignOn()
	{
		return mt2009_rankp::Enabled() && IsPlayerBotRankFruitGoalOn() &&
				mt2009_rankp::BotFruitOn(mt2009_rankp::BOT_FRUIT_CONSIGN);
	}

	int GetPlayerBotFruitConsignFlag(const char* name, int def, int lo, int hi)
	{
		const int flag = quest::CQuestManager::instance().GetEventFlag(name);
		return flag > 0 ? std::max(lo, std::min(flag, hi)) : def;
	}

	bool EnsurePlayerBotFruitConsignTable(DWORD dwNow)
	{
		if (s_bPlayerBotFruitConsignTable)
			return true;
		if (s_dwPlayerBotFruitConsignTableTry != 0 && dwNow - s_dwPlayerBotFruitConsignTableTry < 60000)
			return false;
		s_dwPlayerBotFruitConsignTableTry = dwNow ? dwNow : 1;
		std::unique_ptr<SQLMsg> msg(PlayerBotFarmerQuery(
				"CREATE TABLE IF NOT EXISTS player.playerbot_rank_fruit_consign ("
				"id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, "
				"created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
				"from_pid INT UNSIGNED NOT NULL, "
				"channel TINYINT UNSIGNED NOT NULL DEFAULT 0, "
				"vnum INT UNSIGNED NOT NULL, "
				"count INT UNSIGNED NOT NULL, "
				"state TINYINT UNSIGNED NOT NULL DEFAULT 0, "
				"taker_pid INT UNSIGNED NOT NULL DEFAULT 0, "
				"taken_at DATETIME NULL, "
				"paid BIGINT UNSIGNED NOT NULL DEFAULT 0, "
				"collected TINYINT UNSIGNED NOT NULL DEFAULT 0, "
				"KEY state_idx (state, id), KEY from_idx (from_pid, state, collected)) ENGINE=InnoDB"));
		s_bPlayerBotFruitConsignTable = PlayerBotFarmerSqlOk(msg);
		if (!s_bPlayerBotFruitConsignTable)
			sys_err("PLAYERBOT_FRUIT_CONSIGN: the table cannot be created errno=%u", msg.get() ? msg->uiSQLErrno : 0U);
		return s_bPlayerBotFruitConsignTable;
	}

	// A courier: its fruit can not reach a counter of its own.
	bool IsPlayerBotFruitConsignCourier(LPCHARACTER ch)
	{
		if (!ch || IsPlayerBotSidekickPID(ch->GetPlayerID()) ||
				GetPlayerBotPersonalityByPID(ch->GetPlayerID()) == BOT_PERSONALITY_MERCHANT)
			return false;
		if (!PlayerBotHasCounter(ch) || IsPlayerBotArezzoDungeonCohortPID(ch->GetPlayerID()))
			return true;
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		return !HasPlayerBotOfflineShop(ch) && IsPlayerBotBagUnderPressure(ch);
#else
		return false;
#endif
	}

	// A trader that lists what it takes: the MERCHANT personality, a counter of its own on this (the first) channel.
	bool IsPlayerBotFruitConsignTrader(LPCHARACTER ch)
	{
		if (!ch || GetPlayerBotPersonalityByPID(ch->GetPlayerID()) != BOT_PERSONALITY_MERCHANT ||
				IsPlayerBotSidekickPID(ch->GetPlayerID()) || !PlayerBotHasCounter(ch))
			return false;
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		return HasPlayerBotOfflineShop(ch);
#else
		return false;
#endif
	}

	void LoadPlayerBotFruitConsignOwed(DWORD dwNow)
	{
		s_dwPlayerBotFruitConsignOwedAt = dwNow ? dwNow : 1;
		std::unique_ptr<SQLMsg> msg(PlayerBotFarmerQuery(
				"SELECT DISTINCT from_pid FROM player.playerbot_rank_fruit_consign WHERE collected=0 LIMIT 5000"));
		if (!PlayerBotFarmerSqlOk(msg) || !msg->Get()->pSQLResult)
			return;
		MYSQL_ROW row;
		while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			unsigned int pid = 0;
			str_to_number(pid, row[0]);
			if (pid)
				s_setPlayerBotFruitConsignOwed.insert(pid);
		}
	}

	// The yang owed to a courier for its lots taken, as much as its purse may hold. Its lots still queued keep it
	// owed (b.owed), so it asks again at its next look.
	void CollectPlayerBotFruitConsign(LPCHARACTER ch, TPlayerBotFruitConsignBot& b, DWORD dwNow)
	{
		std::unique_ptr<SQLMsg> msg(PlayerBotFarmerQuery(
				"SELECT id, paid, state FROM player.playerbot_rank_fruit_consign WHERE from_pid=%u AND collected=0 "
				"ORDER BY id LIMIT 100", ch->GetPlayerID()));
		if (!PlayerBotFarmerSqlOk(msg) || !msg->Get()->pSQLResult)
			return;
		const long long room = GetPlayerBotFarmerGoldCap(ch) - 1 - (long long)ch->GetGold();
		long long sum = 0;
		std::string ids;
		int rows = 0, waiting = 0;
		MYSQL_ROW row;
		while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			unsigned int id = 0, state = 0;
			long long paid = 0;
			str_to_number(id, row[0]);
			str_to_number(paid, row[1]);
			str_to_number(state, row[2]);
			if (!id)
				continue;
			if (state != 1 || sum + paid > room)
			{
				++waiting;
				continue;
			}
			sum += paid;
			char one[16];
			snprintf(one, sizeof(one), "%s%u", ids.empty() ? "" : ",", id);
			ids += one;
			++rows;
		}
		b.owed = waiting > 0;
		if (!b.owed)
			s_setPlayerBotFruitConsignOwed.erase(ch->GetPlayerID());
		if (rows == 0)
			return;
		std::unique_ptr<SQLMsg> mark(PlayerBotFarmerQuery(
				"UPDATE player.playerbot_rank_fruit_consign SET collected=1 WHERE from_pid=%u AND collected=0 AND state=1 "
				"AND id IN (%s)", ch->GetPlayerID(), ids.c_str()));
		if (!PlayerBotFarmerSqlOk(mark) || (int)mark->Get()->uiAffectedRows != rows)
		{
			sys_err("PLAYERBOT_FRUIT_CONSIGN: collect mark failed pid=%u rows=%d affected=%u", ch->GetPlayerID(), rows,
					PlayerBotFarmerSqlOk(mark) ? (unsigned int)mark->Get()->uiAffectedRows : 0U);
			return;	// nothing paid: a row half marked is the operator's (the log names it)
		}
		if (sum > 0)
		{
			PlayerBotChangeGold(ch, sum);
			LogManager::instance().CharLog(ch, (DWORD)std::min<long long>(sum, 0xFFFFFFFFLL), "PLAYERBOT_FRUIT_CONSIGN_RECV", "");
		}
		++s_uPlayerBotFruitConsignCollects;
		s_llPlayerBotFruitConsignCollected += sum;
		PlayerBotLogThrottled("fruit_consign_collect", dwNow,
				"PLAYERBOT_FRUIT_CONSIGN: collect pid=%u name=%s lots=%d yang=%lld gold=%lld",
				ch->GetPlayerID(), ch->GetName(), rows, sum, (long long)ch->GetGold());
	}

	// The courier's look: its surplus of each fruit, a lot a fruit, PLAYERBOT_FRUIT_CONSIGN_LOTS_A_LOOK at most.
	void DepositPlayerBotFruitConsign(LPCHARACTER ch, TPlayerBotFruitConsignBot& b, DWORD dwNow)
	{
		using namespace mt2009_rankp;
		const int minLot = GetPlayerBotFruitConsignFlag("m2_bot_fruit_consign_min", PLAYERBOT_FRUIT_CONSIGN_MIN_LOT, 1,
				PLAYERBOT_FRUIT_CONSIGN_MAX_LOT);
		int lots = 0;
		for (int i = FRUIT_COUNT - 1; i >= 0 && lots < PLAYERBOT_FRUIT_CONSIGN_LOTS_A_LOOK; --i)
		{
			const DWORD vnum = FRUITS[i].vnum;
			const int held = (int)ch->CountSpecifyItem(vnum);
			const int keep = IsPlayerBotRankFruitEater(ch) ? GetPlayerBotRankFruitKeep(ch, vnum) : 0;
			if (keep >= 1000000)
				return;	// its points not read yet: nothing goes
			const int surplus = held - std::max(0, keep);
			if (surplus < minLot)
				continue;
			const int lot = std::min(surplus, PLAYERBOT_FRUIT_CONSIGN_MAX_LOT);
			ch->RemoveSpecifyItem(vnum, (ITEM_COUNT)lot);
			const int removed = held - (int)ch->CountSpecifyItem(vnum);
			if (removed <= 0)
				continue;
			std::unique_ptr<SQLMsg> msg(PlayerBotFarmerQuery(
					"INSERT INTO player.playerbot_rank_fruit_consign (from_pid, channel, vnum, count) VALUES (%u, %u, %u, %d)",
					ch->GetPlayerID(), (unsigned int)g_bChannel, vnum, removed));
			if (!PlayerBotFarmerSqlOne(msg))
			{
				// the row is not there: the pieces back where they were
				for (int left = removed; left > 0;)
				{
					const int part = std::min(left, PLAYERBOT_FRUIT_CONSIGN_MAX_LOT);
					ch->AutoGiveItem(vnum, (ITEM_COUNT)part, -1, false);
					left -= part;
				}
				++s_uPlayerBotFruitConsignFailed;
				PlayerBotErrThrottled("fruit_consign_insert", dwNow,
						"PLAYERBOT_FRUIT_CONSIGN: deposit failed pid=%u vnum=%u count=%d errno=%u, given back",
						ch->GetPlayerID(), vnum, removed, msg.get() ? msg->uiSQLErrno : 0U);
				return;
			}
			s_aPlayerBotFruitConsignDeposited[i] += (unsigned long long)removed;
			++s_uPlayerBotFruitConsignLots;
			++lots;
			b.owed = true;
			PlayerBotLogThrottled("fruit_consign_deposit", dwNow,
					"PLAYERBOT_FRUIT_CONSIGN: deposit pid=%u name=%s lv=%d map=%ld ch=%u vnum=%u count=%d held=%d keep=%d "
					"counter=%d cohort=%d bag_free=%d",
					ch->GetPlayerID(), ch->GetName(), (int)ch->GetLevel(), (long)ch->GetMapIndex(), (unsigned int)g_bChannel,
					vnum, removed, held, keep, PlayerBotHasCounter(ch) ? 1 : 0,
					IsPlayerBotArezzoDungeonCohortPID(ch->GetPlayerID()) ? 1 : 0, CountPlayerBotFreeInventoryCells(ch));
		}
	}

	// The trader's look: the oldest lot it has the room, the want and the purse for.
	void TakePlayerBotFruitConsign(LPCHARACTER ch, DWORD dwNow)
	{
		using namespace mt2009_rankp;
		if (CountPlayerBotFreeInventoryCells(ch) < PLAYERBOT_FRUIT_CONSIGN_TRADER_FREE_CELLS)
			return;
		if (s_dwPlayerBotFruitConsignCoreTake != 0 && dwNow - s_dwPlayerBotFruitConsignCoreTake < PLAYERBOT_FRUIT_CONSIGN_CORE_TAKE_MS)
			return;
		s_dwPlayerBotFruitConsignCoreTake = dwNow ? dwNow : 1;
		// The fruits it still takes: fewer than PLAYERBOT_FRUIT_CONSIGN_TRADER_HOLD in its bag.
		std::string vnums;
		for (int i = 0; i < FRUIT_COUNT; ++i)
			if ((int)ch->CountSpecifyItem(FRUITS[i].vnum) < PLAYERBOT_FRUIT_CONSIGN_TRADER_HOLD)
			{
				char one[16];
				snprintf(one, sizeof(one), "%s%u", vnums.empty() ? "" : ",", FRUITS[i].vnum);
				vnums += one;
			}
		if (vnums.empty())
			return;
		std::unique_ptr<SQLMsg> msg(PlayerBotFarmerQuery(
				"SELECT id, from_pid, vnum, count FROM player.playerbot_rank_fruit_consign WHERE state=0 AND vnum IN (%s) "
				"ORDER BY id LIMIT 1", vnums.c_str()));
		if (!PlayerBotFarmerSqlOk(msg) || !msg->Get()->pSQLResult)
			return;
		MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult);
		if (!row)
			return;
		unsigned int id = 0, from = 0, vnum = 0;
		int count = 0;
		str_to_number(id, row[0]);
		str_to_number(from, row[1]);
		str_to_number(vnum, row[2]);
		str_to_number(count, row[3]);
		const int index = GetPlayerBotRankFruitIndex(vnum);
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		if (!id || index < 0 || count <= 0 || !proto)
			return;
		const int stack = std::max(1, std::min<int>((int)proto->dwMaxStack, PLAYERBOT_FRUIT_CONSIGN_MAX_LOT));
		const int cells = (count + stack - 1) / stack;
		if (CountPlayerBotFreeInventoryCells(ch) < cells + PLAYERBOT_BAG_PRESSURE_FREE_CELLS)
			return;
		const int pct = GetPlayerBotFruitConsignFlag("m2_bot_fruit_consign_pay_pct", PLAYERBOT_FRUIT_CONSIGN_PAY_PCT, 1, 100);
		const long long full = (long long)GetPlayerBotRankFruitListUnit(vnum) * count * pct / 100;
		const long long spare = (long long)ch->GetGold() - GetPlayerBotReservedGold(ch) - (long long)PLAYERBOT_SHOPPING_GOLD_FLOOR;
		const long long pay = std::max(0LL, std::min(full, spare > 0 ? spare * PLAYERBOT_FRUIT_CONSIGN_PURSE_PCT / 100 : 0LL));
		std::unique_ptr<SQLMsg> claim(PlayerBotFarmerQuery(
				"UPDATE player.playerbot_rank_fruit_consign SET state=1, taker_pid=%u, taken_at=NOW(), paid=%lld "
				"WHERE id=%u AND state=0", ch->GetPlayerID(), pay, id));
		if (!PlayerBotFarmerSqlOne(claim))
		{
			++s_uPlayerBotFruitConsignRaced;
			return;	// another core's trader was first
		}
		for (int left = count; left > 0;)
		{
			const int part = std::min(left, stack);
			ch->AutoGiveItem(vnum, (ITEM_COUNT)part, -1, false);
			left -= part;
		}
		if (pay > 0)
		{
			PlayerBotChangeGold(ch, -pay);
			char hint[32];
			snprintf(hint, sizeof(hint), "lot=%u from=%u", id, from);
			LogManager::instance().CharLog(ch, (DWORD)std::min<long long>(pay, 0xFFFFFFFFLL), "PLAYERBOT_FRUIT_CONSIGN_PAY", hint);
		}
		s_aPlayerBotFruitConsignTaken[index] += (unsigned long long)count;
		++s_uPlayerBotFruitConsignTakes;
		s_llPlayerBotFruitConsignPaid += pay;
		PlayerBotLogThrottled("fruit_consign_take", dwNow,
				"PLAYERBOT_FRUIT_CONSIGN: take pid=%u name=%s map=%ld lot=%u from=%u vnum=%u count=%d paid=%lld full=%lld "
				"held=%d", ch->GetPlayerID(), ch->GetName(), (long)ch->GetMapIndex(), id, from, vnum, count, pay, full,
				(int)ch->CountSpecifyItem(vnum));
	}

	void ReportPlayerBotFruitConsign(DWORD dwNow)
	{
		using namespace mt2009_rankp;
		if (s_dwPlayerBotFruitConsignCensusAt == 0)
		{
			s_dwPlayerBotFruitConsignCensusAt = dwNow ? dwNow : 1;
			return;
		}
		if (dwNow - s_dwPlayerBotFruitConsignCensusAt < PLAYERBOT_FRUIT_CONSIGN_CENSUS_MS)
			return;
		s_dwPlayerBotFruitConsignCensusAt = dwNow ? dwNow : 1;
		long long queuedRows = 0, queuedUnits = 0;
		if (s_bPlayerBotFruitConsignTable)
		{
			LoadPlayerBotFruitConsignOwed(dwNow);
			std::unique_ptr<SQLMsg> msg(PlayerBotFarmerQuery(
					"SELECT COUNT(*), COALESCE(SUM(count),0) FROM player.playerbot_rank_fruit_consign WHERE state=0"));
			if (PlayerBotFarmerSqlOk(msg) && msg->Get()->pSQLResult)
				if (MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult))
				{
					str_to_number(queuedRows, row[0]);
					str_to_number(queuedUnits, row[1]);
				}
		}
		char by[256];
		int len = 0;
		by[0] = '\0';
		for (int i = 0; i < FRUIT_COUNT; ++i)
		{
			if (len >= 0 && len < (int)sizeof(by))
				len += snprintf(by + len, sizeof(by) - len, "%s%u:%llu/%llu", i ? "," : "", FRUITS[i].vnum,
						s_aPlayerBotFruitConsignDeposited[i], s_aPlayerBotFruitConsignTaken[i]);
			s_aPlayerBotFruitConsignDeposited[i] = s_aPlayerBotFruitConsignTaken[i] = 0;
		}
		sys_log(0, "PLAYERBOT_FRUIT_CONSIGN: census on=%d ch=%u couriers=%u traders=%u lots=%u takes=%u raced=%u failed=%u "
				"paid=%lld collects=%u collected=%lld queued_rows=%lld queued_units=%lld owed_couriers=%u deposited/taken=%s",
				IsPlayerBotFruitConsignOn() ? 1 : 0, (unsigned int)g_bChannel, s_uPlayerBotFruitConsignCouriers,
				s_uPlayerBotFruitConsignTraders, s_uPlayerBotFruitConsignLots, s_uPlayerBotFruitConsignTakes,
				s_uPlayerBotFruitConsignRaced, s_uPlayerBotFruitConsignFailed, s_llPlayerBotFruitConsignPaid,
				s_uPlayerBotFruitConsignCollects, s_llPlayerBotFruitConsignCollected, queuedRows, queuedUnits,
				(unsigned int)s_setPlayerBotFruitConsignOwed.size(), by);
		s_uPlayerBotFruitConsignLots = s_uPlayerBotFruitConsignTakes = s_uPlayerBotFruitConsignCollects = 0;
		s_uPlayerBotFruitConsignFailed = s_uPlayerBotFruitConsignRaced = 0;
		s_uPlayerBotFruitConsignCouriers = s_uPlayerBotFruitConsignTraders = 0;
		s_llPlayerBotFruitConsignPaid = s_llPlayerBotFruitConsignCollected = 0;
	}

	// Every bot's tick (playerbot_manager.cpp, beside the rank fruits' look): its own clock, then its role.
	void ManagePlayerBotRankFruitConsign(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || ch->IsDead() || !mt2009_rankp::Enabled())
			return;
		ReportPlayerBotFruitConsign(dwNow);
		TPlayerBotFruitConsignBot& b = s_mapPlayerBotFruitConsign[ch->GetPlayerID()];
		if (b.nextLook == 0)
		{
			b.nextLook = dwNow + 60000 + PlayerBotNavHash(ch->GetPlayerID() ^ 0x434f4e53U) % PLAYERBOT_FRUIT_CONSIGN_COURIER_MIN_MS;
			return;
		}
		if ((int)(dwNow - b.nextLook) < 0)
			return;
		const bool trader = IsPlayerBotFruitConsignTrader(ch);
		b.nextLook = dwNow + (trader
				? (DWORD)number((int)PLAYERBOT_FRUIT_CONSIGN_TRADER_MIN_MS, (int)PLAYERBOT_FRUIT_CONSIGN_TRADER_MAX_MS)
				: (DWORD)number((int)PLAYERBOT_FRUIT_CONSIGN_COURIER_MIN_MS, (int)PLAYERBOT_FRUIT_CONSIGN_COURIER_MAX_MS));
		if (ch->GetExchange() || ch->GetMyShop() || ch->GetShop() || ch->GetSafebox() || !mt2009_rankp::Known(ch))
			return;
		if (!EnsurePlayerBotFruitConsignTable(dwNow))
			return;
		if (s_dwPlayerBotFruitConsignOwedAt == 0)
			LoadPlayerBotFruitConsignOwed(dwNow);
		// The yang owed for its lots taken (by any core's trader), while some are out.
		if (b.owed || s_setPlayerBotFruitConsignOwed.count(ch->GetPlayerID()))
			CollectPlayerBotFruitConsign(ch, b, dwNow);
		if (!IsPlayerBotFruitConsignOn())
			return;
		if (trader)
		{
			++s_uPlayerBotFruitConsignTraders;
			TakePlayerBotFruitConsign(ch, dwNow);
		}
		else if (IsPlayerBotFruitConsignCourier(ch))
		{
			++s_uPlayerBotFruitConsignCouriers;
			DepositPlayerBotFruitConsign(ch, b, dwNow);
		}
	}
}

#endif
