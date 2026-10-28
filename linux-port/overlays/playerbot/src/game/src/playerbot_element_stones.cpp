// MT2009_PLUS_ELEMENT_STONES_V1: Kamien Ochrony Zywiolow (39120) and Kamien Mocy Zywiolow (39119) - only one of the two
// on a character at a time (the owner, 28 October 2026: "Mozna zalozyc tylko jeden z nich").
//
// The stones are ITEM_UNIQUE amulets of the two unique slots (tools/kamienie_zywiolow, kamienie_zywiolow.sql); their six
// bonuses each are world.item_extra_apply lines (MT2009_PLUS_ITEM_EXTRA_APPLY_V1). The engine's own rule for the unique
// slots (CHARACTER::CanEquipNow: IsSameSpecialGroup) already refuses the same vnum twice, in English; the second stone
// of the other kind it would let on. CanEquipNow's first hook (Mt2009SwitchbotRefuseEquip, playerbot_switchbot.cpp) asks
// Mt2009ElementStoneRefuseEquip first: a stone, while a stone (either kind) is worn in a unique slot and is not the item
// itself, is refused with a message in Polish - a player drags the worn one off first. The bots' stone
// (playerbot_element_stones.h) goes through the same check.
#include "stdafx.h"
#include "char.h"
#include "item.h"

bool Mt2009IsElementStone(DWORD dwVnum)
{
	return dwVnum == 39119 || dwVnum == 39120;
}

bool Mt2009ElementStoneRefuseEquip(LPCHARACTER ch, LPITEM item)
{
	if (!ch || !item || !Mt2009IsElementStone(item->GetVnum()))
		return false;
	for (int wear = WEAR_UNIQUE1; wear <= WEAR_UNIQUE2; ++wear)
	{
		LPITEM worn = ch->GetWear(wear);
		if (!worn || worn == item || !Mt2009IsElementStone(worn->GetVnum()))
			continue;
		// "Mozesz nosic tylko jeden Kamien Zywiolow naraz (Ochrony albo Mocy)." - cp1250
		ch->ChatPacket(CHAT_TYPE_INFO, "Mo\xbf" "esz nosi\xe6 tylko jeden Kamie\xf1 \xafywio\xb3\xf3w naraz (Ochrony albo Mocy). "
				"Najpierw zdejmij ten, kt\xf3ry nosisz.");
		return true;
	}
	return false;
}
