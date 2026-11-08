#ifndef __INC_METIN2_PLAYERBOT_SM_MARKET_RULE_H__
#define __INC_METIN2_PLAYERBOT_SM_MARKET_RULE_H__

// MT2009_PLUS_BOT_SM_MARKET_RULE_V1 - the bots' Smocze Monety on the market (the owner, 8 November 2026: "Jesli boty maja
// za duzo SM - nie wystawiaja ich na rynek. Na rynek moga trafic tylko w dwoch przypadkach: (1) SM zostaly wydropione z
// Metina/bossa/battle passa/z gry; (2) bot bardzo potrzebuje Yang - w tej kategorii moze wystawic maksymalnie 1000 SM
// lacznie dziennie, wszystkie boty razem").
//
// Smocze Monety reach the market only as a Kupon SM line on a bot's counter (IsPlayerBotSmCouponVnum: 80032 10, 80031
// 20, 80017 50, 80014 100, 80018 250, 80015 500, 80016 1000 coins). Before this rule a bot listed every coupon of its
// bag when it was one of the voucher sellers (half the bots with a counter) whose balance covered its needs - "has too
// many SM" - or when it was exp-locked (MT2009_PLUS_BOT_SM_HP70_V1), whatever the coupon's origin.
//
// The origin. Every coupon a bot holds is from the game (a Metin's or a boss's drop, the Battle Pass, Boss Swiata, a
// chest, the wheel's old spins, the market, a person's gift), except those of its ACCOUNT's Smocze Monety: the panel's
// "Daj wszystkim botom SM" (item_grants.py - the coins handed out as Kupon SM, player.web_seban_grants) and the need
// sale's own coupons below. Those few are what is recorded, by coins, a bot (player.playerbot_sm_origin.acct_coins,
// durable - restarts, relogs, cores); the bag's coupon coins over it are the game's. Coins rather than a mark on the
// item: the coupons stack (MT2009_PLUS_STACK_CHESTS_COUPONS_V1) and move as stacks onto counters and into the voucher
// pass, the engine's give paths (pickup, quest give_item2, AutoGiveItem) are outside the bots' code, and a socket would
// travel with the coupon to its buyer. The account's coupons go first wherever coupons go: cashed first (the voucher
// pass), counted last when a line goes up. A panel grant row is credited once it is done (every core looks every
// PLAYERBOT_SMR_REFRESH_MS, one at a time - GET_LOCK; the grants made before the rule's first look are the baseline,
// never credited). The record never says more than the bag holds (the census puts it down to the bag).
//
// The listing (IsPlayerBotVoucherForCounter, PlayerBotKeepsVouchersForCounter, the offline stand's add and create):
//   * the game's coupons: as before (the sellers' share, the exp-locked bots) - no limit;
//   * the account's: never - the voucher pass cashes them (PlayerBotKeepsVouchersForCounter says no while the bag holds
//     account coupons the need pool does not cover) - EXCEPT out of the need pool: a coupon line goes up while its
//     coins are within the bag's game coins plus the pool coins the bot holds (need_coins); the coupons of the bag in
//     cell order, so the lines of one visit never take more than that together.
// The need ("bardzo potrzebuje Yang") - IsPlayerBotBadlyShortOfYang: a bot of PLAYERBOT_SMR_NEED_MIN_LEVEL+ with a
// counter whose gold is under what it holds back (GetPlayerBotReservedGold: the horse's fee and savings, the frontier's
// Teleporter fares, the guild's fund) plus the shopping floor (PLAYERBOT_SHOPPING_GOLD_FLOOR, 200 000) - the purse every
// spender of the bots already stops at - for PLAYERBOT_SMR_NEED_SUSTAIN_MS without a break, with no Smocze Monety need
// of its own open (HasPlayerBotSmCouponNeed), no game coupon in the bag it could list instead and no coupon line on its
// counter yet. Then (ManagePlayerBotSmNeedSale, from the voucher pass's minute):
//   * the server-wide pool of the day (player.playerbot_sm_market_pool, CURDATE() of the database - Europe/Warsaw, so
//     the day turns at Polish midnight) gives it PLAYERBOT_SMR_NEED_CHUNK coins at most - within the event flag
//     m2_bot_sm_need_daily (default 1000) for every core and channel together (one conditional UPDATE) and
//     m2_bot_sm_need_per_bot (default 100) a bot a day;
//   * the coupons: account coupons already in its bag, else the account's Smocze Monety turned into Kupon SM (a
//     conditional UPDATE of account.cash, as the Kolo Losu charges; 100 / 50 / 20 / 10 coupons - face value, the same
//     coins the voucher pass would credit back); not enough coins over the open V3 goals' reserve - nothing;
//   * they go on its counter at its next service at the coupon band's price; reserved coins it never lists stay its
//     own until listed (cashed meanwhile: made again from the account, no second pool share).
// Players: nothing changes (their coupons, counters and ItemShop are untouched); nor a companion (IsPlayerBotSidekickPID).
//
// Switches (event flags, read live): m2_bot_sm_market_rule_off 1 - the old behaviour (every coupon by the old rules, no
// need sale); m2_bot_sm_need_daily N - the pool a day (0/unset 1000, negative: none); m2_bot_sm_need_per_bot N - a
// bot's share a day (0/unset 100); m2_bot_sm_need_convert_off 1 - no account Smocze Monety turned into coupons (account
// coupons already held still sell from the pool).
// The log: PLAYERBOT_SMRYNEK - listed (origin split), blocked (throttled), account coupons cashed (throttled), need sale
// (reserved / converted / refused, throttled), grants credited, the census every ten minutes: the coupons this core's
// bots hold by origin, the need coins they hold, the lines listed and blocked since the last census by origin, today's
// pool (used / cap, listed game / need - every core).
//
// An implementation fragment: included once by playerbot_manager.cpp after playerbot_sm_coupons.h (the coupons' values,
// the bag's count, the SM need), in the anonymous namespace; declared in playerbot_types.h for the voucher pass
// (playerbot_itemshop.h) and the offline stand (playerbot_offline_shop.h) above it.

#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_BOT_SM_COUPON_MARKET_V1) && defined(MT2009_PLUS_BOT_SM_MARKET_RULE_V1)

namespace
{
	const DWORD PLAYERBOT_SMR_REFRESH_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_SMR_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_SMR_NEED_SUSTAIN_MS = 15 * 60 * 1000;
	const DWORD PLAYERBOT_SMR_NEED_LOOK_MS = 5 * 60 * 1000;
	const int PLAYERBOT_SMR_NEED_MIN_LEVEL = 30;
	const long long PLAYERBOT_SMR_NEED_CHUNK = 100;
	const long long PLAYERBOT_SMR_NEED_DAILY_DEFAULT = 1000;
	const long long PLAYERBOT_SMR_NEED_PER_BOT_DEFAULT = 100;
	// the coupons a need sale makes, the biggest first (Kupon SM 100 / 50 / 20 / 10)
	const DWORD PLAYERBOT_SMR_MAKE_VNUMS[] = { 80014, 80017, 80031, 80032 };

	struct TPlayerBotSmOrigin
	{
		long long llAcct = 0;		// coupon coins of the account in the bag (the record)
		long long llNeed = 0;		// need pool coins held, not listed yet
		long long llNeedToday = 0;	// pool coins this bot took today
	};
	std::map<DWORD, TPlayerBotSmOrigin> s_mapPlayerBotSmOrigin;
	bool s_bPlayerBotSmOriginLoaded = false;
	bool s_bPlayerBotSmOriginTables = false;
	DWORD s_dwPlayerBotSmOriginNextRefresh = 0;
	DWORD s_dwPlayerBotSmMarketNextCensus = 0;
	std::map<DWORD, DWORD> s_mapPlayerBotSmNeedSince;	// pid -> first seen badly short of yang (0: not)
	std::map<DWORD, DWORD> s_mapPlayerBotSmNeedNextLook;

	struct TPlayerBotSmMarketStats
	{
		unsigned int uLinesGame = 0, uLinesNeed = 0, uLinesOff = 0, uBlocked = 0, uCashedAcct = 0, uReserved = 0,
				uConverted = 0, uPoolFull = 0, uBotCap = 0, uNoCoins = 0, uGrantRows = 0;
		long long llListedGame = 0, llListedNeed = 0, llListedOff = 0, llBlocked = 0, llCashedAcct = 0, llReserved = 0,
				llConverted = 0, llGrantCoins = 0;
	};
	TPlayerBotSmMarketStats s_kPlayerBotSmMarket;

	bool IsPlayerBotSmMarketRuleOn()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_bot_sm_market_rule_off") == 0;
	}

	long long GetPlayerBotSmNeedDailyCap()
	{
		const int flag = quest::CQuestManager::instance().GetEventFlag("m2_bot_sm_need_daily");
		return flag < 0 ? 0 : (flag == 0 ? PLAYERBOT_SMR_NEED_DAILY_DEFAULT : (long long)flag);
	}

	long long GetPlayerBotSmNeedPerBotCap()
	{
		const int flag = quest::CQuestManager::instance().GetEventFlag("m2_bot_sm_need_per_bot");
		return flag < 0 ? 0 : (flag == 0 ? PLAYERBOT_SMR_NEED_PER_BOT_DEFAULT : (long long)flag);
	}

	bool PlayerBotSmrSqlOk(const std::unique_ptr<SQLMsg>& msg)
	{
		return msg.get() && msg->uiSQLErrno == 0 && msg->Get();
	}

	std::unique_ptr<SQLMsg> PlayerBotSmrQuery(const std::string& query)
	{
		return std::unique_ptr<SQLMsg>(AccountDB::instance().DirectQuery(query.c_str()));
	}

	bool PlayerBotSmrExec(const std::string& query)
	{
		std::unique_ptr<SQLMsg> msg(PlayerBotSmrQuery(query));
		return PlayerBotSmrSqlOk(msg);
	}

	// The coins a coupon vnum is worth, as SQL (the panel's grants are read in the database).
	std::string PlayerBotSmrCouponCoinsSql(const char* column)
	{
		static const DWORD vnums[] = { 80032, 80031, 80017, 80014, 80018, 80015, 80016 };
		std::string sql = std::string("CASE ") + column;
		for (size_t i = 0; i < sizeof(vnums) / sizeof(vnums[0]); ++i)
			sql += " WHEN " + std::to_string(vnums[i]) + " THEN " + std::to_string(GetPlayerBotSmCouponValue(vnums[i]));
		return sql + " ELSE 0 END";
	}

	std::string PlayerBotSmrCouponVnumList()
	{
		static const DWORD vnums[] = { 80032, 80031, 80017, 80014, 80018, 80015, 80016 };
		std::string list;
		for (size_t i = 0; i < sizeof(vnums) / sizeof(vnums[0]); ++i)
			list += (list.empty() ? "" : ",") + std::to_string(vnums[i]);
		return list;
	}

	bool EnsurePlayerBotSmOriginTables()
	{
		if (s_bPlayerBotSmOriginTables)
			return true;
		const bool a = PlayerBotSmrExec("CREATE TABLE IF NOT EXISTS player.playerbot_sm_origin (pid INT UNSIGNED NOT NULL PRIMARY KEY, "
				"acct_coins BIGINT NOT NULL DEFAULT 0, need_coins BIGINT NOT NULL DEFAULT 0, need_day DATE NULL DEFAULT NULL, "
				"need_today BIGINT NOT NULL DEFAULT 0, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE "
				"CURRENT_TIMESTAMP) ENGINE=InnoDB");
		const bool b = PlayerBotSmrExec("CREATE TABLE IF NOT EXISTS player.playerbot_sm_origin_grant (grant_id BIGINT UNSIGNED NOT NULL "
				"PRIMARY KEY, pid INT UNSIGNED NOT NULL DEFAULT 0, coins BIGINT NOT NULL DEFAULT 0, credited TINYINT(1) NOT NULL "
				"DEFAULT 0, seen_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, KEY credited (credited)) ENGINE=InnoDB");
		const bool c = PlayerBotSmrExec("CREATE TABLE IF NOT EXISTS player.playerbot_sm_market_pool (day DATE NOT NULL PRIMARY KEY, "
				"used BIGINT NOT NULL DEFAULT 0, listed_game BIGINT NOT NULL DEFAULT 0, listed_need BIGINT NOT NULL DEFAULT 0, "
				"conversions INT NOT NULL DEFAULT 0, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE "
				"CURRENT_TIMESTAMP) ENGINE=InnoDB");
		s_bPlayerBotSmOriginTables = a && b && c;
		if (!s_bPlayerBotSmOriginTables)
			PlayerBotLogThrottled("smrynek_tables", get_dword_time(), "PLAYERBOT_SMRYNEK: tables missing and not made - no coupon "
					"of a bot is listed until they are (sm_rynek.sql)");
		return s_bPlayerBotSmOriginTables;
	}

	// The panel's coupon grants to bots that are done and not credited yet: credited to the bots' account coins, once
	// (every core looks, one at a time). The first look ever only marks what was there (the baseline).
	void ScanPlayerBotSmOriginGrants()
	{
		std::unique_ptr<SQLMsg> lock(PlayerBotSmrQuery("SELECT GET_LOCK('m2_bot_sm_origin_scan', 0)"));
		if (!PlayerBotSmrSqlOk(lock) || !lock->Get()->pSQLResult)
			return;
		MYSQL_ROW lr = mysql_fetch_row(lock->Get()->pSQLResult);
		if (!lr || !lr[0] || atoi(lr[0]) != 1)
			return;
		const std::string coins = PlayerBotSmrCouponCoinsSql("g.vnum");
		const std::string rows = " FROM player.web_seban_grants AS g "
				"JOIN player.player AS p ON p.id = g.player_id JOIN account.account AS a ON a.id = p.account_id "
				"WHERE g.vnum IN (" + PlayerBotSmrCouponVnumList() + ") AND g.status IN ('done', 'partial') AND "
				"a.login LIKE 'playerbot\\_%'";
		bool baseline = false;
		{
			std::unique_ptr<SQLMsg> any(PlayerBotSmrQuery("SELECT COUNT(*) FROM player.playerbot_sm_origin_grant WHERE grant_id = 0"));
			if (PlayerBotSmrSqlOk(any) && any->Get()->pSQLResult)
			{
				MYSQL_ROW r = mysql_fetch_row(any->Get()->pSQLResult);
				baseline = r && r[0] && atoi(r[0]) == 0;
			}
			else
			{
				PlayerBotSmrExec("SELECT RELEASE_LOCK('m2_bot_sm_origin_scan')");
				return;
			}
		}
		if (baseline)
		{
			// the grants before the rule: their coupons were cashed or listed long ago - never credited
			const bool ok = PlayerBotSmrExec("INSERT IGNORE INTO player.playerbot_sm_origin_grant (grant_id, pid, coins, credited) "
					"SELECT g.id, g.player_id, 0, 1" + rows);
			// (web_seban_grants missing: a world without the panel's grants - the baseline marker alone)
			PlayerBotSmrExec("INSERT IGNORE INTO player.playerbot_sm_origin_grant (grant_id, pid, coins, credited) VALUES (0, 0, 0, 1)");
			sys_log(0, "PLAYERBOT_SMRYNEK: grants baseline marked (panel grants before the rule are never credited) ok=%d", ok ? 1 : 0);
			PlayerBotSmrExec("SELECT RELEASE_LOCK('m2_bot_sm_origin_scan')");
			return;
		}
		if (PlayerBotSmrExec("START TRANSACTION"))
		{
			bool ok = PlayerBotSmrExec("INSERT IGNORE INTO player.playerbot_sm_origin_grant (grant_id, pid, coins, credited) "
					"SELECT g.id, g.player_id, g.quantity * (" + coins + "), 0" + rows);
			unsigned int credited = 0;
			long long creditedCoins = 0;
			if (ok)
			{
				std::unique_ptr<SQLMsg> sum(PlayerBotSmrQuery("SELECT COUNT(*), IFNULL(SUM(coins), 0) FROM "
						"player.playerbot_sm_origin_grant WHERE credited = 0"));
				if (PlayerBotSmrSqlOk(sum) && sum->Get()->pSQLResult)
					if (MYSQL_ROW r = mysql_fetch_row(sum->Get()->pSQLResult))
					{
						credited = r[0] ? (unsigned int)strtoul(r[0], NULL, 10) : 0;
						creditedCoins = r[1] ? atoll(r[1]) : 0;
					}
			}
			if (ok && credited > 0)
				ok = PlayerBotSmrExec("INSERT INTO player.playerbot_sm_origin (pid, acct_coins) SELECT pid, SUM(coins) FROM "
						"player.playerbot_sm_origin_grant WHERE credited = 0 AND pid <> 0 GROUP BY pid "
						"ON DUPLICATE KEY UPDATE acct_coins = acct_coins + VALUES(acct_coins)") &&
						PlayerBotSmrExec("UPDATE player.playerbot_sm_origin_grant SET credited = 1 WHERE credited = 0");
			PlayerBotSmrExec(ok ? "COMMIT" : "ROLLBACK");
			if (ok && credited > 0)
			{
				s_kPlayerBotSmMarket.uGrantRows += credited;
				s_kPlayerBotSmMarket.llGrantCoins += creditedCoins;
				sys_log(0, "PLAYERBOT_SMRYNEK: grants credited rows=%u coins=%lld (the panel's Kupon SM to bots - account origin)",
						credited, creditedCoins);
			}
		}
		PlayerBotSmrExec("SELECT RELEASE_LOCK('m2_bot_sm_origin_scan')");
	}

	// Every PLAYERBOT_SMR_REFRESH_MS: the grants, then every bot's record (the rows with something in them - few).
	void RefreshPlayerBotSmOrigin(DWORD now, bool force)
	{
		if (!force && s_bPlayerBotSmOriginLoaded && (int)(now - s_dwPlayerBotSmOriginNextRefresh) < 0)
			return;
		s_dwPlayerBotSmOriginNextRefresh = now + PLAYERBOT_SMR_REFRESH_MS;
		if (!EnsurePlayerBotSmOriginTables())
			return;
		ScanPlayerBotSmOriginGrants();
		std::unique_ptr<SQLMsg> msg(PlayerBotSmrQuery("SELECT pid, acct_coins, need_coins, IF(need_day <=> CURDATE(), need_today, 0) "
				"FROM player.playerbot_sm_origin WHERE acct_coins > 0 OR need_coins > 0 OR need_day <=> CURDATE()"));
		if (!PlayerBotSmrSqlOk(msg) || !msg->Get()->pSQLResult)
		{
			PlayerBotLogThrottled("smrynek_read", now, "PLAYERBOT_SMRYNEK: origin read failed - the last one stands%s",
					s_bPlayerBotSmOriginLoaded ? "" : " (none yet: no coupon of a bot is listed)");
			return;
		}
		std::map<DWORD, TPlayerBotSmOrigin> fresh;
		MYSQL_ROW row;
		while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			if (!row[0])
				continue;
			TPlayerBotSmOrigin& o = fresh[(DWORD)strtoul(row[0], NULL, 10)];
			o.llAcct = row[1] ? std::max(0LL, atoll(row[1])) : 0;
			o.llNeed = row[2] ? std::max(0LL, atoll(row[2])) : 0;
			o.llNeedToday = row[3] ? std::max(0LL, atoll(row[3])) : 0;
		}
		s_mapPlayerBotSmOrigin.swap(fresh);
		s_bPlayerBotSmOriginLoaded = true;
	}

	TPlayerBotSmOrigin GetPlayerBotSmOrigin(DWORD pid)
	{
		std::map<DWORD, TPlayerBotSmOrigin>::const_iterator it = s_mapPlayerBotSmOrigin.find(pid);
		return it != s_mapPlayerBotSmOrigin.end() ? it->second : TPlayerBotSmOrigin();
	}

	// The record changed: in the database at once (a relative UPDATE - another core may have credited a grant
	// meanwhile) and in this core's copy.
	void ChangePlayerBotSmOrigin(DWORD pid, long long dAcct, long long dNeed, long long dNeedToday)
	{
		if (!pid || (dAcct == 0 && dNeed == 0 && dNeedToday == 0))
			return;
		std::string q = "INSERT INTO player.playerbot_sm_origin (pid, acct_coins, need_coins, need_day, need_today) VALUES (" +
				std::to_string(pid) + ", " + std::to_string(std::max(0LL, dAcct)) + ", " + std::to_string(std::max(0LL, dNeed)) +
				", CURDATE(), " + std::to_string(std::max(0LL, dNeedToday)) + ") ON DUPLICATE KEY UPDATE "
				"acct_coins = GREATEST(0, acct_coins + (" + std::to_string(dAcct) + ")), "
				"need_coins = GREATEST(0, need_coins + (" + std::to_string(dNeed) + "))";
		if (dNeedToday != 0)
			q += ", need_today = IF(need_day <=> CURDATE(), need_today, 0) + (" + std::to_string(dNeedToday) + "), need_day = CURDATE()";
		if (!PlayerBotSmrExec(q))
			sys_err("PLAYERBOT_SMRYNEK: origin write failed pid=%u acct=%lld need=%lld", pid, dAcct, dNeed);
		TPlayerBotSmOrigin& o = s_mapPlayerBotSmOrigin[pid];
		o.llAcct = std::max(0LL, o.llAcct + dAcct);
		o.llNeed = std::max(0LL, o.llNeed + dNeed);
		o.llNeedToday = std::max(0LL, o.llNeedToday + dNeedToday);
	}

	void AddPlayerBotSmMarketPoolListed(long long game, long long need)
	{
		if (game <= 0 && need <= 0)
			return;
		PlayerBotSmrExec("INSERT INTO player.playerbot_sm_market_pool (day, listed_game, listed_need) VALUES (CURDATE(), " +
				std::to_string(std::max(0LL, game)) + ", " + std::to_string(std::max(0LL, need)) + ") ON DUPLICATE KEY UPDATE "
				"listed_game = listed_game + VALUES(listed_game), listed_need = listed_need + VALUES(listed_need)");
	}

	// The bag's coupon coins by origin: the account's (the record, never over the bag), the game's (the rest) and the
	// account's the pool covers.
	struct TPlayerBotSmBag
	{
		long long llBag = 0, llAcct = 0, llGame = 0, llNeedAvail = 0;
	};

	TPlayerBotSmBag GetPlayerBotSmBag(LPCHARACTER ch)
	{
		TPlayerBotSmBag b;
		if (!ch)
			return b;
		const TPlayerBotSmOrigin o = GetPlayerBotSmOrigin(ch->GetPlayerID());
		b.llBag = CountPlayerBotSmCouponCoins(ch);
		b.llAcct = std::min(o.llAcct, b.llBag);
		b.llGame = b.llBag - b.llAcct;
		b.llNeedAvail = std::min(o.llNeed, b.llAcct);
		return b;
	}

	// A bot that holds need pool coins and the account coupons for them: they are its counter's.
	bool PlayerBotHoldsSmNeedCoupons(LPCHARACTER ch)
	{
		if (!ch || !IsPlayerBotSmMarketRuleOn() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return false;
		return GetPlayerBotSmBag(ch).llNeedAvail > 0;
	}

	// The bag holds account coupons the pool does not cover: the voucher pass cashes them (and the bag's other coupons
	// with them - the coins stay the bot's, nothing goes to the market).
	bool PlayerBotMustCashSmAccountCoupons(LPCHARACTER ch)
	{
		if (!ch || !IsPlayerBotSmMarketRuleOn() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return false;
		const TPlayerBotSmBag b = GetPlayerBotSmBag(ch);
		if (b.llAcct <= b.llNeedAvail)
			return false;
		PlayerBotLogThrottled("smrynek_cash_acct", get_dword_time(),
				"PLAYERBOT_SMRYNEK: account coupons cashed, not listed pid=%u name=%s bag=%lld account=%lld need=%lld",
				ch->GetPlayerID(), ch->GetName(), b.llBag, b.llAcct, b.llNeedAvail);
		return true;
	}

	// The coupon may go on the counter (the scoring's test): its coins with the coupons of the cells before it within
	// the bag's game coins and the need coins it holds. Not before this core read the records once.
	bool IsPlayerBotSmCouponListable(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !IsPlayerBotSmCouponVnum(item->GetVnum()) || !IsPlayerBotSmMarketRuleOn())
			return true;
		RefreshPlayerBotSmOrigin(get_dword_time(), false);
		const long long coins = GetPlayerBotSmCouponValue(item->GetVnum()) * std::max<long long>(1, (long long)item->GetCount());
		if (!s_bPlayerBotSmOriginLoaded)
		{
			PlayerBotLogThrottled("smrynek_unknown", get_dword_time(),
					"PLAYERBOT_SMRYNEK: blocked pid=%u name=%s vnum=%u coins=%lld why=origin_unknown", ch->GetPlayerID(),
					ch->GetName(), item->GetVnum(), coins);
			return false;
		}
		const TPlayerBotSmBag b = GetPlayerBotSmBag(ch);
		long long before = 0;
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM && cell < item->GetCell(); ++cell)
		{
			LPITEM other = ch->GetInventoryItem(cell);
			if (other && other != item && IsPlayerBotSmCouponVnum(other->GetVnum()))
				before += GetPlayerBotSmCouponValue(other->GetVnum()) * std::max<long long>(1, (long long)other->GetCount());
		}
		const long long budget = b.llGame + b.llNeedAvail;
		if (before + coins <= budget)
			return true;
		++s_kPlayerBotSmMarket.uBlocked;
		s_kPlayerBotSmMarket.llBlocked += coins;
		PlayerBotLogThrottled("smrynek_blocked", get_dword_time(),
				"PLAYERBOT_SMRYNEK: blocked pid=%u name=%s vnum=%u coins=%lld cells_before=%lld bag=%lld game=%lld account=%lld "
				"need=%lld why=account_sm", ch->GetPlayerID(), ch->GetName(), item->GetVnum(), coins, before, b.llBag, b.llGame,
				b.llAcct, b.llNeedAvail);
		return false;
	}

	// A line of coupons about to go up: what of it is the game's and what the pool's, after the lines of the same
	// submission before it (taken*). False: the line is not covered (it stays in the bag).
	bool SplitPlayerBotSmCouponListing(LPCHARACTER ch, DWORD vnum, long long count, long long takenGame, long long takenNeed,
			TPlayerBotSmListSplit& out)
	{
		out = TPlayerBotSmListSplit();
		if (!ch || !IsPlayerBotSmCouponVnum(vnum))
			return true;
		out.dwVnum = vnum;
		out.llCoins = GetPlayerBotSmCouponValue(vnum) * std::max<long long>(1, count);
		if (!IsPlayerBotSmMarketRuleOn())
			return true;	// bRule false: counted as the old behaviour's
		out.bRule = true;
		if (!s_bPlayerBotSmOriginLoaded)
			return false;
		const TPlayerBotSmBag b = GetPlayerBotSmBag(ch);
		const long long game = std::max(0LL, b.llGame - takenGame);
		const long long need = std::max(0LL, b.llNeedAvail - takenNeed);
		out.llGame = std::min(out.llCoins, game);
		out.llNeed = out.llCoins - out.llGame;
		if (out.llNeed <= need)
			return true;
		++s_kPlayerBotSmMarket.uBlocked;
		s_kPlayerBotSmMarket.llBlocked += out.llCoins;
		PlayerBotLogThrottled("smrynek_blocked_line", get_dword_time(),
				"PLAYERBOT_SMRYNEK: blocked line pid=%u name=%s vnum=%u coins=%lld game=%lld need=%lld why=account_sm",
				ch->GetPlayerID(), ch->GetName(), vnum, out.llCoins, game, need);
		return false;
	}

	// The line went up: the pool's part off the bot's need coins and account coins, the day's counts.
	void NotePlayerBotSmCouponListed(LPCHARACTER ch, const TPlayerBotSmListSplit& split, const char* at)
	{
		if (!ch || split.llCoins <= 0)
			return;
		if (!split.bRule)
		{
			++s_kPlayerBotSmMarket.uLinesOff;
			s_kPlayerBotSmMarket.llListedOff += split.llCoins;
			return;
		}
		if (split.llNeed > 0)
		{
			ChangePlayerBotSmOrigin(ch->GetPlayerID(), -split.llNeed, -split.llNeed, 0);
			++s_kPlayerBotSmMarket.uLinesNeed;
			s_kPlayerBotSmMarket.llListedNeed += split.llNeed;
		}
		if (split.llGame > 0)
		{
			++s_kPlayerBotSmMarket.uLinesGame;
			s_kPlayerBotSmMarket.llListedGame += split.llGame;
		}
		AddPlayerBotSmMarketPoolListed(split.llGame, split.llNeed);
		sys_log(0, "PLAYERBOT_SMRYNEK: listed pid=%u name=%s vnum=%u coins=%lld game=%lld need_pool=%lld at=%s gold=%lld",
				ch->GetPlayerID(), ch->GetName(), split.dwVnum, split.llCoins, split.llGame, split.llNeed, at ? at : "-",
				(long long)ch->GetGold());
	}

	// The voucher pass cashed coupons: the account's go first.
	void NotePlayerBotSmCouponsCashedOrigin(LPCHARACTER ch, long long coins)
	{
		if (!ch || coins <= 0 || !IsPlayerBotSmMarketRuleOn())
			return;
		const TPlayerBotSmOrigin o = GetPlayerBotSmOrigin(ch->GetPlayerID());
		const long long acct = std::min(o.llAcct, coins);
		if (acct <= 0)
			return;
		ChangePlayerBotSmOrigin(ch->GetPlayerID(), -acct, 0, 0);
		++s_kPlayerBotSmMarket.uCashedAcct;
		s_kPlayerBotSmMarket.llCashedAcct += acct;
		sys_log(0, "PLAYERBOT_SMRYNEK: account coupons cashed pid=%u name=%s coins=%lld account=%lld need_held=%lld",
				ch->GetPlayerID(), ch->GetName(), coins, acct, o.llNeed);
	}

	// "Bardzo potrzebuje Yang" (the header): under the reserve and the shopping floor.
	bool IsPlayerBotBadlyShortOfYang(LPCHARACTER ch, long long* spareOut)
	{
		const long long spare = ch ? (long long)ch->GetGold() - (long long)GetPlayerBotReservedGold(ch) -
				(long long)PLAYERBOT_SHOPPING_GOLD_FLOOR : 0;
		if (spareOut)
			*spareOut = spare;
		return ch && (int)ch->GetLevel() >= PLAYERBOT_SMR_NEED_MIN_LEVEL && spare < 0;
	}

#if defined(ENABLE_IKASHOP_RENEWAL)
	bool PlayerBotHasSmCouponOnCounter(LPCHARACTER ch)
	{
		auto shop = ch ? ikashop::GetManager().GetShopByOwnerID(ch->GetPlayerID()) : nullptr;
		if (!shop)
			return false;
		for (const auto& [id, line] : shop->GetItems())
			if (line && IsPlayerBotSmCouponVnum(line->GetInfo().vnum))
				return true;
		return false;
	}
#else
	bool PlayerBotHasSmCouponOnCounter(LPCHARACTER)
	{
		return false;
	}
#endif

	// The account's Smocze Monety turned into coupons (face value) - the conditional charge first, the coupons after,
	// the coins back for what could not be given. The coins made.
	long long MakePlayerBotSmNeedCoupons(LPCHARACTER ch, TPlayerBotAIState& state, long long coins, DWORD now)
	{
		if (!ch || !ch->GetDesc() || coins <= 0)
			return 0;
		const DWORD aid = ch->GetDesc()->GetAccountTable().id;
		// whole coupons only, the biggest first; a cell for each (stacks merge, a new kind may need one)
		std::vector<DWORD> make;
		long long left = coins;
		for (size_t i = 0; i < sizeof(PLAYERBOT_SMR_MAKE_VNUMS) / sizeof(PLAYERBOT_SMR_MAKE_VNUMS[0]); ++i)
		{
			const long long v = GetPlayerBotSmCouponValue(PLAYERBOT_SMR_MAKE_VNUMS[i]);
			while (v > 0 && left >= v)
			{
				make.push_back(PLAYERBOT_SMR_MAKE_VNUMS[i]);
				left -= v;
			}
		}
		const long long total = coins - left;
		if (total <= 0 || ch->GetEmptyInventory(1) < 0)
			return 0;
		{
			std::unique_ptr<SQLMsg> paid(PlayerBotSmrQuery("UPDATE account.account SET cash = cash - " + std::to_string(total) +
					" WHERE id = " + std::to_string(aid) + " AND cash >= " + std::to_string(total)));
			if (!PlayerBotSmrSqlOk(paid) || paid->Get()->uiAffectedRows != 1)
				return 0;
		}
		long long given = 0;
		for (size_t i = 0; i < make.size(); ++i)
		{
			// AutoGiveItem puts what finds no cell on the ground - a coupon there would come back as the game's
			if (ch->GetEmptyInventory(1) < 0)
				break;
			LPITEM item = ch->AutoGiveItem(make[i], 1, -1, false);
			if (!item)
				break;
			given += GetPlayerBotSmCouponValue(make[i]);
		}
		if (given < total)
			PlayerBotSmrExec("UPDATE account.account SET cash = cash + " + std::to_string(total - given) + " WHERE id = " +
					std::to_string(aid));
		state.iDragonCoins = (int)std::max(0LL, (long long)state.iDragonCoins - given);
#ifdef MT2009_PLUS_BOT_ISHOP_V3_V1
		s_mapPlayerBotIshop3LastCharge[ch->GetPlayerID()] = now;	// no stale balance read on its heels
#endif
		return given;
	}

	// The need sale (the header), from the voucher pass's minute.
	void ManagePlayerBotSmNeedSale(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now)
	{
		if (!ch || !IsPlayerBotSmMarketRuleOn() || IsPlayerBotSidekickPID(ch->GetPlayerID()) || !PlayerBotHasCounter(ch))
			return;
		RefreshPlayerBotSmOrigin(now, false);
		if (!s_bPlayerBotSmOriginLoaded)
			return;
		const DWORD pid = ch->GetPlayerID();
		long long spare = 0;
		const bool shortOfYang = IsPlayerBotBadlyShortOfYang(ch, &spare);
		DWORD& since = s_mapPlayerBotSmNeedSince[pid];
		if (!shortOfYang)
		{
			since = 0;
		}
		else if (since == 0)
			since = now ? now : 1;
		const TPlayerBotSmOrigin o = GetPlayerBotSmOrigin(pid);
		const TPlayerBotSmBag b = GetPlayerBotSmBag(ch);
		const bool convertOn = quest::CQuestManager::instance().GetEventFlag("m2_bot_sm_need_convert_off") == 0;
		// coins of the pool it holds whose coupons were cashed meanwhile: made again from the account (no new share)
		const long long deficit = o.llNeed - b.llAcct;
		if (deficit > 0)
		{
			const long long made = convertOn && state.bDragonBalanceKnown && state.iDragonCoins >= deficit
					? MakePlayerBotSmNeedCoupons(ch, state, deficit, now) : 0;
			if (made > 0)
			{
				ChangePlayerBotSmOrigin(pid, made, 0, 0);
				++s_kPlayerBotSmMarket.uConverted;
				s_kPlayerBotSmMarket.llConverted += made;
				sys_log(0, "PLAYERBOT_SMRYNEK: need sale coupons made again pid=%u name=%s coins=%lld need_held=%lld balance=%d",
						pid, ch->GetName(), made, o.llNeed, state.iDragonCoins);
			}
			else
			{
				// the account cannot (or may not) make them: the share is given up
				ChangePlayerBotSmOrigin(pid, 0, -deficit, 0);
				PlayerBotLogThrottled("smrynek_need_drop", now,
						"PLAYERBOT_SMRYNEK: need sale share given up pid=%u name=%s coins=%lld balance=%d convert=%d", pid,
						ch->GetName(), deficit, state.iDragonCoins, convertOn ? 1 : 0);
			}
			return;
		}
		if (!shortOfYang || (int)(now - since) < (int)PLAYERBOT_SMR_NEED_SUSTAIN_MS || o.llNeed > 0)
			return;
		DWORD& next = s_mapPlayerBotSmNeedNextLook[pid];
		if (next != 0 && (int)(now - next) < 0)
			return;
		next = now + PLAYERBOT_SMR_NEED_LOOK_MS;
		if (b.llGame > 0 || PlayerBotHasSmCouponOnCounter(ch) || HasPlayerBotSmCouponNeed(ch))
			return;	// it has a game coupon to sell, one on its counter already, or wants coins itself
		const long long perBot = GetPlayerBotSmNeedPerBotCap();
		long long chunk = std::min(PLAYERBOT_SMR_NEED_CHUNK, perBot - o.llNeedToday);
		chunk -= chunk % 10;
		if (chunk <= 0)
		{
			++s_kPlayerBotSmMarket.uBotCap;
			return;
		}
		const bool fromBag = b.llAcct - o.llNeed >= chunk;	// the panel's coupons already in its bag
		if (!fromBag)
		{
			if (!convertOn || !state.bDragonBalanceKnown)
				return;
			long long keep = 0;
#ifdef MT2009_PLUS_BOT_ISHOP_V3_V1
			keep = GetPlayerBotIshop3GoalReserve(ch, state);
#endif
			if ((long long)state.iDragonCoins < chunk + keep)
			{
				++s_kPlayerBotSmMarket.uNoCoins;
				PlayerBotLogThrottled("smrynek_need_nocoins", now,
						"PLAYERBOT_SMRYNEK: need sale refused pid=%u name=%s why=coins balance=%d goal_reserve=%lld gold=%lld spare=%lld",
						pid, ch->GetName(), state.iDragonCoins, keep, (long long)ch->GetGold(), spare);
				return;
			}
		}
		// the server-wide pool of the day (every core and channel): one conditional UPDATE
		const long long cap = GetPlayerBotSmNeedDailyCap();
		PlayerBotSmrExec("INSERT IGNORE INTO player.playerbot_sm_market_pool (day) VALUES (CURDATE())");
		std::unique_ptr<SQLMsg> took(PlayerBotSmrQuery("UPDATE player.playerbot_sm_market_pool SET used = used + " +
				std::to_string(chunk) + ", conversions = conversions + 1 WHERE day = CURDATE() AND used + " + std::to_string(chunk) +
				" <= " + std::to_string(cap)));
		if (!PlayerBotSmrSqlOk(took) || took->Get()->uiAffectedRows != 1)
		{
			++s_kPlayerBotSmMarket.uPoolFull;
			PlayerBotLogThrottled("smrynek_pool_full", now,
					"PLAYERBOT_SMRYNEK: need sale refused pid=%u name=%s why=pool_full chunk=%lld cap=%lld gold=%lld spare=%lld",
					pid, ch->GetName(), chunk, cap, (long long)ch->GetGold(), spare);
			return;
		}
		long long made = 0;
		if (!fromBag)
		{
			made = MakePlayerBotSmNeedCoupons(ch, state, chunk, now);
			if (made <= 0)
			{
				PlayerBotSmrExec("UPDATE player.playerbot_sm_market_pool SET used = GREATEST(0, used - " + std::to_string(chunk) +
						"), conversions = GREATEST(0, conversions - 1) WHERE day = CURDATE()");
				PlayerBotLogThrottled("smrynek_need_make", now,
						"PLAYERBOT_SMRYNEK: need sale refused pid=%u name=%s why=charge_or_bag balance=%d", pid, ch->GetName(),
						state.iDragonCoins);
				return;
			}
			if (made < chunk)
				PlayerBotSmrExec("UPDATE player.playerbot_sm_market_pool SET used = GREATEST(0, used - " +
						std::to_string(chunk - made) + ") WHERE day = CURDATE()");
		}
		const long long share = fromBag ? chunk : made;
		ChangePlayerBotSmOrigin(pid, fromBag ? 0 : made, share, share);
		++s_kPlayerBotSmMarket.uReserved;
		s_kPlayerBotSmMarket.llReserved += share;
		if (!fromBag)
		{
			++s_kPlayerBotSmMarket.uConverted;
			s_kPlayerBotSmMarket.llConverted += made;
		}
		sys_log(0, "PLAYERBOT_SMRYNEK: need sale reserved pid=%u name=%s lv=%d coins=%lld from=%s gold=%lld reserved_gold=%d "
				"spare=%lld balance=%d bot_today=%lld cap=%lld", pid, ch->GetName(), ch->GetLevel(), share,
				fromBag ? "account_coupons" : "account_sm", (long long)ch->GetGold(), GetPlayerBotReservedGold(ch), spare,
				state.iDragonCoins, o.llNeedToday + share, cap);
	}

	// Every ten minutes: the coupons this core's bots hold by origin (the records put down to the bags), the lines since
	// the last census, today's pool (every core).
	void WritePlayerBotSmMarketCensus(DWORD now)
	{
		if (s_dwPlayerBotSmMarketNextCensus != 0 && (int)(now - s_dwPlayerBotSmMarketNextCensus) < 0)
			return;
		s_dwPlayerBotSmMarketNextCensus = now + PLAYERBOT_SMR_CENSUS_MS;
		RefreshPlayerBotSmOrigin(now, true);
		unsigned int bots = 0, withGame = 0, withAcct = 0, withNeed = 0, needy = 0, trimmed = 0;
		long long game = 0, acct = 0, need = 0;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !ch->IsPC() || !ch->GetDesc() || !ch->GetDesc()->IsBot() || !ch->IsItemLoaded() ||
					IsPlayerBotSidekickPID(it->first))
				continue;
			++bots;
			const TPlayerBotSmOrigin o = GetPlayerBotSmOrigin(it->first);
			const TPlayerBotSmBag b = GetPlayerBotSmBag(ch);
			// the record never says more than the bag holds: a coupon gone another way (traded, given, dropped)
			if (s_bPlayerBotSmOriginLoaded && o.llAcct > b.llBag)
			{
				ChangePlayerBotSmOrigin(it->first, b.llBag - o.llAcct, 0, 0);
				++trimmed;
			}
			game += b.llGame;
			acct += b.llAcct;
			need += o.llNeed;
			withGame += b.llGame > 0 ? 1 : 0;
			withAcct += b.llAcct > 0 ? 1 : 0;
			withNeed += o.llNeed > 0 ? 1 : 0;
			std::map<DWORD, DWORD>::const_iterator s = s_mapPlayerBotSmNeedSince.find(it->first);
			needy += s != s_mapPlayerBotSmNeedSince.end() && s->second != 0 ? 1 : 0;
		}
		for (std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotSmNeedSince.begin(); it != s_mapPlayerBotSmNeedSince.end();)
			if (s_mapPlayerBotAIStates.find(it->first) == s_mapPlayerBotAIStates.end())
			{
				s_mapPlayerBotSmNeedNextLook.erase(it->first);
				s_mapPlayerBotSmNeedSince.erase(it++);
			}
			else
				++it;
		long long used = 0, listedGame = 0, listedNeed = 0;
		long long conversions = 0;
		{
			std::unique_ptr<SQLMsg> msg(PlayerBotSmrQuery("SELECT used, listed_game, listed_need, conversions FROM "
					"player.playerbot_sm_market_pool WHERE day = CURDATE()"));
			if (PlayerBotSmrSqlOk(msg) && msg->Get()->pSQLResult)
				if (MYSQL_ROW r = mysql_fetch_row(msg->Get()->pSQLResult))
				{
					used = r[0] ? atoll(r[0]) : 0;
					listedGame = r[1] ? atoll(r[1]) : 0;
					listedNeed = r[2] ? atoll(r[2]) : 0;
					conversions = r[3] ? atoll(r[3]) : 0;
				}
		}
		const TPlayerBotSmMarketStats& s = s_kPlayerBotSmMarket;
		sys_log(0, "PLAYERBOT_SMRYNEK: census rule=%d bots=%u held_game=%lld held_account=%lld need_held=%lld bots_game=%u "
				"bots_account=%u bots_need=%u short_of_yang=%u trimmed=%u listed_game=%u/%lld listed_need=%u/%lld listed_rule_off=%u/%lld "
				"blocked=%u/%lld cashed_account=%u/%lld reserved=%u/%lld converted=%u/%lld pool_full=%u bot_cap=%u no_coins=%u "
				"grants=%u/%lld pool_today_used=%lld pool_cap=%lld pool_today_listed_game=%lld pool_today_listed_need=%lld "
				"pool_today_reservations=%lld per_bot=%lld loaded=%d",
				IsPlayerBotSmMarketRuleOn() ? 1 : 0, bots, game, acct, need, withGame, withAcct, withNeed, needy, trimmed,
				s.uLinesGame, s.llListedGame, s.uLinesNeed, s.llListedNeed, s.uLinesOff, s.llListedOff, s.uBlocked, s.llBlocked,
				s.uCashedAcct, s.llCashedAcct, s.uReserved, s.llReserved, s.uConverted, s.llConverted, s.uPoolFull, s.uBotCap,
				s.uNoCoins, s.uGrantRows, s.llGrantCoins, used, GetPlayerBotSmNeedDailyCap(), listedGame, listedNeed, conversions,
				GetPlayerBotSmNeedPerBotCap(), s_bPlayerBotSmOriginLoaded ? 1 : 0);
		s_kPlayerBotSmMarket = TPlayerBotSmMarketStats();
	}

	// The voucher pass's minute (CashPlayerBotVouchers): the records, the census, the need sale.
	void TickPlayerBotSmMarketRule(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now)
	{
		if (!now)
			now = 1;
		if (!IsPlayerBotSmMarketRuleOn())
		{
			WritePlayerBotSmMarketCensus(now);
			return;
		}
		RefreshPlayerBotSmOrigin(now, false);
		WritePlayerBotSmMarketCensus(now);
		ManagePlayerBotSmNeedSale(ch, state, now);
	}
}

#endif

#endif
