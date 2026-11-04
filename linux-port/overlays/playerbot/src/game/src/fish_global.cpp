// MT2009_PLUS_FISHING_GLOBAL_V1: fishing as on the global server (the owner, 4 November 2026; cache/yohara/
// decyzje-lowienie-mikstury.md "Lowienie", cache/yohara/lowienie-analiza.md) - the engine's part. The hooks are
// server-patches/fishglobal (fishing.cpp, char_item.cpp, item_manager.cpp); the catch is quest/libs/fishing
// (linux-port/docker/game/lowienie: fishing.lua, fishing_drop.lua), the rod upgrade dialog quest rybak_wedki, the
// golden tuna quest zloty_tunczyk, the items mariadb/playerbot/yohara_lowienie.sql.
//
//   Mt2009FishMindOrTuna(ch)   Rybie Wnetrznosci (the ItemShop premium PREMIUM_FISH_MIND, or 71008 / 72013-72015 worn -
//                              unique group 10009) or the golden tuna's bonus (affect 742): the bite chance's +10 of
//                              fishing::GetFishingChance (the wiki: "the chance rises with Rybie Wnetrznosci and the
//                              Bonus Zlotego Tunczyka"; before, only the premium counted - a worn 71008 did nothing).
//   Mt2009FishNimfaDrop(...)   Skrzynia Nimfy Wodnej (27625) from every monster of level 70 or more (not a Metin), as
//                              a monster's "Type drop" row: event flag nimfa_chest_drop = the row's value x 100 (0 -
//                              the default 200, a row "2" = 0.5% a kill; below 0 - off), with the kill's level
//                              difference and drop bonuses (ITEM_MANAGER::CreateDropItem's iDeltaPercent / iRandRange).
#include "stdafx.h"
#include "constants.h"
#include "utils.h"
#include "config.h"
#include "char.h"
#include "desc.h"
#include "item.h"
#include "item_manager.h"
#include "questmanager.h"
#include "affect.h"
#include "unique_item.h"

namespace
{
	// the golden tuna's bonus (quest zloty_tunczyk: value 200 the 60 minutes of a release, 250 the 5 minutes of the
	// bait - the rare fish x2 / x2.5 in fishing_drop.lua) and Mokre Szaty (743, movement -50 for 5 minutes); 740-759
	// were free (730 Potega madrosci, 760 the relics)
	const DWORD FISHGLOBAL_AFFECT_GOLD_TUNA = 742;
	const DWORD FISHGLOBAL_NIMFA_CHEST = 27625;
	const int FISHGLOBAL_NIMFA_MIN_LEVEL = 70;
	const int FISHGLOBAL_NIMFA_DEFAULT_X100 = 200;
}

bool Mt2009FishMindOrTuna(LPCHARACTER ch)
{
	if (!ch)
		return false;
	return ch->GetPremiumRemainSeconds(PREMIUM_FISH_MIND) > 0 || ch->IsEquipUniqueGroup(UNIQUE_GROUP_FISH_MIND) ||
		ch->FindAffect(FISHGLOBAL_AFFECT_GOLD_TUNA) != NULL;
}

void Mt2009FishNimfaDrop(LPCHARACTER pkChr, LPCHARACTER pkKiller, int iDeltaPercent, int iRandRange,
		std::vector<LPITEM>& vec_item)
{
	if (!pkChr || !pkKiller || !pkChr->IsMonster() || pkChr->IsStone() || iRandRange <= 0)
		return;
	if ((int)pkChr->GetLevel() < FISHGLOBAL_NIMFA_MIN_LEVEL)
		return;
	int x100 = quest::CQuestManager::instance().GetEventFlag("nimfa_chest_drop");
	if (x100 < 0)
		return;
	if (x100 == 0)
		x100 = FISHGLOBAL_NIMFA_DEFAULT_X100;
	// a "Type drop" row's dwPct is its value x 10000 (item_manager_read_tables.cpp), here value x 100 -> x 100
	const long long pct = (long long)x100 * 100LL * iDeltaPercent / 100LL;
	if (pct < number(1, iRandRange))
		return;
	LPITEM item = ITEM_MANAGER::instance().CreateItem(FISHGLOBAL_NIMFA_CHEST, 1, 0, true);
	if (!item)
		return;
	vec_item.emplace_back(item);
	if (pkKiller->IsPC() && pkKiller->GetDesc() && !pkKiller->GetDesc()->IsBot())
		sys_log(0, "FISHGLOBAL: Skrzynia Nimfy Wodnej dropped by %u (level %d) for %s pid=%u",
				pkChr->GetRaceNum(), (int)pkChr->GetLevel(), pkKiller->GetName(), pkKiller->GetPlayerID());
}
