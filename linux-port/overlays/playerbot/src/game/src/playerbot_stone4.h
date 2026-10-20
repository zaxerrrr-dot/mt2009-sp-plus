#ifndef __INC_METIN2_PLAYERBOT_STONE4_H__
#define __INC_METIN2_PLAYERBOT_STONE4_H__

// MT2009_PLUS_BOT_STONE4_MARKET_V1 (the owner, 19 October): the soul stones +4.
//
// Iwakura's list kept every +4 a bot found, five of a kind counting the box
// (playerbot_persona_rules.h, LppKeepsStone), and the box never let a stone
// go again. The counters sold the +4 only while the boxes were full; with the
// four pages of 15 October none was, and from that day the market had none:
// 1 474 stones +4 in 575 bots' boxes on 19 October, not a bot over four of a
// kind, 1 156 of them of the kinds no bot ever seats (Powtorki, the four
// class stones, Magii - PvE tier under PLAYERBOT_SOUL_STONE_MIN_PVE_TIER).
//
// The rule now, every number in playerbot_weights.tsv (STONE4_*):
//
//   * A kind the bot seats (GetPlayerBotSoulStoneSeatTier > 0) has a quota of
//     its own, STONE4_KEEP (4): each new stone of the kind draws once,
//     STONE4_KEEP_PCT (60) percent into the quota while it is short, the rest
//     surplus. A kind it never seats has no quota.
//   * Surplus goes on the bot's own counter. MT2009 PLUS port (20 October,
//     the owner: "nie limituj dalej rynku, ale spraw aby boty wystawialy KD
//     +4"): the world's counters are not capped - STONE4_MARKET_SEATED /
//     STONE4_MARKET_UNSEATED default to 0, no limit; a number above 0 is the
//     original patch's cap of the kind across all counters.
//   * The box and the merchant are fallbacks only: with no counter, or no
//     room on it, surplus goes into the box, up to STONE4_BOX_SEATED (200) /
//     STONE4_BOX_UNSEATED (2) of the kind in bag and box; past that, and
//     still no room on the counter, to the general merchant.
//   * The box gives its surplus back for the counter whenever the counter has
//     room, at most STONE4_RELEASE_VISIT (2) stones a visit
//     (WithdrawPlayerBotSafebox).
//   * A stone the bot has a socket for now is seated, as before.
//
// The draw is no mark on the item. The stones stack to two hundred and a new
// drop joins the stack it finds, which is how the old per-stack draw of the
// +0..+2 grew its "market" stacks without end (6cd7172). What is drawn is a
// count per bot and kind: `seen` the units the bot held at its last look,
// `quota` the units of them that are its own; the bag's first `quota` units
// in cell order (after what the box holds of it) are the kept ones, and the
// stack the line falls inside is cut there (SplitPlayerBotStone4Kept).
//
// STONE4_OFF 1: Iwakura's rule as it was. An implementation fragment in the
// sense playerbot_types.h describes: include it once, after playerbot_town.h
// and before playerbot_lpp.h; playerbot_economy.h and playerbot_town.h
// forward-declare what they ask of it.

namespace
{
	enum EPlayerBotStone4Role
	{
		PLAYERBOT_STONE4_NONE,      // not a +4 of this rule: the old rules decide
		PLAYERBOT_STONE4_KEEP,      // the bot's own: bag or box, never sold
		PLAYERBOT_STONE4_SELL,      // counter goods
		PLAYERBOT_STONE4_BOX,       // surplus, into the box while the market is full
		PLAYERBOT_STONE4_MERCHANT,  // surplus past the box's cap: the merchant's
	};

	struct TPlayerBotStone4Kind
	{
		int box;    // units in the box at the last visit
		int seen;   // units in bag and box at the last look
		int quota;  // of them, the bot's own
		bool init;
		TPlayerBotStone4Kind() : box(0), seen(0), quota(0), init(false)
		{
		}
	};
	typedef std::map<DWORD, TPlayerBotStone4Kind> TPlayerBotStone4Kinds;
	std::map<DWORD, TPlayerBotStone4Kinds> s_mapPlayerBotStone4;
	// The bots whose box a visit has counted since this start: until then the
	// rule does not know what is down there and keeps every +4, as before.
	std::set<DWORD> s_setPlayerBotStone4BoxKnown;

	const DWORD PLAYERBOT_STONE4_REPORT_MS = 10 * 60 * 1000;
	DWORD s_dwPlayerBotStone4ReportAt = 0;
	unsigned int s_uPlayerBotStone4Kept = 0;
	unsigned int s_uPlayerBotStone4Surplus = 0;
	unsigned int s_uPlayerBotStone4Released = 0;
	unsigned int s_uPlayerBotStone4Merchant = 0;
	unsigned int s_uPlayerBotStone4Splits = 0;

	bool IsPlayerBotStone4Vnum(DWORD vnum)
	{
		return IsPlayerBotSoulStoneVnum(vnum) && GetPlayerBotSoulStoneGrade(vnum) == 4;
	}

	bool IsPlayerBotStone4On()
	{
		return !IsPlayerBotStone4Off() && IsPlayerBotPersonaEnabled();
	}

	// A kind the bot puts into a socket at all - the test its seating asks
	// first (ManagePlayerBotSoulStones).
	bool IsPlayerBotStone4Seated(DWORD vnum)
	{
		return GetPlayerBotSoulStoneSeatTier(vnum) > 0;
	}

	int GetPlayerBotStone4Keep(DWORD vnum)
	{
		return IsPlayerBotStone4Seated(vnum) ? GetPlayerBotStone4KeepUnits() : 0;
	}

	// What the world's counters still take of the kind, players' counters
	// counted (the ledger, moved by every add - AddPlayerBotMarketSupply).
	// Before the first ledger there is no room: nothing goes up blind.
	// A cap of 0 (the MT2009 PLUS default) is no cap: room without end.
	const int PLAYERBOT_STONE4_NO_CAP_ROOM = 1000000;
	int GetPlayerBotStone4MarketRoom(DWORD vnum)
	{
		const int cap = GetPlayerBotStone4MarketCapOf(IsPlayerBotStone4Seated(vnum));
		if (cap <= 0)
			return PLAYERBOT_STONE4_NO_CAP_ROOM;
		if (s_dwMarketLedgerTime == 0)
			return 0;
		const TPlayerBotMarketLedgerEntry* entry = GetPlayerBotMarketLedgerEntry(vnum);
		const int listed = entry ? (int)entry->dwSupplyUnits : 0;
		return std::max(0, cap - listed);
	}

	// MT2009 PLUS port: whether the bot's own counter has a free cell, as the
	// last listing pass saw it (BotOfflinePrepareVisitLine). A bot whose
	// counter no pass has looked at yet counts as having room: it opens one.
	std::map<DWORD, bool> s_mapPlayerBotStone4StallRoom;
	void NotePlayerBotStone4StallRoom(LPCHARACTER ch, bool room)
	{
		if (ch)
			s_mapPlayerBotStone4StallRoom[ch->GetPlayerID()] = room;
	}
	bool PlayerBotStone4StallHasRoom(LPCHARACTER ch)
	{
		if (!ch || !PlayerBotHasCounter(ch))
			return false;
		std::map<DWORD, bool>::const_iterator it = s_mapPlayerBotStone4StallRoom.find(ch->GetPlayerID());
		return it == s_mapPlayerBotStone4StallRoom.end() || it->second;
	}

	bool IsPlayerBotStone4MarketFull(DWORD vnum)
	{
		return GetPlayerBotStone4MarketRoom(vnum) <= 0;
	}

	// The bot's count of the kind, or NULL while its box has not been counted
	// since this start. A companion's bag is its owner's: not this rule's.
	TPlayerBotStone4Kind* FindPlayerBotStone4Kind(LPCHARACTER ch, DWORD vnum)
	{
		if (!ch || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return NULL;
		const DWORD pid = ch->GetPlayerID();
		if (s_setPlayerBotStone4BoxKnown.find(pid) == s_setPlayerBotStone4BoxKnown.end())
			return NULL;
		TPlayerBotStone4Kind& kind = s_mapPlayerBotStone4[pid][vnum];
		return kind.init ? &kind : NULL;
	}

	// Of the quota, what the bag must hold: the box's units count first.
	int GetPlayerBotStone4BagKeep(const TPlayerBotStone4Kind& kind)
	{
		return kind.quota - std::min(kind.box, kind.quota);
	}

	// What becomes of this +4 in the bag. A line on a counter or a stone in
	// the box is no bag piece: never "kept" by this rule, so no counter line
	// comes home for it (BotOfflineUnwantedLine).
	int GetPlayerBotStone4Role(LPCHARACTER ch, LPITEM item, bool boxFull)
	{
		if (!ch || !item || item->GetType() != ITEM_METIN || !IsPlayerBotStone4Vnum(item->GetVnum()) ||
				!IsPlayerBotStone4On() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return PLAYERBOT_STONE4_NONE;
		if (item->GetWindow() != INVENTORY || item->IsEquipped() || ch->GetInventoryItem(item->GetCell()) != item)
			return PLAYERBOT_STONE4_SELL;
		const DWORD vnum = item->GetVnum();
		const TPlayerBotStone4Kind* kind = FindPlayerBotStone4Kind(ch, vnum);
		// Not counted yet: kept, the way the list kept it, until a visit
		// counts the box.
		if (!kind)
			return PLAYERBOT_STONE4_KEEP;
		const int ahead = CountPlayerBotVnumUnitsAhead(ch, item);
		const int bagKeep = GetPlayerBotStone4BagKeep(*kind);
		if (ahead < bagKeep)
			return PLAYERBOT_STONE4_KEEP;
		// A socket for it now: it is seated within seconds.
		if (CanPlayerBotSeatSoulStone(ch, vnum, (DWORD)item->GetValue(5)))
			return PLAYERBOT_STONE4_KEEP;
		if (!IsPlayerBotStone4MarketFull(vnum) && PlayerBotStone4StallHasRoom(ch))
			return PLAYERBOT_STONE4_SELL;
		const int cap = GetPlayerBotStone4BoxCapOf(IsPlayerBotStone4Seated(vnum));
		if (!boxFull && kind->box + ahead + (int)item->GetCount() <= cap)
			return PLAYERBOT_STONE4_BOX;
		return PLAYERBOT_STONE4_MERCHANT;
	}

	bool IsPlayerBotStone4ForMerchant(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item)
			return false;
		TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		const bool boxFull = st != s_mapPlayerBotAIStates.end() && st->second.persona.bLppBoxFull;
		return GetPlayerBotStone4Role(ch, item, boxFull) == PLAYERBOT_STONE4_MERCHANT;
	}

	// For the counter's scorer: a +4 of this rule that is not counter goods.
	bool IsPlayerBotStone4HeldBack(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item)
			return false;
		TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.find(ch->GetPlayerID());
		const bool boxFull = st != s_mapPlayerBotAIStates.end() && st->second.persona.bLppBoxFull;
		const int role = GetPlayerBotStone4Role(ch, item, boxFull);
		return role != PLAYERBOT_STONE4_NONE && role != PLAYERBOT_STONE4_SELL;
	}

	// A counter takes no line of a kind the world's counters hold their cap of
	// (BotOfflineCounterRefuses) - never, at the MT2009 PLUS default cap 0.
	bool IsPlayerBotStone4CounterFull(LPITEM item)
	{
		return item && item->GetType() == ITEM_METIN && IsPlayerBotStone4Vnum(item->GetVnum()) &&
				IsPlayerBotStone4On() && IsPlayerBotStone4MarketFull(item->GetVnum());
	}

	// The box counted at a visit (RefreshPlayerBotLppStored): every +4 in it.
	void NotePlayerBotStone4Box(LPCHARACTER ch, CSafebox* box)
	{
		if (!ch || !box)
			return;
		const DWORD pid = ch->GetPlayerID();
		TPlayerBotStone4Kinds& kinds = s_mapPlayerBotStone4[pid];
		for (TPlayerBotStone4Kinds::iterator it = kinds.begin(); it != kinds.end(); ++it)
			it->second.box = 0;
		for (DWORD pos = 0; pos < SAFEBOX_MAX_NUM; ++pos)
		{
			if (!box->IsValidPosition(pos))
				continue;
			LPITEM item = box->Get(pos);
			if (item && item->GetType() == ITEM_METIN && IsPlayerBotStone4Vnum(item->GetVnum()))
				kinds[item->GetVnum()].box += std::max<int>(1, item->GetCount());
		}
		s_setPlayerBotStone4BoxKnown.insert(pid);
	}

	// What the box holds over the quota, by kind, that the market has room for
	// now - the visits the release asks for (wLppReleasable).
	int CountPlayerBotStone4Releasable(LPCHARACTER ch)
	{
		if (!ch || !IsPlayerBotStone4On() || !PlayerBotStone4StallHasRoom(ch) || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return 0;
		std::map<DWORD, TPlayerBotStone4Kinds>::const_iterator bot = s_mapPlayerBotStone4.find(ch->GetPlayerID());
		if (bot == s_mapPlayerBotStone4.end())
			return 0;
		int units = 0;
		for (TPlayerBotStone4Kinds::const_iterator it = bot->second.begin(); it != bot->second.end(); ++it)
		{
			if (!it->second.init)
				continue;
			const int surplus = it->second.box - std::min(it->second.box, it->second.quota);
			units += std::min(surplus, GetPlayerBotStone4MarketRoom(it->first));
		}
		return std::min(units, GetPlayerBotStone4ReleaseVisit());
	}

	// How many of this box stack come out now for a counter: the box's surplus
	// of the kind, the market's room, the visit's allowance - less what this
	// visit took already (`takenOfKind`, `takenAll`).
	int GetPlayerBotStone4BoxRelease(LPCHARACTER ch, LPITEM boxItem, int takenOfKind, int takenAll)
	{
		if (!ch || !boxItem || boxItem->GetType() != ITEM_METIN || !IsPlayerBotStone4Vnum(boxItem->GetVnum()) ||
				!IsPlayerBotStone4On() || !PlayerBotStone4StallHasRoom(ch))
			return 0;
		const TPlayerBotStone4Kind* kind = FindPlayerBotStone4Kind(ch, boxItem->GetVnum());
		if (!kind)
			return 0;
		const int surplus = kind->box - std::min(kind->box, kind->quota) - takenOfKind;
		const int room = GetPlayerBotStone4MarketRoom(boxItem->GetVnum()) - takenOfKind;
		const int allowance = GetPlayerBotStone4ReleaseVisit() - takenAll;
		const int freeAfter = CountPlayerBotFreeInventoryCells(ch) - 1;
		if (freeAfter <= PLAYERBOT_BAG_PRESSURE_FREE_CELLS)
			return 0;
		return std::max(0, std::min(std::min(surplus, room), std::min(allowance, (int)boxItem->GetCount())));
	}

	void NotePlayerBotStone4Released(int units)
	{
		s_uPlayerBotStone4Released += (unsigned int)std::max(0, units);
	}

	void NotePlayerBotStone4Sold(int units)
	{
		s_uPlayerBotStone4Merchant += (unsigned int)std::max(0, units);
	}

	// One of the kind went into a socket (ManagePlayerBotSoulStones), cracked
	// or not: out of the quota and of the count, so the next look does not
	// take the gap for a sale.
	void NotePlayerBotStone4Used(LPCHARACTER ch, DWORD vnum)
	{
		if (!IsPlayerBotStone4Vnum(vnum))
			return;
		TPlayerBotStone4Kind* kind = FindPlayerBotStone4Kind(ch, vnum);
		if (!kind)
			return;
		kind->quota = std::max(0, kind->quota - 1);
		kind->seen = std::max(0, kind->seen - 1);
	}

	// The bag's kept units of a kind in one stack or more at its front: the
	// stack the line falls inside is cut there, so a whole stack is either the
	// bot's or surplus. One cut a look.
	bool SplitPlayerBotStone4Kept(LPCHARACTER ch, DWORD vnum, int bagKeep)
	{
		if (bagKeep <= 0)
			return false;
		int ahead = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetCell() != cell || item->GetVnum() != vnum)
				continue;
			const int count = std::max<int>(1, item->GetCount());
			if (ahead < bagKeep && ahead + count > bagKeep)
			{
				if (item->IsEquipped() || item->isLocked())
					return false;
				const int cut = ahead + count - bagKeep;
				const int to = ch->GetEmptyInventory(item->GetSize());
				if (to < 0 || CountPlayerBotFreeInventoryCells(ch) <= PLAYERBOT_BAG_PRESSURE_FREE_CELLS)
					return false;
				if (!ch->MoveItem(TItemPos(INVENTORY, cell), TItemPos(INVENTORY, (WORD)to), cut))
					return false;
				++s_uPlayerBotStone4Splits;
				return true;
			}
			ahead += count;
			if (ahead >= bagKeep)
				return false;
		}
		return false;
	}

	void ReportPlayerBotStone4(DWORD dwNow)
	{
		if (s_dwPlayerBotStone4ReportAt != 0 && dwNow - s_dwPlayerBotStone4ReportAt < PLAYERBOT_STONE4_REPORT_MS)
			return;
		const bool first = s_dwPlayerBotStone4ReportAt == 0;
		s_dwPlayerBotStone4ReportAt = dwNow;
		if (first)
			return;
		unsigned int boxed = 0, quota = 0;
		std::map<DWORD, unsigned int> boxByKind;
		for (std::map<DWORD, TPlayerBotStone4Kinds>::const_iterator bot = s_mapPlayerBotStone4.begin();
				bot != s_mapPlayerBotStone4.end(); ++bot)
			for (TPlayerBotStone4Kinds::const_iterator it = bot->second.begin(); it != bot->second.end(); ++it)
			{
				boxed += (unsigned int)std::max(0, it->second.box);
				quota += (unsigned int)std::max(0, it->second.quota);
				boxByKind[it->first] += (unsigned int)std::max(0, it->second.box);
			}
		std::string market;
		for (DWORD vnum = 28430; vnum <= 28443; ++vnum)
		{
			if (!IsPlayerBotStone4Vnum(vnum))
				continue;
			const TPlayerBotMarketLedgerEntry* entry = GetPlayerBotMarketLedgerEntry(vnum);
			char buf[48];
			snprintf(buf, sizeof(buf), " %u=%u/%d(box %u)", vnum, entry ? entry->dwSupplyUnits : 0U,
					GetPlayerBotStone4MarketCapOf(IsPlayerBotStone4Seated(vnum)), boxByKind[vnum]);
			market += buf;
		}
		sys_log(0, "PLAYERBOT_STONE4: report bots=%u box=%u quota=%u kept=%u surplus=%u released=%u merchant=%u splits=%u market:%s",
				(unsigned int)s_setPlayerBotStone4BoxKnown.size(), boxed, quota, s_uPlayerBotStone4Kept,
				s_uPlayerBotStone4Surplus, s_uPlayerBotStone4Released, s_uPlayerBotStone4Merchant,
				s_uPlayerBotStone4Splits, market.c_str());
		s_uPlayerBotStone4Kept = s_uPlayerBotStone4Surplus = s_uPlayerBotStone4Released = 0;
		s_uPlayerBotStone4Merchant = s_uPlayerBotStone4Splits = 0;
	}

	// The look, on the seating's clock (ManagePlayerBotSoulStones): what the
	// bot holds of each +4 kind, bag and box; each unit over the last look
	// draws once for the quota; the kept units' stack cut.
	void UpdatePlayerBotStone4(LPCHARACTER ch, DWORD dwNow)
	{
		ReportPlayerBotStone4(dwNow);
		if (!ch || !ch->IsItemLoaded() || !IsPlayerBotStone4On() || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return;
		const DWORD pid = ch->GetPlayerID();
		if (s_setPlayerBotStone4BoxKnown.find(pid) == s_setPlayerBotStone4BoxKnown.end())
			return;
		std::map<DWORD, int> bag;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (item && item->GetCell() == cell && !item->IsEquipped() && item->GetType() == ITEM_METIN &&
					IsPlayerBotStone4Vnum(item->GetVnum()))
				bag[item->GetVnum()] += std::max<int>(1, item->GetCount());
		}
		TPlayerBotStone4Kinds& kinds = s_mapPlayerBotStone4[pid];
		for (std::map<DWORD, int>::const_iterator it = bag.begin(); it != bag.end(); ++it)
			kinds[it->first];
		const int percent = GetPlayerBotStone4KeepPercent();
		bool cut = false;
		for (TPlayerBotStone4Kinds::iterator it = kinds.begin(); it != kinds.end(); ++it)
		{
			TPlayerBotStone4Kind& kind = it->second;
			std::map<DWORD, int>::const_iterator inBag = bag.find(it->first);
			const int held = (inBag != bag.end() ? inBag->second : 0) + kind.box;
			const int keep = GetPlayerBotStone4Keep(it->first);
			if (!kind.init)
			{
				// What a bot holds when this start first counts it is its own
				// up to the quota: no bot held over four of a kind on the day
				// this came in.
				kind.init = true;
				kind.seen = held;
				kind.quota = std::min(held, keep);
				continue;
			}
			if (held > kind.seen)
			{
				int kept = 0, surplus = 0;
				for (int n = kind.seen; n < held; ++n)
				{
					if (kind.quota < keep && number(1, 100) <= percent)
					{
						++kind.quota;
						++kept;
					}
					else
						++surplus;
				}
				s_uPlayerBotStone4Kept += (unsigned int)kept;
				s_uPlayerBotStone4Surplus += (unsigned int)surplus;
				sys_log(0, "PLAYERBOT_STONE4: drew pid=%u name=%s vnum=%u new=%d kept=%d surplus=%d quota=%d/%d held=%d box=%d",
						pid, ch->GetName(), it->first, held - kind.seen, kept, surplus, kind.quota, keep, held, kind.box);
			}
			kind.seen = held;
			kind.quota = std::min(kind.quota, held);
			if (!cut && inBag != bag.end())
				cut = SplitPlayerBotStone4Kept(ch, it->first, GetPlayerBotStone4BagKeep(kind));
		}
	}
}

#endif
