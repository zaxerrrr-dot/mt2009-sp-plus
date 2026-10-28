#ifndef __INC_METIN2_PLAYERBOT_MLODZI_BOTS_H__
#define __INC_METIN2_PLAYERBOT_MLODZI_BOTS_H__

// MT2009_PLUS_BOT_MLODZI_V1: the bots and Bronie dla Mlodych Bohaterow (MT2009_PLUS_MLODZI_BOHATEROWIE_V1,
// playerbot_mlodzi.h). The owner, 22 October 2026:
//   - while the system is on, every bot - the droppers and farmers too - takes the young heroes' weapon of its
//     class and build at every tier (the kind its own equipment score would pick: the Archer's bow, the Dagger
//     Ninja's dagger, the Mental Warrior's two-hander, the Shaman's by its school's damage model) and wears it
//     at once (ManagePlayerBotMlodzi, the equipment pass's PlayerBotMlodziHandRule) - V3 below: only when it beats its real weapon;
//   - its own weapon planning - the weapon goal, the market's and the merchants' weapons, the anvil's weapon
//     steps, the level-30 weapon hunt - waits while it holds one with more than seven days left
//     (IsPlayerBotWeaponPlanSuspended); from seven days on it gets and refines the real weapon of its level as
//     ever, and that prepared weapon (the best real weapon in the bag, GetPlayerBotHandWeapon) is kept;
//   - two minutes before the engine removes the young heroes' weapon the prepared one goes on
//     (PLAYERBOT_MLODZI_SWITCH_SECONDS), so no bot fights bare-handed;
//   - the weapon itself is never sold, listed, traded, stored, refined, socketed, bonused or absorbed by a bot
//     (IsPlayerBotMlodziKept at the bot code's choke points; the engine refuses the players' paths).
// System off (mlodzi::Enabled() false): no grant and no hold; a weapon given earlier is worn until it goes.
//
// MT2009_PLUS_MLODZI_BOHATEROWIE_V2 (the owner, 22 October 2026, the second word):
//   - every readiness check (the Spider Dungeon's gear, the cape puller, the Metinolog's and the Executor's
//     weapon, a companion's weak-weapon plan) counts a valid young heroes' weapon as +9
//     (GetPlayerBotReadyWeaponPlus) - it read the weapon's +0;
//   - the seven days' preparation of a real weapon is only for (a) a dropper or a spot farmer whose experience
//     is locked (AFFECT_EXP_BLOCK) - "dropper_locked" - and (b) a character of 70 or more that gets no further
//     young heroes' weapon (the last tier taken; or the system off) - "last_tier";
//   - every other bot keeps levelling to the next tier's level and takes the new weapon at once (the claim's
//     clock); only on the weapon's LAST day, and only when it cannot reach that level in time - its experience
//     locked, or the experience it still needs over its own exp/h of the last hours
//     (PLAYERBOT_MLODZI_RATE_*) is more than the time left - does it get a real weapon of its level as ever:
//     "last_day_cant_level", kept for that weapon once decided (GetPlayerBotMlodziPrepReason).
//   Each decision is logged once: "PLAYERBOT_MLODZI: prep reason=dropper_locked|last_tier|last_day_cant_level".
//
// MT2009_PLUS_MLODZI_BOHATEROWIE_V3 (the test server, 23 October 2026: bots of every level took the weapons - 57 level-120
// Champions in Zodiac +9 / Hydra gear wore the level-70 one, a thousand of them sat in 617 bags, and the claim's
// "no_space" filled the log):
//   - a bot claims a tier only when the offered weapon - scored as the equipment pass scores a weapon: its attack,
//     average damage, fixed lines and "Wartosc ataku" (GetPlayerBotMlodziProtoScore) - beats the best real weapon it
//     wears or has in the bag by PLAYERBOT_MLODZI_CLAIM_MARGIN_PERCENT; in practice the young characters, who level
//     with it and take the next tier as before. Weaker: no claim, a look again in PLAYERBOT_MLODZI_WEAKER_RECHECK_MS;
//   - nor while it holds an unexpired young heroes' weapon of the offered tier or higher (no second one in the bag);
//   - the hand: no more "a young heroes' weapon over any other" - the score decides (PlayerBotMlodziHandRule), so a
//     bot wearing a weaker young weapon puts its best real weapon back on at the next equipment pass. The young one
//     stays in the bag until it expires (it cannot be dropped, sold or destroyed by any bot path);
//   - the hold of the weapon planning (and the 7-day / last-day preparation) counts only a young weapon the bot
//     wears or would wear (FindPlayerBotMlodziHeld): one lying in the bag under a better real weapon holds nothing;
//   - "no_space": said once per tier, the claim waits for a free cell (looked at on the claim's clock, no claim
//     call), and the bag-room pass is asked at most every PLAYERBOT_MLODZI_NO_SPACE_BACKOFF_MS.
//
// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1 (the owner, 28 October 2026 - the young heroes' weapon running out):
//   - plenty of time left: a +9 weapon of the bot's level everywhere (GetPlayerBotWeaponEffective);
//   - 4 days or less left and a next tier exists (the system on, the bot under 70 - tiers at 1, 10 ... 70): the bot goes
//     "200%" for the replacement - "level_up" while its exp/h of the last hours (PLAYERBOT_MLODZI_RATE_*) makes the next
//     tier's level before the weapon goes (it keeps its weapon plan waiting and levels; the claim's clock takes the new one
//     the moment it is offered), else "new_weapon" (the hold ends: the weapon goal, the market and the anvil get and raise a
//     real weapon of its level - the old "last_day_cant_level", now from 4 days and decided once a weapon);
//   - the last tier (no next one, or the system off): "refine_real" from 7 days - the real weapon's preparation;
//   - "200%": the existing levers - the ambition (LEVEL for level_up, EQUIPMENT otherwise, as the progression's push does;
//     not while the progression checklist holds the bot, whose push it is), the weight gates (REFINE / HUNTING / LEVEL /
//     METIN open, FISHING / MINING / HERB shut - PlayerBotMlodziWeightGate, asked by IsPlayerBotWeightGateOpen) and no
//     fishing session (PlayerBotProgressionBlocksFishing);
//   - the refine decisions (IsPlayerBotBigThreeAtPlus, the Perfectionist's target) read the REAL weapon in a window
//     (IsPlayerBotMlodziRealWeaponView) - outside one the +9 view holds; with the young weapon gone the worn one is real;
//   - the log: "PLAYERBOT_MLODZI: window plan=... days_left ..." when a bot enters a window or its plan changes, and an
//     hourly "PLAYERBOT_MLODZI: window census".
//
// An implementation fragment in the sense playerbot_types.h describes: included once, from
// playerbot_manager.cpp, right after playerbot_gear.h (which forward-declares what it asks of this file).

#include "playerbot_mlodzi.h"

namespace
{
	// The planning waits while the weapon has more than this left (the owner: "more than 7 days").
	const long PLAYERBOT_MLODZI_PLAN_HOLD_SECONDS = 7L * 24L * 60L * 60L;
	// The prepared weapon goes on this long before the engine's real_time_expire_event removes the young one.
	const long PLAYERBOT_MLODZI_SWITCH_SECONDS = 120;
	// The grant is tried this often per bot (an offer only appears at a tier's level).
	const DWORD PLAYERBOT_MLODZI_CLAIM_CHECK_MS = 30 * 1000;
	// After a refusal that does not clear by itself (not offered, no proto ...).
	const DWORD PLAYERBOT_MLODZI_CLAIM_BACKOFF_MS = 10 * 60 * 1000;
	// How long the hold's answer and the prepared weapon are kept per bot (they walk the bag).
	const DWORD PLAYERBOT_MLODZI_CACHE_MS = 5 * 1000;
	// MT2009_PLUS_MLODZI_BOHATEROWIE_V3: an offered weapon is claimed only when it scores this much over the best real
	// weapon (the equipment pass's swap margin is 1%; a little more, so a tier is not spent on a point).
	const long long PLAYERBOT_MLODZI_CLAIM_MARGIN_PERCENT = 5;
	// A bot whose real weapon is better looks at the offer again this late (it levels, its weapon may burn).
	const DWORD PLAYERBOT_MLODZI_WEAKER_RECHECK_MS = 30 * 60 * 1000;
	// With the bag full the bag-room pass is asked at most this often; the claim waits for a free cell.
	const DWORD PLAYERBOT_MLODZI_NO_SPACE_BACKOFF_MS = 30 * 60 * 1000;
	// MT2009_PLUS_MLODZI_BOHATEROWIE_V2: the last day - the levelling bot's preparation is decided only then.
	const long PLAYERBOT_MLODZI_LAST_DAY_SECONDS = 24L * 60L * 60L;
	// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1: the next tier's window (4 days) and the last tier's (7 days), the census's clock.
	const long PLAYERBOT_MLODZI_NEXT_TIER_WINDOW_SECONDS = 4L * 24L * 60L * 60L;
	const long PLAYERBOT_MLODZI_LAST_TIER_WINDOW_SECONDS = 7L * 24L * 60L * 60L;
	const DWORD PLAYERBOT_MLODZI_WINDOW_CENSUS_MS = 60 * 60 * 1000;
	// The bot's exp/h: a sample of its total experience every PLAYERBOT_MLODZI_RATE_SAMPLE_SECONDS, the rate over
	// the oldest kept (at most PLAYERBOT_MLODZI_RATE_SAMPLES, three hours); none said before
	// PLAYERBOT_MLODZI_RATE_MIN_SECONDS of them (a fresh start keeps levelling until it knows).
	const long PLAYERBOT_MLODZI_RATE_SAMPLE_SECONDS = 10L * 60L;
	const size_t PLAYERBOT_MLODZI_RATE_SAMPLES = 19;
	const long PLAYERBOT_MLODZI_RATE_MIN_SECONDS = 30L * 60L;

	bool IsPlayerBotMlodziWeapon(LPITEM item)
	{
		return item && mlodzi::IsWeapon(item);
	}

	// One the bot may still wear: past the switch's two minutes.
	bool IsPlayerBotMlodziWeaponValid(LPITEM item)
	{
		return IsPlayerBotMlodziWeapon(item) && mlodzi::SecondsLeft(item) > PLAYERBOT_MLODZI_SWITCH_SECONDS;
	}

	// MT2009_PLUS_MLODZI_BOHATEROWIE_V2: why the bot prepares a real weapon (none: it keeps levelling).
	enum EPlayerBotMlodziPrep
	{
		PLAYERBOT_MLODZI_PREP_NONE = 0,
		PLAYERBOT_MLODZI_PREP_DROPPER_LOCKED,
		PLAYERBOT_MLODZI_PREP_LAST_TIER,
		PLAYERBOT_MLODZI_PREP_LAST_DAY_CANT_LEVEL,
	};

	const char* GetPlayerBotMlodziPrepName(int prep)
	{
		switch (prep)
		{
			case PLAYERBOT_MLODZI_PREP_DROPPER_LOCKED: return "dropper_locked";
			case PLAYERBOT_MLODZI_PREP_LAST_TIER: return "last_tier";
			case PLAYERBOT_MLODZI_PREP_LAST_DAY_CANT_LEVEL: return "cant_level_in_time";	// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1: from 4 days (was the last day)
			default: return "none";
		}
	}

	// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1: what a bot does about its young weapon's end.
	enum EPlayerBotMlodziPlan
	{
		PLAYERBOT_MLODZI_PLAN_NONE = 0,
		PLAYERBOT_MLODZI_PLAN_LEVEL_UP,		// the next tier's level in time: level, take the next weapon
		PLAYERBOT_MLODZI_PLAN_NEW_WEAPON,	// not in time: earn, get and refine a real weapon of its level
		PLAYERBOT_MLODZI_PLAN_REFINE_REAL,	// the last tier: materials and refines for the real weapon
		PLAYERBOT_MLODZI_PLAN_COUNT
	};

	const char* GetPlayerBotMlodziPlanName(int plan)
	{
		switch (plan)
		{
			case PLAYERBOT_MLODZI_PLAN_LEVEL_UP: return "level_up";
			case PLAYERBOT_MLODZI_PLAN_NEW_WEAPON: return "new_weapon";
			case PLAYERBOT_MLODZI_PLAN_REFINE_REAL: return "refine_real";
			default: return "none";
		}
	}

	struct TPlayerBotMlodziExpSample
	{
		long lAt;			// get_global_time()
		unsigned long long qwTotal;	// the experience of all its levels (GetPlayerBotMlodziTotalExp)
	};

	struct TPlayerBotMlodziMemo
	{
		DWORD dwHoldAt;
		bool bHold;
		DWORD dwPreparedAt;
		DWORD dwPreparedID;
		DWORD dwNextClaimAt;
		DWORD dwWornID;		// the young heroes' weapon last seen in the hand
		bool bSwitchLogged;
		bool bHoldSeen;		// the hold held at the last pass (the prep start is said once)
		// MT2009_PLUS_MLODZI_BOHATEROWIE_V2
		int iPrep;		// the last answer's reason (EPlayerBotMlodziPrep)
		DWORD dwCantLevelID;	// the held weapon the last day's "cannot make it" was decided for (kept)
		long lNeedExp;		// the last day's figures, for the log: the experience to the next tier's level,
		long lExpPerHour;	// the exp/h (-1 unknown) and that level
		int iNextLevel;
		// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1
		int iPlan;		// EPlayerBotMlodziPlan of the last answer
		int iLoggedPlan;	// the plan last said in the log, for dwPlanItemID
		DWORD dwPlanItemID;	// the young weapon the plan is for
		long lPlanLeft;		// its seconds left at the last answer
		bool bAmbitionSet;	// the plan set the bot's ambition (given back when it ends)
		std::deque<TPlayerBotMlodziExpSample> samples;
		// MT2009_PLUS_MLODZI_BOHATEROWIE_V3
		int iWeakerTier;	// the tier "weaker than its weapon" was last said for (once a tier)
		int iNoSpaceTier;	// the tier waiting for a free cell, 0 none
		BYTE bNoSpaceSize;	// the cells that weapon needs
		DWORD dwRoomAt;		// the bag-room pass's next turn while it waits
		TPlayerBotMlodziMemo() : dwHoldAt(0), bHold(false), dwPreparedAt(0), dwPreparedID(0), dwNextClaimAt(0),
				dwWornID(0), bSwitchLogged(false), bHoldSeen(false), iPrep(PLAYERBOT_MLODZI_PREP_NONE),
				dwCantLevelID(0), lNeedExp(0), lExpPerHour(-1), iNextLevel(0),
				iPlan(0), iLoggedPlan(0), dwPlanItemID(0), lPlanLeft(0), bAmbitionSet(false), iWeakerTier(0), iNoSpaceTier(0),
				bNoSpaceSize(0), dwRoomAt(0) {}
	};
	std::map<DWORD, TPlayerBotMlodziMemo> s_mapPlayerBotMlodzi;

	// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1: playerbot_progression.h, included later.
	bool IsPlayerBotProgressionHeld(DWORD pid);
	BYTE GetPlayerBotStableAmbition(LPCHARACTER ch, BYTE personality);
	bool PlayerBotMlodziNextTierExists(LPCHARACTER ch);

	// The level a spot farmer is held at, or 0 (playerbot_farmer_link.h, included later).
	BYTE GetPlayerBotFarmerSpotLock(DWORD pid);

	// The valid young heroes' weapon counts as +9 wherever a check asks whether the bot is ready (a dungeon's
	// gear, the cape pull, the rare personas' weapon); any other weapon its own plus, -1 for none.
	// MT2009_PLUS_MLODZI_WEAPON_EFFECTIVE_V1 (the owner, 28 October 2026: "it must be counted as a +9 weapon for the given level"): a
	// young heroes' weapon is +9 for as long as it is worn - no "time left" condition beyond the item existing.
	int GetPlayerBotReadyWeaponPlus(LPITEM weapon)
	{
		if (!weapon || weapon->GetType() != ITEM_WEAPON)
			return -1;
		if (IsPlayerBotMlodziWeapon(weapon))
			return 9;
		return (int)weapon->GetRefineLevel();
	}

	// MT2009_PLUS_MLODZI_WEAPON_EFFECTIVE_V1: the one reading of a bot's weapon every strength check uses (the Spider Dungeons' gear,
	// the progression checklist, the advancement law, the rare personas, the cape pull, the companion's weak
	// weapon, the big three's plus, the M3 door, the Zodiac runs' gear level). A worn young heroes' weapon
	// counts as a +9 weapon of the bot's CURRENT level - the weapon a bot of this level would carry - not of its
	// own tier, for as long as it is worn. Any other weapon: its level limit and its plus. weapon: the piece to
	// read (NULL: the worn weapon). False (level and plus -1) without a weapon.
	bool GetPlayerBotWeaponEffective(LPCHARACTER ch, int* level, int* plus, LPITEM weapon)
	{
		if (!weapon && ch)
			weapon = ch->GetWear(WEAR_WEAPON);
		int l = -1, p = -1;
		bool ok = false;
		if (weapon && weapon->GetType() == ITEM_WEAPON && weapon->GetProto())
		{
			ok = true;
			if (IsPlayerBotMlodziWeapon(weapon))
			{
				l = ch ? (int)ch->GetLevel() : GetPlayerBotProtoLevelLimit(weapon->GetProto());
				p = 9;
			}
			else
			{
				l = GetPlayerBotProtoLevelLimit(weapon->GetProto());
				p = (int)weapon->GetRefineLevel();
			}
		}
		if (level)
			*level = l;
		if (plus)
			*plus = p;
		return ok;
	}

	bool IsPlayerBotMlodziExpLocked(LPCHARACTER ch)
	{
#if defined(PLAYERBOT_ENGINE_MT2009)
		return ch && ch->FindAffect(AFFECT_EXP_BLOCK) != NULL;
#else
		return false;
#endif
	}

	// All the experience of a character's levels below its own plus what it has of this one.
	unsigned long long GetPlayerBotMlodziTotalExp(LPCHARACTER ch)
	{
		if (!ch)
			return 0;
		unsigned long long total = ch->GetExp();
		const int level = std::min<int>((int)ch->GetLevel(), PLAYER_MAX_LEVEL_CONST + 1);
		for (int l = 1; l < level; ++l)
			total += exp_table[l];
		return total;
	}

	// The experience it still needs to reach the level (0 when it has it).
	unsigned long long GetPlayerBotMlodziExpToLevel(LPCHARACTER ch, int targetLevel)
	{
		if (!ch || (int)ch->GetLevel() >= targetLevel)
			return 0;
		const DWORD next = ch->GetNextExp();
		unsigned long long need = next > ch->GetExp() ? (unsigned long long)(next - ch->GetExp()) : 0;
		for (int l = (int)ch->GetLevel() + 1; l < targetLevel && l <= PLAYER_MAX_LEVEL_CONST; ++l)
			need += exp_table[l];
		return need;
	}

	// A sample of the bot's experience, every PLAYERBOT_MLODZI_RATE_SAMPLE_SECONDS.
	void SamplePlayerBotMlodziExp(LPCHARACTER ch, TPlayerBotMlodziMemo& memo)
	{
		const long now = (long)get_global_time();
		if (!memo.samples.empty() && now - memo.samples.back().lAt < PLAYERBOT_MLODZI_RATE_SAMPLE_SECONDS)
			return;
		TPlayerBotMlodziExpSample sample;
		sample.lAt = now;
		sample.qwTotal = GetPlayerBotMlodziTotalExp(ch);
		// A level lost or a character reset: the old samples say nothing of this one.
		if (!memo.samples.empty() && sample.qwTotal < memo.samples.back().qwTotal)
			memo.samples.clear();
		memo.samples.push_back(sample);
		while (memo.samples.size() > PLAYERBOT_MLODZI_RATE_SAMPLES)
			memo.samples.pop_front();
	}

	// Its exp/h over the kept samples and now; -1 while they cover less than PLAYERBOT_MLODZI_RATE_MIN_SECONDS.
	long long GetPlayerBotMlodziExpPerHour(LPCHARACTER ch, const TPlayerBotMlodziMemo& memo)
	{
		if (memo.samples.empty())
			return -1;
		const long span = (long)get_global_time() - memo.samples.front().lAt;
		if (span < PLAYERBOT_MLODZI_RATE_MIN_SECONDS)
			return -1;
		const unsigned long long total = GetPlayerBotMlodziTotalExp(ch);
		const unsigned long long gained = total > memo.samples.front().qwTotal ? total - memo.samples.front().qwTotal : 0;
		return (long long)(gained * 3600ULL / (unsigned long long)span);
	}

	// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1: a young heroes' tier still to come for this bot (the system on, a tier above its level's).
	bool PlayerBotMlodziNextTierExists(LPCHARACTER ch)
	{
		return ch && mlodzi::Enabled() && mlodzi::TierForLevel((int)ch->GetLevel()) < (int)mlodzi::TIER_COUNT;
	}

	// The owner's rule of 22 October: whether - and why - a bot holding the young heroes' weapon `held` with
	// `left` seconds gets its real weapon now (PLAYERBOT_MLODZI_PREP_NONE: it keeps levelling, the planning waits).
	int GetPlayerBotMlodziPrepReason(LPCHARACTER ch, TPlayerBotMlodziMemo& memo, LPITEM held, long left)
	{
		if (!ch || !held || left > PLAYERBOT_MLODZI_PLAN_HOLD_SECONDS)
			return PLAYERBOT_MLODZI_PREP_NONE;
		const bool locked = IsPlayerBotMlodziExpLocked(ch);
		const DWORD pid = ch->GetPlayerID();
		// (a) a dropper or a spot farmer held at its level for good.
		if (locked && (IsPlayerBotDropper(GetPlayerBotPersonalityByPID(pid)) || GetPlayerBotFarmerSpotLock(pid) != 0))
			return PLAYERBOT_MLODZI_PREP_DROPPER_LOCKED;
		// A tier offered now is taken on the claim's clock, not prepared against.
		const int offer = mlodzi::CurrentOffer(ch);
		// (b) 70 and over with the last tier taken: no young heroes' weapon comes after this one.
		// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1: nor with the system off (no tier is offered any more).
		if (offer <= 0 && !PlayerBotMlodziNextTierExists(ch))
			return PLAYERBOT_MLODZI_PREP_LAST_TIER;
		// (c) everybody else levels to the next tier - and only from 4 days before the end (MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1; was the
		// last day), unable to get there in time, gets the real one.
		if (left > PLAYERBOT_MLODZI_NEXT_TIER_WINDOW_SECONDS || offer > 0)
			return PLAYERBOT_MLODZI_PREP_NONE;
		if (memo.dwCantLevelID == held->GetID())
			return PLAYERBOT_MLODZI_PREP_LAST_DAY_CANT_LEVEL;
		const int nextTier = mlodzi::TierForLevel((int)ch->GetLevel()) + 1;
		memo.iNextLevel = mlodzi::TierLevel(nextTier);
		const unsigned long long need = GetPlayerBotMlodziExpToLevel(ch, memo.iNextLevel);
		const long long rate = GetPlayerBotMlodziExpPerHour(ch, memo);
		memo.lNeedExp = (long)std::min<unsigned long long>(need, 2000000000ULL);
		memo.lExpPerHour = (long)std::max<long long>(-1, std::min<long long>(rate, 2000000000LL));
		bool cant = locked;
		if (!cant && rate >= 0)
		{
			const long long usable = std::max<long long>(0, (long long)left - PLAYERBOT_MLODZI_SWITCH_SECONDS);
			// rate * usable / 3600 is the experience it would still make: too little, or none at all.
			cant = rate == 0 || (unsigned long long)rate * (unsigned long long)usable / 3600ULL < need;
		}
		if (!cant)
			return PLAYERBOT_MLODZI_PREP_NONE;
		memo.dwCantLevelID = held->GetID();
		return PLAYERBOT_MLODZI_PREP_LAST_DAY_CANT_LEVEL;
	}

	// MT2009_PLUS_MLODZI_BOHATEROWIE_V3: the equipment score of the best real weapon the bot has - the one in the hand
	// (not a young heroes' one, not a rod or a pickaxe) or the best in the bag (FindPlayerBotBestBagWeapon) - and that
	// weapon; 0 and NULL for none.
	long long GetPlayerBotMlodziRealBestScore(LPCHARACTER ch, LPITEM* bestOut)
	{
		if (bestOut)
			*bestOut = NULL;
		if (!ch || !ch->IsItemLoaded())
			return 0;
		long long bagScore = 0;
		LPITEM best = FindPlayerBotBestBagWeapon(ch, NULL, &bagScore);
		long long bestScore = best ? bagScore : 0;
		LPITEM worn = ch->GetWear(WEAR_WEAPON);
		if (worn && IsPlayerBotWeapon(ch, worn) && worn->GetSubType() != WEAPON_ARROW && !IsPlayerBotMlodziWeapon(worn))
		{
			const long long wornScore = GetPlayerBotEquipmentScore(worn, ch);
			if (!best || wornScore > bestScore)
			{
				best = worn;
				bestScore = wornScore;
			}
		}
		if (bestOut)
			*bestOut = best;
		return bestScore;
	}

	// MT2009_PLUS_MLODZI_BOHATEROWIE_V3: an offered weapon nobody holds yet, scored as GetPlayerBotEquipmentScore
	// would score it in this bot's hands: the blow with the tier's average damage (the attribute the grant sets),
	// the family's tier, the class preferences, the fixed lines outside the hit model, and the legend tier's weight
	// of its one attribute.
	long long GetPlayerBotMlodziProtoScore(LPCHARACTER ch, const TItemTable* proto, int tier)
	{
		if (!ch || !proto || proto->bType != ITEM_WEAPON)
			return 0;
		long long score = 1;
		long long blow = GetPlayerBotWeaponHitDamageAt(NULL, proto, ch, mlodzi::AverageDamage(tier)) * 1000;
		const int familyTier = GetPlayerBotItemTier(proto->dwVnum, (int)ch->GetJob(), false);
		if (familyTier > 0)
		{
			blow = blow * (100 + (familyTier - 3) * PLAYERBOT_WEAPON_TIER_BLOW_PERCENT) / 100;
			score += familyTier;
		}
		score += blow;
		score += GetPlayerBotWeaponClassPreference(ch, proto->bSubType, score);
		for (int i = 0; i < ITEM_APPLY_MAX_NUM; ++i)
			if (!IsPlayerBotHitModelApply(proto->aApplies[i].bType, ch))
				score += ScorePlayerBotApplyTiered(proto->aApplies[i].bType, proto->aApplies[i].lValue, ch);
		if (const std::vector<TItemApply>* extraApplies = GetMt2009ItemExtraApplies(proto->dwVnum))
			for (const TItemApply& extra : *extraApplies)
				if (!IsPlayerBotHitModelApply(extra.bType, ch))
					score += ScorePlayerBotApplyTiered(extra.bType, extra.lValue, ch);
		if (proto->dwImmuneFlag != 0)
			score += 1000;
		const BYTE legend = ClampPlayerBotLegendTier(GetPlayerBotLegendTierOf(ch));
		if (legend >= BOT_LEGEND_SPECIAL && score > 0)
			score += score / 1000 * PLAYERBOT_LEGEND_GEAR_BONUS_PERMILLE[legend];
		return score;
	}

	// MT2009_PLUS_MLODZI_BOHATEROWIE_V3: an unexpired young heroes' weapon of this tier or higher, worn or in the bag
	// (any class or level - it is a bag cell either way).
	bool HoldsPlayerBotMlodziTierOrHigher(LPCHARACTER ch, int tier)
	{
		if (!ch)
			return false;
		LPITEM worn = ch->GetWear(WEAR_WEAPON);
		if (IsPlayerBotMlodziWeapon(worn) && mlodzi::TierOfVnum(worn->GetVnum()) >= tier && mlodzi::SecondsLeft(worn) > 0)
			return true;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && IsPlayerBotMlodziWeapon(item) &&
					mlodzi::TierOfVnum(item->GetVnum()) >= tier && mlodzi::SecondsLeft(item) > 0)
				return true;
		}
		return false;
	}

	// The young heroes' weapon this bot holds - worn or in the bag, of its class and build, a level it has reached - with
	// the most time left, and that time; NULL for none.
	// MT2009_PLUS_MLODZI_BOHATEROWIE_V3: one in the bag counts only while the equipment pass would put it on - valid and
	// scoring over the best real weapon by the pass's swap margin; one lying under a better real weapon holds nothing.
	LPITEM FindPlayerBotMlodziHeld(LPCHARACTER ch, long* leftOut)
	{
		if (leftOut)
			*leftOut = 0;
		if (!ch || !ch->IsItemLoaded())
			return NULL;
		LPITEM best = NULL;
		long bestLeft = 0;
		LPITEM worn = ch->GetWear(WEAR_WEAPON);
		if (IsPlayerBotMlodziWeapon(worn) && IsPlayerBotWeapon(ch, worn))
		{
			best = worn;
			bestLeft = mlodzi::SecondsLeft(worn);
		}
		bool realKnown = false;
		long long realScore = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || !IsPlayerBotMlodziWeapon(item) ||
					item->GetLevelLimit() > ch->GetLevel() || !item->CanUsedBy(ch) || !IsPlayerBotWeapon(ch, item) ||
					!IsPlayerBotMlodziWeaponValid(item))
				continue;
			if (!realKnown)
			{
				realScore = GetPlayerBotMlodziRealBestScore(ch, NULL);
				realKnown = true;
			}
			if (realScore > 0 && GetPlayerBotEquipmentScore(item, ch) * 100 <=
					realScore * (100 + PLAYERBOT_WEAPON_SWAP_MARGIN_PERCENT))
				continue;
			const long left = mlodzi::SecondsLeft(item);
			if (!best || left > bestLeft)
			{
				best = item;
				bestLeft = left;
			}
		}
		if (leftOut)
			*leftOut = bestLeft;
		return best;
	}

	// The owner's seven days: the bot's own weapon planning waits while the system is on and the bot holds a
	// young heroes' weapon with more than PLAYERBOT_MLODZI_PLAN_HOLD_SECONDS left.
	// MT2009_PLUS_MLODZI_BOHATEROWIE_V2: and below that too, unless GetPlayerBotMlodziPrepReason gives a reason.
	// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1: the plan for the young weapon `held` with `left` seconds (memo.iPrep already answered), and the
	// next tier's figures in the memo for the log (need, exp/h, level).
	int GetPlayerBotMlodziPlan(LPCHARACTER ch, TPlayerBotMlodziMemo& memo, LPITEM held, long left)
	{
		if (!ch || !held)
			return PLAYERBOT_MLODZI_PLAN_NONE;
		if (PlayerBotMlodziNextTierExists(ch))
		{
			if (left > PLAYERBOT_MLODZI_NEXT_TIER_WINDOW_SECONDS)
				return PLAYERBOT_MLODZI_PLAN_NONE;
			if (memo.iPrep != PLAYERBOT_MLODZI_PREP_NONE)
				return PLAYERBOT_MLODZI_PLAN_NEW_WEAPON;
			// the estimate, for the log (the decision is GetPlayerBotMlodziPrepReason's)
			memo.iNextLevel = mlodzi::TierLevel(mlodzi::TierForLevel((int)ch->GetLevel()) + 1);
			const unsigned long long need = GetPlayerBotMlodziExpToLevel(ch, memo.iNextLevel);
			const long long rate = GetPlayerBotMlodziExpPerHour(ch, memo);
			memo.lNeedExp = (long)std::min<unsigned long long>(need, 2000000000ULL);
			memo.lExpPerHour = (long)std::max<long long>(-1, std::min<long long>(rate, 2000000000LL));
			return PLAYERBOT_MLODZI_PLAN_LEVEL_UP;
		}
		return left <= PLAYERBOT_MLODZI_LAST_TIER_WINDOW_SECONDS ? PLAYERBOT_MLODZI_PLAN_REFINE_REAL
				: PLAYERBOT_MLODZI_PLAN_NONE;
	}

	bool IsPlayerBotWeaponPlanSuspended(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return false;
		const bool enabled = mlodzi::Enabled();
		// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1: with the system off a weapon given earlier still runs out - its plan is the last tier's.
		std::map<DWORD, TPlayerBotMlodziMemo>::iterator found = s_mapPlayerBotMlodzi.find(ch->GetPlayerID());
		if (!enabled && found == s_mapPlayerBotMlodzi.end() && !IsPlayerBotMlodziWeapon(ch->GetWear(WEAR_WEAPON)))
			return false;
		TPlayerBotMlodziMemo& memo = found != s_mapPlayerBotMlodzi.end() ? found->second : s_mapPlayerBotMlodzi[ch->GetPlayerID()];
		const DWORD now = get_dword_time();
		if (memo.dwHoldAt != 0 && now - memo.dwHoldAt < PLAYERBOT_MLODZI_CACHE_MS)
			return memo.bHold;
		long left = 0;
		LPITEM held = FindPlayerBotMlodziHeld(ch, &left);
		memo.iPrep = held ? GetPlayerBotMlodziPrepReason(ch, memo, held, left) : PLAYERBOT_MLODZI_PREP_NONE;
		memo.iPlan = GetPlayerBotMlodziPlan(ch, memo, held, left);
		memo.dwPlanItemID = held ? held->GetID() : 0;
		memo.lPlanLeft = left;
		memo.bHold = enabled && held != NULL && memo.iPrep == PLAYERBOT_MLODZI_PREP_NONE;
		memo.dwHoldAt = now != 0 ? now : 1;
		return memo.bHold;
	}

	// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1: the bot's plan now (fresh at most PLAYERBOT_MLODZI_CACHE_MS old), PLAN_NONE outside a window.
	int GetPlayerBotMlodziWindowPlan(LPCHARACTER ch)
	{
		if (!ch)
			return PLAYERBOT_MLODZI_PLAN_NONE;
		IsPlayerBotWeaponPlanSuspended(ch);
		std::map<DWORD, TPlayerBotMlodziMemo>::const_iterator it = s_mapPlayerBotMlodzi.find(ch->GetPlayerID());
		return it == s_mapPlayerBotMlodzi.end() ? PLAYERBOT_MLODZI_PLAN_NONE : it->second.iPlan;
	}

	// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1: the refine decisions read the real weapon while a window is open.
	bool IsPlayerBotMlodziRealWeaponView(LPCHARACTER ch)
	{
		return GetPlayerBotMlodziWindowPlan(ch) != PLAYERBOT_MLODZI_PLAN_NONE;
	}

	// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1: the weight gates of a bot in a window (IsPlayerBotWeightGateOpen, by pid - the last answer).
	bool PlayerBotMlodziWeightGate(DWORD pid, BYTE weight, bool& open)
	{
		std::map<DWORD, TPlayerBotMlodziMemo>::const_iterator it = s_mapPlayerBotMlodzi.find(pid);
		if (it == s_mapPlayerBotMlodzi.end() || it->second.iPlan == PLAYERBOT_MLODZI_PLAN_NONE)
			return false;
		const bool levelUp = it->second.iPlan == PLAYERBOT_MLODZI_PLAN_LEVEL_UP;
		switch (weight)
		{
			case PLAYERBOT_WEIGHT_HUNTING:
			case PLAYERBOT_WEIGHT_LEVEL:
				open = true;
				return true;
			case PLAYERBOT_WEIGHT_REFINE:
			case PLAYERBOT_WEIGHT_METIN:
				if (levelUp)
					return false;
				open = true;
				return true;
			case PLAYERBOT_WEIGHT_FISHING:
			case PLAYERBOT_WEIGHT_MINING:
			case PLAYERBOT_WEIGHT_HERB:
				open = false;
				return true;
			default:
				return false;
		}
	}

	// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1: no fishing session for a bot in a window (PlayerBotProgressionBlocksFishing).
	bool PlayerBotMlodziBlocksLeisure(DWORD pid)
	{
		std::map<DWORD, TPlayerBotMlodziMemo>::const_iterator it = s_mapPlayerBotMlodzi.find(pid);
		return it != s_mapPlayerBotMlodzi.end() && it->second.iPlan != PLAYERBOT_MLODZI_PLAN_NONE;
	}

	// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1: the hourly census of the windows.
	DWORD s_dwPlayerBotMlodziWindowCensusAt = 0;
	void LogPlayerBotMlodziWindowCensus(DWORD dwNow)
	{
		if (s_dwPlayerBotMlodziWindowCensusAt != 0 && dwNow - s_dwPlayerBotMlodziWindowCensusAt < PLAYERBOT_MLODZI_WINDOW_CENSUS_MS)
			return;
		s_dwPlayerBotMlodziWindowCensusAt = dwNow ? dwNow : 1;
		unsigned int counts[PLAYERBOT_MLODZI_PLAN_COUNT] = { 0 };
		unsigned int online = 0, minDays = 99;
		for (std::map<DWORD, TPlayerBotMlodziMemo>::const_iterator it = s_mapPlayerBotMlodzi.begin(); it != s_mapPlayerBotMlodzi.end(); ++it)
		{
			if (!CHARACTER_MANAGER::instance().FindByPID(it->first))
				continue;
			++online;
			const int plan = it->second.iPlan;
			if (plan > 0 && plan < PLAYERBOT_MLODZI_PLAN_COUNT)
			{
				++counts[plan];
				minDays = std::min<unsigned int>(minDays, (unsigned int)(std::max(0L, it->second.lPlanLeft) / 86400L));
			}
		}
		sys_log(0, "PLAYERBOT_MLODZI: window census bots=%u level_up=%u new_weapon=%u refine_real=%u min_days_left=%d",
				online, counts[PLAYERBOT_MLODZI_PLAN_LEVEL_UP], counts[PLAYERBOT_MLODZI_PLAN_NEW_WEAPON],
				counts[PLAYERBOT_MLODZI_PLAN_REFINE_REAL], minDays == 99 ? -1 : (int)minDays);
	}

	// The same hold asked of one piece: a weapon (not an arrow) while the hold holds.
	bool IsPlayerBotWeaponPlanSuspendedFor(LPCHARACTER ch, LPITEM item)
	{
		return item && item->GetType() == ITEM_WEAPON && item->GetSubType() != WEAPON_ARROW &&
				IsPlayerBotWeaponPlanSuspended(ch);
	}

	// The real weapon waiting in the bag while the young heroes' one is in the hand: the best weapon of the bag
	// (FindPlayerBotBestBagWeapon, which never counts a young one). Kept PLAYERBOT_MLODZI_CACHE_MS by id - the
	// junk rule asks for it at every bag cell.
	LPITEM GetPlayerBotMlodziPreparedWeapon(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return NULL;
		TPlayerBotMlodziMemo& memo = s_mapPlayerBotMlodzi[ch->GetPlayerID()];
		const DWORD now = get_dword_time();
		if (memo.dwPreparedAt != 0 && now - memo.dwPreparedAt < PLAYERBOT_MLODZI_CACHE_MS)
		{
			if (memo.dwPreparedID == 0)
				return NULL;
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				if (item && item->GetCell() == cell && item->GetID() == memo.dwPreparedID && !item->IsEquipped())
					return item;
			}
		}
		LPITEM prepared = FindPlayerBotBestBagWeapon(ch, NULL, NULL);
		memo.dwPreparedAt = now != 0 ? now : 1;
		memo.dwPreparedID = prepared ? prepared->GetID() : 0;
		return prepared;
	}

	// What no bot path may sell, list, give, store, scrap, refine, socket, bonus or absorb: a young heroes'
	// weapon, and - while one is in the hand - the prepared real weapon in the bag.
	bool IsPlayerBotMlodziKept(LPCHARACTER ch, LPITEM item)
	{
		if (!item)
			return false;
		if (IsPlayerBotMlodziWeapon(item))
			return true;
#ifdef MT2009_PLUS_BOT_YOHARA_GUIDES_V1
		if (IsPlayerBotYoharaLochTicketKept(ch, item))	// MT2009_PLUS_BOT_YOHARA_GUIDES_V1: a Champion's Loch ticket
			return true;
#endif
		if (!ch || item->GetType() != ITEM_WEAPON || item->IsEquipped() ||
				!IsPlayerBotMlodziWeapon(ch->GetWear(WEAR_WEAPON)))
			return false;
		return item == GetPlayerBotMlodziPreparedWeapon(ch);
	}

	// The equipment pass's word on a weapon for the hand: -1 the candidate is not put on, 1 the piece in the
	// hand counts for nothing against it, 0 the score decides. One in its last two minutes never goes on and
	// gives way to anything.
	// MT2009_PLUS_MLODZI_BOHATEROWIE_V3: otherwise the score decides - a young heroes' weapon is worn only while it
	// scores over the best real weapon (V1 put a valid one over any other: level-120 Champions wore the level-70 one).
	int PlayerBotMlodziHandRule(LPITEM item, LPITEM old)
	{
		if (IsPlayerBotMlodziWeapon(item) && !IsPlayerBotMlodziWeaponValid(item))
			return -1;
		if (old && IsPlayerBotMlodziWeapon(old) && !IsPlayerBotMlodziWeaponValid(old))
			return 1;
		return 0;
	}

	// The choice of the offered tier this bot takes: the kind its equipment score would put in the hand - the
	// blow of its school (the Shamans' magic, GetPlayerBotWeaponHitDamageAt) and the class preferences of
	// GetPlayerBotEquipmentScoreTerms (the Archer's bow, the Dagger Ninja's dagger, the Mental Warrior's
	// two-hander, the Body Warrior's sword). 0 when none of the class's choices is a weapon it fights with.
	// MT2009_PLUS_MLODZI_BOHATEROWIE_V3: scored by GetPlayerBotMlodziProtoScore (the equipment score's own terms), that
	// score in *scoreOut.
	int ChoosePlayerBotMlodziChoice(LPCHARACTER ch, int tier, long long* scoreOut)
	{
		if (scoreOut)
			*scoreOut = 0;
		if (!ch)
			return 0;
		const int job = ch->GetJob();
		int bestChoice = 0;
		long long bestScore = 0;
		for (int choice = 1; choice <= mlodzi::ChoiceCount(job); ++choice)
		{
			const unsigned int vnum = mlodzi::WeaponVnum(tier, job, choice);
			const TItemTable* proto = vnum ? ITEM_MANAGER::instance().GetTable(vnum) : NULL;
			if (!proto || proto->bType != ITEM_WEAPON || !IsPlayerBotWeaponSubTypeFor(ch, proto->bSubType))
				continue;
			const long long score = GetPlayerBotMlodziProtoScore(ch, proto, tier);
			if (!bestChoice || score > bestScore)
			{
				bestChoice = choice;
				bestScore = score;
			}
		}
		if (scoreOut)
			*scoreOut = bestScore;
		return bestChoice;
	}

	const char* GetPlayerBotMlodziClaimName(int result)
	{
		switch (result)
		{
			case mlodzi::CLAIM_OK: return "ok";
			case mlodzi::CLAIM_NOT_OFFERED: return "not_offered";
			case mlodzi::CLAIM_BAD_CHOICE: return "bad_choice";
			case mlodzi::CLAIM_NO_SPACE: return "no_space";
			case mlodzi::CLAIM_BAD_PROTO: return "bad_proto";
			case mlodzi::CLAIM_FAILED: return "failed";
			case mlodzi::CLAIM_BUSY: return "busy";
			case mlodzi::CLAIM_DISABLED: return "disabled";
			default: return "?";
		}
	}

	// The bot's pass, every tick before the equipment pass: the expiry switch of the hand, the start of the real
	// weapon's preparation at seven days, and the grant of the tier the bot's level is offered.
	void ManagePlayerBotMlodzi(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || ch->IsDead())
			return;
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, TPlayerBotMlodziMemo>::iterator found = s_mapPlayerBotMlodzi.find(pid);
		LPITEM worn = ch->GetWear(WEAR_WEAPON);
		const bool wornYoung = IsPlayerBotMlodziWeapon(worn);
		// Nothing for a bot that never had one while the system is off - no map row per bot.
		if (found == s_mapPlayerBotMlodzi.end() && !wornYoung && !mlodzi::Enabled())
			return;
		TPlayerBotMlodziMemo& memo = found != s_mapPlayerBotMlodzi.end() ? found->second : s_mapPlayerBotMlodzi[pid];

		// The hand: the young weapon in its last two minutes gives way to the prepared one now, and an empty hand
		// where it was (the engine removed it) is filled on this very tick.
		if (wornYoung)
		{
			if (memo.dwWornID != worn->GetID())
			{
				memo.dwWornID = worn->GetID();
				memo.bSwitchLogged = false;
			}
			if (!IsPlayerBotMlodziWeaponValid(worn) && !memo.bSwitchLogged)
			{
				memo.bSwitchLogged = true;
				state.dwNextEquipmentCheckTime = dwNow;
				state.bEquipPending = true;
				LPITEM prepared = GetPlayerBotMlodziPreparedWeapon(ch);
				sys_log(0, "PLAYERBOT_MLODZI: expiry switch pid=%u name=%s level=%u young=%u left=%ld prepared=%u+%u",
						pid, ch->GetName(), (unsigned int)ch->GetLevel(), worn->GetVnum(), mlodzi::SecondsLeft(worn),
						prepared ? prepared->GetVnum() : 0, prepared ? (unsigned int)prepared->GetRefineLevel() : 0);
			}
		}
		else if (memo.dwWornID != 0)
		{
			// Another weapon or a tool in the hand is the equipment pass's own change; an empty hand is the engine's
			// removal (or the switch's piece not yet on) and is filled now.
			if (!worn)
			{
				LPITEM prepared = GetPlayerBotMlodziPreparedWeapon(ch);
				sys_log(0, "PLAYERBOT_MLODZI: young weapon gone from the hand pid=%u name=%s level=%u prepared=%u+%u",
						pid, ch->GetName(), (unsigned int)ch->GetLevel(),
						prepared ? prepared->GetVnum() : 0, prepared ? (unsigned int)prepared->GetRefineLevel() : 0);
				state.dwNextEquipmentCheckTime = dwNow;
				state.bEquipPending = true;
			}
			memo.dwWornID = 0;
			memo.bSwitchLogged = false;
		}

		// MT2009_PLUS_MLODZI_BOHATEROWIE_V2: the exp/h the last day's decision reads, sampled while one is held.
		if (wornYoung || memo.bHoldSeen)
			SamplePlayerBotMlodziExp(ch, memo);

		// The preparation: said once, with its reason, when the hold ends while a young weapon is still held.
		const bool hold = IsPlayerBotWeaponPlanSuspended(ch);
		if (memo.bHoldSeen && !hold)
		{
			long left = 0;
			LPITEM held = FindPlayerBotMlodziHeld(ch, &left);
			if (held)
			{
				LPITEM prepared = GetPlayerBotMlodziPreparedWeapon(ch);
				sys_log(0, "PLAYERBOT_MLODZI: prep reason=%s pid=%u name=%s level=%u young=%u left_h=%ld locked=%d "
						"next_level=%d need_exp=%ld exp_h=%ld prepared=%u+%u",
						GetPlayerBotMlodziPrepName(memo.iPrep), pid, ch->GetName(), (unsigned int)ch->GetLevel(),
						held->GetVnum(), left / 3600, IsPlayerBotMlodziExpLocked(ch) ? 1 : 0,
						memo.iPrep == PLAYERBOT_MLODZI_PREP_LAST_DAY_CANT_LEVEL ? memo.iNextLevel : 0,
						memo.iPrep == PLAYERBOT_MLODZI_PREP_LAST_DAY_CANT_LEVEL ? memo.lNeedExp : 0,
						memo.iPrep == PLAYERBOT_MLODZI_PREP_LAST_DAY_CANT_LEVEL ? memo.lExpPerHour : -1,
						prepared ? prepared->GetVnum() : 0, prepared ? (unsigned int)prepared->GetRefineLevel() : 0);
			}
		}
		memo.bHoldSeen = hold;

		// MT2009_PLUS_MLODZI_WEAPON_EXPIRY_PLAN_V1: the window's line (once a plan per weapon), the "200%" ambition, the census.
		if (memo.iPlan != PLAYERBOT_MLODZI_PLAN_NONE && memo.iLoggedPlan != memo.iPlan)
		{
			memo.iLoggedPlan = memo.iPlan;
			const long long rate = memo.lExpPerHour;
			const long estH = memo.iPlan == PLAYERBOT_MLODZI_PLAN_LEVEL_UP && rate > 0
					? (long)((long long)memo.lNeedExp / rate) : -1;
			sys_log(0, "PLAYERBOT_MLODZI: window plan=%s pid=%u name=%s level=%u young=%u days_left=%.1f next_tier_level=%d "
					"need_exp=%ld exp_h=%ld est_h=%ld prep=%s",
					GetPlayerBotMlodziPlanName(memo.iPlan), pid, ch->GetName(), (unsigned int)ch->GetLevel(),
					memo.dwPlanItemID, (double)memo.lPlanLeft / 86400.0,
					memo.iPlan == PLAYERBOT_MLODZI_PLAN_REFINE_REAL ? 0 : memo.iNextLevel,
					memo.iPlan == PLAYERBOT_MLODZI_PLAN_REFINE_REAL ? 0 : memo.lNeedExp,
					memo.iPlan == PLAYERBOT_MLODZI_PLAN_REFINE_REAL ? -1 : memo.lExpPerHour, estH,
					GetPlayerBotMlodziPrepName(memo.iPrep));
		}
		else if (memo.iPlan == PLAYERBOT_MLODZI_PLAN_NONE)
			memo.iLoggedPlan = PLAYERBOT_MLODZI_PLAN_NONE;
		if (memo.iPlan != PLAYERBOT_MLODZI_PLAN_NONE && !IsPlayerBotProgressionHeld(pid))
		{
			const BYTE want = memo.iPlan == PLAYERBOT_MLODZI_PLAN_LEVEL_UP ? (BYTE)BOT_AMBITION_LEVEL : (BYTE)BOT_AMBITION_EQUIPMENT;
			if (state.bAmbition != want)
			{
				state.bAmbition = want;
				memo.bAmbitionSet = true;
			}
		}
		else if (memo.bAmbitionSet)
		{
			memo.bAmbitionSet = false;
			if (!IsPlayerBotProgressionHeld(pid))
				state.bAmbition = GetPlayerBotStableAmbition(ch, state.bPersonality);
		}
		LogPlayerBotMlodziWindowCensus(dwNow);

		// The grant, on its own clock.
		if (!mlodzi::Enabled() || (memo.dwNextClaimAt != 0 && (int)(dwNow - memo.dwNextClaimAt) < 0))
			return;
		memo.dwNextClaimAt = dwNow + PLAYERBOT_MLODZI_CLAIM_CHECK_MS;
		// A window open is the engine's CLAIM_BUSY (CanHandleItem); the bot's own counter waits too.
		if (ch->GetMyShop() || state.bVisitingShop)
			return;
		const int tier = mlodzi::CurrentOffer(ch);
		if (tier <= 0)
		{
			memo.iNoSpaceTier = 0;
			return;
		}
		// MT2009_PLUS_MLODZI_BOHATEROWIE_V3: a full bag waits for a free cell - looked at on this clock, no claim
		// call and no line in the log; the bag-room pass is asked at most every PLAYERBOT_MLODZI_NO_SPACE_BACKOFF_MS.
		if (memo.iNoSpaceTier == tier && ch->GetEmptyInventory(std::max<BYTE>(1, memo.bNoSpaceSize)) < 0)
		{
			if ((int)(dwNow - memo.dwRoomAt) >= 0)
			{
				memo.dwRoomAt = dwNow + PLAYERBOT_MLODZI_NO_SPACE_BACKOFF_MS;
				MakePlayerBotBagColumnRoom(ch, state, dwNow);
			}
			return;
		}
		// MT2009_PLUS_MLODZI_BOHATEROWIE_V3: never a second one of this tier or higher in the bag.
		if (HoldsPlayerBotMlodziTierOrHigher(ch, tier))
		{
			memo.dwNextClaimAt = dwNow + PLAYERBOT_MLODZI_WEAKER_RECHECK_MS;
			return;
		}
		long long youngScore = 0;
		const int choice = ChoosePlayerBotMlodziChoice(ch, tier, &youngScore);
		if (choice <= 0)
		{
			memo.dwNextClaimAt = dwNow + PLAYERBOT_MLODZI_CLAIM_BACKOFF_MS;
			return;
		}
		// MT2009_PLUS_MLODZI_BOHATEROWIE_V3: only a weapon better than the best real one it has (the young characters in
		// practice); a stronger bot never claims it and looks again in PLAYERBOT_MLODZI_WEAKER_RECHECK_MS.
		LPITEM real = NULL;
		const long long realScore = GetPlayerBotMlodziRealBestScore(ch, &real);
		if (real && youngScore * 100 <= realScore * (100 + PLAYERBOT_MLODZI_CLAIM_MARGIN_PERCENT))
		{
			memo.dwNextClaimAt = dwNow + PLAYERBOT_MLODZI_WEAKER_RECHECK_MS;
			if (memo.iWeakerTier != tier)
			{
				memo.iWeakerTier = tier;
				PlayerBotLogThrottled("mlodzi_claim_weaker", dwNow,
						"PLAYERBOT_MLODZI: claim skipped, own weapon better pid=%u name=%s level=%u tier=%d choice=%d "
						"young_score=%lld real=%u+%u real_score=%lld",
						pid, ch->GetName(), (unsigned int)ch->GetLevel(), tier, choice, youngScore,
						real->GetVnum(), (unsigned int)real->GetRefineLevel(), realScore);
			}
			return;
		}
		unsigned int vnum = 0;
		const int result = mlodzi::Claim(ch, tier, choice, &vnum);
		if (result == mlodzi::CLAIM_OK)
		{
			memo.dwCantLevelID = 0;	// MT2009_PLUS_MLODZI_BOHATEROWIE_V2: the new weapon is levelled with again
			memo.iNoSpaceTier = 0;	// MT2009_PLUS_MLODZI_BOHATEROWIE_V3
			memo.dwHoldAt = 0;
			memo.dwPreparedAt = 0;
			memo.bHoldSeen = true;
			// On at once: the equipment pass right after this one puts it on (it was claimed for scoring over the real
			// weapon by more than the pass's swap margin - MT2009_PLUS_MLODZI_BOHATEROWIE_V3).
			state.dwNextEquipmentCheckTime = dwNow;
			state.bEquipPending = true;
			sys_log(0, "PLAYERBOT_MLODZI: taken pid=%u name=%s level=%u job=%u group=%u tier=%d choice=%d vnum=%u hand=%u",
					pid, ch->GetName(), (unsigned int)ch->GetLevel(), (unsigned int)ch->GetJob(),
					(unsigned int)ch->GetSkillGroup(), tier, choice, vnum, worn ? worn->GetVnum() : 0);
			return;
		}
		if (result == mlodzi::CLAIM_NO_SPACE)
		{
			// MT2009_PLUS_MLODZI_BOHATEROWIE_V3: said once for the tier; then it waits for a free cell (above).
			const TItemTable* proto = vnum ? ITEM_MANAGER::instance().GetTable(vnum) : NULL;
			if (!proto)
				proto = ITEM_MANAGER::instance().GetTable(mlodzi::WeaponVnum(tier, ch->GetJob(), choice));
			memo.bNoSpaceSize = proto ? proto->bSize : 3;
			memo.dwRoomAt = dwNow + PLAYERBOT_MLODZI_NO_SPACE_BACKOFF_MS;
			MakePlayerBotBagColumnRoom(ch, state, dwNow);
			if (memo.iNoSpaceTier != tier)
			{
				memo.iNoSpaceTier = tier;
				sys_log(0, "PLAYERBOT_MLODZI: claim waits for a free cell pid=%u name=%s level=%u tier=%d choice=%d size=%u",
						pid, ch->GetName(), (unsigned int)ch->GetLevel(), tier, choice, (unsigned int)memo.bNoSpaceSize);
			}
			return;
		}
		if (result != mlodzi::CLAIM_BUSY)
			memo.dwNextClaimAt = dwNow + PLAYERBOT_MLODZI_CLAIM_BACKOFF_MS;
		PlayerBotLogThrottled("mlodzi_claim_refused", dwNow,
				"PLAYERBOT_MLODZI: claim refused pid=%u name=%s level=%u tier=%d choice=%d result=%s",
				pid, ch->GetName(), (unsigned int)ch->GetLevel(), tier, choice, GetPlayerBotMlodziClaimName(result));
	}
}

#endif
