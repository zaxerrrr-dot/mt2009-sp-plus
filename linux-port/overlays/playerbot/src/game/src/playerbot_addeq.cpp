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
// Here instead: the inactive pages lie in a hidden store of the character after the belt's inventory
// (MT2009_ADDEQ_SLOT_START = BELT_INVENTORY_SLOT_END, one cell per wear cell), saved as window INVENTORY (the DB's
// window enum and every packet unchanged) - and a switch swaps the worn items of the paged slots with the store's: the
// engine's own Unequip / EquipTo, so the bonuses, looks, set bonuses, timers and refine events are what a hand change
// does, and only the worn page counts. The store is never sent to the client and no client packet reaches it (TItemPos
// validity, GetItem and every handler stay at INVENTORY_AND_EQUIP_SLOT_MAX): an old client sees the worn page only.
//
// MT2009_PLUS_ADDEQ_V2 - four pages (the owner, 29 October 2026: "Yes, add them; each next page is unlocked with the
// same scroll from the ItemShop."): the store is four blocks of WEAR_MAX_NUM cells, a home block per page -
//   II  308-339 (V1's one block: a V1 character on page I is already in this layout)
//   III 340-371
//   IV  372-403
//   I   404-435
// The worn page's own block is always empty: a switch from page A to page B puts B's block on, A's worn items into A's
// block. Something found in the worn page's block (AddeqRepair - at the hello and before every switch) is a V1
// character worn on page II, whose page I still lies in block II: it moves to page I's block (apply.sh moves the same
// rows once at the update, MT2009_PLUS_ADDEQ_V2 - this is the fallback); anything else there (a broken switch) goes into
// the bag - never lost.
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
// State: quest flags addeq.unlocked - the number of extra pages unlocked, 0..3 (V1's 1 = page II, the same meaning) - and
// addeq.page (0 = I .. 3 = IV); the skill 200 at level 1 shows the switch in the support skills (restored at the hello
// if a skill reset cleared it). Each use of 38306 / 76055 unlocks the next page (II, III, IV); a fourth is refused.
// Commands (root/uiaddeq.py):
//   /addeq hello        the client's hello after every load: "addeq_page <unlocked 0..3> <page 0..3>" back
//   /addeq <0..3>       the page tabs I-IV of the equipment window (only unlocked pages)
//   /addeq toggle       the next unlocked page (as the skill 200: I -> II -> ... -> I)
// Bots never: they have neither the item nor the hello (Mt2009AddeqSwitch / Mt2009AddeqUseItem refuse a bot; the
// ItemShop V3 goals never buy 76055), their second set (playerbot_element_second_set.h) swaps through the bag.
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

	// MT2009_PLUS_ADDEQ_V2: four pages, three of them extra
	const int ADDEQ_PAGES = 4;
	const int ADDEQ_EXTRA_MAX = ADDEQ_PAGES - 1;
	const char* const ADDEQ_PAGE_NAME[ADDEQ_PAGES] = { "I", "II", "III", "IV" };
	static_assert(MT2009_ADDEQ_STORE_BLOCKS == ADDEQ_PAGES, "a store block per page");

	const BYTE ADDEQ_WEARS[] = { WEAR_BODY, WEAR_HEAD, WEAR_FOOTS, WEAR_WRIST, WEAR_WEAPON, WEAR_NECK, WEAR_EAR, WEAR_ARROW,
		WEAR_SHIELD, WEAR_PENDANT, WEAR_GLOVE };

	std::unordered_map<DWORD, DWORD> s_mapAddeqLastSwitch;

	// the extra pages unlocked, 0..3 (V1's flag 1 = one; a character with the skill and no flag has one)
	int AddeqUnlocked(LPCHARACTER ch)
	{
		int n = ch->GetQuestFlag(ADDEQ_FLAG_UNLOCKED);
		if (n < 0)
			n = 0;
		if (n > ADDEQ_EXTRA_MAX)
			n = ADDEQ_EXTRA_MAX;
		if (n == 0 && ch->GetSkillLevel(ADDEQ_SKILL_VNUM) > 0)
			n = 1;
		return n;
	}

	bool AddeqIsUnlocked(LPCHARACTER ch)
	{
		return AddeqUnlocked(ch) > 0;
	}

	int AddeqPage(LPCHARACTER ch)
	{
		const int iPage = ch->GetQuestFlag(ADDEQ_FLAG_PAGE);
		return iPage >= 0 && iPage < ADDEQ_PAGES ? iPage : 0;
	}

	// a page's home block in the store: II 308.., III 340.., IV 372.., I 404..
	WORD AddeqCell(int iPage, BYTE bWear)
	{
		return MT2009_ADDEQ_SLOT_START + WEAR_MAX_NUM * ((iPage + ADDEQ_PAGES - 1) % ADDEQ_PAGES) + bWear;
	}

	void AddeqSendState(LPCHARACTER ch)
	{
		ch->ChatPacket(CHAT_TYPE_COMMAND, "addeq_page %d %d", AddeqUnlocked(ch), AddeqPage(ch));
	}

	// the skill 200 at level 1 while a page is unlocked (a skill reset clears it)
	void AddeqSyncSkill(LPCHARACTER ch)
	{
		if (ch->GetQuestFlag(ADDEQ_FLAG_UNLOCKED) != 0 && ch->GetSkillLevel(ADDEQ_SKILL_VNUM) == 0)
		{
			ch->SetSkillLevel(ADDEQ_SKILL_VNUM, 1);
			ch->SkillLevelPacket();
		}
	}

	// The worn page's own block must be empty. An item there: a V1 character worn on page II (bLegacy: its page I's
	// piece, to page I's block when that cell is free) or a switch that broke halfway - to the bag. False: something is
	// still there (a full bag).
	bool AddeqRepair(LPCHARACTER ch, int iWorn, bool bLegacy)
	{
		bool bClean = true;
		for (BYTE bWear = 0; bWear < WEAR_MAX_NUM; ++bWear)
		{
			LPITEM item = ch->Mt2009AddeqGetCellItem(AddeqCell(iWorn, bWear));
			if (!item)
				continue;

			if (bLegacy && iWorn == 1 && !ch->Mt2009AddeqGetCellItem(AddeqCell(0, bWear)))
			{
				item->RemoveFromCharacter();
				item->AddToCharacter(ch, TItemPos(INVENTORY, AddeqCell(0, bWear)));
				sys_log(0, "ADDEQ: %s (%u) %s (%u) from page II's block to page I's (V1 layout)", ch->GetName(),
					ch->GetPlayerID(), item->GetName(), item->GetID());
				continue;
			}

			const int iBag = ch->GetEmptyInventory(item->GetSize());
			if (iBag < 0)
			{
				bClean = false;
				continue;
			}
			item->RemoveFromCharacter();
			item->AddToCharacter(ch, TItemPos(INVENTORY, iBag));
			sys_log(0, "ADDEQ: %s (%u) %s (%u) from the worn page's block (page %d) to the bag cell %d", ch->GetName(),
				ch->GetPlayerID(), item->GetName(), item->GetID(), iWorn + 1, iBag);
		}
		return bClean;
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

// V1's accessor: page II's block (the only block of V1)
LPITEM CHARACTER::Mt2009AddeqGetItem(BYTE bWear) const
{
	if (!m_PlayerSlots || bWear >= WEAR_MAX_NUM)
		return NULL;
	return m_PlayerSlots->pAddeqItems[bWear];
}

// MT2009_PLUS_ADDEQ_V2: any store cell (MT2009_ADDEQ_SLOT_START..END)
LPITEM CHARACTER::Mt2009AddeqGetCellItem(WORD wCell) const
{
	if (!m_PlayerSlots || !Mt2009AddeqIsCell(wCell))
		return NULL;
	return m_PlayerSlots->pAddeqItems[wCell - MT2009_ADDEQ_SLOT_START];
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

// the switch to page iPage (0..3): the paged slots' worn items into the worn page's block, the target page's block onto them
bool CHARACTER::Mt2009AddeqSwitch(int iPage)
{
	if (!IsPC() || !GetDesc() || GetDesc()->IsBot() || !m_PlayerSlots)
		return false;

	const int iUnlocked = AddeqUnlocked(this);
	if (iUnlocked == 0)
	{
		ChatPacket(CHAT_TYPE_INFO, "Najpierw odblokuj dodatkow\xb9 stron\xea ekwipunku (przedmiot \"Strona ekwipunku II\").");
		return false;
	}

	if (iPage < 0 || iPage >= ADDEQ_PAGES)
		return false;

	if (iPage > iUnlocked)
	{
		ChatPacket(CHAT_TYPE_INFO, "Strona ekwipunku %s jest jeszcze zablokowana - odblokowuje j\xb9 kolejny przedmiot \"Strona ekwipunku II\".",
			ADDEQ_PAGE_NAME[iPage]);
		AddeqSendState(this);
		return false;
	}

	const int iWorn = AddeqPage(this);
	if (iPage == iWorn)
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

	// the worn page's block must be empty: the worn items go there
	if (!AddeqRepair(this, iWorn, true))
	{
		ChatPacket(CHAT_TYPE_INFO, "Zr\xf3""b miejsce w ekwipunku - przedmiot z magazynu stron ekwipunku czeka na wolne pole.");
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
		LPITEM stored = Mt2009AddeqGetCellItem(AddeqCell(iPage, bWear));
		if (stored && !AddeqFits(this, stored))
		{
			ChatPacket(CHAT_TYPE_INFO, "Nie mo\xbf""esz za\xb3o\xbfy\xe6 przedmiotu %s ze strony ekwipunku %s - strona bez zmian.",
				stored->GetName(), ADDEQ_PAGE_NAME[iPage]);
			return false;
		}
	}

	int iMoved = 0;
	bool bBroken = false;
	for (BYTE bWear : ADDEQ_WEARS)
	{
		LPITEM worn = GetWear(bWear);
		LPITEM stored = Mt2009AddeqGetCellItem(AddeqCell(iPage, bWear));
		if (!worn && !stored)
			continue;

		if (worn)
			worn->RemoveFromCharacter();	// Unequip: its points, look, events off

		if (stored && !stored->EquipTo(this, bWear))	// out of the store (RemoveFromCharacter), on, its points
		{
			sys_err("ADDEQ: %s could not put on %s (%u) at %u", GetName(), stored->GetName(), stored->GetID(), bWear);
			if (worn)
				worn->EquipTo(this, bWear);
			bBroken = true;	// the target page's piece stays in its block - to the bag below
			continue;
		}

		if (worn)
			worn->AddToCharacter(this, TItemPos(INVENTORY, AddeqCell(iWorn, bWear)));

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
	if (bBroken)
		AddeqRepair(this, iPage, false);	// the new worn page's block empty again (what did not go on: the bag)

	CheckMaximumPoints();
	ComputeBattlePoints();
	UpdatePacket();

	sys_log(0, "ADDEQ: %s (%u) page %d -> %d, %d slot(s) swapped", GetName(), GetPlayerID(), iWorn + 1, iPage + 1, iMoved);
	ChatPacket(CHAT_TYPE_INFO, "Strona ekwipunku: %s.", ADDEQ_PAGE_NAME[iPage]);
	AddeqSendState(this);
	return true;
}

// ---- the engine's hooks (server-patches/addeq) ----

// CHARACTER::UseItemEx: the unlock items - each use the next page (II, III, IV); -1 not one of them
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

	const int iUnlocked = AddeqUnlocked(ch);
	if (iUnlocked >= ADDEQ_EXTRA_MAX)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Masz ju\xbf odblokowane wszystkie 4 strony ekwipunku.");
		AddeqSyncSkill(ch);
		return 0;
	}

	ch->SetQuestFlag(ADDEQ_FLAG_UNLOCKED, iUnlocked + 1);
	if (iUnlocked == 0)
		ch->SetQuestFlag(ADDEQ_FLAG_PAGE, 0);
	AddeqSyncSkill(ch);
	sys_log(0, "ADDEQ: %s (%u) unlocked page %d with %u (%u)", ch->GetName(), ch->GetPlayerID(), iUnlocked + 2, item->GetVnum(),
		item->GetID());
	item->SetCount(item->GetCount() - 1);

	ch->ChatPacket(CHAT_TYPE_INFO, "Odblokowano stron\xea ekwipunku %s (stron: %d/4). Prze\xb3\xb9""czasz je zak\xb3""adkami w oknie "
		"ekwipunku albo umiej\xeatno\x9c""ci\xb9 \"Zmiana strony ekwipunku\" (umiej\xeatno\x9c""ci pomocnicze).",
		ADDEQ_PAGE_NAME[iUnlocked + 1], iUnlocked + 2);
	AddeqSendState(ch);
	return 1;
}

// CHARACTER::UseSkill, before anything: the skill 200 switches to the next unlocked page (true: it was this skill,
// bResult the answer)
bool Mt2009AddeqUseSkill(LPCHARACTER ch, DWORD dwVnum, bool& bResult)
{
	if (dwVnum != ADDEQ_SKILL_VNUM)
		return false;

	bResult = false;
	if (!ch || !ch->IsPC() || ch->GetSkillLevel(ADDEQ_SKILL_VNUM) == 0)
		return true;

	bResult = ch->Mt2009AddeqSwitch((AddeqPage(ch) + 1) % (AddeqUnlocked(ch) + 1));
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
		if (AddeqIsUnlocked(ch))
			AddeqRepair(ch, AddeqPage(ch), true);	// a V1 character worn on page II (README.md)
		AddeqSendState(ch);
		return;
	}
	if (sub == "toggle")
	{
		ch->Mt2009AddeqSwitch((AddeqPage(ch) + 1) % (AddeqUnlocked(ch) + 1));
		return;
	}
	if (sub.size() == 1 && sub[0] >= '0' && sub[0] < '0' + ADDEQ_PAGES)
	{
		ch->Mt2009AddeqSwitch(sub[0] - '0');
		return;
	}
}
