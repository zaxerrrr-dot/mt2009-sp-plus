#ifndef __INC_METIN2_PLAYERBOT_MLODZI_BOTS_H__
#define __INC_METIN2_PLAYERBOT_MLODZI_BOTS_H__

// MT2009_PLUS_BOT_MLODZI_V1: the bots and Bronie dla Mlodych Bohaterow (MT2009_PLUS_MLODZI_BOHATEROWIE_V1,
// playerbot_mlodzi.h). The owner, 22 October 2026:
//   - while the system is on, every bot - the droppers and farmers too - takes the young heroes' weapon of its
//     class and build at every tier (the kind its own equipment score would pick: the Archer's bow, the Dagger
//     Ninja's dagger, the Mental Warrior's two-hander, the Shaman's by its school's damage model) and wears it
//     at once (ManagePlayerBotMlodzi, the equipment pass's PlayerBotMlodziHandRule);
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
		TPlayerBotMlodziMemo() : dwHoldAt(0), bHold(false), dwPreparedAt(0), dwPreparedID(0), dwNextClaimAt(0),
				dwWornID(0), bSwitchLogged(false), bHoldSeen(false), iPrep(PLAYERBOT_MLODZI_PREP_NONE),
				dwCantLevelID(0), lNeedExp(0), lExpPerHour(-1), iNextLevel(0) {}
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

	// The young heroes' weapon this bot holds - worn or in the bag, of its class and build, a level it has reached - with
	// the most time left, and that time; NULL for none.
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
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || !IsPlayerBotMlodziWeapon(item) ||
					item->GetLevelLimit() > ch->GetLevel() || !item->CanUsedBy(ch) || !IsPlayerBotWeapon(ch, item))
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
	// hand counts for nothing against it, 0 the score decides. A valid young heroes' weapon beats any other
	// (a higher tier beats a lower), and one in its last two minutes gives way to anything.
	int PlayerBotMlodziHandRule(LPITEM item, LPITEM old)
	{
		const bool itemYoung = IsPlayerBotMlodziWeapon(item);
		if (itemYoung && !IsPlayerBotMlodziWeaponValid(item))
			return -1;
		if (!old || !IsPlayerBotMlodziWeapon(old))
			return itemYoung && old ? 1 : 0;
		if (!IsPlayerBotMlodziWeaponValid(old))
			return 1;
		return itemYoung && mlodzi::TierOfVnum(item->GetVnum()) > mlodzi::TierOfVnum(old->GetVnum()) ? 1 : -1;
	}

	// The choice of the offered tier this bot takes: the kind its equipment score would put in the hand - the
	// blow of its school (the Shamans' magic, GetPlayerBotWeaponHitDamageAt) and the class preferences of
	// GetPlayerBotEquipmentScoreTerms (the Archer's bow, the Dagger Ninja's dagger, the Mental Warrior's
	// two-hander, the Body Warrior's sword). 0 when none of the class's choices is a weapon it fights with.
	int ChoosePlayerBotMlodziChoice(LPCHARACTER ch, int tier)
	{
		if (!ch)
			return 0;
		const int job = ch->GetJob();
		const int group = ch->GetSkillGroup();
		int bestChoice = 0;
		long long bestScore = 0;
		for (int choice = 1; choice <= mlodzi::ChoiceCount(job); ++choice)
		{
			const unsigned int vnum = mlodzi::WeaponVnum(tier, job, choice);
			const TItemTable* proto = vnum ? ITEM_MANAGER::instance().GetTable(vnum) : NULL;
			if (!proto || proto->bType != ITEM_WEAPON || !IsPlayerBotWeaponSubTypeFor(ch, proto->bSubType))
				continue;
			long long score = 1 + GetPlayerBotWeaponHitDamageAt(NULL, proto, ch) * 1000;
			if (job == JOB_ASSASSIN && group == 2 && proto->bSubType == WEAPON_BOW)
				score += 500000;
			else if (job == JOB_ASSASSIN && group != 2 && proto->bSubType == WEAPON_DAGGER)
				score += 300000;
			else if (job == JOB_WARRIOR && group == 2 && proto->bSubType == WEAPON_TWO_HANDED)
				score += 500000;
			else if (job == JOB_WARRIOR && group == 1 && proto->bSubType == WEAPON_SWORD)
				score += 200000;
			if (!bestChoice || score > bestScore)
			{
				bestChoice = choice;
				bestScore = score;
			}
		}
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
			return;
		const int choice = ChoosePlayerBotMlodziChoice(ch, tier);
		if (choice <= 0)
		{
			memo.dwNextClaimAt = dwNow + PLAYERBOT_MLODZI_CLAIM_BACKOFF_MS;
			return;
		}
		unsigned int vnum = 0;
		const int result = mlodzi::Claim(ch, tier, choice, &vnum);
		if (result == mlodzi::CLAIM_OK)
		{
			memo.dwCantLevelID = 0;	// MT2009_PLUS_MLODZI_BOHATEROWIE_V2: the new weapon is levelled with again
			memo.dwHoldAt = 0;
			memo.dwPreparedAt = 0;
			memo.bHoldSeen = true;
			// On at once: the equipment pass right after this one prefers it (PlayerBotMlodziHandRule).
			state.dwNextEquipmentCheckTime = dwNow;
			state.bEquipPending = true;
			sys_log(0, "PLAYERBOT_MLODZI: taken pid=%u name=%s level=%u job=%u group=%u tier=%d choice=%d vnum=%u hand=%u",
					pid, ch->GetName(), (unsigned int)ch->GetLevel(), (unsigned int)ch->GetJob(),
					(unsigned int)ch->GetSkillGroup(), tier, choice, vnum, worn ? worn->GetVnum() : 0);
			return;
		}
		if (result == mlodzi::CLAIM_NO_SPACE)
			MakePlayerBotBagColumnRoom(ch, state, dwNow);
		else if (result != mlodzi::CLAIM_BUSY)
			memo.dwNextClaimAt = dwNow + PLAYERBOT_MLODZI_CLAIM_BACKOFF_MS;
		PlayerBotLogThrottled("mlodzi_claim_refused", dwNow,
				"PLAYERBOT_MLODZI: claim refused pid=%u name=%s level=%u tier=%d choice=%d result=%s",
				pid, ch->GetName(), (unsigned int)ch->GetLevel(), tier, choice, GetPlayerBotMlodziClaimName(result));
	}
}

#endif
