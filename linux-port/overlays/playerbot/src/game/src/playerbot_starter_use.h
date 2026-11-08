#ifndef __INC_METIN2_PLAYERBOT_STARTER_USE_H__
#define __INC_METIN2_PLAYERBOT_STARTER_USE_H__

// MT2009_PLUS_BOT_STARTER_USE_V1 - everything out of the apprentice chests put to its use.
//
// The owner, 8 November 2026: "Naucz boty korzystac ze wszystkich rzeczy ze szkatul ucznia. Bo teraz chyba nie
// ogarniaja, na przyklad Zwojow Blogoslawienstwa, ktore wylatuja ze szkatuly ucznia, i je sprzedaja u handlarki."
//
// The chain (special_item_group.starter.txt: Skrzynia Ucznia I 50187/50212/50213 at level 1, II-III, Eksperta I-III,
// Mistrza I-III and Arcymistrza 50188-50196 every ten levels to 90) hands out some fifty kinds. The first night of the
// test world's clean install (7-8 November, 2 000 bots from level 1; log.log, player.item) showed what the bots made
// of them. Most were already right - the potions, the speed / attack / exp / drop boosters (UsePlayerBotBoosters), the
// auto potions (switched on, sold only once empty), the green and the (n) change / add stones (playerbot_bonus.h),
// the marble, the exorcism scroll and the hermit's advice (the book pass), the cape (MT2009_PLUS_BOT_CAPE_V2), the
// leader's book and the mask (unique slots), the Appaloosa (the mount slot), the weapon (worn, then outgrown and
// sold), the Dragon God scroll (the refine ladder from +7), the Seeker's elixir (the biologist), the dried head (the
// Catacomb) and the chests themselves (ManagePlayerBotProgressionChests, at each chest's level). Four were not:
//
//  - Zwoj Blogoslawienstwa (76016, five in each of Skrzynia Eksperta I and II): the bound Blessing Scroll, USE_TUNING
//    value0 0 like 25040 - but neither IsPlayerBotRefineScroll nor IsPlayerBotSafeRefineScroll knew the vnum, so the
//    scroll keep did not count it and the junk rule sold it: 14 387 at the General Store in the first ten hours.
//    Both lists know it now (playerbot_types.h): kept, counted in GetPlayerBotRefineScrollKeep and the scroll rule's
//    count, spent by FindPlayerBotRefineScrollCell (which on mt2009 already took any USE_TUNING by its values).
//    It carries ANTI_MYSHOP and ANTI_GIVE, so no counter takes it - the bot's own anvil is where it goes.
//  - Wino z Kwiatu Brzoskwini (76000, ten in Skrzynia Mistrza I): a red potion (USE_POTION_NODELAY, 500 HP) no potion
//    list knew - every one went to the merchant. UseHealthPotion drinks it after the ordinary reds.
//  - Przekaska Appaloosa (38103, Skrzynia Ucznia III): seven more days for the Appaloosa (starter_chest.quest's
//    38103.use). Sold by 2 441 of the 2 474 bots that got one. Fed to the Appaloosa now once it has less than
//    m2_bot_starter_snack_lead_h hours (48 by default) left; kept while the bot has an Appaloosa, a leftover after.
//  - Wykrywacz Kamieni Metin (76006, Skrzynia Ucznia III): a client-side compass to a Metin; a bot knows where the
//    stones are without one. Kept for good as "a player thing for the counter" - but it carries ANTI_MYSHOP, so it
//    sat in 2 474 bags. A leftover now: the merchant's.
//
// The leftovers that stay the merchant's, as before: Bilet Podrozniczy (56001, its trip is a select() a bot cannot
// answer), Zwoj Powrotu Statusu (76001, a stat reset), Przepustka (76019 - the dungeon's quest takes 71095/71130 only),
// Krwisty Kamien (76010, nothing here reads it), the outgrown starter weapon, the empty auto potions. Pierscien
// Teleportacji (70058, a quest dialog; ANTI_SELL) stays in the bag as before (the 70038-70060 keep).
//
// Switches (event flags, read every five seconds): m2_bot_starter_use_off - everything below and the two vnums of
// playerbot_types.h; m2_bot_starter_scroll_off, m2_bot_starter_wine_off, m2_bot_starter_snack_off,
// m2_bot_starter_leftover_off, m2_bot_starter_census_off each one alone. m2_bot_starter_snack_lead_h: the snack's
// lead in hours (0 = 48; 168 feeds at once, for a test).
//
// Logs: PLAYERBOT_STARTER: snack fed / snack refused (throttled), PLAYERBOT_STARTER: leftover sold (throttled), and
// PLAYERBOT_STARTER_CENSUS every ten minutes - the chests opened by kind, then per item vnum:recv/used/sold/bag/worn
// (recv: the chests' lines since the core started; used: the bots' passes that spend it - potions, boosters, auto
// potions, bonus stones, refine scrolls, the snack - which count every unit of the vnum, bought or dropped as well;
// sold: the General Store; bag/worn: the online bots' bags and equipment now).
//
// An implementation fragment in the sense playerbot_types.h describes: include it exactly once, after
// playerbot_consumables.h and before playerbot_activities.h and playerbot_economy.h.

namespace
{
	const DWORD PLAYERBOT_STARTER_SNACK_VNUM = 38103;	// Przekaska Appaloosa
	const DWORD PLAYERBOT_STARTER_APPALOOSA_VNUM = 56000;	// Appaloosa (pieczec, 7 dni - LIMIT_REAL_TIME, socket 0 the end)
	const DWORD PLAYERBOT_STARTER_DETECTOR_VNUM = 76006;	// Wykrywacz Kamieni Metin (bound)
	const int PLAYERBOT_STARTER_SNACK_LEAD_HOURS = 48;
	const DWORD PLAYERBOT_STARTER_PASS_MS = 60000;
	const DWORD PLAYERBOT_STARTER_SNACK_REFUSED_MS = 6 * 60 * 60 * 1000;
	const DWORD PLAYERBOT_STARTER_CENSUS_MS = 10 * 60 * 1000;
	const size_t PLAYERBOT_STARTER_CENSUS_PER_LINE = 12;

	// The chests of the chain and every item vnum their groups hand out (special_item_group.starter.txt, generated by
	// tools/skrzynie_ucznia/gen_skrzynie_ucznia.py - a vnum added there wants a line here for the census only).
	const DWORD PLAYERBOT_STARTER_CHEST_VNUMS[] = { 50187, 50212, 50213, 50188, 50189, 50190, 50191, 50192, 50193,
			50194, 50195, 50196 };
	const DWORD PLAYERBOT_STARTER_ITEM_VNUMS[] = {
		27051, 27052, 27053, 27054, 71155, 10, 1000, 7000,				// Skrzynia Ucznia I
		76012, 71014, 76021, 71153, 56000, 56001,					// Skrzynia Ucznia II
		76004, 76006, 76007, 71033, 38103,						// Skrzynia Ucznia III
		76011, 76016,									// Skrzynia Eksperta I
		76018, 76026, 76023, 76024,							// Skrzynia Eksperta II
		70058, 76003, 76019, 76036, 76035, 76037, 76038,				// Skrzynia Eksperta III
		76000, 76009,									// Skrzynia Mistrza I
		76001, 76013, 76014, 76034,							// Skrzynia Mistrza II
		76005, 76020, 51639,								// Skrzynia Mistrza III
		76002, 76010, 76015, 76022,							// Skrzynia Arcymistrza
	};

	struct TPlayerBotStarterStat
	{
		unsigned int recv, used, sold;
		TPlayerBotStarterStat() : recv(0), used(0), sold(0) {}
	};
	std::map<DWORD, TPlayerBotStarterStat> s_mapPlayerBotStarterStats;
	std::map<DWORD, unsigned int> s_mapPlayerBotStarterChestsOpened;
	std::map<DWORD, DWORD> s_mapPlayerBotStarterNextPass;
	std::map<DWORD, DWORD> s_mapPlayerBotStarterSnackRefused;
	unsigned int s_uPlayerBotStarterSnackFed = 0, s_uPlayerBotStarterSnackRefused = 0, s_uPlayerBotStarterLeftoverSold = 0;
	DWORD s_dwPlayerBotStarterNextCensus = 0;

	bool IsPlayerBotStarterUseOn(int iSwitch)
	{
		static const char* const s_aszFlags[PLAYERBOT_STARTER_SW_COUNT] = {
			"m2_bot_starter_scroll_off", "m2_bot_starter_wine_off", "m2_bot_starter_snack_off",
			"m2_bot_starter_leftover_off", "m2_bot_starter_census_off" };
		static bool s_abOn[PLAYERBOT_STARTER_SW_COUNT] = { true, true, true, true, true };
		static DWORD s_dwAt = 0;
		if (iSwitch < 0 || iSwitch >= PLAYERBOT_STARTER_SW_COUNT)
			return false;
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 5000)
		{
			s_dwAt = now ? now : 1;
			const bool all = quest::CQuestManager::instance().GetEventFlag("m2_bot_starter_use_off") == 0;
			for (int i = 0; i < PLAYERBOT_STARTER_SW_COUNT; ++i)
				s_abOn[i] = all && quest::CQuestManager::instance().GetEventFlag(s_aszFlags[i]) == 0;
		}
		return s_abOn[iSwitch];
	}

	bool IsPlayerBotStarterItemVnum(DWORD dwVnum)
	{
		for (size_t i = 0; i < sizeof(PLAYERBOT_STARTER_ITEM_VNUMS) / sizeof(PLAYERBOT_STARTER_ITEM_VNUMS[0]); ++i)
			if (PLAYERBOT_STARTER_ITEM_VNUMS[i] == dwVnum)
				return true;
		return false;
	}

	bool IsPlayerBotStarterChestVnum(DWORD dwVnum)
	{
		for (size_t i = 0; i < sizeof(PLAYERBOT_STARTER_CHEST_VNUMS) / sizeof(PLAYERBOT_STARTER_CHEST_VNUMS[0]); ++i)
			if (PLAYERBOT_STARTER_CHEST_VNUMS[i] == dwVnum)
				return true;
		return false;
	}

	// A chest of the chain opened by a bot: its group's lines are what it received (a PCT group: every line).
	void NotePlayerBotStarterChestOpened(DWORD dwChestVnum)
	{
		if (!IsPlayerBotStarterChestVnum(dwChestVnum))
			return;
		++s_mapPlayerBotStarterChestsOpened[dwChestVnum];
#if defined(PLAYERBOT_ENGINE_MT2009)
		const CSpecialItemGroup* pGroup = ITEM_MANAGER::instance().GetSpecialItemGroup(dwChestVnum);
		if (!pGroup)
			return;
		const std::vector<CSpecialItemGroup::CSpecialItemInfo> lines = pGroup->GetItems();
		for (size_t i = 0; i < lines.size(); ++i)
			if (lines[i].vnum >= PLAYERBOT_GROUP_FIRST_ITEM_VNUM && !IsPlayerBotStarterChestVnum(lines[i].vnum))
				s_mapPlayerBotStarterStats[lines[i].vnum].recv += (unsigned int)std::max(1, lines[i].count);
#endif
	}

	void NotePlayerBotStarterItemUsed(DWORD dwVnum, int iUnits)
	{
		if (iUnits > 0 && IsPlayerBotStarterItemVnum(dwVnum))
			s_mapPlayerBotStarterStats[dwVnum].used += (unsigned int)iUnits;
	}

	// The two true leftovers this change gives the merchant (GetPlayerBotStarterJunkVerdict).
	bool IsPlayerBotStarterNewLeftover(LPCHARACTER ch, LPITEM item);

	// Called by the General Store's sale just before the item goes.
	void NotePlayerBotStarterItemSold(LPCHARACTER ch, LPITEM item)
	{
		if (!item || !IsPlayerBotStarterItemVnum(item->GetVnum()))
			return;
		const unsigned int units = (unsigned int)std::max<int>(1, item->GetCount());
		s_mapPlayerBotStarterStats[item->GetVnum()].sold += units;
		if (ch && IsPlayerBotStarterNewLeftover(ch, item))
		{
			s_uPlayerBotStarterLeftoverSold += units;
			PlayerBotLogThrottled("starter_leftover_sold", get_dword_time(),
					"PLAYERBOT_STARTER: leftover sold pid=%u name=%s lv=%d vnum=%u units=%u total=%u",
					ch->GetPlayerID(), ch->GetName(), (int)ch->GetLevel(), item->GetVnum(), units,
					s_uPlayerBotStarterLeftoverSold);
		}
	}

	// The Appaloosa this bot rides (the mount slot, or any slot) or keeps in its bag; NULL none.
	LPITEM FindPlayerBotStarterAppaloosa(LPCHARACTER ch)
	{
		if (!ch || !ch->IsItemLoaded())
			return NULL;
		for (int wear = 0; wear < WEAR_MAX_NUM; ++wear)
		{
			LPITEM worn = ch->GetWear(wear);
			if (worn && worn->GetVnum() == PLAYERBOT_STARTER_APPALOOSA_VNUM)
				return worn;
		}
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM held = ch->GetInventoryItem(cell);
			if (held && held->GetCell() == cell && held->GetVnum() == PLAYERBOT_STARTER_APPALOOSA_VNUM)
				return held;
		}
		return NULL;
	}

	bool IsPlayerBotStarterNewLeftover(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item || !IsPlayerBotStarterUseOn(PLAYERBOT_STARTER_SW_LEFTOVER))
			return false;
		const DWORD vnum = item->GetVnum();
		if (vnum == PLAYERBOT_STARTER_DETECTOR_VNUM)
			return true;
		// The snack with no Appaloosa left to feed (it ran out, or was never put on).
		return vnum == PLAYERBOT_STARTER_SNACK_VNUM && IsPlayerBotStarterUseOn(PLAYERBOT_STARTER_SW_SNACK) &&
				FindPlayerBotStarterAppaloosa(ch) == NULL;
	}

	// IsPlayerBotJunkItem's answer for the chests' items this change places: 0 keep, 1 the merchant's, -1 not ours
	// (the rules below it answer, as before). Asked after the operator's own word on the item and the companions'.
	int GetPlayerBotStarterJunkVerdict(LPCHARACTER ch, LPITEM item)
	{
		if (!ch || !item)
			return -1;
		const DWORD vnum = item->GetVnum();
		switch (vnum)
		{
			case PLAYERBOT_STARTER_BLESSING_SCROLL_VNUM:
				return IsPlayerBotStarterUseOn(PLAYERBOT_STARTER_SW_SCROLL) ? 0 : -1;
			case PLAYERBOT_STARTER_WINE_VNUM:
				return IsPlayerBotStarterUseOn(PLAYERBOT_STARTER_SW_WINE) ? 0 : -1;
			case PLAYERBOT_STARTER_SNACK_VNUM:
				if (!IsPlayerBotStarterUseOn(PLAYERBOT_STARTER_SW_SNACK))
					return -1;
				if (FindPlayerBotStarterAppaloosa(ch) != NULL)
					return 0;
				return IsPlayerBotStarterUseOn(PLAYERBOT_STARTER_SW_LEFTOVER) ? 1 : -1;
			case PLAYERBOT_STARTER_DETECTOR_VNUM:
				return IsPlayerBotStarterUseOn(PLAYERBOT_STARTER_SW_LEFTOVER) ? 1 : -1;
			default:
				return -1;
		}
	}

	// The census line(s): the chests opened, then vnum:recv/used/sold/bag/worn for every item of the chain.
	void RunPlayerBotStarterCensus(DWORD dwNow)
	{
		std::map<DWORD, std::pair<unsigned int, unsigned int> > held;	// vnum -> (bag units, worn pieces)
		int bots = 0;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch || !ch->IsItemLoaded())
				continue;
			++bots;
			for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				if (item && item->GetCell() == cell && IsPlayerBotStarterItemVnum(item->GetVnum()))
					held[item->GetVnum()].first += (unsigned int)std::max<int>(1, item->GetCount());
			}
			for (int wear = 0; wear < WEAR_MAX_NUM; ++wear)
			{
				LPITEM worn = ch->GetWear(wear);
				if (worn && IsPlayerBotStarterItemVnum(worn->GetVnum()))
					++held[worn->GetVnum()].second;
			}
		}
		std::string chests;
		char buf[96];
		for (size_t i = 0; i < sizeof(PLAYERBOT_STARTER_CHEST_VNUMS) / sizeof(PLAYERBOT_STARTER_CHEST_VNUMS[0]); ++i)
		{
			const std::map<DWORD, unsigned int>::const_iterator c =
					s_mapPlayerBotStarterChestsOpened.find(PLAYERBOT_STARTER_CHEST_VNUMS[i]);
			snprintf(buf, sizeof(buf), " %u:%u", PLAYERBOT_STARTER_CHEST_VNUMS[i],
					c != s_mapPlayerBotStarterChestsOpened.end() ? c->second : 0U);
			chests += buf;
		}
		sys_log(0, "PLAYERBOT_STARTER_CENSUS: bots=%d chests_opened%s snack_fed=%u snack_refused=%u leftover_sold=%u",
				bots, chests.c_str(), s_uPlayerBotStarterSnackFed, s_uPlayerBotStarterSnackRefused,
				s_uPlayerBotStarterLeftoverSold);
		const size_t total = sizeof(PLAYERBOT_STARTER_ITEM_VNUMS) / sizeof(PLAYERBOT_STARTER_ITEM_VNUMS[0]);
		for (size_t from = 0, part = 1; from < total; from += PLAYERBOT_STARTER_CENSUS_PER_LINE, ++part)
		{
			std::string line;
			for (size_t i = from; i < total && i < from + PLAYERBOT_STARTER_CENSUS_PER_LINE; ++i)
			{
				const DWORD vnum = PLAYERBOT_STARTER_ITEM_VNUMS[i];
				const TPlayerBotStarterStat& st = s_mapPlayerBotStarterStats[vnum];
				const std::pair<unsigned int, unsigned int>& h = held[vnum];
				snprintf(buf, sizeof(buf), " %u:%u/%u/%u/%u/%u", vnum, st.recv, st.used, st.sold, h.first, h.second);
				line += buf;
			}
			sys_log(0, "PLAYERBOT_STARTER_CENSUS: items part=%u (vnum:recv/used/sold/bag/worn)%s", (unsigned int)part,
					line.c_str());
		}
		(void)dwNow;
	}

	// The snack, once the Appaloosa it feeds has under the lead left: the quest's own 38103.use (starter_chest.quest)
	// finds the worn one or the first in the bag and adds seven days. A use the quest refused (an open quest window,
	// no Appaloosa where it looks) is not asked again for six hours.
	bool FeedPlayerBotStarterAppaloosa(LPCHARACTER ch, DWORD dwNow)
	{
		if (!IsPlayerBotStarterUseOn(PLAYERBOT_STARTER_SW_SNACK) ||
				ch->CountSpecifyItem(PLAYERBOT_STARTER_SNACK_VNUM) <= 0)
			return false;
		const std::map<DWORD, DWORD>::iterator refused = s_mapPlayerBotStarterSnackRefused.find(ch->GetPlayerID());
		if (refused != s_mapPlayerBotStarterSnackRefused.end())
		{
			if ((int)(dwNow - refused->second) < 0)
				return false;
			s_mapPlayerBotStarterSnackRefused.erase(refused);
		}
		LPITEM mount = FindPlayerBotStarterAppaloosa(ch);
		if (!mount)
			return false;
		int leadHours = (int)quest::CQuestManager::instance().GetEventFlag("m2_bot_starter_snack_lead_h");
		if (leadHours <= 0)
			leadHours = PLAYERBOT_STARTER_SNACK_LEAD_HOURS;
		const int now = get_global_time();
		const int end = (int)mount->GetSocket(0);
		if (end > now && end - now > leadHours * 3600)
			return false;
		if (ch->GetExchange() || ch->GetMyShop() || ch->GetShopOwner() || ch->IsOpenSafebox() || ch->IsCubeOpen() ||
				ch->IsWarping())
			return false;
		for (WORD cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM snack = ch->GetInventoryItem(cell);
			if (!snack || snack->GetCell() != cell || snack->GetVnum() != PLAYERBOT_STARTER_SNACK_VNUM ||
					snack->isLocked() || IsPlayerBotSidekickHeld(ch, snack))
				continue;
			const int before = (int)ch->CountSpecifyItem(PLAYERBOT_STARTER_SNACK_VNUM);
			ch->UseItem(TItemPos(INVENTORY, cell));
			LPITEM after = FindPlayerBotStarterAppaloosa(ch);
			const int newEnd = after ? (int)after->GetSocket(0) : 0;
			if ((int)ch->CountSpecifyItem(PLAYERBOT_STARTER_SNACK_VNUM) < before && newEnd > end)
			{
				++s_uPlayerBotStarterSnackFed;
				NotePlayerBotStarterItemUsed(PLAYERBOT_STARTER_SNACK_VNUM, 1);
				PlayerBotLogThrottled("starter_snack_fed", dwNow,
						"PLAYERBOT_STARTER: snack fed pid=%u name=%s lv=%d left_h=%d now_left_h=%d worn=%d total=%u",
						ch->GetPlayerID(), ch->GetName(), (int)ch->GetLevel(), (end - now) / 3600,
						(newEnd - now) / 3600, mount->IsEquipped() ? 1 : 0, s_uPlayerBotStarterSnackFed);
				return true;
			}
			++s_uPlayerBotStarterSnackRefused;
			s_mapPlayerBotStarterSnackRefused[ch->GetPlayerID()] = dwNow + PLAYERBOT_STARTER_SNACK_REFUSED_MS;
			PlayerBotLogThrottled("starter_snack_refused", dwNow,
					"PLAYERBOT_STARTER: snack refused pid=%u name=%s lv=%d left_h=%d worn=%d snacks=%d total=%u",
					ch->GetPlayerID(), ch->GetName(), (int)ch->GetLevel(), (end - now) / 3600,
					mount->IsEquipped() ? 1 : 0, (int)ch->CountSpecifyItem(PLAYERBOT_STARTER_SNACK_VNUM),
					s_uPlayerBotStarterSnackRefused);
			return false;
		}
		return false;
	}

	// The per-bot pass (once a minute a bot, out of a fight) and the census (the first bot past its ten minutes).
	// MT2009_PLUS_BOT_TELEPORT_RING_KEEP_V1 (the owner, 8 November 2026: chests of skill instructions bought ten in a row
	// bring a spam of Pierscienie Teleportacji - "jesli potrzebuja, to niech zostawia maksymalnie 4 sztuki"): the ring is
	// not consumed (the frontier recall, PLAYERBOT_TELEPORT_RING_VNUM, has its own 30-minute clock), so a bot keeps ONE
	// (m2_bot_teleport_ring_keep N, 1-4) and destroys the rest - the ring cannot be sold to a merchant (ANTI_SELL).
	// m2_bot_teleport_ring_keep_off 1: as before.
	unsigned int s_uPlayerBotTeleportRingsRemoved = 0;

	void TrimPlayerBotTeleportRings(LPCHARACTER ch, DWORD dwNow)
	{
		if (quest::CQuestManager::instance().GetEventFlag("m2_bot_teleport_ring_keep_off") == 1)
			return;
		int keep = (int)quest::CQuestManager::instance().GetEventFlag("m2_bot_teleport_ring_keep");
		keep = keep <= 0 ? 1 : MIN(keep, 4);
		int seen = 0, removed = 0;
		for (int cell = 0; cell < ch->GetInventoryMaxCount(); ++cell)
		{
			LPITEM ring = ch->GetInventoryItem(cell);
			if (!ring || ring->GetCell() != cell || ring->GetVnum() != PLAYERBOT_TELEPORT_RING_VNUM || ring->IsEquipped() ||
					ring->isLocked() || ring->IsExchanging())
				continue;
			if (++seen <= keep)
				continue;
			ITEM_MANAGER::instance().RemoveItem(ring, "PLAYERBOT_RING_SURPLUS");
			++removed;
		}
		if (removed > 0)
		{
			s_uPlayerBotTeleportRingsRemoved += removed;
			PlayerBotLogThrottled("starter_ring_trim", dwNow,
					"PLAYERBOT_STARTER: teleport rings removed pid=%u name=%s removed=%d kept=%d total=%u",
					ch->GetPlayerID(), ch->GetName(), removed, keep, s_uPlayerBotTeleportRingsRemoved);
		}
	}

	bool ManagePlayerBotStarterItems(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || ch->IsDead())
			return false;
		if (IsPlayerBotStarterUseOn(PLAYERBOT_STARTER_SW_CENSUS) &&
				(s_dwPlayerBotStarterNextCensus == 0 || (int)(dwNow - s_dwPlayerBotStarterNextCensus) >= 0))
		{
			// The first look only sets the clock: the counters start with the core.
			if (s_dwPlayerBotStarterNextCensus != 0)
				RunPlayerBotStarterCensus(dwNow);
			s_dwPlayerBotStarterNextCensus = dwNow + PLAYERBOT_STARTER_CENSUS_MS;
		}
		if (s_mapPlayerBotStarterNextPass.size() > 20000)
			s_mapPlayerBotStarterNextPass.clear();
		DWORD& next = s_mapPlayerBotStarterNextPass[ch->GetPlayerID()];
		if (next != 0 && (int)(dwNow - next) < 0)
			return false;
		next = dwNow + PLAYERBOT_STARTER_PASS_MS + (PlayerBotNavHash(ch->GetPlayerID()) % 15000U);
		if (state.bCurrentAction == BOT_ACTION_FIGHT || IsPlayerBotSidekickPID(ch->GetPlayerID()))
			return false;
		TrimPlayerBotTeleportRings(ch, dwNow);
		return FeedPlayerBotStarterAppaloosa(ch, dwNow);
	}
}

#endif
