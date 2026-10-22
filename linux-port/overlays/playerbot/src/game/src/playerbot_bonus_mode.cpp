// MT2009_PLUS_GLOBAL_BONUS_V1 - M2_BONUS_MODE: mt2009 (the default) or global (Tieru's 2.2.31 "Bonusy jak na
// serwerze globalnym", the owner 14 October 2026; server-patches/bonusyglobal/README.md).
//
// The migrator (mariadb/playerbot/apply.sh) switches world.item_attr and the monsters' elements and writes the
// world event flag m2_bonus_global (1 = global) at every start; the cores read it here:
//   * BonusModeElementResist - a player's element resistance against a monster of that element
//     (playerbot_elements.cpp): mt2009 takes its full percent off (cap 80%, Digi Rasta's rule); global, as the
//     original game's code (battle.cpp's commented apply_elemental_resistances, which Tieru switched on): 30% of
//     it - 15% resistance = 4.5% less damage;
//   * BonusModeItemDropBonus - the double-item chance line (POINT_ITEM_DROP_BONUS of a bracelet or earrings) adds
//     to the drop chance as the thief's gloves and the premium do (item_manager.cpp, Tieru's 2.2.31); 0 in mt2009;
//   * BonusModeAttrValue - one item_attr row holds one set of values for every item: global gives the armour's
//     fire/lightning/wind resistance 2-15%, and a talisman (ATTRIBUTE_SET_PENDANT) keeps its own 5-25% of those
//     three (5% a level), as in mt2009 (item_attribute.cpp, CItem::AddAttr).
// The chance of an experience bonus (POINT_EXP_DOUBLE_BONUS) needs nothing: the engine has always given it
// (char_battle.cpp); only global rolls it on items.
#include "stdafx.h"
#include "char.h"
#include "item.h"
#include "questmanager.h"

bool BonusModeGlobal()
{
	return quest::CQuestManager::instance().GetEventFlag("m2_bonus_global") != 0;
}

int BonusModeElementResist(int resist)
{
	if (resist <= 0)
		return 0;
	return BonusModeGlobal() ? resist * 30 / 100 : resist;
}

int BonusModeItemDropBonus(LPCHARACTER killer)
{
	if (!killer || !BonusModeGlobal())
		return 0;
	return MAX(0, killer->GetPoint(POINT_ITEM_DROP_BONUS));
}

long BonusModeAttrValue(CItem* item, BYTE apply, BYTE level, long value)
{
#ifdef ENABLE_PENDANT_SYSTEM
	if (item && level > 0 && item->GetAttributeSetIndex() == ATTRIBUTE_SET_PENDANT &&
			(apply == POINT_RESIST_FIRE || apply == POINT_RESIST_ELEC || apply == POINT_RESIST_WIND) && BonusModeGlobal())
		return 5 * MIN(5, (int)level);
#endif
	return value;
}
