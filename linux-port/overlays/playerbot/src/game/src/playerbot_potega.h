#ifndef __INC_METIN2_PLAYERBOT_POTEGA_H__
#define __INC_METIN2_PLAYERBOT_POTEGA_H__

// MT2009_PLUS_POTEGA_MADROSCI_V1 - "Potega madrosci" (the owner, 3 November 2026, from the pl-wiki's server pages:
// "Spytaj Uriela o potege madrosci, aby otrzymac bonus PD w zaleznosci od przedzialu poziomow").
//
// The players' half is the quest potega_madrosci.quest: while the event flag potega_madrosci is on (the events
// planner's kind "potega", playerbot_ingame_events.h writes the flag; a GM's /eventflag potega_madrosci 1 too) Uriel
// (20011 - in every first village, and in Dongan) has the option "Potega madrosci" and gives the affect 730 on point
// 127 (POINT_RAMADAN_CANDY_BONUS_EXP) for the configured minutes: +N% experience by the character's level range, or by
// its Champion level range for a Champion. Point 127 is the one every item experience bonus goes through since
// server-patches/pdbonus: GiveExp adds it to the rate factor like the server's rates (no 100 cap as on 116, so the
// +125% fits and the Mikstura Madrosci on 116 stacks beside it), the Champion bar counts it (playerbot_champion.cpp)
// and the client's bonus window shows it in the PD line.
//
// The settings are player.potega_madrosci_config (minutes, the bots' switch and share) and player.potega_madrosci_tier
// (champion 0/1, the level range, the percent) - mariadb/playerbot/potega_madrosci.sql, the advanced panel's page
// "Potega madrosci" (seban-panel potega_madrosci.py). The quest reads them on every talk; this file every minute.
//
// The bots' half (here): a bot that is near an Uriel (the same map, PLAYERBOT_POTEGA_RANGE) while the event runs,
// has no bonus yet and whose level falls in a range walks to him and takes it - the same affect, the same tiers.
// Cheap and without a stampede: a look every 1-3 minutes a bot (staggered by the pid), only the share of bots the
// panel sets (a stable pick by the pid, default 60%), never a stall keeper, an angler in a session, a bot in a
// person's party or held for company, never from a fight, and at most PLAYERBOT_POTEGA_MAX_WALKERS on the way at
// once on a core. It is asked after every errand of the village and before the town linger and the world travel -
// the bots that reach it are the ones about to go out and hunt. PLAYERBOT_POTEGA: lines (going / taken / gave up)
// and a census every 10 minutes.
#include <unordered_map>
#include <vector>

namespace mt2009_potega
{
	const DWORD AFFECT_POTEGA_MADROSCI = 730;	// free: 720/721 Boss Swiata, 760-776 the relics, 780-788 the horse
	const DWORD URIEL_VNUM = 20011;
	const char* const EVENT_FLAG = "potega_madrosci";

	struct TTier
	{
		int champion;	// 0: the level, 1: the Champion level
		int from, to;
		int pct;
	};

	struct TConfig
	{
		bool read;
		bool fromTable;
		int minutes;
		int bots;		// 0 off, 1 on
		int botShare;	// per cent of the bots that bother
		std::vector<TTier> tiers;
		TConfig() : read(false), fromTable(false), minutes(240), bots(1), botShare(60) {}
	};

	TConfig s_cfg;
	DWORD s_dwConfigReadAt = 0;

	// The wiki's table - what the quest and the bots use while the tables are missing (a core before the migration).
	void Defaults(TConfig& c)
	{
		static const TTier k[] = { { 0, 41, 80, 25 }, { 0, 81, 100, 50 }, { 0, 101, 120, 100 }, { 1, 1, 10, 125 }, { 1, 11, 30, 100 } };
		c.tiers.assign(k, k + sizeof(k) / sizeof(k[0]));
		c.minutes = 240;
	}

	long Num(const char* s)
	{
		return s ? atol(s) : 0;
	}

	void ReadConfig(DWORD dwNow)
	{
		if (s_cfg.read && dwNow - s_dwConfigReadAt < 60000)
			return;
		s_dwConfigReadAt = dwNow;
		TConfig c;
		c.read = true;
		std::unique_ptr<SQLMsg> m(DBManager::instance().DirectQuery(
				"SELECT minutes, bots, bot_share FROM player.potega_madrosci_config WHERE id = 1"));
		std::unique_ptr<SQLMsg> t(DBManager::instance().DirectQuery(
				"SELECT champion, lvl_from, lvl_to, pct FROM player.potega_madrosci_tier WHERE enabled = 1 "
				"ORDER BY champion, lvl_from, lvl_to"));
		const bool cfgOk = m.get() && m->uiSQLErrno == 0 && m->Get() && m->Get()->pSQLResult;
		const bool tierOk = t.get() && t->uiSQLErrno == 0 && t->Get() && t->Get()->pSQLResult;
		if (!cfgOk || !tierOk)
		{
			Defaults(c);
			if (!s_cfg.read || s_cfg.fromTable)
				sys_log(0, "PLAYERBOT_POTEGA: no settings tables (player.potega_madrosci_*) - the wiki's table");
			s_cfg = c;
			return;
		}
		c.fromTable = true;
		if (m->Get()->uiNumRows)
		{
			MYSQL_ROW r = mysql_fetch_row(m->Get()->pSQLResult);
			if (r)
			{
				c.minutes = MINMAX(1, (int)Num(r[0]), 10080);
				c.bots = Num(r[1]) ? 1 : 0;
				c.botShare = MINMAX(0, (int)Num(r[2]), 100);
			}
		}
		MYSQL_ROW r;
		while ((r = mysql_fetch_row(t->Get()->pSQLResult)) != NULL)
		{
			TTier x;
			x.champion = Num(r[0]) ? 1 : 0;
			x.from = (int)Num(r[1]);
			x.to = (int)Num(r[2]);
			x.pct = MINMAX(0, (int)Num(r[3]), 1000);
			if (x.pct > 0 && x.to >= x.from)
				c.tiers.push_back(x);
		}
		s_cfg = c;
	}

	bool IsEventOn()
	{
		return quest::CQuestManager::instance().GetEventFlag(EVENT_FLAG) > 0;
	}

	// The quest's rule: a Champion (Champion level 1+) by the Champion ranges only, anybody else by the level ranges;
	// the first range that holds it. 0: none.
	int PercentFor(LPCHARACTER ch)
	{
		const int champion = ch->GetConquerorLevel() >= 1 ? 1 : 0;
		const int level = champion ? (int)ch->GetConquerorLevel() : (int)ch->GetLevel();
		for (size_t i = 0; i < s_cfg.tiers.size(); ++i)
		{
			const TTier& x = s_cfg.tiers[i];
			if (x.champion == champion && level >= x.from && level <= x.to)
				return x.pct;
		}
		return 0;
	}

	// ------------------------------------------------------------ the bots

	const int PLAYERBOT_POTEGA_RANGE = 25000;	// 250 m around Uriel: the village and its square
	const int PLAYERBOT_POTEGA_MAX_WALKERS = 6;
	const DWORD PLAYERBOT_POTEGA_CHECK_MIN_MS = 60000;
	const DWORD PLAYERBOT_POTEGA_CHECK_MAX_MS = 180000;
	const DWORD PLAYERBOT_POTEGA_GIVE_UP_MS = 120000;

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
	// The bots on the way (pid, start); a bot that logs out on the way drops off after PLAYERBOT_POTEGA_GIVE_UP_MS.
	std::vector<std::pair<DWORD, DWORD> > s_walkers;

	int Walkers(DWORD dwNow)
	{
		for (size_t i = 0; i < s_walkers.size();)
		{
			if (dwNow - s_walkers[i].second > PLAYERBOT_POTEGA_GIVE_UP_MS + 5000)
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
	unsigned int s_uTaken = 0, s_uGoing = 0, s_uGaveUp = 0, s_uCapped = 0;
	DWORD s_dwCensusAt = 0;

	void Census(DWORD dwNow)
	{
		if (s_dwCensusAt == 0)
		{
			s_dwCensusAt = dwNow;
			return;
		}
		if (dwNow - s_dwCensusAt < 600000)
			return;
		s_dwCensusAt = dwNow;
		sys_log(0, "PLAYERBOT_POTEGA: census event=%d tiers=%u minutes=%d bots=%d share=%d walking=%d going=%u taken=%u gave_up=%u capped=%u",
				IsEventOn() ? 1 : 0, (unsigned)s_cfg.tiers.size(), s_cfg.minutes, s_cfg.bots, s_cfg.botShare, Walkers(dwNow),
				s_uGoing, s_uTaken, s_uGaveUp, s_uCapped);
	}

	LPCHARACTER FindUriel(LPCHARACTER ch, DWORD vid)
	{
		if (vid)
		{
			LPCHARACTER npc = CHARACTER_MANAGER::instance().Find(vid);
			if (npc && npc->GetRaceNum() == URIEL_VNUM && npc->GetMapIndex() == ch->GetMapIndex())
				return npc;
		}
		CharacterVectorInteractor found;
		if (!CHARACTER_MANAGER::instance().GetCharactersByRaceNum(URIEL_VNUM, found))
			return NULL;
		LPCHARACTER best = NULL;
		int bestDist = PLAYERBOT_POTEGA_RANGE + 1;
		for (CharacterVectorInteractor::iterator it = found.begin(); it != found.end(); ++it)
		{
			LPCHARACTER npc = *it;
			if (!npc || !npc->IsNPC() || npc->GetMapIndex() != ch->GetMapIndex())
				continue;
			const int dist = DISTANCE_APPROX(ch->GetX() - npc->GetX(), ch->GetY() - npc->GetY());
			if (dist < bestDist)
			{
				bestDist = dist;
				best = npc;
			}
		}
		return best;
	}

	void EndVisit(DWORD pid, TVisit& v, TPlayerBotAIState& state, DWORD dwNow, bool clearRoute)
	{
		if (v.walking)
			DropWalker(pid);
		v.walking = false;
		v.actionAt = 0;
		v.npcVid = 0;
		v.nextCheck = dwNow + number(PLAYERBOT_POTEGA_CHECK_MIN_MS, PLAYERBOT_POTEGA_CHECK_MAX_MS);
		if (clearRoute)
			ClearPlayerBotRoute(state, true);
	}

	// The affect itself - the quest's affect.add_new(730, 127, pct, minutes * 60, 0, true).
	void Give(LPCHARACTER ch, int pct)
	{
		ch->AddAffect(AFFECT_POTEGA_MADROSCI, POINT_RAMADAN_CANDY_BONUS_EXP, pct, AFF_NONE, s_cfg.minutes * 60, 0, true);
	}
}

// The tick (playerbot_manager.cpp, before the town linger and the world travel). True while it owns the tick.
bool ManagePlayerBotPotega(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
{
	using namespace mt2009_potega;
	if (!ch || !ch->IsItemLoaded())
		return false;
	TVisit& v = s_visits[ch->GetPlayerID()];
	if (!v.walking)
	{
		if (v.nextCheck == 0)
		{
			// The first look staggered by the pid, so a core's bots never ask together after a start.
			v.nextCheck = dwNow + PLAYERBOT_POTEGA_CHECK_MIN_MS + (ch->GetPlayerID() * 7919U) % PLAYERBOT_POTEGA_CHECK_MAX_MS;
			return false;
		}
		if (dwNow < v.nextCheck)
			return false;
		v.nextCheck = dwNow + number(PLAYERBOT_POTEGA_CHECK_MIN_MS, PLAYERBOT_POTEGA_CHECK_MAX_MS);
		ReadConfig(dwNow);
		Census(dwNow);
		if (!s_cfg.bots || !IsEventOn() || ch->FindAffect(AFFECT_POTEGA_MADROSCI))
			return false;
		// The share: a stable pick by the pid, the same bots every time.
		if ((int)((ch->GetPlayerID() * 2654435761U) >> 16) % 100 >= s_cfg.botShare)
			return false;
		// Only a bot that goes out to hunt: no stall, no fishing, no fight, nobody's company.
		if (ch->GetMyShop() || state.bFishingSession || state.bMarketTrip || state.bVisitingShop ||
				state.bVisitingBiologist || state.bVisitingHerbalist || state.bVisitingStable || state.bVisitingAlchemist ||
				state.bVisitingUriel || state.bCraftErrand != 0 || state.bWorldEventKind != 0 ||
				ch->GetVictim() != NULL || state.dwTargetVID != 0 ||
				(ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())) || IsPlayerBotHeldForCompany(ch))
			return false;
		const int pct = PercentFor(ch);
		if (pct <= 0)
			return false;
		LPCHARACTER uriel = FindUriel(ch, 0);
		if (!uriel)
			return false;
		if (Walkers(dwNow) >= PLAYERBOT_POTEGA_MAX_WALKERS)
		{
			++s_uCapped;
			v.nextCheck = dwNow + number(20000, 45000);
			return false;
		}
		s_walkers.push_back(std::make_pair(ch->GetPlayerID(), dwNow));
		++s_uGoing;
		v.walking = true;
		v.startedAt = dwNow;
		v.actionAt = 0;
		v.npcVid = uriel->GetVID();
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		ch->Stop();
		ClearPlayerBotRoute(state, true);
		sys_log(0, "PLAYERBOT_POTEGA: going pid=%u name=%s lv=%d champion=%d map=%ld pct=%d dist=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), (int)ch->GetConquerorLevel(), ch->GetMapIndex(), pct,
				DISTANCE_APPROX(ch->GetX() - uriel->GetX(), ch->GetY() - uriel->GetY()));
	}

	// On the way: anything real takes the bot back (another errand, a fight, a person's party), and a walk that
	// lasts too long is given up.
	LPCHARACTER uriel = FindUriel(ch, v.npcVid);
	if (!uriel || !IsEventOn() || ch->GetVictim() != NULL || state.bVisitingShop || state.bVisitingUriel ||
			state.bVisitingAlchemist || state.bFishingSession || state.bWorldEventKind != 0 ||
			(ch->GetParty() && IsPlayerBotHumanLedParty(ch->GetParty())) || dwNow - v.startedAt > PLAYERBOT_POTEGA_GIVE_UP_MS)
	{
		++s_uGaveUp;
		sys_log(0, "PLAYERBOT_POTEGA: gave up pid=%u name=%s map=%ld uriel=%d event=%d after=%ums",
				ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), uriel ? 1 : 0, IsEventOn() ? 1 : 0, dwNow - v.startedAt);
		EndVisit(ch->GetPlayerID(), v, state, dwNow, true);
		return false;
	}
	SetPlayerBotAction(state, BOT_ACTION_SHOP, dwNow);
	state.dwTargetVID = 0;

	long approachX = 0, approachY = 0;
	GetPlayerBotNpcApproach(ch->GetPlayerID(), uriel->GetX(), uriel->GetY(), 0x504F5445U, approachX, approachY);
	if (DISTANCE_APPROX(ch->GetX() - approachX, ch->GetY() - approachY) > 650)
	{
		if (!MovePlayerBot(ch, approachX, approachY, dwNow, 20, true, true, false, true) && state.bStuckCounter >= 6)
		{
			++s_uGaveUp;
			sys_err("PLAYERBOT_POTEGA: route to Uriel failed pid=%u name=%s map=%ld from=(%ld,%ld)",
					ch->GetPlayerID(), ch->GetName(), ch->GetMapIndex(), ch->GetX(), ch->GetY());
			EndVisit(ch->GetPlayerID(), v, state, dwNow, true);
			return false;
		}
		return true;
	}

	ch->Stop();
	ch->SetPosition(POS_STANDING);
	if (v.actionAt == 0)
	{
		v.actionAt = dwNow + number(2000, 5000);	// "talks" to him a moment
		return true;
	}
	if (dwNow < v.actionAt)
		return true;

	ReadConfig(dwNow);
	const int pct = PercentFor(ch);
	if (pct > 0 && !ch->FindAffect(mt2009_potega::AFFECT_POTEGA_MADROSCI))
	{
		Give(ch, pct);
		++s_uTaken;
		sys_log(0, "PLAYERBOT_POTEGA: taken pid=%u name=%s lv=%d champion=%d map=%ld pct=%d minutes=%d",
				ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), (int)ch->GetConquerorLevel(), ch->GetMapIndex(), pct,
				s_cfg.minutes);
	}
	EndVisit(ch->GetPlayerID(), v, state, dwNow, true);
	return false;
}

#endif
