// MT2009_PLUS_ADDEQ_V1: Druga strona ekwipunku - the "Official Additional Equipment Page" package (the owner, 28 October
// 2026: "Add this too to the client."), rebuilt on our engine. server-patches/addeq/README.md has the whole picture; the
// engine's hooks are server-patches/addeq (edits.json) and call the methods and free functions of this file.
//
// What the package does: a second set of the equipment slots (body, head, shoes, bracelet, weapon, necklace, earrings,
// arrows, shield, belt, talisman, gloves); the player unlocks it once with an item (38306 bound / 76055 tradeable, which
// gives the support skill 200 "Zmiana strony ekwipunku"), switches with the skill or the page tabs of the equipment
// window, and only the active page's items give their bonuses. The package keeps both pages worn (twelve new wear
// cells WEAR_SECOND_*, a renumbered wear enum, every GetWear(WEAR_WEAPON) of the engine turned into GetEquipWear) -
// that is a new wear layout, which the old clients (their wear, Dragon Soul and belt cells are numbers) cannot take.
//
// Here instead: the inactive page lies in a hidden store of the character - 32 cells after the belt's inventory
// (MT2009_ADDEQ_SLOT_START = BELT_INVENTORY_SLOT_END, one cell per wear cell), saved as window INVENTORY, pos 308-339
// (the DB's window enum and every packet unchanged) - and a switch swaps the worn items of the paged slots with the
// store's: the engine's own Unequip / EquipTo, so the bonuses, looks, set bonuses, timers and refine events are what a
// hand change does, and only the worn page counts. The store is never sent to the client and no client packet reaches
// it (TItemPos validity, GetItem and every handler stay at INVENTORY_AND_EQUIP_SLOT_MAX): an old client sees the
// active page only, as worn equipment.
//
// Paged: WEAR_BODY, HEAD, FOOTS, WRIST, WEAPON, NECK, EAR, ARROW, SHIELD, PENDANT (talisman), GLOVE. Shared (as the
// package's uniques and costumes): the rings, costumes, mount, sash, aura, Buffi's slots and the belt - a belt holds the
// belt inventory's items, which a page switch cannot move.
//
// Rules of the switch (package: no trade / shop / storage / crafting window, 5 seconds between switches; ours added: the
// engine's 1.5 s "stand still" after an attack or skill, not dead / stunned / transformed / fishing / mining): every
// item of the target page must fit the character now (class, sex, level, Champion level, stats - the bonus reset can
// lower them) and every worn item must come off (not IRREMOVABLE, not locked) - else nothing moves and the chat says
// which item. A weapon costume that no longer fits the new weapon goes into the bag.
//
// State: quest flags addeq.unlocked (1) and addeq.page (0 = I, 1 = II); the skill 200 at level 1 shows the switch in the
// support skills (restored at the hello if a skill reset cleared it). Commands (root/uiaddeq.py):
//   /addeq hello        the client's hello after every load: "addeq_page <unlocked> <page>" back
//   /addeq <0|1>        the page tabs I / II of the equipment window
//   /addeq toggle       the other page
// Bots never: they have neither the item nor the hello (their second set, playerbot_element_second_set.h, swaps through
// the bag and could use this store later).
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "utils.h"
#include "char.h"
#include "desc.h"
#include "item.h"
#include "item_manager.h"
#include "cmd.h"

#include <unordered_map>

namespace
{
	const DWORD ADDEQ_SKILL_VNUM = 200;
	const DWORD ADDEQ_ITEM_BOUND = 38306;
	const DWORD ADDEQ_ITEM_TRADE = 76055;
	const DWORD ADDEQ_SWITCH_MS = 5000;
	const DWORD ADDEQ_STILL_MS = 1500;
	const char* const ADDEQ_FLAG_UNLOCKED = "addeq.unlocked";
	const char* const ADDEQ_FLAG_PAGE = "addeq.page";

	const BYTE ADDEQ_WEARS[] = { WEAR_BODY, WEAR_HEAD, WEAR_FOOTS, WEAR_WRIST, WEAR_WEAPON, WEAR_NECK, WEAR_EAR, WEAR_ARROW,
		WEAR_SHIELD, WEAR_PENDANT, WEAR_GLOVE };

	std::unordered_map<DWORD, DWORD> s_mapAddeqLastSwitch;

	bool AddeqIsUnlocked(LPCHARACTER ch)
	{
		return ch->GetQuestFlag(ADDEQ_FLAG_UNLOCKED) != 0 || ch->GetSkillLevel(ADDEQ_SKILL_VNUM) > 0;
	}

	int AddeqPage(LPCHARACTER ch)
	{
		return ch->GetQuestFlag(ADDEQ_FLAG_PAGE) == 1 ? 1 : 0;
	}

	void AddeqSendState(LPCHARACTER ch)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "addeq_page %d %d", AddeqIsUnlocked(ch) ? 1 : 0, AddeqPage(ch));
	}

	// the skill 200 at level 1 while the page is unlocked (a skill reset clears it)
	void AddeqSyncSkill(LPCHARACTER ch)
	{
		if (ch->GetQuestFlag(ADDEQ_FLAG_UNLOCKED) != 0 && ch->GetSkillLevel(ADDEQ_SKILL_VNUM) == 0)
		{
			ch->SetSkillLevel(ADDEQ_SKILL_VNUM, 1);
			ch->SkillLevelPacket();
		}
	}

	// what CanEquipNow checks of the item itself - silent, for an item that was worn on the same cell before
	bool AddeqFits(LPCHARACTER ch, LPITEM item)
	{
		if (item->IsExchanging())
			return false;

		switch (ch->GetJob())
		{
			case JOB_WARRIOR:	if (item->GetAntiFlag() & ITEM_ANTIFLAG_WARRIOR) return false; break;
			case JOB_ASSASSIN:	if (item->GetAntiFlag() & ITEM_ANTIFLAG_ASSASSIN) return false; break;
			case JOB_SHAMAN:	if (item->GetAntiFlag() & ITEM_ANTIFLAG_SHAMAN) return false; break;
			case JOB_SURA:		if (item->GetAntiFlag() & ITEM_ANTIFLAG_SURA) return false; break;
#ifdef ENABLE_WOLFMAN_CHARACTER
			case JOB_WOLFMAN:	if (item->GetAntiFlag() & ITEM_ANTIFLAG_WOLFMAN) return false; break;
#endif
		}

		if (IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_MALE) && SEX_MALE == GET_SEX(ch))
			return false;
		if (IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_FEMALE) && SEX_FEMALE == GET_SEX(ch))
			return false;

		const TItemTable* proto = item->GetProto();
		for (int i = 0; i < ITEM_LIMIT_MAX_NUM; ++i)
		{
			const long limit = proto->aLimits[i].lValue;
			switch (proto->aLimits[i].bType)
			{
				case LIMIT_LEVEL:	if (ch->GetLevel() < limit) return false; break;
#ifdef ENABLE_CONQUEROR_LEVEL
				case LIMIT_CONQUEROR_LEVEL:	if (ch->GetConquerorLevel() < limit) return false; break;
#endif
				case LIMIT_STR:		if (ch->GetPoint(POINT_ST) < limit) return false; break;
				case LIMIT_INT:		if (ch->GetPoint(POINT_IQ) < limit) return false; break;
				case LIMIT_DEX:		if (ch->GetPoint(POINT_DX) < limit) return false; break;
				case LIMIT_CON:		if (ch->GetPoint(POINT_HT) < limit) return false; break;
			}
		}
		return true;
	}
}

// ---- the store (CHARACTER methods, char.h) ----

LPITEM CHARACTER::Mt2009AddeqGetItem(BYTE bWear) const
{
	if (!m_PlayerSlots || bWear >= WEAR_MAX_NUM)
		return NULL;
	return m_PlayerSlots->pAddeqItems[bWear];
}

// CHARACTER::SetItem of a store cell (INVENTORY, MT2009_ADDEQ_SLOT_START..END): no packet - the client never sees it
void CHARACTER::Mt2009AddeqSetItem(WORD wCell, LPITEM pItem)
{
	if (!m_PlayerSlots || !Mt2009AddeqIsCell(wCell))
		return;

	LPITEM& slot = m_PlayerSlots->pAddeqItems[wCell - MT2009_ADDEQ_SLOT_START];
	if (pItem && slot && slot != pItem)
		sys_err("ADDEQ: %s cell %u taken by %s (%u), %s (%u) put over it", GetName(), wCell, slot->GetName(), slot->GetID(),
			pItem->GetName(), pItem->GetID());
	slot = pItem;

	if (pItem)
	{
		pItem->SetCell(this, wCell);
		pItem->SetWindow(INVENTORY);
#ifdef ENABLE_ITEM_SAFE_FLUSH
		m_PlayerSlots->setTouchedItems.emplace(pItem->GetID());
#endif
	}
}

void CHARACTER::Mt2009AddeqFlushItems()
{
	if (!m_PlayerSlots)
		return;
	for (LPITEM item : m_PlayerSlots->pAddeqItems)
		if (item)
			ITEM_MANAGER::instance().FlushDelayedSave(item);
}

// ClearItem: as the bag's items
void CHARACTER::Mt2009AddeqClearItems()
{
	if (!m_PlayerSlots)
		return;
	for (size_t i = 0; i < m_PlayerSlots->pAddeqItems.size(); ++i)
	{
		LPITEM item = m_PlayerSlots->pAddeqItems[i];
		if (!item)
			continue;
		item->SetSkipSave(true);
		ITEM_MANAGER::instance().FlushDelayedSave(item);
		item->RemoveFromCharacter();
		M2_DESTROY_ITEM(item);
		m_PlayerSlots->pAddeqItems[i] = NULL;
	}
	s_mapAddeqLastSwitch.erase(GetPlayerID());
}

// the switch: the paged slots' worn items into the store, the store's onto them
bool CHARACTER::Mt2009AddeqSwitch(int iPage)
{
	if (!IsPC() || !GetDesc() || GetDesc()->IsBot() || !m_PlayerSlots)
		return false;

	if (!AddeqIsUnlocked(this))
	{
		ChatPacket(CHAT_TYPE_INFO, "Najpierw odblokuj drug\xb9 stron\xea ekwipunku (przedmiot \"Strona ekwipunku II\").");
		return false;
	}

	iPage = iPage ? 1 : 0;
	if (iPage == AddeqPage(this))
	{
		AddeqSendState(this);
		return true;
	}

	if (IsDead() || IsStun() || IsPolymorphed() || m_pkFishingEvent || m_pkPreFishingEvent || m_pkMiningEvent)
	{
		ChatPacket(CHAT_TYPE_INFO, "Nie mo\xbf""esz teraz zmieni\xe6 strony ekwipunku.");
		return false;
	}

	if (GetExchange() || GetMyShop() || GetShopOwner() || IsOpenSafebox() || IsCubeOpen() || !CanHandleItem())
	{
		ChatPacket(CHAT_TYPE_INFO, "Zamknij inne okna, aby zmieni\xe6 stron\xea ekwipunku.");
		return false;
	}

	const DWORD dwNow = get_dword_time();
	if (dwNow - GetLastAttackTime() <= ADDEQ_STILL_MS || dwNow - m_dwLastSkillTime <= ADDEQ_STILL_MS)
	{
		ChatPacket(CHAT_TYPE_INFO, "Musisz sta\xe6 spokojnie, aby zmieni\xe6 stron\xea ekwipunku.");
		return false;
	}

	const auto itLast = s_mapAddeqLastSwitch.find(GetPlayerID());
	if (itLast != s_mapAddeqLastSwitch.end() && dwNow - itLast->second < ADDEQ_SWITCH_MS)
	{
		ChatPacket(CHAT_TYPE_INFO, "Stron\xea ekwipunku mo\xbfna zmienia\xe6 raz na 5 sekund.");
		return false;
	}

	// everything checked first: nothing moves unless all of it can
	for (BYTE bWear : ADDEQ_WEARS)
	{
		LPITEM worn = GetWear(bWear);
		if (worn && (IS_SET(worn->GetFlag(), ITEM_FLAG_IRREMOVABLE) || worn->isLocked() || worn->IsExchanging()))
		{
			ChatPacket(CHAT_TYPE_INFO, "Przedmiotu %s nie mo\xbfna teraz zdj\xb9\xe6 - strona ekwipunku bez zmian.", worn->GetName());
			return false;
		}
		LPITEM stored = Mt2009AddeqGetItem(bWear);
		if (stored && !AddeqFits(this, stored))
		{
			ChatPacket(CHAT_TYPE_INFO, "Nie mo\xbf""esz za\xb3o\xbfy\xe6 przedmiotu %s z drugiej strony ekwipunku - strona bez zmian.",
				stored->GetName());
			return false;
		}
	}

	int iMoved = 0;
	for (BYTE bWear : ADDEQ_WEARS)
	{
		LPITEM worn = GetWear(bWear);
		LPITEM stored = Mt2009AddeqGetItem(bWear);
		if (!worn && !stored)
			continue;

		if (worn)
			worn->RemoveFromCharacter();	// Unequip: its points, look, events off

		if (stored && !stored->EquipTo(this, bWear))	// out of the store (RemoveFromCharacter), on, its points
		{
			sys_err("ADDEQ: %s could not put on %s (%u) at %u", GetName(), stored->GetName(), stored->GetID(), bWear);
			if (worn)
				worn->EquipTo(this, bWear);
			continue;
		}

		if (worn)
			worn->AddToCharacter(this, TItemPos(INVENTORY, MT2009_ADDEQ_SLOT_START + bWear));

		if (bWear == WEAR_WEAPON)
			OnWeaponChange(stored, worn);
		++iMoved;
	}

#ifdef ENABLE_WEAPON_COSTUME_SYSTEM
	// a weapon costume must match the weapon's kind (EquipItem's rule)
	if (LPITEM costumeWeapon = GetWear(WEAR_COSTUME_WEAPON))
	{
		LPITEM weapon = GetWear(WEAR_WEAPON);
		if (!weapon || weapon->GetType() != ITEM_WEAPON || costumeWeapon->GetValue(3) != weapon->GetSubType())
		{
			if (UnequipItem(costumeWeapon))
				ChatPacket(CHAT_TYPE_INFO, "Kostium broni nie pasuje do broni tej strony - zdj\xeaty do ekwipunku.");
			else
				ChatPacket(CHAT_TYPE_INFO, "Kostium broni nie pasuje do broni tej strony, a w ekwipunku brak miejsca, aby go zdj\xb9\xe6.");
		}
	}
#endif

	SetQuestFlag(ADDEQ_FLAG_PAGE, iPage);
	s_mapAddeqLastSwitch[GetPlayerID()] = dwNow;

	CheckMaximumPoints();
	ComputeBattlePoints();
	UpdatePacket();

	sys_log(0, "ADDEQ: %s (%u) page %d, %d slot(s) swapped", GetName(), GetPlayerID(), iPage + 1, iMoved);
	ChatPacket(CHAT_TYPE_INFO, "Strona ekwipunku: %s.", iPage ? "II" : "I");
	AddeqSendState(this);
	return true;
}

// ---- the engine's hooks (server-patches/addeq) ----

// CHARACTER::UseItemEx: the unlock items; -1 not one of them
int Mt2009AddeqUseItem(LPCHARACTER ch, LPITEM item)
{
	if (!ch || !item || (item->GetVnum() != ADDEQ_ITEM_BOUND && item->GetVnum() != ADDEQ_ITEM_TRADE))
		return -1;

	if (!ch->IsPC() || !ch->GetDesc() || ch->GetDesc()->IsBot())
		return 0;

	if (ch->GetExchange() || ch->GetMyShop() || ch->GetShopOwner() || ch->IsOpenSafebox() || ch->IsCubeOpen())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Zamknij inne okna, aby u\xbfy\xe6 tego przedmiotu.");
		return 0;
	}

	if (ch->GetQuestFlag(ADDEQ_FLAG_UNLOCKED) != 0)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Masz ju\xbf odblokowan\xb9 drug\xb9 stron\xea ekwipunku.");
		AddeqSyncSkill(ch);
		return 0;
	}

	ch->SetQuestFlag(ADDEQ_FLAG_UNLOCKED, 1);
	ch->SetQuestFlag(ADDEQ_FLAG_PAGE, 0);
	AddeqSyncSkill(ch);
	sys_log(0, "ADDEQ: %s (%u) unlocked the second page with %u (%u)", ch->GetName(), ch->GetPlayerID(), item->GetVnum(), item->GetID());
	item->SetCount(item->GetCount() - 1);

	ch->ChatPacket(CHAT_TYPE_INFO, "Odblokowano drug\xb9 stron\xea ekwipunku. Prze\xb3\xb9""czasz j\xb9 zak\xb3""adkami I / II w oknie ekwipunku "
		"albo umiej\xeatno\x9c""ci\xb9 \"Zmiana strony ekwipunku\" (umiej\xeatno\x9c""ci pomocnicze).");
	AddeqSendState(ch);
	return 1;
}

// CHARACTER::UseSkill, before anything: the skill 200 switches the page (true: it was this skill, bResult the answer)
bool Mt2009AddeqUseSkill(LPCHARACTER ch, DWORD dwVnum, bool& bResult)
{
	if (dwVnum != ADDEQ_SKILL_VNUM)
		return false;

	bResult = false;
	if (!ch || !ch->IsPC() || ch->GetSkillLevel(ADDEQ_SKILL_VNUM) == 0)
		return true;

	bResult = ch->Mt2009AddeqSwitch(AddeqPage(ch) ? 0 : 1);
	return true;
}

ACMD(do_addeq)
{
	char arg1[256];
	one_argument(argument, arg1, sizeof(arg1));

	if (!ch || !ch->GetDesc() || ch->GetDesc()->IsBot())
		return;

	const std::string sub = arg1;
	if (sub == "hello")
	{
		AddeqSyncSkill(ch);
		AddeqSendState(ch);
		return;
	}
	if (sub == "toggle")
	{
		ch->Mt2009AddeqSwitch(AddeqPage(ch) ? 0 : 1);
		return;
	}
	if (sub == "0" || sub == "1")
	{
		ch->Mt2009AddeqSwitch(sub == "1" ? 1 : 0);
		return;
	}
}
