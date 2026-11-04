#ifndef __INC_METIN2_PLAYERBOT_NEWPET_H__
#define __INC_METIN2_PLAYERBOT_NEWPET_H__

// MT2009_PLUS_NEW_PET_V1 is retired (the owner, 4 November 2026: the official growth pet replaces it -
// MT2009_PLUS_GROWTH_PET_V1, growth_pet.cpp, server-patches/pety/README.md). Its engine hooks of
// server-patches/playerqol stay in the tree and land here:
//   - NewPetUseItem (char_item.cpp, ITEM_PET subtypes but the seals): never reached - the growth pet's own hook
//     (MT2009_PLUS_GROWTH_PET_V1 (use)) runs first at the top of UseItemEx; kept as a refusal;
//   - NewPetOnExp (char_battle.cpp): nothing - the growth pet takes the kill's experience in its own hook
//     (MT2009_PLUS_GROWTH_PET_V1 (exp), with the owner's bonuses); the old Metin / egg drops are gone (the wiki's drops:
//     linux-port/docker/game/pety);
//   - NewPetApplyPoints (char.cpp ComputePoints): the summoned growth pet's bonuses;
//   - do_newpet (cmd.cpp "/newpet", the old window's protocol): a pointer to the new window.
// player.newpet_pet stays as the old pets' backup; server-patches/pety's migration made every row a growth pet.
// Included once, from playerbot_manager.cpp.

#include "growth_pet.h"

bool NewPetUseItem(LPCHARACTER ch, LPITEM item)
{
	if (ch && ch->GetDesc() && !ch->GetDesc()->IsBot())
		ch->ChatPacket(CHAT_TYPE_INFO, "Tego przedmiotu u\xbfywa si\xea w oknie zwierzaka (klawisz U).");
	return false;
}

void NewPetOnExp(LPCHARACTER victim, LPCHARACTER to, int exp)
{
}

void NewPetApplyPoints(LPCHARACTER ch)
{
	if (ch && ch->IsPC())
		growth_pet::ApplyPoints(ch);
}

ACMD(do_newpet)
{
	if (ch && ch->GetDesc() && !ch->GetDesc()->IsBot())
		ch->ChatPacket(CHAT_TYPE_INFO, "Dawny system pet\xf3w zast\xb9pi\xb3 System Zwierz\xb9t Domowych - okno zwierzaka otwiera klawisz U.");
}

#endif
