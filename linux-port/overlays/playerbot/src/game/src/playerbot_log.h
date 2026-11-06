#ifndef __INC_METIN2_PLAYERBOT_LOG_H__
#define __INC_METIN2_PLAYERBOT_LOG_H__

// Saying something once for three hundred bots.
//
// A message written from the tick is written by every bot on the map, four
// times a second. "This bot is too low for Orc Valley" is a decision working
// exactly as intended, and it had put ninety-one thousand SYSERR lines into one
// core's log - which is not a report, it is a way of making the real errors
// impossible to find.
//
// So: a tag, a minute, and a count. The first occurrence in each window is
// written in full and the rest are counted, and the next line to come through
// says how many were swallowed. Nothing is lost - the fact that it happened
// eleven thousand times is more useful than eleven thousand copies of it, and
// it is one line instead of eleven thousand.
//
// The manager already had this shape once, hand-rolled, for the spawn refusals.
// This is that idea with a name, so the next place that needs it does not grow
// its own.
//
// An implementation fragment in the sense playerbot_types.h describes: include
// it exactly once, early - anything may want to log.

namespace
{
	const DWORD PLAYERBOT_LOG_THROTTLE_WINDOW = 60000;

	struct TPlayerBotLogThrottle
	{
		DWORD dwSuppressed;
		DWORD dwNextTime;
		TPlayerBotLogThrottle() : dwSuppressed(0), dwNextTime(0) {}
	};

	// Keyed by whatever the caller decides one "kind" of message is. Make the
	// tag as specific as the thing worth hearing about separately: the travel
	// refusals are tagged by their reason, so a new reason still speaks up
	// within the minute instead of hiding behind an old one.
	std::map<std::string, TPlayerBotLogThrottle> s_mapPlayerBotLogThrottle;

	void PlayerBotLogThrottledV(bool bError, const char* szTag, DWORD dwNow,
			const char* szFormat, va_list args)
	{
		TPlayerBotLogThrottle& throttle = s_mapPlayerBotLogThrottle[szTag ? szTag : "?"];
		if (throttle.dwNextTime != 0 && dwNow < throttle.dwNextTime)
		{
			++throttle.dwSuppressed;
			return;
		}

		char body[512];
		vsnprintf(body, sizeof(body), szFormat, args);

		const DWORD dwSuppressed = throttle.dwSuppressed;
		throttle.dwSuppressed = 0;
		throttle.dwNextTime = dwNow + PLAYERBOT_LOG_THROTTLE_WINDOW;

		if (dwSuppressed == 0)
		{
			if (bError)
				sys_err("%s", body);
			else
				sys_log(0, "%s", body);
			return;
		}
		if (bError)
			sys_err("%s [+%u more in the last minute]", body, dwSuppressed);
		else
			sys_log(0, "%s [+%u more in the last minute]", body, dwSuppressed);
	}

	// Not an error: a decision, a state, something an operator may want to see
	// but that nothing is wrong about.
	void PlayerBotLogThrottled(const char* szTag, DWORD dwNow, const char* szFormat, ...)
	{
		va_list args;
		va_start(args, szFormat);
		PlayerBotLogThrottledV(false, szTag, dwNow, szFormat, args);
		va_end(args);
	}

	// Genuinely wrong, and still not worth eleven thousand copies of.
	void PlayerBotErrThrottled(const char* szTag, DWORD dwNow, const char* szFormat, ...)
	{
		va_list args;
		va_start(args, szFormat);
		PlayerBotLogThrottledV(true, szTag, dwNow, szFormat, args);
		va_end(args);
	}

	// MT2009_PLUS_BOT_LOG_QUIET_V1 (the owner, 6 November 2026: syslog 3.5-10 GB a day; "much less spam, keep the
	// census lines"). The lines every bot writes for every potion, skill, mount and swap are kept one a bot every
	// PLAYERBOT_LOG_QUIET_GAP_MIN minutes (default 10) and counted otherwise; the counts come out on one line,
	// "PLAYERBOT_LOG: quiet ...", every ten minutes. PLAYERBOT_LOG_QUIET=0 writes every line as before. The census
	// lines never come through here.
	const DWORD PLAYERBOT_LOG_QUIET_REPORT_MS = 10 * 60 * 1000;

	struct TPlayerBotLogQuiet
	{
		int on;	// -1 unread
		DWORD gapMs;
		DWORD reportAt;
		std::map<std::pair<const char*, DWORD>, DWORD> lastByBot;	// (tag, pid) -> when written
		std::map<std::string, std::pair<DWORD, DWORD> > counts;	// tag -> written, held
		TPlayerBotLogQuiet() : on(-1), gapMs(600000), reportAt(0) {}
	};
	TPlayerBotLogQuiet s_kPlayerBotLogQuiet;

	bool IsPlayerBotLogQuiet()
	{
		TPlayerBotLogQuiet& q = s_kPlayerBotLogQuiet;
		if (q.on < 0)
		{
			const char* v = std::getenv("PLAYERBOT_LOG_QUIET");
			q.on = (v && *v == '0') ? 0 : 1;
			const char* g = std::getenv("PLAYERBOT_LOG_QUIET_GAP_MIN");
			const int gap = g && *g ? atoi(g) : 10;
			q.gapMs = (DWORD)std::max(1, std::min(24 * 60, gap)) * 60000U;
			sys_log(0, "PLAYERBOT_LOG: quiet on=%d gap_min=%u", q.on, q.gapMs / 60000U);
		}
		return q.on != 0;
	}

	void PlayerBotLogQuietReport(DWORD dwNow)
	{
		TPlayerBotLogQuiet& q = s_kPlayerBotLogQuiet;
		if (q.reportAt == 0)
		{
			q.reportAt = dwNow;
			return;
		}
		if (dwNow - q.reportAt < PLAYERBOT_LOG_QUIET_REPORT_MS)
			return;
		std::string line;
		for (std::map<std::string, std::pair<DWORD, DWORD> >::const_iterator it = q.counts.begin(); it != q.counts.end(); ++it)
		{
			char buf[96];
			snprintf(buf, sizeof(buf), " %s=%u/%u", it->first.c_str(), it->second.first, it->second.first + it->second.second);
			line += buf;
		}
		sys_log(0, "PLAYERBOT_LOG: quiet window_min=%u written/all:%s", (dwNow - q.reportAt) / 60000U, line.c_str());
		q.counts.clear();
		q.reportAt = dwNow;
		// A bot that left keeps no entry for ever.
		if (q.lastByBot.size() > 200000)
			q.lastByBot.clear();
	}

	// One line a bot every gap for this tag (a string literal: its address is the key), the rest counted.
	void PlayerBotLogPerBot(const char* szTag, DWORD dwPid, DWORD dwNow, const char* szFormat, ...)
	{
		if (IsPlayerBotLogQuiet())
		{
			TPlayerBotLogQuiet& q = s_kPlayerBotLogQuiet;
			PlayerBotLogQuietReport(dwNow);
			std::pair<DWORD, DWORD>& count = q.counts[szTag];
			DWORD& last = q.lastByBot[std::make_pair(szTag, dwPid)];
			if (last != 0 && dwNow - last < q.gapMs)
			{
				++count.second;
				return;
			}
			last = dwNow ? dwNow : 1;
			++count.first;
		}
		char body[512];
		va_list args;
		va_start(args, szFormat);
		vsnprintf(body, sizeof(body), szFormat, args);
		va_end(args);
		sys_log(0, "%s", body);
	}

	// PlayerBotLogThrottled with a window of its own: one line a window for the whole population, the rest counted
	// and said on the next. Under PLAYERBOT_LOG_QUIET=0 the window is the usual minute.
	struct TPlayerBotLogEvery
	{
		DWORD next, held;
		TPlayerBotLogEvery() : next(0), held(0) {}
	};
	std::map<std::string, TPlayerBotLogEvery> s_mapPlayerBotLogEvery;

	void PlayerBotLogThrottledEvery(const char* szTag, DWORD dwNow, DWORD dwWindowMs, const char* szFormat, ...)
	{
		const DWORD window = IsPlayerBotLogQuiet() ? dwWindowMs : PLAYERBOT_LOG_THROTTLE_WINDOW;
		TPlayerBotLogEvery& e = s_mapPlayerBotLogEvery[szTag ? szTag : "?"];
		if (e.next != 0 && (int)(dwNow - e.next) < 0)
		{
			++e.held;
			return;
		}
		char body[512];
		va_list args;
		va_start(args, szFormat);
		vsnprintf(body, sizeof(body), szFormat, args);
		va_end(args);
		if (e.held)
			sys_log(0, "%s [+%u more in the last %u min]", body, e.held, window / 60000U);
		else
			sys_log(0, "%s", body);
		e.held = 0;
		e.next = dwNow + window;
	}
}

#endif
