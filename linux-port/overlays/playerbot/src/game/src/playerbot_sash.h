#ifndef __INC_METIN2_PLAYERBOT_SASH_H__
#define __INC_METIN2_PLAYERBOT_SASH_H__

// Sashes (MT2009 Plus): a bot builds one, fills it and wears it.
//
// Until now a sash was only counter goods for a bot (GetPlayerBotRareGoodsKind):
// dropped by a boss, carried to a stall, sold. Here a share of the bots keeps
// them and does what a player does with them at Uriel (NPC 20011, in each
// first village, acce_costume_uriel.quest):
//
//   * combine two sashes of the same grade (any kind: a Szarfa Mistrza goes
//     with a Krolewska Szarfa, the engine asks only the grade) - 1+1 -> 2 (5%),
//     2+2 -> 3 (10%), 3+3 -> 4 (11-19%), 4+4 -> 4 (+1..5, at most 25%); the
//     second sash is lost whether it works or not, the yang too
//     (CHARACTER::RefineAcceMaterials, item_length.h ACCE_*);
//   * absorb a weapon or a body armour into a sash of the grade its level
//     wants: the piece is gone, the sash carries its bonuses times its
//     absorption, class restrictions stay behind with the piece;
//   * wear it (WEAR_COSTUME_ACCE).
//
// Uriel's window is a client's, so the pass calls the engine's own functions
// the window's packets call (OpenAcce, AddAcceMaterial, RefineAcceMaterials,
// CloseAcce): every check and roll is the engine's. A bot's DESC is a bot
// desc, and the packets these send go nowhere.
//
// Who: PLAYERBOT_SASH_KEEPER_PERCENT of the bots of PLAYERBOT_SASH_MIN_LEVEL
// and more, picked by player id so the choice survives a restart; the rest
// keep selling sashes, so the market does not dry up. None while the world
// has sashes switched off (M2_SASHES=0 -> event flag m2_sash_off).

#if defined(ENABLE_ACCE_COSTUME_SYSTEM)

namespace
{
	const int PLAYERBOT_SASH_MIN_LEVEL = 30;
	const int PLAYERBOT_SASH_KEEPER_PERCENT = 60;
	// Unworn sashes a keeper holds for the combining; past this many the worst
	// are goods again.
	const int PLAYERBOT_SASH_KEEP = 10;
	const DWORD PLAYERBOT_SASH_CHECK_MIN_MS = 5 * 60 * 1000;
	const DWORD PLAYERBOT_SASH_CHECK_MAX_MS = 10 * 60 * 1000;
	// A visit's work: combines and one absorption, a few seconds apart.
	const int PLAYERBOT_SASH_VISIT_MAX_STEPS = 8;
	// 4+4 only for a bot with this much to spare over its reserve.
	const long long PLAYERBOT_SASH_RICH_GOLD = 10000000LL;
	// A piece is absorbed only when it is worth this share of what the bot
	// wears in that slot (GetPlayerBotEquipmentScore, class-neutral).
	const int PLAYERBOT_SASH_ABSORB_MIN_PERCENT = 40;
	// A sash bought off a counter: at most this share of the spare purse.
	const int PLAYERBOT_SASH_MARKET_PURSE_PERCENT = 25;
	// Uriel: npc.txt cells (713,605), (655,553) and (425,716) on each first
	// village's BasePosition (409600,896000), (0,102400), (921600,204800).
	const DWORD PLAYERBOT_URIEL_VNUM = 20011;

	struct TPlayerBotSashTarget
	{
		int grade;
		int absorption;
	};

	struct TPlayerBotSashStats
	{
		unsigned combines;
		unsigned combineFails;
		unsigned absorbs;
		unsigned wears;
		unsigned trips;
		unsigned bought;
	};
	TPlayerBotSashStats s_kPlayerBotSashStats = { 0, 0, 0, 0, 0, 0 };

	bool GetPlayerBotUriel(long mapIndex, playerbot_empire_rules::TPoint& out)
	{
		switch (mapIndex)
		{
			case 1:  out.x = 480900; out.y = 956500; return true;
			case 21: out.x = 65500;  out.y = 157700; return true;
			case 41: out.x = 964100; out.y = 276400; return true;
			default: return false;
		}
	}

	bool ArePlayerBotSashesOff()
	{
		return quest::CQuestManager::instance().GetEventFlag("m2_sash_off") != 0;
	}

	bool IsPlayerBotSashItem(LPITEM item)
	{
		return item && item->GetType() == ITEM_COSTUME && item->GetSubType() == COSTUME_ACCE &&
				IsPlayerBotSashVnum(item->GetVnum());
	}

	int GetPlayerBotSashGrade(LPITEM item)
	{
		return item ? (int)item->GetValue(ACCE_GRADE_VALUE_FIELD) : 0;
	}

	int GetPlayerBotSashAbsorption(LPITEM item)
	{
		return item ? (int)item->GetSocket(ACCE_ABSORPTION_SOCKET) : 0;
	}

	bool IsPlayerBotSashAbsorbed(LPITEM item)
	{
		return item && item->GetSocket(ACCE_ABSORBED_SOCKET) > 0;
	}

	// Which bots build one: a stable roll on the player id.
	bool IsPlayerBotSashKeeperPID(DWORD pid)
	{
		const DWORD h = (pid * 2654435761U) ^ 0x53415348U;
		return (int)((h >> 16) % 100) < PLAYERBOT_SASH_KEEPER_PERCENT;
	}

	bool IsPlayerBotSashKeeper(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC() || ch->GetLevel() < PLAYERBOT_SASH_MIN_LEVEL)
			return false;
		const DWORD pid = ch->GetPlayerID();
		if (!IsPlayerBotSashKeeperPID(pid) || IsPlayerBotSidekickPID(pid) ||
				CPlayerBotManager::instance().IsMedalDropperCohortPID(pid))
			return false;
		return !ArePlayerBotSashesOff();
	}

	long long GetPlayerBotSashSpareGold(LPCHARACTER ch)
	{
		return ch ? (long long)ch->GetGold() - (long long)GetPlayerBotReservedGold(ch) -
				(long long)PLAYERBOT_SHOPPING_GOLD_FLOOR : 0;
	}

	// What a sash should be at this level before the bot absorbs a piece into
	// it: the operator's table (plan of 25 September 2026).
	TPlayerBotSashTarget GetPlayerBotSashTarget(LPCHARACTER ch)
	{
		TPlayerBotSashTarget t = { 0, 0 };
		if (!ch)
			return t;
		const int level = ch->GetLevel();
		if (level < PLAYERBOT_SASH_MIN_LEVEL)
			return t;
		if (level < 50)       { t.grade = 2; t.absorption = ACCE_GRADE_2_ABS; }
		else if (level < 65)  { t.grade = 3; t.absorption = ACCE_GRADE_3_ABS; }
		else if (level < 75)  { t.grade = 4; t.absorption = 13; }
		else                  { t.grade = 4; t.absorption = 17; }
		if (level >= 90 && GetPlayerBotSashSpareGold(ch) >= PLAYERBOT_SASH_RICH_GOLD)
			t.absorption = 21;
		return t;
	}

	bool IsPlayerBotSashAtTarget(LPITEM item, const TPlayerBotSashTarget& t)
	{
		return item && t.grade > 0 && GetPlayerBotSashGrade(item) >= t.grade &&
				GetPlayerBotSashAbsorption(item) >= t.absorption;
	}

	// Which sash is the better one to wear: a filled one over an empty one,
	// then the absorption.
	int RankPlayerBotSash(LPITEM item)
	{
		if (!item)
			return -1;
		return (IsPlayerBotSashAbsorbed(item) ? 1000 : 0) + GetPlayerBotSashAbsorption(item);
	}

	bool IsPlayerBotSashDone(LPCHARACTER ch, const TPlayerBotSashTarget& t)
	{
		LPITEM worn = ch ? ch->GetWear(WEAR_COSTUME_ACCE) : NULL;
		return worn && IsPlayerBotSashItem(worn) && IsPlayerBotSashAbsorbed(worn) &&
				IsPlayerBotSashAtTarget(worn, t);
	}

	bool IsPlayerBotSashUsable(LPITEM item)
	{
		return IsPlayerBotSashItem(item) && !item->IsEquipped() && !item->isLocked() &&
				!item->IsExchanging();
	}

	void CollectPlayerBotBagSashes(LPCHARACTER ch, std::vector<LPITEM>& out)
	{
		out.clear();
		if (!ch || !ch->IsItemLoaded())
			return;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && IsPlayerBotSashUsable(item))
				out.push_back(item);
		}
	}

	// Kept, not goods: a keeper's sashes while its sash is not done, the best
	// PLAYERBOT_SASH_KEEP of those at or under its target grade; once done,
	// only one that would beat what it wears. The worn one is never goods.
	bool IsPlayerBotKeptSash(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !IsPlayerBotSashItem(item))
			return false;
		if (item->IsEquipped())
			return true;
		if (!IsPlayerBotSashKeeper(ch))
			return false;
		const TPlayerBotSashTarget t = GetPlayerBotSashTarget(ch);
		if (t.grade <= 0)
			return false;
		if (IsPlayerBotSashDone(ch, t))
			return RankPlayerBotSash(item) > RankPlayerBotSash(ch->GetWear(WEAR_COSTUME_ACCE));
		if (IsPlayerBotSashAbsorbed(item))
			return RankPlayerBotSash(item) > RankPlayerBotSash(ch->GetWear(WEAR_COSTUME_ACCE));
		if (GetPlayerBotSashGrade(item) > t.grade)
			return true;
		const int grade = GetPlayerBotSashGrade(item);
		const int absorption = GetPlayerBotSashAbsorption(item);
		int better = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM other = ch->GetInventoryItem(cell);
			if (!other || other == item || other->GetCell() != cell || !IsPlayerBotSashItem(other) ||
					IsPlayerBotSashAbsorbed(other))
				continue;
			const int g = GetPlayerBotSashGrade(other);
			if (g > grade || (g == grade && GetPlayerBotSashAbsorption(other) > absorption) ||
					(g == grade && GetPlayerBotSashAbsorption(other) == absorption && other->GetID() < item->GetID()))
				++better;
		}
		return better < PLAYERBOT_SASH_KEEP;
	}

	// A counter's sash worth a keeper's money: an empty one of a grade it still
	// combines, or one already at its target grade and absorption.
	bool WantsPlayerBotSashOffer(LPCHARACTER ch, LPITEM offer)
	{
		if (!IsPlayerBotSashItem(offer) || IsPlayerBotSashAbsorbed(offer) || !IsPlayerBotSashKeeper(ch))
			return false;
		const TPlayerBotSashTarget t = GetPlayerBotSashTarget(ch);
		if (t.grade <= 0 || IsPlayerBotSashDone(ch, t))
			return false;
		std::vector<LPITEM> bag;
		CollectPlayerBotBagSashes(ch, bag);
		if ((int)bag.size() >= PLAYERBOT_SASH_KEEP)
			return false;
		// A finished-grade sash in the bag waits only for a piece to absorb.
		for (size_t i = 0; i < bag.size(); ++i)
			if (!IsPlayerBotSashAbsorbed(bag[i]) && IsPlayerBotSashAtTarget(bag[i], t))
				return false;
		const int grade = GetPlayerBotSashGrade(offer);
		return grade < t.grade || IsPlayerBotSashAtTarget(offer, t);
	}

	bool CanPlayerBotPayForSashOffer(LPCHARACTER ch, long long price)
	{
		const long long spare = GetPlayerBotSashSpareGold(ch);
		return price > 0 && price <= spare * PLAYERBOT_SASH_MARKET_PURSE_PERCENT / 100;
	}

	// Asked before a market walk, without reading a counter: a keeper short of
	// sashes while some counter carries one.
	bool PlayerBotWantsSashFromMarket(LPCHARACTER ch)
	{
		if (!IsPlayerBotSashKeeper(ch))
			return false;
		const TPlayerBotSashTarget t = GetPlayerBotSashTarget(ch);
		if (t.grade <= 0 || IsPlayerBotSashDone(ch, t))
			return false;
		std::vector<LPITEM> bag;
		CollectPlayerBotBagSashes(ch, bag);
		if ((int)bag.size() >= PLAYERBOT_SASH_KEEP || GetPlayerBotSashSpareGold(ch) < 4000000LL)
			return false;
		for (size_t i = 0; i < bag.size(); ++i)
			if (!IsPlayerBotSashAbsorbed(bag[i]) && IsPlayerBotSashAtTarget(bag[i], t))
				return false;
		for (DWORD vnum = 85001; vnum <= 85024; ++vnum)
		{
			const TPlayerBotMarketLedgerEntry* e = GetPlayerBotMarketLedgerEntry(vnum);
			if (e && e->dwSupplyUnits > 0)
				return true;
		}
		return false;
	}

	void NotePlayerBotSashBought(LPCHARACTER ch, DWORD vnum, long long price)
	{
		++s_kPlayerBotSashStats.bought;
		sys_log(0, "PLAYERBOT_SASH: bought pid=%u name=%s vnum=%u price=%lld",
				ch ? ch->GetPlayerID() : 0, ch ? ch->GetName() : "", vnum, price);
	}

	// ------------------------------------------------------------ the work

	// A sash to absorb into: empty and at the target - from the bag, or the
	// empty one the bot already wears.
	LPITEM FindPlayerBotSashToFill(LPCHARACTER ch, const TPlayerBotSashTarget& t)
	{
		LPITEM best = NULL;
		std::vector<LPITEM> bag;
		CollectPlayerBotBagSashes(ch, bag);
		for (size_t i = 0; i < bag.size(); ++i)
			if (!IsPlayerBotSashAbsorbed(bag[i]) && IsPlayerBotSashAtTarget(bag[i], t) &&
					(!best || RankPlayerBotSash(bag[i]) > RankPlayerBotSash(best)))
				best = bag[i];
		LPITEM worn = ch->GetWear(WEAR_COSTUME_ACCE);
		if (worn && IsPlayerBotSashItem(worn) && !IsPlayerBotSashAbsorbed(worn) &&
				IsPlayerBotSashAtTarget(worn, t) && (!best || RankPlayerBotSash(worn) > RankPlayerBotSash(best)))
			best = worn;
		return best;
	}

	// Two sashes to combine: the lowest grade under the target with a pair,
	// else (rich, level 75+) two uniques under the target absorption. First
	// material the better one - it is the one a failure leaves.
	bool FindPlayerBotSashPair(LPCHARACTER ch, const TPlayerBotSashTarget& t,
			LPITEM& first, LPITEM& second)
	{
		first = second = NULL;
		// Nothing more to combine once the sash is done, or while one at the
		// target waits for a piece to absorb: more would be money for goods.
		if (IsPlayerBotSashDone(ch, t) || FindPlayerBotSashToFill(ch, t))
			return false;
		std::vector<LPITEM> bag;
		CollectPlayerBotBagSashes(ch, bag);
		const long long spare = GetPlayerBotSashSpareGold(ch);
		for (int grade = 1; grade <= 4; ++grade)
		{
			if (grade >= t.grade && !(grade == 4 && t.grade == 4))
				break;
			LPITEM best = NULL, worst = NULL;
			int count = 0;
			for (size_t i = 0; i < bag.size(); ++i)
			{
				LPITEM s = bag[i];
				if (GetPlayerBotSashGrade(s) != grade || GetPlayerBotSashAbsorption(s) >= ACCE_GRADE_4_ABS_MAX)
					continue;
				++count;
				if (!best || RankPlayerBotSash(s) > RankPlayerBotSash(best))
					best = s;
			}
			if (count < 2)
				continue;
			for (size_t i = 0; i < bag.size(); ++i)
			{
				LPITEM s = bag[i];
				if (s == best || GetPlayerBotSashGrade(s) != grade || IsPlayerBotSashAbsorbed(s) ||
						GetPlayerBotSashAbsorption(s) >= ACCE_GRADE_4_ABS_MAX)
					continue;
				if (!worst || RankPlayerBotSash(s) < RankPlayerBotSash(worst))
					worst = s;
			}
			if (!worst)
				continue;
			if (grade == 4)
			{
				// Uniques: only past level 75, with money to lose at 30%, and
				// while the better one is under the target.
				if (ch->GetLevel() < 75 || spare < PLAYERBOT_SASH_RICH_GOLD ||
						GetPlayerBotSashAbsorption(best) >= t.absorption)
					continue;
			}
			if (spare < (long long)ch->GetAcceCombinePrice(grade))
				return false;
			first = best;
			second = worst;
			return true;
		}
		return false;
	}

	// The piece to absorb: a weapon or a body armour in the bag the bot will
	// not wear and does not keep for anything else, worth at least
	// PLAYERBOT_SASH_ABSORB_MIN_PERCENT of what it wears in that slot. Any
	// class's: the sash does not ask.
	LPITEM FindPlayerBotSashAbsorbPiece(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return NULL;
		LPITEM wornWeapon = ch->GetWear(WEAR_WEAPON);
		LPITEM wornBody = ch->GetWear(WEAR_BODY);
		const long long weaponBar = wornWeapon ? GetPlayerBotEquipmentScore(wornWeapon, NULL) : 0;
		const long long bodyBar = wornBody ? GetPlayerBotEquipmentScore(wornBody, NULL) : 0;
		LPITEM best = NULL;
		long long bestPercent = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || item->IsEquipped() || item->isLocked() ||
					item->IsExchanging() || !item->GetProto())
				continue;
			const bool weapon = item->GetType() == ITEM_WEAPON && item->GetSubType() != WEAPON_ARROW
#if defined(ENABLE_QUIVER_SYSTEM)
					&& item->GetSubType() != WEAPON_QUIVER
#endif
					;
			const bool body = item->GetType() == ITEM_ARMOR && item->GetSubType() == ARMOR_BODY;
			if (!weapon && !body)
				continue;
			if (IsPlayerBotLppKeptItem(ch, item) || IsPlayerBotKeptBackupArmour(ch, item) ||
					IsPlayerBotSidekickGift(ch, item) || IsPlayerBotSidekickPinned(ch, item))
				continue;
			// One it would put on is not spare.
			if (IsPlayerBotEquipmentCandidate(ch, item) && item->GetLevelLimit() <= ch->GetLevel())
			{
				LPITEM worn = weapon ? wornWeapon : wornBody;
				if (!worn || GetPlayerBotEquipmentScore(item, ch) > GetPlayerBotEquipmentScore(worn, ch))
					continue;
			}
			const long long bar = weapon ? weaponBar : bodyBar;
			const long long score = GetPlayerBotEquipmentScore(item, NULL);
			const long long percent = bar > 0 ? score * 100 / bar : 100;
			if (percent < PLAYERBOT_SASH_ABSORB_MIN_PERCENT)
				continue;
			if (!best || percent > bestPercent)
			{
				best = item;
				bestPercent = percent;
			}
		}
		return best;
	}

	bool HasPlayerBotSashWork(LPCHARACTER ch, const TPlayerBotSashTarget& t)
	{
		LPITEM a = NULL, b = NULL;
		if (FindPlayerBotSashPair(ch, t, a, b))
			return true;
		return FindPlayerBotSashToFill(ch, t) && FindPlayerBotSashAbsorbPiece(ch);
	}

	// Takes the worn sash off into the bag, for the window: it refuses an
	// equipped one.
	bool TakeOffPlayerBotSash(LPCHARACTER ch, LPITEM sash)
	{
		if (!sash || !sash->IsEquipped())
			return true;
		if (ch->GetEmptyInventory(sash->GetSize()) < 0)
			return false;
		return ch->UnequipItem(sash) && !sash->IsEquipped();
	}

	bool CombinePlayerBotSashes(LPCHARACTER ch, LPITEM first, LPITEM second)
	{
		const DWORD firstId = first->GetID();
		const DWORD secondId = second->GetID();
		const WORD firstCell = first->GetCell();
		const int grade = GetPlayerBotSashGrade(first);
		const int oldAbs = GetPlayerBotSashAbsorption(first);
		const DWORD firstVnum = first->GetVnum();
		const long long goldBefore = ch->GetGold();

		ch->OpenAcce(true);
		ch->AddAcceMaterial(TItemPos(INVENTORY, first->GetCell()), 0);
		ch->AddAcceMaterial(TItemPos(INVENTORY, second->GetCell()), 1);
		std::vector<LPITEM> mats = ch->GetAcceMaterials();
		if (mats.size() < 2 || mats[0] != first || mats[1] != second)
		{
			ch->CloseAcce();
			sys_err("PLAYERBOT_SASH: combine refused pid=%u name=%s first=%u second=%u grade=%d",
					ch->GetPlayerID(), ch->GetName(), firstVnum, second->GetVnum(), grade);
			return false;
		}
		ch->RefineAcceMaterials();
		ch->CloseAcce();

		// Neither pointer is to be trusted now: read the bag.
		LPITEM result = ch->GetInventoryItem(firstCell);
		const bool secondGone = ITEM_MANAGER::instance().Find(secondId) == NULL;
		const long long paid = goldBefore - (long long)ch->GetGold();
		if (result && result->GetID() != firstId && IsPlayerBotSashItem(result))
		{
			++s_kPlayerBotSashStats.combines;
			sys_log(0, "PLAYERBOT_SASH: combine ok pid=%u name=%s lv=%d grade=%d->%d vnum=%u->%u abs=%d->%d paid=%lld",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), grade, GetPlayerBotSashGrade(result),
					firstVnum, result->GetVnum(), oldAbs, GetPlayerBotSashAbsorption(result), paid);
			return true;
		}
		if (secondGone && paid > 0)
		{
			++s_kPlayerBotSashStats.combineFails;
			sys_log(0, "PLAYERBOT_SASH: combine fail pid=%u name=%s lv=%d grade=%d vnum=%u paid=%lld",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), grade, firstVnum, paid);
			return true;
		}
		sys_err("PLAYERBOT_SASH: combine did nothing pid=%u name=%s grade=%d gold=%lld",
				ch->GetPlayerID(), ch->GetName(), grade, (long long)ch->GetGold());
		return false;
	}

	bool AbsorbIntoPlayerBotSash(LPCHARACTER ch, LPITEM sash, LPITEM piece)
	{
		if (!TakeOffPlayerBotSash(ch, sash))
			return false;
		const DWORD sashId = sash->GetID();
		const DWORD pieceId = piece->GetID();
		const DWORD pieceVnum = piece->GetVnum();
		const int pieceRefine = piece->GetRefineLevel();

		ch->OpenAcce(false);
		ch->AddAcceMaterial(TItemPos(INVENTORY, sash->GetCell()), 0);
		ch->AddAcceMaterial(TItemPos(INVENTORY, piece->GetCell()), 1);
		std::vector<LPITEM> mats = ch->GetAcceMaterials();
		if (mats.size() < 2 || mats[0] != sash || mats[1] != piece)
		{
			ch->CloseAcce();
			sys_err("PLAYERBOT_SASH: absorb refused pid=%u name=%s sash=%u piece=%u",
					ch->GetPlayerID(), ch->GetName(), sash->GetVnum(), pieceVnum);
			return false;
		}
		ch->RefineAcceMaterials();
		ch->CloseAcce();

		LPITEM filled = ITEM_MANAGER::instance().Find(sashId);
		if (filled && IsPlayerBotSashAbsorbed(filled) && ITEM_MANAGER::instance().Find(pieceId) == NULL)
		{
			++s_kPlayerBotSashStats.absorbs;
			sys_log(0, "PLAYERBOT_SASH: absorb pid=%u name=%s lv=%d sash=%u grade=%d abs=%d piece=%u+%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), filled->GetVnum(),
					GetPlayerBotSashGrade(filled), GetPlayerBotSashAbsorption(filled), pieceVnum, pieceRefine);
			return true;
		}
		sys_err("PLAYERBOT_SASH: absorb did nothing pid=%u name=%s sash=%u piece=%u",
				ch->GetPlayerID(), ch->GetName(), filled ? filled->GetVnum() : 0, pieceVnum);
		return false;
	}

	// Puts on the best sash the bot has: a filled one, or the empty one at its
	// target that waits for a piece (a look until then). An empty one under
	// the target stays in the bag for the combining.
	bool WearPlayerBotBestSash(LPCHARACTER ch, const TPlayerBotSashTarget& t)
	{
		if (!ch || ch->IsDead() || ch->GetExchange() || ch->GetMyShop() || ch->IsAcceOpened())
			return false;
		LPITEM worn = ch->GetWear(WEAR_COSTUME_ACCE);
		std::vector<LPITEM> bag;
		CollectPlayerBotBagSashes(ch, bag);
		LPITEM best = NULL;
		for (size_t i = 0; i < bag.size(); ++i)
		{
			LPITEM s = bag[i];
			if (!IsPlayerBotSashAbsorbed(s) && !IsPlayerBotSashAtTarget(s, t))
				continue;
			if (!best || RankPlayerBotSash(s) > RankPlayerBotSash(best))
				best = s;
		}
		if (!best || (worn && RankPlayerBotSash(best) <= RankPlayerBotSash(worn)))
			return false;
		const DWORD oldVnum = worn ? worn->GetVnum() : 0;
		if (worn && !TakeOffPlayerBotSash(ch, worn))
			return false;
		if (!ch->EquipItem(best))
		{
			if (worn && !worn->IsEquipped())
				ch->EquipItem(worn);
			return false;
		}
		++s_kPlayerBotSashStats.wears;
		sys_log(0, "PLAYERBOT_SASH: wear pid=%u name=%s lv=%d vnum=%u grade=%d abs=%d absorbed=%u old=%u",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), best->GetVnum(), GetPlayerBotSashGrade(best),
				GetPlayerBotSashAbsorption(best), (DWORD)best->GetSocket(ACCE_ABSORBED_SOCKET), oldVnum);
		return true;
	}

	void EndPlayerBotUrielVisit(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		state.bVisitingUriel = false;
		state.dwNextSashActionTime = 0;
		state.dwNextSashCheckTime = dwNow + number(PLAYERBOT_SASH_CHECK_MIN_MS, PLAYERBOT_SASH_CHECK_MAX_MS);
		ClearPlayerBotRoute(state, true);
		if (ch && ch->IsAcceOpened())
		{
			if (ch->IsAcceOpened(true))
				ch->CloseAcce();
			if (ch->IsAcceOpened(false))
				ch->CloseAcce();
		}
	}

	// The tick: now and then, look at the sashes; with work for Uriel, go to
	// him (a first village of its kingdom, by the road the medal stand takes)
	// and do it there, a step every few seconds.
	bool ManagePlayerBotSash(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || state.bVisitingShop || state.bVisitingBiologist || state.bVisitingHerbalist ||
				state.bVisitingStable || state.bVisitingAlchemist || state.bFishingSession ||
				state.bMarketTrip)
			return false;
		if (!state.bVisitingUriel && dwNow < state.dwNextSashCheckTime)
			return false;
		if (!IsPlayerBotSashKeeper(ch) ||
				(ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())) ||
				IsPlayerBotHeldForCompany(ch) || ch->GetMyShop() != NULL)
		{
			if (state.bVisitingUriel)
				EndPlayerBotUrielVisit(ch, state, dwNow);
			state.dwNextSashCheckTime = dwNow + number(PLAYERBOT_SASH_CHECK_MIN_MS, PLAYERBOT_SASH_CHECK_MAX_MS);
			return false;
		}
		const TPlayerBotSashTarget t = GetPlayerBotSashTarget(ch);

		if (!state.bVisitingUriel)
		{
			state.dwNextSashCheckTime = dwNow + number(PLAYERBOT_SASH_CHECK_MIN_MS, PLAYERBOT_SASH_CHECK_MAX_MS);
			WearPlayerBotBestSash(ch, t);
			if (!HasPlayerBotSashWork(ch, t))
				return false;

			playerbot_empire_rules::TPoint uriel;
			if (!GetPlayerBotUriel(ch->GetMapIndex(), uriel))
			{
				long homeMap = 0, homeX = 0, homeY = 0;
				if (!GetPlayerBotVillageReturn(ch, playerbot_empire_rules::MAP_ROLE_M1, homeMap, homeX, homeY) ||
						!IsPlayerBotMapHostedHere(homeMap) || !GetPlayerBotUriel(homeMap, uriel))
					return false;
				// Not from a fight: the next look, then.
				if (ch->GetVictim() != NULL || state.dwTargetVID != 0)
				{
					state.dwNextSashCheckTime = dwNow + number(20000, 60000);
					return false;
				}
				SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
				if (!TransitionPlayerBotMap(ch, state, homeMap, homeX, homeY, dwNow, "sash_to_uriel"))
					return false;
				++s_kPlayerBotSashStats.trips;
				// Straight to Uriel once it stands in the village.
				state.dwNextSashCheckTime = 0;
				return true;
			}
			state.bVisitingUriel = true;
			state.dwNextSashActionTime = 0;
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ch->Stop();
			ClearPlayerBotRoute(state, true);
			sys_log(0, "PLAYERBOT_SASH: going to Uriel pid=%u name=%s lv=%d target=%d/%d gold=%lld",
					ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), t.grade, t.absorption,
					(long long)ch->GetGold());
		}

		playerbot_empire_rules::TPoint uriel;
		if (!GetPlayerBotUriel(ch->GetMapIndex(), uriel))
		{
			EndPlayerBotUrielVisit(ch, state, dwNow);
			return false;
		}
		SetPlayerBotAction(state, BOT_ACTION_SHOP, dwNow);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);

		long approachX = 0, approachY = 0;
		GetPlayerBotNpcApproach(ch->GetPlayerID(), uriel.x, uriel.y, 0x55524945U, approachX, approachY);
		if (DISTANCE_APPROX(ch->GetX() - approachX, ch->GetY() - approachY) > 650)
		{
			if (!MovePlayerBot(ch, approachX, approachY, dwNow, 20, true, true, false, true) &&
					state.bStuckCounter >= 6)
			{
				sys_err("PLAYERBOT_SASH: route to Uriel failed pid=%u name=%s map=%ld from=(%ld,%ld)",
						ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), ch->GetX(), ch->GetY());
				EndPlayerBotUrielVisit(ch, state, dwNow);
				return false;
			}
			return true;
		}

		ch->Stop();
		ch->SetPosition(POS_STANDING);
		if (state.dwNextSashActionTime == 0)
		{
			state.dwNextSashActionTime = dwNow + number(3000, 7000);
			state.bSashVisitSteps = 0;
			return true;
		}
		if (dwNow < state.dwNextSashActionTime)
			return true;

		// One step: a combine, else the absorption; then the next in a few
		// seconds, until nothing is left or the visit has done enough.
		bool did = false;
		LPITEM first = NULL, second = NULL;
		if (state.bSashVisitSteps < PLAYERBOT_SASH_VISIT_MAX_STEPS && FindPlayerBotSashPair(ch, t, first, second))
			did = CombinePlayerBotSashes(ch, first, second);
		else if (state.bSashVisitSteps < PLAYERBOT_SASH_VISIT_MAX_STEPS)
		{
			LPITEM sash = FindPlayerBotSashToFill(ch, t);
			LPITEM piece = sash ? FindPlayerBotSashAbsorbPiece(ch) : NULL;
			if (sash && piece)
			{
				did = AbsorbIntoPlayerBotSash(ch, sash, piece);
				if (did)
					WearPlayerBotBestSash(ch, t);
			}
		}
		if (did)
		{
			++state.bSashVisitSteps;
			state.dwNextSashActionTime = dwNow + number(2500, 5000);
			return true;
		}
		WearPlayerBotBestSash(ch, t);
		sys_log(0, "PLAYERBOT_SASH: visit over pid=%u name=%s lv=%d steps=%d worn=%u grade=%d abs=%d absorbed=%d gold=%lld",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), (int)state.bSashVisitSteps,
				ch->GetWear(WEAR_COSTUME_ACCE) ? ch->GetWear(WEAR_COSTUME_ACCE)->GetVnum() : 0,
				GetPlayerBotSashGrade(ch->GetWear(WEAR_COSTUME_ACCE)),
				GetPlayerBotSashAbsorption(ch->GetWear(WEAR_COSTUME_ACCE)),
				IsPlayerBotSashAbsorbed(ch->GetWear(WEAR_COSTUME_ACCE)) ? 1 : 0, (long long)ch->GetGold());
		EndPlayerBotUrielVisit(ch, state, dwNow);
		return false;
	}

	void LogPlayerBotSashCensus()
	{
		sys_log(0, "PLAYERBOT_SASH: census combines=%u fails=%u absorbs=%u wears=%u trips=%u bought=%u",
				s_kPlayerBotSashStats.combines, s_kPlayerBotSashStats.combineFails,
				s_kPlayerBotSashStats.absorbs, s_kPlayerBotSashStats.wears,
				s_kPlayerBotSashStats.trips, s_kPlayerBotSashStats.bought);
	}
}

#else

namespace
{
	bool IsPlayerBotKeptSash(LPCHARACTER, LPITEM) { return false; }
	bool WantsPlayerBotSashOffer(LPCHARACTER, LPITEM) { return false; }
	bool CanPlayerBotPayForSashOffer(LPCHARACTER, long long) { return false; }
	bool PlayerBotWantsSashFromMarket(LPCHARACTER) { return false; }
	void NotePlayerBotSashBought(LPCHARACTER, DWORD, long long) {}
	bool ManagePlayerBotSash(LPCHARACTER, TPlayerBotAIState&, DWORD) { return false; }
	void LogPlayerBotSashCensus() {}
}

#endif

#endif
