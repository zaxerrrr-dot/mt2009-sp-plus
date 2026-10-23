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
			case PLAYERBOT_MLODZI_PREP_LAST_DAY_CANT_LEVEL: return "last_day_cant_level";
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
		std::deque<TPlayerBotMlodziExpSample> samples;
		// MT2009_PLUS_MLODZI_BOHATEROWIE_V3
		int iWeakerTier;	// the tier "weaker than its weapon" was last said for (once a tier)
		int iNoSpaceTier;	// the tier waiting for a free cell, 0 none
		BYTE bNoSpaceSize;	// the cells that weapon needs
		DWORD dwRoomAt;		// the bag-room pass's next turn while it waits
		TPlayerBotMlodziMemo() : dwHoldAt(0), bHold(false), dwPreparedAt(0), dwPreparedID(0), dwNextClaimAt(0),
				dwWornID(0), bSwitchLogged(false), bHoldSeen(false), iPrep(PLAYERBOT_MLODZI_PREP_NONE),
				dwCantLevelID(0), lNeedExp(0), lExpPerHour(-1), iNextLevel(0), iWeakerTier(0), iNoSpaceTier(0),
				bNoSpaceSize(0), dwRoomAt(0) {}
	};
	std::map<DWORD, TPlayerBotMlodziMemo> s_mapPlayerBotMlodzi;

	// The level a spot farmer is held at, or 0 (playerbot_farmer_link.h, included later).
	BYTE GetPlayerBotFarmerSpotLock(DWORD pid);

	// The valid young heroes' weapon counts as +9 wherever a check asks whether the bot is ready (a dungeon's
	// gear, the cape pull, the rare personas' weapon); any other weapon its own plus, -1 for none.
	int GetPlayerBotReadyWeaponPlus(LPITEM weapon)
	{
		if (!weapon || weapon->GetType() != ITEM_WEAPON)
			return -1;
		if (IsPlayerBotMlodziWeaponValid(weapon))
			return 9;
		return (int)weapon->GetRefineLevel();
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
		if (offer <= 0 && mlodzi::TierForLevel((int)ch->GetLevel()) >= (int)mlodzi::TIER_COUNT)
			return PLAYERBOT_MLODZI_PREP_LAST_TIER;
		// (c) everybody else levels to the next tier - and only on the weapon's last day, unable to get there in
		// time, gets the real one.
		if (left > PLAYERBOT_MLODZI_LAST_DAY_SECONDS || offer > 0)
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
	bool IsPlayerBotWeaponPlanSuspended(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded() || !mlodzi::Enabled())
			return false;
		TPlayerBotMlodziMemo& memo = s_mapPlayerBotMlodzi[ch->GetPlayerID()];
		const DWORD now = get_dword_time();
		if (memo.dwHoldAt != 0 && now - memo.dwHoldAt < PLAYERBOT_MLODZI_CACHE_MS)
			return memo.bHold;
		long left = 0;
		LPITEM held = FindPlayerBotMlodziHeld(ch, &left);
		memo.iPrep = held ? GetPlayerBotMlodziPrepReason(ch, memo, held, left) : PLAYERBOT_MLODZI_PREP_NONE;
		memo.bHold = held != NULL && memo.iPrep == PLAYERBOT_MLODZI_PREP_NONE;
		memo.dwHoldAt = now != 0 ? now : 1;
		return memo.bHold;
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
