#ifndef __INC_METIN2_PLAYERBOT_CHAT_DEALS_H__
#define __INC_METIN2_PLAYERBOT_CHAT_DEALS_H__

// MT2009_PLUS_BOT_CHAT_V2 (deals) - a trade talked over on the whisper, done
// in the exchange window.
//
// The owner, 4 October: a bot posts "B> Zdobycz Dzikusa x10, kto ma? pw", a
// person whispers "czesc, mam do sprzedania zdobycz dzikusa" - and the bot
// has to know it is the answer to its post, name its price, bargain within
// what it can really pay, and then buy: meet the person, take the items in
// the window, put the yang in, accept. The same for a bot selling from its
// bag.
//
// The talk is the conversation's (playerbot_conv_generator.h, TDeal in the
// pair's memory). This file is the rest:
//   - QuotePlayerBotDealItem: what a whisper names, as an item of this world
//     (the bag, the counter, the wanted materials, the item table), its fair
//     price (the sale memory, the cheapest counter, else the asking price),
//     whether the bot buys it (a material it is short of, an open "K>" post
//     of its own, the weapon it saves for, a merchant's resale) and at what
//     most, and whether it has it to sell and at what least. A bot never pays
//     more than the market's price and a tenth (its own post's price for its
//     post) nor more than 60% of its purse; it never sells under 85% of the
//     market, nor what it is short of itself, nor what it wears.
//   - RegisterPlayerBotDeal: the settled deal, held for PLAYERBOT_DEAL_TTL_MS,
//     and the meeting - near (the window now), on the same map (the bot walks
//     over, the summon's walk), elsewhere (the person comes).
//   - HandlePlayerBotDealTrade: the bot's tick while a deal waits. Near the
//     person it opens the window itself; in the window it checks what the
//     person put in - only the item, no more than agreed - and pays exactly
//     for it (CExchange::AddGold), or puts its own pieces in (a stack split
//     to the count) and waits for the person's yang
//     (CExchange::Mt2009PlusGetGold, server-patches/playerqol); it accepts
//     only after the person has, and only while the window still holds what
//     was checked. Done: a thanks, the post closed, the memory told.
//
// An implementation fragment: include it once, after
// playerbot_chat_conversation.h and playerbot_gift_trade.h; the manager's
// tick asks HandlePlayerBotDealTrade before the gift trade.

namespace
{
	const DWORD PLAYERBOT_DEAL_TTL_MS = 15 * 60 * 1000;
	const int PLAYERBOT_DEAL_NEAR = 800;
	const DWORD PLAYERBOT_DEAL_OPEN_RETRY_MS = 15000;
	const DWORD PLAYERBOT_DEAL_WINDOW_MAX_MS = 3 * 60 * 1000;
	const DWORD PLAYERBOT_DEAL_GLANCE_MIN_MS = 700;
	const DWORD PLAYERBOT_DEAL_GLANCE_MAX_MS = 1600;

	struct TPlayerBotDeal
	{
		BYTE side;          // playerbot_conv::EDealSide
		DWORD vnum;
		int count;
		long long unit;
		DWORD at;
		DWORD nextOpenAt;
		DWORD windowSince;
		DWORD decideAt;
		bool paid;          // the bot's yang is in the window
		int paidPieces;
		bool offered;       // the bot's pieces are in the window
		DWORD warnedAt;
		TPlayerBotDeal() : side(0), vnum(0), count(0), unit(0), at(0), nextOpenAt(0), windowSince(0), decideAt(0),
			paid(false), paidPieces(0), offered(false), warnedAt(0) {}
	};
	typedef std::pair<DWORD, DWORD> TPlayerBotDealKey; // (bot pid, person pid)
	std::map<TPlayerBotDealKey, TPlayerBotDeal> s_mapPlayerBotDeals;

	// ------------------------------------------------------------ pricing

	// The market's price of one piece: what was paid lately, the cheapest
	// counter, else what a keeper would ask for it.
	long long GetPlayerBotDealFairPrice(DWORD vnum)
	{
		size_t samples = 0;
		long long unit = GetPlayerBotSaleUnitPrice(vnum, 0, get_dword_time(), &samples);
		if (unit > 0)
			return unit;
		TPlayerBotStall stall;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER keeper = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!keeper || !keeper->GetMyShop() || !GetPlayerBotStall(it->first, keeper, stall))
				continue;
			for (size_t i = 0; i < stall.lines.size(); ++i)
			{
				if (stall.lines[i].vnum != vnum || stall.lines[i].price <= 0)
					continue;
				const long long per = stall.lines[i].price / (stall.lines[i].count ? stall.lines[i].count : 1);
				if (unit == 0 || per < unit)
					unit = per;
			}
		}
		if (unit > 0)
			return unit;
		LPITEM probe = ITEM_MANAGER::instance().CreateItem(vnum, 1, 0, false);
		if (!probe)
			return 0;
		unit = (long long)GetPlayerBotShopAskingPrice(probe);
		M2_DESTROY_ITEM(probe);
		return unit;
	}

	// The item a whisper names: the bot's bag, its counter, what it is short
	// of, then the whole item table - the exact name first, else the
	// shortest that matches (the base of a weapon rather than its +9).
	DWORD FindPlayerBotDealVnum(LPCHARACTER bot, const std::string& folded)
	{
		if (folded.empty())
			return 0;
		std::vector<std::string> candidates;
		playerbot_conv::ExpandItemQuery(folded, candidates);
		if (bot->IsItemLoaded())
		{
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			{
				LPITEM item = bot->GetInventoryItem(cell);
				if (item && item->GetProto() &&
						playerbot_conv::ItemNameMatchesAny(playerbot_conv::FoldName(item->GetProto()->szLocaleName), candidates))
					return item->GetVnum();
			}
		}
		std::set<DWORD> wanted;
		CollectPlayerBotWantedMaterials(bot, wanted);
		for (std::set<DWORD>::const_iterator it = wanted.begin(); it != wanted.end(); ++it)
		{
			const TItemTable* proto = ITEM_MANAGER::instance().GetTable(*it);
			if (proto && playerbot_conv::ItemNameMatchesAny(playerbot_conv::FoldName(proto->szLocaleName), candidates))
				return *it;
		}
		DWORD best = 0;
		size_t bestLen = 0;
		const std::vector<TItemTable>& protos = ITEM_MANAGER::instance().GetTable();
		for (size_t i = 0; i < protos.size(); ++i)
		{
			const TItemTable& t = protos[i];
			if (t.bType == ITEM_NONE || !*t.szLocaleName)
				continue;
			const std::string name = playerbot_conv::FoldName(t.szLocaleName);
			if (name == folded)
				return t.dwVnum;
			if (!playerbot_conv::ItemNameMatchesAny(name, candidates))
				continue;
			if (best == 0 || name.size() < bestLen)
			{
				best = t.dwVnum;
				bestLen = name.size();
			}
		}
		return best;
	}

	// The bot's own open "K>" post of this item, if any.
	const TPlayerBotPublicLine* FindPlayerBotOpenBuyPost(DWORD botPID, DWORD vnum)
	{
		std::map<DWORD, std::deque<TPlayerBotPublicLine> >::const_iterator it = s_mapPlayerBotPublicLines.find(botPID);
		if (it == s_mapPlayerBotPublicLines.end())
			return NULL;
		const DWORD now = get_dword_time();
		for (size_t i = 0; i < it->second.size(); ++i)
		{
			const TPlayerBotPublicLine& l = it->second[i];
			if (l.vnum == vnum && l.kind == playerbot_conv::PL_BUY && l.open && now - l.at < PLAYERBOT_PUBLIC_LINE_TTL_MS)
				return &l;
		}
		return NULL;
	}

	bool IsPlayerBotDealSellable(LPITEM item)
	{
		return item && item->GetProto() && !item->IsEquipped() && !item->IsExchanging() && !item->isLocked() &&
				!IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_GIVE) && !IS_SET(item->GetAntiFlag(), ITEM_ANTIFLAG_MYSHOP);
	}

	bool QuotePlayerBotDealItem(LPCHARACTER bot, const std::string& query, DWORD vnumHint,
			playerbot_conv::TDealQuote& out)
	{
		out = playerbot_conv::TDealQuote();
		if (!bot)
			return false;
		const DWORD vnum = vnumHint ? vnumHint : FindPlayerBotDealVnum(bot, playerbot_conv::FoldName(query.c_str()));
		const TItemTable* proto = vnum ? ITEM_MANAGER::instance().GetTable(vnum) : NULL;
		if (!proto)
			return false;
		TPlayerBotAIStateMap::const_iterator st = s_mapPlayerBotAIStates.find(bot->GetPlayerID());
		out.found = true;
		out.vnum = vnum;
		out.name = proto->szLocaleName;
		out.stackable = IS_SET(proto->dwFlags, ITEM_FLAG_STACKABLE);
		out.fair = GetPlayerBotDealFairPrice(vnum);
		out.botGold = (long long)bot->GetGold();

		// Would it buy it, and at what most.
		std::set<DWORD> wanted;
		CollectPlayerBotWantedMaterials(bot, wanted);
		const TPlayerBotPublicLine* post = FindPlayerBotOpenBuyPost(bot->GetPlayerID(), vnum);
		if (post)
		{
			out.botWants = true;
			out.wantCount = post->count > 0 ? post->count : (out.stackable ? 10 : 1);
			out.maxBuyUnit = std::max<long long>(post->unit, out.fair) * 110 / 100;
		}
		else if (wanted.count(vnum) || (GetPlayerBotRefineMaterialVnums().count(vnum) && PlayerBotNeedsRefineMaterial(bot, vnum)))
		{
			out.botWants = out.fair > 0;
			out.wantCount = out.stackable ? 10 : 1;
			out.maxBuyUnit = out.fair * 105 / 100;
		}
		else
		{
			std::map<DWORD, TPlayerBotWeaponGoal>::const_iterator goal = s_mapPlayerBotWeaponGoals.find(bot->GetPlayerID());
			if (goal != s_mapPlayerBotWeaponGoals.end() && goal->second.family &&
					proto->bType == ITEM_WEAPON && vnum - (vnum % 10) == goal->second.family->dwBaseVnum)
			{
				const long long goalPrice = (long long)GetPlayerBotWeaponGoalPrice(goal->second.family);
				out.botWants = goalPrice > 0;
				out.wantCount = 1;
				out.maxBuyUnit = std::max(goalPrice, out.fair) * 110 / 100;
			}
			else if (st != s_mapPlayerBotAIStates.end() && MapPlayerBotConvStyle(st->second) == playerbot_conv::S_MERCHANT &&
					out.fair > 0)
			{
				// A merchant buys anything worth something, for its counter.
				out.botWants = true;
				out.wantCount = out.stackable ? 20 : 1;
				out.maxBuyUnit = out.fair * 70 / 100;
			}
		}

		// Would it sell it, and at what least: its bag, never what it wears,
		// what it is short of, or what its counter holds.
		if (!wanted.count(vnum) && out.fair > 0 && bot->IsItemLoaded())
		{
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			{
				LPITEM item = bot->GetInventoryItem(cell);
				if (item && item->GetVnum() == vnum && item->GetCell() == cell && IsPlayerBotDealSellable(item))
					out.botHas += (int)item->GetCount();
			}
			out.minSellUnit = out.fair * 85 / 100;
			out.sellUnit = out.fair * 110 / 100;
		}
		TPlayerBotStall stall;
		if (GetPlayerBotStall(bot->GetPlayerID(), bot, stall))
		{
			for (size_t i = 0; i < stall.lines.size(); ++i)
			{
				if (stall.lines[i].vnum != vnum)
					continue;
				out.onStall = true;
				out.stallUnit = stall.lines[i].price / (stall.lines[i].count ? stall.lines[i].count : 1);
				out.stallWhere = GetPlayerBotTownName(stall.mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN
						? stall.mapIndex / 10000 : stall.mapIndex);
				break;
			}
		}
		return true;
	}

	// --------------------------------------------------------- the meeting

	int RegisterPlayerBotDeal(LPCHARACTER bot, DWORD personPID, LPCHARACTER person, BYTE side, DWORD vnum, int count,
			long long unit)
	{
		using namespace playerbot_conv;
		if (!bot || !personPID || count <= 0 || unit <= 0)
			return DEAL_MEET_FAILED;
		if (side == DEAL_BOT_BUYS && (long long)bot->GetGold() < unit * count)
			return DEAL_MEET_FAILED;
		const DWORD now = get_dword_time();
		TPlayerBotDeal& d = s_mapPlayerBotDeals[std::make_pair(bot->GetPlayerID(), personPID)];
		d = TPlayerBotDeal();
		d.side = side;
		d.vnum = vnum;
		d.count = count;
		d.unit = unit;
		d.at = now;
		sys_log(0, "PLAYERBOT_DEAL: agreed pid=%u name=%s person_pid=%u side=%s vnum=%u count=%d unit=%lld",
				bot->GetPlayerID(), bot->GetName(), personPID, side == DEAL_BOT_BUYS ? "buys" : "sells", vnum, count, unit);
		// Another core holds the person: they have to come over.
		if (!person || person->GetMapIndex() != bot->GetMapIndex())
			return DEAL_MEET_COME_TO_ME;
		if (DISTANCE_APPROX(person->GetX() - bot->GetX(), person->GetY() - bot->GetY()) <= PLAYERBOT_DEAL_NEAR)
			return DEAL_MEET_NEAR;
		const int code = StartPlayerBotSummon(bot, person, now);
		return code == SUMMON_START_OK || code == SUMMON_START_RENEWED ? DEAL_MEET_COMING : DEAL_MEET_COME_TO_ME;
	}

	void EndPlayerBotDeal(LPCHARACTER bot, DWORD personPID, unsigned char state, const char* why)
	{
		std::map<TPlayerBotDealKey, TPlayerBotDeal>::iterator it =
				s_mapPlayerBotDeals.find(std::make_pair(bot->GetPlayerID(), personPID));
		if (it != s_mapPlayerBotDeals.end())
		{
			sys_log(0, "PLAYERBOT_DEAL: %s pid=%u name=%s person_pid=%u vnum=%u count=%d unit=%lld", why,
					bot->GetPlayerID(), bot->GetName(), personPID, it->second.vnum, it->second.count, it->second.unit);
			if (state == playerbot_conv::DEAL_DONE)
				ClosePlayerBotPublicPost(bot->GetPlayerID(), it->second.vnum);
			s_mapPlayerBotDeals.erase(it);
		}
		if (playerbot_conv::TConvPair* pair = s_PlayerBotConvEngine.FindPair(personPID, bot->GetPlayerID()))
			pair->mem.deal.state = state;
	}

	// --------------------------------------------------------- the window

	void SayPlayerBotDealLine(LPCHARACTER bot, LPCHARACTER person, const char* text)
	{
		playerbot_conv::TBotSnapshot snap;
		if (!s_PlayerBotConvHost.BuildSnapshot(person->GetPlayerID(), bot->GetPlayerID(), snap))
		{
			SendPlayerBotWhisper(bot, person, text);
			return;
		}
		s_PlayerBotConvEngine.QueueBotLine(s_PlayerBotConvHost, person->GetPlayerID(), bot->GetPlayerID(), text,
				std::string(), playerbot_conv::I_DEAL, snap, get_dword_time(), 200);
		EnsurePlayerBotConvTimer();
	}

	// The bot's pieces of the deal into its side of the window, a stack split
	// to the count when it has to be. False when it has not got them.
	bool OfferPlayerBotDealPieces(LPCHARACTER ch, CExchange* exchange, DWORD vnum, int count)
	{
		std::vector<LPITEM> chosen;
		int pieces = 0;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS && pieces < count; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetVnum() != vnum || item->GetCell() != cell || !IsPlayerBotDealSellable(item))
				continue;
			const int left = count - pieces;
			if ((int)item->GetCount() > left)
			{
				// Split: the rest stays, the deal's part goes to a cell of its own.
				LPITEM part = ITEM_MANAGER::instance().CreateItem(vnum, left, 0, false);
				if (!part)
					return false;
				const int free = ch->GetEmptyInventory(part->GetSize());
				if (free < 0)
				{
					M2_DESTROY_ITEM(part);
					return false;
				}
				item->SetCount(item->GetCount() - left);
				part->AddToCharacter(ch, TItemPos(INVENTORY, (WORD)free));
				chosen.push_back(part);
				pieces += left;
				break;
			}
			chosen.push_back(item);
			pieces += (int)item->GetCount();
		}
		if (pieces != count)
			return false;
		BYTE display = 0;
		for (size_t i = 0; i < chosen.size(); ++i)
		{
			bool added = false;
			for (; display < EXCHANGE_ITEM_MAX_NUM && !added; ++display)
				added = exchange->AddItem(TItemPos(INVENTORY, chosen[i]->GetCell()), display);
			if (!added)
				return false;
		}
		return true;
	}

	// true while a deal holds the bot in an exchange (or it just opened one).
	bool HandlePlayerBotDealTrade(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		using namespace playerbot_conv;
		if (!ch || s_mapPlayerBotDeals.empty())
			return false;
		const DWORD pid = ch->GetPlayerID();
		CExchange* exchange = ch->GetExchange();
		if (!exchange)
		{
			// The bot's deals: the stale ones go; a person standing near gets
			// the window opened.
			std::map<TPlayerBotDealKey, TPlayerBotDeal>::iterator it = s_mapPlayerBotDeals.lower_bound(std::make_pair(pid, (DWORD)0));
			while (it != s_mapPlayerBotDeals.end() && it->first.first == pid)
			{
				TPlayerBotDeal& d = it->second;
				const DWORD personPID = it->first.second;
				if (dwNow - d.at > PLAYERBOT_DEAL_TTL_MS)
				{
					++it;
					EndPlayerBotDeal(ch, personPID, DEAL_FAILED, "expired");
					return false;
				}
				LPCHARACTER person = CHARACTER_MANAGER::instance().FindByPID(personPID);
				if (person && person->GetDesc() && person->GetMapIndex() == ch->GetMapIndex() && !person->GetExchange() &&
						!person->IsDead() && dwNow >= d.nextOpenAt &&
						DISTANCE_APPROX(person->GetX() - ch->GetX(), person->GetY() - ch->GetY()) <= PLAYERBOT_DEAL_NEAR)
				{
					d.nextOpenAt = dwNow + PLAYERBOT_DEAL_OPEN_RETRY_MS;
					if (ch->IsStateMove())
						ch->Stop();
					if (ch->ExchangeStart(person))
					{
						sys_log(0, "PLAYERBOT_DEAL: window opened pid=%u name=%s person=%s", pid, ch->GetName(), person->GetName());
						return true;
					}
				}
				++it;
			}
			return false;
		}
		CExchange* other = exchange->GetCompany();
		LPCHARACTER partner = other ? other->GetOwner() : NULL;
		if (!partner)
			return false;
		std::map<TPlayerBotDealKey, TPlayerBotDeal>::iterator found =
				s_mapPlayerBotDeals.find(std::make_pair(pid, partner->GetPlayerID()));
		if (found == s_mapPlayerBotDeals.end())
			return false; // not a deal: the gift trade's
		TPlayerBotDeal& d = found->second;
		const TItemTable* proto = ITEM_MANAGER::instance().GetTable(d.vnum);
		const char* name = proto ? proto->szLocaleName : "to";

		// Standing still at the window, as the gift trade does.
		ch->SetVictim(NULL);
		if (ch->IsStateMove())
			ch->Stop();
		SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
		state.dwLastMeaningfulActivityTime = dwNow;
		if (d.windowSince == 0)
			d.windowSince = dwNow;
		if (dwNow - d.windowSince > PLAYERBOT_DEAL_WINDOW_MAX_MS)
		{
			exchange->Cancel();
			d.windowSince = 0;
			d.paid = false;
			d.offered = false;
			SayPlayerBotDealLine(ch, partner, "Za dlugo to trwa, zamykam. Daj wymiane jeszcze raz jak bedziesz gotowy.");
			return true;
		}

		std::vector<LPITEM> offer;
		CollectPlayerBotGiftOffer(partner, offer);
		if (d.side == DEAL_BOT_BUYS)
		{
			int pieces = 0, others = 0;
			for (size_t i = 0; i < offer.size(); ++i)
			{
				if (offer[i]->GetVnum() == d.vnum)
					pieces += (int)offer[i]->GetCount();
				else
					++others;
			}
			char line[CHAT_MAX_LEN + 1];
			if ((others > 0 || pieces > d.count) && dwNow - d.warnedAt > 8000)
			{
				d.warnedAt = dwNow;
				if (others > 0)
					snprintf(line, sizeof(line), "Daj tylko %s, reszte zabierz.", name);
				else
					snprintf(line, sizeof(line), "Mialo byc %d szt, zabierz reszte.", d.count);
				SayPlayerBotDealLine(ch, partner, line);
			}
			if (others > 0 || pieces == 0 || pieces > d.count)
				return true;
			if (!d.paid)
			{
				const long long pay = d.unit * pieces;
				if ((long long)ch->GetGold() < pay || !exchange->AddGold(pay))
				{
					exchange->Cancel();
					SayPlayerBotDealLine(ch, partner, "Sorki, nie mam teraz tyle yang.");
					EndPlayerBotDeal(ch, partner->GetPlayerID(), DEAL_FAILED, "no_gold");
					return true;
				}
				d.paid = true;
				d.paidPieces = pieces;
				d.decideAt = 0;
				return true;
			}
			if (pieces != d.paidPieces)
			{
				exchange->Cancel();
				d.paid = false;
				d.windowSince = 0;
				SayPlayerBotDealLine(ch, partner, "Zmieniles ilosc po tym jak dalem yang. Daj wymiane jeszcze raz.");
				return true;
			}
		}
		else
		{
			if (!d.offered)
			{
				if (!OfferPlayerBotDealPieces(ch, exchange, d.vnum, d.count))
				{
					exchange->Cancel();
					SayPlayerBotDealLine(ch, partner, "Ups, juz tego nie mam. Sorki.");
					EndPlayerBotDeal(ch, partner->GetPlayerID(), DEAL_FAILED, "no_pieces");
					return true;
				}
				d.offered = true;
				d.decideAt = 0;
				return true;
			}
			const long long due = d.unit * d.count;
			if (other->GetAcceptStatus() && other->Mt2009PlusGetGold() < due && dwNow - d.warnedAt > 8000)
			{
				d.warnedAt = dwNow;
				char line[CHAT_MAX_LEN + 1];
				snprintf(line, sizeof(line), "Mialo byc %s yang, doloz brakujace.", playerbot_conv::FormatYang(due).c_str());
				SayPlayerBotDealLine(ch, partner, line);
			}
			if (other->Mt2009PlusGetGold() < due || !offer.empty())
			{
				// Yang only from the person's side: an item in it is not the deal.
				if (!offer.empty() && dwNow - d.warnedAt > 8000)
				{
					d.warnedAt = dwNow;
					SayPlayerBotDealLine(ch, partner, "Daj tylko yang, przedmioty zabierz.");
				}
				return true;
			}
		}

		// The person's accept first, then a glance, then the bot's.
		if (!other->GetAcceptStatus() || exchange->GetAcceptStatus())
		{
			d.decideAt = 0;
			return true;
		}
		if (d.decideAt == 0)
		{
			d.decideAt = dwNow + number(PLAYERBOT_DEAL_GLANCE_MIN_MS, PLAYERBOT_DEAL_GLANCE_MAX_MS);
			return true;
		}
		if (dwNow < d.decideAt)
			return true;
		const long long goldBefore = (long long)ch->GetGold();
		const DWORD personPID = partner->GetPlayerID();
		exchange->Accept(true);
		if (ch->GetExchange())
			return true; // not done yet
		const long long goldNow = (long long)ch->GetGold();
		const bool done = d.side == DEAL_BOT_BUYS ? goldNow < goldBefore : goldNow > goldBefore;
		static const char* const kThanks[] = { "Dzieki, dobry handel!", "Dzieki, polecam sie na przyszlosc :)", "Gitara, dzieki!",
			"Dzieki, milo sie handlowalo." };
		if (done)
		{
			SayPlayerBotDealLine(ch, partner, kThanks[number(0, 3)]);
			state.dwNextEquipmentCheckTime = 0;
		}
		EndPlayerBotDeal(ch, personPID, done ? DEAL_DONE : DEAL_FAILED, done ? "done" : "window_closed");
		return true;
	}
}

#endif
