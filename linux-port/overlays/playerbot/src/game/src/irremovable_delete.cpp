// MT2009_PLUS_IRREMOVABLE_DELETE_V1 - a worn item that cannot be taken off (ITEM_FLAG_IRREMOVABLE: the timed unique
// items - Talizman Pracowitosci 70004, Diabelski Kolec 70042, Pierscien Doswiadczenia 72303...) asks whether to
// destroy it when its owner tries to take it off (the owner's list of 3 November 2026; server-patches/irrem,
// README.md). Until now the take-off was refused without a word and the item sat on its slot until its time ran out.
//
// Ported from the other MT2009 PLUS tree (patch-02-11, commit a7dbe0c3 of 2 November 2026: char_item.cpp
// Mt2009AskRemoveIrremovable + cmd_general.cpp do_usun_zalozony + root/game.py "usun_zalozony_pytaj"), with what that
// one lacks: its question went out from every refused take-off of the engine (quest pc.unequip, the mount's
// UnEquipSpecialRideUniqueItem, the costume commands...) and its yes was only "<cell> <vnum>" - any irremovable item
// that came onto that slot later was destroyed by a stale yes. Here:
//   - the question only for the player's own packet: CInputMain::ItemUse (right click / use of the worn item) and
//     CInputMain::ItemMove (dragging it out, or another item onto its slot) open a scope for their character; a
//     refusal of CanUnequipNow (its ITEM_FLAG_IRREMOVABLE branch) or MoveItem's early ITEM_FLAG_IRREMOVABLE test
//     inside that scope asks, once per packet. Playerbots (bot descriptors) are never asked.
//   - the yes carries a random token bound to the item's id, the player, the connection and 60 s:
//       server -> client  "IRREM ask <token> <vnum>"        root uiirremovable.py: the question window
//       client -> server  "/irrem usun <token>"             destroy it
//                         "/irrem anuluj"                   the window closed with "Nie"
//   - the yes is checked again: the item is still that id, owned by him, worn, ITEM_FLAG_IRREMOVABLE, not locked
//     (switchbot) nor in an exchange; the player alive, no exchange / shop / safebox / crafting window open, free
//     to handle items (CanHandleItem). The destruction goes through ITEM_MANAGER::RemoveItem with the reason
//     "IRREMOVABLE_DELETE" (the item log's row, the item's name and count as its hint) - the same way a timed
//     unique item leaves when its time runs out (Unequip, then destroyed).
// Removable items never get here: both hooks test ITEM_FLAG_IRREMOVABLE first (Rekawica Zlodzieja 72005/70043 and
// Pierscien Doswiadczenia 39002/72003/70005 are removable since MT2009_PLUS_DROP307_V1 and come off as before).
#include "stdafx.h"
#include "constants.h"
#include "config.h"
#include "char.h"
#include "desc.h"
#include "item.h"
#include "item_manager.h"
#include "log.h"
#include "utils.h"

#include <cstring>
#include <map>

namespace irrem
{
	enum
	{
		TOKEN_TTL_MS = 60 * 1000,	// the question window's answer, at most a minute later
		ASK_REPEAT_MS = 1000,		// the same item asked again no sooner (a held right click, a drag after a drag)
	};

	struct TAsk
	{
		DWORD	token;
		DWORD	itemId;
		DWORD	vnum;
		DWORD	handle;		// the connection that was asked: a relog never answers an old question
		DWORD	time;		// get_dword_time() of the question
		TAsk() : token(0), itemId(0), vnum(0), handle(0), time(0) {}
	};

	static std::map<DWORD, TAsk> s_mapAsk;	// pid -> the open question (one at a time; a new one replaces it)
	static LPCHARACTER s_pScope = NULL;	// the character whose own packet is being handled (Mt2009IrremScope)

	static bool IsPerson(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && ch->GetDesc() && !ch->GetDesc()->IsBot();
	}
}

// server-patches/irrem (input_main.cpp, ItemUse / ItemMove): ch before the player's packet is handled, NULL after it
void Mt2009IrremScope(LPCHARACTER ch)
{
	irrem::s_pScope = ch;
}

// server-patches/irrem (char_item.cpp, CanUnequipNow's ITEM_FLAG_IRREMOVABLE branch and MoveItem's early test): the
// take-off of item is refused - inside the player's own packet, ask whether to destroy it. The refusal stands.
void Mt2009IrremAsk(LPCHARACTER ch, LPITEM item)
{
	using namespace irrem;
	if (!ch || ch != s_pScope || !item)
		return;
	if (!IsPerson(ch) || item->GetOwner() != ch || !item->IsEquipped() || !IS_SET(item->GetFlag(), ITEM_FLAG_IRREMOVABLE))
		return;
	s_pScope = NULL;	// once per packet (UnequipItem may test the costume weapon, then the item)

	const DWORD now = get_dword_time();
	TAsk& ask = s_mapAsk[ch->GetPlayerID()];
	if (ask.itemId == item->GetID() && ask.handle == ch->GetDesc()->GetHandle() && now - ask.time < (DWORD)ASK_REPEAT_MS)
		return;

	ask.token = (DWORD)number(1, 999999999);
	ask.itemId = item->GetID();
	ask.vnum = item->GetVnum();
	ask.handle = ch->GetDesc()->GetHandle();
	ask.time = now;
	ch->ChatPacket(CHAT_TYPE_COMMAND, "IRREM ask %u %u", ask.token, ask.vnum);
}

// "/irrem usun <token>" | "/irrem anuluj" (cmd.cpp, server-patches/irrem)
void Mt2009IrremCommand(LPCHARACTER ch, const char* argument)
{
	using namespace irrem;
	if (!IsPerson(ch))
		return;

	char sub[32] = { 0 }, tok[32] = { 0 };
	two_arguments(argument, sub, sizeof(sub), tok, sizeof(tok));

	std::map<DWORD, TAsk>::iterator it = s_mapAsk.find(ch->GetPlayerID());
	if (it == s_mapAsk.end())
		return;
	if (!strcmp(sub, "anuluj"))
	{
		s_mapAsk.erase(it);
		return;
	}
	if (strcmp(sub, "usun"))
		return;

	DWORD token = 0;
	if (!*tok || !str_to_number(token, tok) || !token)
		return;

	const TAsk ask = it->second;
	if (ask.token != token)
		return;
	s_mapAsk.erase(it);	// one yes per question, whatever follows

	if (ask.handle != ch->GetDesc()->GetHandle() || get_dword_time() - ask.time > (DWORD)TOKEN_TTL_MS)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Pytanie wygas\xb3o - spr\xf3""buj zdj\xb9\xe6 przedmiot jeszcze raz.");
		return;
	}

	LPITEM item = ITEM_MANAGER::instance().Find(ask.itemId);
	if (!item || item->GetOwner() != ch || item->GetVnum() != ask.vnum || !item->IsEquipped() ||
		!IS_SET(item->GetFlag(), ITEM_FLAG_IRREMOVABLE))
		return;

	if (ch->IsDead() || ch->GetExchange() || ch->GetShop() || ch->GetMyShop() || ch->IsOpenSafebox() || ch->IsCubeOpen() ||
		!ch->CanHandleItem() || item->isLocked() || item->IsExchanging())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Nie mo\xbfna teraz zniszczy\xe6 tego przedmiotu - zamknij inne okna i spr\xf3""buj ponownie.");
		return;
	}

	char szName[128];
	strlcpy(szName, item->GetName(), sizeof(szName));
	sys_log(0, "IRREMOVABLE_DELETE: %s pid=%u item id=%u vnum=%u cell=%d", ch->GetName(), ch->GetPlayerID(), item->GetID(),
		item->GetVnum(), (int)item->GetCell());
	ITEM_MANAGER::instance().RemoveItem(item, "IRREMOVABLE_DELETE");	// the item log's row (LogManager::ItemLog)
	ch->ChatPacket(CHAT_TYPE_INFO, "Zniszczono: %s.", szName);
}
