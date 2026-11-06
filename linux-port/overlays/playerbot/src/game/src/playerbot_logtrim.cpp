// MT2009_PLUS_BOT_LOG_TRIM_V1 - the bots' rows in the log database (the owner, 6 November 2026, second-pass bot
// analysis #1: "log DB: no per-pickup GET_GOLD and no SOCKET_*/ATTR_FORCE item_meta_log rows for BOTS (hourly
// aggregate counter instead)"). On the supporters' server log.log had grown to 25 GB / 199 million rows, 57-83% of
// them a bot picking up yang (GET_GOLD, one row a pickup over 1000 yang), and item_meta_log to 9.8 GB, mostly
// SOCKET_FISHING / SOCKET_WEAR / ATTR_FORCE rows of bots' items.
//
// server-patches/logtrim hooks log.cpp:
//   * LogManager::CharLog(ch, ...) asks Mt2009BotLogTrimGold first: a playerbot's GET_GOLD is not written - it is
//     added to this core's counter instead, and once an hour the counter goes out as ONE log.log row:
//       type CHARACTER, who 0, how GET_GOLD, what <the hour's yang of every bot>, ip "playerbot",
//       hint "BOTS_HOURLY picks=<n> bots=<distinct bots> ch=<channel> port=<core port>"
//     so SUM(what) WHERE how='GET_GOLD' (the Seban panel's yang event, collector "yang_extra") still counts the
//     bots' yang - an hour's grain instead of a row a pickup. A player's GET_GOLD is written as before.
//   * LogManager::ItemSocketLog (SOCKET, SOCKET_WEAR, SOCKET_FISHING, SOCKET_UNIQUE...) and ItemAttrLog's
//     ATTR_FORCE ask Mt2009BotLogTrimMeta: a playerbot's row is not written to item_meta_log (only counted for the
//     hourly syslog line). Players' rows, and the bots' other item_meta_log rows (CHANGE_ATTR, ADD_ATTR), stay.
// Switch: event flag m2_bot_log_rows_on = 1 writes the bots' rows as before (default 0 = trimmed); read every 30 s.
// Log: "BOT_LOGTRIM: hour gold=<yang> picks=<n> bots=<n> meta_socket_skipped=<n> meta_attr_skipped=<n>" once an hour
// (with the aggregate row), and "BOT_LOGTRIM: switch rows_on=<0|1>" when the flag changes.
// The counter of the running hour is lost if the core stops before the hour is up (at most an hour of bots' yang
// missing from the sum); it is flushed by the next bot's pickup after the hour, not by a clock.
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "log.h"
#include "questmanager.h"

#include <cstring>
#include <ctime>
#include <set>

namespace
{
	const DWORD MT2009_BOT_LOG_TRIM_FLAG_MS = 30000;
	const time_t MT2009_BOT_LOG_TRIM_FLUSH_S = 3600;
	const char* const MT2009_BOT_LOG_TRIM_FLAG = "m2_bot_log_rows_on";

	struct TBotLogTrim
	{
		bool bTrim;
		bool bFlagKnown;
		DWORD dwFlagAt;
		time_t tSince;
		long long llGold;
		DWORD dwPicks;
		DWORD dwSocket;
		DWORD dwAttr;
		std::set<DWORD> setBots;
		TBotLogTrim() : bTrim(true), bFlagKnown(false), dwFlagAt(0), tSince(0), llGold(0), dwPicks(0), dwSocket(0), dwAttr(0) {}
	};
	TBotLogTrim s_botLogTrim;

	bool IsBotLogTrimOn()
	{
		TBotLogTrim& t = s_botLogTrim;
		const DWORD dwNow = get_dword_time();
		if (!t.bFlagKnown || dwNow - t.dwFlagAt >= MT2009_BOT_LOG_TRIM_FLAG_MS)
		{
			const bool trim = quest::CQuestManager::instance().GetEventFlag(MT2009_BOT_LOG_TRIM_FLAG) == 0;
			if (t.bFlagKnown && trim != t.bTrim)
				sys_log(0, "BOT_LOGTRIM: switch rows_on=%d", trim ? 0 : 1);
			t.bTrim = trim;
			t.bFlagKnown = true;
			t.dwFlagAt = dwNow;
		}
		return t.bTrim;
	}

	bool IsBotLogChar(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && ch->GetDesc()->IsBot();
	}

	// Once an hour: the aggregate row and the syslog line. Called from the hooks (a bot's pickup or meta row).
	void FlushBotLogTrim(bool force)
	{
		TBotLogTrim& t = s_botLogTrim;
		const time_t now = time(0);
		if (t.tSince == 0)
		{
			t.tSince = now;
			return;
		}
		if (!force && now - t.tSince < MT2009_BOT_LOG_TRIM_FLUSH_S)
			return;
		if (t.dwPicks > 0)
		{
			char hint[128];
			snprintf(hint, sizeof(hint), "BOTS_HOURLY picks=%u bots=%u ch=%u port=%u", t.dwPicks,
					(unsigned int)t.setBots.size(), (unsigned int)g_bChannel, (unsigned int)mother_port);
			LogManager::instance().CharLog(0, 0, 0, t.llGold, "GET_GOLD", hint, "playerbot");
		}
		sys_log(0, "BOT_LOGTRIM: hour gold=%lld picks=%u bots=%u meta_socket_skipped=%u meta_attr_skipped=%u span_s=%ld",
				t.llGold, t.dwPicks, (unsigned int)t.setBots.size(), t.dwSocket, t.dwAttr, (long)(now - t.tSince));
		t.tSince = now;
		t.llGold = 0;
		t.dwPicks = 0;
		t.dwSocket = 0;
		t.dwAttr = 0;
		t.setBots.clear();
	}
}

// log.cpp LogManager::CharLog(LPCHARACTER, ...): true = counted here, the row is not written.
bool Mt2009BotLogTrimGold(LPCHARACTER ch, long long amount, const char* how)
{
	if (!how || strcmp(how, "GET_GOLD") != 0 || !IsBotLogChar(ch) || !IsBotLogTrimOn())
		return false;
	TBotLogTrim& t = s_botLogTrim;
	FlushBotLogTrim(false);
	t.llGold += amount;
	++t.dwPicks;
	t.setBots.insert(ch->GetPlayerID());
	return true;
}

// log.cpp LogManager::ItemSocketLog / ItemAttrLog: true = a bot's SOCKET* / ATTR_FORCE row, not written.
bool Mt2009BotLogTrimMeta(DWORD pid, const char* what)
{
	if (!pid || !what)
		return false;
	const bool socket = strncmp(what, "SOCKET", 6) == 0;
	const bool attr = !socket && strcmp(what, "ATTR_FORCE") == 0;
	if (!socket && !attr)
		return false;
	if (!IsBotLogChar(CHARACTER_MANAGER::instance().FindByPID(pid)) || !IsBotLogTrimOn())
		return false;
	TBotLogTrim& t = s_botLogTrim;
	FlushBotLogTrim(false);
	if (socket)
		++t.dwSocket;
	else
		++t.dwAttr;
	return true;
}
