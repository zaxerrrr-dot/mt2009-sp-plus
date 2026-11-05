// MT2009_PLUS_GLOBAL_BONUS_V1 - M2_BONUS_MODE: mt2009 (the default) or global (2.2.31 "Bonusy jak na
// serwerze globalnym", the owner 14 October 2026; server-patches/bonusyglobal/README.md).
//
// The migrator (mariadb/playerbot/apply.sh) switches world.item_attr and the monsters' elements and writes the
// world event flag m2_bonus_global (1 = global) at every start; the cores read it here:
//   * BonusModeElementResist - a player's element resistance against a monster of that element
//     (playerbot_elements.cpp): in BOTH modes the full percent, cap 80% (the owner, 23 October 2026 - 1% of
//     resistance = 1% less damage; from 14 October to 23 October it was 30% of it);
//   * BonusModeItemDropBonus - the double-item chance line (POINT_ITEM_DROP_BONUS of a bracelet or earrings) adds
//     to the drop chance as the thief's gloves and the premium do (item_manager.cpp, the upstream 2.2.31); 0 in mt2009;
//   * BonusModeAttrValue - one item_attr row holds one set of values for every item: global gives the armour's
//     fire/lightning/wind resistance 2-15%, and a talisman (ATTRIBUTE_SET_PENDANT) keeps its own 5-25% of those
//     three (5% a level), as in mt2009 (item_attribute.cpp, CItem::AddAttr).
// The chance of an experience bonus (POINT_EXP_DOUBLE_BONUS) needs nothing: the engine has always given it
// (char_battle.cpp); only global rolls it on items.
#include "stdafx.h"
#include "mt2009_wideattr.h" // MT2009_PLUS_WIDE_ATTR_V1
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
	// MT2009_PLUS_ELEMENT_RESIST_FULL_V1 (the owner, 23 October 2026: "kazdy procent odpornosci zmniejsza obrazenia
	// o 1%"): the full percent again, in both modes (the cap of 80% stays in playerbot_elements.cpp); the element
	// power (the attacker's side) is unchanged. Was MT2009_PLUS_ELEMENT_RESIST_30_V1: 30% of it.
	return resist;
}

int BonusModeItemDropBonus(LPCHARACTER killer)
{
	if (!killer || !BonusModeGlobal())
		return 0;
	return MAX(0, killer->GetPoint(POINT_ITEM_DROP_BONUS));
}

// MT2009_PLUS_SWITCHBOT_ATTR_VALUES_V1: the same rule by attribute set, for what has no item at hand - the switchbot's
// list of bonuses and their maxima (playerbot_switchbot.cpp SendItemAttributeInformations) gives exactly what
// CItem::AddAttr gives an item of that set.
long BonusModeSetAttrValue(int iSet, WORD apply, BYTE level, long value) // MT2009_PLUS_WIDE_ATTR_V1
{
#ifdef ENABLE_PENDANT_SYSTEM
	if (level > 0 && iSet == ATTRIBUTE_SET_PENDANT &&
			(apply == POINT_RESIST_FIRE || apply == POINT_RESIST_ELEC || apply == POINT_RESIST_WIND) && BonusModeGlobal())
		return 5 * MIN(5, (int)level);
#endif
	return value;
}

long BonusModeAttrValue(CItem* item, TMt2009PointNum apply, BYTE level, long value) // MT2009_PLUS_WIDE_ATTR_V1 (mt2009_wideattr.h)
{
	if (!item)
		return value;
	return BonusModeSetAttrValue(item->GetAttributeSetIndex(), apply, level, value);
}
