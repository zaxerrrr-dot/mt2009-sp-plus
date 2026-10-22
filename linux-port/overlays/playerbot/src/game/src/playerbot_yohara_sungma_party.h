#ifndef __INC_METIN2_PLAYERBOT_YOHARA_SUNGMA_PARTY_H__
#define __INC_METIN2_PLAYERBOT_YOHARA_SUNGMA_PARTY_H__

// MT2009_PLUS_BOT_YOHARA_FIGHT_V1 - the bots' parties on the Sung Ma maps (the owner, 22 October 2026, night: "druzyny
// botow na rdzeniu Yohary na bossow i posterunki"; doc: cache/yohara/boty-mapy-yohary.md, section 11).
//
// The bosses, the outposts and the Metins of these maps are a party's of three (IsPlayerBotSungmaStoneForMe, the boss
// rule of BuildPlayerBotCombatContext, the party hubs), and the ordinary party pass gave game3 next to none: its draw
// (the companion phase of Iwakura's personas) let 0-4 of 27-46 bots of the core in, a partner had to stand within
// 1 800 units and three levels - every Champion is level 120, so the level said nothing of the band - and a party
// lasted five to fifteen minutes. The test of 22 October (18:40-19:36) made 8 parties of two on the whole core and
// none of three. So a resident of a Sung Ma map (ManagePlayerBotParty hands it here) is in a party by these rules:
//   * who: residents on their own map (not on Dongan's errand, nor walking to a portal, nor leaving), alive, of one
//     kingdom (the engine's rule), within PLAYERBOT_SUNGMA_PARTY_BAND Champion levels of the leader;
//   * how: a free bot joins the biggest party with room whose leader is within PLAYERBOT_SUNGMA_PARTY_FIND_RANGE and
//     reachable (the follow walks it up), else makes a party with the nearest free bot; a leader with room asks the
//     nearest free bot in; a pair older than PLAYERBOT_SUNGMA_PARTY_PAIR_MS goes over to a party of three or four
//     beside it; three to five (PLAYERBOT_SUNGMA_PARTY_MIN / _MAX); no time limit;
//   * the leader picks the spot (the party hubs from three) and the target (PickPlayerBotSungmaTarget: a stone or a boss
//     with three ready members by it), the members take its target (FindPlayerBotPartyFocusTarget) and follow it; a
//     leader with nothing to fight waits for members farther than PLAYERBOT_SUNGMA_REGROUP_RADIUS (the regroup);
//   * out: a member whose leader is on another map, more than the band apart or farther than
//     PLAYERBOT_SUNGMA_PARTY_LEAVE_RANGE; anyone going on Dongan's errand or the trade trip, moving to another map or
//     leaving the maps (LeavePlayerBotSungmaParty - a leader's going ends the party, the others make a new one at once);
//     a member revived stands up by its party only with two of them beside it (MovePlayerBotSungmaRevived).
//
// An implementation fragment: included by playerbot_yohara_bots.h after playerbot_yohara_sungma.h, in its namespace.

	const int PLAYERBOT_SUNGMA_PARTY_BAND = 4;
	const int PLAYERBOT_SUNGMA_PARTY_FIND_RANGE = 12000;
	const int PLAYERBOT_SUNGMA_PARTY_LEAVE_RANGE = 20000;
	const DWORD PLAYERBOT_SUNGMA_PARTY_PAIR_MS = 4 * 60 * 1000;
	const int PLAYERBOT_SUNGMA_REGROUP_RADIUS = 2500;
	const DWORD PLAYERBOT_SUNGMA_REGROUP_MS = 45 * 1000;
	const DWORD PLAYERBOT_SUNGMA_REGROUP_GAP_MS = 90 * 1000;

	struct TPlayerBotSungmaPartyBot
	{
		DWORD dwSince;			// in its party since
		DWORD dwRegroupSince, dwNextRegroup;
		TPlayerBotSungmaPartyBot() : dwSince(0), dwRegroupSince(0), dwNextRegroup(0) {}
	};
	std::map<DWORD, TPlayerBotSungmaPartyBot> s_mapPlayerBotSungmaParty;

	// A resident that may be in a party now: on its own map, nothing else on its hands.
	bool IsPlayerBotSungmaPartyFree(LPCHARACTER ch, const TPlayerBotYoharaResident& r)
	{
		if (!ch || r.iPurpose != YOHARA_PURPOSE_SUNGMA || !ch->IsItemLoaded())
			return false;
		const long base = ch->GetMapIndex() >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ? ch->GetMapIndex() / 10000 : ch->GetMapIndex();
		const DWORD pid = ch->GetPlayerID();
		return base == r.lMap && IsPlayerBotSungmaBotMap(base) && GetPlayerBotSungmaActivity(pid) == 0 &&
				!IsPlayerBotYoharaLeaving(pid) && !IsPlayerBotOnDungeonRun(pid) && !IsPlayerBotOnMercContract(pid);
	}

	// The same of another bot, with its AI state (alive, not in its revival or a retreat).
	bool IsPlayerBotSungmaPartyPartner(LPCHARACTER other)
	{
		if (!other || other->IsDead() || !other->GetDesc() || !other->GetDesc()->IsBot())
			return false;
		const TPlayerBotYoharaResident* r = FindPlayerBotYoharaResident(other->GetPlayerID());
		if (!r || !IsPlayerBotSungmaPartyFree(other, *r))
			return false;
		TPlayerBotAIStateMap::const_iterator s = s_mapPlayerBotAIStates.find(other->GetPlayerID());
		return s != s_mapPlayerBotAIStates.end() && !s->second.bRecoveringAfterDeath;
	}

	bool IsPlayerBotSungmaPartyReachable(LPCHARACTER a, LPCHARACTER b)
	{
		CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(a->GetMapIndex());
		return !navigation.Init(a->GetMapIndex()) || navigation.CanReach(a->GetX(), a->GetY(), b->GetX(), b->GetY());
	}

	void NotePlayerBotSungmaPartyIn(LPCHARACTER ch, TPlayerBotAIState& state, LPPARTY party, DWORD dwNow)
	{
		state.dwPartyExpireTime = 0;
		state.dwNextPartyCheckTime = dwNow + PLAYERBOT_PARTY_CHECK_INTERVAL;
		s_mapPlayerBotSungmaParty[ch->GetPlayerID()].dwSince = dwNow ? dwNow : 1;
		if (party && party->GetExpDistributionMode() != PARTY_EXP_DISTRIBUTION_PARITY)
			party->SetParameter(PARTY_EXP_DISTRIBUTION_PARITY);
	}

	// Into another bot's party (the engine's join and link).
	bool JoinPlayerBotSungmaParty(LPCHARACTER ch, TPlayerBotAIState& state, LPPARTY party, const char* why, DWORD dwNow)
	{
		if (!ch || !party || ch->GetParty() || (int)party->GetMemberCount() >= PLAYERBOT_SUNGMA_PARTY_MAX)
			return false;
		LPCHARACTER leader = party->GetLeaderCharacter();
		if (!leader || leader->GetEmpire() != ch->GetEmpire())
			return false;
		party->Join(ch->GetPlayerID());
		party->Link(ch);
		if (ch->GetParty() != party)
			return false;
		NotePlayerBotSungmaPartyIn(ch, state, party, dwNow);
		if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(ch->GetMapIndex()))
			++st->partyJoins;
		sys_log(0, "PLAYERBOT_SUNGMA: party join pid=%u name=%s map=%ld leader=%s members=%u champion=%d leader_champion=%d why=%s dist=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), leader->GetName(), (unsigned int)party->GetMemberCount(),
				GetPlayerBotChampionLevel(ch), GetPlayerBotChampionLevel(leader), why,
				DISTANCE_APPROX(ch->GetX() - leader->GetX(), ch->GetY() - leader->GetY()));
		return true;
	}

	// The nearest free partner for ch (its kingdom, its map, its band, within range, not in a party). With a party
	// (a leader recruiting) the band is the leader's.
	LPCHARACTER FindPlayerBotSungmaFreePartner(LPCHARACTER ch)
	{
		const int champion = GetPlayerBotChampionLevel(ch);
		LPCHARACTER best = NULL;
		int bestDist = INT_MAX;
		for (std::map<DWORD, TPlayerBotYoharaResident>::const_iterator r = s_mapPlayerBotYoharaResident.begin();
				r != s_mapPlayerBotYoharaResident.end(); ++r)
		{
			if (r->first == ch->GetPlayerID() || r->second.iPurpose != YOHARA_PURPOSE_SUNGMA)
				continue;
			LPCHARACTER other = CHARACTER_MANAGER::instance().FindByPID(r->first);
			if (!other || other->GetMapIndex() != ch->GetMapIndex() || other->GetEmpire() != ch->GetEmpire() || other->GetParty())
				continue;
			const int d = DISTANCE_APPROX(other->GetX() - ch->GetX(), other->GetY() - ch->GetY());
			if (d > PLAYERBOT_SUNGMA_PARTY_FIND_RANGE || d >= bestDist ||
					abs(GetPlayerBotChampionLevel(other) - champion) > PLAYERBOT_SUNGMA_PARTY_BAND ||
					!IsPlayerBotSungmaPartyPartner(other) || ArePlayerBotLegendRivalPids(ch->GetPlayerID(), other->GetPlayerID()))
				continue;
			best = other;
			bestDist = d;
		}
		return best && IsPlayerBotSungmaPartyReachable(ch, best) ? best : NULL;
	}

	// The biggest bots' party with room beside ch whose leader takes it (the kingdom, the band, the range); minMembers:
	// the smallest one looked at. NULL: none.
	LPPARTY FindPlayerBotSungmaOpenParty(LPCHARACTER ch, int minMembers)
	{
		const int champion = GetPlayerBotChampionLevel(ch);
		LPPARTY best = NULL;
		LPCHARACTER bestLeader = NULL;
		long long bestScore = LLONG_MIN;
		std::set<LPPARTY> seen;
		for (std::map<DWORD, TPlayerBotYoharaResident>::const_iterator r = s_mapPlayerBotYoharaResident.begin();
				r != s_mapPlayerBotYoharaResident.end(); ++r)
		{
			if (r->second.iPurpose != YOHARA_PURPOSE_SUNGMA || r->first == ch->GetPlayerID())
				continue;
			LPCHARACTER other = CHARACTER_MANAGER::instance().FindByPID(r->first);
			LPPARTY party = other ? other->GetParty() : NULL;
			if (!party || party == ch->GetParty() || !seen.insert(party).second)
				continue;
			const int members = (int)party->GetMemberCount();
			LPCHARACTER leader = party->GetLeaderCharacter();
			if (members < minMembers || members >= PLAYERBOT_SUNGMA_PARTY_MAX || !leader || IsPlayerBotHumanLedParty(party) ||
					leader->GetMapIndex() != ch->GetMapIndex() || leader->GetEmpire() != ch->GetEmpire() || leader->IsDead() ||
					abs(GetPlayerBotChampionLevel(leader) - champion) > PLAYERBOT_SUNGMA_PARTY_BAND ||
					PlayerBotPartyHasLegendRival(ch, party))
				continue;
			const int d = DISTANCE_APPROX(leader->GetX() - ch->GetX(), leader->GetY() - ch->GetY());
			if (d > PLAYERBOT_SUNGMA_PARTY_FIND_RANGE)
				continue;
			const long long score = (long long)members * 100000LL - d;
			if (score > bestScore)
			{
				bestScore = score;
				best = party;
				bestLeader = leader;
			}
		}
		return best && IsPlayerBotSungmaPartyReachable(ch, bestLeader) ? best : NULL;
	}

	// ManagePlayerBotParty's part for a resident of the Sung Ma maps: -1 not its (the ordinary rules), 0 done.
	int ManagePlayerBotSungmaParty(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch)
			return -1;
		const TPlayerBotYoharaResident* r = FindPlayerBotYoharaResident(ch->GetPlayerID());
		if (!r || r->iPurpose != YOHARA_PURPOSE_SUNGMA || !IsPlayerBotSungmaBotMap(ch->GetMapIndex()))
			return -1;
		LPPARTY party = ch->GetParty();
		if (party && IsPlayerBotHumanLedParty(party))
			return -1;
		const bool free = IsPlayerBotSungmaPartyFree(ch, *r);
		if (party && party->GetMemberCount() < 2)
		{
			CPartyManager::instance().DeleteParty(party);
			party = NULL;
		}
		if (party)
		{
			// a member's errand, walk or move: out (the errand and the trade trip leave by themselves too)
			if (!free)
			{
				LeavePlayerBotSungmaParty(ch, "busy", GetPlayerBotSungmaActivity(ch->GetPlayerID()) == 2);
				return 0;
			}
			if (party->GetExpDistributionMode() != PARTY_EXP_DISTRIBUTION_PARITY)
				party->SetParameter(PARTY_EXP_DISTRIBUTION_PARITY);
			LPCHARACTER leader = party->GetLeaderCharacter();
			if (!leader)
			{
				LeavePlayerBotSungmaParty(ch, "no_leader", false);
				return 0;
			}
			TPlayerBotSungmaPartyBot& pb = s_mapPlayerBotSungmaParty[ch->GetPlayerID()];
			if (pb.dwSince == 0)
				pb.dwSince = dwNow ? dwNow : 1;
			if (leader != ch)
			{
				const char* why = NULL;
				if (leader->GetMapIndex() != ch->GetMapIndex())
					why = "leader_map";
				else if (abs(GetPlayerBotChampionLevel(leader) - GetPlayerBotChampionLevel(ch)) > PLAYERBOT_SUNGMA_PARTY_BAND)
					why = "band";
				else if (DISTANCE_APPROX(leader->GetX() - ch->GetX(), leader->GetY() - ch->GetY()) > PLAYERBOT_SUNGMA_PARTY_LEAVE_RANGE ||
						!IsPlayerBotSungmaPartyReachable(ch, leader))
					why = "far";
				if (why)
				{
					LeavePlayerBotSungmaParty(ch, why, false);
					return 0;
				}
				// a pair that found no third goes over to a party of three or four beside it
				if (party->GetMemberCount() == 2 && dwNow - pb.dwSince >= PLAYERBOT_SUNGMA_PARTY_PAIR_MS && !ch->IsDead() &&
						state.dwTargetVID == 0 && ch->GetVictim() == NULL)
				{
					LPPARTY bigger = FindPlayerBotSungmaOpenParty(ch, PLAYERBOT_SUNGMA_PARTY_MIN);
					if (bigger)
					{
						LeavePlayerBotSungmaParty(ch, "pair_merge", false);
						JoinPlayerBotSungmaParty(ch, state, bigger, "pair_merge", dwNow);
					}
				}
				return 0;
			}
			// the leader asks a free bot in while it has room
			if ((int)party->GetMemberCount() < PLAYERBOT_SUNGMA_PARTY_MAX && !ch->IsDead())
			{
				LPCHARACTER partner = FindPlayerBotSungmaFreePartner(ch);
				TPlayerBotAIStateMap::iterator ps = partner ? s_mapPlayerBotAIStates.find(partner->GetPlayerID()) : s_mapPlayerBotAIStates.end();
				if (partner && ps != s_mapPlayerBotAIStates.end())
					JoinPlayerBotSungmaParty(partner, ps->second, party, "invited", dwNow);
			}
			return 0;
		}
		s_mapPlayerBotSungmaParty.erase(ch->GetPlayerID());
		if (!free || ch->IsDead() || state.bRecoveringAfterDeath)
			return 0;
		// a free bot: the biggest party with room by it, else a new one with the nearest free bot
		LPPARTY open = FindPlayerBotSungmaOpenParty(ch, 2);
		if (open && JoinPlayerBotSungmaParty(ch, state, open, "joined", dwNow))
			return 0;
		LPCHARACTER partner = FindPlayerBotSungmaFreePartner(ch);
		if (!partner)
			return 0;
		TPlayerBotAIStateMap::iterator ps = s_mapPlayerBotAIStates.find(partner->GetPlayerID());
		if (ps == s_mapPlayerBotAIStates.end())
			return 0;
		LPPARTY made = CPartyManager::instance().CreateParty(ch);
		if (!made)
			return 0;
		made->Link(ch);
		NotePlayerBotSungmaPartyIn(ch, state, made, dwNow);
		made->Join(partner->GetPlayerID());
		made->Link(partner);
		if (partner->GetParty() == made)
			NotePlayerBotSungmaPartyIn(partner, ps->second, made, dwNow);
		if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(ch->GetMapIndex()))
			++st->partyForms;
		sys_log(0, "PLAYERBOT_SUNGMA: party form pid=%u name=%s map=%ld partner=%s champion=%d partner_champion=%d dist=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), partner->GetName(), GetPlayerBotChampionLevel(ch),
				GetPlayerBotChampionLevel(partner), DISTANCE_APPROX(ch->GetX() - partner->GetX(), ch->GetY() - partner->GetY()));
		return 0;
	}

	struct FFindPlayerBotSungmaStraggler
	{
		LPCHARACTER m_leader;
		int m_far, m_near;
		explicit FFindPlayerBotSungmaStraggler(LPCHARACTER leader) : m_leader(leader), m_far(0), m_near(0) {}
		void operator()(LPCHARACTER member)
		{
			if (!member || member == m_leader || member->IsDead())
				return;
			const int d = DISTANCE_APPROX(member->GetX() - m_leader->GetX(), member->GetY() - m_leader->GetY());
			if (d > PLAYERBOT_SUNGMA_REGROUP_RADIUS && d <= PLAYERBOT_SUNGMA_PARTY_LEAVE_RANGE)
				++m_far;
			else if (d <= PLAYERBOT_SUNGMA_REGROUP_RADIUS)
				++m_near;
		}
	};

	// The leader with nothing to fight and members still walking up: it stands (up to PLAYERBOT_SUNGMA_REGROUP_MS, then
	// not again for PLAYERBOT_SUNGMA_REGROUP_GAP_MS). True: the tick is the wait's.
	bool HoldPlayerBotSungmaRegroup(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		LPPARTY party = ch ? ch->GetParty() : NULL;
		if (!party || party->GetLeaderPID() != ch->GetPlayerID() || party->GetMemberCount() < 2 || IsPlayerBotHumanLedParty(party))
			return false;
		TPlayerBotSungmaPartyBot& pb = s_mapPlayerBotSungmaParty[ch->GetPlayerID()];
		if (state.dwTargetVID != 0 || ch->GetVictim() != NULL || state.bTacticalRetreat || state.bRecoveringAfterDeath ||
				ch->IsDead())
		{
			pb.dwRegroupSince = 0;
			return false;
		}
		FFindPlayerBotSungmaStraggler f(ch);
		party->ForEachOnMapMember(f, ch->GetMapIndex());
		if (f.m_far == 0)
		{
			pb.dwRegroupSince = 0;
			return false;
		}
		if (pb.dwRegroupSince == 0)
		{
			if ((int)(dwNow - pb.dwNextRegroup) < 0)
				return false;
			pb.dwRegroupSince = dwNow ? dwNow : 1;
			if (TPlayerBotSungmaFightStats* st = GetPlayerBotSungmaFightStats(ch->GetMapIndex()))
				++st->regroups;
			PlayerBotLogThrottled("sungma_regroup", dwNow, "PLAYERBOT_SUNGMA: regroup pid=%u name=%s map=%ld members=%u far=%d near=%d",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), (unsigned int)party->GetMemberCount(), f.m_far, f.m_near);
		}
		if (dwNow - pb.dwRegroupSince >= PLAYERBOT_SUNGMA_REGROUP_MS || FindPlayerBotEngagedTarget(ch, &state, dwNow))
		{
			pb.dwRegroupSince = 0;
			pb.dwNextRegroup = dwNow + PLAYERBOT_SUNGMA_REGROUP_GAP_MS;
			return false;
		}
		if (ch->IsStateMove())
			ch->Stop();
		ClearPlayerBotRoute(state, true);
		SetPlayerBotAction(state, BOT_ACTION_PARTY_ASSEMBLE, dwNow);
		return true;
	}

#endif
