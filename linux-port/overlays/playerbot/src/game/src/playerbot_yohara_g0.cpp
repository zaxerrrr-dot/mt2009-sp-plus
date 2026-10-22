// MT2009_PLUS_BOT_YOHARA_G0_V1 / MT2009_PLUS_ITEM_ACCOUNT_BOUND_V1 - the account-bound items of the bots' G0 package
// (playerbot_yohara_g0.h, plan cache/yohara/plan-boty-yohara.md 6.1/6.4 and the owner's decisions of 22 October:
// "Sprzet z pakietu jest przypisany do konta: bot moze go ulepszac, ale nie moze wyrzucic, przekazac w handlu ani
// sprzedac graczom - moze sprzedac tylko innym botom").
//
// The binding is the engine's (server-patches/g0bind): CItem::IsAccountBound adds DROP / GIVE / MYSHOP / PKDROP to the
// item's GetAntiFlag (MT2009_PLUS_BOT_YOHARA_G0_V2: not SELL - the NPC merchant may buy an unneeded piece, the owner,
// 22 October), so the drop, the trade window, both shops and the death's drop refuse it,
// and a refine (CopyAttributeTo) makes the new item bound too (Mt2009AccountBoundCarry below). The store is this file's:
// player.item_account_bound, a row an item id (its owner's pid for the logs and a move between bots) - read back when
// such an item is loaded (Mt2009AccountBoundLoad, ITEM_MANAGER::CreateItem's end through Mt2009GloveLoad), only for the
// Yohara gear's families (the gloves, the jade jewellery, the Will talismans), the only items bound so far.
#include "stdafx.h"
#include "playerbot_yohara_gear.h"
#include "constants.h"
#include "utils.h"
#include "char.h"
#include "item.h"
#include "db.h"

#include <unordered_set>

namespace
{
	bool s_bMt2009AccountBoundTable = false;
	// The ids bound on this core (and read back here) - the binding itself when the engine patch is not in.
	std::unordered_set<DWORD> s_setMt2009AccountBound;

	void EnsureMt2009AccountBoundTable()
	{
		if (s_bMt2009AccountBoundTable)
			return;
		s_bMt2009AccountBoundTable = true;
		std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery(
				"CREATE TABLE IF NOT EXISTS item_account_bound ("
				"id INT UNSIGNED NOT NULL PRIMARY KEY, pid INT UNSIGNED NOT NULL DEFAULT 0, vnum INT UNSIGNED NOT NULL DEFAULT 0, "
				"why VARCHAR(24) NOT NULL DEFAULT '', bound_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, KEY pid (pid)) "
				"ENGINE=InnoDB DEFAULT CHARSET=latin1"));
	}

	void SetMt2009AccountBoundFlag(LPITEM item, bool b)
	{
#ifdef MT2009_PLUS_ITEM_ACCOUNT_BOUND_V1
		item->SetAccountBound(b);
#endif
		if (b)
			s_setMt2009AccountBound.insert(item->GetID());
		else
			s_setMt2009AccountBound.erase(item->GetID());
	}
}

// The families a bound item may be of (the G0 package's): a row is looked for only when one of these is loaded.
bool Mt2009AccountBoundFamily(DWORD dwVnum)
{
	const DWORD dwBase = dwVnum - dwVnum % 10;
	return (dwVnum >= 23000 && dwVnum <= 23039) ||	// Rekawice Sung Ma
			(dwVnum >= 14580 && dwVnum <= 14619) || (dwVnum >= 16580 && dwVnum <= 16619) ||
			(dwVnum >= 17570 && dwVnum <= 17609) ||	// Obrecze, Kolie, Klipsy Jadeitu
			dwBase == 81000 || dwBase == 81250 || dwBase == 81300 || dwBase == 81550;	// Talizmany Woli
}

bool Mt2009AccountBound(LPITEM item)
{
	if (!item)
		return false;
#ifdef MT2009_PLUS_ITEM_ACCOUNT_BOUND_V1
	return item->IsAccountBound();
#else
	return item->GetID() && s_setMt2009AccountBound.count(item->GetID()) != 0;
#endif
}

// A new bound item (the package): the flag and its row.
bool Mt2009AccountBoundMark(LPITEM item, DWORD dwPID, const char* szWhy)
{
	if (!item || !item->GetID())
		return false;
	EnsureMt2009AccountBoundTable();
	SetMt2009AccountBoundFlag(item, true);
	char szEscaped[64];
	DBManager::instance().EscapeString(szEscaped, sizeof(szEscaped), szWhy ? szWhy : "", strlen(szWhy ? szWhy : ""));
	DBManager::instance().DirectQuery("REPLACE INTO item_account_bound (id, pid, vnum, why) VALUES (%u, %u, %u, '%s')",
			item->GetID(), dwPID, item->GetVnum(), szEscaped);
	return true;
}

// A bound item gone to another bot (the bot-to-bot sale): the row's owner.
void Mt2009AccountBoundOwner(LPITEM item, DWORD dwPID)
{
	if (!item || !item->GetID() || !Mt2009AccountBound(item))
		return;
	EnsureMt2009AccountBoundTable();
	DBManager::instance().DirectQuery("UPDATE item_account_bound SET pid = %u WHERE id = %u", dwPID, item->GetID());
}

// ITEM_MANAGER::CreateItem's end (Mt2009GloveLoad): a loaded item of the families is bound if its row is there.
void Mt2009AccountBoundLoad(LPITEM item, bool bIsNewItem)
{
	if (!item || bIsNewItem || !item->GetID() || !Mt2009AccountBoundFamily(item->GetVnum()))
		return;
	EnsureMt2009AccountBoundTable();
	std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery("SELECT pid FROM item_account_bound WHERE id = %u", item->GetID()));
	SQLResult* pRes = pMsg ? pMsg->Get() : NULL;
	if (pRes && pRes->uiNumRows > 0)
		SetMt2009AccountBoundFlag(item, true);
}

// CItem::CopyAttributeTo (server-patches/g0bind): a refine's new item is bound (the engine set its flag) - the row
// follows it to the new id. The old item goes on to be destroyed (or, a failed refine of a scroll, stays the lower one).
void Mt2009AccountBoundCarry(LPITEM pOld, LPITEM pNew)
{
	if (!pOld || !pNew || !pNew->GetID() || pOld == pNew)
		return;
	EnsureMt2009AccountBoundTable();
	SetMt2009AccountBoundFlag(pNew, true);
	const DWORD dwPID = pOld->GetOwner() ? pOld->GetOwner()->GetPlayerID() : 0;
	DBManager::instance().DirectQuery("REPLACE INTO item_account_bound (id, pid, vnum, why) VALUES (%u, %u, %u, 'refine')",
			pNew->GetID(), dwPID, pNew->GetVnum());
	DBManager::instance().DirectQuery("DELETE FROM item_account_bound WHERE id = %u", pOld->GetID());
	s_setMt2009AccountBound.erase(pOld->GetID());
	sys_log(0, "PLAYERBOT_G0: bound carried pid=%u from=%u (vnum %u) to=%u (vnum %u)", dwPID, pOld->GetID(), pOld->GetVnum(),
			pNew->GetID(), pNew->GetVnum());
}
