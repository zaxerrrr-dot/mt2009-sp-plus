#ifndef __INC_METIN2_PLAYERBOT_JUKI_H__
#define __INC_METIN2_PLAYERBOT_JUKI_H__

// MT2009_PLUS_BOT_JUKI_REVIEW_V1 - the bots learn where their horse bags went.
//
// The horse bags ("juki konne") are gone on Yohara (MT2009_PLUS_HORSE40_V3,
// server-patches/konie): linux-port/docker/mariadb/playerbot/juki_usuniecie.sql
// moved every item kept in them, once per world, to the owner's bag pages, else
// the account's storeroom (window SAFEBOX), else the ItemShop storage
// (item_award), and logged each move in player.horse_bag_migration_log.
//
// - The bag: nothing to do. The items load with the character, and the
//   equipment pass, the anvil, the merchants and the counter look at the bag
//   from the first tick after a login as they always do.
// - The storeroom: the visit's own cache of the box (TPlayerBotPersona's
//   bLppStoredKnown, mapGearStored, wBoxMaterialUnits) starts unknown at every
//   login, but nothing sent a bot to the storekeeper for a box it had never
//   put anything in, and the withdrawal's rules look at four gear slots and the
//   kinds the deposit sends down - a saddlebag's jewellery, potions and junk
//   would have stayed there for good. So: once per character (the quest flag
//   PLAYERBOT_JUKI_REVIEWED_FLAG), the log's rows for its pid are read on the
//   engine's queue; the ids that went to the storeroom make a storekeeper
//   visit of their own (ignoring the empty-visit back-off), and at the open box
//   RunPlayerBotJukiSafeboxReview takes out of those ids what the bot wants -
//   a piece that beats what it wears in any slot, a material the anvil is
//   short of, potions up to the belt the merchant's trim leaves, arrows it is
//   short of, its own skill book, the merchant's junk and goods for its own
//   counter (while the market is not glutted) - into a bag clear of pressure,
//   and leaves the rest where it is. The ids it decided on are done; the ones
//   it wanted but had no room or turn for wait for the next visit, at most
//   PLAYERBOT_JUKI_MAX_VISITS of them.
// - The ItemShop storage: the bots' storerooms have four pages, so on the test
//   world no bot item went there (the log says so per bot:
//   "PLAYERBOT_JUKI: ... award=N"); a bot does not open the mall window, and
//   what is there stays for the operator to see.
//
// An implementation fragment in the sense playerbot_types.h describes:
// included once, from playerbot_manager.cpp, right after playerbot_town.h,
// which declares what it calls from here.

namespace
{
	const char* const PLAYERBOT_JUKI_REVIEWED_FLAG = "juki.reviewed";
	// Out of the migrated ids at one open box, and how many visits the ids the
	// bot wanted but had no room for may take before the review is closed.
	const int PLAYERBOT_JUKI_WITHDRAW_MAX = 12;
	const int PLAYERBOT_JUKI_MAX_VISITS = 4;
	// The cheapest line a counter is worth a cell of the bag for.
	const DWORD PLAYERBOT_JUKI_COUNTER_MIN_PRICE = 20000;

	struct TPlayerBotJukiReview
	{
		std::set<DWORD> ids;	// item ids moved to the storeroom, not decided yet
		int visits;
		TPlayerBotJukiReview() : visits(0) {}
	};
	std::map<DWORD, TPlayerBotJukiReview> s_mapPlayerBotJukiReview;	// pid -> pending review
	std::set<DWORD> s_setPlayerBotJukiAsked;	// pid: the log was asked for in this core's life

	void MarkPlayerBotJukiReviewed(LPCHARACTER ch, const char* why)
	{
		if (!ch)
			return;
		ch->SetQuestFlag(PLAYERBOT_JUKI_REVIEWED_FLAG, 1);
		s_mapPlayerBotJukiReview.erase(ch->GetPlayerID());
		sys_log(0, "PLAYERBOT_JUKI: reviewed pid=%u name=%s why=%s", ch->GetPlayerID(), ch->GetName(), why);
	}

	// Once per character and core: the log's rows for this pid, on the
	// engine's queue. Called from the bot's tick; does nothing until the
	// quest flags are loaded, and nothing again once the flag is set.
	void PollPlayerBotJukiReview(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return;
		const DWORD pid = ch->GetPlayerID();
		if (s_setPlayerBotJukiAsked.find(pid) != s_setPlayerBotJukiAsked.end())
			return;
		quest::PC* pc = quest::CQuestManager::instance().GetPC(pid);
		if (!pc || !pc->IsLoaded())
			return;
		s_setPlayerBotJukiAsked.insert(pid);
		if (ch->GetQuestFlag(PLAYERBOT_JUKI_REVIEWED_FLAG) > 0)
			return;
		DBManager::instance().FuncQuery([pid](SQLMsg* msg)
		{
			LPCHARACTER bot = CHARACTER_MANAGER::instance().FindByPID(pid);
			if (!bot || s_mapPlayerBotAIStates.find(pid) == s_mapPlayerBotAIStates.end())
			{
				// Gone before the answer: asked again at its next login.
				s_setPlayerBotJukiAsked.erase(pid);
				return;
			}
			if (!msg || msg->uiSQLErrno != 0 || !msg->Get())
			{
				sys_err("PLAYERBOT_JUKI: log query failed pid=%u name=%s errno=%u", pid, bot->GetName(),
						msg ? (unsigned int)msg->uiSQLErrno : 0U);
				return;
			}
			int inBag = 0, inBox = 0, inAward = 0;
			TPlayerBotJukiReview review;
			if (msg->Get()->pSQLResult)
			{
				MYSQL_ROW row;
				while ((row = mysql_fetch_row(msg->Get()->pSQLResult)))
				{
					DWORD itemId = 0;
					str_to_number(itemId, row[0]);
					const char* dest = row[1] ? row[1] : "";
					if (!strcmp(dest, "SAFEBOX"))
					{
						++inBox;
						if (itemId)
							review.ids.insert(itemId);
					}
					else if (!strcmp(dest, "ITEM_AWARD"))
						++inAward;
					else
						++inBag;
				}
			}
			sys_log(0, "PLAYERBOT_JUKI: log pid=%u name=%s bag=%d safebox=%d award=%d",
					pid, bot->GetName(), inBag, inBox, inAward);
			if (inAward > 0)
				sys_log(0, "PLAYERBOT_JUKI: award left for the operator pid=%u name=%s items=%d (a bot opens no ItemShop storage)",
						pid, bot->GetName(), inAward);
			if (review.ids.empty())
			{
				MarkPlayerBotJukiReviewed(bot, inBag + inAward > 0 ? "nothing_in_safebox" : "no_rows");
				return;
			}
			s_mapPlayerBotJukiReview[pid] = review;
			// The visit is asked now, not after the empty-visit back-off.
			s_mapPlayerBotSafeboxIdleUntil.erase(pid);
			sys_log(0, "PLAYERBOT_JUKI: storekeeper visit wanted pid=%u name=%s items=%u",
					pid, bot->GetName(), (unsigned int)review.ids.size());
		}, "SELECT item_id, dest FROM player.horse_bag_migration_log WHERE owner_id=%u", pid);
	}

	// The town visit's question: a review is pending and the bag has room for
	// at least a three-cell piece.
	bool PlayerBotWantsJukiReview(LPCHARACTER ch)
	{
		if (!ch || IsPlayerBotSidekickServing(ch))
			return false;
		std::map<DWORD, TPlayerBotJukiReview>::const_iterator it = s_mapPlayerBotJukiReview.find(ch->GetPlayerID());
		return it != s_mapPlayerBotJukiReview.end() && !it->second.ids.empty() && ch->GetEmptyInventory(3) >= 0;
	}

	// A piece of the box this bot would put on now, in any slot: the
	// storeroom twin of IsPlayerBotWearableUpgrade (which needs a bag cell)
	// and IsPlayerBotOwnBoxGear (which looks at four slots).
	bool IsPlayerBotJukiGearUpgrade(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || item->GetLevelLimit() > ch->GetLevel() || !IsPlayerBotEquipmentCandidate(ch, item))
			return false;
		const int wearCell = item->FindEquipCell(ch);
		if (wearCell < 0 || wearCell >= WEAR_MAX_NUM)
			return false;
		const long long score = GetPlayerBotEquipmentScore(item, ch);
		LPITEM worn = ch->GetWear((WORD)wearCell);
		if (worn && (IS_SET(worn->GetFlag(), ITEM_FLAG_IRREMOVABLE) || GetPlayerBotEquipmentScore(worn, ch) >= score))
			return false;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM other = ch->GetInventoryItem(cell);
			if (other && other->GetCell() == cell && !other->IsEquipped() && other->FindEquipCell(ch) == wearCell &&
					other->GetLevelLimit() <= ch->GetLevel() && IsPlayerBotEquipmentCandidate(ch, other) &&
					GetPlayerBotEquipmentScore(other, ch) >= score)
				return false;
		}
		return true;
	}

	// Why the bot takes this migrated piece out, or NULL to leave it.
	// needsRoom: the take must leave the bag clear of pressure.
	const char* GetPlayerBotJukiWant(LPCHARACTER ch, LPITEM item, bool& needsRoom)
	{
		needsRoom = true;
		if (IsPlayerBotJukiGearUpgrade(ch, item))
		{
			needsRoom = false;
			return "gear";
		}
		const DWORD vnum = item->GetVnum();
		if (IsPlayerBotTradeableMaterial(item) && PlayerBotNeedsRefineMaterial(ch, vnum))
			return "anvil";
		const EPlayerBotPotionSupply supply = GetPlayerBotPotionSupply(vnum);
		if (supply != PLAYERBOT_POTION_SUPPLY_NONE)
			return CountPlayerBotPotionSupply(ch, supply) + item->GetCount() <= GetPlayerBotPotionSupplyLimit(ch, supply)
					? "potion" : NULL;
		if (IsPlayerBotUsableArrow(ch, item))
			return NeedsPlayerBotArrows(ch) ? "arrows" : NULL;
		if (item->GetType() == ITEM_SKILLBOOK)
			return !IsPlayerBotSurplusSkillBook(ch, item) ? "book" : NULL;
		if (IsPlayerBotJunkItem(ch, item))
			return "sell";
		if (PlayerBotHasCounter(ch) && GetPlayerBotShopAskingPrice(item) >= PLAYERBOT_JUKI_COUNTER_MIN_PRICE &&
				GetPlayerBotMarketSupplyState(vnum) <= 0)
			return "counter";
		return NULL;
	}

	// At the open box, after the visit's own deposit and withdrawal: the
	// migrated ids still pending. Returns how many came out; *pSell counts the
	// ones for the merchants, so the visit calls on them again.
	int RunPlayerBotJukiSafeboxReview(LPCHARACTER ch, CSafebox* box, const std::set<DWORD>& justDeposited, int* pSell)
	{
		if (pSell)
			*pSell = 0;
		if (!ch || !box || IsPlayerBotSidekickServing(ch))
			return 0;
		std::map<DWORD, TPlayerBotJukiReview>::iterator rv = s_mapPlayerBotJukiReview.find(ch->GetPlayerID());
		if (rv == s_mapPlayerBotJukiReview.end())
			return 0;
		TPlayerBotJukiReview& review = rv->second;
		++review.visits;
		const DWORD dwBoxNow = get_dword_time();
		std::set<DWORD> seen;
		int taken = 0, left = 0, waiting = 0;
		for (DWORD pos = 0; pos < SAFEBOX_MAX_NUM; ++pos)
		{
			if (!box->IsValidPosition(pos))
				continue;
			LPITEM item = box->Get(pos);
			if (!item || review.ids.find(item->GetID()) == review.ids.end())
				continue;
			seen.insert(item->GetID());
			// The kind this visit just put down stays, as the withdrawal's own
			// rule has it; the G0 dust is the G0 package's.
			if (justDeposited.find(item->GetVnum()) != justDeposited.end() || IsPlayerBotG0BoxDust(ch, item))
			{
				review.ids.erase(item->GetID());
				++left;
				continue;
			}
			bool needsRoom = true;
			const char* why = GetPlayerBotJukiWant(ch, item, needsRoom);
			if (!why)
			{
				review.ids.erase(item->GetID());
				++left;
				continue;
			}
			const int freeAfter = CountPlayerBotFreeInventoryCells(ch) - (int)item->GetSize();
			const int cell = ch->GetEmptyInventory(item->GetSize());
			if (taken >= PLAYERBOT_JUKI_WITHDRAW_MAX || cell < 0 ||
					(needsRoom && freeAfter <= PLAYERBOT_BAG_PRESSURE_FREE_CELLS))
			{
				++waiting;
				continue;
			}
			char szHint[128];
			snprintf(szHint, sizeof(szHint), "%s %u", item->GetName(), (unsigned int)item->GetCount());
			const DWORD itemId = item->GetID();
			box->Remove(pos);
			item->AddToCharacter(ch, TItemPos(INVENTORY, (WORD)cell));
			FlushPlayerBotItemRow(item);
			LogManager::instance().ItemLog(ch, item, "SAFEBOX GET", szHint);
			sys_log(0, "PLAYERBOT_JUKI: safebox withdraw pid=%u name=%s item=%u vnum=%u count=%u reason=%s",
					ch->GetPlayerID(), ch->GetName(), itemId, item->GetVnum(), (unsigned int)item->GetCount(), why);
			NotePlayerBotBoxMove(s_mapPlayerBotBoxTakenAt, ch->GetPlayerID(), item->GetVnum(), dwBoxNow);
			if (pSell && !strcmp(why, "sell"))
				++*pSell;
			review.ids.erase(itemId);
			++taken;
		}
		// What is no longer in the box - taken by the visit's own rules a moment
		// ago, or by anyone since the migration - needs nothing more.
		int gone = 0;
		for (std::set<DWORD>::iterator it = review.ids.begin(); it != review.ids.end();)
		{
			if (seen.find(*it) == seen.end())
			{
				review.ids.erase(it++);
				++gone;
			}
			else
				++it;
		}
		const int visits = review.visits;
		const size_t pending = review.ids.size();
		sys_log(0, "PLAYERBOT_JUKI: safebox review pid=%u name=%s visit=%d taken=%d left=%d gone=%d waiting=%d free_cells=%d",
				ch->GetPlayerID(), ch->GetName(), visits, taken, left, gone, waiting, CountPlayerBotFreeInventoryCells(ch));
		if (pending == 0)
			MarkPlayerBotJukiReviewed(ch, "safebox_done");
		else if (visits >= PLAYERBOT_JUKI_MAX_VISITS)
			MarkPlayerBotJukiReviewed(ch, "safebox_visits_used");
		return taken;
	}
}

#endif
