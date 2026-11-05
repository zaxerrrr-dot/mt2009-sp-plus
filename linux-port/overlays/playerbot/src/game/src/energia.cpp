// MT2009_PLUS_ENERGY_V1 - System Energii (server-patches/energia/README.md).
//
// The pl-wiki ("System Energii", "Krysztal Energii"): a Krysztal Energii (51002) raises the bonuses of the
// equipment by 1, 3, 5, 7 or 10 % (the crystal's own value, set when it is made) for 2 hours of play. It is a
// blend item (blend.txt): using it puts AFFECT_BLEND on POINT_ENERGY (128) with that value; the affect counts down
// only while the character is in the game, like every affect. The energy bar of the client's taskbar shows it
// (player.ENERGY / ENERGY_END_TIME - the exe fills them from the affect and the point change).
//
// The bonuses are the official ones (CBuffOnAttributes of the energy, which our engine never had - only the
// g_aBuffOnAttrPoints table and the empty m_map_buff_on_attrs were left): the random bonuses (attributes) of
// the items worn as body, head, shoes, bracelet, weapon, necklace, earrings, shield and gloves, summed by type,
// each sum times the per cent. The fixed bonuses of an item's proto do not grow (as on the official server).
//
// Mt2009EnergyRefresh takes back what it gave last time (m_mapMt2009EnergyApplied) and gives the share of the
// items worn now, so it can run any time: the energy's point change (the affect on, off, the recompute),
// an item put on or taken off (CItem::EquipTo / Unequip). ComputePoints zeroes every point, so it empties the
// map first; its RefreshAffect gives the energy again after the worn items.
#include "stdafx.h"
#include <map>
#include "constants.h"
#include "char.h"
#include "item.h"

namespace
{
	const WORD s_aMt2009EnergyWear[] = { WEAR_BODY, WEAR_HEAD, WEAR_FOOTS, WEAR_WRIST, WEAR_WEAPON, WEAR_NECK, WEAR_EAR,
		WEAR_SHIELD, WEAR_GLOVE };
}

int Bonus67AttrValue(LPITEM item, int iSlot, WORD bType, int iValue); // MT2009_PLUS_WIDE_ATTR_V1
extern int g_iMt2009PlusComputeDepth; // item.cpp: CHARACTER::ComputePoints nesting

void Mt2009EnergyRefresh(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC())
		return;

	const int pct = MINMAX(0, ch->GetPoint(POINT_ENERGY), 100);
	if (pct <= 0 && ch->m_mapMt2009EnergyApplied.empty())
		return;

	std::map<WORD, int> want;
	if (pct > 0)
	{
		std::map<WORD, long long> sum;
		for (size_t s = 0; s < sizeof(s_aMt2009EnergyWear) / sizeof(s_aMt2009EnergyWear[0]); ++s)
		{
			LPITEM item = ch->GetWear(s_aMt2009EnergyWear[s]);
			if (!item)
				continue;
			for (int i = 0; i < ITEM_ATTRIBUTE_MAX_NUM; ++i)
			{
				const WORD type = item->GetAttributeType(i);
				if (!type || ch->IsUtilityPoint(type) || type == POINT_ENERGY)
					continue;
				// "1./2./3./4./5. dodany bonus +x%" raise another line of the item; the energy raises that line
				if (type >= POINT_FIRST_ATTRIBUTE_BONUS && type <= POINT_FIFTH_ATTRIBUTE_BONUS)
					continue;
				const TPlayerItemAttribute& ia = item->GetAttribute(i);
				sum[type] += Bonus67AttrValue(item, i, type, ia.sValue);
			}
		}
		for (std::map<WORD, long long>::const_iterator it = sum.begin(); it != sum.end(); ++it)
		{
			const int v = (int) (it->second * pct / 100);
			if (v)
				want[it->first] = v;
		}
	}

	if (want == ch->m_mapMt2009EnergyApplied)
		return;

	// the map is swapped before the point changes: a point change never comes back here with the old map
	std::map<WORD, int> old;
	old.swap(ch->m_mapMt2009EnergyApplied);
	ch->m_mapMt2009EnergyApplied = want;

	for (std::map<WORD, int>::const_iterator it = old.begin(); it != old.end(); ++it)
	{
		std::map<WORD, int>::const_iterator n = want.find(it->first);
		const int delta = (n == want.end() ? 0 : n->second) - it->second;
		if (delta)
			ch->PointChange(it->first, delta);
	}
	for (std::map<WORD, int>::const_iterator it = want.begin(); it != want.end(); ++it)
	{
		if (old.find(it->first) == old.end())
			ch->PointChange(it->first, it->second);
	}
	// inside ComputePoints the battle points were counted already and every later point change keeps them; on its own
	// (an item put on or taken off, the crystal used, the energy over) they are counted again, as CItem::EquipTo does
	if (g_iMt2009PlusComputeDepth <= 0)
		ch->ComputeBattlePoints();
}
