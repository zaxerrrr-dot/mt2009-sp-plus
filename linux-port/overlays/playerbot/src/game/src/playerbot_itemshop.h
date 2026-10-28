#ifndef __INC_METIN2_PLAYERBOT_ITEMSHOP_H__
#define __INC_METIN2_PLAYERBOT_ITEMSHOP_H__

// The bots and the ItemShop, on the 2.x line.
//
// mt2009 carries a shop of its own inside the game (CItemShopManager,
// common.itemshop_items, "/itemshop" from the client): a hundred and fifty
// lines priced in Dragon Coins - the account's `cash` - and in Dragon Marks -
// `cash_mark`, credited one for one for every coin spent. The coins come into
// the world as Kupon SM vouchers (80014-80018, a Metin stone's or a boss's
// drop by M2_DRAGON_COIN_*_PERMILLE), and until 2.0.60 a bot kept every one
// in its bag for good: ninety-seven of them on the test world after three
// days, and not one coin on any account. "Uzywanie wydropionych kuponow SM i
// przeznaczanie na potrzebne zakupy w itemshop" (Tieru, 16 September).
//
// What a bot does with the shop is what a careful player does with a small
// allowance. A voucher is cashed the moment it is found - the same charge the
// package's itemshop_manage quest makes for a player (AddCash through the db
// core, the itemshop_dragon_scroll row), without its dialog. The balance is
// kept in the state and read back from the account once an hour, because
// GetPlayerAccountBalance is a synchronous query. A purchase is the engine's
// own CItemShopManager::BuyItem behind the browse flag a client sets by
// opening the window: the level floor, the price, the account and the
// engine's purchase log are all its, and the goods arrive through
// AutoGiveItem. One purchase an hour a bot, and only what the bot's own rules
// would use: Kamien Duchowy for a Grand Master skill it can train, the change
// stone for a worn weapon whose lines the reroll pass would still reroll,
// with marks a Blessing Scroll for a piece under scroll work and the Dragon
// God's attack potions, and a hairstyle - one in four bots, once - because a
// crowd of a thousand identical heads is the thing a player notices first.
// MT2009 Plus (24 September 2026): the look is the whole of it now - every
// bot from level 30 with coins buys, in this order and one at a time, a
// costume, a hairstyle, a weapon skin for its weapon and a pet (no mount),
// wears them (the pet is summoned from its seal), and buys a piece again
// when its time runs out and the slot is empty.
// Tieru 2.2.20 (26 September) added the Exorcism Scroll, Kamien Duchowy and
// the single change stone to what a bot buys; see the wishes below.
// Nothing timed: every bot already holds the premium subscription for five
// years (SpawnBot, the operator's rule), so the VIP rings and the Przepustka
// Triumfu are worth nothing to it, and BuyItem refuses a VIP item to a
// subscriber anyway.
//
// r40250 has no such shop and this file is empty there: the tick calls the
// two functions below and gets nothing.
//
// An implementation fragment in the sense playerbot_types.h describes: include
// it exactly once, after playerbot_offline_shop.h (it asks
// PlayerBotWearsScrollWork of playerbot_town.h and the reroll rules of
// playerbot_bonus.h) and before playerbot_market.h.

#if defined(PLAYERBOT_ENGINE_MT2009)
#include "itemshop_manager.h"
#include "log.h"
#include "playerbot_collector.h"	// MT2009_PLUS_COLLECTOR_ITEM_V1: its item's vnum
#include "playerbot_arezzo_costumes.h"	// MT2009_PLUS_AREZZO_COSTUME_SETS_V2: the Arezzo sets, only with the module on
#if defined(__PET_SYSTEM__)
#include "PetSystem.h"
#endif
#endif

namespace
{
#if defined(PLAYERBOT_ENGINE_MT2009)
	struct TPlayerBotItemShopEntry
	{
		DWORD dwIndex;
		DWORD dwPrice;
		DWORD dwCount;
		BYTE bMinLevel;
#ifdef MT2009_PLUS_BOT_ISHOP_V3_V1
		// MT2009_PLUS_BOT_ISHOP_V3_V1: a line of the ItemShop V3 (itemshop3.shop) - its time in minutes (the expiry put
		// into the item as the shop's buy.php does, Player::CreateItem; 0 = the proto's own), whether it stacks, and the
		// sockets the line sets. dwIndex is the V3 line id then.
		DWORD dwMinutes;
		bool bStackable;
		long alSockets[ITEM_SOCKET_MAX_NUM];
#endif
	};

	// The catalogue as the bots read it: every line per vnum for each
	// currency, and the hairstyles for sale. Rebuilt every hour from the
	// manager, which holds what the db core sent at boot - an operator who
	// edits common.itemshop_items restarts the world anyway.
	//
	// Every line, not the cheapest unit alone: that kept the change stone's
	// four-pack (207 coins) and never the single (69), and four accounts of
	// 418 on m2zip held 207 - so the wish was one nobody could pay for
	// (26 September). The buyer takes the cheapest unit it can afford
	// (FindPlayerBotItemShopEntry).
	typedef std::map<DWORD, std::vector<TPlayerBotItemShopEntry> > TPlayerBotItemShopTable;
	TPlayerBotItemShopTable s_mapPlayerBotItemShopCoins;
	TPlayerBotItemShopTable s_mapPlayerBotItemShopMarks;
	std::vector<DWORD> s_vecPlayerBotItemShopHair;
	// MT2009 Plus: the rest of a bot's look, for coins - costumes, weapon
	// skins and pet seals (PET_PAY); a pet with its own loot is left out, it
	// costs more and a bot's pet never loots (PetSystem.cpp).
	std::vector<DWORD> s_vecPlayerBotItemShopBody;
	std::vector<DWORD> s_vecPlayerBotItemShopWeaponSkin;
	std::vector<DWORD> s_vecPlayerBotItemShopPet;
	std::vector<DWORD> s_vecPlayerBotItemShopMount;
	DWORD s_dwNextPlayerBotItemShopScan = 0;

	// MT2009_PLUS_SIDEKICK_COINS_V1: the player's companion and the shop
	// (playerbot_sidekick.h, later in the include order). Its owner's switch
	// "Smocze Monety: wydaje / nie wydaje" in the window decides, not the
	// world's ISHOP; it buys only what it uses - no look of any kind - and
	// tells its owner every voucher cashed and every purchase.
	bool IsPlayerBotSidekickPID(DWORD pid);
	bool IsPlayerBotSidekickCoinsOn(DWORD pid);
	void NotePlayerBotSidekickVouchers(LPCHARACTER sk, long long coins, int balance);
	void NotePlayerBotSidekickItemShopBuy(LPCHARACTER sk, DWORD vnum, DWORD count, DWORD price, bool marks,
			const char* reason, int left);

	unsigned int s_uPlayerBotVouchersUsed = 0;
	unsigned int s_uPlayerBotCoinsCharged = 0;
	unsigned int s_uPlayerBotItemShopBuys = 0;
	unsigned int s_uPlayerBotItemShopRefusals = 0;
	// Looks that found a wish the balance could not pay for.
	unsigned int s_uPlayerBotItemShopSaving = 0;
	std::map<DWORD, unsigned int> s_mapPlayerBotItemShopBought;
	DWORD s_dwNextPlayerBotItemShopCensus = 0;

	// One line of the catalogue into the tables the wishes and the looks read.
	void AddPlayerBotItemShopLine(DWORD vnum, const TItemTable* proto, const TPlayerBotItemShopEntry& entry, bool marks)
	{
		TPlayerBotItemShopTable& table = marks ? s_mapPlayerBotItemShopMarks : s_mapPlayerBotItemShopCoins;
		std::vector<TPlayerBotItemShopEntry>& lines = table[vnum];
		const bool first = lines.empty();
		lines.push_back(entry);
		// the look lists name a vnum once (a second line of it - another time - is the same look)
		if (!first)
			return;
		// MT2009_PLUS_BOT_HAIR_V1: only a costume set's hairstyle is a
		// bot's to buy (IsPlayerBotSetHairVnum, playerbot_economy.h).
		if (!marks && proto->bType == ITEM_COSTUME && proto->bSubType == COSTUME_HAIR &&
				IsPlayerBotSetHairVnum(vnum))
			s_vecPlayerBotItemShopHair.push_back(vnum);
		if (!marks && proto->bType == ITEM_COSTUME && proto->bSubType == COSTUME_BODY)
			s_vecPlayerBotItemShopBody.push_back(vnum);
		if (!marks && proto->bType == ITEM_COSTUME && proto->bSubType == COSTUME_WEAPON)
			s_vecPlayerBotItemShopWeaponSkin.push_back(vnum);
		if (!marks && proto->bType == ITEM_PET && proto->bSubType == PET_PAY && proto->alValues[0] != 0 &&
				proto->alValues[2] == 0)
			s_vecPlayerBotItemShopPet.push_back(vnum);
#if defined(ENABLE_MOUNT_COSTUME_SYSTEM)
		if (!marks && proto->bType == ITEM_COSTUME && proto->bSubType == COSTUME_MOUNT && proto->alValues[1] != 0)
			s_vecPlayerBotItemShopMount.push_back(vnum);
#endif
	}

#ifdef MT2009_PLUS_BOT_ISHOP_V3_V1
	// ------------------------------------------------- MT2009_PLUS_BOT_ISHOP_V3_V1
	//
	// The bots buy in the ItemShop V3 only (the owner, 28 October 2026): the lines and prices the players see there
	// (the view itemshop3.shop - common.itemshop_items with itemshop3.line_overrides, the V3-only lines of
	// itemshop3.v3_lines, the set chests), read every PLAYERBOT_ISHOP_CATALOGUE_INTERVAL per core. Never a Kupon SM
	// (80014-80019), a VIP line, a flash offer, Auto Lowy (72800/72801), Szklo Handlu (72802), Kolekcjoner (70115) or
	// Kamien Duchowy (50513, hidden in V3 - line 907, category 0); never an Arezzo line while the module is off.
	//
	// The purchase is the bots' own, as buy.php makes it for a player: the balance read fresh, the bag's room for every
	// piece, the charge (CItemShopManager::AddCash through the db core - a Smocze Monety line gives the price back as
	// Smocze Znaki in the same UPDATE, ClientManager::ChargeCash, as V3 gives 100% back), the goods (AutoGiveItem, the
	// line's time put into the item as Player::CreateItem puts it), log.itemshop with the bots' currency marker
	// (PLAYERBOT_ISHOP3_LOG_CURRENCY_*: 11 Smocze Monety, 12 Smocze Znaki - never V3's history, so nothing a bot buys
	// counts for "Popularne"), and the money back for whatever could not be given. The source switch: ISHOP_SOURCE
	// (playerbot_config.h; 2 V3, 1 the old in-game catalogue, 0 nothing). The goals that buy through it are
	// playerbot_ishop3_goals.h.
	const int PLAYERBOT_ISHOP3_LOG_CURRENCY_COINS = 11;
	const int PLAYERBOT_ISHOP3_LOG_CURRENCY_MARKS = 12;
	const int PLAYERBOT_ISHOP3_MAX_QTY = 10;		// buy.php: 1..10 a purchase
	const DWORD PLAYERBOT_ISHOP3_FRESH_MS = 60 * 1000;	// a balance older than this is read again before a purchase
	const DWORD PLAYERBOT_ISHOP3_CHARGE_SETTLE_MS = 10 * 1000;	// no read on the heels of a charge (async, db core)

	int GetPlayerBotItemShopSource();

	bool IsPlayerBotIshop3ExcludedVnum(DWORD vnum)
	{
		return (vnum >= 80014 && vnum <= 80019) || vnum == 72800 || vnum == 72801 || vnum == 72802 || vnum == 70115 ||
				vnum == PLAYERBOT_GRAND_MASTER_STONE_VNUM || vnum == playerbot_collector::ITEM_VNUM;
	}

	// A set chest of the "Sety Bonusowe" category (itemshop3.chests / chest_drops / chest_items): its results with
	// their chances (parts per million) and, per result, its items - each the alternatives by sex and class.
	struct TPlayerBotIshop3ChestAlt
	{
		DWORD dwVnum;
		DWORD dwCount;
		DWORD dwMinutes;
	};

	struct TPlayerBotIshop3ChestDrop
	{
		int iDropNo;
		int iPpm;
		std::vector<std::vector<TPlayerBotIshop3ChestAlt> > items;
	};

	struct TPlayerBotIshop3Chest
	{
		DWORD dwLine;
		DWORD dwChestId;
		DWORD dwPrice;
		DWORD dwRolls;	// the line's count: rolls a purchase (buy_chest.php)
		BYTE bMinLevel;
		std::vector<TPlayerBotIshop3ChestDrop> drops;
	};

	std::vector<TPlayerBotIshop3Chest> s_vecPlayerBotIshop3Chests;

	// The census by category (PLAYERBOT_ISHOP3: census, hourly).
	struct TPlayerBotIshop3Census
	{
		unsigned int uBuys, uPieces, uNoCoins, uNotListed, uBagFull, uRefunds;
		long long llCoins, llMarks;
		// MT2009_PLUS_BOT_SM_DAILY_POOL_V1: refused by the daily pool / urgent purchases from tomorrow's seventh
		unsigned int uPoolBlock, uPoolBorrow;
	};
	std::map<std::string, TPlayerBotIshop3Census> s_mapPlayerBotIshop3Census;
	std::map<DWORD, DWORD> s_mapPlayerBotIshop3LastCharge;

	TPlayerBotIshop3Census& GetPlayerBotIshop3Census(const char* category)
	{
		std::map<std::string, TPlayerBotIshop3Census>::iterator it = s_mapPlayerBotIshop3Census.find(category);
		if (it == s_mapPlayerBotIshop3Census.end())
		{
			TPlayerBotIshop3Census zero = TPlayerBotIshop3Census();
			it = s_mapPlayerBotIshop3Census.insert(std::make_pair(std::string(category), zero)).first;
		}
		return it->second;
	}

	// The census category of a purchase's reason (the goals' own reasons are their categories).
	const char* GetPlayerBotIshop3Category(const char* reason)
	{
		if (!reason)
			return "other";
		static const char* const s_looks[] = { "look", "hairstyle", "secondset", "counter_hairstyle" };
		for (size_t i = 0; i < sizeof(s_looks) / sizeof(s_looks[0]); ++i)
			if (strncmp(reason, s_looks[i], strlen(s_looks[i])) == 0)
				return "look";
		if (strncmp(reason, "element", 7) == 0)
			return "element";
		// MT2009_PLUS_BOT_SM_DAILY_POOL_V1: the Sung Ma buys and the Loch tickets apart from the wishes in the census
		if (strncmp(reason, "sungma", 6) == 0)
			return "sungma";
		if (strcmp(reason, "loch_ticket") == 0)
			return "loch";
		if (strcmp(reason, "change_stone") == 0)
			return "bonus_change";
		if (strcmp(reason, "blessing_scroll") == 0)
			return "refine";
		if (strncmp(reason, "bonus_", 6) == 0 || strcmp(reason, "cor") == 0 || strcmp(reason, "bean") == 0 ||
				strcmp(reason, "sash") == 0 || strcmp(reason, "refine") == 0 || strcmp(reason, "chest") == 0)
			return reason;
		return "wish";
	}

	long long PlayerBotIshop3Num(MYSQL_ROW row, int i)
	{
		return row[i] ? atoll(row[i]) : 0;
	}

#ifdef MT2009_PLUS_BOT_SM_DAILY_POOL_V1
	// ------------------------------------------------- MT2009_PLUS_BOT_SM_DAILY_POOL_V1
	//
	// The weekly Smocze Monety split into days inside the bots (the owner, 28 October 2026: "paczki tygodniowe dziel
	// wewnetrznie na dni - kazdego dnia bot ma do wydania 1/7 tygodniowych SM; jesli NAPRAWDE czegos potrzebuje, moze
	// wziac z puli nastepnego dnia"). The grant itself stays as it is (seban-panel/sm_grants.py, once a week); only what
	// a bot account spends in the ItemShop V3 is paced. With no cap the bots spent a week's grant within hours.
	//
	// * The week: the ISO week in Europe/Warsaw - read from the database's own clock (its NOW() is Warsaw time, as
	//   sm_grants.py's period_key and log.itemshop's time): the key (2026-W44) and the Monday 00:00 as a unix time; the
	//   day d of the week (1..7) is counted from that Monday.
	// * The weekly base of an account: its account.sm_grant_log row of the week (period 'week', the week's key - one a
	//   week, the table's unique key). An account with no grant this week: its balance plus what it already spent this
	//   week, taken at its first look of the week (so a restart mid-week gives the same base).
	// * The allowance: base * d / 7, cumulative - an unspent day rolls over within the week. A purchase in Smocze Monety
	//   is allowed while spent + price <= allowance(d); an urgent one (IsPlayerBotSmPoolUrgent, playerbot_ishop3_goals.h:
	//   what blocks the bot's progression now) while spent + price <= allowance(d + 1) - the next day's seventh. Sunday's
	//   next day is the next week's grant: never borrowed (allowance(8) = the base).
	// * The spent: durable - log.itemshop, the bots' own Smocze Monety rows (currency PLAYERBOT_ISHOP3_LOG_CURRENCY_COINS,
	//   11: the lines and the set chests) since the week's Monday, summed by account in one query a core an hour (and at
	//   once when the week turns), plus what this core charged since that read. A read never lowers what the core
	//   already counted (a row still on its way through the log queue is not lost).
	// * Outside the pool: anything in Smocze Znaki (they come back 1:1 from the coins spent), the cashing of the
	//   vouchers (Kupon SM - untouched), a companion (its owner's coins and its own switch), the old in-game catalogue.
	// * The log: PLAYERBOT_ISHOP3 census - pool_block / pool_borrow per category, and a "pool" line: the accounts asked
	//   today, their average base, allowance and spent, the share of today's allowance used, how many are at it and how
	//   many borrow from tomorrow; "pool block" (throttled) for a refused purchase.
	bool IsPlayerBotSmPoolUrgent(LPCHARACTER ch, const char* reason);	// playerbot_ishop3_goals.h
	bool IsPlayerBotSidekickPID(DWORD pid);

	const long PLAYERBOT_SM_POOL_REFRESH_S = 60 * 60;
	const long PLAYERBOT_SM_POOL_WEEK_S = 7 * 24 * 60 * 60;

	struct TPlayerBotSmPool
	{
		long long llSpentDb;	// log.itemshop at the last read
		long long llSpentMem;	// charged by this core since
		long long llFallback;	// no grant: the balance + spent at the first look of the week; -1 not yet
		long lSeen;		// the last ask (unix)
		TPlayerBotSmPool() : llSpentDb(0), llSpentMem(0), llFallback(-1), lSeen(0) {}
	};

	struct TPlayerBotSmPoolRoom
	{
		bool bActive;
		bool bUrgent;
		long long llToday;	// what is left of today's allowance (negative: over it)
		long long llTomorrow;	// ... of tomorrow's
		long long Room() const { return !bActive ? LLONG_MAX : (bUrgent ? llTomorrow : llToday); }
	};

	std::map<DWORD, TPlayerBotSmPool> s_mapPlayerBotSmPool;	// by account id
	std::map<DWORD, long long> s_mapPlayerBotSmPoolGrant;
	std::map<DWORD, long long> s_mapPlayerBotSmPoolSpentDb;
	std::string s_strPlayerBotSmPoolWeek;
	long s_lPlayerBotSmPoolWeekStart = 0;
	long s_lPlayerBotSmPoolNextRead = 0;
	long s_lPlayerBotSmPoolLastTry = 0;

	void RefreshPlayerBotSmPool()
	{
		const long now = (long)get_global_time();
		// hourly, and at once when the week turns - never twice within a minute (a failed read: five minutes; the
		// pool works on the last week read meanwhile, or not at all before the first)
		const bool weekTurned = s_lPlayerBotSmPoolWeekStart != 0 && now >= s_lPlayerBotSmPoolWeekStart + PLAYERBOT_SM_POOL_WEEK_S;
		if (s_lPlayerBotSmPoolNextRead != 0 && now < s_lPlayerBotSmPoolNextRead &&
				!(weekTurned && now >= s_lPlayerBotSmPoolLastTry + 60))
			return;
		s_lPlayerBotSmPoolLastTry = now;
		s_lPlayerBotSmPoolNextRead = now + 5 * 60;
		std::string week;
		long weekStart = 0;
		{
			std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(
					"SELECT DATE_FORMAT(NOW(), '%x-W%v'), UNIX_TIMESTAMP(CURDATE() - INTERVAL WEEKDAY(CURDATE()) DAY)"));
			if (!msg || !msg->Get() || !msg->Get()->pSQLResult)
				return;
			MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult);
			if (!row || !row[0] || !row[1])
				return;
			week = row[0];
			weekStart = atol(row[1]);
		}
		if (week.empty() || week.size() > 10 || weekStart <= 0)
			return;
		std::map<DWORD, long long> grant, spent;
		{
			char query[256];
			snprintf(query, sizeof(query), "SELECT account_id, amount FROM account.sm_grant_log WHERE period = 'week' AND "
					"period_key = '%s' AND target = 'bot'", week.c_str());
			std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
			if (!msg || !msg->Get() || !msg->Get()->pSQLResult)
				return;
			MYSQL_ROW row;
			while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
				if (row[0] && row[1])
					grant[(DWORD)strtoul(row[0], NULL, 10)] = atoll(row[1]);
		}
		{
			char query[256];
			snprintf(query, sizeof(query), "SELECT aid, SUM(price) FROM log.itemshop WHERE currency = %d AND "
					"time >= FROM_UNIXTIME(%ld) GROUP BY aid", PLAYERBOT_ISHOP3_LOG_CURRENCY_COINS, weekStart);
			std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
			if (!msg || !msg->Get() || !msg->Get()->pSQLResult)
				return;
			MYSQL_ROW row;
			while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
				if (row[0] && row[1])
					spent[(DWORD)strtoul(row[0], NULL, 10)] = atoll(row[1]);
		}
		const bool newWeek = week != s_strPlayerBotSmPoolWeek;
		if (newWeek)
			s_mapPlayerBotSmPool.clear();
		for (std::map<DWORD, TPlayerBotSmPool>::iterator it = s_mapPlayerBotSmPool.begin(); it != s_mapPlayerBotSmPool.end();
				++it)
		{
			std::map<DWORD, long long>::const_iterator db = spent.find(it->first);
			const long long fresh = db != spent.end() ? db->second : 0;
			const long long counted = it->second.llSpentDb + it->second.llSpentMem;
			it->second.llSpentDb = fresh;
			it->second.llSpentMem = std::max(0LL, counted - fresh);
		}
		sys_log(0, "PLAYERBOT_ISHOP3: pool read week=%s%s monday=%ld grants=%u spenders=%u", week.c_str(),
				newWeek ? " (new)" : "", weekStart, (unsigned int)grant.size(), (unsigned int)spent.size());
		s_strPlayerBotSmPoolWeek = week;
		s_lPlayerBotSmPoolWeekStart = weekStart;
		s_mapPlayerBotSmPoolGrant.swap(grant);
		s_mapPlayerBotSmPoolSpentDb.swap(spent);
		s_lPlayerBotSmPoolNextRead = now + PLAYERBOT_SM_POOL_REFRESH_S;
	}

	// The day of the week, 1 (Monday) .. 7 (Sunday).
	int GetPlayerBotSmPoolDay(long now)
	{
		const long d = (now - s_lPlayerBotSmPoolWeekStart) / (24 * 60 * 60) + 1;
		return (int)std::max(1L, std::min(7L, d));
	}

	// The account's weekly base (-1: not known yet) and its pool entry.
	long long GetPlayerBotSmPoolBase(DWORD aid, TPlayerBotSmPool& pool, const TPlayerBotAIState* state, int coins)
	{
		std::map<DWORD, long long>::const_iterator g = s_mapPlayerBotSmPoolGrant.find(aid);
		if (g != s_mapPlayerBotSmPoolGrant.end())
			return std::max(0LL, g->second);
		if (pool.llFallback < 0 && state && state->bDragonBalanceKnown)
			pool.llFallback = std::max(0, coins) + pool.llSpentDb + pool.llSpentMem;
		return pool.llFallback;
	}

	TPlayerBotSmPool* GetPlayerBotSmPool(DWORD aid)
	{
		std::map<DWORD, TPlayerBotSmPool>::iterator it = s_mapPlayerBotSmPool.find(aid);
		if (it != s_mapPlayerBotSmPool.end())
			return &it->second;
		TPlayerBotSmPool fresh;
		std::map<DWORD, long long>::const_iterator db = s_mapPlayerBotSmPoolSpentDb.find(aid);
		fresh.llSpentDb = db != s_mapPlayerBotSmPoolSpentDb.end() ? db->second : 0;
		return &s_mapPlayerBotSmPool.insert(std::make_pair(aid, fresh)).first->second;
	}

	// What the pool leaves a purchase in Smocze Monety of this reason (inactive: the switch off, a companion, the week
	// not read, the base not known).
	TPlayerBotSmPoolRoom GetPlayerBotSmPoolRoom(LPCHARACTER ch, const TPlayerBotAIState& state, const char* reason)
	{
		TPlayerBotSmPoolRoom r = { false, false, 0, 0 };
		if (!IsPlayerBotSmDailyPoolOn() || !ch || !ch->GetDesc() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return r;
		RefreshPlayerBotSmPool();
		if (s_lPlayerBotSmPoolWeekStart == 0)
			return r;
		const DWORD aid = ch->GetDesc()->GetAccountTable().id;
		TPlayerBotSmPool& pool = *GetPlayerBotSmPool(aid);
		const long now = (long)get_global_time();
		pool.lSeen = now;
		const long long base = GetPlayerBotSmPoolBase(aid, pool, &state, state.iDragonCoins);
		if (base < 0)
			return r;
		const int d = GetPlayerBotSmPoolDay(now);
		const long long spent = pool.llSpentDb + pool.llSpentMem;
		r.bActive = true;
		r.bUrgent = IsPlayerBotSmPoolUrgent(ch, reason);
		r.llToday = base * d / 7 - spent;
		r.llTomorrow = base * std::min(d + 1, 7) / 7 - spent;
		return r;
	}

	void NotePlayerBotSmPoolSpent(LPCHARACTER ch, long long paid)
	{
		if (paid <= 0 || !ch || !ch->GetDesc() || s_lPlayerBotSmPoolWeekStart == 0)
			return;
		GetPlayerBotSmPool(ch->GetDesc()->GetAccountTable().id)->llSpentMem += paid;
	}

	// The census's pool line: the accounts asked today.
	void WritePlayerBotSmPoolCensus()
	{
		if (!IsPlayerBotSmDailyPoolOn())
		{
			sys_log(0, "PLAYERBOT_ISHOP3: pool off (ISHOP_DAILY_POOL=0)");
			return;
		}
		if (s_lPlayerBotSmPoolWeekStart == 0)
			return;
		const long now = (long)get_global_time();
		const int d = GetPlayerBotSmPoolDay(now);
		const long dayStart = s_lPlayerBotSmPoolWeekStart + (long)(d - 1) * 24 * 60 * 60;
		unsigned int accounts = 0, fromGrant = 0, atCap = 0, borrowing = 0;
		long long sumBase = 0, sumAllowance = 0, sumSpent = 0, sumPct = 0;
		for (std::map<DWORD, TPlayerBotSmPool>::iterator it = s_mapPlayerBotSmPool.begin(); it != s_mapPlayerBotSmPool.end();
				++it)
		{
			if (it->second.lSeen < dayStart)
				continue;
			const long long base = GetPlayerBotSmPoolBase(it->first, it->second, NULL, 0);
			if (base < 0)
				continue;
			const long long allowance = base * d / 7;
			const long long spent = it->second.llSpentDb + it->second.llSpentMem;
			++accounts;
			if (s_mapPlayerBotSmPoolGrant.find(it->first) != s_mapPlayerBotSmPoolGrant.end())
				++fromGrant;
			sumBase += base;
			sumAllowance += allowance;
			sumSpent += spent;
			sumPct += allowance > 0 ? std::min(999LL, spent * 100 / allowance) : (spent > 0 ? 999 : 0);
			if (spent >= allowance)
				++atCap;
			if (spent > allowance)
				++borrowing;
		}
		if (accounts == 0)
			return;
		sys_log(0, "PLAYERBOT_ISHOP3: pool week=%s day=%d accounts=%u from_grant=%u from_balance=%u avg_base=%lld "
				"avg_allowance=%lld avg_spent=%lld avg_used_pct=%lld at_cap=%u borrowing=%u",
				s_strPlayerBotSmPoolWeek.c_str(), d, accounts, fromGrant, accounts - fromGrant, sumBase / accounts,
				sumAllowance / accounts, sumSpent / accounts, sumPct / accounts, atCap, borrowing);
	}
#endif

	// The set chests' results, once a catalogue read: the chances must add up to the million (buy_chest.php refuses
	// a chest whose do not).
	void LoadPlayerBotIshop3ChestDrops()
	{
		if (s_vecPlayerBotIshop3Chests.empty())
			return;
		std::map<DWORD, size_t> byId;
		for (size_t i = 0; i < s_vecPlayerBotIshop3Chests.size(); ++i)
			byId[s_vecPlayerBotIshop3Chests[i].dwChestId] = i;
		{
			std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery(
					"SELECT chest_id, drop_no, ppm FROM itemshop3.chest_drops ORDER BY chest_id, drop_no"));
			if (!msg || !msg->Get() || !msg->Get()->pSQLResult)
				return;
			MYSQL_ROW row;
			while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
			{
				std::map<DWORD, size_t>::const_iterator it = byId.find((DWORD)PlayerBotIshop3Num(row, 0));
				if (it == byId.end())
					continue;
				TPlayerBotIshop3ChestDrop drop;
				drop.iDropNo = (int)PlayerBotIshop3Num(row, 1);
				drop.iPpm = (int)PlayerBotIshop3Num(row, 2);
				s_vecPlayerBotIshop3Chests[it->second].drops.push_back(drop);
			}
		}
		{
			std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery(
					"SELECT chest_id, drop_no, item_no, vnum, count, minutes FROM itemshop3.chest_items "
					"ORDER BY chest_id, drop_no, item_no, alt_no"));
			if (!msg || !msg->Get() || !msg->Get()->pSQLResult)
				return;
			MYSQL_ROW row;
			while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
			{
				std::map<DWORD, size_t>::const_iterator it = byId.find((DWORD)PlayerBotIshop3Num(row, 0));
				if (it == byId.end())
					continue;
				std::vector<TPlayerBotIshop3ChestDrop>& drops = s_vecPlayerBotIshop3Chests[it->second].drops;
				const int dropNo = (int)PlayerBotIshop3Num(row, 1);
				const int itemNo = (int)PlayerBotIshop3Num(row, 2);
				for (size_t d = 0; d < drops.size(); ++d)
				{
					if (drops[d].iDropNo != dropNo)
						continue;
					if (itemNo < 1 || itemNo > 16)
						break;
					if ((int)drops[d].items.size() < itemNo)
						drops[d].items.resize(itemNo);
					TPlayerBotIshop3ChestAlt alt;
					alt.dwVnum = (DWORD)PlayerBotIshop3Num(row, 3);
					alt.dwCount = (DWORD)std::max<long long>(1, PlayerBotIshop3Num(row, 4));
					alt.dwMinutes = (DWORD)std::max<long long>(0, PlayerBotIshop3Num(row, 5));
					if (ITEM_MANAGER::instance().GetTable(alt.dwVnum))
						drops[d].items[itemNo - 1].push_back(alt);
					break;
				}
			}
		}
		// a chest whose chances are not the million, or with a result of no item, is not bought
		std::vector<TPlayerBotIshop3Chest> sound;
		for (size_t i = 0; i < s_vecPlayerBotIshop3Chests.size(); ++i)
		{
			const TPlayerBotIshop3Chest& c = s_vecPlayerBotIshop3Chests[i];
			long long ppm = 0;
			bool ok = !c.drops.empty();
			for (size_t d = 0; d < c.drops.size(); ++d)
			{
				ppm += c.drops[d].iPpm;
				for (size_t k = 0; k < c.drops[d].items.size(); ++k)
					if (c.drops[d].items[k].empty())
						ok = false;
				if (c.drops[d].items.empty())
					ok = false;
			}
			if (ok && ppm == 1000000)
				sound.push_back(c);
		}
		s_vecPlayerBotIshop3Chests.swap(sound);
	}

	// The V3 catalogue into the tables; the lines kept. 0: the view could not be read (asked again soon).
	unsigned int RefreshPlayerBotIshop3Catalogue(bool arezzoClosed)
	{
		s_vecPlayerBotIshop3Chests.clear();
		std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery(
				"SELECT s.id, s.category, s.pay_type, s.coins, s.discount, s.count, s.vnum, s.socket0, s.socket1, s.socket2, "
				"s.time, s.min_level, s.stackable, COALESCE(s.vip, 0), COALESCE(s.auction, 0), s.arezzo_locked, s.chest, "
				"COALESCE(s.available, 0), COALESCE(c.kind, '') "
				"FROM itemshop3.shop s LEFT JOIN itemshop3.categories c ON c.id = s.category"));
		if (!msg || !msg->Get() || !msg->Get()->pSQLResult)
			return 0;
		unsigned int kept = 0, rows = 0, chests = 0;
		MYSQL_ROW row;
		while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			++rows;
			const DWORD id = (DWORD)PlayerBotIshop3Num(row, 0);
			const long long category = PlayerBotIshop3Num(row, 1);
			const int payType = (int)PlayerBotIshop3Num(row, 2);
			const long long coins = PlayerBotIshop3Num(row, 3);
			const long long discount = PlayerBotIshop3Num(row, 4);
			const long long count = PlayerBotIshop3Num(row, 5);
			const DWORD vnum = (DWORD)PlayerBotIshop3Num(row, 6);
			const long long minutes = PlayerBotIshop3Num(row, 10);
			const long long minLevel = PlayerBotIshop3Num(row, 11);
			const bool vip = PlayerBotIshop3Num(row, 13) != 0;
			const bool auction = PlayerBotIshop3Num(row, 14) != 0;
			const bool arezzoLocked = PlayerBotIshop3Num(row, 15) != 0;
			const DWORD chest = (DWORD)PlayerBotIshop3Num(row, 16);
			const bool available = PlayerBotIshop3Num(row, 17) == 1;
			const char* kind = row[18] ? row[18] : "";
			// Shop::getItemPrice: the discount's whole per cent off
			const long long price = coins - (long long)((double)discount / 100.0 * (double)coins);
			if (category <= 0 || vip || auction || arezzoLocked || !available || price <= 0 || price > INT_MAX ||
					count <= 0 || (payType != 1 && payType != 2))
				continue;
			if (chest != 0)
			{
				// MT2009_PLUS_BOT_ISHOP_V3_V1 (phase 2): the costume set chests only, for Smocze Monety
				if (strcmp(kind, "sets") == 0 && payType == 1)
				{
					TPlayerBotIshop3Chest c;
					c.dwLine = id;
					c.dwChestId = chest;
					c.dwPrice = (DWORD)price;
					c.dwRolls = (DWORD)std::min<long long>(count, 100);
					c.bMinLevel = (BYTE)std::min<long long>(std::max<long long>(minLevel, 0), 255);
					s_vecPlayerBotIshop3Chests.push_back(c);
					++chests;
				}
				continue;
			}
			if (IsPlayerBotIshop3ExcludedVnum(vnum))
				continue;
			const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
			if (!proto)
				continue;
			// the Arezzo costume sets while the module is off (the view says it too - arezzo_locked)
			if (arezzoClosed && mt2009_arezzo_costumes::IsItem(vnum))
				continue;
			TPlayerBotItemShopEntry entry = TPlayerBotItemShopEntry();
			entry.dwIndex = id;
			entry.dwPrice = (DWORD)price;
			entry.dwCount = (DWORD)std::min<long long>(count, 10000);
			entry.bMinLevel = (BYTE)std::min<long long>(std::max<long long>(minLevel, 0), 255);
			entry.dwMinutes = (DWORD)std::max<long long>(0, minutes);
			entry.bStackable = PlayerBotIshop3Num(row, 12) != 0 && IS_SET(proto->dwFlags, ITEM_FLAG_STACKABLE) &&
					!IS_SET(proto->dwAntiFlags, ITEM_ANTIFLAG_STACK);
			for (int i = 0; i < ITEM_SOCKET_MAX_NUM && i < 3; ++i)
				entry.alSockets[i] = (long)PlayerBotIshop3Num(row, 7 + i);
			AddPlayerBotItemShopLine(vnum, proto, entry, payType == 2);
			++kept;
		}
		LoadPlayerBotIshop3ChestDrops();
		sys_log(0, "PLAYERBOT_ISHOP3: catalogue rows=%u lines=%u coins=%u marks=%u chests=%u/%u hairstyles=%u costumes=%u "
				"weapon_skins=%u pets=%u mounts=%u",
				rows, kept, (unsigned int)s_mapPlayerBotItemShopCoins.size(), (unsigned int)s_mapPlayerBotItemShopMarks.size(),
				(unsigned int)s_vecPlayerBotIshop3Chests.size(), chests, (unsigned int)s_vecPlayerBotItemShopHair.size(),
				(unsigned int)s_vecPlayerBotItemShopBody.size(), (unsigned int)s_vecPlayerBotItemShopWeaponSkin.size(),
				(unsigned int)s_vecPlayerBotItemShopPet.size(), (unsigned int)s_vecPlayerBotItemShopMount.size());
		return kept;
	}
#endif

	void RefreshPlayerBotItemShopCatalogue(DWORD dwNow)
	{
		// MT2009_PLUS_AREZZO_COSTUME_SETS_V2: the Arezzo module switched on or off (the panel, live) -
		// the catalogue again at once, with or without the Arezzo costume sets.
		static int s_iPlayerBotItemShopArezzoClosed = -1;
		const int arezzoClosed = mt2009_arezzo_costumes::ModuleClosed() ? 1 : 0;
		if (arezzoClosed != s_iPlayerBotItemShopArezzoClosed)
		{
			s_iPlayerBotItemShopArezzoClosed = arezzoClosed;
			s_dwNextPlayerBotItemShopScan = 0;
		}
#ifdef MT2009_PLUS_BOT_ISHOP_V3_V1
		// MT2009_PLUS_BOT_ISHOP_V3_V1: the source switched (the panel, live) - the other catalogue at once.
		static int s_iPlayerBotItemShopSourceRead = -1;
		const int source = GetPlayerBotItemShopSource();
		if (source != s_iPlayerBotItemShopSourceRead)
		{
			s_iPlayerBotItemShopSourceRead = source;
			s_dwNextPlayerBotItemShopScan = 0;
		}
#endif
		if (s_dwNextPlayerBotItemShopScan != 0 && dwNow < s_dwNextPlayerBotItemShopScan)
			return;
		s_dwNextPlayerBotItemShopScan = dwNow + PLAYERBOT_ISHOP_CATALOGUE_INTERVAL;
		s_mapPlayerBotItemShopCoins.clear();
		s_mapPlayerBotItemShopMarks.clear();
		s_vecPlayerBotItemShopHair.clear();
		s_vecPlayerBotItemShopBody.clear();
		s_vecPlayerBotItemShopWeaponSkin.clear();
		s_vecPlayerBotItemShopPet.clear();
		s_vecPlayerBotItemShopMount.clear();
#ifdef MT2009_PLUS_BOT_ISHOP_V3_V1
		if (source == 2)
		{
			if (RefreshPlayerBotIshop3Catalogue(arezzoClosed != 0) == 0)
				s_dwNextPlayerBotItemShopScan = dwNow + 5 * 60 * 1000;
			return;
		}
		s_vecPlayerBotIshop3Chests.clear();
#endif

		CItemShopManager& shop = CItemShopManager::instance();
		unsigned int entries = 0;
		for (int index = 1; index <= PLAYERBOT_ISHOP_MAX_INDEX; ++index)
		{
			if (!shop.IsItemExist(index))
				continue;
			TItemShopItem item = shop.GetItem(index);
			if (!shop.IsProperItem(item) || item.dwCount == 0 || shop.IsItemTimeAuction(item))
				continue;
			const TItemTable* proto = ITEM_MANAGER::instance().GetTable(item.dwVnum);
			if (!proto)
				continue;
			++entries;
			// MT2009_PLUS_COLLECTOR_ITEM_V1: "Kolekcjoner" opens the collector's
			// storage, which a bot never uses (playerbot_collector.h) - its lines
			// are no bot's goods, whatever a wish may name later.
			if (item.dwVnum == playerbot_collector::ITEM_VNUM)
				continue;
			// MT2009_PLUS_AREZZO_COSTUME_SETS_V2: the Arezzo costume sets are no bot's goods while the
			// Arezzo module is off (the engine's BuyItem refuses them too).
			if (arezzoClosed && mt2009_arezzo_costumes::IsItem(item.dwVnum))
				continue;
			TPlayerBotItemShopEntry entry = TPlayerBotItemShopEntry();
			entry.dwIndex = item.dwIndex;
			entry.dwPrice = shop.GetItemPrice(item);
			entry.dwCount = item.dwCount;
			entry.bMinLevel = item.bMinLevel;
			const bool marks = shop.GetItemCurrency(item) == CItemShopManager::CURRENCY_DRAGON_MARK;
			AddPlayerBotItemShopLine(item.dwVnum, proto, entry, marks);
		}
		if (entries == 0)
		{
			// The db core has not sent the catalogue yet: ask again soon.
			s_dwNextPlayerBotItemShopScan = dwNow + 5 * 60 * 1000;
			return;
		}
		sys_log(0, "PLAYERBOT_ISHOP: catalogue entries=%u coins=%u marks=%u hairstyles=%u costumes=%u weapon_skins=%u pets=%u mounts=%u",
				entries, (unsigned int)s_mapPlayerBotItemShopCoins.size(),
				(unsigned int)s_mapPlayerBotItemShopMarks.size(), (unsigned int)s_vecPlayerBotItemShopHair.size(),
				(unsigned int)s_vecPlayerBotItemShopBody.size(), (unsigned int)s_vecPlayerBotItemShopWeaponSkin.size(),
				(unsigned int)s_vecPlayerBotItemShopPet.size(), (unsigned int)s_vecPlayerBotItemShopMount.size());
	}

	void RefreshPlayerBotDragonBalance(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		const CItemShopManager::PlayerAccountBalance balance = CItemShopManager::instance().GetPlayerAccountBalance(ch);
		state.iDragonCoins = (int)std::min<DWORD>(balance.dwDragonCoins, INT_MAX);
		state.iDragonMarks = (int)std::min<DWORD>(balance.dwDragonMarks, INT_MAX);
		state.bDragonBalanceKnown = true;
		state.dwNextItemShopBalanceTime = dwNow + PLAYERBOT_ISHOP_BALANCE_INTERVAL;
	}

#ifdef MT2009_PLUS_BOT_ISHOP_V3_V1
	// MT2009_PLUS_BOT_ISHOP_V3_V1: the balance read fresh before a purchase session - the weekly grants
	// (account.sm_grant_tier) and the panel put coins on the account outside the core - unless it was read within
	// PLAYERBOT_ISHOP3_FRESH_MS, or a charge of this bot's is still on its way through the db core (a read then would
	// show the coins it already spent).
	void EnsurePlayerBotIshop3FreshBalance(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		std::map<DWORD, DWORD>::const_iterator charge = s_mapPlayerBotIshop3LastCharge.find(ch->GetPlayerID());
		if (state.bDragonBalanceKnown && charge != s_mapPlayerBotIshop3LastCharge.end() &&
				(int)(dwNow - charge->second) < (int)PLAYERBOT_ISHOP3_CHARGE_SETTLE_MS)
			return;
		const DWORD readAt = state.dwNextItemShopBalanceTime - PLAYERBOT_ISHOP_BALANCE_INTERVAL;
		if (state.bDragonBalanceKnown && state.dwNextItemShopBalanceTime != 0 &&
				(int)(dwNow - readAt) < (int)PLAYERBOT_ISHOP3_FRESH_MS)
			return;
		RefreshPlayerBotDragonBalance(ch, state, dwNow);
	}

	// The line's time into a new item, as Player::CreateItem (shop3/include/classes/Player.php) writes it for the
	// ItemShop storage: a unique item's remaining time (or its end), a real-time item's end, a first-use item's and a
	// worn-time item's seconds.
	void ApplyPlayerBotIshop3Time(LPITEM item, const TItemTable* proto, DWORD minutes)
	{
		if (!item || !proto || minutes == 0)
			return;
		const long secs = (long)minutes * 60;
		const long now = (long)get_global_time();
		if (proto->bType == ITEM_UNIQUE)
		{
			item->SetSocket(ITEM_SOCKET_UNIQUE_REMAIN_TIME, proto->alValues[2] == 0 ? secs : now + secs);
			return;
		}
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
		{
			const BYTE type = proto->aLimits[i].bType;
			if (type == LIMIT_REAL_TIME)
				item->SetSocket(0, now + secs);
			else if (type == LIMIT_REAL_TIME_START_FIRST_USE)
				item->SetSocket(0, proto->aLimits[i].lValue ? secs : now + secs);
			else if (type == LIMIT_TIMER_BASED_ON_WEAR)
				item->SetSocket(0, secs);
		}
	}

	// The charge (negative) or the refund (positive) of a purchase. A Smocze Monety charge gives the price back as
	// Smocze Znaki in the same UPDATE (ClientManager::ChargeCash: cash_mark + |second|), so its refund takes them back.
	void ChargePlayerBotIshop3(LPCHARACTER ch, bool marks, long long amount)
	{
		if (amount == 0)
			return;
		CItemShopManager& shop = CItemShopManager::instance();
		if (marks)
		{
			shop.AddCash(ch, ERequestCharge_Marks, (long)amount, false);
			return;
		}
		shop.AddCash(ch, ERequestCharge_Cash, (long)amount, false);
		if (amount > 0)
			shop.AddCash(ch, ERequestCharge_Marks, -(long)amount, false);
	}

	// The log.itemshop row of a bot's V3 purchase (V3's own history and so "Popularne" never see it).
	void LogPlayerBotIshop3(LPCHARACTER ch, DWORD line, DWORD vnum, int qty, long long price, bool marks, DWORD itemId,
			int before)
	{
		LogManager::instance().Query("INSERT INTO itemshop (pid, aid, item_index, vnum, quantity, price, currency, item_id, "
				"time, money_before) VALUES (%u, %u, %u, %u, %d, %lld, %d, %u, NOW(), %u)",
				ch->GetPlayerID(), ch->GetDesc()->GetAccountTable().id, line, vnum, qty, price,
				marks ? PLAYERBOT_ISHOP3_LOG_CURRENCY_MARKS : PLAYERBOT_ISHOP3_LOG_CURRENCY_COINS, itemId,
				(unsigned int)std::max(0, before));
	}

	// One purchase of a V3 line, qty times (1..10; one of what does not stack): the balance fresh, the bag's room for
	// every piece, the charge, the goods, the log, the money back for what could not be given. The state's balance
	// follows (a Smocze Monety purchase adds its price in Smocze Znaki).
	bool BuyPlayerBotIshop3Line(LPCHARACTER ch, TPlayerBotAIState& state, const TPlayerBotItemShopEntry& line, DWORD vnum,
			bool marks, int qty, const char* reason, DWORD dwNow)
	{
		TPlayerBotIshop3Census& census = GetPlayerBotIshop3Census(GetPlayerBotIshop3Category(reason));
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
		if (!ch || !ch->GetDesc() || !proto || line.dwCount == 0 || ch->GetLevel() < line.bMinLevel)
		{
			++census.uNotListed;
			return false;
		}
		if (!line.bStackable)
			qty = 1;
		qty = std::max(1, std::min(qty, PLAYERBOT_ISHOP3_MAX_QTY));
		EnsurePlayerBotIshop3FreshBalance(ch, state, dwNow);
		const long long price = (long long)line.dwPrice * qty;
		const int before = marks ? state.iDragonMarks : state.iDragonCoins;
		if (price <= 0 || price > INT_MAX || (long long)before < price)
		{
			++census.uNoCoins;
			return false;
		}
#ifdef MT2009_PLUS_BOT_SM_DAILY_POOL_V1
		// MT2009_PLUS_BOT_SM_DAILY_POOL_V1: a Smocze Monety line within the day's allowance (an urgent one: tomorrow's)
		bool poolBorrow = false;
		if (!marks)
		{
			const TPlayerBotSmPoolRoom pool = GetPlayerBotSmPoolRoom(ch, state, reason);
			if (price > pool.Room())
			{
				++census.uPoolBlock;
				PlayerBotLogThrottled("ishop3_pool_block", dwNow,
						"PLAYERBOT_ISHOP3: pool block pid=%u name=%s line=%u vnum=%u price=%lld reason=%s urgent=%d today=%lld "
						"tomorrow=%lld coins=%d", ch->GetPlayerID(), ch->GetName(), line.dwIndex, vnum, price,
						reason ? reason : "-", (int)pool.bUrgent, pool.llToday, pool.llTomorrow, state.iDragonCoins);
				return false;
			}
			poolBorrow = pool.bActive && price > pool.llToday;
		}
#endif
		const DWORD pieces = line.dwCount * (DWORD)qty;
		const DWORD stack = line.bStackable ? std::max<DWORD>(1, std::min<DWORD>(proto->dwMaxStack, 200)) : 1;
		const DWORD chunks = (pieces + stack - 1) / stack;
		const int size = std::max<int>(1, proto->bSize);
		if (chunks == 1 ? ch->GetEmptyInventory((BYTE)size) < 0
				: CountPlayerBotFreeInventoryCells(ch) < (int)(chunks * size) + 1)
		{
			++census.uBagFull;
			PlayerBotLogThrottled("ishop3_bag_full", dwNow,
					"PLAYERBOT_ISHOP3: bag full pid=%u name=%s line=%u vnum=%u pieces=%u reason=%s", ch->GetPlayerID(),
					ch->GetName(), line.dwIndex, vnum, pieces, reason ? reason : "-");
			return false;
		}
		ChargePlayerBotIshop3(ch, marks, -price);
		s_mapPlayerBotIshop3LastCharge[ch->GetPlayerID()] = dwNow;
		// a timed piece, or one with the line's sockets, is a new item of its own (never merged into a stack)
		bool ownSockets = false;
		for (int i = 0; i < ITEM_SOCKET_MAX_NUM && i < 3; ++i)
			if (line.alSockets[i] > 0)
				ownSockets = true;
		const bool fresh = line.dwMinutes > 0 || ownSockets;
		DWORD delivered = 0, lastId = 0;
		for (DWORD left = pieces; left > 0;)
		{
			const DWORD n = std::min(left, stack);
			LPITEM item = ch->AutoGiveItem(vnum, (ITEM_COUNT)n, -1, false, fresh);
			if (!item)
				break;
			if (fresh)
			{
				for (int i = 0; i < ITEM_SOCKET_MAX_NUM && i < 3; ++i)
					if (line.alSockets[i] > 0)
						item->SetSocket(i, line.alSockets[i]);
				ApplyPlayerBotIshop3Time(item, proto, line.dwMinutes);
			}
			lastId = item->GetID();
			delivered += n;
			left -= n;
		}
		long long refund = 0;
		if (delivered < pieces)
		{
			refund = price * (long long)(pieces - delivered) / (long long)pieces;
			ChargePlayerBotIshop3(ch, marks, refund);
			++census.uRefunds;
		}
		const long long paid = price - refund;
		if (marks)
			state.iDragonMarks = (int)std::max<long long>(0, (long long)state.iDragonMarks - paid);
		else
		{
			state.iDragonCoins = (int)std::max<long long>(0, (long long)state.iDragonCoins - paid);
			state.iDragonMarks = (int)std::min<long long>((long long)state.iDragonMarks + paid, INT_MAX);
		}
		if (delivered == 0)
		{
			sys_log(0, "PLAYERBOT_ISHOP3: not given, refunded pid=%u name=%s line=%u vnum=%u price=%lld %s reason=%s",
					ch->GetPlayerID(), ch->GetName(), line.dwIndex, vnum, price, marks ? "SZ" : "SM", reason ? reason : "-");
			return false;
		}
		LogPlayerBotIshop3(ch, line.dwIndex, vnum, qty, paid, marks, lastId, before);
#ifdef MT2009_PLUS_BOT_SM_DAILY_POOL_V1
		if (!marks)
			NotePlayerBotSmPoolSpent(ch, paid);
		if (poolBorrow)
			++census.uPoolBorrow;
#endif
		++census.uBuys;
		census.uPieces += delivered;
		(marks ? census.llMarks : census.llCoins) += paid;
		++s_uPlayerBotItemShopBuys;
		s_mapPlayerBotItemShopBought[vnum] += delivered;
		sys_log(0, "PLAYERBOT_ISHOP3: bought pid=%u name=%s lv=%d line=%u vnum=%u qty=%d pieces=%u price=%lld %s goal=%s "
				"before=%d after=%d coins=%d marks=%d refund=%lld",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), line.dwIndex, vnum, qty, delivered, paid, marks ? "SZ" : "SM",
				reason ? reason : "-", before, marks ? state.iDragonMarks : state.iDragonCoins, state.iDragonCoins,
				state.iDragonMarks, refund);
		return true;
	}

	// MT2009_PLUS_BOT_ISHOP_V3_V1 (phase 2): a set chest bought and rolled as buy_chest.php rolls it - each roll one of
	// the chest's results by its chance (1..1 000 000 against the results in their order), each item of the result
	// the alternative this bot can wear (sex, class - any when none fits), given with its minutes; every roll logged
	// in itemshop3.chest_rolls (token: the bots' own, ending in b07b07) and the purchase in log.itemshop.
	unsigned int s_uPlayerBotIshop3ChestToken = 0;

	bool BuyPlayerBotIshop3Chest(LPCHARACTER ch, TPlayerBotAIState& state, const TPlayerBotIshop3Chest& chest, int qty,
			DWORD dwNow)
	{
		TPlayerBotIshop3Census& census = GetPlayerBotIshop3Census("chest");
		if (!ch || !ch->GetDesc() || chest.drops.empty() || ch->GetLevel() < chest.bMinLevel)
		{
			++census.uNotListed;
			return false;
		}
		size_t widest = 1;
		for (size_t d = 0; d < chest.drops.size(); ++d)
			widest = std::max(widest, chest.drops[d].items.size());
		const int rollsPer = (int)std::max<DWORD>(1, chest.dwRolls);
		const int room = CountPlayerBotFreeInventoryCells(ch) - 2;
		qty = std::max(1, std::min(qty, PLAYERBOT_ISHOP3_MAX_QTY));
		while (qty > 0 && qty * rollsPer * (int)widest * 3 > room)	// a costume / a skin may take three cells
			--qty;
		if (qty <= 0)
		{
			++census.uBagFull;
			return false;
		}
		EnsurePlayerBotIshop3FreshBalance(ch, state, dwNow);
		const long long price = (long long)chest.dwPrice * qty;
		const int before = state.iDragonCoins;
		if (price <= 0 || price > INT_MAX || (long long)before < price)
		{
			++census.uNoCoins;
			return false;
		}
#ifdef MT2009_PLUS_BOT_SM_DAILY_POOL_V1
		// MT2009_PLUS_BOT_SM_DAILY_POOL_V1: a chest is never urgent - today's allowance only
		if (price > GetPlayerBotSmPoolRoom(ch, state, "chest").Room())
		{
			++census.uPoolBlock;
			return false;
		}
#endif
		ChargePlayerBotIshop3(ch, false, -price);
		s_mapPlayerBotIshop3LastCharge[ch->GetPlayerID()] = dwNow;
		char token[40];
		snprintf(token, sizeof(token), "%08x%08x%08x%08x", ch->GetPlayerID(), (unsigned int)get_global_time(),
				++s_uPlayerBotIshop3ChestToken, 0x00b07b07U);
		const DWORD aid = ch->GetDesc()->GetAccountTable().id;
		const int rolls = qty * rollsPer;
		int given = 0, failed = 0;
		std::string won;
		for (int n = 1; n <= rolls; ++n)
		{
			const int rnd = number(1, 1000000);
			int acc = 0;
			const TPlayerBotIshop3ChestDrop* drop = &chest.drops.back();
			for (size_t d = 0; d < chest.drops.size(); ++d)
			{
				acc += chest.drops[d].iPpm;
				if (rnd <= acc)
				{
					drop = &chest.drops[d];
					break;
				}
			}
			std::string vnums, ids;
			for (size_t k = 0; k < drop->items.size(); ++k)
			{
				const std::vector<TPlayerBotIshop3ChestAlt>& alts = drop->items[k];
				std::vector<const TPlayerBotIshop3ChestAlt*> fit;
				for (size_t a = 0; a < alts.size(); ++a)
					if (IsPlayerBotProtoForCharacter(ch, ITEM_MANAGER::instance().GetTable(alts[a].dwVnum)))
						fit.push_back(&alts[a]);
				if (fit.empty())
					for (size_t a = 0; a < alts.size(); ++a)
						fit.push_back(&alts[a]);
				const TPlayerBotIshop3ChestAlt* pick = fit[number(0, (int)fit.size() - 1)];
				const TItemTable* proto = ITEM_MANAGER::instance().GetTable(pick->dwVnum);
				LPITEM item = proto ? ch->AutoGiveItem(pick->dwVnum, (ITEM_COUNT)pick->dwCount, -1, false, true) : NULL;
				if (!item)
				{
					++failed;
					continue;
				}
				ApplyPlayerBotIshop3Time(item, proto, pick->dwMinutes);
				char buf[24];
				snprintf(buf, sizeof(buf), "%s%u", vnums.empty() ? "" : ",", pick->dwVnum);
				vnums += buf;
				snprintf(buf, sizeof(buf), "%s%u", ids.empty() ? "" : ",", item->GetID());
				ids += buf;
				++given;
			}
			if (vnums.size() > 250)
				vnums.resize(250);
			if (ids.size() > 250)
				ids.resize(250);
			DBManager::instance().Query("INSERT INTO itemshop3.chest_rolls (token, account, pid, line, chest_id, roll_no, "
					"drop_no, ppm, rnd, label, vnums, award_ids, price, pay_type) SELECT '%s', %u, %u, %u, %u, %d, drop_no, ppm, "
					"%d, label, '%s', '%s', %u, 1 FROM itemshop3.chest_drops WHERE chest_id = %u AND drop_no = %d",
					token, aid, ch->GetPlayerID(), chest.dwLine, chest.dwChestId, n, rnd, vnums.c_str(), ids.c_str(),
					chest.dwPrice, chest.dwChestId, drop->iDropNo);
			if (!vnums.empty() && won.size() < 200)
				won += (won.empty() ? "" : "|") + vnums;
		}
		// nothing given at all: the money back (a piece or two short: kept, as a roll of the common results)
		if (given == 0)
		{
			ChargePlayerBotIshop3(ch, false, price);
			++census.uRefunds;
			sys_log(0, "PLAYERBOT_ISHOP3: chest not given, refunded pid=%u name=%s line=%u price=%lld", ch->GetPlayerID(),
					ch->GetName(), chest.dwLine, price);
			return false;
		}
		state.iDragonCoins = (int)std::max<long long>(0, (long long)state.iDragonCoins - price);
		state.iDragonMarks = (int)std::min<long long>((long long)state.iDragonMarks + price, INT_MAX);
		LogPlayerBotIshop3(ch, chest.dwLine, 0, qty, price, false, 0, before);
#ifdef MT2009_PLUS_BOT_SM_DAILY_POOL_V1
		NotePlayerBotSmPoolSpent(ch, price);
#endif
		++census.uBuys;
		census.uPieces += (unsigned int)given;
		census.llCoins += price;
		++s_uPlayerBotItemShopBuys;
		sys_log(0, "PLAYERBOT_ISHOP3: chest pid=%u name=%s lv=%d line=%u chest=%u qty=%d rolls=%d price=%lld before=%d "
				"after=%d given=%d failed=%d won=%s",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), chest.dwLine, chest.dwChestId, qty, rolls, price, before,
				state.iDragonCoins, given, failed, won.empty() ? "-" : won.c_str());
		return true;
	}

	// The census, hourly: per category the coins and marks spent, the purchases and pieces, and why none was made -
	// no_coins (the balance), not_listed (V3 sells no such line for the bot), bag_full, refunds.
	DWORD s_dwNextPlayerBotIshop3Census = 0;

	void WritePlayerBotIshop3Census(DWORD dwNow)
	{
		if (s_dwNextPlayerBotIshop3Census == 0)
		{
			s_dwNextPlayerBotIshop3Census = dwNow + 60 * 60 * 1000;
			return;
		}
		if (dwNow < s_dwNextPlayerBotIshop3Census)
			return;
		s_dwNextPlayerBotIshop3Census = dwNow + 60 * 60 * 1000;
#ifdef MT2009_PLUS_BOT_SM_DAILY_POOL_V1
		WritePlayerBotSmPoolCensus();
#endif
		if (s_mapPlayerBotIshop3Census.empty())
			return;
		std::string out;
		char buf[256];
		for (std::map<std::string, TPlayerBotIshop3Census>::const_iterator it = s_mapPlayerBotIshop3Census.begin();
				it != s_mapPlayerBotIshop3Census.end(); ++it)
		{
			const TPlayerBotIshop3Census& c = it->second;
			snprintf(buf, sizeof(buf), "%s%s=spent_sm:%lld,spent_sz:%lld,count:%u,pieces:%u,no_coins:%u,not_listed:%u,"
					"bag_full:%u,refunds:%u,pool_block:%u,pool_borrow:%u", out.empty() ? "" : " ", it->first.c_str(), c.llCoins,
					c.llMarks, c.uBuys, c.uPieces, c.uNoCoins, c.uNotListed, c.uBagFull, c.uRefunds, c.uPoolBlock, c.uPoolBorrow);
			out += buf;
		}
		sys_log(0, "PLAYERBOT_ISHOP3: census source=%s %s", GetPlayerBotItemShopSource() == 2 ? "v3" :
				(GetPlayerBotItemShopSource() == 1 ? "game" : "off"), out.c_str());
		s_mapPlayerBotIshop3Census.clear();
	}
#endif

	// The saddlebag page too (INVENTORY_MAX_NUM, not PLAYERBOT_BAG_CELLS): a
	// coupon the panel hands a bot with a full bag lands in its open rows.
	LPITEM FindPlayerBotVoucher(LPCHARACTER ch)
	{
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && !item->isLocked() && !item->IsExchanging() &&
					item->GetVnum() >= PLAYERBOT_ISHOP_VOUCHER_MIN_VNUM &&
					item->GetVnum() <= PLAYERBOT_ISHOP_VOUCHER_MAX_VNUM)
				return item;
		}
		return NULL;
	}

	// Every voucher in the bag in one pass, every unit of every stack - the
	// charge the package's quest makes for a player (AddCash through the db
	// core, cash += value, the itemshop_dragon_scroll row), without its
	// dialog. It was one unit a pass, and a pass comes every ten minutes: a
	// stack of 200 took a day and a half, and a bot handed coupons by the
	// panel sat on almost all of them ("boty maja klikac wszystkie kupony SM,
	// a nie tylko 50", operator, 26 September 2026). The quest itself is not
	// run - item.remove() there takes the whole stack for one charge, and a
	// dialog-free UseItem would still cost the bot the flag the quest checks;
	// the flag is honoured here.
	// What a bot's vouchers brought it since this core first cashed one for
	// it: the pace a need it cannot pay for yet is saved up at
	// (PlayerBotSavesForWish). A restart starts the count again.
	struct TPlayerBotCoinIncome
	{
		int iSince;
		long long llCoins;
	};
	std::map<DWORD, TPlayerBotCoinIncome> s_mapPlayerBotCoinIncome;

	void NotePlayerBotCoinIncome(DWORD pid, long long coins)
	{
		std::map<DWORD, TPlayerBotCoinIncome>::iterator it = s_mapPlayerBotCoinIncome.find(pid);
		if (it == s_mapPlayerBotCoinIncome.end())
		{
			TPlayerBotCoinIncome income = { get_global_time(), 0 };
			it = s_mapPlayerBotCoinIncome.insert(std::make_pair(pid, income)).first;
		}
		it->second.llCoins += coins;
	}

	bool UsePlayerBotVoucher(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (quest::CQuestManager::instance().GetEventFlag("block_dragon_voucher") > 0)
			return false;
		int cashed = 0;
		long long total = 0;
		for (LPITEM voucher = FindPlayerBotVoucher(ch); voucher; voucher = FindPlayerBotVoucher(ch))
		{
			const int value = voucher->GetValue(0);
			const int count = (int)voucher->GetCount();
			if (value <= 0 || count <= 0)
				break;
			// One charge for the stack, kept inside the packet's long.
			const long long coins = (long long)value * count;
			if (coins > INT_MAX || !CItemShopManager::instance().AddCash(ch, ERequestCharge_Cash, (long)coins, false))
				break;
			LogManager::instance().Query("INSERT INTO itemshop_dragon_scroll VALUES (%u, %u, NOW(), %u, %lld)",
					ch->GetPlayerID(), ch->GetDesc()->GetAccountTable().id, voucher->GetID(), coins);
			ITEM_MANAGER::instance().RemoveItem(voucher, "PLAYERBOT_VOUCHER");
			state.iDragonCoins = (int)std::min<long long>((long long)state.iDragonCoins + coins, INT_MAX);
			NotePlayerBotCoinIncome(ch->GetPlayerID(), coins);
			s_uPlayerBotVouchersUsed += (unsigned int)count;
			s_uPlayerBotCoinsCharged += (unsigned int)coins;
			cashed += count;
			total += coins;
		}
		if (cashed == 0)
			return false;
		sys_log(0, "PLAYERBOT_ISHOP: voucher cashed pid=%u name=%s vouchers=%d coins=%lld balance=%d",
				ch->GetPlayerID(), ch->GetName(), cashed, total, state.iDragonCoins);
		if (IsPlayerBotSidekickPID(ch->GetPlayerID()))
			NotePlayerBotSidekickVouchers(ch, total, state.iDragonCoins);
		return true;
	}

	// The vouchers, every minute and ahead of the stall: a bot standing at its
	// counter ends its pass in ManagePlayerBotPrivateShop and never reached
	// the ItemShop's upkeep, so the coupons the panel handed out sat in the
	// bags of every stall keeper - 13 cashed of 1578 delivered in half an
	// hour on the test world (26 September 2026). The account is read first
	// when its balance is not known or due, never on the heels of a charge.
	// MT2009_PLUS_MARKET_LIFE_V1, point 6: a voucher seller whose needs the
	// balance covers keeps its vouchers for its counter (defined below).
	bool PlayerBotKeepsVouchersForCounter(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow);

	void CashPlayerBotVouchers(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || ch->IsDead() || !ch->GetDesc() || dwNow < state.dwNextVoucherCheckTime)
			return;
		state.dwNextVoucherCheckTime = dwNow + PLAYERBOT_ISHOP_VOUCHER_CHECK_INTERVAL +
				PlayerBotNavHash(ch->GetPlayerID() ^ 0x564f5543U) % 15000U;
		// MT2009_PLUS_SIDEKICK_COINS_V1: a companion by its owner's switch.
		const bool sidekick = IsPlayerBotSidekickPID(ch->GetPlayerID());
		if ((sidekick ? !IsPlayerBotSidekickCoinsOn(ch->GetPlayerID()) : !IsPlayerBotItemShopEnabled()) ||
				ch->GetExchange() || !FindPlayerBotVoucher(ch))
			return;
		if (!state.bDragonBalanceKnown || dwNow >= state.dwNextItemShopBalanceTime)
			RefreshPlayerBotDragonBalance(ch, state, dwNow);
		if (!sidekick && PlayerBotKeepsVouchersForCounter(ch, state, dwNow))
			return;
		UsePlayerBotVoucher(ch, state, dwNow);
	}

	// --------------------------------------------------------------- wishes

	struct TPlayerBotItemShopWish
	{
		DWORD dwVnum;
		bool bMarks;
		const char* szReason;
	};

	// A Grand Master skill the training pass could train now, and no stone.
	bool PlayerBotWantsGrandMasterStone(LPCHARACTER ch)
	{
		if (ch->GetSkillGroup() == 0)
			return false;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetVnum() == PLAYERBOT_GRAND_MASTER_STONE_VNUM)
				return false;
		}
		const TJobSkillBuild build = GetPlayerBotSkillBuild(ch->GetJob(), ch->GetSkillGroup(), ch->GetPlayerID());
		for (BYTE i = 0; i < build.bSkillCount; ++i)
		{
			const DWORD vnum = build.dwSkills[i];
			if (vnum == 0 || ch->GetSkillMasterType(vnum) != SKILL_GRAND_MASTER)
				continue;
			const int level = ch->GetSkillLevel(vnum);
			if (level < 30 || level >= 40)
				continue;
			const int cost = GetPlayerBotGrandMasterRankCost(level);
			// MT2009_PLUS_SIDEKICK_ZEN_BEAN_TRAINING_V1: the beans in the bag count.
			if (ch->GetRealAlignment() + GetPlayerBotZenBeanLift(ch) - cost >= 0)
				return true;
		}
		return false;
	}

	// The worn weapon the reroll pass would reroll if it had a stone, and no
	// stone in the bag: the same tests ManagePlayerBotBonusReroll makes.
	bool PlayerBotWantsChangeStone(LPCHARACTER ch)
	{
		if (ch->GetLevel() < PLAYERBOT_BONUS_MIN_LEVEL)
			return false;
		LPITEM weapon = ch->GetWear(WEAR_WEAPON);
		if (!CanPlayerBotRerollItem(weapon))
			return false;
		if (weapon->GetAttributeCount() < PLAYERBOT_BONUS_MAX_LINES ||
				weapon->GetRefineLevel() < PLAYERBOT_BONUS_CHANGE_MIN_REFINE)
			return false;
		// Whether an ordinary change would still move it towards its finish,
		// asked the way the pass asks it (PlayerBotWantsBonusChange).
		const TPlayerBotBonusTarget target = { weapon, (BYTE)WEAR_WEAPON, (BYTE)PLAYERBOT_BONUS_TARGET_WORN,
				(BYTE)playerbot_bonus_rules::PLAIN_CATEGORY };
		if (!PlayerBotWantsBonusChange(ch, target, false))
			return false;
		return !HasPlayerBotBonusStone(ch, PLAYERBOT_BONUS_CHANGE_VNUM);
	}

	bool PlayerBotHoldsBooster(LPCHARACTER ch)
	{
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && IsPlayerBotBoosterItem(item))
				return true;
		}
		return false;
	}

	// ------------------------------------------------------------- the look

	// MT2009 Plus (operator, 24 September 2026): a bot with Dragon Coins
	// dresses itself from the ItemShop - costume, then hairstyle, then weapon
	// skin, then pet - one piece at a time, and wears what it bought. Every bot
	// from PLAYERBOT_ISHOP_LOOK_MIN_LEVEL, not one in four once as the
	// hairstyle alone was: a piece that runs out (REAL_TIME) leaves its slot
	// empty, and the next look buys the missing piece again.

	// A weapon skin goes on only over a real weapon of its own kind: the engine
	// compares the skin's value3 with the weapon's subtype (CanEquipNow).
	bool IsPlayerBotWeaponSkinFor(LPCHARACTER ch, const TItemTable* proto)
	{
		if (!proto || proto->bType != ITEM_COSTUME || proto->bSubType != COSTUME_WEAPON ||
				!IsPlayerBotProtoForCharacter(ch, proto))
			return false;
		LPITEM weapon = ch->GetWear(WEAR_WEAPON);
		return weapon && weapon->GetType() == ITEM_WEAPON && proto->alValues[3] == (long)weapon->GetSubType();
	}

	// A piece whose level limit the bot has not reached would wait in the bag
	// for good, and a piece in the bag counts as had: never bought, never worn.
	bool IsPlayerBotLookLevelReached(LPCHARACTER ch, const TItemTable* proto)
	{
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
			if (proto->aLimits[i].bType == LIMIT_LEVEL && (long)ch->GetLevel() < proto->aLimits[i].lValue)
				return false;
		return true;
	}

	// Would this bot put the item on (or summon it) for the given piece?
	bool IsPlayerBotOwnLook(LPCHARACTER ch, const TItemTable* proto, int look)
	{
		if (!proto || !IsPlayerBotLookLevelReached(ch, proto))
			return false;
		switch (look)
		{
			case PLAYERBOT_ISHOP_LOOK_BODY:
				return proto->bType == ITEM_COSTUME && proto->bSubType == COSTUME_BODY &&
						IsPlayerBotProtoForCharacter(ch, proto);
			case PLAYERBOT_ISHOP_LOOK_HAIR:
				// MT2009_PLUS_BOT_HAIR_V1: a costume set's hairstyle only.
				return proto->bType == ITEM_COSTUME && proto->bSubType == COSTUME_HAIR &&
						IsPlayerBotProtoForCharacter(ch, proto) && IsPlayerBotSetHairVnum(proto->dwVnum);
			case PLAYERBOT_ISHOP_LOOK_WEAPON:
				return IsPlayerBotWeaponSkinFor(ch, proto);
			case PLAYERBOT_ISHOP_LOOK_PET:
				return proto->bType == ITEM_PET && proto->bSubType == PET_PAY && proto->alValues[0] != 0;
#if defined(ENABLE_MOUNT_COSTUME_SYSTEM)
			case PLAYERBOT_ISHOP_LOOK_MOUNT:
				return proto->bType == ITEM_COSTUME && proto->bSubType == COSTUME_MOUNT && proto->alValues[1] != 0;
#endif
		}
		return false;
	}

	bool IsPlayerBotPetSummoned(LPCHARACTER ch)
	{
#if defined(__PET_SYSTEM__)
		return ch->GetPetSystem() && ch->GetPetSystem()->CountSummoned() > 0;
#else
		return false;
#endif
	}

	// The piece is worn (summoned), or on its way: bought and in the bag.
	bool PlayerBotHasLook(LPCHARACTER ch, int look)
	{
		switch (look)
		{
			case PLAYERBOT_ISHOP_LOOK_BODY:
				if (ch->GetWear(WEAR_COSTUME_BODY))
					return true;
				break;
			case PLAYERBOT_ISHOP_LOOK_HAIR:
			{
				// MT2009_PLUS_BOT_HAIR_V1: a head is dressed while the ItemShop
				// sells nothing better for it (IsPlayerBotHairUpgrade) - a plain
				// hairstyle is replaced by a set one, a set one by the worn
				// costume's own set's - and a better one in the bag is on its
				// way; the hairstyle it replaced, in the bag too, is not.
				for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
					if (IsPlayerBotHairToWear(ch, ch->GetInventoryItem(cell)) &&
							IsPlayerBotOwnLook(ch, ch->GetInventoryItem(cell)->GetProto(), look))
						return true;
				if (!ch->GetWear(WEAR_COSTUME_HAIR))
					return false;
				for (size_t i = 0; i < s_vecPlayerBotItemShopHair.size(); ++i)
					if (IsPlayerBotHairUpgrade(ch, s_vecPlayerBotItemShopHair[i]) &&
							IsPlayerBotOwnLook(ch, ITEM_MANAGER::instance().GetTable(s_vecPlayerBotItemShopHair[i]), look))
						return false;
				return true;
			}
			case PLAYERBOT_ISHOP_LOOK_WEAPON:
			{
				if (ch->GetWear(WEAR_COSTUME_WEAPON))
					return true;
				// No real weapon to dress: nothing to buy for now.
				LPITEM weapon = ch->GetWear(WEAR_WEAPON);
				if (!weapon || weapon->GetType() != ITEM_WEAPON)
					return true;
				break;
			}
			case PLAYERBOT_ISHOP_LOOK_PET:
				if (IsPlayerBotPetSummoned(ch))
					return true;
				break;
			case PLAYERBOT_ISHOP_LOOK_MOUNT:
#if defined(ENABLE_MOUNT_COSTUME_SYSTEM)
				if (ch->GetWear(WEAR_COSTUME_MOUNT))
					return true;
				break;
#else
				return true;
#endif
		}
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && IsPlayerBotOwnLook(ch, item->GetProto(), look))
				return true;
		}
		return false;
	}

	const std::vector<DWORD>& GetPlayerBotLookCatalogue(int look)
	{
		switch (look)
		{
			case PLAYERBOT_ISHOP_LOOK_BODY: return s_vecPlayerBotItemShopBody;
			case PLAYERBOT_ISHOP_LOOK_HAIR: return s_vecPlayerBotItemShopHair;
			case PLAYERBOT_ISHOP_LOOK_WEAPON: return s_vecPlayerBotItemShopWeaponSkin;
			case PLAYERBOT_ISHOP_LOOK_MOUNT: return s_vecPlayerBotItemShopMount;
			default: return s_vecPlayerBotItemShopPet;
		}
	}

	const char* GetPlayerBotLookReason(int look)
	{
		switch (look)
		{
			case PLAYERBOT_ISHOP_LOOK_BODY: return "look_costume";
			case PLAYERBOT_ISHOP_LOOK_HAIR: return "hairstyle";
			case PLAYERBOT_ISHOP_LOOK_WEAPON: return "look_weapon_skin";
			case PLAYERBOT_ISHOP_LOOK_MOUNT: return "look_mount";
			default: return "look_pet";
		}
	}

	// MT2009_PLUS_BOT_ISHOP_FRESH_V1: how long a bought look lasts, in
	// seconds; 0 for a permanent one. A REAL_TIME limit of 0 is the engine's
	// seven days (ITEM_MANAGER::CreateItem).
	long GetPlayerBotLookSeconds(const TItemTable* proto)
	{
		if (!proto)
			return 0;
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
		{
			const BYTE type = proto->aLimits[i].bType;
			if (type == LIMIT_REAL_TIME)
				return proto->aLimits[i].lValue > 0 ? proto->aLimits[i].lValue : 7L * 24 * 60 * 60;
			if (type == LIMIT_REAL_TIME_START_FIRST_USE || type == LIMIT_TIMER_BASED_ON_WEAR)
				return proto->aLimits[i].lValue > 0 ? proto->aLimits[i].lValue : 1;
		}
		return 0;
	}

	// The first piece missing, in the operator's order; 0 when the bot is
	// dressed or its piece is not for sale. The strict order is the point: a
	// bot saves for the costume before it spends on a hairstyle. Which item
	// of the kind is drawn at random among those the bot can wear.
	DWORD PickPlayerBotLook(LPCHARACTER ch, int* pLook)
	{
		if (ch->GetLevel() < PLAYERBOT_ISHOP_LOOK_MIN_LEVEL)
			return 0;
		for (int look = 0; look < PLAYERBOT_ISHOP_LOOK_COUNT; ++look)
		{
			if (PlayerBotHasLook(ch, look))
				continue;
			const std::vector<DWORD>& catalogue = GetPlayerBotLookCatalogue(look);
			std::vector<DWORD> mine;
			for (size_t i = 0; i < catalogue.size(); ++i)
				if (IsPlayerBotOwnLook(ch, ITEM_MANAGER::instance().GetTable(catalogue[i]), look) &&
						(look != PLAYERBOT_ISHOP_LOOK_HAIR || IsPlayerBotHairUpgrade(ch, catalogue[i])))
					mine.push_back(catalogue[i]);
			if (mine.empty())
				continue;
			// MT2009_PLUS_BOT_HAIR_V1: the worn costume's own set's hairstyle,
			// when the ItemShop has one - the set bonus is the point of it.
			if (look == PLAYERBOT_ISHOP_LOOK_HAIR)
			{
				LPITEM body = ch->GetWear(WEAR_COSTUME_BODY);
				std::vector<DWORD> matching;
				for (size_t i = 0; body && i < mine.size(); ++i)
					if (IsPlayerBotHairOfBodySet(body->GetVnum(), mine[i]))
						matching.push_back(mine[i]);
				if (!matching.empty())
					mine.swap(matching);
			}
			// MT2009_PLUS_BOT_ISHOP_FRESH_V1: a line that lasts (30 days or
			// for good) when the shop has one for this bot - the price is the
			// same for ten minutes and for a month.
			std::vector<DWORD> lasting;
			for (size_t i = 0; i < mine.size(); ++i)
			{
				const long seconds = GetPlayerBotLookSeconds(ITEM_MANAGER::instance().GetTable(mine[i]));
				if (seconds == 0 || seconds >= PLAYERBOT_ISHOP_LOOK_MIN_SECONDS)
					lasting.push_back(mine[i]);
			}
			if (!lasting.empty())
				mine.swap(lasting);
			*pLook = look;
			// Any of them, drawn anew each time (operator: variety), so a
			// piece that runs out is followed by another.
			return mine[number(0, (int)mine.size() - 1)];
		}
		return 0;
	}

	// A head for the counter (PLAYERBOT_ISHOP_HAIR_TRADE_SHARE) was one this
	// bot could not wear, bought for its stand.
	// MT2009_PLUS_BOT_HAIR_V1: never any more - a hairstyle is no goods; the
	// only one a counter takes is the bot's own old one (IsPlayerBotReplacedHair).
	DWORD PickPlayerBotHairstyleForCounter(LPCHARACTER ch)
	{
		(void)ch;
		return 0;
	}

	// The book pass's own two answers (playerbot_manager.cpp, after this file).
	int FindPlayerBotBookAffectCell(LPCHARACTER ch, DWORD affectType);
	bool PlayerBotHasBookReadExp(LPCHARACTER ch);
	bool PlayerBotMarksCover(const TPlayerBotAIState& state, DWORD vnum);

	// A class book in the bag the bot could read but for the wait, with at
	// least PLAYERBOT_ISHOP_EXORCISM_MIN_WAIT_SECONDS of it left, and no
	// Exorcism Scroll of its own: the scroll the book pass already uses when it
	// has one. Nothing on a world whose bots do not wait (the easy difficulty).
	bool PlayerBotWantsExorcismScroll(LPCHARACTER ch)
	{
		if (IsPlayerBotFastBooksEnabled() || ch->GetSkillGroup() == 0 ||
				ch->FindAffect(AFFECT_SKILL_NO_BOOK_DELAY) ||
				FindPlayerBotBookAffectCell(ch, AFFECT_SKILL_NO_BOOK_DELAY) >= 0 ||
				!PlayerBotHasBookReadExp(ch))
			return false;
		const int now = get_global_time();
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetType() != ITEM_SKILLBOOK)
				continue;
			const DWORD skill = GetPlayerBotSkillBookSkillVnum(item);
			if (!IsPlayerBotOwnSkill(ch, skill) || ch->GetSkillMasterType(skill) != SKILL_MASTER ||
					ch->GetSkillLevel(skill) < 20 || ch->GetSkillLevel(skill) >= 30)
				continue;
			if ((int)ch->GetSkillNextReadTime(skill) - now >= PLAYERBOT_ISHOP_EXORCISM_MIN_WAIT_SECONDS)
				return true;
		}
		return false;
	}

	// Every wish the bot has, in the order it would spend on them. The buyer
	// takes the first it can afford: the first build picked one wish only,
	// and a bot with no marks whose first wish was the marks' Blessing Scroll
	// never got as far as the hairstyle its coins would have bought.
	const int PLAYERBOT_ISHOP_MAX_WISHES = 14;

	// ItemShop by needs (sosen94: on the test world 346 of 347 purchases in a
	// week were hairstyles). Besides the stone, the change stone and the
	// Exorcism Scroll: a Metin detector for a stone hunter, the Teleport Ring
	// on the frontier, and for marks the Rada Pustelnika for a book waiting
	// to be read and the boosters for a raid, the tower and a war - what the
	// bot is doing now first. A need the balance cannot pay yet is saved for
	// when the bot's vouchers would bring it within
	// PLAYERBOT_ISHOP_SAVE_DAYS, and the look is bought only from what is
	// over the needs' reserve.
	const DWORD PLAYERBOT_ISHOP_METIN_DETECTOR_VNUM = 27989;
	const DWORD PLAYERBOT_ISHOP_RADA_VNUM = 71094;
	const DWORD PLAYERBOT_ISHOP_BOOSTER_VNUMS[] = { 71028, 71044, 71027, 71045, 71030 };
	const int PLAYERBOT_ISHOP_SAVE_DAYS = 10;

	bool PlayerBotHoldsReadableClassBook(LPCHARACTER ch);
	bool IsPlayerBotFrontierMapIndex(long mapIndex);

	// The cheapest line of a wish the bot's level may buy, whatever the
	// balance; 0 when the shop has none.
	DWORD GetPlayerBotItemShopCheapest(LPCHARACTER ch, DWORD vnum, bool marks)
	{
		const TPlayerBotItemShopTable& table = marks ? s_mapPlayerBotItemShopMarks : s_mapPlayerBotItemShopCoins;
		TPlayerBotItemShopTable::const_iterator it = table.find(vnum);
		DWORD best = 0;
		if (it != table.end())
			for (size_t i = 0; i < it->second.size(); ++i)
				if (it->second[i].dwCount != 0 && ch->GetLevel() >= it->second[i].bMinLevel &&
						(best == 0 || it->second[i].dwPrice < best))
					best = it->second[i].dwPrice;
		return best;
	}

	// Whether a need the balance cannot pay yet is worth saving for: the
	// coins this bot's vouchers have brought, at their pace, would cover it
	// within PLAYERBOT_ISHOP_SAVE_DAYS.
	bool PlayerBotSavesForWish(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD price)
	{
		if (price == 0)
			return false;
		const long long have = state.iDragonCoins;
		if (have >= (long long)price)
			return true;
		std::map<DWORD, TPlayerBotCoinIncome>::const_iterator it = s_mapPlayerBotCoinIncome.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotCoinIncome.end() || it->second.llCoins <= 0)
			return false;
		const long long elapsed = std::max<long long>(86400, (long long)get_global_time() - it->second.iSince);
		return it->second.llCoins * PLAYERBOT_ISHOP_SAVE_DAYS * 86400LL / elapsed >= (long long)price - have;
	}

	bool PlayerBotHoldsAnyOf(LPCHARACTER ch, const DWORD* vnums, size_t count)
	{
		for (size_t i = 0; i < count; ++i)
			if (ch->CountSpecifyItem(vnums[i]) > 0)
				return true;
		return false;
	}

	// The coins the needs keep back from the look: each coin need the bot
	// can pay or is saving for, at its cheapest line.
	long long GetPlayerBotItemShopNeedReserve(LPCHARACTER ch, const TPlayerBotAIState& state,
			const TPlayerBotItemShopWish* wishes, int n)
	{
		long long reserve = 0;
		for (int i = 0; i < n; ++i)
		{
			if (wishes[i].bMarks)
				continue;
			const DWORD price = GetPlayerBotItemShopCheapest(ch, wishes[i].dwVnum, false);
			if (PlayerBotSavesForWish(ch, state, price))
				reserve += price;
		}
#ifdef MT2009_PLUS_BOT_ISHOP_V3_V1
		// MT2009_PLUS_BOT_ISHOP_V3_V1: a look only from the coins the open gear goals do not need (their next batch)
		if (GetPlayerBotItemShopSource() == 2)
			reserve += GetPlayerBotIshop3GoalReserve(ch, state);
#endif
		return reserve;
	}

	// A look - hairstyle, costume, skin or pet - only from the coins over the
	// needs' reserve.
	bool PlayerBotLookFromSurplus(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD vnum, long long reserve)
	{
		const DWORD price = GetPlayerBotItemShopCheapest(ch, vnum, false);
		return price != 0 && (long long)state.iDragonCoins - (long long)price >= reserve;
	}

	int CollectPlayerBotItemShopNeeds(LPCHARACTER ch, const TPlayerBotAIState& state, TPlayerBotItemShopWish* wishes)
	{
		int n = 0;
		const DWORD now = get_dword_time();
		// What the bot is doing now goes first: a raid, the tower or a war,
		// a stone hunt, the frontier, a book waiting.
		const bool fighting = IsPlayerBotOnTowerBusiness(ch, state) || state.dwGuildWarEnemyGID != 0;
		const bool hunting = IsPlayerBotMetinHunting(state, now);
		const bool frontier = IsPlayerBotFrontierMapIndex(ch->GetMapIndex());
		TPlayerBotItemShopWish now_[PLAYERBOT_ISHOP_MAX_WISHES];
		TPlayerBotItemShopWish later[PLAYERBOT_ISHOP_MAX_WISHES];
		int nNow = 0, nLater = 0;
		auto add = [&](DWORD vnum, bool marks, const char* reason, bool current)
		{
			TPlayerBotItemShopWish w;
			w.dwVnum = vnum;
			w.bMarks = marks;
			w.szReason = reason;
			if (current && nNow < PLAYERBOT_ISHOP_MAX_WISHES)
				now_[nNow++] = w;
			else if (!current && nLater < PLAYERBOT_ISHOP_MAX_WISHES)
				later[nLater++] = w;
		};
		if (fighting && !PlayerBotHoldsBooster(ch))
			for (size_t i = 0; i < sizeof(PLAYERBOT_ISHOP_BOOSTER_VNUMS) / sizeof(PLAYERBOT_ISHOP_BOOSTER_VNUMS[0]); ++i)
				if (PlayerBotMarksCover(state, PLAYERBOT_ISHOP_BOOSTER_VNUMS[i]))
				{
					add(PLAYERBOT_ISHOP_BOOSTER_VNUMS[i], true, "raid_booster", true);
					break;
				}
		if (hunting && !PlayerBotHoldsAnyOf(ch, PLAYERBOT_METIN_DETECTOR_VNUMS,
				sizeof(PLAYERBOT_METIN_DETECTOR_VNUMS) / sizeof(PLAYERBOT_METIN_DETECTOR_VNUMS[0])))
			add(PLAYERBOT_ISHOP_METIN_DETECTOR_VNUM, false, "metin_detector", true);
		if (frontier && ch->GetLevel() >= PLAYERBOT_TELEPORT_RING_MIN_LEVEL &&
				ch->CountSpecifyItem(PLAYERBOT_TELEPORT_RING_VNUM) == 0)
			add(PLAYERBOT_TELEPORT_RING_VNUM, false, "teleport_ring", true);
		const bool bookWaits = PlayerBotHoldsReadableClassBook(ch);
		if (s_mapPlayerBotItemShopCoins.find(PLAYERBOT_ISHOP_EXORCISM_VNUM) != s_mapPlayerBotItemShopCoins.end() &&
				PlayerBotWantsExorcismScroll(ch))
			add(PLAYERBOT_ISHOP_EXORCISM_VNUM, false, "exorcism_scroll", true);
		if (bookWaits && !ch->FindAffect(AFFECT_SKILL_BOOK_BONUS) &&
				FindPlayerBotBookAffectCell(ch, AFFECT_SKILL_BOOK_BONUS) < 0 &&
				PlayerBotMarksCover(state, PLAYERBOT_ISHOP_RADA_VNUM))
			add(PLAYERBOT_ISHOP_RADA_VNUM, true, "rada_pustelnika", true);
		if (PlayerBotWantsGrandMasterStone(ch))
			add(PLAYERBOT_GRAND_MASTER_STONE_VNUM, false, "grand_master_stone", false);
		if (PlayerBotWantsChangeStone(ch))
			add(PLAYERBOT_BONUS_CHANGE_VNUM, false, "change_stone", false);
		if (PlayerBotWearsScrollWork(ch) && CountPlayerBotSafeRefineScrolls(ch) == 0 &&
				PlayerBotMarksCover(state, PLAYERBOT_ISHOP_BLESSING_SCROLL_VNUM))
			add(PLAYERBOT_ISHOP_BLESSING_SCROLL_VNUM, true, "blessing_scroll", false);
		for (int i = 0; i < nNow && n < PLAYERBOT_ISHOP_MAX_WISHES; ++i)
			wishes[n++] = now_[i];
		for (int i = 0; i < nLater && n < PLAYERBOT_ISHOP_MAX_WISHES; ++i)
			wishes[n++] = later[i];
		return n;
	}

	int CollectPlayerBotItemShopWishes(LPCHARACTER ch, const TPlayerBotAIState& state, TPlayerBotItemShopWish* wishes)
	{
		int n = CollectPlayerBotItemShopNeeds(ch, state, wishes);
		// MT2009_PLUS_SIDEKICK_COINS_V1: a companion spends on what it uses
		// alone - no hairstyle, costume, skin or pet, and nothing for a counter.
		if (IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return n;
		const long long reserve = GetPlayerBotItemShopNeedReserve(ch, state, wishes, n);
		int look = 0;
		const DWORD lookVnum = PickPlayerBotLook(ch, &look);
		if (lookVnum != 0 && n < PLAYERBOT_ISHOP_MAX_WISHES && PlayerBotLookFromSurplus(ch, state, lookVnum, reserve))
		{
			wishes[n].dwVnum = lookVnum;
			wishes[n].bMarks = false;
			wishes[n++].szReason = GetPlayerBotLookReason(look);
		}
#ifdef MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
		// MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1: a costume / hairstyle for the element set's empty slot
		// (playerbot_element_second_set.h), its own look first.
		if (lookVnum == 0 && n < PLAYERBOT_ISHOP_MAX_WISHES)
		{
			int ssLook = 0;
			const DWORD ssVnum = PickPlayerBotSecondSetLook(ch, &ssLook);
			if (ssVnum != 0 && PlayerBotLookFromSurplus(ch, state, ssVnum, reserve))
			{
				wishes[n].dwVnum = ssVnum;
				wishes[n].bMarks = false;
				wishes[n++].szReason = ssLook == PLAYERBOT_ISHOP_LOOK_HAIR ? "secondset_hair" : "secondset_costume";
			}
		}
#endif
		// Its own come first; a head for the counter only when nothing else
		// is wanted, or the coins saved for a Kamien Duchowy would go on it.
		if (n == 0)
		{
			const DWORD stock = PickPlayerBotHairstyleForCounter(ch);
			if (stock != 0)
			{
				wishes[n].dwVnum = stock;
				wishes[n].bMarks = false;
				wishes[n++].szReason = "counter_hairstyle";
			}
		}
		return n;
	}

	// The line a wish is bought from: of the lines the balance and the level
	// allow, the cheapest unit. NULL when none of them is affordable.
	const TPlayerBotItemShopEntry* FindPlayerBotItemShopEntry(LPCHARACTER ch, const TPlayerBotAIState& state,
			const TPlayerBotItemShopWish& wish)
	{
		const TPlayerBotItemShopTable& table = wish.bMarks ? s_mapPlayerBotItemShopMarks : s_mapPlayerBotItemShopCoins;
		TPlayerBotItemShopTable::const_iterator it = table.find(wish.dwVnum);
		if (it == table.end())
			return NULL;
		const int have = wish.bMarks ? state.iDragonMarks : state.iDragonCoins;
		const TPlayerBotItemShopEntry* best = NULL;
		for (size_t i = 0; i < it->second.size(); ++i)
		{
			const TPlayerBotItemShopEntry& line = it->second[i];
			if (line.dwCount == 0 || ch->GetLevel() < line.bMinLevel || have < (int)line.dwPrice)
				continue;
			if (!best || (unsigned long long)line.dwPrice * best->dwCount <
					(unsigned long long)best->dwPrice * line.dwCount)
				best = &line;
		}
		return best;
	}

	bool CanPlayerBotAffordWish(LPCHARACTER ch, const TPlayerBotAIState& state, const TPlayerBotItemShopWish& wish)
	{
		return FindPlayerBotItemShopEntry(ch, state, wish) != NULL;
	}

	// A marks wish only while the balance covers its cheapest line. Marks come
	// only from coins spent, one for one, so every mark in the world came from
	// a hairstyle - the largest balance on m2zip was 117 against the Blessing
	// Scroll's 719 and the potions' 249 - and the two marks wishes stood for
	// nearly every bot of thirty: an hourly account read for nothing (36 282
	// "saving" looks in eight hours) and the counter's hairstyle, which waits
	// for a bot with no other wish, blocked for good. The balance is kept in
	// the state and a bot's own purchases move it, so this asks no query.
	bool PlayerBotMarksCover(const TPlayerBotAIState& state, DWORD vnum)
	{
		if (!state.bDragonBalanceKnown)
			return false;
		TPlayerBotItemShopTable::const_iterator it = s_mapPlayerBotItemShopMarks.find(vnum);
		if (it == s_mapPlayerBotItemShopMarks.end())
			return false;
		for (size_t i = 0; i < it->second.size(); ++i)
			if (state.iDragonMarks >= (int)it->second[i].dwPrice)
				return true;
		return false;
	}

	// ------------------------------------------------------------- purchase

	// A bought piece goes on when the engine lets it: EquipItem refuses within
	// a second and a half of a blow or a cast, and the bot bought it mid-hunt,
	// so the pass asks again on every look while a slot is empty and its piece
	// waits in the bag. A pet seal is used once no pet is out: using it again
	// would send the pet away (CHARACTER::SummonPetFromItem is a toggle).
	void WearPlayerBotBoughtLook(LPCHARACTER ch, TPlayerBotAIState& state)
	{
		static const BYTE s_abWear[PLAYERBOT_ISHOP_LOOK_PET] = { WEAR_COSTUME_BODY, WEAR_COSTUME_HAIR, WEAR_COSTUME_WEAPON };
		for (int look = 0; look < PLAYERBOT_ISHOP_LOOK_COUNT; ++look)
		{
			// MT2009_PLUS_BOT_HAIR_V1: a better hairstyle goes on over the worn
			// one (EquipItem swaps them); the old one, in the bag, is the one
			// hairstyle a counter takes (IsPlayerBotReplacedHair).
			if (look == PLAYERBOT_ISHOP_LOOK_HAIR && ch->GetWear(WEAR_COSTUME_HAIR))
			{
				for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
				{
					LPITEM item = ch->GetInventoryItem(cell);
					if (!item || item->isLocked() || item->IsExchanging() || !IsPlayerBotHairToWear(ch, item) ||
							!IsPlayerBotOwnLook(ch, item->GetProto(), look) ||
							IsPlayerBotSidekickUnwanted(ch, item))	// MT2009_PLUS_SIDEKICK_MOUNT_FIX_V1
						continue;
#ifdef MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
					// MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1: an element set's hairstyle goes on with its set only, and the
					// set's worn one stays
					if (IsPlayerBotSecondSetStored(ch, item) || IsPlayerBotSecondSetWornLocked(ch, ch->GetWear(WEAR_COSTUME_HAIR)))
						continue;
#endif
					const DWORD oldVnum = ch->GetWear(WEAR_COSTUME_HAIR)->GetVnum();
					if (ch->EquipItem(item))
						sys_log(0, "PLAYERBOT_ISHOP: hairstyle changed pid=%u name=%s vnum=%u old=%u",
								ch->GetPlayerID(), ch->GetName(), item->GetVnum(), oldVnum);
					break;
				}
				continue;
			}
			if (look == PLAYERBOT_ISHOP_LOOK_PET ? IsPlayerBotPetSummoned(ch) :
					look == PLAYERBOT_ISHOP_LOOK_MOUNT ?
#if defined(ENABLE_MOUNT_COSTUME_SYSTEM)
						ch->GetWear(WEAR_COSTUME_MOUNT) != NULL
#else
						true
#endif
					: ch->GetWear(s_abWear[look]) != NULL)
				continue;
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				// MT2009_PLUS_SIDEKICK_MOUNT_FIX_V1: not a piece a companion's
				// owner took off it (its costumes window) - a seal, a costume.
				if (!item || item->isLocked() || item->IsExchanging() || !item->CanUsedBy(ch) ||
						!IsPlayerBotOwnLook(ch, item->GetProto(), look) || IsPlayerBotSidekickUnwanted(ch, item))
					continue;
#ifdef MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
				if (IsPlayerBotSecondSetStored(ch, item))	// MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1
					continue;
#endif
				if (look == PLAYERBOT_ISHOP_LOOK_HAIR)
					state.bBoughtHairstyle = true;
				if (look == PLAYERBOT_ISHOP_LOOK_PET)
				{
#if defined(__PET_SYSTEM__) && defined(USE_PET_SEAL_ON_LOGIN)
					if (ch->GetPetSystem() && ch->SummonPetFromItem(item) && IsPlayerBotPetSummoned(ch))
						sys_log(0, "PLAYERBOT_ISHOP: pet out pid=%u name=%s vnum=%u",
								ch->GetPlayerID(), ch->GetName(), item->GetVnum());
#endif
				}
				else if (ch->EquipItem(item))
					sys_log(0, "PLAYERBOT_ISHOP: %s on pid=%u name=%s vnum=%u", GetPlayerBotLookReason(look),
							ch->GetPlayerID(), ch->GetName(), item->GetVnum());
				break;
			}
		}
	}

	// The engine's own purchase, as a client makes it: the browse flag the
	// window sets, BuyItem (level, price, the account's balance read back, the
	// charge through the db core, AutoGiveItem, the purchase log), the flag off
	// on the same tick so IsBusy does not hold the rest of the tick.
	bool BuyPlayerBotItemShop(LPCHARACTER ch, TPlayerBotAIState& state, const TPlayerBotItemShopWish& wish, DWORD dwNow)
	{
		const TPlayerBotItemShopEntry* pEntry = FindPlayerBotItemShopEntry(ch, state, wish);
		if (!pEntry)
			return false;
		const TPlayerBotItemShopEntry& entry = *pEntry;
		if (!ch->HasPlayerData() || ch->IsBusy() || !ch->CanHandleItem() || !ch->HasSlotForItem(wish.dwVnum))
		{
			PlayerBotLogThrottled("ishop_not_now", dwNow,
					"PLAYERBOT_ISHOP: cannot buy now pid=%u name=%s vnum=%u reason=%s busy=%d handle=%d slot=%d",
					ch->GetPlayerID(), ch->GetName(), wish.dwVnum, wish.szReason, (int)ch->IsBusy(),
					(int)ch->CanHandleItem(), (int)ch->HasSlotForItem(wish.dwVnum));
			return false;
		}

#ifdef MT2009_PLUS_BOT_ISHOP_V3_V1
		// MT2009_PLUS_BOT_ISHOP_V3_V1: the ItemShop V3's line (the catalogue is V3's then), bought by the bots' own path;
		// nothing at all with the source off. The engine's BuyItem below only for the old in-game catalogue.
		const int source = GetPlayerBotItemShopSource();
		if (source == 0)
			return false;
		if (source == 2)
		{
			const int coinsBeforeV3 = state.iDragonCoins;
			const bool boughtV3 = BuyPlayerBotIshop3Line(ch, state, entry, wish.dwVnum, wish.bMarks, 1, wish.szReason, dwNow);
			state.dwNextItemShopBuyTime = dwNow + PLAYERBOT_ISHOP_BUY_INTERVAL;
			if (!boughtV3)
			{
				++s_uPlayerBotItemShopRefusals;
				return false;
			}
			if (!wish.bMarks && state.iDragonCoins >= PLAYERBOT_ISHOP_FRESH_BALANCE)
			{
				const DWORD next = dwNow + PLAYERBOT_ISHOP_FRESH_BUY_INTERVAL +
						PlayerBotNavHash(ch->GetPlayerID() ^ 0x46524553U) % 60000U;
				state.dwNextItemShopBuyTime = next;
				if (state.dwNextItemShopCheckTime > next)
					state.dwNextItemShopCheckTime = next;
			}
			(void)coinsBeforeV3;
			WearPlayerBotBoughtLook(ch, state);
			if (IsPlayerBotSidekickPID(ch->GetPlayerID()))
				NotePlayerBotSidekickItemShopBuy(ch, wish.dwVnum, entry.dwCount, entry.dwPrice, wish.bMarks, wish.szReason,
						wish.bMarks ? state.iDragonMarks : state.iDragonCoins);
			return true;
		}
#endif
		ch->playerData->SetItemShopBrowse(true);
		const bool bought = CItemShopManager::instance().BuyItem(ch, (int)entry.dwIndex, 1);
		ch->playerData->SetItemShopBrowse(false);
		state.dwNextItemShopBuyTime = dwNow + PLAYERBOT_ISHOP_BUY_INTERVAL;
		const int coinsBefore = state.iDragonCoins;
		if (!bought)
		{
			++s_uPlayerBotItemShopRefusals;
			// The balance the engine read may not be the one kept here.
			state.bDragonBalanceKnown = false;
			PlayerBotLogThrottled("ishop_refused", dwNow,
					"PLAYERBOT_ISHOP: purchase refused pid=%u name=%s vnum=%u index=%u price=%u %s reason=%s",
					ch->GetPlayerID(), ch->GetName(), wish.dwVnum, entry.dwIndex, entry.dwPrice,
					wish.bMarks ? "marks" : "coins", wish.szReason);
			return false;
		}
		if (wish.bMarks)
			state.iDragonMarks -= (int)entry.dwPrice;
		else
		{
			state.iDragonCoins -= (int)entry.dwPrice;
			state.iDragonMarks += (int)entry.dwPrice;
		}
		++s_uPlayerBotItemShopBuys;
		++s_mapPlayerBotItemShopBought[wish.dwVnum];
		// MT2009_PLUS_BOT_ISHOP_FRESH_V1: one line a purchase for the monitor -
		// the level, the balance before and after, how long the piece lasts
		// (days, 0 = for good) and whether the fresh-balance pace applies.
		const long lookSeconds = GetPlayerBotLookSeconds(ITEM_MANAGER::instance().GetTable(wish.dwVnum));
		const bool fresh = !wish.bMarks && state.iDragonCoins >= PLAYERBOT_ISHOP_FRESH_BALANCE;
		sys_log(0, "PLAYERBOT_ISHOP: bought pid=%u name=%s lv=%d vnum=%u x%u index=%u price=%u %s reason=%s days=%ld coins_before=%d coins_left=%d marks_left=%d fresh=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), wish.dwVnum, entry.dwCount, entry.dwIndex, entry.dwPrice,
				wish.bMarks ? "marks" : "coins", wish.szReason, lookSeconds > 0 ? std::max(1L, lookSeconds / 86400) : 0L,
				coinsBefore, state.iDragonCoins, state.iDragonMarks, (int)fresh);
		// A fresh balance (the 800 Yohara bots' 2000 coins): the next need in a
		// few minutes, not an hour; the look session below may make it sooner.
		if (fresh)
		{
			const DWORD next = dwNow + PLAYERBOT_ISHOP_FRESH_BUY_INTERVAL +
					PlayerBotNavHash(ch->GetPlayerID() ^ 0x46524553U) % 60000U;
			state.dwNextItemShopBuyTime = next;
			if (state.dwNextItemShopCheckTime > next)
				state.dwNextItemShopCheckTime = next;
		}
		WearPlayerBotBoughtLook(ch, state);
		if (IsPlayerBotSidekickPID(ch->GetPlayerID()))
			NotePlayerBotSidekickItemShopBuy(ch, wish.dwVnum, entry.dwCount, entry.dwPrice, wish.bMarks, wish.szReason,
					wish.bMarks ? state.iDragonMarks : state.iDragonCoins);
		return true;
	}

	// ----------------------------------------------------------------- tick

	bool IsPlayerBotLookReason(const char* szReason)
	{
		for (int look = 0; look < PLAYERBOT_ISHOP_LOOK_COUNT; ++look)
			if (szReason && strcmp(szReason, GetPlayerBotLookReason(look)) == 0)
				return true;
		return false;
	}

	// After a purchase: another piece missing and the coins for it, and the
	// bot comes back in a few seconds instead of an hour.
	void ContinuePlayerBotLookSession(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		int look = 0;
		TPlayerBotItemShopWish next;
		next.dwVnum = PickPlayerBotLook(ch, &look);
		next.bMarks = false;
		next.szReason = GetPlayerBotLookReason(look);
		if (next.dwVnum == 0 || !CanPlayerBotAffordWish(ch, state, next))
			return;
		TPlayerBotItemShopWish needs[PLAYERBOT_ISHOP_MAX_WISHES];
		const int n = CollectPlayerBotItemShopNeeds(ch, state, needs);
		if (!PlayerBotLookFromSurplus(ch, state, next.dwVnum, GetPlayerBotItemShopNeedReserve(ch, state, needs, n)))
			return;
		state.bItemShopLookSession = true;
		state.dwNextItemShopBuyTime = dwNow + PLAYERBOT_ISHOP_SESSION_STEP;
		state.dwNextItemShopCheckTime = dwNow + PLAYERBOT_ISHOP_SESSION_STEP;
	}

	// Upkeep, never the tick's owner: a voucher cashed, a purchase made, and
	// the rest of the tick goes on. Every ten minutes a bot; the account is
	// asked for its balance only when the bot wants something.
	void ManagePlayerBotItemShop(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || ch->IsDead() || !ch->GetDesc())
			return;
#if defined(ENABLE_MOUNT_COSTUME_SYSTEM)
		// Death takes the seal off into the bag (server-patches/mountdeath); it
		// goes back on within seconds instead of at the next look, ten
		// minutes on.
		if (!ch->GetWear(WEAR_COSTUME_MOUNT) && dwNow >= state.dwNextMountRewearTime &&
				!ch->IsBusy() && !ch->GetMyShop() && !ch->GetExchange())
		{
			state.dwNextMountRewearTime = dwNow + 5000;
			WearPlayerBotBoughtLook(ch, state);
		}
#endif
		// MT2009_PLUS_BOT_ISHOP_FRESH_V1: the first look after login, spread
		// by pid over a few minutes (hundreds of bots log in together).
		if (state.dwNextItemShopCheckTime == 0)
		{
			state.dwNextItemShopCheckTime = dwNow + PLAYERBOT_ISHOP_FIRST_LOOK_DELAY +
					PlayerBotNavHash(ch->GetPlayerID() ^ 0x46495253U) % PLAYERBOT_ISHOP_FIRST_LOOK_SPREAD;
			return;
		}
#ifdef MT2009_PLUS_BOT_ISHOP_V3_V1
		// MT2009_PLUS_BOT_ISHOP_V3_V1: the gear goals on their own clock (playerbot_ishop3_goals.h) - a few minutes
		// apart while one is open, whatever the look's hour says.
		ManagePlayerBotIshop3Goals(ch, state, dwNow);
#endif
		if (dwNow < state.dwNextItemShopCheckTime)
			return;
		state.dwNextItemShopCheckTime = dwNow + PLAYERBOT_ISHOP_CHECK_INTERVAL +
				PlayerBotNavHash(ch->GetPlayerID() ^ 0x49534850U) % 60000U;
		if (IsPlayerBotSidekickPID(ch->GetPlayerID()) ? !IsPlayerBotSidekickCoinsOn(ch->GetPlayerID()) :
				!IsPlayerBotItemShopEnabled())
			return;
		if (ch->IsBusy() || ch->GetMyShop() || ch->GetExchange())
			return;
		RefreshPlayerBotItemShopCatalogue(dwNow);
		WearPlayerBotBoughtLook(ch, state);

		const bool voucher = FindPlayerBotVoucher(ch) != NULL;
		// MT2009_PLUS_BOT_ISHOP_FRESH_V1: coins put on the account directly (the
		// 800 Yohara bots' 2000, the panel) and no voucher or need to make the
		// bot read it: the look is wanted only from a known balance, so a piece
		// missing reads the account - once after login, then hourly while one
		// is still missing.
		if (!IsPlayerBotSidekickPID(ch->GetPlayerID()) &&
				(!state.bDragonBalanceKnown || dwNow >= state.dwNextItemShopBalanceTime))
		{
			int missing = 0;
			if (PickPlayerBotLook(ch, &missing) != 0)
				RefreshPlayerBotDragonBalance(ch, state, dwNow);
		}
		TPlayerBotItemShopWish wishes[PLAYERBOT_ISHOP_MAX_WISHES];
		const int wants = CollectPlayerBotItemShopWishes(ch, state, wishes);
		if (!voucher && wants == 0)
			return;
		// The account is read before a voucher is cashed, never after: the
		// charge is a round trip through the db core, and a read on its heels
		// would put the old balance back over the coins just added.
		if (!state.bDragonBalanceKnown || dwNow >= state.dwNextItemShopBalanceTime)
			RefreshPlayerBotDragonBalance(ch, state, dwNow);
		// And a purchase waits for the next look for the same reason: BuyItem
		// reads the account itself.
		if (voucher && UsePlayerBotVoucher(ch, state, dwNow))
			return;
		if (dwNow < state.dwNextItemShopBuyTime)
			return;
#ifdef MT2009_PLUS_BOT_ISHOP_V3_V1
		if (GetPlayerBotItemShopSource() == 0)
			return;
#endif
		// Within a session only the look is bought: a stone the bot still
		// wants after buying one would be bought again every few seconds.
		const bool session = state.bItemShopLookSession;
		state.bItemShopLookSession = false;
		for (int i = 0; i < wants; ++i)
		{
			if (session && !IsPlayerBotLookReason(wishes[i].szReason))
				continue;
			if (!CanPlayerBotAffordWish(ch, state, wishes[i]))
				continue;
			if (BuyPlayerBotItemShop(ch, state, wishes[i], dwNow))
				ContinuePlayerBotLookSession(ch, state, dwNow);
			return;
		}
		if (!session)
			++s_uPlayerBotItemShopSaving;
	}

	void WritePlayerBotItemShopCensus(DWORD dwNow)
	{
#ifdef MT2009_PLUS_BOT_ISHOP_V3_V1
		WritePlayerBotIshop3Census(dwNow);
#endif
		if (s_dwNextPlayerBotItemShopCensus != 0 && dwNow < s_dwNextPlayerBotItemShopCensus)
			return;
		s_dwNextPlayerBotItemShopCensus = dwNow + PLAYERBOT_ISHOP_CENSUS_INTERVAL;
		if (s_uPlayerBotVouchersUsed == 0 && s_uPlayerBotItemShopBuys == 0 && s_uPlayerBotItemShopRefusals == 0 &&
				s_uPlayerBotItemShopSaving == 0)
			return;
		std::string bought;
		char buf[48];
		for (std::map<DWORD, unsigned int>::const_iterator it = s_mapPlayerBotItemShopBought.begin();
				it != s_mapPlayerBotItemShopBought.end(); ++it)
		{
			snprintf(buf, sizeof(buf), "%s%u:%u", bought.empty() ? "" : ",", it->first, it->second);
			bought += buf;
		}
		sys_log(0, "PLAYERBOT_ISHOP: census vouchers=%u coins=%u purchases=%u refused=%u saving_looks=%u bought=%s",
				s_uPlayerBotVouchersUsed, s_uPlayerBotCoinsCharged, s_uPlayerBotItemShopBuys,
				s_uPlayerBotItemShopRefusals, s_uPlayerBotItemShopSaving, bought.empty() ? "-" : bought.c_str());
	}

	// MT2009_PLUS_MARKET_LIFE_V1, point 6 (the owner's list, 9 October): "Kupony
	// SM: boty wystawiaja je na sklepy, kiedy nie potrzebuja ich w ItemShopie".
	// PLAYERBOT_VOUCHER_SELLER_PERCENT of the bots with a counter (by pid) cash
	// a voucher only while the coins of their needs (CollectPlayerBotItemShopNeeds:
	// what they would use - the look waits for a surplus anyway) are more than
	// the balance; otherwise the voucher is the counter's for the next
	// PLAYERBOT_VOUCHER_COUNTER_HOLD_MS (IsPlayerBotVoucherForCounter), priced
	// off the sheet like any good (80014-80018, playerbot_price_tables.h). With
	// the ItemShop off for the bots (ISHOP) the vouchers stay in the bags, and
	// every bot with a counter puts them up.
	const int PLAYERBOT_VOUCHER_SELLER_PERCENT = 50;
	const DWORD PLAYERBOT_VOUCHER_COUNTER_HOLD_MS = 30 * 60 * 1000;
	std::map<DWORD, DWORD> s_mapPlayerBotVoucherCounterUntil;
	unsigned int s_uPlayerBotVoucherKeeps = 0;

	bool IsPlayerBotVoucherSeller(LPCHARACTER ch)
	{
		return ch && (int)(PlayerBotNavHash(ch->GetPlayerID() ^ 0x4b55504fU) % 100U) < PLAYERBOT_VOUCHER_SELLER_PERCENT;
	}

	bool PlayerBotKeepsVouchersForCounter(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !PlayerBotHasCounter(ch) || !IsPlayerBotVoucherSeller(ch))
			return false;
		TPlayerBotItemShopWish wishes[PLAYERBOT_ISHOP_MAX_WISHES];
		const int n = CollectPlayerBotItemShopNeeds(ch, state, wishes);
		long long need = 0;
		for (int i = 0; i < n; ++i)
			if (!wishes[i].bMarks)
				need += GetPlayerBotItemShopCheapest(ch, wishes[i].dwVnum, false);
		if (need > (long long)state.iDragonCoins)
			return false;
		std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotVoucherCounterUntil.find(ch->GetPlayerID());
		const bool fresh = it == s_mapPlayerBotVoucherCounterUntil.end() || (int)(dwNow - it->second) >= 0;
		s_mapPlayerBotVoucherCounterUntil[ch->GetPlayerID()] = dwNow + PLAYERBOT_VOUCHER_COUNTER_HOLD_MS;
		if (fresh)
		{
			++s_uPlayerBotVoucherKeeps;
			sys_log(0, "PLAYERBOT_ISHOP: vouchers kept for the counter pid=%u name=%s balance=%d need=%lld",
					ch->GetPlayerID(), ch->GetName(), state.iDragonCoins, need);
		}
		return true;
	}

	bool IsPlayerBotVoucherForCounter(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || IsPlayerBotSidekickPID(ch->GetPlayerID()) || !PlayerBotHasCounter(ch))
			return false;
		if (!IsPlayerBotItemShopEnabled())
			return true;
		std::map<DWORD, DWORD>::const_iterator it = s_mapPlayerBotVoucherCounterUntil.find(ch->GetPlayerID());
		return it != s_mapPlayerBotVoucherCounterUntil.end() && (int)(it->second - get_dword_time()) > 0;
	}
#else
	bool IsPlayerBotVoucherForCounter(LPCHARACTER, LPITEM)
	{
		return false;
	}

	void CashPlayerBotVouchers(LPCHARACTER, TPlayerBotAIState&, DWORD)
	{
	}

	void ManagePlayerBotItemShop(LPCHARACTER, TPlayerBotAIState&, DWORD)
	{
	}

	void WritePlayerBotItemShopCensus(DWORD)
	{
	}
#endif
}

#endif
