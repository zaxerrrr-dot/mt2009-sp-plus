// MT2009_PLUS_PD_BONUS_V1 (attr max, server-patches/pdbonus): the bonus maxima of this world for the item tooltip's gold
// line (the owner, 3 November 2026: "zlote wyroznienie max wartosci bonusa, liczone wg limitow danego swiata"). The
// client had one fixed table per bonus mode (root/localeinfo_point.py ATTR_MAX_VALUES, mt2009 / global); the truth is
// what the game loaded from world.item_attr and world.item_attr_rare - the bonus mode's migrator and the Seban panel's
// editor write those - per item kind: a bonus's value at the highest level its attribute set may roll (the same
// lValues[min(level, max level of the set) - 1] CItem::AddAttr / AddRareAttribute / Bonus67 give).
//
// At every login (input_login.cpp) the client hears:
//   AttrMaxBegin <sets>                              the number of attribute sets (EAttributeSet order)
//   AttrMax <rare> <apply>:<v0>/<v1>/.../<vN-1> ...  rare 0 = item_attr (bonuses 1-5), 1 = item_attr_rare (6/7);
//                                                    v = the set's maximum, 0 = the set never rolls it
//   AttrMaxEnd
// (root/localeinfo_point.py SetServerAttrMax, game.py, uitooltip.py). An item's lines are its own: nothing changes on
// the server's side of an item.
#include "stdafx.h"
#include "constants.h"
#include "char.h"
#include "desc.h"

bool BonusModeGlobal();

namespace
{
	long Mt2009AttrMaxValue(const TItemAttrTable& r, int iSet)
	{
		const int iLevel = MIN((int) r.bMaxLevelBySet[iSet], (int) ITEM_ATTRIBUTE_MAX_LEVEL);
		if (iLevel <= 0)
			return 0;
		long lValue = r.lValues[iLevel - 1];
#ifdef ENABLE_PENDANT_SYSTEM
		// BonusModeAttrValue (playerbot_bonus_mode.cpp): in global mode a talisman's fire / lightning / wind resistance is
		// 5% a level, not the row's armour values.
		if (iSet == ATTRIBUTE_SET_PENDANT && BonusModeGlobal() &&
				(r.dwApplyIndex == POINT_RESIST_FIRE || r.dwApplyIndex == POINT_RESIST_ELEC || r.dwApplyIndex == POINT_RESIST_WIND))
			lValue = 5 * iLevel;
#endif
		return lValue;
	}

	void Mt2009AttrMaxSend(LPCHARACTER ch, const TItemAttrMap& table, int iRare)
	{
		std::string line;
		for (TItemAttrMap::const_iterator it = table.begin(); it != table.end(); ++it)
		{
			const TItemAttrTable& r = it->second;
			if (!it->first || r.dwApplyIndex != it->first)	// operator[] leaves empty rows behind
				continue;
			std::string token = std::to_string(it->first) + ":";
			bool bAny = false;
			for (int iSet = 0; iSet < ATTRIBUTE_SET_MAX_NUM; ++iSet)
			{
				const long lValue = Mt2009AttrMaxValue(r, iSet);
				bAny = bAny || lValue != 0;
				if (iSet)
					token += "/";
				token += std::to_string(lValue);
			}
			if (!bAny)
				continue;
			if (!line.empty() && line.size() + token.size() + 1 > 400)
			{
				ch->ChatPacket(CHAT_TYPE_COMMAND, "AttrMax %d %s", iRare, line.c_str());
				line.clear();
			}
			if (!line.empty())
				line += " ";
			line += token;
		}
		if (!line.empty())
			ch->ChatPacket(CHAT_TYPE_COMMAND, "AttrMax %d %s", iRare, line.c_str());
	}
}

void Mt2009AttrMaxOnLogin(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot())
		return;
	ch->ChatPacket(CHAT_TYPE_COMMAND, "AttrMaxBegin %d", (int) ATTRIBUTE_SET_MAX_NUM);
	Mt2009AttrMaxSend(ch, g_map_itemAttr, 0);
	Mt2009AttrMaxSend(ch, g_map_itemRare, 1);
	ch->ChatPacket(CHAT_TYPE_COMMAND, "AttrMaxEnd");
}
