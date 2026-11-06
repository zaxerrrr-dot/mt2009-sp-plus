#ifndef __INC_METIN2_PLAYERBOT_RANK_FRUIT_CRAFT_H__
#define __INC_METIN2_PLAYERBOT_RANK_FRUIT_CRAFT_H__

// MT2009_PLUS_RANK_FRUIT_CRAFT_V1 - the rank fruits crafted 7 -> 1 at Uriel (the owner, 6 November 2026, Yohara:
// "Dodaj mozliwosc wytwarzania u Uriela. 7 owocow klasy poprzedniej przerabiasz na owoc wyzej. Czyli 7 jablek na 1
// gruszke, szansa 95%, bez oplaty yang. Boty rowniez przerabiaja, mysle, ze to bedzie dobra opcja, aby wyczyscic
// jablka z rynku").
//
// The players' half: cube.owoce.txt (tools/owoce/gen_owoce.py) - Uriel (20011) 7 Jablko -> Gruszka, 7 Gruszka ->
// Winogrono, 7 Winogrono -> Arbuz, 7 Arbuz -> Ananas, 95%, 0 Yang; his crafting window opens by quest mikstury_okno
// ("Wytwarzanie owocow").
//
// The bots' half (here and playerbot_rank_fruit_market.h), the same recipe (PLAYERBOT_FRUIT_CRAFT_*,
// playerbot_rank_points.h) done the way the engine's Cube_make does it - the seven pieces go, the 95% roll, the
// higher piece on a success, CubeLog - as the belts at Mistrz (playerbot_belts.h; a bot has no hands for the window):
//   * what a bot crafts (GetPlayerBotFruitCraftCount): the pieces of a fruit above its own base keep (the rank goal's
//     need and the Jablka reserve, playerbot_rank_points.h). Its surplus only while the lower fruit is overstocked
//     (the market's clearing ask is on) or seven of it cost less than one of the higher (the bots' asks); and always
//     the pieces it holds for its own crafts (GetPlayerBotRankFruitCraftKeep: seven a higher piece it still eats);
//   * the walk: a bot near an Uriel (the same map, 250 m - the village and its square: a bot in town for its errands
//     or about to go out to hunt) with a craft walks to him - Potega madrosci's way (playerbot_potega.h), its own
//     staggered clock, never from a fight, a stall, a person's party, another errand, a few walkers on a core at once;
//   * the buying (playerbot_rank_fruit_market.h, GetPlayerBotRankFruitCraftBuyWant): an eater buys the fruit below
//     the one it eats when seven cost less than one at its ask, or when no counter holds the fruit it eats at all.
// Event flag m2_bot_fruit_craft_off 1: none of it (the keep for crafts too). Census every 10 minutes:
// "PLAYERBOT_RANK_FRUIT_CRAFT: census ..." (crafted / failed / apples_bought_for_craft / bought_for_craft_no_higher).

#include <unordered_map>
#include <vector>

namespace mt2009_fruitcraft
{
	const int MAX_WALKERS = 8;
	const int MAX_CRAFTS_A_VISIT = 40;
	const DWORD CHECK_MIN_MS = 90000;
	const DWORD CHECK_MAX_MS = 240000;
	const DWORD GIVE_UP_MS = 120000;
	const DWORD CENSUS_MS = 10 * 60 * 1000;

	struct TVisit
	{
		DWORD nextCheck;
		DWORD startedAt;
		DWORD actionAt;
		DWORD npcVid;
		bool walking;
		TVisit() : nextCheck(0), startedAt(0), actionAt(0), npcVid(0), walking(false) {}
	};

	std::unordered_map<DWORD, TVisit> s_visits;
	std::vector<std::pair<DWORD, DWORD> > s_walkers;	// (pid, start)

	unsigned long long s_crafted[mt2009_rankp::FRUIT_COUNT];	// by the result's index
	unsigned long long s_failed[mt2009_rankp::FRUIT_COUNT];
	unsigned long long s_craftedTotal = 0, s_failedTotal = 0;
	unsigned long long s_boughtSeen[mt2009_rankp::FRUIT_COUNT];	// the market's counters at the last census
	unsigned long long s_noHigherSeen = 0;
	unsigned int s_going = 0, s_gaveUp = 0, s_capped = 0, s_visits_done = 0;
	DWORD s_censusAt = 0;

	int Walkers(DWORD dwNow)
	{
		for (size_t i = 0; i < s_walkers.size();)
		{
			if (dwNow - s_walkers[i].second > GIVE_UP_MS + 5000)
			{
				s_walkers[i] = s_walkers.back();
				s_walkers.pop_back();
			}
			else
				++i;
		}
		return (int)s_walkers.size();
	}

	void DropWalker(DWORD pid)
	{
		for (size_t i = 0; i < s_walkers.size(); ++i)
			if (s_walkers[i].first == pid)
			{
				s_walkers[i] = s_walkers.back();
				s_walkers.pop_back();
				return;
			}
	}

	void EndVisit(DWORD pid, TVisit& v, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (v.walking)
			DropWalker(pid);
		v.walking = false;
		v.actionAt = 0;
		v.npcVid = 0;
		v.nextCheck = dwNow + number(CHECK_MIN_MS, CHECK_MAX_MS);
		ClearPlayerBotRoute(state, true);
	}

	void Census(DWORD dwNow)
	{
		using namespace mt2009_rankp;
		if (s_censusAt == 0)
		{
			s_censusAt = dwNow;
			return;
		}
		if (dwNow - s_censusAt < CENSUS_MS)
			return;
		s_censusAt = dwNow;
		unsigned long long crafted = 0, failed = 0, boughtAll = 0;
		char steps[256];
		int len = 0;
		steps[0] = '\0';
		for (int i = 0; i < FRUIT_COUNT; ++i)
		{
			crafted += s_crafted[i];
			failed += s_failed[i];
			if (i > 0 && len >= 0 && len < (int)sizeof(steps))
				len += snprintf(steps + len, sizeof(steps) - len, "%s%u:%llu/%llu", i > 1 ? "," : "", FRUITS[i].vnum,
						s_crafted[i], s_failed[i]);
			const unsigned long long bought = s_aPlayerBotRankFruitBoughtForCraft[i] - s_boughtSeen[i];
			boughtAll += bought;
		}
		const unsigned long long apples = s_aPlayerBotRankFruitBoughtForCraft[0] - s_boughtSeen[0];
		const unsigned long long noHigher = s_ullPlayerBotRankFruitBoughtNoHigher - s_noHigherSeen;
		sys_log(0, "PLAYERBOT_RANK_FRUIT_CRAFT: census on=%d crafted=%llu failed=%llu apples_bought_for_craft=%llu "
				"bought_for_craft=%llu bought_for_craft_no_higher=%llu visits=%u going=%u gave_up=%u capped=%u walking=%d "
				"crafted_total=%llu failed_total=%llu steps=%s",
				IsPlayerBotFruitCraftOn() ? 1 : 0, crafted, failed, apples, boughtAll, noHigher, s_visits_done, s_going,
				s_gaveUp, s_capped, Walkers(dwNow), s_craftedTotal, s_failedTotal, steps);
		for (int i = 0; i < FRUIT_COUNT; ++i)
		{
			s_crafted[i] = s_failed[i] = 0;
			s_boughtSeen[i] = s_aPlayerBotRankFruitBoughtForCraft[i];
		}
		s_noHigherSeen = s_ullPlayerBotRankFruitBoughtNoHigher;
		s_visits_done = s_going = s_gaveUp = s_capped = 0;
	}
}

namespace
{
	// Worth crafting a fruit's surplus (index `lower` -> lower + 1): the lower fruit overstocked (the clearing ask is
	// on) or seven of it at its ask under one of the higher.
	bool IsPlayerBotFruitCraftWorth(int lower)
	{
		using namespace mt2009_rankp;
		if (lower < 0 || lower + 1 >= FRUIT_COUNT)
			return false;
		const DWORD low = FRUITS[lower].vnum, high = FRUITS[lower + 1].vnum;
		return GetPlayerBotClearingUnit(low) > 0 ||
				(unsigned long long)GetPlayerBotRankFruitListUnit(low) * PLAYERBOT_FRUIT_CRAFT_IN <
				(unsigned long long)GetPlayerBotRankFruitListUnit(high);
	}

	// The crafts of step `lower` (FRUITS[lower] x7 -> FRUITS[lower + 1]) the bot would make now.
	int GetPlayerBotFruitCraftCount(LPCHARACTER ch, int lower)
	{
		using namespace mt2009_rankp;
		if (!ch || lower < 0 || lower + 1 >= FRUIT_COUNT)
			return 0;
		const DWORD vnum = FRUITS[lower].vnum;
		const int base = GetPlayerBotRankFruitBaseKeep(ch, vnum);
		if (base >= 1000000)
			return 0;
		int avail = (int)ch->CountSpecifyItem(vnum) - base;
		if (avail < PLAYERBOT_FRUIT_CRAFT_IN)
			return 0;
		if (!IsPlayerBotFruitCraftWorth(lower))
			avail = std::min(avail, GetPlayerBotRankFruitCraftKeep(ch, vnum));
		return std::max(0, avail / PLAYERBOT_FRUIT_CRAFT_IN);
	}

	bool HasPlayerBotFruitCraftWork(LPCHARACTER ch)
	{
		if (!ch || !IsPlayerBotFruitCraftOn() || !mt2009_rankp::Known(ch) ||
				(long long)ch->GetGold() < PLAYERBOT_FRUIT_CRAFT_GOLD)
			return false;
		for (int i = 0; i + 1 < mt2009_rankp::FRUIT_COUNT; ++i)
			if (GetPlayerBotFruitCraftCount(ch, i) > 0)
				return true;
		return false;
	}

	// Room for one more piece of `vnum`: a stack of it with room, or a free cell.
	bool HasPlayerBotFruitCraftRoom(LPCHARACTER ch, DWORD vnum)
	{
		for (int cell = 0; cell < PLAYERBOT_BAG_CELLS; ++cell)
		{
			LPITEM held = ch->GetInventoryItem(cell);
			if (held && held->GetVnum() == vnum && !held->isLocked() && (int)held->GetCount() < (int)held->GetMaxStack())
				return true;
		}
		return ch->GetEmptyInventory(1) >= 0;
	}

	// One attempt, Cube_make's steps: the seven pieces (and the recipe's Yang, none) go whatever the roll says, the
	// higher piece comes on a success.
	bool CraftPlayerBotFruitOnce(LPCHARACTER ch, int lower)
	{
		using namespace mt2009_rankp;
		const DWORD low = FRUITS[lower].vnum, high = FRUITS[lower + 1].vnum;
		if ((int)ch->CountSpecifyItem(low) < PLAYERBOT_FRUIT_CRAFT_IN || !HasPlayerBotFruitCraftRoom(ch, high) ||
				(long long)ch->GetGold() < PLAYERBOT_FRUIT_CRAFT_GOLD)
			return false;
		ch->RemoveSpecifyItem(low, PLAYERBOT_FRUIT_CRAFT_IN);
		if (PLAYERBOT_FRUIT_CRAFT_GOLD > 0)
			PlayerBotChangeGold(ch, -PLAYERBOT_FRUIT_CRAFT_GOLD);
		const bool success = number(1, 100) <= PLAYERBOT_FRUIT_CRAFT_PERCENT;
		LPITEM made = success ? ch->AutoGiveItem(high, 1, -1, false) : NULL;
		LogManager::instance().CubeLog(ch->GetPlayerID(), ch->GetX(), ch->GetY(), high, made ? made->GetID() : 0,
				made ? 1 : 0, made != NULL);
		if (made)
		{
			++mt2009_fruitcraft::s_crafted[lower + 1];
			++mt2009_fruitcraft::s_craftedTotal;
		}
		else
		{
			++mt2009_fruitcraft::s_failed[lower + 1];
			++mt2009_fruitcraft::s_failedTotal;
		}
		return true;
	}
}

// The tick (playerbot_manager.cpp, beside Potega madrosci's: after the village's errands, before the town linger and
// the world travel). True while it owns the tick.
bool ManagePlayerBotRankFruitCraft(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
{
	using namespace mt2009_fruitcraft;
	if (!ch || !ch->IsItemLoaded() || ch->IsDead())
		return false;
	Census(dwNow);
	TVisit& v = s_visits[ch->GetPlayerID()];
	if (!v.walking)
	{
		if (v.nextCheck == 0)
		{
			// The first look staggered by the pid, so a core's bots never ask together after a start.
			v.nextCheck = dwNow + CHECK_MIN_MS + (ch->GetPlayerID() * 7919U) % CHECK_MAX_MS;
			return false;
		}
		if ((int)(dwNow - v.nextCheck) < 0)
			return false;
		v.nextCheck = dwNow + number(CHECK_MIN_MS, CHECK_MAX_MS);
		if (ch->GetMyShop() || ch->GetExchange() || state.bFishingSession || state.bMarketTrip || state.bVisitingShop ||
				state.bVisitingBiologist || state.bVisitingHerbalist || state.bVisitingStable || state.bVisitingAlchemist ||
				state.bVisitingUriel || state.bCraftErrand != 0 || state.bWorldEventKind != 0 ||
				ch->GetVictim() != NULL || state.dwTargetVID != 0 || IsPlayerBotSidekickPID(ch->GetPlayerID()) ||
				(ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())) || IsPlayerBotHeldForCompany(ch))
			return false;
		if (!HasPlayerBotFruitCraftWork(ch) || CountPlayerBotFreeInventoryCells(ch) < 2)
			return false;
		LPCHARACTER uriel = mt2009_potega::FindUriel(ch, 0);
		if (!uriel)
			return false;
		if (Walkers(dwNow) >= MAX_WALKERS)
		{
			++s_capped;
			v.nextCheck = dwNow + number(20000, 45000);
			return false;
		}
		s_walkers.push_back(std::make_pair(ch->GetPlayerID(), dwNow));
		++s_going;
		v.walking = true;
		v.startedAt = dwNow;
		v.actionAt = 0;
		v.npcVid = uriel->GetVID();
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		ch->Stop();
		ClearPlayerBotRoute(state, true);
		sys_log(1, "PLAYERBOT_RANK_FRUIT_CRAFT: going pid=%u name=%s lv=%d map=%ld dist=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), ch->GetMapIndex(),
				DISTANCE_APPROX(ch->GetX() - uriel->GetX(), ch->GetY() - uriel->GetY()));
	}

	// On the way: anything real takes the bot back, and a walk that lasts too long is given up.
	LPCHARACTER uriel = mt2009_potega::FindUriel(ch, v.npcVid);
	if (!uriel || !IsPlayerBotFruitCraftOn() || ch->GetVictim() != NULL || state.bVisitingShop || state.bVisitingUriel ||
			state.bVisitingAlchemist || state.bFishingSession || state.bWorldEventKind != 0 || ch->GetMyShop() ||
			(ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())) || dwNow - v.startedAt > GIVE_UP_MS)
	{
		++s_gaveUp;
		sys_log(1, "PLAYERBOT_RANK_FRUIT_CRAFT: gave up pid=%u name=%s map=%ld uriel=%d after=%ums",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), uriel ? 1 : 0, dwNow - v.startedAt);
		EndVisit(ch->GetPlayerID(), v, state, dwNow);
		return false;
	}
	SetPlayerBotAction(state, BOT_ACTION_SHOP, dwNow);
	state.dwTargetVID = 0;

	long approachX = 0, approachY = 0;
	GetPlayerBotNpcApproach(ch->GetPlayerID(), uriel->GetX(), uriel->GetY(), 0x4F574F43U, approachX, approachY);
	if (DISTANCE_APPROX(ch->GetX() - approachX, ch->GetY() - approachY) > 650)
	{
		if (!MovePlayerBot(ch, approachX, approachY, dwNow, 20, true, true, false, true) && state.bStuckCounter >= 6)
		{
			++s_gaveUp;
			sys_err("PLAYERBOT_RANK_FRUIT_CRAFT: route to Uriel failed pid=%u name=%s map=%ld from=(%ld,%ld)",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), ch->GetX(), ch->GetY());
			EndVisit(ch->GetPlayerID(), v, state, dwNow);
			return false;
		}
		return true;
	}

	ch->Stop();
	ch->SetPosition(POS_STANDING);
	if (v.actionAt == 0)
	{
		v.actionAt = dwNow + number(2000, 5000);	// at his window a moment
		return true;
	}
	if ((int)(dwNow - v.actionAt) < 0)
		return true;

	// The steps from the bottom up: the pears a step makes may be the next step's surplus.
	int made = 0;
	unsigned long long okBefore = s_craftedTotal, failBefore = s_failedTotal;
	for (int i = 0; i + 1 < mt2009_rankp::FRUIT_COUNT && made < MAX_CRAFTS_A_VISIT; ++i)
		for (int n = GetPlayerBotFruitCraftCount(ch, i); n > 0 && made < MAX_CRAFTS_A_VISIT; --n)
		{
			if (!CraftPlayerBotFruitOnce(ch, i))
				break;
			++made;
		}
	++s_visits_done;
	sys_log(1, "PLAYERBOT_RANK_FRUIT_CRAFT: visit pid=%u name=%s lv=%d points=%d crafted=%llu failed=%llu",
			ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), mt2009_rankp::KnownPoints(ch), s_craftedTotal - okBefore,
			s_failedTotal - failBefore);
	EndVisit(ch->GetPlayerID(), v, state, dwNow);
	return false;
}

#endif
