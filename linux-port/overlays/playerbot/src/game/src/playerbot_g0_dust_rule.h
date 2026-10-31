#ifndef __INC_METIN2_PLAYERBOT_G0_DUST_RULE_H__
#define __INC_METIN2_PLAYERBOT_G0_DUST_RULE_H__

// MT2009_PLUS_BOT_G0_DUST_RULE_V1 - who holds Magiczny Pyl back, and the power elixir's dust (the owner, 28 October 2026:
// "Po co maja zbierac na G0, skoro juz maja G0? Pyl maja zbierac tylko wtedy, gdy nie radza sobie z obecnym G0 i chca
// zbierac na drugi zestaw G0").
//
// The census of 28 October: PLAYERBOT_SHOP2 power_made=0 dust_paid=0 dust_bought=0, every "errand wanted" line
// dust_free=0. 900 bots had their G0 (mt2009_g0.given), 144 of them had started a second set (mt2009_ss.e2) and so were
// second G0 savers (MT2009_PLUS_BOT_ELEMENT_SECOND_SET_V1): 400 dust kept, the market's dust and the trips theirs,
// nothing for the power elixir - whether they coped with their set or not.
//
// 1. The first package (playerbot_yohara_g0.h, IsPlayerBotG0Saver): unchanged - a bot of level 110+ the package is for,
//    not given yet, keeps 400 (in the bag, or banked till it qualifies as a Champion).
// 2. A bot with its G0 holds no reserve, unless it is a second G0 saver (IsPlayerBotG0Saver2), which now needs both:
//    * the second-set mode (IsPlayerBotG0SecondSetMode): its second set started (an element E2 chosen), or a step down
//      to a map of another element refused for want of the set (the hunt element's "change refused why=down", or the
//      map pick holding it where its maps no longer fit - NotePlayerBotG0DownBlocked) in the last
//      PLAYERBOT_G0DR_BLOCKED_S;
//    * the struggle (IsPlayerBotG0Struggling) - it cannot cope with its set, by the numbers the bots already keep:
//      (a) "stepped_down": a step down after its deaths (3 in half an hour, playerbot_yohara_sungma.h) still holds it
//          off its map ("not now", two hours) - it is held below the map its band and Will give it;
//      (b) "kills_per_death": in its Sung Ma window (the current and the last hour, kills and deaths of its own on the
//          Sung Ma maps) PLAYERBOT_G0DR_MIN_DEATHS deaths or more, and its kills per death under
//          PLAYERBOT_G0DR_KPD_PCT per cent of its map's (the map's last fight2 line; PLAYERBOT_G0DR_KPD_FALLBACK10 / 10
//          before the first) - the night's maps ran 4-9 kills per death on Dongan, Namgan, Wawoz and Rozpadlina, 11-87
//          elsewhere, so a bot under half of that dies twice as often as its neighbours;
//      (c) "retreat_time": PLAYERBOT_G0DR_RETREAT_S or more of retreats in the same window (37-75% of it - FIGHT2 put the
//          map's average well under that).
//      Proven, the struggle holds PLAYERBOT_G0DR_HOLD_S (a quest flag, so it crosses the cores with the bot: its home
//      village's counters see the same reserve as its map), renewed while proven again; the reserve does not flap.
//    Only then the 400 are kept and sought (the counters' keep, the marbles and bonus stones, the G0 market line, the
//    dust trips - all asking GetPlayerBotG0DustReserve / IsPlayerBotG0DustHunter); the package itself goes into a
//    started set only (a saver whose set has no element yet keeps the 400 till it has).
// 3. The dust over the reserve is the hunt element's power elixir's at Handlarka (playerbot_yohara_shop.h, its targets
//    as before: filled to 8, the errand under 4). Bots buy the power elixir's dust on the market too (the shop's line,
//    existing since MT2009_PLUS_BOT_YOHARA_SHOP_V1 and held by the reserve till now), bounded here: at most
//    PLAYERBOT_G0_DUST_PRICE_CAP_PCT of the bots' dust price, out of PLAYERBOT_YSHOP_DUST_PURSE_PCT of the spare purse,
//    at most PLAYERBOT_G0DR_POWER_DUST_DAY units a bot in PLAYERBOT_G0DR_DAY_MS (this core's memory), and only while the
//    core's counters keep more than PLAYERBOT_G0DR_POWER_DUST_FLOOR units after the buy. The elixir burns 60 dust an
//    hour on the map: 900 Champions on an open line would take every unit off the counters (the lower bots' marbles
//    and bonus stones, and the players, buy there) and pin its price at the cap - the budget keeps the market's share a
//    top-up of what the bot's own dust (the Alchemist's, its drops) pays.
// 4. The log: PLAYERBOT_G0DUST - reason (every change of a bot's reason: none / first_g0 / second_g0_struggling, with the
//    second-set mode and the struggle's why), struggle start / end (the window's numbers), down blocked (throttled),
//    power dust bought, census every ten minutes: the reasons of the bots looked at on this core, the second-set
//    bots struggling or calm (by why), the reason changes, the power elixir's dust bought and refused, power_made /
//    dust_paid of the shop, and the power elixir's uptime per element (on or drunk of the looks alive on its map, as
//    the resistance elixir's elixir_up) with its looks by outcome.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_element_second_set.h, in the anonymous
// namespace; the declarations the earlier fragments use are in playerbot_types.h.

#ifdef MT2009_PLUS_BOT_G0_DUST_RULE_V1
namespace
{
	const DWORD PLAYERBOT_G0DR_BUCKET_MS = 60 * 60 * 1000;	// the window: this bucket and the last
	const unsigned int PLAYERBOT_G0DR_MIN_DEATHS = 3;
	// MT2009_PLUS_BOT_G0_DUST_RULE_V2 (the owner's approval of item 4 of BOTY-YOHARA-ANALIZA-v2.md, 31 October 2026): 75
	// (was 50) - in 24 hours 9 struggle starts of 271-397 second-set bots, second_g0_struggling=0 in every census
	const int PLAYERBOT_G0DR_KPD_PCT = 75;
	const int PLAYERBOT_G0DR_KPD_FALLBACK10 = 50;	// 5.0 kills per death, a map without a fight2 line yet
	const DWORD PLAYERBOT_G0DR_RETREAT_S = 30 * 60;	// MT2009_PLUS_BOT_G0_DUST_RULE_V2: 30 (was 45) minutes of the two hours
	const int PLAYERBOT_G0DR_HOLD_S = 2 * 60 * 60;
	const int PLAYERBOT_G0DR_HOLD_RENEW_S = 10 * 60;	// the flag rewritten when this much of the hold has passed
	const int PLAYERBOT_G0DR_BLOCKED_S = 2 * 60 * 60;
	const int PLAYERBOT_G0DR_BLOCKED_RENEW_S = 10 * 60;
	const int PLAYERBOT_G0DR_POWER_DUST_DAY = 120;	// twelve power elixirs a day off the market
	const DWORD PLAYERBOT_G0DR_DAY_MS = 24 * 60 * 60 * 1000;
	// MT2009_PLUS_BOT_DUST_MARKET_V1: 0 (was 100) - the floor kept the counters' dust for the lower bots' marbles and
	// bonus stones; the producers of level 100 and under spend none now (they list it for the Champions), and with a
	// floor of a hundred a thin market never sold one unit for an elixir (power_dust_bought=0 on every core)
	const int PLAYERBOT_G0DR_POWER_DUST_FLOOR = 0;
	const DWORD PLAYERBOT_G0DR_CENSUS_MS = 10 * 60 * 1000;

	const char* const PLAYERBOT_G0DR_FLAG_UNTIL = "mt2009_g0.struggle_until";
	const char* const PLAYERBOT_G0DR_FLAG_WHY = "mt2009_g0.struggle_why";
	const char* const PLAYERBOT_G0DR_FLAG_BLOCKED = "mt2009_g0.down_blocked";

	enum { PLAYERBOT_G0DR_WHY_NONE, PLAYERBOT_G0DR_WHY_STEPPED, PLAYERBOT_G0DR_WHY_KPD, PLAYERBOT_G0DR_WHY_RETREAT, PLAYERBOT_G0DR_WHYS };
	const char* const PLAYERBOT_G0DR_WHY_NAMES[PLAYERBOT_G0DR_WHYS] = { "none", "stepped_down", "kills_per_death", "retreat_time" };

	struct TPlayerBotG0Struggle
	{
		DWORD dwBucketAt;
		unsigned int auKills[2], auDeaths[2];
		DWORD adwRetreatMs[2];
		long lMap;	// the Sung Ma map of its last kill or death
		bool bStruggling;	// this core's last answer (the start / end lines)
		DWORD dwBlockedLogAt;
		DWORD dwPowerDayAt;
		int iPowerDust;
		TPlayerBotG0Struggle() : dwBucketAt(0), lMap(0), bStruggling(false), dwBlockedLogAt(0), dwPowerDayAt(0), iPowerDust(0)
		{
			for (int i = 0; i < 2; ++i)
			{
				auKills[i] = auDeaths[i] = 0;
				adwRetreatMs[i] = 0;
			}
		}
	};
	std::map<DWORD, TPlayerBotG0Struggle> s_mapPlayerBotG0Struggle;

	struct TPlayerBotG0DustRuleStats
	{
		unsigned int reasonChanges, toFirst, toSecond, toNone, struggleStarts, struggleEnds, downBlocked;
		unsigned int powerDustBought, powerDustBuys;
		DWORD dwCensusAt;
		TPlayerBotG0DustRuleStats() : reasonChanges(0), toFirst(0), toSecond(0), toNone(0), struggleStarts(0), struggleEnds(0),
			downBlocked(0), powerDustBought(0), powerDustBuys(0), dwCensusAt(0) {}
	};
	TPlayerBotG0DustRuleStats s_kPlayerBotG0DustRuleStats;
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
	unsigned int s_aPlayerBotPowerElixirLooks[PLAYERBOT_YOHARA_ELEMENTS][PLAYERBOT_ELIXIR_COUNT];
#endif

	// The bot's record, its window moved on to now.
	TPlayerBotG0Struggle& GetPlayerBotG0Struggle(DWORD pid, DWORD dwNow)
	{
		TPlayerBotG0Struggle& s = s_mapPlayerBotG0Struggle[pid];
		if (s.dwBucketAt == 0)
			s.dwBucketAt = dwNow ? dwNow : 1;
		const DWORD el = dwNow - s.dwBucketAt;
		if (el >= 2 * PLAYERBOT_G0DR_BUCKET_MS)
		{
			for (int i = 0; i < 2; ++i)
			{
				s.auKills[i] = s.auDeaths[i] = 0;
				s.adwRetreatMs[i] = 0;
			}
			s.dwBucketAt = dwNow ? dwNow : 1;
		}
		else if (el >= PLAYERBOT_G0DR_BUCKET_MS)
		{
			s.auKills[1] = s.auKills[0];
			s.auDeaths[1] = s.auDeaths[0];
			s.adwRetreatMs[1] = s.adwRetreatMs[0];
			s.auKills[0] = s.auDeaths[0] = 0;
			s.adwRetreatMs[0] = 0;
			s.dwBucketAt += PLAYERBOT_G0DR_BUCKET_MS;
		}
		return s;
	}

	long GetPlayerBotG0StruggleBase(LPCHARACTER ch)
	{
		const long map = ch->GetMapIndex();
		return map >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? map / 10000 : map;
	}

	void NotePlayerBotG0StruggleKill(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC())
			return;
		TPlayerBotG0Struggle& s = GetPlayerBotG0Struggle(ch->GetPlayerID(), get_dword_time());
		++s.auKills[0];
		s.lMap = GetPlayerBotG0StruggleBase(ch);
	}

	void NotePlayerBotG0StruggleDeath(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC())
			return;
		TPlayerBotG0Struggle& s = GetPlayerBotG0Struggle(ch->GetPlayerID(), get_dword_time());
		++s.auDeaths[0];
		s.lMap = GetPlayerBotG0StruggleBase(ch);
	}

	void NotePlayerBotG0StruggleRetreat(LPCHARACTER ch, DWORD ms)
	{
		if (!ch || !ch->IsPC())
			return;
		TPlayerBotG0Struggle& s = GetPlayerBotG0Struggle(ch->GetPlayerID(), get_dword_time());
		s.adwRetreatMs[0] += ms;
	}

	// A step down to another element's map refused for want of the second set: the mode's flag (a bot with its G0 only,
	// the flag rewritten every PLAYERBOT_G0DR_BLOCKED_RENEW_S at most).
	void NotePlayerBotG0DownBlocked(LPCHARACTER ch, const char* where)
	{
		if (!ch || !ch->IsPC() || !ch->GetDesc() || !ch->GetDesc()->IsBot() || ch->GetQuestFlag(PLAYERBOT_G0_GIVEN_FLAG) == 0 ||
				ch->GetQuestFlag(PLAYERBOT_G0_GIVEN2_FLAG) != 0)
			return;
		const int now = (int)time(0);
		const int at = ch->GetQuestFlag(PLAYERBOT_G0DR_FLAG_BLOCKED);
		if (at != 0 && now - at < PLAYERBOT_G0DR_BLOCKED_RENEW_S)
			return;
		ch->SetQuestFlag(PLAYERBOT_G0DR_FLAG_BLOCKED, now);
		++s_kPlayerBotG0DustRuleStats.downBlocked;
		const DWORD dwNow = get_dword_time();
		TPlayerBotG0Struggle& s = GetPlayerBotG0Struggle(ch->GetPlayerID(), dwNow);
		if (s.dwBlockedLogAt != 0 && dwNow - s.dwBlockedLogAt < (DWORD)PLAYERBOT_G0DR_BLOCKED_S * 1000U)
			return;
		s.dwBlockedLogAt = dwNow ? dwNow : 1;
		sys_log(0, "PLAYERBOT_G0DUST: down blocked pid=%u name=%s map=%ld where=%s e2=%d", ch->GetPlayerID(), ch->GetName(),
				ch->GetMapIndex(), where ? where : "-", GetPlayerBotSecondSetElement(ch));
	}

	// The second-set mode: the set started, or a step down refused for want of it lately.
	bool IsPlayerBotG0SecondSetMode(LPCHARACTER ch)
	{
		if (!ch)
			return false;
		if (GetPlayerBotSecondSetElement(ch) >= 0)
			return true;
		const int at = ch->GetQuestFlag(PLAYERBOT_G0DR_FLAG_BLOCKED);
		return at != 0 && (int)time(0) - at < PLAYERBOT_G0DR_BLOCKED_S;
	}

	// The struggle's proof now (PLAYERBOT_G0DR_WHY_NONE: none); the window's numbers out.
	int ProvePlayerBotG0Struggle(LPCHARACTER ch, DWORD dwNow, unsigned int& kills, unsigned int& deaths, DWORD& retreatMs, int& mapKpd10)
	{
		const DWORD pid = ch->GetPlayerID();
		TPlayerBotG0Struggle& s = GetPlayerBotG0Struggle(pid, dwNow);
		kills = s.auKills[0] + s.auKills[1];
		deaths = s.auDeaths[0] + s.auDeaths[1];
		retreatMs = s.adwRetreatMs[0] + s.adwRetreatMs[1];
		const int slot = s.lMap ? GetPlayerBotSungmaSlot(s.lMap) : -1;
		mapKpd10 = slot >= 0 && slot < 9 && s_aiPlayerBotSungmaF2Kpd10[slot] > 0 ? s_aiPlayerBotSungmaF2Kpd10[slot] : PLAYERBOT_G0DR_KPD_FALLBACK10;
		// (a) the deaths' step down still holding it off its map
		std::map<DWORD, TPlayerBotSungmaBot>::const_iterator b = s_mapPlayerBotSungma.find(pid);
		if (b != s_mapPlayerBotSungma.end())
			for (std::map<long, DWORD>::const_iterator nn = b->second.mapNotNow.begin(); nn != b->second.mapNotNow.end(); ++nn)
				if ((int)(nn->second - dwNow) > 0)
					return PLAYERBOT_G0DR_WHY_STEPPED;
		// (b) its kills per death under half its map's
		if (deaths >= PLAYERBOT_G0DR_MIN_DEATHS &&
				(long long)kills * 10 * 100 < (long long)mapKpd10 * deaths * PLAYERBOT_G0DR_KPD_PCT)
			return PLAYERBOT_G0DR_WHY_KPD;
		// (c) its time in retreats
		if (retreatMs / 1000 >= PLAYERBOT_G0DR_RETREAT_S)
			return PLAYERBOT_G0DR_WHY_RETREAT;
		return PLAYERBOT_G0DR_WHY_NONE;
	}

	// It cannot cope with its set: proven now (the hold renewed), or within the hold of the last proof (the flag, on
	// whichever core). why: the proof's name ("none" when not struggling).
	bool IsPlayerBotG0Struggling(LPCHARACTER ch, const char** why)
	{
		if (why)
			*why = PLAYERBOT_G0DR_WHY_NAMES[PLAYERBOT_G0DR_WHY_NONE];
		if (!ch || !ch->IsPC())
			return false;
		const DWORD dwNow = get_dword_time();
		const int now = (int)time(0);
		unsigned int kills = 0, deaths = 0;
		DWORD retreatMs = 0;
		int mapKpd10 = 0;
		const int proof = ProvePlayerBotG0Struggle(ch, dwNow, kills, deaths, retreatMs, mapKpd10);
		int until = ch->GetQuestFlag(PLAYERBOT_G0DR_FLAG_UNTIL);
		if (proof != PLAYERBOT_G0DR_WHY_NONE && until - now < PLAYERBOT_G0DR_HOLD_S - PLAYERBOT_G0DR_HOLD_RENEW_S)
		{
			until = now + PLAYERBOT_G0DR_HOLD_S;
			ch->SetQuestFlag(PLAYERBOT_G0DR_FLAG_UNTIL, until);
			ch->SetQuestFlag(PLAYERBOT_G0DR_FLAG_WHY, proof);
		}
		const bool on = until > now;
		int whyCode = on ? ch->GetQuestFlag(PLAYERBOT_G0DR_FLAG_WHY) : PLAYERBOT_G0DR_WHY_NONE;
		if (whyCode < 0 || whyCode >= PLAYERBOT_G0DR_WHYS)
			whyCode = PLAYERBOT_G0DR_WHY_NONE;
		if (why)
			*why = PLAYERBOT_G0DR_WHY_NAMES[whyCode];
		TPlayerBotG0Struggle& s = GetPlayerBotG0Struggle(ch->GetPlayerID(), dwNow);
		if (on != s.bStruggling)
		{
			s.bStruggling = on;
			if (on)
				++s_kPlayerBotG0DustRuleStats.struggleStarts;
			else
				++s_kPlayerBotG0DustRuleStats.struggleEnds;
			sys_log(0, "PLAYERBOT_G0DUST: struggle %s pid=%u name=%s why=%s proof_now=%s map=%ld kills=%u deaths=%u map_kpd=%d.%d "
					"retreat_s=%u hold_s=%d champion=%d e2=%d",
					on ? "start" : "end", ch->GetPlayerID(), ch->GetName(), PLAYERBOT_G0DR_WHY_NAMES[whyCode],
					PLAYERBOT_G0DR_WHY_NAMES[proof], s.lMap, kills, deaths, mapKpd10 / 10, mapKpd10 % 10,
					(unsigned int)(retreatMs / 1000), on ? until - now : 0, GetPlayerBotChampionLevel(ch),
					GetPlayerBotSecondSetElement(ch));
		}
		return on;
	}

	// LookPlayerBotG0: a bot's reason changed (old -1: its first look on this core).
	void NotePlayerBotG0DustReason(LPCHARACTER ch, int oldReason, int newReason)
	{
		if (!ch || newReason < 0 || newReason >= PLAYERBOT_G0_REASONS)
			return;
		if (oldReason >= 0)
		{
			++s_kPlayerBotG0DustRuleStats.reasonChanges;
			if (newReason == PLAYERBOT_G0_REASON_FIRST)
				++s_kPlayerBotG0DustRuleStats.toFirst;
			else if (newReason == PLAYERBOT_G0_REASON_SECOND)
				++s_kPlayerBotG0DustRuleStats.toSecond;
			else
				++s_kPlayerBotG0DustRuleStats.toNone;
		}
		const char* why = PLAYERBOT_G0DR_WHY_NAMES[PLAYERBOT_G0DR_WHY_NONE];
		const int until = ch->GetQuestFlag(PLAYERBOT_G0DR_FLAG_UNTIL);
		if (until > (int)time(0))
		{
			const int code = ch->GetQuestFlag(PLAYERBOT_G0DR_FLAG_WHY);
			if (code > 0 && code < PLAYERBOT_G0DR_WHYS)
				why = PLAYERBOT_G0DR_WHY_NAMES[code];
		}
		sys_log(0, "PLAYERBOT_G0DUST: reason pid=%u name=%s from=%s to=%s level=%u champion=%d g0=%d g0_set2=%d second_mode=%d "
				"e2=%d struggle=%s dust=%d banked=%d map=%ld",
				ch->GetPlayerID(), ch->GetName(), oldReason >= 0 && oldReason < PLAYERBOT_G0_REASONS ? PLAYERBOT_G0_REASON_NAMES[oldReason] : "-",
				PLAYERBOT_G0_REASON_NAMES[newReason], (unsigned int)ch->GetLevel(), GetPlayerBotChampionLevel(ch),
				ch->GetQuestFlag(PLAYERBOT_G0_GIVEN_FLAG) != 0 ? 1 : 0, ch->GetQuestFlag(PLAYERBOT_G0_GIVEN2_FLAG) != 0 ? 1 : 0,
				ch->GetQuestFlag(PLAYERBOT_G0_GIVEN_FLAG) != 0 && IsPlayerBotG0SecondSetMode(ch) ? 1 : 0,
				GetPlayerBotSecondSetElement(ch), why, GetPlayerBotG0DustHeld(ch), ch->GetQuestFlag(PLAYERBOT_G0_BANKED_FLAG),
				ch->GetMapIndex());
	}

	// ------------------------------------------------------------ the power elixir's market dust

	// The day's units left and the counters' floor kept after `units` more.
	bool AllowsPlayerBotPowerDustMarket(LPCHARACTER ch, int units)
	{
		if (!ch || units <= 0)
			return false;
		const TPlayerBotMarketLedgerEntry* dust = GetPlayerBotMarketLedgerEntry(PLAYERBOT_MAGIC_DUST_VNUM);
		if (!dust || (long long)dust->dwSupplyUnits - units < (long long)PLAYERBOT_G0DR_POWER_DUST_FLOOR)
			return false;
		const DWORD dwNow = get_dword_time();
		TPlayerBotG0Struggle& s = GetPlayerBotG0Struggle(ch->GetPlayerID(), dwNow);
		if (s.dwPowerDayAt == 0 || dwNow - s.dwPowerDayAt >= PLAYERBOT_G0DR_DAY_MS)
		{
			s.dwPowerDayAt = dwNow ? dwNow : 1;
			s.iPowerDust = 0;
		}
		return s.iPowerDust + units <= PLAYERBOT_G0DR_POWER_DUST_DAY;
	}

	void NotePlayerBotPowerDustMarket(LPCHARACTER ch, int units)
	{
		if (!ch || units <= 0)
			return;
		const DWORD dwNow = get_dword_time();
		TPlayerBotG0Struggle& s = GetPlayerBotG0Struggle(ch->GetPlayerID(), dwNow);
		if (s.dwPowerDayAt == 0 || dwNow - s.dwPowerDayAt >= PLAYERBOT_G0DR_DAY_MS)
		{
			s.dwPowerDayAt = dwNow ? dwNow : 1;
			s.iPowerDust = 0;
		}
		s.iPowerDust += units;
		s_kPlayerBotG0DustRuleStats.powerDustBought += (unsigned int)units;
		++s_kPlayerBotG0DustRuleStats.powerDustBuys;
		sys_log(0, "PLAYERBOT_G0DUST: power dust bought pid=%u name=%s count=%d day=%d/%d dust=%d", ch->GetPlayerID(), ch->GetName(),
				units, s.iPowerDust, PLAYERBOT_G0DR_POWER_DUST_DAY, GetPlayerBotG0DustHeld(ch));
	}

	// ------------------------------------------------------------ the power elixir's uptime, the census

	void NotePlayerBotPowerElixirLook(int e, int outcome)
	{
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
		if (e >= 0 && e < PLAYERBOT_YOHARA_ELEMENTS && outcome >= 0 && outcome < PLAYERBOT_ELIXIR_COUNT)
			++s_aPlayerBotPowerElixirLooks[e][outcome];
#else
		(void)e;
		(void)outcome;
#endif
	}

	void LogPlayerBotG0DustRuleCensus(DWORD dwNow)
	{
		TPlayerBotG0DustRuleStats& st = s_kPlayerBotG0DustRuleStats;
		if (st.dwCensusAt == 0)
		{
			st.dwCensusAt = dwNow ? dwNow : 1;
			return;
		}
		if (dwNow - st.dwCensusAt < PLAYERBOT_G0DR_CENSUS_MS)
			return;
		st.dwCensusAt = dwNow ? dwNow : 1;
		int reasons[PLAYERBOT_G0_REASONS] = { 0 };
		int secondMode = 0, struggling = 0, calm = 0, banked = 0;
		int whys[PLAYERBOT_G0DR_WHYS] = { 0 };
		const int now = (int)time(0);
		for (std::map<DWORD, TPlayerBotG0>::const_iterator it = s_mapPlayerBotG0.begin(); it != s_mapPlayerBotG0.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || it->second.iReason < 0 || it->second.iReason >= PLAYERBOT_G0_REASONS)
				continue;
			++reasons[it->second.iReason];
			if (it->second.iReason == PLAYERBOT_G0_REASON_FIRST && IsPlayerBotG0DustBanked(ch))
				++banked;
			if (ch->GetQuestFlag(PLAYERBOT_G0_GIVEN_FLAG) == 0 || ch->GetQuestFlag(PLAYERBOT_G0_GIVEN2_FLAG) != 0 ||
					!IsPlayerBotG0SecondSetMode(ch))
				continue;
			++secondMode;
			if (ch->GetQuestFlag(PLAYERBOT_G0DR_FLAG_UNTIL) > now)
			{
				++struggling;
				const int code = ch->GetQuestFlag(PLAYERBOT_G0DR_FLAG_WHY);
				++whys[code > 0 && code < PLAYERBOT_G0DR_WHYS ? code : 0];
			}
			else
				++calm;
		}
		std::string power;
#ifdef MT2009_PLUS_BOT_ELEMENT_RESIST_V3
		for (int e = 0; e < PLAYERBOT_YOHARA_ELEMENTS; ++e)
		{
			const unsigned int* looks = s_aPlayerBotPowerElixirLooks[e];
			const unsigned int on = looks[PLAYERBOT_ELIXIR_ON] + looks[PLAYERBOT_ELIXIR_DRUNK];
			const unsigned int alive = on + looks[PLAYERBOT_ELIXIR_NO_STOCK] + looks[PLAYERBOT_ELIXIR_USE_FAILED];
			std::string why;
			for (int k = 0; k < PLAYERBOT_ELIXIR_COUNT; ++k)
			{
				char part[40];
				snprintf(part, sizeof(part), "%s%s=%u", k ? " " : "", PLAYERBOT_ELIXIR_REASON_NAMES[k], looks[k]);
				why += part;
			}
			char one[256];
			snprintf(one, sizeof(one), " %s=[power_up=%u%% looks=[%s]]", PLAYERBOT_YOHARA_ELEMENT_NAMES[e], alive ? on * 100 / alive : 0,
					why.c_str());
			power += one;
			for (int k = 0; k < PLAYERBOT_ELIXIR_COUNT; ++k)
				s_aPlayerBotPowerElixirLooks[e][k] = 0;
		}
#endif
		sys_log(0, "PLAYERBOT_G0DUST: census reserve=[first_g0=%d second_g0_struggling=%d none=%d] first_g0_banked=%d second_mode=%d "
				"struggling=%d (stepped_down=%d kills_per_death=%d retreat_time=%d) calm=%d reason_changes=%u to_first=%u to_second=%u "
				"to_none=%u struggle_starts=%u struggle_ends=%u down_blocked=%u power_dust_bought=%u buys=%u power_made=%u dust_paid=%u%s",
				reasons[PLAYERBOT_G0_REASON_FIRST], reasons[PLAYERBOT_G0_REASON_SECOND], reasons[PLAYERBOT_G0_REASON_NONE], banked,
				secondMode, struggling, whys[PLAYERBOT_G0DR_WHY_STEPPED], whys[PLAYERBOT_G0DR_WHY_KPD], whys[PLAYERBOT_G0DR_WHY_RETREAT],
				calm, st.reasonChanges, st.toFirst, st.toSecond, st.toNone, st.struggleStarts, st.struggleEnds, st.downBlocked,
				st.powerDustBought, st.powerDustBuys, s_kPlayerBotYoharaShopStats.powerMade, s_kPlayerBotYoharaShopStats.dustPaid,
				power.c_str());
	}
}
#endif

#endif
