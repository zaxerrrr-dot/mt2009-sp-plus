#ifndef __INC_METIN2_PLAYERBOT_AWAKENING_H__
#define __INC_METIN2_PLAYERBOT_AWAKENING_H__

// The soul stones +0..+9 and Olejek Niebios - what is left of Digi Rasta's
// Rytual Przebudzenia (the Ritual of Awakening) and soul stones.
//
// MT2009_PLUS_NO_AWAKENING_V1 (the owner, 15 October 2026, Yohara 3.0): the
// ritual and the awakened weapons are gone. The engine's hooks stay (the test
// engine tree keeps server-patches/digirasta's edits; a fresh tree gets them
// too): AwakeningSpecialRefineResult / AwakeningSpecialRefineSet answer for the
// soul stones only, AwakeningIsAwakenedWeapon is always false (no "never
// burns", no forced sockets), AwakeningCreateBossDrop rolls Olejek Niebios
// only - Kamien Przebudzenia (30670) drops from no boss. The bots neither
// perform the ritual nor price, keep or list awakened goods. The seven
// families are official rows again and the awakened pieces the level-87
// weapons (mariadb/playerbot/noawaken.sql). What the history said:
//
// Autor systemow: Digi Rasta (nowy-system v0.16, "Nowy system - Etap 1"),
// ported into MT2009 PLUS as our own code: MT2009_PLUS_AWAKENING_V1 and
// MT2009_PLUS_SOULSTONE9_V1. His package hooked these into the engine with
// zastosuj.py; here the engine edits are server-patches/digirasta (edits.json),
// the item and recipe rows are mariadb/playerbot/apply.sh, the client rows are
// client-patches/client-2.0.30/tools/digirasta.
//
//   * (gone) A weapon 75 +9 and Kamien Przebudzenia (30670) at the plain Blacksmith
//     make the awakened weapon +0 through the ordinary refine window: recipe
//     7110 (the stone and 200 000 000 yang, 100%), the bonuses and stones go
//     over as in every refine (CopyAllAttrTo). In item_proto the +9 keeps
//     refined_vnum 0, so nothing else reads it as "can be refined" - only the
//     engine's refine path asks AwakeningSpecialRefineResult below.
//   * (gone) The awakened weapons refine +0..+9 by the owner's recipes 7100-7108; a
//     failed refine never destroys nor lowers one, with a scroll neither. The
//     ritual and the awakened weapons never go through a guild smith (its fee
//     multiplier would overflow int at these prices) nor the Demon Tower.
//   * A soul stone +4..+8 is refined at the Blacksmith by recipe 7200 + grade
//     (Magiczny Pyl and yang); a failure destroys the stone, as before.
//   * (gone) Kamien Przebudzenia dropped from the bosses of AWAKENING_BOSS_DROPS (his
//     table, plus Krolowa Dzungli); Razador and Nemere give none (the owner,
//     3 October - it was their dungeon quests' boss_drop at 15%).
//   * MT2009_PLUS_HEAVEN_OIL_V1 (Autor: Digi Rasta, nowy-system v0.17):
//     Olejek Niebios (71056) is a plain material (apply.sh) and the second
//     ingredient of the soul stone steps 7204-7208 (1/1/2/2/3 beside the
//     dust); it drops from the bosses of HEAVEN_OIL_BOSS_DROPS. The bots keep
//     it for their next stone step, buy it off counters for it, list what is
//     over and raise a bag stone +4..+8 at the Blacksmith themselves
//     (ManagePlayerBotSoulStoneStep) - never without the oil, the dust and
//     the fee, and never twice in PLAYERBOT_STONE_STEP_RETRY_MS.
//
// The bots' half: the stones +5..+9 and the oil are never the merchant's
// (IsPlayerBotAwakeningGoods, playerbot_economy.h), their prices are in
// playerbot_price_tables.h, the stones' kind and tier in playerbot_gear.h /
// playerbot_item_tiers.h.
//
// An implementation fragment in the sense playerbot_types.h describes: include
// it exactly once, after playerbot_economy.h and playerbot_battle_horse.h
// (GetPlayerBotReservedGold). The engine hooks are plain functions at file
// scope, as playerbot_legends.h's are.

namespace mt2009_awakening
{
	// world.refine_proto rows (apply.sh): 7204-7208 the soul stones' steps.
	const DWORD STONE_REFINE_SET_BASE = 7200;
	const int STONE_KINDS = 14;
	// A soul stone is refined from +4 (+0..+3 go to the Alchemist's dust).
	const int STONE_REFINE_MIN_GRADE = 4;

	// Soul stones: 14 kinds (k = 0..13, Penetracji .. Przyspieszenia); +0..+4 =
	// 28g30+k, +5 = 28530+k, +6..+9 = 28g00+k (g = the grade).
	inline DWORD StoneVnum(int grade, int kind)
	{
		if (grade <= 5)
			return 28030 + grade * 100 + kind;
		return 28000 + grade * 100 + kind;
	}

	inline bool StoneGradeKind(DWORD dwVnum, int& grade, int& kind)
	{
		if (dwVnum < 28000 || dwVnum > 28999)
			return false;
		grade = (int)((dwVnum / 100) % 10);
		kind = (int)(dwVnum % 100) - (grade <= 5 ? 30 : 0);
		return kind >= 0 && kind < STONE_KINDS;
	}

	inline bool IsRefinableStone(DWORD dwVnum, int& grade, int& kind)
	{
		return StoneGradeKind(dwVnum, grade, kind) && grade >= STONE_REFINE_MIN_GRADE && grade < 9;
	}

	// A soul stone +5..+9 of the chain (the bots' goods, never the merchant's).
	inline bool IsHighSoulStone(DWORD dwVnum)
	{
		int grade = 0, kind = 0;
		return StoneGradeKind(dwVnum, grade, kind) && grade >= 5;
	}

	// A boss drop: per 10 000 kills, whatever mob_drop_item.txt says.
	struct TBossDrop
	{
		DWORD dwMobVnum;
		WORD wChance;
	};

	// MT2009_PLUS_HEAVEN_OIL_V1 (Autor: Digi Rasta, nowy-system v0.17):
	// Olejek Niebios, the soul stone steps' second ingredient (refine_proto
	// 7204-7208 vnum1, 1/1/2/2/3 - apply.sh). Per 10 000 kills: his row (Silna Lodowa Wiedzma 3%) and the owner's two -
	// the dragon of Leze Smoka 3% and the last boss of the hardest Arezzo
	// dungeon (Starozytna Dzungla, from level 95) 10%.
	const DWORD HEAVEN_OIL_VNUM = 71056;

	const TBossDrop HEAVEN_OIL_BOSS_DROPS[] = {
		{ 1192,  300 },	// Silna Lodowa Wiedzma - Grota Wygnancow 1 (map 72), his row
		{ 2493,  300 },	// Beran-Setaou - Leze Smoka (the Blue Dragon lair, map 208)
		{ 9714, 1000 },	// Krolowa Dzungli - Starozytna Dzungla (map 366), the hardest Arezzo dungeon
	};
}

// ---------------------------------------------------------------- the engine's hooks
// char_item.cpp (server-patches/digirasta, MT2009_PLUS_AWAKENING_V1 /
// MT2009_PLUS_SOULSTONE9_V1): the refine past item_proto - the soul stones'
// steps (MT2009_PLUS_NO_AWAKENING_V1: no ritual, no awakened weapon).

// The result of a refine item_proto does not carry, or 0.
DWORD AwakeningSpecialRefineResult(DWORD dwVnum)
{
	int grade = 0, kind = 0;
	if (mt2009_awakening::IsRefinableStone(dwVnum, grade, kind))
		return mt2009_awakening::StoneVnum(grade + 1, kind);
	return 0;
}

// Its refine_proto recipe, or 0.
DWORD AwakeningSpecialRefineSet(DWORD dwVnum)
{
	int grade = 0, kind = 0;
	if (mt2009_awakening::IsRefinableStone(dwVnum, grade, kind))
		return mt2009_awakening::STONE_REFINE_SET_BASE + grade;
	return 0;
}

// MT2009_PLUS_NO_AWAKENING_V1: no weapon is an awakened one - every refine of
// a weapon burns and lowers as item_proto and the scroll say, and no forced
// sockets (the engine's "no burn", "scroll no burn" and "sockets" edits ask it).
bool AwakeningIsAwakenedWeapon(DWORD dwVnum)
{
	(void)dwVnum;
	return false;
}

// One boss table rolled for one kill: dwItemVnum into the loot for every row
// of the victim's race that comes up. true = something dropped.
static bool AwakeningRollBossTable(const mt2009_awakening::TBossDrop* table, size_t count, DWORD dwItemVnum,
		LPCHARACTER victim, LPCHARACTER killer, std::vector<LPITEM>& vec_item)
{
	const DWORD dwRace = victim->GetRaceNum();
	bool bDropped = false;
	for (size_t i = 0; i < count; ++i)
	{
		const mt2009_awakening::TBossDrop& d = table[i];
		if (d.dwMobVnum != dwRace || number(1, 10000) > d.wChance)
			continue;
		LPITEM item = ITEM_MANAGER::instance().CreateItem(dwItemVnum, 1, 0, true);
		if (!item)
		{
			sys_err("AWAKENING: no item %u in item_proto (drop of %u)", dwItemVnum, dwRace);
			continue;
		}
		vec_item.emplace_back(item);
		bDropped = true;
		sys_log(0, "AWAKENING: item %u dropped by %u (%s) for %s", dwItemVnum, dwRace, victim->GetName(), killer->GetName());
	}
	return bDropped;
}

// char_battle.cpp, CHARACTER::Reward: MT2009_PLUS_HEAVEN_OIL_V1, Olejek Niebios
// into the kill's loot beside ITEM_MANAGER::CreateDropItem (Kamien Przebudzenia
// no more - MT2009_PLUS_NO_AWAKENING_V1). true = something dropped.
bool AwakeningCreateBossDrop(LPCHARACTER victim, LPCHARACTER killer, std::vector<LPITEM>& vec_item)
{
	if (!victim || !killer || victim->IsPC())
		return false;

	// MT2009_PLUS_HEAVEN_OIL_V1 (Autor: Digi Rasta, v0.17): the oil.
	return AwakeningRollBossTable(mt2009_awakening::HEAVEN_OIL_BOSS_DROPS,
			sizeof(mt2009_awakening::HEAVEN_OIL_BOSS_DROPS) / sizeof(mt2009_awakening::HEAVEN_OIL_BOSS_DROPS[0]),
			mt2009_awakening::HEAVEN_OIL_VNUM, victim, killer, vec_item);
}

// ---------------------------------------------------------------- the bots
namespace
{
	// MT2009_PLUS_HEAVEN_OIL_V1 (Autor: Digi Rasta): a soul stone +5..+9 and Olejek
	// Niebios - a counter's or the bot's own stone step's, never the merchant's
	// (MT2009_PLUS_NO_AWAKENING_V1: Kamien Przebudzenia and the awakened weapons
	// are no such goods any more).
	bool IsPlayerBotAwakeningGoods(DWORD vnum)
	{
		return mt2009_awakening::IsHighSoulStone(vnum) || vnum == mt2009_awakening::HEAVEN_OIL_VNUM;
	}

	// ------------------------------------------------------------ the soul stone step
	// MT2009_PLUS_HEAVEN_OIL_V1 (Autor: Digi Rasta, nowy-system v0.17): a bot
	// of PLAYERBOT_STONE_STEP_MIN_LEVEL with a soul stone +4..+8 in its bag
	// raises it one grade at the Blacksmith by recipe 7200 + grade - Magiczny
	// Pyl, Olejek Niebios (1/1/2/2/3) and the fee - as a player does: a failure
	// destroys the stone. Only a bag stone (a seated one never leaves its
	// socket), never a companion's nor a pinned one, one step a visit, and
	// after every attempt or refusal not again for PLAYERBOT_STONE_STEP_RETRY_MS:
	// the planner asks HasPlayerBotSoulStoneStep, which says no while that runs
	// (the way MT2009_PLUS_BOT_TOWN_SPREAD_V1 shuts an anvil that refused
	// everything), so a missing oil or a refused step never loops the bot
	// between the town and the anvil. The lowest grade goes first: the
	// cheapest step with the best chance and the fewest oils.
	//
	// The oil (playerbot_economy.h): kept in the bag up to the next step's
	// count while a bag stone waits for it (GetPlayerBotRefineMaterialReserve,
	// the counter lists only what is over), bought off a counter when the fee
	// and the dust are there and only the oil is short
	// (PlayerBotIsShortOfRefineMaterial), priced in playerbot_price_tables.h,
	// never sold to the merchant (IsPlayerBotAwakeningGoods).
	const int PLAYERBOT_STONE_STEP_MIN_LEVEL = 75;
	const DWORD PLAYERBOT_STONE_STEP_RETRY_MS = 10 * 60 * 1000;
	std::map<DWORD, DWORD> s_mapPlayerBotStoneStepRetry;

	enum EPlayerBotStoneStepAsk
	{
		PLAYERBOT_STONE_STEP_KEEP,	// a bag stone waits for a step
		PLAYERBOT_STONE_STEP_WANT,	// and the fee and the dust are there
		PLAYERBOT_STONE_STEP_DO,	// and the oil too: the anvil can take it
	};

	// The bag stone of this bot's next step and its recipe, or NULL.
	LPITEM FindPlayerBotSoulStoneStep(LPCHARACTER ch, EPlayerBotStoneStepAsk ask, const TRefineTable** outRecipe)
	{
		if (!ch || !ch->IsItemLoaded() || (int)ch->GetLevel() < PLAYERBOT_STONE_STEP_MIN_LEVEL ||
				IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return NULL;
		LPITEM best = NULL;
		const TRefineTable* bestRecipe = NULL;
		int bestGrade = 99;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			int grade = 0, kind = 0;
			if (!item || item->GetCell() != cell || item->IsEquipped() ||
					!mt2009_awakening::IsRefinableStone(item->GetVnum(), grade, kind) || grade >= bestGrade ||
					IsPlayerBotSidekickPinned(ch, item))
				continue;
			const TRefineTable* recipe = CRefineManager::instance().GetRefineRecipe(
					mt2009_awakening::STONE_REFINE_SET_BASE + grade);
			if (!recipe)
				continue;
			if (ask != PLAYERBOT_STONE_STEP_KEEP)
			{
				// The fee twice over the reserve: the step and as much again.
				const long long fee = (long long)ch->ComputeRefineFee(recipe->cost);
				if ((long long)ch->GetGold() < fee * 2 + (long long)GetPlayerBotReservedGold(ch))
					continue;
				bool materials = true;
				for (int m = 0; m < recipe->material_count && materials; ++m)
				{
					const DWORD vnum = recipe->materials[m].vnum;
					if (vnum == 0 || (vnum == mt2009_awakening::HEAVEN_OIL_VNUM && ask != PLAYERBOT_STONE_STEP_DO))
						continue;
					if ((int)ch->CountSpecifyItem(vnum) < recipe->materials[m].count)
						materials = false;
				}
				if (!materials)
					continue;
			}
			best = item;
			bestRecipe = recipe;
			bestGrade = grade;
		}
		if (outRecipe)
			*outRecipe = bestRecipe;
		return best;
	}

	// How many oils the next step's recipe takes (0 without a step).
	int GetPlayerBotSoulStoneStepOil(LPCHARACTER ch, EPlayerBotStoneStepAsk ask)
	{
		const TRefineTable* recipe = NULL;
		if (!FindPlayerBotSoulStoneStep(ch, ask, &recipe) || !recipe)
			return 0;
		for (int m = 0; m < recipe->material_count; ++m)
			if (recipe->materials[m].vnum == mt2009_awakening::HEAVEN_OIL_VNUM)
				return recipe->materials[m].count;
		return 0;
	}

	// playerbot_economy.h: the oil kept back for the next step.
	int GetPlayerBotHeavenOilKeep(LPCHARACTER ch)
	{
		return GetPlayerBotSoulStoneStepOil(ch, PLAYERBOT_STONE_STEP_KEEP);
	}

	// playerbot_economy.h: short of the oil and of nothing else for the step.
	bool PlayerBotWantsHeavenOil(LPCHARACTER ch)
	{
		const int need = GetPlayerBotSoulStoneStepOil(ch, PLAYERBOT_STONE_STEP_WANT);
		return need > 0 && (int)ch->CountSpecifyItem(mt2009_awakening::HEAVEN_OIL_VNUM) < need;
	}

	bool IsPlayerBotSoulStoneStepResting(LPCHARACTER ch, DWORD dwNow)
	{
		std::map<DWORD, DWORD>::iterator it = s_mapPlayerBotStoneStepRetry.find(ch->GetPlayerID());
		if (it == s_mapPlayerBotStoneStepRetry.end())
			return false;
		if ((int)(dwNow - it->second) >= 0)
		{
			s_mapPlayerBotStoneStepRetry.erase(it);
			return false;
		}
		return true;
	}

	// A reason for the anvil (HasPlayerBotRefineOpportunity).
	bool HasPlayerBotSoulStoneStep(LPCHARACTER ch)
	{
		return ch && !IsPlayerBotSoulStoneStepResting(ch, get_dword_time()) &&
				FindPlayerBotSoulStoneStep(ch, PLAYERBOT_STONE_STEP_DO, NULL) != NULL;
	}

	// At the Blacksmith (ManagePlayerBotRefining): one step.
	// DoRefine reads recipe 7200 + grade through the engine hook, takes the
	// dust, the oil and the fee, and puts the stone +1 in the same cell - or
	// destroys the stone.
	bool ManagePlayerBotSoulStoneStep(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || IsPlayerBotSoulStoneStepResting(ch, dwNow))
			return false;
		LPITEM stone = FindPlayerBotSoulStoneStep(ch, PLAYERBOT_STONE_STEP_DO, NULL);
		if (!stone)
			return false;
		// Whatever happens below, not again for a while.
		s_mapPlayerBotStoneStepRetry[ch->GetPlayerID()] = dwNow + PLAYERBOT_STONE_STEP_RETRY_MS;

		const DWORD oldVnum = stone->GetVnum();
		int grade = 0, kind = 0;
		mt2009_awakening::StoneGradeKind(oldVnum, grade, kind);
		const DWORD result = mt2009_awakening::StoneVnum(grade + 1, kind);
		const WORD cell = stone->GetCell();
		const YANG goldBefore = ch->GetGold();
		const int oilBefore = (int)ch->CountSpecifyItem(mt2009_awakening::HEAVEN_OIL_VNUM);
		// A guild smith's VID would make it a guild refine, which the engine
		// refuses for the stone steps.
		ch->SetRefineNPC(NULL);
		const bool attempted = ch->DoRefine(stone, false, REFINE_TYPE_NORMAL);
		// The stone is gone or replaced either way: only the cell is asked.
		LPITEM after = ch->GetInventoryItem(cell);
		const bool raised = after && after->GetVnum() == result;
		const int oilAfter = (int)ch->CountSpecifyItem(mt2009_awakening::HEAVEN_OIL_VNUM);
		// (A Goblin's blessing takes no materials, so the fee is asked too.)
		if (attempted && (raised || oilAfter < oilBefore || (long long)ch->GetGold() < (long long)goldBefore))
		{
			sys_log(0, "PLAYERBOT_STONE_STEP: pid=%u name=%s from=%u to=%u %s oil=%d->%d gold=%lld->%lld",
					ch->GetPlayerID(), ch->GetName(), oldVnum, result, raised ? "raised" : "burnt",
					oilBefore, oilAfter, (long long)goldBefore, (long long)ch->GetGold());
			SetPlayerBotAction(state, BOT_ACTION_REFINE, dwNow);
			return true;
		}
		sys_err("PLAYERBOT_STONE_STEP: refused pid=%u name=%s vnum=%u attempted=%d oil=%d dust=%d gold=%lld",
				ch->GetPlayerID(), ch->GetName(), oldVnum, attempted ? 1 : 0, oilAfter,
				(int)ch->CountSpecifyItem(PLAYERBOT_MAGIC_DUST_VNUM), (long long)ch->GetGold());
		return false;
	}
}

#endif
