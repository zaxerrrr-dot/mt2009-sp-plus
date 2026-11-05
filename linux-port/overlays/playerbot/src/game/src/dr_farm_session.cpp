// MT2009_PLUS_FARM_SESSION_V1 - Sesja farmienia (server-patches/sesja/README.md): port of Digi Rasta's
// p-sesja-farmienia (DR_FARM_SESSION_V1: "Sesja farmienia", the Y window) - the server's part, see
// dr_farm_session.h. Ours beyond the package (MT2009_PLUS_FARM_SESSION_V1): a registered bot never counts
// (DrFarmIsHuman), FarmInfo ends with the time of the last yang (the Yang row's tooltip; column yang_last),
// FarmSpark (the items of the last DR_FARM_SPARK_MINUTES active minutes, the window's line chart) and
// FarmStatAll (every item's total with its category, the window's own categories) - described below. A session belongs to a human player
// (never a bot) and lives in two places: the map s_mapSessions of this core
// (the characters playing here, by player id) and the row in
// player.dr_farm_session (AccountDB; plus dr_farm_item / dr_farm_mob /
// dr_farm_map: the kills of a monster's kind and the news of a map, kept in
// the session too and written with it, the dirty rows only).
//
// Time: a running session counts the seconds the character is in the game on
// this core (a tick of one second, started when the first session runs and
// stopped when none does). Logout, a change of channel or of core takes the
// session out of the map (DrFarmOnDisconnect): the time stops, the row is
// written with DirectQuery. The row keeps the state the player had set
// (status 0 running = "goes on at the next login", 1 paused = stays paused), so
// the next entry (DrFarmOnEnterGame) reads the newest row with status 0 or 1
// and goes on from the counters in the row. Every counter is written absolute
// with GREATEST(), so a late or doubled write never takes a counter back.
// Every minute a running session with news is written with AsyncQuery: a
// crash costs at most that minute.
//
// To the client (numbers only, one line under 480 bytes; the names are the
// client's):
//   FarmInfo 1 <state 0 none|1 running|2 paused> <id> <start_unix> <active_sec> <limit_sec> <now_unix>
//            <exp> <yang m s b> <items m s b> <kills m s b> <yang_last_unix>    (m monsters, s Metin stones, b bosses;
//            yang_last_unix: MT2009_PLUS_FARM_SESSION_V1, 0 = none yet)
//   FarmResult <0 ok|1 already|2 no session|3 wrong state|4 wrong limit|5 database error|6 ended at the limit>
// A command is answered with FarmInfo and then FarmResult; "stan" with FarmInfo only.
// A session that ends at its limit while the player is here (the tick, the entry)
// is told with FarmInfo (no session) and FarmResult 6; a logout sends nothing.
//   FarmItems <src 0 monsters|1 Metin stones|2 bosses> <n> <vnum>:<cnt>:<last_unix> ...  (n <= 14) and FarmDone
//            "pelne" sends every item row of the session, "stan" (every 5 s) the rows that changed
//            since the last FarmItems (nothing changed: FarmInfo only); FarmDone ends a snapshot
//   FarmSpark <minute> <n> <c1> ... <cn>   (MT2009_PLUS_FARM_SESSION_V1: just before every FarmDone of a session)
//            the items counted in the active minutes minute-n+1 .. minute (minute = active_sec / 60), n =
//            DR_FARM_SPARK_MINUTES; memory only (a relog or a change of core starts it empty)
//   "historia": FarmInfo, FarmHist <id> <start_unix> <active_sec> <yang> <items> <kills> <exp> <reason>
//            (the 50 newest ended sessions, one a line), FarmHistEnd
//   "stat": FarmInfo, FarmStatSum <sessions> <active_sec> <exp> <yang m s b> <items m s b> <kills m s b>
//            (the open session counts), FarmStatPer <today_sessions> <today_yang> <7d_sessions> <7d_yang>,
//            FarmStatRec <best_yang> <at> <best_yang_h> <at> <longest_sec> <at> <most_kills> <at>,
//            FarmStatCat <c0> ... <c5>, FarmStatTop <n> <vnum>:<cnt> ... (10), FarmStatMob <n> <vnum>:<kills> ... (10),
//            FarmStatMap <n> <map>:<yang>:<items>:<kills> ... (n <= 6 a line),
//            FarmStatAll <n> <vnum>:<cat>:<cnt> ... (MT2009_PLUS_FARM_SESSION_V1: n <= 12 a line, the
//            DR_FARM_ALL_MAX most counted items; the window moves them into the player's own categories), FarmStatEnd
//   "historia" and "stat" first write the player's open session (so the SQL totals include it); a
//   database error is FarmInfo and FarmResult 5, nothing else. The statistics cover the sessions the
//   table still holds (the 100 newest ended ones and the open one, see TrimDrFarmHistory).
//
// The row of a logged-out player keeps status 0 (it goes on at the next login), so the history and
// the statistics tell only an ended session (status 2) from an open one (0, 1), never "online".
//
// The drop and the yang count when they reach a bag (see dr_farm_session.h):
// a kill's items on the ground carry a tag in s_mapDrFarmTags (by VID) until
// their pick-up or 330 s; what a kill hands over at once counts inside a
// DrFarmKillScope (a stack of contexts, s_aDrFarmScopes).

#include "stdafx.h"

#ifdef DR_FARM_SESSION_V1

#include <algorithm>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <map>
#include <string>
#include <strings.h>
#include <unordered_map>
#include <utility>
#include <vector>

#include "constants.h"
#include "config.h"
#include "utils.h"
#include "packet.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "db.h"
#include "party.h"
#include "item.h"
#include "item_manager.h"
#include "playerbot_manager.h"	// MT2009_PLUS_FARM_SESSION_V1: IsRegisteredBotPID (DrFarmIsHuman)
#include "dr_farm_session.h"

int g_iDrFarmActive = 0;

namespace
{
	const int DR_FARM_PROTOCOL = 1;
	// How often a running session with news is written (AsyncQuery), and how
	// soon a refused ending or a refused creation of the tables is tried again.
	const DWORD DR_FARM_FLUSH_MS = 60000;
	const DWORD DR_FARM_END_RETRY_MS = 10000;
	const DWORD DR_FARM_TABLES_RETRY_MS = 5000;
	// The finished sessions kept for a player.
	const int DR_FARM_HISTORY_MAX = 100;
	// The longest command line sent to the client (CHAT_MAX_LEN is 512).
	const int DR_FARM_LINE_MAX = 480;
	// How many entries a line carries, and the characters of an entry in the worst
	// case (a DWORD or an int: 10 digits; a long long: 19 digits and a sign; one
	// space before it). The static_asserts below prove that a full line fits.
	const int DR_FARM_ITEMS_PER_LINE = 14;	// " <vnum>:<cnt>:<last_unix>": 1+10+1+10+1+10; header "FarmItems 2 14"
	const int DR_FARM_MAPS_PER_LINE = 6;	// " <map>:<yang>:<items>:<kills>": 1+11+1+20+1+20+1+20; header "FarmStatMap 6"
	const int DR_FARM_TOP_LINE = 10;		// " <vnum>:<cnt>": 1+10+1+20; header "FarmStatTop 10"
	const int DR_FARM_HIST_SEND = 50;		// the ended sessions "historia" sends
	// MT2009_PLUS_FARM_SESSION_V1: FarmSpark's minutes (" <cnt>": 1+10; header "FarmSpark <minute> 40": 10+10+3)
	// and FarmStatAll (" <vnum>:<cat>:<cnt>": 1+10+1+3+1+20; header "FarmStatAll 12"), the items it sends at most.
	const int DR_FARM_SPARK_MINUTES = 40;
	const int DR_FARM_ALL_PER_LINE = 12;
	const int DR_FARM_ALL_MAX = 300;
	static_assert(23 + DR_FARM_SPARK_MINUTES * (1 + 10) <= DR_FARM_LINE_MAX, "FarmSpark line");
	static_assert(14 + DR_FARM_ALL_PER_LINE * (1 + 10 + 1 + 3 + 1 + 20) <= DR_FARM_LINE_MAX, "FarmStatAll line");
	static_assert(14 + DR_FARM_ITEMS_PER_LINE * (1 + 10 + 1 + 10 + 1 + 10) <= DR_FARM_LINE_MAX, "FarmItems line");
	static_assert(13 + DR_FARM_MAPS_PER_LINE * (1 + 11 + 1 + 20 + 1 + 20 + 1 + 20) <= DR_FARM_LINE_MAX, "FarmStatMap line");
	static_assert(14 + DR_FARM_TOP_LINE * (1 + 10 + 1 + 20) <= DR_FARM_LINE_MAX, "FarmStatTop/Mob line");
	static_assert(9 + 8 * 21 <= DR_FARM_LINE_MAX, "FarmHist / FarmStatRec line");
	static_assert(11 + 12 * 21 <= DR_FARM_LINE_MAX, "FarmStatSum line");
	// The rows of one trimming (a long query list stays under QUERY_MAX_LEN).
	const int DR_FARM_TRIM_BATCH = 200;
	// The dr_farm_item / dr_farm_mob / dr_farm_map rows of one INSERT.
	const size_t DR_FARM_ROWS_BATCH = 30;
	// A drop's tag: its life (an item on the ground goes after 300 s), the most
	// tags kept, how often the tick drops the old ones; the deepest scope stack.
	const DWORD DR_FARM_TAG_SEC = 330;
	const size_t DR_FARM_TAG_MAX = 8192;
	const DWORD DR_FARM_TAG_PURGE_MS = 30000;
	const int DR_FARM_SCOPE_DEPTH = 8;
	// DrFarmCategoryOf
	enum { DR_FARM_CAT_MATERIAL, DR_FARM_CAT_USE, DR_FARM_CAT_WEAPON, DR_FARM_CAT_ARMOR, DR_FARM_CAT_JEWEL, DR_FARM_CAT_OTHER };

	// The sources of a kill, an item, yang (the suffixes m, s, b of the columns).
	enum { DR_FARM_SRC_MOB, DR_FARM_SRC_STONE, DR_FARM_SRC_BOSS, DR_FARM_SRC_COUNT };
	// player.dr_farm_session.status
	enum { DR_FARM_RUNNING, DR_FARM_PAUSED, DR_FARM_ENDED };
	// player.dr_farm_session.end_reason
	enum { DR_FARM_END_MANUAL, DR_FARM_END_LIMIT, DR_FARM_END_ABANDONED };
	// FarmResult
	enum
	{
		DR_FARM_OK, DR_FARM_ALREADY, DR_FARM_NONE, DR_FARM_BAD_STATE, DR_FARM_BAD_LIMIT, DR_FARM_DB_ERROR,
		DR_FARM_LIMIT_ENDED
	};
	// What DrFarmAdopt found.
	enum { DR_FARM_ADOPT_ERROR, DR_FARM_ADOPT_NONE, DR_FARM_ADOPT_SESSION, DR_FARM_ADOPT_ENDED };

	// A row of dr_farm_mob (by the monster's vnum) and of dr_farm_map (by the
	// map's index), absolute as the session's counters.
	struct TDrFarmMobRow
	{
		BYTE src = DR_FARM_SRC_MOB;
		int kills = 0;
		bool dirty = false;
	};
	struct TDrFarmMapRow
	{
		long long yang = 0;
		int items = 0;
		int kills = 0;
		bool dirty = false;
	};
	// A row of dr_farm_item (by the item's vnum and the source).
	struct TDrFarmItemRow
	{
		BYTE cat = DR_FARM_CAT_OTHER;
		int cnt = 0;
		DWORD lastAt = 0;	// unix time of the last count
		bool dirty = false;
		DWORD gen = 0;		// the session's itemGen at the last change ("stan" sends the newer rows)
	};
	typedef std::map<DWORD, TDrFarmMobRow> TDrFarmMobMap;
	typedef std::map<long, TDrFarmMapRow> TDrFarmMapMap;
	typedef std::map<std::pair<DWORD, BYTE>, TDrFarmItemRow> TDrFarmItemMap;

	struct TDrFarmSession
	{
		long long id = 0;
		DWORD pid = 0;
		DWORD startedAt = 0;	// unix time
		BYTE status = DR_FARM_RUNNING;
		int limitSec = 0;		// 0: no limit
		int activeSec = 0;
		DWORD lastMs = 0;		// get_dword_time() of the last count (a running session)
		DWORD restMs = 0;		// milliseconds that are not a whole second yet
		DWORD flushedMs = 0;	// get_dword_time() of the last write
		DWORD retryMs = 0;		// a refused ending is not tried before this time (0: now)
		long long exp = 0;
		long long yang[DR_FARM_SRC_COUNT] = { 0, 0, 0 };
		int items[DR_FARM_SRC_COUNT] = { 0, 0, 0 };
		int kills[DR_FARM_SRC_COUNT] = { 0, 0, 0 };
		bool dirty = false;		// news since the last write
		DWORD lastKillVid = 0;	// a death is counted once
		DWORD itemGen = 0;		// bumped on every change of an item row
		DWORD sentGen = 0;		// itemGen when the last FarmItems went to the player
		DWORD yangLastAt = 0;	// MT2009_PLUS_FARM_SESSION_V1: unix time of the last yang (FarmInfo, yang_last)
		std::map<int, int> spark;	// MT2009_PLUS_FARM_SESSION_V1: items by active minute (FarmSpark), memory only
		TDrFarmMobMap mobs;
		TDrFarmMapMap maps;
		TDrFarmItemMap drops;
	};

	// The tag of a kill's item on the ground, and the context of a scope:
	// who may count it (the kill's pids, an owner) and where it comes from.
	struct TDrFarmTag
	{
		BYTE src;
		DWORD mobVnum;
		long mapIdx;
		DWORD expire;		// get_global_time()
		BYTE n;
		DWORD eligible[DR_FARM_KILL_PIDS];
	};
	typedef std::unordered_map<DWORD, TDrFarmTag> TDrFarmTagMap;

	typedef std::map<DWORD, TDrFarmSession> TDrFarmSessionMap;
	TDrFarmSessionMap s_mapDrFarmSessions;	// by player id, this core only
	TDrFarmKillCtx s_kDrFarmKill = {};		// DrFarmLastKill
	TDrFarmTagMap s_mapDrFarmTags;			// by the item's VID
	DWORD s_dwDrFarmTagPurgeMs = 0;
	DWORD s_dwDrFarmTagFullLog = 0;
	TDrFarmTag s_aDrFarmScopes[DR_FARM_SCOPE_DEPTH];	// n 0: nobody counts
	int s_iDrFarmScopeDepth = 0;
	bool s_bDrFarmTables = false;
	DWORD s_dwDrFarmTablesRetry = 0;
	LPEVENT s_pkDrFarmTick = NULL;
	LPEVENT s_pkDrFarmInit = NULL;

	// ---------------------------------------------------------------------
	// The tables. The migrator does not know them: the core makes them
	// (as DR_DROPEK_V1 does). Asked until it works, then never again.
	// ---------------------------------------------------------------------

	bool DrFarmSqlOk(const std::unique_ptr<SQLMsg>& msg)
	{
		return msg.get() && msg->uiSQLErrno == 0 && msg->Get();
	}

	bool EnsureDrFarmTables()
	{
		if (s_bDrFarmTables)
			return true;
		const DWORD now = get_dword_time();
		if (s_dwDrFarmTablesRetry != 0 && (int)(now - s_dwDrFarmTablesRetry) < 0)
			return false;
		static const char* const create[] =
		{
			"CREATE TABLE IF NOT EXISTS player.dr_farm_session ("
			"id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
			"player_id INT UNSIGNED NOT NULL, "
			"started_at INT NOT NULL, "
			"ended_at INT NULL DEFAULT NULL, "
			"status TINYINT NOT NULL DEFAULT 0, "
			"end_reason TINYINT NOT NULL DEFAULT 0, "
			"limit_sec INT NOT NULL DEFAULT 0, "
			"active_sec INT NOT NULL DEFAULT 0, "
			"exp BIGINT NOT NULL DEFAULT 0, "
			"yang_m BIGINT NOT NULL DEFAULT 0, yang_s BIGINT NOT NULL DEFAULT 0, yang_b BIGINT NOT NULL DEFAULT 0, "
			"items_m INT NOT NULL DEFAULT 0, items_s INT NOT NULL DEFAULT 0, items_b INT NOT NULL DEFAULT 0, "
			"kills_m INT NOT NULL DEFAULT 0, kills_s INT NOT NULL DEFAULT 0, kills_b INT NOT NULL DEFAULT 0, "
			"yang_last INT NOT NULL DEFAULT 0, "	// MT2009_PLUS_FARM_SESSION_V1: the time of the last yang
			"KEY player_status (player_id, status), "
			"KEY player_started (player_id, started_at)) ENGINE=InnoDB",

			"CREATE TABLE IF NOT EXISTS player.dr_farm_item ("
			"session_id BIGINT NOT NULL, "
			"vnum INT UNSIGNED NOT NULL, "
			"src TINYINT NOT NULL, "
			"cat TINYINT NOT NULL DEFAULT 0, "
			"cnt INT NOT NULL DEFAULT 0, "
			"last_at INT NOT NULL DEFAULT 0, "
			"PRIMARY KEY (session_id, vnum, src)) ENGINE=InnoDB",

			"CREATE TABLE IF NOT EXISTS player.dr_farm_mob ("
			"session_id BIGINT NOT NULL, "
			"mob_vnum INT UNSIGNED NOT NULL, "
			"src TINYINT NOT NULL, "
			"kills INT NOT NULL DEFAULT 0, "
			"PRIMARY KEY (session_id, mob_vnum)) ENGINE=InnoDB",

			"CREATE TABLE IF NOT EXISTS player.dr_farm_map ("
			"session_id BIGINT NOT NULL, "
			"map_idx INT NOT NULL, "
			"yang BIGINT NOT NULL DEFAULT 0, "
			"items INT NOT NULL DEFAULT 0, "
			"kills INT NOT NULL DEFAULT 0, "
			"PRIMARY KEY (session_id, map_idx)) ENGINE=InnoDB"
		};
		for (size_t i = 0; i < sizeof(create) / sizeof(create[0]); ++i)
		{
			std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(create[i]));
			if (!DrFarmSqlOk(msg))
			{
				s_dwDrFarmTablesRetry = now + DR_FARM_TABLES_RETRY_MS;
				sys_err("DR_FARM: the table %u cannot be created errno=%u", (unsigned)i, msg.get() ? msg->uiSQLErrno : 0U);
				return false;
			}
		}
		s_bDrFarmTables = true;
		sys_log(0, "DR_FARM: table ready");
		return true;
	}

	// ---------------------------------------------------------------------
	// To the client.
	// ---------------------------------------------------------------------

	// Refused rather than cut when it would not fit (as SendDrDropekCommand);
	// DR_FARM_DEBUG (not defined; beside DR_FARM_SESSION_V1 in CommonDefines.h
	// for a test build) writes each to the log.
	void SendDrFarmCommand(LPCHARACTER ch, const char* format, ...)
	{
		char text[CHAT_MAX_LEN + 1];
		va_list args;
		va_start(args, format);
		const int len = vsnprintf(text, sizeof(text), format, args);
		va_end(args);
		if (len < 0 || len > DR_FARM_LINE_MAX)
		{
			sys_err("DR_FARM: command too long (%d) for %s", len, ch->GetName());
			return;
		}
		ch->ChatPacket(CHAT_TYPE_COMMAND, "%s", text);
#ifdef DR_FARM_DEBUG
		sys_log(0, "DR_FARM: to=%s len=%d %s", ch->GetName(), len, text);
		static int s_iLongest = 0;
		if (len > s_iLongest)
		{
			s_iLongest = len;
			sys_log(0, "DR_FARM: longest line so far %d (limit %d)", len, DR_FARM_LINE_MAX);
		}
#endif
	}

	// s NULL: no session.
	void SendDrFarmInfo(LPCHARACTER ch, const TDrFarmSession* s)
	{
		const long long now = (long long)get_global_time();
		if (!s)
		{
			SendDrFarmCommand(ch, "FarmInfo %d 0 0 0 0 0 %lld 0 0 0 0 0 0 0 0 0 0 0", DR_FARM_PROTOCOL, now);
			return;
		}
		SendDrFarmCommand(ch, "FarmInfo %d %d %lld %u %d %d %lld %lld %lld %lld %lld %d %d %d %d %d %d %u",
				DR_FARM_PROTOCOL, s->status == DR_FARM_RUNNING ? 1 : 2, s->id, (unsigned)s->startedAt,
				s->activeSec, s->limitSec, now, s->exp,
				s->yang[DR_FARM_SRC_MOB], s->yang[DR_FARM_SRC_STONE], s->yang[DR_FARM_SRC_BOSS],
				s->items[DR_FARM_SRC_MOB], s->items[DR_FARM_SRC_STONE], s->items[DR_FARM_SRC_BOSS],
				s->kills[DR_FARM_SRC_MOB], s->kills[DR_FARM_SRC_STONE], s->kills[DR_FARM_SRC_BOSS],
				(unsigned)s->yangLastAt);
	}

	void SendDrFarmResult(LPCHARACTER ch, int code)
	{
		SendDrFarmCommand(ch, "FarmResult %d", code);
	}

	// ---------------------------------------------------------------------
	// The state in memory.
	// ---------------------------------------------------------------------

	TDrFarmSession* FindDrFarmSession(DWORD pid)
	{
		TDrFarmSessionMap::iterator it = s_mapDrFarmSessions.find(pid);
		return it == s_mapDrFarmSessions.end() ? NULL : &it->second;
	}

	void RecountDrFarmActive()
	{
		int running = 0;
		for (TDrFarmSessionMap::const_iterator it = s_mapDrFarmSessions.begin(); it != s_mapDrFarmSessions.end(); ++it)
			if (it->second.status == DR_FARM_RUNNING)
				++running;
		g_iDrFarmActive = running;
		// A tag must not outlive the gate: nothing runs, nothing is counted (and the
		// tick that purges the tags stops with the last running session).
		if (running == 0)
			s_mapDrFarmTags.clear();
	}

	bool DrFarmLimitReached(const TDrFarmSession& s)
	{
		return s.limitSec > 0 && s.activeSec >= s.limitSec;
	}

	// Adds the time since the last count to a running session (never past the
	// limit).
	void CountDrFarmTime(TDrFarmSession& s, DWORD now)
	{
		if (s.status != DR_FARM_RUNNING)
			return;
		const DWORD elapsed = now - s.lastMs;
		s.lastMs = now;
		s.restMs += elapsed;
		const DWORD secs = s.restMs / 1000;
		if (secs == 0)
			return;
		s.restMs -= secs * 1000;
		s.activeSec += (int)secs;
		if (s.limitSec > 0 && s.activeSec > s.limitSec)
			s.activeSec = s.limitSec;
		s.dirty = true;
	}

	// ---------------------------------------------------------------------
	// The row. Every counter is absolute and only grows (GREATEST); an ended
	// row is never written again (status<2). status < 0: the status is not
	// written (the periodic write, which must not overtake a change of state
	// made with DirectQuery); endReason < 0: not an ending.
	// ---------------------------------------------------------------------

	void BuildDrFarmWrite(char* query, size_t size, const TDrFarmSession& s, int status, int endReason, DWORD endedAt)
	{
		int n = snprintf(query, size, "UPDATE player.dr_farm_session SET ");
		if (status >= 0 && n > 0 && (size_t)n < size)
			n += snprintf(query + n, size - n, "status=%d, ", status);
		if (endReason >= 0 && n > 0 && (size_t)n < size)
			n += snprintf(query + n, size - n, "end_reason=%d, ended_at=%u, ", endReason, (unsigned)endedAt);
		if (n > 0 && (size_t)n < size)
			snprintf(query + n, size - n,
					"active_sec=GREATEST(active_sec,%d), exp=GREATEST(exp,%lld)"
					", yang_m=GREATEST(yang_m,%lld), yang_s=GREATEST(yang_s,%lld), yang_b=GREATEST(yang_b,%lld)"
					", items_m=GREATEST(items_m,%d), items_s=GREATEST(items_s,%d), items_b=GREATEST(items_b,%d)"
					", kills_m=GREATEST(kills_m,%d), kills_s=GREATEST(kills_s,%d), kills_b=GREATEST(kills_b,%d)"
					", yang_last=GREATEST(yang_last,%u)"
					" WHERE id=%lld AND status<2",
					s.activeSec, s.exp,
					s.yang[DR_FARM_SRC_MOB], s.yang[DR_FARM_SRC_STONE], s.yang[DR_FARM_SRC_BOSS],
					s.items[DR_FARM_SRC_MOB], s.items[DR_FARM_SRC_STONE], s.items[DR_FARM_SRC_BOSS],
					s.kills[DR_FARM_SRC_MOB], s.kills[DR_FARM_SRC_STONE], s.kills[DR_FARM_SRC_BOSS],
					(unsigned)s.yangLastAt, s.id);
	}

	// One INSERT of the rows in values (DirectQuery, or AsyncQuery when not
	// direct); the rows are clean once it went. False: DirectQuery refused it.
	bool FlushDrFarmRows(const char* head, std::string& values, const char* tail, std::vector<bool*>& dirty, bool direct)
	{
		if (dirty.empty())
			return true;
		const std::string query = std::string(head) + values + tail;
		if (direct)
		{
			std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query.c_str()));
			if (!DrFarmSqlOk(msg))
			{
				sys_err("DR_FARM: the rows of a session cannot be written errno=%u", msg.get() ? msg->uiSQLErrno : 0U);
				return false;
			}
		}
		else
			AccountDB::instance().AsyncQuery(query.c_str());
		for (size_t i = 0; i < dirty.size(); ++i)
			*dirty[i] = false;
		values.clear();
		dirty.clear();
		return true;
	}

	// The dirty rows of dr_farm_item, dr_farm_mob and dr_farm_map,
	// DR_FARM_ROWS_BATCH a query, absolute (GREATEST) as the session's row.
	bool WriteDrFarmRows(TDrFarmSession& s, bool direct)
	{
		static const char* const itemHead = "INSERT INTO player.dr_farm_item (session_id, vnum, src, cat, cnt, last_at) VALUES ";
		static const char* const itemTail = " ON DUPLICATE KEY UPDATE cnt=GREATEST(cnt,VALUES(cnt)), "
				"last_at=GREATEST(last_at,VALUES(last_at))";
		static const char* const mobHead = "INSERT INTO player.dr_farm_mob (session_id, mob_vnum, src, kills) VALUES ";
		static const char* const mobTail = " ON DUPLICATE KEY UPDATE kills=GREATEST(kills,VALUES(kills))";
		static const char* const mapHead = "INSERT INTO player.dr_farm_map (session_id, map_idx, yang, items, kills) VALUES ";
		static const char* const mapTail = " ON DUPLICATE KEY UPDATE yang=GREATEST(yang,VALUES(yang)), "
				"items=GREATEST(items,VALUES(items)), kills=GREATEST(kills,VALUES(kills))";
		std::string values;
		std::vector<bool*> dirty;
		char one[128];
		for (TDrFarmItemMap::iterator it = s.drops.begin(); it != s.drops.end(); ++it)
		{
			if (!it->second.dirty)
				continue;
			snprintf(one, sizeof(one), "%s(%lld,%u,%d,%d,%d,%u)", values.empty() ? "" : ",",
					s.id, (unsigned)it->first.first, (int)it->first.second, (int)it->second.cat,
					it->second.cnt, (unsigned)it->second.lastAt);
			values += one;
			dirty.push_back(&it->second.dirty);
			if (dirty.size() >= DR_FARM_ROWS_BATCH && !FlushDrFarmRows(itemHead, values, itemTail, dirty, direct))
				return false;
		}
		if (!FlushDrFarmRows(itemHead, values, itemTail, dirty, direct))
			return false;
		for (TDrFarmMobMap::iterator it = s.mobs.begin(); it != s.mobs.end(); ++it)
		{
			if (!it->second.dirty)
				continue;
			snprintf(one, sizeof(one), "%s(%lld,%u,%d,%d)", values.empty() ? "" : ",",
					s.id, (unsigned)it->first, (int)it->second.src, it->second.kills);
			values += one;
			dirty.push_back(&it->second.dirty);
			if (dirty.size() >= DR_FARM_ROWS_BATCH && !FlushDrFarmRows(mobHead, values, mobTail, dirty, direct))
				return false;
		}
		if (!FlushDrFarmRows(mobHead, values, mobTail, dirty, direct))
			return false;
		for (TDrFarmMapMap::iterator it = s.maps.begin(); it != s.maps.end(); ++it)
		{
			if (!it->second.dirty)
				continue;
			snprintf(one, sizeof(one), "%s(%lld,%ld,%lld,%d,%d)", values.empty() ? "" : ",",
					s.id, it->first, it->second.yang, it->second.items, it->second.kills);
			values += one;
			dirty.push_back(&it->second.dirty);
			if (dirty.size() >= DR_FARM_ROWS_BATCH && !FlushDrFarmRows(mapHead, values, mapTail, dirty, direct))
				return false;
		}
		return FlushDrFarmRows(mapHead, values, mapTail, dirty, direct);
	}

	// The rows first, so an ended session's row comes after its children.
	bool WriteDrFarmDirect(TDrFarmSession& s, int status, int endReason, DWORD endedAt)
	{
		if (!WriteDrFarmRows(s, true))
			return false;
		char query[1024];
		BuildDrFarmWrite(query, sizeof(query), s, status, endReason, endedAt);
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (!DrFarmSqlOk(msg))
		{
			sys_err("DR_FARM: the session %lld cannot be written errno=%u", s.id, msg.get() ? msg->uiSQLErrno : 0U);
			return false;
		}
		s.flushedMs = get_dword_time();
		s.dirty = false;
		return true;
	}

	// The periodic write: the counters and the time only (withStatus false). A
	// write that stands in for a refused DirectQuery (withStatus true) keeps the
	// status too.
	void WriteDrFarmAsync(TDrFarmSession& s, bool withStatus)
	{
		WriteDrFarmRows(s, false);
		char query[1024];
		BuildDrFarmWrite(query, sizeof(query), s, withStatus ? (int)s.status : -1, -1, 0);
		AccountDB::instance().AsyncQuery(query);
		s.flushedMs = get_dword_time();
		s.dirty = false;
	}

	// The oldest finished sessions of a player over DR_FARM_HISTORY_MAX go,
	// with their rows in the child tables (a session stays when its children
	// cannot be deleted: the next ending tries again).
	void TrimDrFarmHistory(DWORD pid)
	{
		char query[256];
		snprintf(query, sizeof(query),
				"SELECT id FROM player.dr_farm_session WHERE player_id=%u AND status=2 "
				"ORDER BY id DESC LIMIT %d, %d",
				(unsigned)pid, DR_FARM_HISTORY_MAX, DR_FARM_TRIM_BATCH);
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (!DrFarmSqlOk(msg) || !msg->Get()->pSQLResult)
		{
			sys_err("DR_FARM: the history of %u cannot be read errno=%u", (unsigned)pid, msg.get() ? msg->uiSQLErrno : 0U);
			return;
		}
		std::string ids;
		int count = 0;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			if (!row[0])
				continue;
			long long id = 0;
			str_to_number(id, row[0]);
			if (id <= 0)
				continue;
			char one[32];
			snprintf(one, sizeof(one), "%s%lld", ids.empty() ? "" : ",", id);
			ids += one;
			++count;
		}
		if (count == 0)
			return;
		static const char* const children[] =
		{
			"DELETE FROM player.dr_farm_item WHERE session_id IN (",
			"DELETE FROM player.dr_farm_mob WHERE session_id IN (",
			"DELETE FROM player.dr_farm_map WHERE session_id IN (",
			"DELETE FROM player.dr_farm_session WHERE status=2 AND id IN ("
		};
		for (size_t i = 0; i < sizeof(children) / sizeof(children[0]); ++i)
		{
			const std::string del = std::string(children[i]) + ids + ")";
			std::unique_ptr<SQLMsg> res(AccountDB::instance().DirectQuery(del.c_str()));
			if (!DrFarmSqlOk(res))
			{
				sys_err("DR_FARM: the history of %u cannot be trimmed (step %u) errno=%u",
						(unsigned)pid, (unsigned)i, res.get() ? res->uiSQLErrno : 0U);
				return;
			}
		}
		sys_log(0, "DR_FARM: pid=%u history trimmed by %d", (unsigned)pid, count);
	}

	// Ends a session in the table (the counters of s are written with it) and
	// trims the history; false when the table refused (nothing changed).
	bool FinishDrFarmSession(TDrFarmSession& s, int endReason)
	{
		const DWORD endedAt = (DWORD)get_global_time();
		if (!WriteDrFarmDirect(s, DR_FARM_ENDED, endReason, endedAt))
			return false;
		sys_log(0, "DR_FARM: end pid=%u id=%lld reason=%d active=%d limit=%d",
				(unsigned)s.pid, s.id, endReason, s.activeSec, s.limitSec);
		TrimDrFarmHistory(s.pid);
		return true;
	}

	// The tags past their life go (the tick, a full map).
	void PurgeDrFarmTags()
	{
		const DWORD now = (DWORD)get_global_time();
		for (TDrFarmTagMap::iterator it = s_mapDrFarmTags.begin(); it != s_mapDrFarmTags.end();)
		{
			if (it->second.expire <= now)
				it = s_mapDrFarmTags.erase(it);
			else
				++it;
		}
	}

	// ---------------------------------------------------------------------
	// The tick: one second, started with the first running session, stopped
	// (returns 0) when none runs. Counts the time, ends a session at its
	// limit, writes the news of a running session every DR_FARM_FLUSH_MS,
	// drops the old tags every DR_FARM_TAG_PURGE_MS.
	// ---------------------------------------------------------------------

	void TickDrFarm()
	{
		const DWORD now = get_dword_time();
		if (!s_mapDrFarmTags.empty() && now - s_dwDrFarmTagPurgeMs >= DR_FARM_TAG_PURGE_MS)
		{
			s_dwDrFarmTagPurgeMs = now;
			PurgeDrFarmTags();
		}
		for (TDrFarmSessionMap::iterator it = s_mapDrFarmSessions.begin(); it != s_mapDrFarmSessions.end();)
		{
			TDrFarmSession& s = it->second;
			if (s.status != DR_FARM_RUNNING)
			{
				++it;
				continue;
			}
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(s.pid);
			if (!ch || !ch->GetDesc())
			{
				// The character is gone without DrFarmOnDisconnect: the session stops here.
				sys_err("DR_FARM: pid=%u id=%lld is not in the world, its session leaves", (unsigned)s.pid, s.id);
				CountDrFarmTime(s, now);
				WriteDrFarmDirect(s, s.status, -1, 0);
				s_mapDrFarmSessions.erase(it++);
				continue;
			}
			CountDrFarmTime(s, now);
			if (DrFarmLimitReached(s))
			{
				if (s.retryMs == 0 || (int)(now - s.retryMs) >= 0)
				{
					if (FinishDrFarmSession(s, DR_FARM_END_LIMIT))
					{
						SendDrFarmInfo(ch, NULL);
						SendDrFarmResult(ch, DR_FARM_LIMIT_ENDED);
						s_mapDrFarmSessions.erase(it++);
						continue;
					}
					s.retryMs = now + DR_FARM_END_RETRY_MS;
				}
			}
			else if (s.dirty && now - s.flushedMs >= DR_FARM_FLUSH_MS)
				WriteDrFarmAsync(s, false);
			++it;
		}
		RecountDrFarmActive();
	}

	EVENTINFO(dr_farm_tick_info)
	{
		int unused;
		dr_farm_tick_info() : unused(0) {}
	};

	EVENTFUNC(dr_farm_tick_event)
	{
		TickDrFarm();
		if (g_iDrFarmActive == 0)
		{
			s_pkDrFarmTick = NULL;
			return 0;
		}
		return PASSES_PER_SEC(1);
	}

	void EnsureDrFarmTick()
	{
		if (s_pkDrFarmTick)
			return;
		dr_farm_tick_info* info = AllocEventInfo<dr_farm_tick_info>();
		s_pkDrFarmTick = event_create(dr_farm_tick_event, info, PASSES_PER_SEC(1));
	}

	// At the core's start the tables may be out of reach (the database comes
	// up later): asked again every ten seconds until they are made.
	EVENTINFO(dr_farm_init_info)
	{
		int unused;
		dr_farm_init_info() : unused(0) {}
	};

	EVENTFUNC(dr_farm_init_event)
	{
		if (EnsureDrFarmTables())
		{
			s_pkDrFarmInit = NULL;
			return 0;
		}
		return PASSES_PER_SEC(10);
	}

	// ---------------------------------------------------------------------
	// Reading the player's open session (status 0 or 1) into the map.
	// ---------------------------------------------------------------------

	// The dr_farm_item / dr_farm_mob / dr_farm_map rows of a session that goes
	// on, so that its counters go on from the table's (they are written absolute).
	bool ReadDrFarmRows(TDrFarmSession& s)
	{
		char query[256];
		snprintf(query, sizeof(query), "SELECT vnum, src, cat, cnt, last_at FROM player.dr_farm_item WHERE session_id=%lld", s.id);
		std::unique_ptr<SQLMsg> items(AccountDB::instance().DirectQuery(query));
		if (!DrFarmSqlOk(items) || !items->Get()->pSQLResult)
		{
			sys_err("DR_FARM: the items of the session %lld cannot be read errno=%u", s.id, items.get() ? items->uiSQLErrno : 0U);
			return false;
		}
		MYSQL_ROW itemRow;
		while (NULL != (itemRow = mysql_fetch_row(items->Get()->pSQLResult)))
		{
			if (!itemRow[0] || !itemRow[1])
				continue;
			DWORD vnum = 0;
			unsigned int src = 0, cat = 0;
			str_to_number(vnum, itemRow[0]);
			str_to_number(src, itemRow[1]);
			if (src >= DR_FARM_SRC_COUNT)
				continue;
			TDrFarmItemRow& item = s.drops[std::make_pair(vnum, (BYTE)src)];
			if (itemRow[2]) str_to_number(cat, itemRow[2]);
			if (itemRow[3]) str_to_number(item.cnt, itemRow[3]);
			if (itemRow[4]) str_to_number(item.lastAt, itemRow[4]);
			item.cat = cat <= DR_FARM_CAT_OTHER ? (BYTE)cat : (BYTE)DR_FARM_CAT_OTHER;
			item.gen = 1;	// the first "stan" after the entry sends them all
		}
		s.itemGen = s.drops.empty() ? 0 : 1;
		s.sentGen = 0;
		snprintf(query, sizeof(query), "SELECT mob_vnum, src, kills FROM player.dr_farm_mob WHERE session_id=%lld", s.id);
		std::unique_ptr<SQLMsg> mobs(AccountDB::instance().DirectQuery(query));
		if (!DrFarmSqlOk(mobs) || !mobs->Get()->pSQLResult)
		{
			sys_err("DR_FARM: the monsters of the session %lld cannot be read errno=%u", s.id, mobs.get() ? mobs->uiSQLErrno : 0U);
			return false;
		}
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(mobs->Get()->pSQLResult)))
		{
			if (!row[0])
				continue;
			DWORD vnum = 0;
			unsigned int src = 0;
			str_to_number(vnum, row[0]);
			TDrFarmMobRow& mob = s.mobs[vnum];
			if (row[1]) str_to_number(src, row[1]);
			if (row[2]) str_to_number(mob.kills, row[2]);
			mob.src = src < DR_FARM_SRC_COUNT ? (BYTE)src : (BYTE)DR_FARM_SRC_MOB;
		}
		snprintf(query, sizeof(query), "SELECT map_idx, yang, items, kills FROM player.dr_farm_map WHERE session_id=%lld", s.id);
		std::unique_ptr<SQLMsg> maps(AccountDB::instance().DirectQuery(query));
		if (!DrFarmSqlOk(maps) || !maps->Get()->pSQLResult)
		{
			sys_err("DR_FARM: the maps of the session %lld cannot be read errno=%u", s.id, maps.get() ? maps->uiSQLErrno : 0U);
			return false;
		}
		while (NULL != (row = mysql_fetch_row(maps->Get()->pSQLResult)))
		{
			if (!row[0])
				continue;
			long idx = 0;
			str_to_number(idx, row[0]);
			TDrFarmMapRow& map = s.maps[idx];
			if (row[1]) str_to_number(map.yang, row[1]);
			if (row[2]) str_to_number(map.items, row[2]);
			if (row[3]) str_to_number(map.kills, row[3]);
		}
		return true;
	}

	// The newest open row goes on; older ones (there should be none) end with
	// DR_FARM_END_ABANDONED. A row at its limit ends (DR_FARM_END_LIMIT) and
	// is not taken. The map has no session of the player when this is called.
	int AdoptDrFarmSession(DWORD pid)
	{
		char query[512];
		snprintf(query, sizeof(query),
				"SELECT id, started_at, status, limit_sec, active_sec, exp, yang_m, yang_s, yang_b, "
				"items_m, items_s, items_b, kills_m, kills_s, kills_b, yang_last "
				"FROM player.dr_farm_session WHERE player_id=%u AND status IN (0,1) ORDER BY id DESC",
				(unsigned)pid);
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (!DrFarmSqlOk(msg) || !msg->Get()->pSQLResult)
		{
			sys_err("DR_FARM: the session of %u cannot be read errno=%u", (unsigned)pid, msg.get() ? msg->uiSQLErrno : 0U);
			return DR_FARM_ADOPT_ERROR;
		}
		TDrFarmSession s;
		bool found = false;
		bool older = false;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			if (found)
			{
				older = true;
				continue;
			}
			unsigned int startedAt = 0, status = 0;
			s.pid = pid;
			if (row[0]) str_to_number(s.id, row[0]);
			if (row[1]) str_to_number(startedAt, row[1]);
			if (row[2]) str_to_number(status, row[2]);
			if (row[3]) str_to_number(s.limitSec, row[3]);
			if (row[4]) str_to_number(s.activeSec, row[4]);
			if (row[5]) str_to_number(s.exp, row[5]);
			for (int i = 0; i < DR_FARM_SRC_COUNT; ++i)
			{
				if (row[6 + i]) str_to_number(s.yang[i], row[6 + i]);
				if (row[9 + i]) str_to_number(s.items[i], row[9 + i]);
				if (row[12 + i]) str_to_number(s.kills[i], row[12 + i]);
			}
			if (row[15]) str_to_number(s.yangLastAt, row[15]);	// MT2009_PLUS_FARM_SESSION_V1
			s.startedAt = startedAt;
			s.status = status == DR_FARM_PAUSED ? DR_FARM_PAUSED : DR_FARM_RUNNING;
			found = s.id > 0;
		}
		if (!found)
			return DR_FARM_ADOPT_NONE;
		const DWORD nowSec = (DWORD)get_global_time();
		if (older)
		{
			char close[256];
			snprintf(close, sizeof(close),
					"UPDATE player.dr_farm_session SET status=2, end_reason=%d, ended_at=%u "
					"WHERE player_id=%u AND status IN (0,1) AND id<>%lld",
					DR_FARM_END_ABANDONED, (unsigned)nowSec, (unsigned)pid, s.id);
			std::unique_ptr<SQLMsg> res(AccountDB::instance().DirectQuery(close));
			if (!DrFarmSqlOk(res))
				sys_err("DR_FARM: the older sessions of %u cannot be closed errno=%u", (unsigned)pid, res.get() ? res->uiSQLErrno : 0U);
			else
				sys_log(0, "DR_FARM: pid=%u older open sessions closed (kept id=%lld)", (unsigned)pid, s.id);
			TrimDrFarmHistory(pid);
		}
		if (DrFarmLimitReached(s))
		{
			if (!FinishDrFarmSession(s, DR_FARM_END_LIMIT))
				return DR_FARM_ADOPT_ERROR;
			return DR_FARM_ADOPT_ENDED;
		}
		if (!ReadDrFarmRows(s))
			return DR_FARM_ADOPT_ERROR;
		const DWORD now = get_dword_time();
		s.lastMs = now;
		s.restMs = 0;
		s.flushedMs = now;
		s.dirty = false;
		s_mapDrFarmSessions[pid] = s;
		RecountDrFarmActive();
		if (s.status == DR_FARM_RUNNING)
			EnsureDrFarmTick();
		sys_log(0, "DR_FARM: enter pid=%u id=%lld status=%d active=%d limit=%d",
				(unsigned)pid, s.id, (int)s.status, s.activeSec, s.limitSec);
		return DR_FARM_ADOPT_SESSION;
	}

	// ---------------------------------------------------------------------
	// The commands. Each returns a FarmResult code; the state in memory
	// changes only when the table has taken the change.
	// ---------------------------------------------------------------------

	// Whole decimal digits, at most six: 3600 7200 14400 28800 0 only (a test
	// build with DR_FARM_DEBUG takes 60 as well, a limit a test can wait for).
	bool ParseDrFarmLimit(const char* text, int& limit)
	{
		if (!text || !text[0] || strlen(text) > 6)
			return false;
		for (const char* p = text; *p; ++p)
			if (*p < '0' || *p > '9')
				return false;
		str_to_number(limit, text);
#ifdef DR_FARM_DEBUG
		if (limit == 60)
			return true;
#endif
		return limit == 3600 || limit == 7200 || limit == 14400 || limit == 28800 || limit == 0;
	}

	int StartDrFarm(LPCHARACTER ch, const char* args)
	{
		const DWORD pid = ch->GetPlayerID();
		if (FindDrFarmSession(pid))
			return DR_FARM_ALREADY;
		char word[16];
		one_argument(args, word, sizeof(word));
		int limit = 0;
		if (!ParseDrFarmLimit(word, limit))
			return DR_FARM_BAD_LIMIT;
		// An open row this core has not read (the read at the entry failed, or
		// another core wrote it a moment ago) is taken, not doubled.
		const int adopted = AdoptDrFarmSession(pid);
		if (adopted == DR_FARM_ADOPT_ERROR)
			return DR_FARM_DB_ERROR;
		if (adopted == DR_FARM_ADOPT_SESSION)
			return DR_FARM_ALREADY;
		const DWORD nowSec = (DWORD)get_global_time();
		char query[256];
		snprintf(query, sizeof(query),
				"INSERT INTO player.dr_farm_session (player_id, started_at, status, limit_sec) VALUES (%u, %u, 0, %d)",
				(unsigned)pid, (unsigned)nowSec, limit);
		std::unique_ptr<SQLMsg> msg(AccountDB::instance().DirectQuery(query));
		if (!DrFarmSqlOk(msg) || msg->Get()->uiInsertID == 0)
		{
			sys_err("DR_FARM: the session of %u cannot be created errno=%u", (unsigned)pid, msg.get() ? msg->uiSQLErrno : 0U);
			return DR_FARM_DB_ERROR;
		}
		TDrFarmSession s;
		s.id = msg->Get()->uiInsertID;
		s.pid = pid;
		s.startedAt = nowSec;
		s.status = DR_FARM_RUNNING;
		s.limitSec = limit;
		s.lastMs = get_dword_time();
		s.flushedMs = s.lastMs;
		s_mapDrFarmSessions[pid] = s;
		RecountDrFarmActive();
		EnsureDrFarmTick();
		sys_log(0, "DR_FARM: start pid=%u id=%lld limit=%d", (unsigned)pid, s.id, limit);
		return DR_FARM_OK;
	}

	int PauseDrFarm(LPCHARACTER ch)
	{
		TDrFarmSession* s = FindDrFarmSession(ch->GetPlayerID());
		if (!s)
			return DR_FARM_NONE;
		if (s->status != DR_FARM_RUNNING)
			return DR_FARM_BAD_STATE;
		CountDrFarmTime(*s, get_dword_time());
		if (!WriteDrFarmDirect(*s, DR_FARM_PAUSED, -1, 0))
			return DR_FARM_DB_ERROR;
		s->status = DR_FARM_PAUSED;
		RecountDrFarmActive();
		sys_log(0, "DR_FARM: pause pid=%u id=%lld active=%d", (unsigned)s->pid, s->id, s->activeSec);
		return DR_FARM_OK;
	}

	int ResumeDrFarm(LPCHARACTER ch)
	{
		TDrFarmSession* s = FindDrFarmSession(ch->GetPlayerID());
		if (!s)
			return DR_FARM_NONE;
		if (s->status != DR_FARM_PAUSED)
			return DR_FARM_BAD_STATE;
		if (!WriteDrFarmDirect(*s, DR_FARM_RUNNING, -1, 0))
			return DR_FARM_DB_ERROR;
		s->status = DR_FARM_RUNNING;
		s->lastMs = get_dword_time();
		s->restMs = 0;
		RecountDrFarmActive();
		EnsureDrFarmTick();
		sys_log(0, "DR_FARM: resume pid=%u id=%lld active=%d", (unsigned)s->pid, s->id, s->activeSec);
		return DR_FARM_OK;
	}

	int EndDrFarm(LPCHARACTER ch)
	{
		TDrFarmSession* s = FindDrFarmSession(ch->GetPlayerID());
		if (!s)
			return DR_FARM_NONE;
		CountDrFarmTime(*s, get_dword_time());
		if (!FinishDrFarmSession(*s, DR_FARM_END_MANUAL))
			return DR_FARM_DB_ERROR;
		s_mapDrFarmSessions.erase(ch->GetPlayerID());
		RecountDrFarmActive();
		return DR_FARM_OK;
	}

	// ---------------------------------------------------------------------
	// The snapshot of the items ("pelne", "stan"): memory only. The history
	// ("historia") and the statistics ("stat"): SQL totals over the player's
	// rows (player_id), the open session written first. They are built whole
	// before anything is sent, so a database error sends FarmResult 5 only.
	// ---------------------------------------------------------------------

	// Appends to a buffer of CHAT_MAX_LEN + 1 bytes; false (the buffer ends at
	// len) when the line would pass DR_FARM_LINE_MAX.
	bool AppendDrFarmLine(char* line, int& len, const char* format, ...)
	{
		va_list args;
		va_start(args, format);
		const int n = vsnprintf(line + len, CHAT_MAX_LEN + 1 - len, format, args);
		va_end(args);
		if (n < 0 || len + n > DR_FARM_LINE_MAX)
		{
			line[len] = '\0';
			return false;
		}
		len += n;
		return true;
	}

	// The item rows of s newer than sinceGen (0: all), FarmItems by source and
	// DR_FARM_ITEMS_PER_LINE to a line, then FarmDone.
	void SendDrFarmItems(LPCHARACTER ch, const TDrFarmSession& s, DWORD sinceGen)
	{
		struct TOut
		{
			DWORD vnum;
			int cnt;
			DWORD lastAt;
		};
		std::vector<TOut> out[DR_FARM_SRC_COUNT];
		for (TDrFarmItemMap::const_iterator it = s.drops.begin(); it != s.drops.end(); ++it)
		{
			if (it->second.gen <= sinceGen || it->first.second >= DR_FARM_SRC_COUNT)
				continue;
			const TOut row = { it->first.first, it->second.cnt, it->second.lastAt };
			out[it->first.second].push_back(row);
		}
		for (int src = 0; src < DR_FARM_SRC_COUNT; ++src)
		{
			const std::vector<TOut>& rows = out[src];
			for (size_t i = 0; i < rows.size(); i += DR_FARM_ITEMS_PER_LINE)
			{
				const size_t n = std::min<size_t>(DR_FARM_ITEMS_PER_LINE, rows.size() - i);
				char line[CHAT_MAX_LEN + 1];
				int len = snprintf(line, sizeof(line), "FarmItems %d %u", src, (unsigned)n);
				for (size_t j = i; j < i + n; ++j)
					if (!AppendDrFarmLine(line, len, " %u:%d:%u", (unsigned)rows[j].vnum, rows[j].cnt, (unsigned)rows[j].lastAt))
						break;
				SendDrFarmCommand(ch, "%s", line);
			}
		}
		// MT2009_PLUS_FARM_SESSION_V1 (spark): the items of the last active minutes, then the end.
		const int minute = s.activeSec / 60;
		char line[CHAT_MAX_LEN + 1];
		int len = snprintf(line, sizeof(line), "FarmSpark %d %d", minute, DR_FARM_SPARK_MINUTES);
		for (int m = minute - DR_FARM_SPARK_MINUTES + 1; m <= minute; ++m)
		{
			std::map<int, int>::const_iterator it = s.spark.find(m);
			if (!AppendDrFarmLine(line, len, " %d", it == s.spark.end() ? 0 : it->second))
				break;
		}
		SendDrFarmCommand(ch, "%s", line);
		SendDrFarmCommand(ch, "FarmDone");
	}

	// "pelne": FarmInfo and every row of the session (FarmDone even when it has
	// none). "stan": FarmInfo, and the rows that changed since the last FarmItems
	// only when there are some (memory only, no SQL).
	void AnswerDrFarmSnapshot(LPCHARACTER ch, bool full)
	{
		TDrFarmSession* s = FindDrFarmSession(ch->GetPlayerID());
		if (s)
			CountDrFarmTime(*s, get_dword_time());
		SendDrFarmInfo(ch, s);
		if (!s)
		{
			if (full)
				SendDrFarmCommand(ch, "FarmDone");
			return;
		}
		if (!full && s->itemGen == s->sentGen)
			return;
		SendDrFarmItems(ch, *s, full ? 0 : s->sentGen);
		s->sentGen = s->itemGen;
	}

	// The open session's counters and rows into the table, so that the totals
	// include it. False when the table refused.
	bool FlushDrFarmForRead(TDrFarmSession* s)
	{
		if (!s)
			return true;
		CountDrFarmTime(*s, get_dword_time());
		return !s->dirty || WriteDrFarmDirect(*s, -1, -1, 0);
	}

	void PushDrFarmLine(std::vector<std::string>& lines, const char* format, ...)
	{
		char text[CHAT_MAX_LEN + 1];
		va_list args;
		va_start(args, format);
		const int len = vsnprintf(text, sizeof(text), format, args);
		va_end(args);
		if (len < 0 || len > DR_FARM_LINE_MAX)
		{
			sys_err("DR_FARM: a line is too long (%d)", len);
			return;
		}
		lines.push_back(text);
	}

	// Runs a SELECT; false (and a log line) when the database refused it.
	bool DrFarmSelect(const char* what, const char* query, std::unique_ptr<SQLMsg>& msg)
	{
		msg = AccountDB::instance().DirectQuery(query);
		if (!DrFarmSqlOk(msg) || !msg->Get()->pSQLResult)
		{
			sys_err("DR_FARM: %s cannot be read errno=%u", what, msg.get() ? msg->uiSQLErrno : 0U);
			return false;
		}
		return true;
	}

	long long DrFarmNum(MYSQL_ROW row, int column)
	{
		long long value = 0;
		if (row[column])
			str_to_number(value, row[column]);
		return value;
	}

	// The start of the server's local day that holds t.
	DWORD DrFarmDayStart(time_t t)
	{
		struct tm local;
		localtime_r(&t, &local);
		local.tm_hour = 0;
		local.tm_min = 0;
		local.tm_sec = 0;
		local.tm_isdst = -1;
		return (DWORD)mktime(&local);
	}

	// FarmHist: the newest ended sessions (status 2), one line each, then FarmHistEnd.
	bool BuildDrFarmHistory(DWORD pid, std::vector<std::string>& lines)
	{
		char query[512];
		snprintf(query, sizeof(query),
				"SELECT id, started_at, active_sec, yang_m+yang_s+yang_b, items_m+items_s+items_b, "
				"kills_m+kills_s+kills_b, exp, end_reason FROM player.dr_farm_session "
				"WHERE player_id=%u AND status=2 ORDER BY id DESC LIMIT %d",
				(unsigned)pid, DR_FARM_HIST_SEND);
		std::unique_ptr<SQLMsg> msg;
		if (!DrFarmSelect("the history", query, msg))
			return false;
		MYSQL_ROW row;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
			PushDrFarmLine(lines, "FarmHist %lld %lld %lld %lld %lld %lld %lld %lld",
					DrFarmNum(row, 0), DrFarmNum(row, 1), DrFarmNum(row, 2), DrFarmNum(row, 3),
					DrFarmNum(row, 4), DrFarmNum(row, 5), DrFarmNum(row, 6), DrFarmNum(row, 7));
		PushDrFarmLine(lines, "FarmHistEnd");
		return true;
	}

	// "<word> <n> <a>:<b> ..." from the rows of a query (first column the id,
	// second the total); the query takes the player id and the row limit.
	bool BuildDrFarmTopLine(DWORD pid, const char* what, const char* word, const char* queryFormat, std::vector<std::string>& lines)
	{
		char query[768];
		snprintf(query, sizeof(query), queryFormat, (unsigned)pid, DR_FARM_TOP_LINE);
		std::unique_ptr<SQLMsg> msg;
		if (!DrFarmSelect(what, query, msg))
			return false;
		char entries[CHAT_MAX_LEN + 1] = "";
		int len = 0;
		int n = 0;
		MYSQL_ROW row;
		while (n < DR_FARM_TOP_LINE && NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			if (!AppendDrFarmLine(entries, len, " %u:%lld", (unsigned)DrFarmNum(row, 0), DrFarmNum(row, 1)))
				break;
			++n;
		}
		PushDrFarmLine(lines, "%s %d%s", word, n, entries);
		return true;
	}

	// FarmStatSum, FarmStatPer, FarmStatRec, FarmStatCat, FarmStatTop, FarmStatMob,
	// FarmStatMap (one or more lines), FarmStatEnd. Every session of the player in
	// the table counts: the open one (status 0 or 1; it is the current session,
	// whether or not the player is in the game) and the ended ones.
	bool BuildDrFarmStats(DWORD pid, std::vector<std::string>& lines)
	{
		char query[1024];
		std::unique_ptr<SQLMsg> msg;
		MYSQL_ROW row;

		snprintf(query, sizeof(query),
				"SELECT COUNT(*), COALESCE(SUM(active_sec),0), COALESCE(SUM(exp),0), "
				"COALESCE(SUM(yang_m),0), COALESCE(SUM(yang_s),0), COALESCE(SUM(yang_b),0), "
				"COALESCE(SUM(items_m),0), COALESCE(SUM(items_s),0), COALESCE(SUM(items_b),0), "
				"COALESCE(SUM(kills_m),0), COALESCE(SUM(kills_s),0), COALESCE(SUM(kills_b),0) "
				"FROM player.dr_farm_session WHERE player_id=%u", (unsigned)pid);
		if (!DrFarmSelect("the totals", query, msg) || !(row = mysql_fetch_row(msg->Get()->pSQLResult)))
			return false;
		PushDrFarmLine(lines, "FarmStatSum %lld %lld %lld %lld %lld %lld %lld %lld %lld %lld %lld %lld",
				DrFarmNum(row, 0), DrFarmNum(row, 1), DrFarmNum(row, 2), DrFarmNum(row, 3),
				DrFarmNum(row, 4), DrFarmNum(row, 5), DrFarmNum(row, 6), DrFarmNum(row, 7),
				DrFarmNum(row, 8), DrFarmNum(row, 9), DrFarmNum(row, 10), DrFarmNum(row, 11));

		// Today (from the server's local midnight) and the last 7 days, by started_at.
		const DWORD now = (DWORD)get_global_time();
		const DWORD since[2] = { DrFarmDayStart((time_t)now), now - 7 * 86400 };
		long long period[4] = { 0, 0, 0, 0 };
		for (int i = 0; i < 2; ++i)
		{
			snprintf(query, sizeof(query),
					"SELECT COUNT(*), COALESCE(SUM(yang_m+yang_s+yang_b),0) FROM player.dr_farm_session "
					"WHERE player_id=%u AND started_at>=%u", (unsigned)pid, (unsigned)since[i]);
			if (!DrFarmSelect("the period", query, msg) || !(row = mysql_fetch_row(msg->Get()->pSQLResult)))
				return false;
			period[2 * i] = DrFarmNum(row, 0);
			period[2 * i + 1] = DrFarmNum(row, 1);
		}
		PushDrFarmLine(lines, "FarmStatPer %lld %lld %lld %lld", period[0], period[1], period[2], period[3]);

		// The records: the best session by an expression (> 0) and when it began.
		// Yang per hour only counts a session of 10 minutes or more; the cast keeps
		// the product out of BIGINT's range.
		static const struct
		{
			const char* value;
			const char* where;
		} records[4] =
		{
			{ "yang_m+yang_s+yang_b", "1" },
			{ "CAST(yang_m+yang_s+yang_b AS DECIMAL(30,0))*3600 DIV active_sec", "active_sec>=600" },
			{ "active_sec", "1" },
			{ "kills_m+kills_s+kills_b", "1" }
		};
		long long record[8] = { 0, 0, 0, 0, 0, 0, 0, 0 };
		for (int i = 0; i < 4; ++i)
		{
			snprintf(query, sizeof(query),
					"SELECT %s AS v, started_at FROM player.dr_farm_session WHERE player_id=%u AND %s AND %s>0 "
					"ORDER BY v DESC, started_at DESC LIMIT 1",
					records[i].value, (unsigned)pid, records[i].where, records[i].value);
			if (!DrFarmSelect("the records", query, msg))
				return false;
			if (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
			{
				record[2 * i] = DrFarmNum(row, 0);
				record[2 * i + 1] = DrFarmNum(row, 1);
			}
		}
		PushDrFarmLine(lines, "FarmStatRec %lld %lld %lld %lld %lld %lld %lld %lld",
				record[0], record[1], record[2], record[3], record[4], record[5], record[6], record[7]);

		// The items by category (the six of DrFarmCategoryOf).
		long long category[6] = { 0, 0, 0, 0, 0, 0 };
		snprintf(query, sizeof(query),
				"SELECT i.cat, COALESCE(SUM(i.cnt),0) FROM player.dr_farm_item i "
				"JOIN player.dr_farm_session s ON s.id=i.session_id WHERE s.player_id=%u GROUP BY i.cat", (unsigned)pid);
		if (!DrFarmSelect("the categories", query, msg))
			return false;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			const long long cat = DrFarmNum(row, 0);
			if (cat >= 0 && cat < 6)
				category[cat] += DrFarmNum(row, 1);
		}
		PushDrFarmLine(lines, "FarmStatCat %lld %lld %lld %lld %lld %lld",
				category[0], category[1], category[2], category[3], category[4], category[5]);

		if (!BuildDrFarmTopLine(pid, "the top items", "FarmStatTop",
				"SELECT i.vnum, SUM(i.cnt) AS c FROM player.dr_farm_item i "
				"JOIN player.dr_farm_session s ON s.id=i.session_id WHERE s.player_id=%u "
				"GROUP BY i.vnum ORDER BY c DESC, i.vnum LIMIT %d", lines))
			return false;
		if (!BuildDrFarmTopLine(pid, "the top monsters", "FarmStatMob",
				"SELECT m.mob_vnum, SUM(m.kills) AS c FROM player.dr_farm_mob m "
				"JOIN player.dr_farm_session s ON s.id=m.session_id WHERE s.player_id=%u "
				"GROUP BY m.mob_vnum ORDER BY c DESC, m.mob_vnum LIMIT %d", lines))
			return false;

		// Every map, DR_FARM_MAPS_PER_LINE a line (FarmStatMap 0 when there is none).
		struct TMapOut
		{
			int map;
			long long yang, items, kills;
		};
		std::vector<TMapOut> maps;
		snprintf(query, sizeof(query),
				"SELECT m.map_idx, SUM(m.yang), SUM(m.items), SUM(m.kills) FROM player.dr_farm_map m "
				"JOIN player.dr_farm_session s ON s.id=m.session_id WHERE s.player_id=%u "
				"GROUP BY m.map_idx ORDER BY SUM(m.kills) DESC, m.map_idx", (unsigned)pid);
		if (!DrFarmSelect("the maps", query, msg))
			return false;
		while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
		{
			const TMapOut out = { (int)DrFarmNum(row, 0), DrFarmNum(row, 1), DrFarmNum(row, 2), DrFarmNum(row, 3) };
			maps.push_back(out);
		}
		if (maps.empty())
			PushDrFarmLine(lines, "FarmStatMap 0");
		for (size_t i = 0; i < maps.size(); i += DR_FARM_MAPS_PER_LINE)
		{
			const size_t n = std::min<size_t>(DR_FARM_MAPS_PER_LINE, maps.size() - i);
			char entries[CHAT_MAX_LEN + 1] = "";
			int len = 0;
			for (size_t j = i; j < i + n; ++j)
				if (!AppendDrFarmLine(entries, len, " %d:%lld:%lld:%lld", maps[j].map, maps[j].yang, maps[j].items, maps[j].kills))
					break;
			PushDrFarmLine(lines, "FarmStatMap %u%s", (unsigned)n, entries);
		}

		// MT2009_PLUS_FARM_SESSION_V1 (all items): every item's total with its category, the most counted first,
		// DR_FARM_ALL_PER_LINE a line (the window's own categories take theirs out of the six). Nothing: no line.
		snprintf(query, sizeof(query),
				"SELECT i.vnum, MIN(i.cat), SUM(i.cnt) AS c FROM player.dr_farm_item i "
				"JOIN player.dr_farm_session s ON s.id=i.session_id WHERE s.player_id=%u "
				"GROUP BY i.vnum ORDER BY c DESC, i.vnum LIMIT %d", (unsigned)pid, DR_FARM_ALL_MAX);
		if (!DrFarmSelect("the items", query, msg))
			return false;
		{
			char entries[CHAT_MAX_LEN + 1] = "";
			int len = 0;
			int n = 0;
			while (NULL != (row = mysql_fetch_row(msg->Get()->pSQLResult)))
			{
				if (!AppendDrFarmLine(entries, len, " %u:%u:%lld", (unsigned)DrFarmNum(row, 0), (unsigned)DrFarmNum(row, 1),
						DrFarmNum(row, 2)))
					break;
				if (++n == DR_FARM_ALL_PER_LINE)
				{
					PushDrFarmLine(lines, "FarmStatAll %d%s", n, entries);
					entries[0] = '\0';
					len = 0;
					n = 0;
				}
			}
			if (n > 0)
				PushDrFarmLine(lines, "FarmStatAll %d%s", n, entries);
		}
		PushDrFarmLine(lines, "FarmStatEnd");
		return true;
	}

	// "historia" / "stat": FarmInfo, then the lines; the open session is written
	// first. A database error: FarmInfo and FarmResult 5, nothing else.
	void AnswerDrFarmRead(LPCHARACTER ch, bool history, bool tables)
	{
		const DWORD pid = ch->GetPlayerID();
		TDrFarmSession* s = FindDrFarmSession(pid);
		if (s)
			CountDrFarmTime(*s, get_dword_time());
		SendDrFarmInfo(ch, s);
		std::vector<std::string> lines;
		if (!tables || !FlushDrFarmForRead(s) || !(history ? BuildDrFarmHistory(pid, lines) : BuildDrFarmStats(pid, lines)))
		{
			SendDrFarmResult(ch, DR_FARM_DB_ERROR);
			return;
		}
		for (size_t i = 0; i < lines.size(); ++i)
			SendDrFarmCommand(ch, "%s", lines[i].c_str());
	}

	// ---------------------------------------------------------------------
	// The kills. Near the corpse: the reach of the party's experience
	// (NPartyExpDistribute::FPartyDistributor in char_battle.cpp: the same map
	// and PARTY_DEFAULT_RANGE from the victim; DistributeExp leaves out the
	// attackers farther than the same 5000).
	// ---------------------------------------------------------------------

	long DrFarmMapOf(long mapIndex)
	{
		return mapIndex >= 10000 ? mapIndex / 10000 : mapIndex;
	}

	bool DrFarmNearCorpse(LPCHARACTER victim, LPCHARACTER ch)
	{
		return ch->GetMapIndex() == victim->GetMapIndex() &&
			DISTANCE_APPROX(ch->GetX() - victim->GetX(), ch->GetY() - victim->GetY()) <= PARTY_DEFAULT_RANGE;
	}

	// ch's player id into pids: a human with a running session, once.
	void AddDrFarmKiller(std::vector<DWORD>& pids, LPCHARACTER victim, LPCHARACTER ch, bool nearOnly)
	{
		if (!DrFarmIsHuman(ch) || (nearOnly && !DrFarmNearCorpse(victim, ch)))
			return;
		const DWORD pid = ch->GetPlayerID();
		const TDrFarmSession* s = FindDrFarmSession(pid);
		if (!s || s->status != DR_FARM_RUNNING || std::find(pids.begin(), pids.end(), pid) != pids.end())
			return;
		pids.push_back(pid);
	}

	struct FDrFarmPartyKill
	{
		LPCHARACTER victim;
		std::vector<DWORD>* pids;
		void operator () (LPCHARACTER ch)
		{
			AddDrFarmKiller(*pids, victim, ch, true);
		}
	};

	// ---------------------------------------------------------------------
	// The drop and the yang: the tags of the items on the ground, the stack of
	// the scopes, the counting into a session.
	// ---------------------------------------------------------------------

	void FillDrFarmTag(TDrFarmTag& tag, const TDrFarmKillCtx& ctx)
	{
		tag.src = ctx.src;
		tag.mobVnum = ctx.mobVnum;
		tag.mapIdx = ctx.mapIdx;
		tag.expire = (DWORD)get_global_time() + DR_FARM_TAG_SEC;
		tag.n = 0;
		for (BYTE i = 0; i < ctx.count && i < DR_FARM_KILL_PIDS; ++i)
			tag.eligible[tag.n++] = ctx.pids[i];
	}

	bool DrFarmTagHas(const TDrFarmTag& tag, DWORD pid)
	{
		for (BYTE i = 0; i < tag.n; ++i)
			if (tag.eligible[i] == pid)
				return true;
		return false;
	}

	// The tag of vid (a new one, or the one it has); NULL when the map is full
	// even without the old tags.
	TDrFarmTag* NewDrFarmTag(DWORD vid)
	{
		if (s_mapDrFarmTags.size() >= DR_FARM_TAG_MAX && s_mapDrFarmTags.find(vid) == s_mapDrFarmTags.end())
		{
			PurgeDrFarmTags();
			if (s_mapDrFarmTags.size() >= DR_FARM_TAG_MAX)
			{
				const DWORD now = get_dword_time();
				if (s_dwDrFarmTagFullLog == 0 || now - s_dwDrFarmTagFullLog >= 60000)
				{
					s_dwDrFarmTagFullLog = now;
					sys_err("DR_FARM: %u drop tags, no room for more", (unsigned)s_mapDrFarmTags.size());
				}
				return NULL;
			}
		}
		return &s_mapDrFarmTags[vid];
	}

	void TagDrFarmItem(LPITEM item, const TDrFarmKillCtx& ctx)
	{
		if (!item || !item->GetVID())
			return;
		TDrFarmTag* tag = NewDrFarmTag(item->GetVID());
		if (tag)
			FillDrFarmTag(*tag, ctx);
	}

	// The innermost scope's context, NULL outside every scope.
	const TDrFarmTag* DrFarmScope()
	{
		return s_iDrFarmScopeDepth > 0 ? &s_aDrFarmScopes[s_iDrFarmScopeDepth - 1] : NULL;
	}

	// tag NULL or with no pids: nobody counts inside (an outer scope neither).
	bool PushDrFarmScope(const TDrFarmTag* tag)
	{
		if (s_iDrFarmScopeDepth >= DR_FARM_SCOPE_DEPTH)
		{
			sys_err("DR_FARM: the scopes are %d deep", s_iDrFarmScopeDepth);
			return false;
		}
		TDrFarmTag& top = s_aDrFarmScopes[s_iDrFarmScopeDepth++];
		if (tag)
			top = *tag;
		else
			top.n = 0;
		return true;
	}

	// The running session of ch when ch may count what tag stands for.
	TDrFarmSession* DrFarmCounter(LPCHARACTER ch, const TDrFarmTag& tag)
	{
		if (tag.n == 0 || !DrFarmIsHuman(ch))
			return NULL;
		const DWORD pid = ch->GetPlayerID();
		if (!DrFarmTagHas(tag, pid))
			return NULL;
		TDrFarmSession* s = FindDrFarmSession(pid);
		return s && s->status == DR_FARM_RUNNING ? s : NULL;
	}

	void CountDrFarmItem(TDrFarmSession& s, const TDrFarmTag& tag, DWORD vnum, DWORD count)
	{
		if (count == 0 || tag.src >= DR_FARM_SRC_COUNT)
			return;
		s.items[tag.src] += (int)count;
		TDrFarmItemRow& row = s.drops[std::make_pair(vnum, tag.src)];
		row.cat = DrFarmCategoryOf(vnum);
		row.cnt += (int)count;
		row.lastAt = (DWORD)get_global_time();
		row.dirty = true;
		row.gen = ++s.itemGen;
		TDrFarmMapRow& map = s.maps[tag.mapIdx];
		map.items += (int)count;
		map.dirty = true;
		s.dirty = true;
		// MT2009_PLUS_FARM_SESSION_V1 (spark): the active minute's items; the minutes FarmSpark no longer sends go.
		const int minute = s.activeSec / 60;
		s.spark[minute] += (int)count;
		while (!s.spark.empty() && s.spark.begin()->first <= minute - DR_FARM_SPARK_MINUTES)
			s.spark.erase(s.spark.begin());
#ifdef DR_FARM_DEBUG
		sys_log(0, "DR_FARM: item pid=%u vnum=%u count=%u src=%d cat=%d map=%ld",
				(unsigned)s.pid, (unsigned)vnum, (unsigned)count, (int)tag.src, (int)row.cat, tag.mapIdx);
#endif
	}
}

bool DrFarmIsHuman(LPCHARACTER ch)
{
	// MT2009_PLUS_FARM_SESSION_V1 (bots): a bot's descriptor or a registered bot's player id never counts.
	return ch && ch->IsPC() && ch->GetDesc() && !ch->GetDesc()->IsBot() &&
		!CPlayerBotManager::instance().IsRegisteredBotPID(ch->GetPlayerID());
}

void DrFarmInit()
{
	if (g_bAuthServer)
		return;
	if (EnsureDrFarmTables() || s_pkDrFarmInit)
		return;
	dr_farm_init_info* info = AllocEventInfo<dr_farm_init_info>();
	s_pkDrFarmInit = event_create(dr_farm_init_event, info, PASSES_PER_SEC(10));
}

void DrFarmCommand(LPCHARACTER ch, const char* argument)
{
	if (!DrFarmIsHuman(ch))
		return;
	if (!argument)
		argument = "";
	char word[32];
	const char* args = one_argument(argument, word, sizeof(word));
#ifdef DR_FARM_DEBUG
	sys_log(0, "DR_FARM: command from=%s '%s'", ch->GetName(), argument);
#endif
	const bool cmdInfo = !strcasecmp(word, "stan");
	const bool cmdFull = !strcasecmp(word, "pelne");
	const bool cmdHistory = !strcasecmp(word, "historia");
	const bool cmdStat = !strcasecmp(word, "stat");
	const bool cmdStart = !strcasecmp(word, "start");
	const bool cmdPause = !strcasecmp(word, "pauza");
	const bool cmdResume = !strcasecmp(word, "wznow");
	const bool cmdEnd = !strcasecmp(word, "koniec");
	if (!cmdInfo && !cmdFull && !cmdHistory && !cmdStat && !cmdStart && !cmdPause && !cmdResume && !cmdEnd)
		return;

	// The snapshots come from memory (the window asks "stan" every 5 s): no SQL.
	if (cmdInfo || cmdFull)
	{
		AnswerDrFarmSnapshot(ch, cmdFull);
		return;
	}
	if (cmdHistory || cmdStat)
	{
		AnswerDrFarmRead(ch, cmdHistory, EnsureDrFarmTables());
		return;
	}

	int result = DR_FARM_DB_ERROR;
	if (EnsureDrFarmTables())
	{
		if (cmdStart)
			result = StartDrFarm(ch, args);
		else if (cmdPause)
			result = PauseDrFarm(ch);
		else if (cmdResume)
			result = ResumeDrFarm(ch);
		else
			result = EndDrFarm(ch);
	}

	TDrFarmSession* s = FindDrFarmSession(ch->GetPlayerID());
	if (s)
		CountDrFarmTime(*s, get_dword_time());
	SendDrFarmInfo(ch, s);
	SendDrFarmResult(ch, result);
}

void DrFarmOnEnterGame(LPCHARACTER ch)
{
	if (!DrFarmIsHuman(ch) || !EnsureDrFarmTables())
		return;
	const DWORD pid = ch->GetPlayerID();
	int adopted = DR_FARM_ADOPT_NONE;
	if (!FindDrFarmSession(pid))
	{
		adopted = AdoptDrFarmSession(pid);
		if (adopted == DR_FARM_ADOPT_ERROR)
			return;
	}
	SendDrFarmInfo(ch, FindDrFarmSession(pid));
	// The limit passed while the player was away: the session ended just now.
	if (adopted == DR_FARM_ADOPT_ENDED)
		SendDrFarmResult(ch, DR_FARM_LIMIT_ENDED);
}

void DrFarmOnDisconnect(LPCHARACTER ch)
{
	if (!ch || s_mapDrFarmSessions.empty())
		return;
	TDrFarmSessionMap::iterator it = s_mapDrFarmSessions.find(ch->GetPlayerID());
	if (it == s_mapDrFarmSessions.end())
		return;
	TDrFarmSession& s = it->second;
	CountDrFarmTime(s, get_dword_time());
	// The limit passed while the player was here: it ends now. Otherwise the
	// row keeps the player's state (see the top) and the time stops.
	if (s.status == DR_FARM_RUNNING && DrFarmLimitReached(s))
	{
		if (!FinishDrFarmSession(s, DR_FARM_END_LIMIT))
			WriteDrFarmAsync(s, true);
	}
	else if (!WriteDrFarmDirect(s, s.status, -1, 0))
		WriteDrFarmAsync(s, true);
	sys_log(0, "DR_FARM: leave pid=%u id=%lld status=%d active=%d", (unsigned)s.pid, s.id, (int)s.status, s.activeSec);
	s_mapDrFarmSessions.erase(it);
	RecountDrFarmActive();
}

BYTE DrFarmSourceOf(LPCHARACTER victim)
{
	if (!victim)
		return DR_FARM_SRC_MOB;
	if (victim->IsStone())
		return DR_FARM_SRC_STONE;
	if (victim->GetMobRank() >= MOB_RANK_BOSS || IsMiniBoss(victim->GetRaceNum()))
		return DR_FARM_SRC_BOSS;
	return DR_FARM_SRC_MOB;
}

void DrFarmOnKill(LPCHARACTER victim, LPCHARACTER killer, const std::vector<LPCHARACTER>& hurt)
{
	if (!g_iDrFarmActive || !victim)
		return;
	std::vector<DWORD> pids;
	AddDrFarmKiller(pids, victim, killer, false);
	if (killer && killer->GetParty())
	{
		FDrFarmPartyKill party = { victim, &pids };
		killer->GetParty()->ForEachOnlineMember(party);
	}
	for (size_t i = 0; i < hurt.size(); ++i)
		AddDrFarmKiller(pids, victim, hurt[i], true);

	const DWORD vid = (DWORD)victim->GetVID();
	const BYTE src = DrFarmSourceOf(victim);
	const DWORD vnum = victim->GetRaceNum();
	const long mapIdx = DrFarmMapOf(victim->GetMapIndex());
	s_kDrFarmKill.victimVid = vid;
	s_kDrFarmKill.src = src;
	s_kDrFarmKill.mobVnum = vnum;
	s_kDrFarmKill.mapIdx = mapIdx;
	s_kDrFarmKill.count = 0;
	for (size_t i = 0; i < pids.size() && s_kDrFarmKill.count < DR_FARM_KILL_PIDS; ++i)
		s_kDrFarmKill.pids[s_kDrFarmKill.count++] = pids[i];

	int counted = 0;
	for (size_t i = 0; i < pids.size(); ++i)
	{
		TDrFarmSession* s = FindDrFarmSession(pids[i]);
		if (!s || s->lastKillVid == vid)
			continue;
		s->lastKillVid = vid;
		++s->kills[src];
		TDrFarmMobRow& mob = s->mobs[vnum];
		mob.src = src;
		++mob.kills;
		mob.dirty = true;
		TDrFarmMapRow& map = s->maps[mapIdx];
		++map.kills;
		map.dirty = true;
		s->dirty = true;
		++counted;
	}
#ifdef DR_FARM_DEBUG
	sys_log(0, "DR_FARM: kill vid=%u vnum=%u src=%d map=%ld eligible=%u counted=%d",
			(unsigned)vid, (unsigned)vnum, (int)src, mapIdx, (unsigned)pids.size(), counted);
#else
	(void)counted;
#endif
}

void DrFarmOnExp(LPCHARACTER to, int iExp)
{
	if (!g_iDrFarmActive || iExp <= 0 || !DrFarmIsHuman(to))
		return;
	TDrFarmSession* s = FindDrFarmSession(to->GetPlayerID());
	// PointChange gives nothing to a character that blocked its experience.
	if (!s || s->status != DR_FARM_RUNNING || to->FindAffect(AFFECT_EXP_BLOCK))
		return;
	s->exp += iExp;
	s->dirty = true;
}

const TDrFarmKillCtx* DrFarmLastKill(DWORD dwVictimVID)
{
	if (s_kDrFarmKill.victimVid != dwVictimVID || s_kDrFarmKill.count == 0)
		return NULL;
	return &s_kDrFarmKill;
}

void DrFarmTagDrops(LPCHARACTER victim, LPCHARACTER killer, const std::vector<LPITEM>& items)
{
	if (!g_iDrFarmActive || !victim || items.empty())
		return;
	(void)killer;
	const TDrFarmKillCtx* ctx = DrFarmLastKill((DWORD)victim->GetVID());
	if (!ctx)
		return;
	for (size_t i = 0; i < items.size(); ++i)
		TagDrFarmItem(items[i], *ctx);
#ifdef DR_FARM_DEBUG
	sys_log(0, "DR_FARM: drop vid=%u items=%u tags=%u", (unsigned)ctx->victimVid, (unsigned)items.size(),
			(unsigned)s_mapDrFarmTags.size());
#endif
}

void DrFarmTagGroundYang(LPITEM item, LPCHARACTER victim, LPCHARACTER killer)
{
	if (!g_iDrFarmActive || !item || !victim)
		return;
	(void)killer;
	const TDrFarmKillCtx* ctx = DrFarmLastKill((DWORD)victim->GetVID());
	if (ctx)
		TagDrFarmItem(item, *ctx);
}

void DrFarmTagOwner(DWORD dwItemVID, DWORD dwPID)
{
	if (!g_iDrFarmActive || !dwItemVID || !dwPID)
		return;
	TDrFarmTag* tag = NULL;
	TDrFarmTagMap::iterator it = s_mapDrFarmTags.find(dwItemVID);
	if (it != s_mapDrFarmTags.end())
		tag = &it->second;
	else
	{
		// An item a kill's reward made and gave an owner (inside the kill's scope).
		const TDrFarmTag* scope = DrFarmScope();
		if (!scope || scope->n == 0 || !(tag = NewDrFarmTag(dwItemVID)))
			return;
		*tag = *scope;
		tag->expire = (DWORD)get_global_time() + DR_FARM_TAG_SEC;
	}
	if (!DrFarmTagHas(*tag, dwPID) && tag->n < DR_FARM_KILL_PIDS)
		tag->eligible[tag->n++] = dwPID;
}

TDrFarmPick DrFarmPickBegin(LPITEM item)
{
	TDrFarmPick pick = { 0, 0, 0, false };
	if (!g_iDrFarmActive || !item || s_mapDrFarmTags.empty())
		return pick;
	TDrFarmTagMap::iterator it = s_mapDrFarmTags.find(item->GetVID());
	if (it == s_mapDrFarmTags.end())
		return pick;
	if (it->second.expire <= (DWORD)get_global_time())
	{
		s_mapDrFarmTags.erase(it);
		return pick;
	}
	pick.vid = item->GetVID();
	pick.vnum = item->GetVnum();
	pick.count = item->GetCount();
	pick.tagged = true;
	return pick;
}

void DrFarmPickDone(const TDrFarmPick& pick, LPCHARACTER receiver)
{
	if (!pick.tagged)
		return;
	TDrFarmTagMap::iterator it = s_mapDrFarmTags.find(pick.vid);
	if (it == s_mapDrFarmTags.end())
		return;
	const TDrFarmTag tag = it->second;
	s_mapDrFarmTags.erase(it);
	if (!g_iDrFarmActive)
		return;
	// The yang counts in its pick-up's DrFarmKillScope, never as an item.
	const TItemTable* proto = ITEM_MANAGER::instance().GetTable(pick.vnum);
	if (proto && proto->bType == ITEM_ELK)
		return;
	TDrFarmSession* s = DrFarmCounter(receiver, tag);
	if (s)
		CountDrFarmItem(*s, tag, pick.vnum, pick.count);
#ifdef DR_FARM_DEBUG
	else
		sys_log(0, "DR_FARM: pick vid=%u vnum=%u by=%s not counted", (unsigned)pick.vid, (unsigned)pick.vnum,
				receiver ? receiver->GetName() : "-");
#endif
}

DrFarmKillScope::DrFarmKillScope(LPCHARACTER victim, LPCHARACTER killer) : m_bPushed(false)
{
	if (!g_iDrFarmActive)
		return;
	(void)killer;
	const TDrFarmKillCtx* ctx = victim ? DrFarmLastKill((DWORD)victim->GetVID()) : NULL;
	TDrFarmTag tag = {};
	if (ctx)
		FillDrFarmTag(tag, *ctx);
	m_bPushed = PushDrFarmScope(&tag);
}

DrFarmKillScope::DrFarmKillScope(const TDrFarmPick& pick) : m_bPushed(false)
{
	if (!g_iDrFarmActive)
		return;
	TDrFarmTag tag = {};
	if (pick.tagged)
	{
		// The picked-up yang's tag is used up here.
		TDrFarmTagMap::iterator it = s_mapDrFarmTags.find(pick.vid);
		if (it != s_mapDrFarmTags.end())
		{
			tag = it->second;
			s_mapDrFarmTags.erase(it);
		}
	}
	m_bPushed = PushDrFarmScope(&tag);
}

DrFarmKillScope::~DrFarmKillScope()
{
	if (m_bPushed && s_iDrFarmScopeDepth > 0)
		--s_iDrFarmScopeDepth;
}

void DrFarmOnYang(LPCHARACTER ch, long long llAmount)
{
	if (!g_iDrFarmActive || llAmount <= 0)
		return;
	const TDrFarmTag* scope = DrFarmScope();
	if (!scope || scope->src >= DR_FARM_SRC_COUNT)
		return;
	TDrFarmSession* s = DrFarmCounter(ch, *scope);
	if (!s)
		return;
	s->yang[scope->src] += llAmount;
	s->yangLastAt = (DWORD)get_global_time();	// MT2009_PLUS_FARM_SESSION_V1 (yang last)
	TDrFarmMapRow& map = s->maps[scope->mapIdx];
	map.yang += llAmount;
	map.dirty = true;
	s->dirty = true;
#ifdef DR_FARM_DEBUG
	sys_log(0, "DR_FARM: yang pid=%u amount=%lld src=%d map=%ld", (unsigned)s->pid, llAmount, (int)scope->src, scope->mapIdx);
#endif
}

void DrFarmOnAutoGive(LPCHARACTER ch, DWORD dwVnum, DWORD dwCount)
{
	if (!g_iDrFarmActive)
		return;
	const TDrFarmTag* scope = DrFarmScope();
	if (!scope)
		return;
	TDrFarmSession* s = DrFarmCounter(ch, *scope);
	if (s)
		CountDrFarmItem(*s, *scope, dwVnum, dwCount);
}

BYTE DrFarmCategoryOf(DWORD vnum)
{
	const TItemTable* proto = ITEM_MANAGER::instance().GetTable(vnum);
	if (!proto)
		return DR_FARM_CAT_OTHER;
	switch (proto->bType)
	{
		case ITEM_MATERIAL:
		case ITEM_METIN:
		case ITEM_RESOURCE:
			return DR_FARM_CAT_MATERIAL;
		case ITEM_USE:
		case ITEM_AUTOUSE:
		case ITEM_POTION:
		case ITEM_BLEND:
		case ITEM_SKILLBOOK:
		case ITEM_SKILLFORGET:
		case ITEM_GIFTBOX:
			return DR_FARM_CAT_USE;
		case ITEM_WEAPON:
			return DR_FARM_CAT_WEAPON;
		case ITEM_ARMOR:
			switch (proto->bSubType)
			{
				case ARMOR_BODY:
				case ARMOR_HEAD:
				case ARMOR_SHIELD:
				case ARMOR_FOOTS:
					return DR_FARM_CAT_ARMOR;
				default:	// wrist, neck, ear and the rest (as Mt2009PlusPickupKindOf)
					return DR_FARM_CAT_JEWEL;
			}
		case ITEM_RING:
		case ITEM_BELT:
			return DR_FARM_CAT_JEWEL;
		default:
			return DR_FARM_CAT_OTHER;
	}
}

#endif // DR_FARM_SESSION_V1
