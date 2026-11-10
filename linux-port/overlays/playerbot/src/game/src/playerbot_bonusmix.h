#ifndef __INC_METIN2_PLAYERBOT_BONUSMIX_H__
#define __INC_METIN2_PLAYERBOT_BONUSMIX_H__

// MT2009_PLUS_BOT_BONUSMIX_V1 - a 75+ bot mixes its bonuses by what it needs, keeps a reserve, and mixes in the field
// (the owner, 10 November 2026: "ogarnij to, zeby bot wiedzial, czy ma jeszcze zapas na jakies bonusy czy nie, czy
// miksowac dalej czy nie. Na przyklad moze zrobic probe, czy 15% odpornosci na blyskawice wystarczy, czy musi wymiksowac
// 15% odpornosci na blyskawice i 1000 max PZ w zbroi. Miksowac rowniez moga na mapach, nie musza robic tego w M1.").
// The follow-up of MT2009_PLUS_BOT_BONUS75_V1 (playerbot_bonus75.h), whose fixed strong / fair targets made a bot reroll a
// piece towards "strong" and lose a good line it already had.
//
// 1. The need. Every slot of the bonus75 list (weapon, armour, helmet, shield, necklace, bracelet, earrings, boots) has a
//    ladder of four steps (PLAYERBOT_BONUSMIX_LADDER; the roles are bonus75's: must, the element E, wanted; a level is the
//    item_attr table's 1-5, the slot's own top counted as 5):
//      step 0  the map's minimum: the must line (or E on the armour / helmet / bracelet where E rolls) - e.g. the armour
//              on a lightning map: lightning resistance at its top (15%)
//      step 1  the minimum and one more: the armour E 15% + Max HP level 3+ (the owner's "15% + 1000 max PZ"); other
//              slots the must + one wanted line
//      step 2  about bonus75's fair target, step 3 about its strong one (the armour with E four lines)
//    A bot starts at step 0 (m2_bot_bonusmix_start_step); its armour starts at step 1 while the progression checklist
//    holds it for health (NEED_HP). E is bonus75's: the element of the bot's map, next map or Yohara hunt
//    (GetPlayerBotBonus75ElementPoint - the element progression's gate and prebuild, MT2009_PLUS_BOT_ELEMENT_PROGRESS_V1).
// 2. The try. Once no worn piece below its need can be mixed now (all met, or no change stone / budget left) and some
//    piece meets its need unlocked, the bot hunts on: the try runs m2_bot_bonusmix_try_min (40) minutes of real hunting
//    (alive, on a map outside the villages and instances, not fishing, not resting after a death), counting its kills,
//    deaths and HP retreats - the element progression's cope events (NotePlayerBotElementProgressKill / Death /
//    Retreat, any map, a party member's kill nearby counted too) and its thresholds: PLAYERBOT_EPROG_DEATHS (3) deaths
//    or PLAYERBOT_EPROG_RETREATS (8) retreats fail it at once; at the end, fewer kills than PLAYERBOT_EPROG_SLOW_KILLS
//    (25) per 30 minutes fail it as slow. Passed: every worn piece meeting its need is locked as enough (never changed
//    again while worn and E is the same element - the reserve) and the bot watches: the same counts in rolling windows of the try's length, a
//    failure there is judged as a failed try (a new map that is too hard). Failed: one slot's need goes one step up -
//    deaths / retreats the defence slots (armour, bracelet, helmet, boots, shield, necklace - the E pieces first), slow
//    kills the attack ones (weapon, necklace, earrings, boots), the lowest step of them; that slot's lock is dropped and
//    the bot mixes again to the new step, then tries again. All at step 3: "maxed" (logged, counted).
// 3. The protection. A piece meeting its need (or locked) is never rerolled - the ordinary pass's verdict says no, the
//    Yohara pass counts it strong and out of its element phase. Of the pieces below their need one only is mixed: the
//    lowest risk - the fewest and weakest useful lines (must / E lines 4 a level, wanted 2, others 1), a marble-first
//    piece short of five lines last. A below-need piece with a high line (HasPlayerBotProtectedBonusLine: a top roll,
//    a strong PvP line near its top) is held - not mixed - unless its slot's need was raised by a failed try or its E
//    line is short of the step (the map's own requirement). The ordinary pass keeps bonus75's change budget per piece.
// 4. In the field. ManagePlayerBotFieldBonus refused while the action was FIGHT - which stays set through a whole hunt
//    (the next target is taken before the action changes) - so the passes ran at the blacksmith's in town and in
//    looting gaps. Now it runs when it is safe: no living target and no living victim, HP over m2_bot_bonusmix_field_hp
//    (60) per cent, no monster with the bot as its victim within the held-scan range (FindPlayerBotHoldingMonster), not
//    luring, plus the old gates (no shop, no retreat, not after a death, the equip window). The stones need no NPC
//    (the engine's item path); the refiner exchange and the refining stay where they were. The ItemShop V3 purchases run
//    on every map already (ManagePlayerBotItemShop, the general tick).
// 5. Unchanged: the element shop's pinned pieces, marble-first (a change on a five-line piece of a bot with SM; the
//    marble and the adds first), the 6/7 pass, bonus75's scroll-refine rule, the adds (they lose nothing).
// 6. The census every 10 minutes, PLAYERBOT_BONUSMIX: the 75+ bots by phase, the steps per slot, the pieces locked /
//    meeting / below their need, the pieces the old strong target would still reroll that the need keeps (reserve_kept),
//    the below-need pieces held for a high line, and since start: tries started / passed / failed by cause, the raises
//    per slot, maxed, locks, the changes in the field and in town (ordinary / Yohara).
//
// Flags: m2_bot_bonusmix_off 1 - all off (bonus75's strong / fair targets, the old field gate); m2_bot_bonusmix_field_off
// 1 - the old field gate only; m2_bot_bonusmix_try_min N (10-180, default 40) - the try's minutes of hunting;
// m2_bot_bonusmix_field_hp N (30-95, default 60); m2_bot_bonusmix_start_step N (1-3: the start step; 0 - step 0).
//
// An implementation fragment: include it once, from playerbot_manager.cpp, right after playerbot_bonus75.h; the
// declarations the earlier files ask are in playerbot_types.h.

#if defined(PLAYERBOT_ENGINE_MT2009) && defined(MT2009_PLUS_BOT_BONUSMIX_V1) && defined(MT2009_PLUS_BOT_BONUS75_V1)

namespace
{
	const char* const PLAYERBOT_BONUSMIX_OFF_FLAG = "m2_bot_bonusmix_off";
	const char* const PLAYERBOT_BONUSMIX_FIELD_OFF_FLAG = "m2_bot_bonusmix_field_off";
	const char* const PLAYERBOT_BONUSMIX_TRY_MIN_FLAG = "m2_bot_bonusmix_try_min";
	const char* const PLAYERBOT_BONUSMIX_FIELD_HP_FLAG = "m2_bot_bonusmix_field_hp";
	const char* const PLAYERBOT_BONUSMIX_START_STEP_FLAG = "m2_bot_bonusmix_start_step";
	const int PLAYERBOT_BONUSMIX_TRY_MIN = 40;
	const int PLAYERBOT_BONUSMIX_FIELD_HP = 60;
	const int PLAYERBOT_BONUSMIX_STEPS = 4;
	const DWORD PLAYERBOT_BONUSMIX_LOOK_MS = 30 * 1000;
	const DWORD PLAYERBOT_BONUSMIX_TICK_GAP_MS = 10 * 1000;	// a longer gap between two ticks is no hunting time
	const DWORD PLAYERBOT_BONUSMIX_FIELD_RETRY_MS = 3000;
	// a below-need piece with no change on any piece this long (no share or budget left, no window) counts as settled
	const DWORD PLAYERBOT_BONUSMIX_STALL_MS = 15 * 60 * 1000;
	const DWORD PLAYERBOT_BONUSMIX_CENSUS_MS = 10 * 60 * 1000;
	const int PLAYERBOT_BONUSMIX_PROTECT_LOSS = 20;
	const int PLAYERBOT_BONUSMIX_PARTY_KILL_RANGE = 5000;

	// One step of a slot's need: this many useful lines (never more than can roll on the piece), the must line at
	// mustLevel or more (0: not asked), the wanted lines at otherLevel or more, E at eLevel or more (0: not asked).
	struct TPlayerBotBonusMixNeed
	{
		int lines;
		int mustLevel;
		int otherLevel;
		int eLevel;
	};

	// [bonus75 slot][0 without E, 1 with E on the piece][step] - PLAYERBOT_BONUS75_SLOTS' order.
	const TPlayerBotBonusMixNeed PLAYERBOT_BONUSMIX_LADDER[8][2][PLAYERBOT_BONUSMIX_STEPS] = {
		// weapon: strong vs devils, then critical / piercing / the class stat...
		{ { { 1, 3, 0, 0 }, { 2, 3, 3, 0 }, { 2, 4, 3, 0 }, { 3, 4, 3, 0 } },
		  { { 1, 3, 0, 0 }, { 2, 3, 3, 0 }, { 2, 4, 3, 0 }, { 3, 4, 3, 0 } } },
		// armour: Max HP (E: E 15% first, then + HP 1000, ...)
		{ { { 1, 3, 0, 0 }, { 1, 4, 0, 0 }, { 3, 3, 2, 0 }, { 4, 4, 3, 0 } },
		  { { 1, 0, 0, 5 }, { 2, 3, 0, 5 }, { 3, 4, 3, 5 }, { 4, 4, 3, 5 } } },
		// helmet: the defence lines (E: E 10%, then 15%, then + defence)
		{ { { 1, 0, 3, 0 }, { 2, 0, 3, 0 }, { 3, 0, 3, 0 }, { 4, 0, 3, 0 } },
		  { { 1, 0, 0, 4 }, { 1, 0, 0, 5 }, { 2, 0, 3, 5 }, { 3, 0, 3, 5 } } },
		// shield: the stun immunity, then vitality / block / reflection...
		{ { { 1, 5, 0, 0 }, { 2, 5, 2, 0 }, { 2, 5, 3, 0 }, { 3, 5, 3, 0 } },
		  { { 1, 5, 0, 0 }, { 2, 5, 2, 0 }, { 2, 5, 3, 0 }, { 3, 5, 3, 0 } } },
		// necklace: critical, then Max HP / piercing
		{ { { 1, 3, 0, 0 }, { 2, 3, 3, 0 }, { 2, 4, 3, 0 }, { 3, 4, 3, 0 } },
		  { { 1, 3, 0, 0 }, { 2, 3, 3, 0 }, { 2, 4, 3, 0 }, { 3, 4, 3, 0 } } },
		// bracelet: Max HP (E: E 10%, then + HP, then E 15% + HP level 4, ...)
		{ { { 1, 3, 0, 0 }, { 2, 3, 3, 0 }, { 2, 4, 3, 0 }, { 3, 4, 3, 0 } },
		  { { 1, 0, 0, 4 }, { 2, 3, 0, 4 }, { 2, 4, 0, 5 }, { 3, 4, 3, 5 } } },
		// earrings: strong vs devils, then movement / drop / humans
		{ { { 1, 3, 0, 0 }, { 2, 3, 3, 0 }, { 2, 4, 3, 0 }, { 3, 4, 3, 0 } },
		  { { 1, 3, 0, 0 }, { 2, 3, 3, 0 }, { 2, 4, 3, 0 }, { 3, 4, 3, 0 } } },
		// boots: Max HP, then critical / attack speed / dodge / movement
		{ { { 1, 3, 0, 0 }, { 2, 3, 3, 0 }, { 2, 4, 3, 0 }, { 3, 4, 3, 0 } },
		  { { 1, 3, 0, 0 }, { 2, 3, 3, 0 }, { 2, 4, 3, 0 }, { 3, 4, 3, 0 } } },
	};

	// the slots a failed try raises: deaths / retreats (the defence, the E pieces first) and slow kills (the attack)
	const int PLAYERBOT_BONUSMIX_DEFENCE_ORDER[] = { 1, 5, 2, 7, 3, 4 };	// body, wrist, head, foots, shield, neck
	const int PLAYERBOT_BONUSMIX_ATTACK_ORDER[] = { 0, 4, 6, 7 };		// weapon, neck, ear, foots

	enum { PLAYERBOT_BONUSMIX_PHASE_MIX = 0, PLAYERBOT_BONUSMIX_PHASE_TRY, PLAYERBOT_BONUSMIX_PHASE_WATCH,
		PLAYERBOT_BONUSMIX_PHASES };
	const char* const PLAYERBOT_BONUSMIX_PHASE_NAMES[PLAYERBOT_BONUSMIX_PHASES] = { "mix", "try", "watch" };
	enum { PLAYERBOT_BONUSMIX_FAIL_DEATHS = 0, PLAYERBOT_BONUSMIX_FAIL_RETREATS, PLAYERBOT_BONUSMIX_FAIL_SLOW,
		PLAYERBOT_BONUSMIX_FAILS };
	const char* const PLAYERBOT_BONUSMIX_FAIL_NAMES[PLAYERBOT_BONUSMIX_FAILS] = { "deaths", "hp_retreats", "slow_kills" };

	struct TPlayerBotBonusMixBot
	{
		int step[8];
		unsigned int raised;	// the slots a failed try raised (their high lines may go)
		DWORD locked[8];	// the item locked as enough per slot (0 none)
		BYTE lockedElem[8];	// the element the lock was judged for (another element needed: the lock no longer holds)
		int phase;
		DWORD huntMs, lastTick, nextLook;
		DWORD mixSince, lastChange;
		DWORD focusItem;	// the below-need piece being mixed: kept until it meets its need (no hopping between pieces)	// the mix phase's start, the bot's last change - a mix that stalls is settled
		unsigned int kills, deaths, retreats;
		long lMap;
		unsigned int tries, fails;
		TPlayerBotBonusMixBot() { memset(this, 0, sizeof(*this)); }
	};
	std::map<DWORD, TPlayerBotBonusMixBot> s_mapPlayerBotBonusMix;

	struct TPlayerBotBonusMixStats
	{
		unsigned int tries, passes, fails[PLAYERBOT_BONUSMIX_FAILS], watchFails, maxed, locks;
		unsigned int raises[8];
		unsigned int changesField[2], changesTown[2];	// [0 ordinary, 1 Yohara]
		unsigned int fieldPasses, fieldUnsafe;
		TPlayerBotBonusMixStats() { memset(this, 0, sizeof(*this)); }
	};
	TPlayerBotBonusMixStats s_kPlayerBotBonusMixStats;
	DWORD s_dwPlayerBotBonusMixCensusAt = 0;
	// the Yohara pass's pick in progress: the bot and the slot its below-need change may go on (-1 none)
	DWORD s_dwPlayerBotBonusMixPickPid = 0;
	int s_iPlayerBotBonusMixPickSlot = -1;

	int GetPlayerBotBonusMixFlag(const char* flag)
	{
		return quest::CQuestManager::instance().GetEventFlag(flag);
	}

	bool IsPlayerBotBonusMixOn()
	{
		return GetPlayerBotBonusMixFlag(PLAYERBOT_BONUSMIX_OFF_FLAG) == 0;
	}

	bool IsPlayerBotBonusMixStage(LPCHARACTER ch)
	{
		return IsPlayerBotBonusMixOn() && IsPlayerBotBonus75Stage(ch);
	}

	DWORD GetPlayerBotBonusMixTryMs()
	{
		const int v = GetPlayerBotBonusMixFlag(PLAYERBOT_BONUSMIX_TRY_MIN_FLAG);
		const int min = v >= 10 && v <= 180 ? v : PLAYERBOT_BONUSMIX_TRY_MIN;
		return (DWORD)min * 60U * 1000U;
	}

	int GetPlayerBotBonusMixFieldHp()
	{
		const int v = GetPlayerBotBonusMixFlag(PLAYERBOT_BONUSMIX_FIELD_HP_FLAG);
		return v >= 30 && v <= 95 ? v : PLAYERBOT_BONUSMIX_FIELD_HP;
	}

	TPlayerBotBonusMixBot& TouchPlayerBotBonusMix(LPCHARACTER ch)
	{
		std::map<DWORD, TPlayerBotBonusMixBot>::iterator it = s_mapPlayerBotBonusMix.find(ch->GetPlayerID());
		if (it != s_mapPlayerBotBonusMix.end())
			return it->second;
		TPlayerBotBonusMixBot& r = s_mapPlayerBotBonusMix[ch->GetPlayerID()];
		const int start = GetPlayerBotBonusMixFlag(PLAYERBOT_BONUSMIX_START_STEP_FLAG);
		for (int s = 0; s < 8; ++s)
			r.step[s] = start >= 1 && start < PLAYERBOT_BONUSMIX_STEPS ? start : 0;
		return r;
	}

	// The slot's step now: the bot's, the armour at least 1 while the checklist holds the bot for health.
	int GetPlayerBotBonusMixStep(LPCHARACTER ch, const TPlayerBotBonusMixBot& r, int s)
	{
		int step = r.step[s];
		if (PLAYERBOT_BONUS75_SLOTS[s].bWearCell == WEAR_BODY &&
				(GetPlayerBotProgressionNeeds(ch->GetPlayerID()) & playerbot_progression::NEED_HP) != 0)
			step = std::max(step, 1);
		return std::max(0, std::min(step, PLAYERBOT_BONUSMIX_STEPS - 1));
	}

	bool IsPlayerBotBonusMixLocked(const TPlayerBotBonusMixBot& r, int s, LPITEM item, BYTE elem)
	{
		return item && r.locked[s] != 0 && r.locked[s] == item->GetID() && r.lockedElem[s] == elem;
	}

	struct TPlayerBotBonusMixRead
	{
		bool e;			// E rolls on the piece (a must of it)
		bool met;		// the piece meets the step
		bool eShort;		// E asked by the step and short
		bool highLine;		// a protected high line (HasPlayerBotProtectedBonusLine)
		int lines;
		int loss;		// what a change could lose
	};

	// The piece against a step of its slot's ladder.
	void ReadPlayerBotBonusMixPiece(LPCHARACTER ch, LPITEM item, int s, BYTE elem, int step, TPlayerBotBonusMixRead& out)
	{
		using namespace playerbot_yohara_bonus_rules;
		memset(&out, 0, sizeof(out));
		const BYTE wearCell = PLAYERBOT_BONUS75_SLOTS[s].bWearCell;
		const bool addonWeapon = wearCell == WEAR_WEAPON && HasPlayerBotDamageAddon(item);
		const bool e = elem != 0 && (wearCell == WEAR_BODY || wearCell == WEAR_HEAD || wearCell == WEAR_WRIST) &&
				GetPlayerBotYoharaBonusSlotMaxLevel(item, elem) > 0;
		const TPlayerBotBonusMixNeed& need = PLAYERBOT_BONUSMIX_LADDER[s][e ? 1 : 0][std::max(0, std::min(step,
				PLAYERBOT_BONUSMIX_STEPS - 1))];
		out.e = e;
		// what can roll on the piece: the list's kinds, whether a must (other than E) is among them
		int available = 0;
		bool mustRolls = false;
		for (TItemAttrMap::const_iterator it = g_map_itemAttr.begin(); it != g_map_itemAttr.end(); ++it)
		{
			const WORD type = (WORD)it->first;
			if (GetPlayerBotYoharaBonusSlotMaxLevel(item, type) <= 0)
				continue;
			if (e && type == elem)
			{
				++available;
				continue;
			}
			const int role = GetPlayerBotBonus75RoleFor(ch, wearCell, type, addonWeapon, elem);
			if (role <= ROLE_OTHER)
				continue;
			++available;
			if (role == ROLE_MUST)
				mustRolls = true;
		}
		if (addonWeapon)
			++available;
		const int otherLevel = std::max(1, need.otherLevel);
		int eLevel = 0, mustLevel = 0, useful = 0;
		for (int i = 0; i < PLAYERBOT_BONUS_MARBLE_LINES && i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
		{
			const WORD type = item->GetAttributeType(i); // MT2009_PLUS_WIDE_ATTR_V1
			const long value = item->GetAttributeValue(i);
			if (type == 0 || value <= 0)
				continue;
			++out.lines;
			const int level = GetPlayerBotYoharaBonusLineLevel(item, type, value);
			if (e && type == elem)
			{
				eLevel = std::max(eLevel, level);
				out.loss += level * 4;
				if (level >= (need.eLevel > 0 ? need.eLevel : otherLevel))
					++useful;
				continue;
			}
			const int role = GetPlayerBotBonus75RoleFor(ch, wearCell, type, addonWeapon, elem);
			if (role == ROLE_MUST || role == ROLE_MUST2)
			{
				mustLevel = std::max(mustLevel, level);
				out.loss += level * 4;
				if (level >= (need.mustLevel > 0 ? need.mustLevel : otherLevel))
					++useful;
			}
			else if (role == ROLE_WANTED)
			{
				out.loss += level * 2;
				if (level >= otherLevel)
					++useful;
			}
			else
				out.loss += level;
		}
		const bool eOk = need.eLevel <= 0 || !e || eLevel >= need.eLevel;
		const bool mustOk = need.mustLevel <= 0 || !mustRolls || mustLevel >= need.mustLevel;
		const int wantLines = std::min(need.lines, available);
		out.eShort = e && need.eLevel > 0 && eLevel < need.eLevel;
		out.met = out.lines > 0 && eOk && mustOk && useful >= wantLines;
		// a weapon finished by the old rule (its average 30+, a big skill line) is never mixed off (bonus75's own rule)
		if (!out.met && wearCell == WEAR_WEAPON && HasPlayerBotFinishedBonus(ch, item, WEAR_WEAPON))
			out.met = true;
		out.highLine = HasPlayerBotProtectedBonusLine(ch, item);
		if (out.highLine)
			out.loss += PLAYERBOT_BONUSMIX_PROTECT_LOSS;
	}

	// A worn piece this rule may weigh at all.
	bool IsPlayerBotBonusMixPiece(LPCHARACTER ch, LPITEM item)
	{
		return item && CanPlayerBotTakeBonusStone(item) && !IsPlayerBotSidekickPinned(ch, item);
	}

	// -1 not this rule's, 0 the piece meets its need (or is locked as enough), 1 below its need.
	int GetPlayerBotBonusMixPieceState(LPCHARACTER ch, LPITEM item, BYTE wearCell)
	{
		if (!ch || !item || !IsPlayerBotBonusMixStage(ch))
			return -1;
		// the piece may be off the body for its stones right now (both passes take it off): the caller says it is worn
		const int s = FindPlayerBotBonus75Slot(wearCell);
		if (s < 0)
			return -1;
		TPlayerBotBonusMixBot& r = TouchPlayerBotBonusMix(ch);
		const BYTE elem = GetPlayerBotBonus75ElementPoint(ch);
		if (IsPlayerBotBonusMixLocked(r, s, item, elem))
			return 0;
		TPlayerBotBonusMixRead rd;
		ReadPlayerBotBonusMixPiece(ch, item, s, elem, GetPlayerBotBonusMixStep(ch, r, s), rd);
		return rd.met ? 0 : 1;
	}

	// May the high lines of a below-need piece go? Only when a failed try raised its slot or its E is short of the step.
	bool IsPlayerBotBonusMixHeld(const TPlayerBotBonusMixBot& r, int s, const TPlayerBotBonusMixRead& rd)
	{
		return rd.highLine && (r.raised & (1U << s)) == 0 && !rd.eShort;
	}

	// The one below-need worn piece a change may go on: the lowest risk (bonus75 slot index), -1 none. yohara: the
	// Yohara pass (its own shares, no bonus75 budget); excludeMask: slots its pick could not change; inHand / inHandWear:
	// the worn piece the pass has taken off for its stones (its slot is empty meanwhile).
	int GetPlayerBotBonusMixChosenSlot(LPCHARACTER ch, bool yohara, unsigned int excludeMask, LPITEM inHand, BYTE inHandWear)
	{
		if (!ch || !IsPlayerBotBonusMixStage(ch))
			return -1;
		TPlayerBotBonusMixBot& r = TouchPlayerBotBonusMix(ch);
		const BYTE elem = GetPlayerBotBonus75ElementPoint(ch);
		const bool marbleFirst = IsPlayerBotMarbleFirstFor(ch);
		int best = -1;
		long bestKey = 0;
		DWORD bestItem = 0;
		for (int s = 0; s < PLAYERBOT_BONUS75_SLOT_COUNT; ++s)
		{
			if (excludeMask & (1U << s))
				continue;
			const BYTE wearCell = PLAYERBOT_BONUS75_SLOTS[s].bWearCell;
			LPITEM item = ch->GetWear(wearCell);
			if (!item && inHand && inHandWear == wearCell)
				item = inHand;
			if (!IsPlayerBotBonusMixPiece(ch, item) || item->GetAttributeCount() <= 0 ||
					IsPlayerBotBonusMixLocked(r, s, item, elem))
				continue;
			if (!yohara && (IsPlayerBotElementShopPinnedPiece(ch, item) || IsPlayerBotSpecialLevel30WeaponVnum(item->GetVnum())))
				continue;
			TPlayerBotBonusMixRead rd;
			ReadPlayerBotBonusMixPiece(ch, item, s, elem, GetPlayerBotBonusMixStep(ch, r, s), rd);
			if (rd.met || IsPlayerBotBonusMixHeld(r, s, rd))
				continue;
			if (!yohara && GetPlayerBotBonus75Spent(ch, item) >= GetPlayerBotBonus75Cap(s, rd.e))
				continue;
			// marble-first: a piece short of its five lines takes the marble before a change - last in the order
			const bool lineRolls = rd.lines < PLAYERBOT_BONUS_MARBLE_LINES && CanPlayerBotItemRollNewLine(item);
			const bool shortOfFive = marbleFirst && rd.lines < GetPlayerBotMarbleFirstMinLines() && lineRolls;
			const long key = item->GetID() == r.focusItem ? -1L : (shortOfFive ? 100000L : 0L) + rd.loss * 10L + rd.lines;
			if (best < 0 || key < bestKey)
			{
				best = s;
				bestKey = key;
				bestItem = item->GetID();
			}
		}
		r.focusItem = bestItem;
		return best;
	}

	// The ordinary pass's answer for a worn piece of a 75+ bot: -1 not this rule's (bonus75 decides), 0 no change, 1 a
	// change (the chosen below-need piece within bonus75's budget).
	int GetPlayerBotBonusMixChangeVerdict(LPCHARACTER ch, LPITEM item, BYTE wearCell)
	{
		if (!ch || !item || !IsPlayerBotBonusMixStage(ch) || IsPlayerBotYoharaBonusMember(ch) ||
				IsPlayerBotSpecialLevel30WeaponVnum(item->GetVnum()))
			return -1;
		const int state = GetPlayerBotBonusMixPieceState(ch, item, wearCell);
		if (state <= 0)
			return state;
		return GetPlayerBotBonusMixChosenSlot(ch, false, 0, item, wearCell) == FindPlayerBotBonus75Slot(wearCell) ? 1 : 0;
	}

	void SetPlayerBotBonusMixYoharaPick(LPCHARACTER ch, int chosenSlot)
	{
		s_dwPlayerBotBonusMixPickPid = ch ? ch->GetPlayerID() : 0;
		s_iPlayerBotBonusMixPickSlot = ch ? chosenSlot : -1;
	}

	// The Yohara pass's pick in progress lets a change on this below-need piece (no pick in progress: no restriction).
	bool IsPlayerBotBonusMixYoharaPicked(LPCHARACTER ch, BYTE wearCell)
	{
		if (!ch || s_dwPlayerBotBonusMixPickPid != ch->GetPlayerID())
			return true;
		return s_iPlayerBotBonusMixPickSlot >= 0 && FindPlayerBotBonus75Slot(wearCell) == s_iPlayerBotBonusMixPickSlot;
	}

	// A change on a worn piece of a 75+ bot (from NotePlayerBotBonus75Change): where it was made.
	void NotePlayerBotBonusMixChange(LPCHARACTER ch, bool yohara)
	{
		if (!ch || !IsPlayerBotBonusMixOn())
			return;
		std::map<DWORD, TPlayerBotBonusMixBot>::iterator it = s_mapPlayerBotBonusMix.find(ch->GetPlayerID());
		if (it != s_mapPlayerBotBonusMix.end())
			it->second.lastChange = get_dword_time() ? get_dword_time() : 1;
		if (IsPlayerBotVillageMap(ch->GetMapIndex()))
			++s_kPlayerBotBonusMixStats.changesTown[yohara ? 1 : 0];
		else
			++s_kPlayerBotBonusMixStats.changesField[yohara ? 1 : 0];
	}

	// The ground a try counts on: a hunting map (no village, no instance).
	bool IsPlayerBotBonusMixGround(LPCHARACTER ch)
	{
		return ch && !IsPlayerBotVillageMap(ch->GetMapIndex()) && ch->GetMapIndex() < PLAYERBOT_INSTANCE_MAP_INDEX_MIN;
	}

	void CountPlayerBotBonusMixEvent(LPCHARACTER ch, int kind)
	{
		std::map<DWORD, TPlayerBotBonusMixBot>::iterator it = s_mapPlayerBotBonusMix.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotBonusMix.end() || it->second.phase == PLAYERBOT_BONUSMIX_PHASE_MIX ||
				!IsPlayerBotBonusMixGround(ch))
			return;
		if (kind == PLAYERBOT_GATE_TRIAL_EV_KILL)
			++it->second.kills;
		else if (kind == PLAYERBOT_GATE_TRIAL_EV_DEATH)
			++it->second.deaths;
		else if (kind == PLAYERBOT_GATE_TRIAL_EV_RETREAT)
			++it->second.retreats;
	}

	// A party member's kill near the bot counts for it too (an assisting member lands few last hits).
	struct FPlayerBotBonusMixPartyKill
	{
		LPCHARACTER m_pKiller;
		FPlayerBotBonusMixPartyKill(LPCHARACTER killer) : m_pKiller(killer) {}
		void operator()(LPCHARACTER member)
		{
			if (!member || member == m_pKiller || member->GetMapIndex() != m_pKiller->GetMapIndex() ||
					DISTANCE_APPROX(member->GetX() - m_pKiller->GetX(), member->GetY() - m_pKiller->GetY()) >
						PLAYERBOT_BONUSMIX_PARTY_KILL_RANGE)
				return;
			CountPlayerBotBonusMixEvent(member, PLAYERBOT_GATE_TRIAL_EV_KILL);
		}
	};

	// The cope events (playerbot_element_maps.h: a kill, a death, an HP retreat on any map).
	void NotePlayerBotBonusMixEvent(LPCHARACTER ch, int kind, DWORD now)
	{
		(void)now;
		if (!ch || !ch->IsPC() || s_mapPlayerBotBonusMix.empty())
			return;
		CountPlayerBotBonusMixEvent(ch, kind);
		if (kind == PLAYERBOT_GATE_TRIAL_EV_KILL && ch->GetParty())
		{
			FPlayerBotBonusMixPartyKill f(ch);
			ch->GetParty()->ForEachOnMapMember(f, ch->GetMapIndex());
		}
	}

	void ResetPlayerBotBonusMixCounts(TPlayerBotBonusMixBot& r)
	{
		r.huntMs = 0;
		r.kills = r.deaths = r.retreats = 0;
	}

	void EnterPlayerBotBonusMixPhase(TPlayerBotBonusMixBot& r, int phase)
	{
		if (phase == PLAYERBOT_BONUSMIX_PHASE_MIX && r.phase != PLAYERBOT_BONUSMIX_PHASE_MIX)
			r.mixSince = get_dword_time() ? get_dword_time() : 1;
		r.phase = phase;
		ResetPlayerBotBonusMixCounts(r);
	}

	// The worn pieces: those meeting their need unlocked (the try's candidates), and the slots as text for the log.
	int CountPlayerBotBonusMixCandidates(LPCHARACTER ch, TPlayerBotBonusMixBot& r, std::string* desc)
	{
		const BYTE elem = GetPlayerBotBonus75ElementPoint(ch);
		int candidates = 0;
		char buf[48];
		for (int s = 0; s < PLAYERBOT_BONUS75_SLOT_COUNT; ++s)
		{
			LPITEM item = ch->GetWear(PLAYERBOT_BONUS75_SLOTS[s].bWearCell);
			if (!IsPlayerBotBonusMixPiece(ch, item))
				continue;
			const bool locked = IsPlayerBotBonusMixLocked(r, s, item, elem);
			const int step = GetPlayerBotBonusMixStep(ch, r, s);
			TPlayerBotBonusMixRead rd;
			ReadPlayerBotBonusMixPiece(ch, item, s, elem, step, rd);
			if (rd.met && !locked)
				++candidates;
			if (desc)
			{
				snprintf(buf, sizeof(buf), "%s%s:s%d%c", desc->empty() ? "" : " ", PLAYERBOT_BONUS75_SLOTS[s].szName, step,
						locked ? 'L' : (rd.met ? 'M' : (IsPlayerBotBonusMixHeld(r, s, rd) ? 'H' : '-')));
				*desc += buf;
			}
		}
		return candidates;
	}

	// A passed try: every worn piece meeting its need is locked as enough.
	void PassPlayerBotBonusMixTry(LPCHARACTER ch, TPlayerBotBonusMixBot& r)
	{
		const BYTE elem = GetPlayerBotBonus75ElementPoint(ch);
		int locks = 0;
		for (int s = 0; s < PLAYERBOT_BONUS75_SLOT_COUNT; ++s)
		{
			LPITEM item = ch->GetWear(PLAYERBOT_BONUS75_SLOTS[s].bWearCell);
			if (!IsPlayerBotBonusMixPiece(ch, item) || IsPlayerBotBonusMixLocked(r, s, item, elem))
				continue;
			TPlayerBotBonusMixRead rd;
			ReadPlayerBotBonusMixPiece(ch, item, s, elem, GetPlayerBotBonusMixStep(ch, r, s), rd);
			if (!rd.met)
				continue;
			r.locked[s] = item->GetID();
			r.lockedElem[s] = elem;
			++locks;
		}
		s_kPlayerBotBonusMixStats.locks += (unsigned int)locks;
		++s_kPlayerBotBonusMixStats.passes;
		std::string desc;
		CountPlayerBotBonusMixCandidates(ch, r, &desc);
		sys_log(0, "PLAYERBOT_BONUSMIX: try passed pid=%u name=%s lv=%d map=%ld hunt_min=%u kills=%u deaths=%u hp_retreats=%u "
				"locked=%d gear=[%s]",
				ch->GetPlayerID(), ch->GetName(), (int)ch->GetLevel(), r.lMap, (unsigned int)(r.huntMs / 60000U), r.kills,
				r.deaths, r.retreats, locks, desc.c_str());
		EnterPlayerBotBonusMixPhase(r, PLAYERBOT_BONUSMIX_PHASE_WATCH);
	}

	// A failed try (or a failure while watching): one slot's need a step up, its lock dropped.
	void FailPlayerBotBonusMixTry(LPCHARACTER ch, TPlayerBotBonusMixBot& r, int why)
	{
		const bool watch = r.phase == PLAYERBOT_BONUSMIX_PHASE_WATCH;
		const int* order = why == PLAYERBOT_BONUSMIX_FAIL_SLOW ? PLAYERBOT_BONUSMIX_ATTACK_ORDER : PLAYERBOT_BONUSMIX_DEFENCE_ORDER;
		const int count = why == PLAYERBOT_BONUSMIX_FAIL_SLOW
				? (int)(sizeof(PLAYERBOT_BONUSMIX_ATTACK_ORDER) / sizeof(PLAYERBOT_BONUSMIX_ATTACK_ORDER[0]))
				: (int)(sizeof(PLAYERBOT_BONUSMIX_DEFENCE_ORDER) / sizeof(PLAYERBOT_BONUSMIX_DEFENCE_ORDER[0]));
		int pick = -1, pickStep = PLAYERBOT_BONUSMIX_STEPS;
		for (int i = 0; i < count; ++i)
		{
			const int s = order[i];
			if (!IsPlayerBotBonusMixPiece(ch, ch->GetWear(PLAYERBOT_BONUS75_SLOTS[s].bWearCell)))
				continue;
			const int step = GetPlayerBotBonusMixStep(ch, r, s);
			if (step < PLAYERBOT_BONUSMIX_STEPS - 1 && step < pickStep)
			{
				pick = s;
				pickStep = step;
			}
		}
		++s_kPlayerBotBonusMixStats.fails[why];
		if (watch)
			++s_kPlayerBotBonusMixStats.watchFails;
		++r.fails;
		if (pick < 0)
		{
			++s_kPlayerBotBonusMixStats.maxed;
			sys_log(0, "PLAYERBOT_BONUSMIX: try failed pid=%u name=%s lv=%d map=%ld phase=%s why=%s hunt_min=%u kills=%u "
					"deaths=%u hp_retreats=%u raise=none (maxed)",
					ch->GetPlayerID(), ch->GetName(), (int)ch->GetLevel(), r.lMap, PLAYERBOT_BONUSMIX_PHASE_NAMES[r.phase],
					PLAYERBOT_BONUSMIX_FAIL_NAMES[why], (unsigned int)(r.huntMs / 60000U), r.kills, r.deaths, r.retreats);
			EnterPlayerBotBonusMixPhase(r, PLAYERBOT_BONUSMIX_PHASE_WATCH);
			return;
		}
		r.step[pick] = pickStep + 1;
		r.raised |= 1U << pick;
		r.locked[pick] = 0;
		++s_kPlayerBotBonusMixStats.raises[pick];
		std::string desc;
		CountPlayerBotBonusMixCandidates(ch, r, &desc);
		sys_log(0, "PLAYERBOT_BONUSMIX: try failed pid=%u name=%s lv=%d map=%ld phase=%s why=%s hunt_min=%u kills=%u deaths=%u "
				"hp_retreats=%u raise=%s step=%d->%d element=%u gear=[%s]",
				ch->GetPlayerID(), ch->GetName(), (int)ch->GetLevel(), r.lMap, PLAYERBOT_BONUSMIX_PHASE_NAMES[r.phase],
				PLAYERBOT_BONUSMIX_FAIL_NAMES[why], (unsigned int)(r.huntMs / 60000U), r.kills, r.deaths, r.retreats,
				PLAYERBOT_BONUS75_SLOTS[pick].szName, pickStep, pickStep + 1,
				(unsigned int)GetPlayerBotBonus75ElementPoint(ch), desc.c_str());
		EnterPlayerBotBonusMixPhase(r, PLAYERBOT_BONUSMIX_PHASE_MIX);
	}

	// The hunting time a try counts.
	bool IsPlayerBotBonusMixHunting(LPCHARACTER ch, const TPlayerBotAIState& state)
	{
		return ch && !ch->IsDead() && !state.bFishingSession && !state.bRecoveringAfterDeath && !state.bVisitingShop &&
				!ch->GetMyShop() && IsPlayerBotBonusMixGround(ch);
	}

	// Every AI tick of the field pass (ManagePlayerBotFieldBonus): the hunting clock, and every half a minute the try.
	void TickPlayerBotBonusMix(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now)
	{
		if (!ch || !IsPlayerBotBonusMixStage(ch))
			return;
		TPlayerBotBonusMixBot& r = TouchPlayerBotBonusMix(ch);
		const bool hunting = IsPlayerBotBonusMixHunting(ch, state);
		if (hunting && r.lastTick != 0 && now - r.lastTick <= PLAYERBOT_BONUSMIX_TICK_GAP_MS)
			r.huntMs += now - r.lastTick;
		r.lastTick = now ? now : 1;
		if (r.nextLook != 0 && (int)(now - r.nextLook) < 0)
			return;
		r.nextLook = now + PLAYERBOT_BONUSMIX_LOOK_MS;
		if (hunting && r.lMap != ch->GetMapIndex())
		{
			// another ground: the counts start again there (a try goes on, judged on the new map)
			r.lMap = ch->GetMapIndex();
			ResetPlayerBotBonusMixCounts(r);
		}
		// can a below-need piece be mixed now? (a change stone in the bag, a piece the rule would change)
		TPlayerBotYoharaBonusBag bag;
		ReadPlayerBotYoharaBonusBag(ch, bag);
		const bool yohara = IsPlayerBotYoharaBonusMember(ch);
		if (r.mixSince == 0)
			r.mixSince = now ? now : 1;
		const DWORD lastWork = r.lastChange != 0 && (int)(r.lastChange - r.mixSince) > 0 ? r.lastChange : r.mixSince;
		const bool pending = bag.changeUnits > (yohara ? PLAYERBOT_YOHARA_BONUS_CHANGE_RESERVE : 0) &&
				now - lastWork < PLAYERBOT_BONUSMIX_STALL_MS && GetPlayerBotBonusMixChosenSlot(ch, yohara, 0, NULL, 0) >= 0;
		const int candidates = CountPlayerBotBonusMixCandidates(ch, r, NULL);
		const DWORD tryMs = GetPlayerBotBonusMixTryMs();
		if (r.phase == PLAYERBOT_BONUSMIX_PHASE_TRY || r.phase == PLAYERBOT_BONUSMIX_PHASE_WATCH)
		{
			if ((int)r.deaths >= PLAYERBOT_EPROG_DEATHS)
			{
				FailPlayerBotBonusMixTry(ch, r, PLAYERBOT_BONUSMIX_FAIL_DEATHS);
				return;
			}
			if ((int)r.retreats >= PLAYERBOT_EPROG_RETREATS)
			{
				FailPlayerBotBonusMixTry(ch, r, PLAYERBOT_BONUSMIX_FAIL_RETREATS);
				return;
			}
		}
		switch (r.phase)
		{
			case PLAYERBOT_BONUSMIX_PHASE_MIX:
				if (pending)
					break;
				if (candidates > 0)
				{
					EnterPlayerBotBonusMixPhase(r, PLAYERBOT_BONUSMIX_PHASE_TRY);
					++r.tries;
					++s_kPlayerBotBonusMixStats.tries;
					std::string desc;
					CountPlayerBotBonusMixCandidates(ch, r, &desc);
					sys_log(0, "PLAYERBOT_BONUSMIX: try started pid=%u name=%s lv=%d map=%ld try_min=%u candidates=%d "
							"stock_change=%d element=%u gear=[%s]",
							ch->GetPlayerID(), ch->GetName(), (int)ch->GetLevel(), (long)ch->GetMapIndex(),
							(unsigned int)(tryMs / 60000U), candidates, bag.changeUnits,
							(unsigned int)GetPlayerBotBonus75ElementPoint(ch), desc.c_str());
				}
				else
					EnterPlayerBotBonusMixPhase(r, PLAYERBOT_BONUSMIX_PHASE_WATCH);
				break;
			case PLAYERBOT_BONUSMIX_PHASE_TRY:
				if (pending)
				{
					// a piece fell below its need (another piece worn): mixed first, the try after
					EnterPlayerBotBonusMixPhase(r, PLAYERBOT_BONUSMIX_PHASE_MIX);
					break;
				}
				if (r.huntMs < tryMs)
					break;
				// the kill rate: PLAYERBOT_EPROG_SLOW_KILLS per 30 minutes of hunting
				if ((unsigned long long)r.kills * (unsigned long long)PLAYERBOT_EPROG_WINDOW_MS <
						(unsigned long long)PLAYERBOT_EPROG_SLOW_KILLS * (unsigned long long)r.huntMs)
					FailPlayerBotBonusMixTry(ch, r, PLAYERBOT_BONUSMIX_FAIL_SLOW);
				else
					PassPlayerBotBonusMixTry(ch, r);
				break;
			default:
				if (pending || candidates > 0)
				{
					// a piece to mix, or a new piece worn that meets its need: mixed / tried
					EnterPlayerBotBonusMixPhase(r, PLAYERBOT_BONUSMIX_PHASE_MIX);
					r.nextLook = now;
				}
				else if (r.huntMs >= tryMs)
					ResetPlayerBotBonusMixCounts(r);	// the watch's rolling window
				break;
		}
	}

	bool IsPlayerBotBonusMixFieldOn()
	{
		return IsPlayerBotBonusMixOn() && GetPlayerBotBonusMixFlag(PLAYERBOT_BONUSMIX_FIELD_OFF_FLAG) == 0;
	}

	// Out on a map: may the bonus pass run now? No living target or victim, HP over the floor, no monster on the bot.
	bool IsPlayerBotBonusMixFieldSafe(LPCHARACTER ch, TPlayerBotAIState& state, DWORD now)
	{
		if (!ch || state.bCurrentAction == BOT_ACTION_LURE)
			return false;
		if (state.dwTargetVID != 0)
		{
			LPCHARACTER target = CHARACTER_MANAGER::instance().Find(state.dwTargetVID);
			if (target && !target->IsDead())
				return false;
		}
		if (ch->GetVictim() && !ch->GetVictim()->IsDead())
			return false;
		if (ch->GetMaxHP() <= 0 || (long long)ch->GetHP() * 100 <= (long long)ch->GetMaxHP() * GetPlayerBotBonusMixFieldHp())
			return false;
		if (FindPlayerBotHoldingMonster(ch))
		{
			++s_kPlayerBotBonusMixStats.fieldUnsafe;
			state.dwNextBonusCheckTime = now + PLAYERBOT_BONUSMIX_FIELD_RETRY_MS;
			return false;
		}
		if (!IsPlayerBotVillageMap(ch->GetMapIndex()))
			++s_kPlayerBotBonusMixStats.fieldPasses;
		return true;
	}

	// ------------------------------------------------------------------------------------------------ the census

	void LogPlayerBotBonusMixCensus(DWORD dwNow)
	{
		if (s_dwPlayerBotBonusMixCensusAt != 0 && (int)(dwNow - s_dwPlayerBotBonusMixCensusAt) < 0)
			return;
		const bool first = s_dwPlayerBotBonusMixCensusAt == 0;
		s_dwPlayerBotBonusMixCensusAt = dwNow + PLAYERBOT_BONUSMIX_CENSUS_MS;
		if (first)
			return;
		unsigned int bots = 0, phases[PLAYERBOT_BONUSMIX_PHASES] = { 0, 0, 0 };
		unsigned int locked = 0, met = 0, below = 0, held = 0, reserveKept = 0;
		unsigned int steps[8][PLAYERBOT_BONUSMIX_STEPS];
		memset(steps, 0, sizeof(steps));
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !ch->IsItemLoaded() || !IsPlayerBotBonusMixStage(ch))
				continue;
			++bots;
			TPlayerBotBonusMixBot& r = TouchPlayerBotBonusMix(ch);
			if (r.phase >= 0 && r.phase < PLAYERBOT_BONUSMIX_PHASES)
				++phases[r.phase];
			const BYTE elem = GetPlayerBotBonus75ElementPoint(ch);
			for (int s = 0; s < PLAYERBOT_BONUS75_SLOT_COUNT; ++s)
			{
				const BYTE wearCell = PLAYERBOT_BONUS75_SLOTS[s].bWearCell;
				LPITEM item = ch->GetWear(wearCell);
				if (!IsPlayerBotBonusMixPiece(ch, item))
					continue;
				const int step = GetPlayerBotBonusMixStep(ch, r, s);
				++steps[s][step];
				TPlayerBotBonusMixRead rd;
				ReadPlayerBotBonusMixPiece(ch, item, s, elem, step, rd);
				const bool isLocked = IsPlayerBotBonusMixLocked(r, s, item, elem);
				if (isLocked || rd.met)
				{
					if (isLocked)
						++locked;
					else
						++met;
					// bonus75's old target would still change it: a reroll the need prevents
					const int tier = GetPlayerBotBonus75Tier(ch, item, wearCell, elem, NULL);
					if (tier >= 0 && tier < playerbot_yohara_bonus_rules::TIER_STRONG)
						++reserveKept;
				}
				else
				{
					++below;
					if (IsPlayerBotBonusMixHeld(r, s, rd))
						++held;
				}
			}
		}
		const TPlayerBotBonusMixStats& st = s_kPlayerBotBonusMixStats;
		std::string stepText, raiseText;
		char buf[96];
		for (int s = 0; s < PLAYERBOT_BONUS75_SLOT_COUNT; ++s)
		{
			snprintf(buf, sizeof(buf), "%s%s=%u/%u/%u/%u", s ? " " : "", PLAYERBOT_BONUS75_SLOTS[s].szName, steps[s][0],
					steps[s][1], steps[s][2], steps[s][3]);
			stepText += buf;
			snprintf(buf, sizeof(buf), "%s%s:%u", s ? " " : "", PLAYERBOT_BONUS75_SLOTS[s].szName, st.raises[s]);
			raiseText += buf;
		}
		sys_log(0, "PLAYERBOT_BONUSMIX: census on=%d field=%d try_min=%u bots=%u mix=%u try=%u watch=%u pieces locked=%u met=%u "
				"below=%u held_high_line=%u reserve_kept=%u steps(s0/s1/s2/s3) [%s]",
				IsPlayerBotBonusMixOn() ? 1 : 0, IsPlayerBotBonusMixFieldOn() ? 1 : 0,
				(unsigned int)(GetPlayerBotBonusMixTryMs() / 60000U), bots, phases[PLAYERBOT_BONUSMIX_PHASE_MIX],
				phases[PLAYERBOT_BONUSMIX_PHASE_TRY], phases[PLAYERBOT_BONUSMIX_PHASE_WATCH], locked, met, below, held,
				reserveKept, stepText.c_str());
		sys_log(0, "PLAYERBOT_BONUSMIX: census events tries=%u passed=%u failed deaths=%u hp_retreats=%u slow_kills=%u "
				"(watching=%u) maxed=%u locks=%u raises [%s] changes field=%u/%u town=%u/%u (ordinary/yohara) "
				"field_passes=%u field_unsafe=%u",
				st.tries, st.passes, st.fails[PLAYERBOT_BONUSMIX_FAIL_DEATHS], st.fails[PLAYERBOT_BONUSMIX_FAIL_RETREATS],
				st.fails[PLAYERBOT_BONUSMIX_FAIL_SLOW], st.watchFails, st.maxed, st.locks, raiseText.c_str(),
				st.changesField[0], st.changesField[1], st.changesTown[0], st.changesTown[1], st.fieldPasses,
				st.fieldUnsafe);
	}
}

#endif

#endif
