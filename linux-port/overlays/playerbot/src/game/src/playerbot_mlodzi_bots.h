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

	bool IsPlayerBotMlodziWeapon(LPITEM item)
	{
		return item && mlodzi::IsWeapon(item);
	}

	// One the bot may still wear: past the switch's two minutes.
	bool IsPlayerBotMlodziWeaponValid(LPITEM item)
	{
		return IsPlayerBotMlodziWeapon(item) && mlodzi::SecondsLeft(item) > PLAYERBOT_MLODZI_SWITCH_SECONDS;
	}

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
		TPlayerBotMlodziMemo() : dwHoldAt(0), bHold(false), dwPreparedAt(0), dwPreparedID(0), dwNextClaimAt(0),
				dwWornID(0), bSwitchLogged(false), bHoldSeen(false) {}
	};
	std::map<DWORD, TPlayerBotMlodziMemo> s_mapPlayerBotMlodzi;

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
	bool IsPlayerBotWeaponPlanSuspended(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded() || !mlodzi::Enabled())
			return false;
		TPlayerBotMlodziMemo& memo = s_mapPlayerBotMlodzi[ch->GetPlayerID()];
		const DWORD now = get_dword_time();
		if (memo.dwHoldAt != 0 && now - memo.dwHoldAt < PLAYERBOT_MLODZI_CACHE_MS)
			return memo.bHold;
		long left = 0;
		memo.bHold = FindPlayerBotMlodziHeld(ch, &left) != NULL && left > PLAYERBOT_MLODZI_PLAN_HOLD_SECONDS;
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

		// The seven days: said once when the hold ends while a young weapon is still held.
		const bool hold = IsPlayerBotWeaponPlanSuspended(ch);
		if (memo.bHoldSeen && !hold)
		{
			long left = 0;
			LPITEM held = FindPlayerBotMlodziHeld(ch, &left);
			if (held)
			{
				LPITEM prepared = GetPlayerBotMlodziPreparedWeapon(ch);
				sys_log(0, "PLAYERBOT_MLODZI: prep start pid=%u name=%s level=%u young=%u left_h=%ld prepared=%u+%u",
						pid, ch->GetName(), (unsigned int)ch->GetLevel(), held->GetVnum(), left / 3600,
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
