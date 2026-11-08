#ifndef __INC_METIN2_PLAYERBOT_MARBLE_FIRST_H__
#define __INC_METIN2_PLAYERBOT_MARBLE_FIRST_H__

// MT2009_PLUS_BOT_MARBLE_FIRST_V1 - a bot with Smocze Monety brings a piece to five lines before it changes the lines
// (the owner, 8 November 2026: "Jak boty maja SM i zmieniaja bonusy zaczarowaniem przedmiotu, to niech glownie mieszaja
// przedmioty ktore maja 5 bonusow, czyli maja dodany 5. bonus marmurem blogoslawienstwa. Zmienianie bonusow gdy sa tylko
// 4 to mniejsza szansa na wbicie odpowiednich bonusow. Wiec bot powinien dazyc do 5 bonusow, a jesli nie ma takiej
// mozliwosci, to w ostatecznosci zmieniac bonusy w 4-bonusowych przedmiotach. Wyjatkiem jest to, jak boty nie maja w
// ogole SM. Wtedy moga zmieniac przedmioty nawet 2-3 bonusowe i to jest okej.").
//
// What there was: the ordinary pass (playerbot_bonus.h, playerbot_bonus_rules.h StepFor) changed (71084) any worn piece
// of four lines - of three with no add stone in the bag (MT2009_PLUS_BOT_CHANGE_NO_ADD_V1) - and put the marble (70024)
// on a four-line category piece only when one lay in the bag; the Yohara pass (playerbot_yohara_bonus_rules.h Pick)
// changed any piece with a line at all once the adds and a held marble were spent. The ItemShop V3 bought one marble a
// look (hold 2, day 4). On the test world ~60 of ~90 pieces of the 6/7 scope (playerbot_bonus67_bots.h) stood at four
// lines - and the 6/7 pass takes only a piece of five.
//
// Now, for a bot with Smocze Monety it may spend (the balance read, more than none, the ItemShop V3 the bots' source -
// IsPlayerBotMarbleFirstFor):
//   * a worn piece is changed only at m2_bot_change_min_lines_sm lines (5); short of them the adds fill it to four as
//     before, then the marble gives the fifth - held, else bought in V3 ("bonus_marble", one for every four-line piece
//     waiting, hold 4 / day 16 now) - also on a piece of "the rest of the gear" (PLAIN_REST) the marble skipped;
//   * a piece of three lines or fewer is never changed while it can still take a line;
//   * a four-line piece only as the last resort (m2_bot_change_fallback4, on): the marble cannot be had or used - the
//     shop / pool / day cap refused it within PLAYERBOT_MARBLE_FIRST_REFUSED_MS and none is held, the piece cannot roll a
//     fifth line, or PLAYERBOT_MARBLE_FIRST_FAIL_STREAK marbles failed on it in a row - AND the bot's goal needs a better
//     bonus now (IsPlayerBotSmPoolUrgent's bonus_change: a Yohara move waiting on its element must, a gate holding it
//     for HP from items, a 70+ bot under its band's HP median);
//   * the pieces of the 6/7 scope (GetPlayerBotBonus67Scope: armour 61+, helmet / shield 41+, the jewellery of
//     Niebianskie Lzy 54+ with the jade and Yohara tiers, the element jewellery / boots) take the adds and the marble
//     first, so they reach five lines and the 6/7 pass can start on them. PlayerBotPieceWantsFifth is the shared signal
//     ("this piece waits for its fifth line").
// A bot with no SM (or the switch off) changes as before - 2-3 line pieces included. The level-30 weapons' average mix,
// the green stones, the held / goods pieces and the element gate's own work (playerbot_element_shop.h) are untouched.
//
// Flags: m2_bot_marble_first_off 1 (the old behaviour for everyone), m2_bot_change_min_lines_sm N (1-5; 0 = 5),
// m2_bot_change_fallback4 (0 / 1 on - the default; -1 or 2+ off: a four-line piece of an SM bot is never changed).
// The log: PLAYERBOT_MARBLE_FIRST census every 10 minutes - the marbles asked / bought / refused in V3, used / won / lost,
// the changes on 5 / 4 / <=3-line pieces by bots with SM and without, the gate's refusals and last-resort passes, and the
// worn pieces of the 6/7 scope under five lines (the stage's - 75+ - and the bots under it; the change since the last
// census); "fallback4" (throttled) for each last-resort change allowed.
//
// An implementation fragment: include it once, from playerbot_manager.cpp, right after playerbot_bonus67_bots.h; the
// declarations are in playerbot_types.h.

#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_BOT_MARBLE_FIRST_V1)

namespace
{
	const char* const PLAYERBOT_MARBLE_FIRST_OFF_FLAG = "m2_bot_marble_first_off";
	const char* const PLAYERBOT_MARBLE_FIRST_MIN_LINES_FLAG = "m2_bot_change_min_lines_sm";
	const char* const PLAYERBOT_MARBLE_FIRST_FALLBACK4_FLAG = "m2_bot_change_fallback4";
	const int PLAYERBOT_MARBLE_FIRST_MIN_LINES = 5;
	const DWORD PLAYERBOT_MARBLE_FIRST_REFUSED_MS = 30 * 60 * 1000;
	const int PLAYERBOT_MARBLE_FIRST_FAIL_STREAK = 6;	// 70 % a miss: six in a row one time in nine
	const DWORD PLAYERBOT_MARBLE_FIRST_FAIL_MS = 60 * 60 * 1000;
	const DWORD PLAYERBOT_MARBLE_FIRST_CENSUS_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_MARBLE_FIRST_ELEMENT_MS = 60 * 1000;

	struct TPlayerBotMarbleFirst
	{
		DWORD dwRefusedAt;	// the V3 marble goal bought nothing (0: not since it last bought)
		DWORD dwFailItem;	// the piece the marbles failed on, in a row
		int iFailStreak;
		DWORD dwFailAt;
		DWORD dwElementAt;	// the 6/7 element read (cached a minute)
		int iElement;
		TPlayerBotMarbleFirst() : dwRefusedAt(0), dwFailItem(0), iFailStreak(0), dwFailAt(0), dwElementAt(0), iElement(-1) {}
	};
	std::map<DWORD, TPlayerBotMarbleFirst> s_mapPlayerBotMarbleFirst;

	struct TPlayerBotMarbleFirstStats
	{
		unsigned int shopGoals, shopWanted, shopBought, shopRefused;
		unsigned int used, won, lost, usedPriority;
		unsigned int changes[2][3];	// [has SM][5+ / 4 / <=3 lines]
		unsigned int blockLow, blockWait, blockNotUrgent, blockFallbackOff, fallback4;
		TPlayerBotMarbleFirstStats() { memset(this, 0, sizeof(*this)); }
	};
	TPlayerBotMarbleFirstStats s_kPlayerBotMarbleFirstStats;
	DWORD s_dwPlayerBotMarbleFirstCensusAt = 0;
	int s_iPlayerBotMarbleFirstLastStageUnder = -1;
	int s_iPlayerBotMarbleFirstLastPreUnder = -1;

	int GetPlayerBotMarbleFirstFlag(const char* flag)
	{
		return quest::CQuestManager::instance().GetEventFlag(flag);
	}

	int GetPlayerBotMarbleFirstMinLines()
	{
		const int v = GetPlayerBotMarbleFirstFlag(PLAYERBOT_MARBLE_FIRST_MIN_LINES_FLAG);
		return v >= 1 && v <= PLAYERBOT_BONUS_MARBLE_LINES ? v : PLAYERBOT_MARBLE_FIRST_MIN_LINES;
	}

	bool IsPlayerBotMarbleFirstFallback4On()
	{
		const int v = GetPlayerBotMarbleFirstFlag(PLAYERBOT_MARBLE_FIRST_FALLBACK4_FLAG);
		return v == 0 || v == 1;
	}

	// Smocze Monety the bot may spend: the V3 shop is the bots' source, the balance is known and holds some.
	bool PlayerBotMarbleFirstHasSm(LPCHARACTER ch)
	{
		if (!ch || !ch->GetDesc() || IsPlayerBotSidekickPID(ch->GetPlayerID()) || GetPlayerBotItemShopSource() != 2 ||
				!IsPlayerBotItemShopEnabled())
			return false;
		TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		return st != s_mapPlayerBotAIStates.end() && st->second.bDragonBalanceKnown && st->second.iDragonCoins > 0;
	}

	bool IsPlayerBotMarbleFirstFor(LPCHARACTER ch)
	{
		return GetPlayerBotMarbleFirstFlag(PLAYERBOT_MARBLE_FIRST_OFF_FLAG) == 0 && PlayerBotMarbleFirstHasSm(ch);
	}

	// The bonus goal needs a better line now - the urgent rule of the SM pool (playerbot_ishop3_goals.h).
	bool IsPlayerBotMarbleFirstUrgent(LPCHARACTER ch)
	{
#if defined(MT2009_PLUS_BOT_ISHOP_V3_V1) && defined(MT2009_PLUS_BOT_SM_DAILY_POOL_V1)
		return IsPlayerBotSmPoolUrgent(ch, "bonus_change");
#else
		return ch && (GetPlayerBotProgressionNeeds(ch->GetPlayerID()) & playerbot_progression::NEED_HP) != 0;
#endif
	}

	// The marble cannot be had or used for this piece now.
	bool IsPlayerBotMarbleFirstMarbleOut(LPCHARACTER ch, LPITEM item, bool lineRolls)
	{
		if (!lineRolls)
			return true;
		if (FindPlayerBotBlessingMarbleCell(ch) >= 0)
			return false;
		std::map<DWORD, TPlayerBotMarbleFirst>::const_iterator it = s_mapPlayerBotMarbleFirst.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotMarbleFirst.end())
			return false;
		const DWORD now = get_dword_time();
		const TPlayerBotMarbleFirst& m = it->second;
		if (m.dwRefusedAt != 0 && now - m.dwRefusedAt < PLAYERBOT_MARBLE_FIRST_REFUSED_MS)
			return true;
		return item && m.dwFailItem == item->GetID() && m.iFailStreak >= PLAYERBOT_MARBLE_FIRST_FAIL_STREAK &&
				now - m.dwFailAt < PLAYERBOT_MARBLE_FIRST_FAIL_MS;
	}

	// The gate: may an ordinary change (71084) go on this worn piece of this many lines now?
	bool IsPlayerBotMarbleFirstChangeAllowed(LPCHARACTER ch, LPITEM item, int lines, bool lineRolls)
	{
		if (!ch || !item || !IsPlayerBotMarbleFirstFor(ch))
			return true;
		TPlayerBotMarbleFirstStats& s = s_kPlayerBotMarbleFirstStats;
		if (lines >= GetPlayerBotMarbleFirstMinLines())
			return true;
		// short of four and a line can still land: the adds first, never a change
		if (lines < PLAYERBOT_BONUS_MAX_LINES && lineRolls)
		{
			++s.blockLow;
			return false;
		}
		if (!IsPlayerBotMarbleFirstFallback4On())
		{
			++s.blockFallbackOff;
			return false;
		}
		if (!IsPlayerBotMarbleFirstMarbleOut(ch, item, lineRolls))
		{
			++s.blockWait;
			return false;
		}
		if (!IsPlayerBotMarbleFirstUrgent(ch))
		{
			++s.blockNotUrgent;
			return false;
		}
		++s.fallback4;
		PlayerBotLogThrottled("marble_first_fallback4", get_dword_time(),
				"PLAYERBOT_MARBLE_FIRST: fallback4 pid=%u name=%s vnum=%u lines=%d rolls=%d marble_held=%d",
				ch->GetPlayerID(), ch->GetName(), item->GetVnum(), lines, lineRolls ? 1 : 0,
				FindPlayerBotBlessingMarbleCell(ch) >= 0 ? 1 : 0);
		return true;
	}

	int GetPlayerBotMarbleFirstElement(LPCHARACTER ch)
	{
#if defined(MT2009_PLUS_BOT_BONUS67_V1) && defined(MT2009_PLUS_BOT_USE_SHOP_AIDS_V1) && defined(MT2009_PLUS_BOT_SEONHAE_V2)
		TPlayerBotMarbleFirst& m = s_mapPlayerBotMarbleFirst[ch->GetPlayerID()];
		const DWORD now = get_dword_time();
		if (m.dwElementAt == 0 || now - m.dwElementAt >= PLAYERBOT_MARBLE_FIRST_ELEMENT_MS)
		{
			m.dwElementAt = now ? now : 1;
			m.iElement = GetPlayerBotBonus67Element(ch);
		}
		return m.iElement;
#else
		return -1;
#endif
	}

	// A piece of the 6/7 scope (whatever the bot's level: it is made ready for the stage).
	bool IsPlayerBotMarbleFirstPriority(LPCHARACTER ch, LPITEM item)
	{
#if defined(MT2009_PLUS_BOT_BONUS67_V1) && defined(MT2009_PLUS_BOT_USE_SHOP_AIDS_V1) && defined(MT2009_PLUS_BOT_SEONHAE_V2)
		if (!ch || !item)
			return false;
		return GetPlayerBotBonus67Scope(ch, item, GetPlayerBotMarbleFirstElement(ch)) != B67_SCOPE_NONE;
#else
		return false;
#endif
	}

	// The shared signal: a worn piece of four lines that waits for the marble's fifth.
	bool PlayerBotPieceWantsFifth(LPCHARACTER ch, LPITEM item)
	{
		return ch && item && IsPlayerBotMarbleFirstFor(ch) && item->GetAttributeCount() == PLAYERBOT_BONUS_MAX_LINES &&
				CanPlayerBotTakeBonusStone(item) && CanPlayerBotItemRollNewLine(item);
	}

	void NotePlayerBotMarbleFirstShop(LPCHARACTER ch, int wanted, int got)
	{
		if (!ch)
			return;
		TPlayerBotMarbleFirstStats& s = s_kPlayerBotMarbleFirstStats;
		++s.shopGoals;
		s.shopWanted += (unsigned int)std::max(0, wanted);
		s.shopBought += (unsigned int)std::max(0, got);
		TPlayerBotMarbleFirst& m = s_mapPlayerBotMarbleFirst[ch->GetPlayerID()];
		if (got > 0)
			m.dwRefusedAt = 0;
		else
		{
			++s.shopRefused;
			const DWORD now = get_dword_time();
			m.dwRefusedAt = now ? now : 1;
		}
	}

	void NotePlayerBotMarbleFirstUsed(LPCHARACTER ch, LPITEM item, bool won)
	{
		if (!ch || !item)
			return;
		TPlayerBotMarbleFirstStats& s = s_kPlayerBotMarbleFirstStats;
		++s.used;
		++(won ? s.won : s.lost);
		if (IsPlayerBotMarbleFirstPriority(ch, item))
			++s.usedPriority;
		TPlayerBotMarbleFirst& m = s_mapPlayerBotMarbleFirst[ch->GetPlayerID()];
		if (won)
		{
			m.iFailStreak = 0;
			m.dwFailItem = 0;
			return;
		}
		if (m.dwFailItem != item->GetID())
		{
			m.dwFailItem = item->GetID();
			m.iFailStreak = 0;
		}
		++m.iFailStreak;
		const DWORD now = get_dword_time();
		m.dwFailAt = now ? now : 1;
	}

	void NotePlayerBotMarbleFirstChange(LPCHARACTER ch, int lines)
	{
		if (!ch)
			return;
		const int sm = PlayerBotMarbleFirstHasSm(ch) ? 1 : 0;
		const int bucket = lines >= PLAYERBOT_BONUS_MARBLE_LINES ? 0 : (lines == PLAYERBOT_BONUS_MAX_LINES ? 1 : 2);
		++s_kPlayerBotMarbleFirstStats.changes[sm][bucket];
	}

	void LogPlayerBotMarbleFirstCensus(DWORD dwNow)
	{
		if (s_dwPlayerBotMarbleFirstCensusAt != 0 && (int)(dwNow - s_dwPlayerBotMarbleFirstCensusAt) < 0)
			return;
		const bool first = s_dwPlayerBotMarbleFirstCensusAt == 0;
		s_dwPlayerBotMarbleFirstCensusAt = dwNow + PLAYERBOT_MARBLE_FIRST_CENSUS_MS;
		if (first)
			return;
		// the worn pieces of the 6/7 scope and their lines: the stage's bots (75+) and the bots under it
		unsigned int bots = 0, smBots = 0, stagePieces = 0, stageFive = 0, stageFour = 0, stageLow = 0;
		unsigned int prePieces = 0, preFour = 0, preLow = 0;
#if defined(MT2009_PLUS_BOT_BONUS67_V1) && defined(MT2009_PLUS_BOT_USE_SHOP_AIDS_V1) && defined(MT2009_PLUS_BOT_SEONHAE_V2)
		static const BYTE s_wears[] = { WEAR_BODY, WEAR_HEAD, WEAR_SHIELD, WEAR_NECK, WEAR_WRIST, WEAR_EAR, WEAR_FOOTS };
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !ch->IsPC() || !ch->IsItemLoaded() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
				continue;
			++bots;
			if (PlayerBotMarbleFirstHasSm(ch))
				++smBots;
			const bool stage = IsPlayerBotBonus67Stage(ch);
			const int element = GetPlayerBotMarbleFirstElement(ch);
			for (size_t i = 0; i < sizeof(s_wears) / sizeof(s_wears[0]); ++i)
			{
				LPITEM item = ch->GetWear(s_wears[i]);
				if (!item || GetPlayerBotBonus67Scope(ch, item, element) == B67_SCOPE_NONE)
					continue;
				const int lines = item->GetAttributeCount();
				if (stage)
				{
					++stagePieces;
					if (lines >= PLAYERBOT_BONUS_MARBLE_LINES)
						++stageFive;
					else if (lines == PLAYERBOT_BONUS_MAX_LINES)
						++stageFour;
					else
						++stageLow;
				}
				else
				{
					++prePieces;
					if (lines == PLAYERBOT_BONUS_MAX_LINES)
						++preFour;
					else if (lines < PLAYERBOT_BONUS_MAX_LINES)
						++preLow;
				}
			}
		}
#endif
		const int stageUnder = (int)(stageFour + stageLow);
		const int preUnder = (int)(preFour + preLow);
		const int stageTrend = s_iPlayerBotMarbleFirstLastStageUnder < 0 ? 0 : stageUnder - s_iPlayerBotMarbleFirstLastStageUnder;
		const int preTrend = s_iPlayerBotMarbleFirstLastPreUnder < 0 ? 0 : preUnder - s_iPlayerBotMarbleFirstLastPreUnder;
		s_iPlayerBotMarbleFirstLastStageUnder = stageUnder;
		s_iPlayerBotMarbleFirstLastPreUnder = preUnder;
		const TPlayerBotMarbleFirstStats& s = s_kPlayerBotMarbleFirstStats;
		sys_log(0, "PLAYERBOT_MARBLE_FIRST: census on=%d min_lines=%d fallback4=%d bots=%u sm_bots=%u marbles goals=%u wanted=%u "
				"bought=%u refused=%u used=%u won=%u lost=%u on_scope=%u changes sm=[5:%u 4:%u le3:%u] no_sm=[5:%u 4:%u le3:%u] "
				"gate block_low=%u wait_marble=%u not_urgent=%u fallback_off=%u fallback4=%u",
				GetPlayerBotMarbleFirstFlag(PLAYERBOT_MARBLE_FIRST_OFF_FLAG) == 0 ? 1 : 0, GetPlayerBotMarbleFirstMinLines(),
				IsPlayerBotMarbleFirstFallback4On() ? 1 : 0, bots, smBots, s.shopGoals, s.shopWanted, s.shopBought,
				s.shopRefused, s.used, s.won, s.lost, s.usedPriority, s.changes[1][0], s.changes[1][1], s.changes[1][2],
				s.changes[0][0], s.changes[0][1], s.changes[0][2], s.blockLow, s.blockWait, s.blockNotUrgent,
				s.blockFallbackOff, s.fallback4);
		sys_log(0, "PLAYERBOT_MARBLE_FIRST: census scope stage=%u five=%u four=%u le3=%u under_five=%d (%+d) pre_stage=%u four=%u "
				"le3=%u under_five=%d (%+d)",
				stagePieces, stageFive, stageFour, stageLow, stageUnder, stageTrend, prePieces, preFour, preLow, preUnder,
				preTrend);
	}
}

#endif

#endif
