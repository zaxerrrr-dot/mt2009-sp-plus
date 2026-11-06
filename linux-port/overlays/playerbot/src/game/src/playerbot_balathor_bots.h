#ifndef __INC_METIN2_PLAYERBOT_BALATHOR_BOTS_H__
#define __INC_METIN2_PLAYERBOT_BALATHOR_BOTS_H__

// MT2009_PLUS_BOT_BALATHOR_V1 - the bot guilds go into Krypta Balathora (map 420, the guild lair of the White Dragon,
// MT2009_PLUS_BALATHOR_V1 - author dracaryS; balathor.cpp / balathor_manager.cpp / krypta_balathora.quest) and a person's
// guild bots go in with the person ("nauczmy boty korzystac z dungeonow Yohary", the owner, 5 November 2026).
//
// The registration a bot guild meets - the quest's own rules, none waived (the quest itself counts people only, so a
// bot guild is registered here, at Straznik Smokow Dolnarr, the way the quest's register() does it):
//   * the guild: level register_min_guild_level (21, balathor.json), at least 24 h old (guildsys create_time), the
//     ladder points (600, taken), a treasury of 500 000 Yang that may be spent (checked, not taken - the master pays in
//     what it lacks from its own spare gold, the guild's deposit), no Krypta open, out of its 3 h break (the guild flags
//     balathor_channel / balathor_cooldown, set as the quest sets them), and the guild SP for five Hwacha shots;
//   * the master a bot standing here, and 4-16 of its bots (the master among them): level 120, Champion 4, 24 h in the
//     guild (guildsys join_time), free (GetPlayerBotLfgRefusal), no other run, not a Yohara cohort member;
//   * one Krypta of bots at a time on a core (PLAYERBOT_BALATHOR_MAX in the .env, 1; 0 = off), and the DUNGEONS switch
//     of the bots' dungeon runs (IsPlayerBotDgRunOn).
// The run:
//   * the gathering at Dolnarr on Gora Sohan (balathor.json enter_base_pos) - the map change every move of the AI is,
//     and the walk; everybody there, or PLAYERBOT_BALATHOR_GATHER_MS with the master and the minimum: registered
//     (CBalathorManager::Create for the master), every one there into the guild's Krypta at its base_pos (WarpBot, as
//     balathor.teleport does), the way out set to Dolnarr; the master starts the fight after a breath (the NPC's
//     "Zaczynamy": SetStage(RUN));
//   * inside, what a player does at each step: the gate, the waves, the Ice Crystal, the ice walls and the frozen
//     eggs; at the first Balathor the Fire Eggs are pushed into their arrows (a hit of the player's knock-back, the
//     slide the client would sync - the egg is never struck: a broken one counts against the guild), the Fire Arrows
//     the monsters drop picked up and loaded (the item's use), the Hwacha fired by the master (the click's
//     use_hwatcha, guild SP and all) and repaired when broken, the dragon eggs it unfreezes broken; the hidden Balathor
//     fought, its Frozen Eggs first; the ice's polymorph ended at once (the space bar's /balathor unpoly); the reward
//     at the treasure (claim_reward - every member inside). The first Balathor is never struck - only the Hwacha
//     hurts him; nor the Hwacha, the treasure, the guide, a blocked egg or wall;
//   * out by the module's own send-off (ExitAll's WarpSet), or - after it or PLAYERBOT_BALATHOR_LIMIT_MS - here.
// A person's party: a bot of the person's guild, level 120 and Champion 4, follows the person in
// (playerbot_party_dungeon.h) and fights by the rules above (the targets, the polymorph, the arrows).
//
// The log: PLAYERBOT_BALATHOR lines - census (why the bot guilds cannot go), deposit, called, gathered, registered,
// started, hwacha, reached, reward, finished, out.
//
// MT2009_PLUS_BALATHOR_BOT_PARTY_V1 - the bots' own way in (the owner, 6 November 2026: "Zmiana dla botow, boty nie
// musza byc w tej samej gildii, nie sa pobierane punkty gildii, musza spelnic tylko LVL postaci i ilosc osob w PT").
// Next to the guilds' way above, a PARTY of playerbots - led by a playerbot, every member a playerbot, of any guild or
// none - goes in on the characters' level (register_min_level 120 and Champion 4, the quest's member_ok) and the
// party's size (register_min_member_count 4 .. a party's 8 members) only: no guild level/age, no master, no ladder
// points, no treasury, no guild SP for the Hwacha, no guild cooldown (CBalathorManager::CreateForBotParty - a Krypta
// keyed by the runner, not by a guild). People keep every rule of krypta_balathora.quest; the Krypta itself (its
// monsters, Balathor, the Hwacha's arrows, the time limit, the chests) is the same.
//   * the pool: the free fit bots of this core, by kingdom (a party is one kingdom's), the strongest first
//     (ScorePlayerBotYdg); a party is made at Dolnarr (a CParty, the leader's), the members get the YDG run's bonuses
//     for the hour (BuffPlayerBotYdgMember - the bots stronger, the Krypta unchanged) and a bag cell for the chests;
//   * the inside: every step as for a guild's run above (the leader fires the Hwacha), the reward for every bot in it;
//   * the operator: the file playerbot_balathor_train in the core's directory (read when it changed, every 30 s):
//         parties <n> [size]   n party runs at once (0-20), parties of size (4-8, default 8); a short rest after a run
//         # ...                a comment
//     Without it: PLAYERBOT_BALATHOR_PARTIES (.env, default 1) party runs at once, size 8, a member's 3 h rest. The
//     DUNGEONS switch of the bots' dungeon runs (IsPlayerBotDgRunOn) stops new calls.
//   * the log: PLAYERBOT_BALATHOR lines (train, party census, party called, party made, registered ... finished) and
//     BOT_DGRUN lines with dungeon=balathor (entered, stage, closed) as for every bots' dungeon run.
//
// An implementation fragment: included by playerbot_manager.cpp after playerbot_labirynt_bots.h.

#ifdef __BALATHOR__
#include "balathor.h"
#endif
#include "guildsys.h"

namespace
{
	// playerbot_yohara_sungma.h, later.
	int GetPlayerBotChampionLevel(LPCHARACTER ch);

	const long PLAYERBOT_BALATHOR_MAP = 420;
	const int PLAYERBOT_BALATHOR_CHAMPION_MIN = 4;		// krypta_balathora.quest member_ok
	const long long PLAYERBOT_BALATHOR_BANK_MIN = 500000LL;	// krypta_balathora.quest bank_min
	const int PLAYERBOT_BALATHOR_GUILD_HOURS = 24;
	const int PLAYERBOT_BALATHOR_MEMBER_HOURS = 24;
	const int PLAYERBOT_BALATHOR_HWACHA_SHOTS = 5;		// 20% of the first Balathor a shot
	const DWORD PLAYERBOT_BALATHOR_PLAN_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_BALATHOR_FIRST_PLAN_MS = 10 * 60 * 1000;
	const DWORD PLAYERBOT_BALATHOR_CENSUS_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_BALATHOR_GATHER_MS = 4 * 60 * 1000;
	const DWORD PLAYERBOT_BALATHOR_GATHER_MAX_MS = 7 * 60 * 1000;
	const DWORD PLAYERBOT_BALATHOR_START_MS = 20 * 1000;
	const DWORD PLAYERBOT_BALATHOR_LIMIT_MS = 75 * 60 * 1000;
	const DWORD PLAYERBOT_BALATHOR_OUT_GRACE_MS = 90 * 1000;	// after the close: the module's send-off is 60 s
	const DWORD PLAYERBOT_BALATHOR_NONE_INSIDE_MS = 3 * 60 * 1000;
	const DWORD PLAYERBOT_BALATHOR_UNPOLY_MS = 1500;
	const DWORD PLAYERBOT_BALATHOR_PUSH_MS = 1200;
	const int PLAYERBOT_BALATHOR_PUSH_STEP = 350;
	const int PLAYERBOT_BALATHOR_ARROW_RANGE = 1500;
	const int PLAYERBOT_BALATHOR_HWACHA_RANGE = 400;
	const int PLAYERBOT_BALATHOR_SPOT_RANGE = 350;
	const DWORD PLAYERBOT_BALATHOR_REST_MS = 3 * 60 * 60 * 1000;	// a member's own break after a run
	// MT2009_PLUS_BALATHOR_BOT_PARTY_V1
	const DWORD PLAYERBOT_BALATHOR_TRAIN_REST_MIN_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_BALATHOR_TRAIN_REST_SPREAD_MS = 2 * 60 * 1000;
	const DWORD PLAYERBOT_BALATHOR_TRAIN_PLAN_MS = 20 * 1000;
	const DWORD PLAYERBOT_BALATHOR_FILE_MS = 30 * 1000;
	const int PLAYERBOT_BALATHOR_PARTY_SIZE_MAX = 8;	// PARTY_MAX_MEMBER
	const int PLAYERBOT_BALATHOR_PARTY_CALLS_A_PASS = 2;
	const int PLAYERBOT_BALATHOR_DGRUN_ID_BASE = 90000;	// the BOT_DGRUN lines' run=, apart from the dungeon runs' ids
	const char* const PLAYERBOT_BALATHOR_TRAIN_FILE = "playerbot_balathor_train";

	enum EPlayerBotBalathorPhase
	{
		BALATHOR_BOT_GATHER = 1,
		BALATHOR_BOT_INSIDE,
	};

	struct TPlayerBotBalathorRun
	{
		DWORD dwGuild;	// the guild's id - or, for a bot party (bParty), the Krypta's key (CBalathorManager::IsBotPartyKey)
		std::string strGuild;
		DWORD dwMaster;
		std::vector<DWORD> members;	// the master first
		std::set<DWORD> arrived;
		BYTE bPhase;
		DWORD dwCalledAt, dwPhaseSince, dwStartAt, dwClosedAt, dwNoneInsideSince, dwNextGunner;
		long lInstance;
		bool bStarted, bClaimed;
		int iReached, iClaim, iShots, iPushes;
		// MT2009_PLUS_BALATHOR_BOT_PARTY_V1: a bot party's run (no guild; dwMaster is the party's leader)
		bool bParty, bTrain;
		int iRunId;
		BYTE bEmpire;
		TPlayerBotBalathorRun() : dwGuild(0), dwMaster(0), bPhase(BALATHOR_BOT_GATHER), dwCalledAt(0), dwPhaseSince(0),
				dwStartAt(0), dwClosedAt(0), dwNoneInsideSince(0), dwNextGunner(0), lInstance(0), bStarted(false),
				bClaimed(false), iReached(0), iClaim(-1), iShots(0), iPushes(0), bParty(false), bTrain(false), iRunId(0),
				bEmpire(0) {}
	};
	struct TPlayerBotBalathorBot
	{
		DWORD dwGuild;
		DWORD dwNextMove, dwNextUse, dwNextPush;
		bool bTrain;	// MT2009_PLUS_BALATHOR_BOT_PARTY_V1: a training run's member - a short rest after it
		TPlayerBotBalathorBot() : dwGuild(0), dwNextMove(0), dwNextUse(0), dwNextPush(0), bTrain(false) {}
	};
	std::map<DWORD, TPlayerBotBalathorRun> s_mapPlayerBotBalathorRuns;	// by guild id
	std::map<DWORD, TPlayerBotBalathorBot> s_mapPlayerBotBalathorBots;	// by pid
	std::map<DWORD, DWORD> s_mapPlayerBotBalathorRest;			// pid -> no run before
	// Every bot standing in a Krypta (a run's or a person's party's) and since when polymorphed: the module's own player
	// list (CBalathor::Login / Logout - a bot comes in by WarpBot, not by a login).
	std::map<DWORD, long> s_mapPlayerBotBalathorPresence;
	std::map<DWORD, DWORD> s_mapPlayerBotBalathorPolySince;
	unsigned int s_uPlayerBotBalathorCalled = 0, s_uPlayerBotBalathorRegistered = 0, s_uPlayerBotBalathorRewards = 0;
	// MT2009_PLUS_BALATHOR_BOT_PARTY_V1: the party runs' keys and ids, the train file, the counters.
	DWORD s_dwPlayerBotBalathorPartyKey = 0;
	int s_iPlayerBotBalathorPartyRunId = 0;
	struct TPlayerBotBalathorTrain
	{
		int parties;	// 0: no training (PLAYERBOT_BALATHOR_PARTIES)
		int size;
		TPlayerBotBalathorTrain() : parties(0), size(PLAYERBOT_BALATHOR_PARTY_SIZE_MAX) {}
	};
	TPlayerBotBalathorTrain s_kPlayerBotBalathorTrain;
	unsigned int s_uPlayerBotBalathorPartyCalled = 0, s_uPlayerBotBalathorPartyEntered = 0, s_uPlayerBotBalathorPartyWon = 0;

	bool IsPlayerBotOnBalathorRun(DWORD pid)
	{
		return !s_mapPlayerBotBalathorBots.empty() && s_mapPlayerBotBalathorBots.count(pid) != 0;
	}

#ifdef __BALATHOR__
	bool IsPlayerBotBalathorOn()
	{
		const SBalathorConfig& cfg = CBalathorManager::Instance().GetConfig();
		return cfg.dwMapIndex != 0 && map_allow_find(cfg.dwMapIndex) && cfg.dwEnterMapIndex != 0 &&
				IsPlayerBotMapHostedHere(cfg.dwEnterMapIndex) && SECTREE_MANAGER::instance().GetMap(cfg.dwMapIndex);
	}

	bool IsPlayerBotBalathorInstance(long mapIndex)
	{
		return mapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN && mapIndex / 10000 == PLAYERBOT_BALATHOR_MAP &&
				CBalathorManager::Instance().FindByMapIndex((DWORD)mapIndex) != NULL;
	}

	bool IsPlayerBotBalathorFitMember(LPCHARACTER ch)
	{
		const SBalathorConfig& cfg = CBalathorManager::Instance().GetConfig();
		return ch && (int)ch->GetLevel() >= (int)cfg.bRegisterMinLevel &&
				GetPlayerBotChampionLevel(ch) >= PLAYERBOT_BALATHOR_CHAMPION_MIN;
	}

	// A person's party bot into the Krypta: of the guild whose Krypta it is, fit by the entry's rule.
	bool IsPlayerBotBalathorPartyFit(LPCHARACTER ch, long targetMap)
	{
		if (!ch || !ch->GetGuild() || !IsPlayerBotBalathorFitMember(ch))
			return false;
		CBalathor* own = CBalathorManager::Instance().FindByGID(ch->GetGuild()->GetID());
		return own && (targetMap < PLAYERBOT_INSTANCE_MAP_INDEX_MIN || (long)own->GetMapIndex() == targetMap);
	}

	// What a bot never strikes in a Krypta: the Fire Eggs (a broken one counts against the guild), the Hwacha, the
	// treasure, the guide, the first Balathor (only the Hwacha hurts him), and an egg or a wall the module blocks.
	bool IsPlayerBotBalathorNoTarget(LPCHARACTER c)
	{
		if (!c || c->GetMapIndex() < PLAYERBOT_INSTANCE_MAP_INDEX_MIN || c->GetMapIndex() / 10000 != PLAYERBOT_BALATHOR_MAP)
			return false;
		const SBalathorConfig& cfg = CBalathorManager::Instance().GetConfig();
		const DWORD race = c->GetRaceNum();
		return race == cfg.dwFlamingEggVnum || race == cfg.dwHwachaVnum || race == cfg.dwChestVnum || race == cfg.dwNPCVnum ||
				race == cfg.dwBossVnum1 || c->GetBlockStatus();
	}

	// The module's player list kept for the bots, the polymorph ended, the arrows of a Krypta gone with it.
	void SyncPlayerBotBalathorPresence(LPCHARACTER ch, DWORD dwNow)
	{
		const DWORD pid = ch->GetPlayerID();
		const long map = ch->GetMapIndex();
		const bool inside = map >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN && map / 10000 == PLAYERBOT_BALATHOR_MAP;
		std::map<DWORD, long>::iterator p = s_mapPlayerBotBalathorPresence.find(pid);
		if (p != s_mapPlayerBotBalathorPresence.end() && p->second != map)
		{
			CBalathor* old = CBalathorManager::Instance().FindByMapIndex((DWORD)p->second);
			if (old)
				old->Logout(ch);
			const SBalathorConfig& cfg = CBalathorManager::Instance().GetConfig();
			const DWORD arrows = cfg.dwFireArrowVnum ? ch->CountSpecifyItem(cfg.dwFireArrowVnum) : 0;
			if (arrows)
				ch->RemoveSpecifyItem(cfg.dwFireArrowVnum, arrows);
			s_mapPlayerBotBalathorPresence.erase(p);
			s_mapPlayerBotBalathorPolySince.erase(pid);
			p = s_mapPlayerBotBalathorPresence.end();
		}
		if (!inside)
			return;
		CBalathor* here = CBalathorManager::Instance().FindByMapIndex((DWORD)map);
		if (!here)
			return;
		if (p == s_mapPlayerBotBalathorPresence.end())
		{
			here->Login(ch);
			s_mapPlayerBotBalathorPresence[pid] = map;
		}
		// The ice's polymorph: the space bar's /balathor unpoly, a breath later.
		CAffect* poly = ch->FindAffect(AFFECT_POLYMORPH);
		if (poly && poly->lApplyValue == (long)CBalathorManager::Instance().GetConfig().dwIceCrystalVnum)
		{
			DWORD& since = s_mapPlayerBotBalathorPolySince[pid];
			if (since == 0)
				since = dwNow;
			else if (dwNow - since >= PLAYERBOT_BALATHOR_UNPOLY_MS)
			{
				here->UnPoly(ch);
				s_mapPlayerBotBalathorPolySince.erase(pid);
			}
		}
		else
			s_mapPlayerBotBalathorPolySince.erase(pid);
	}

	bool IsPlayerBotBalathorCandidate(LPCHARACTER ch, const TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || ch->IsDead() || !IsPlayerBotBalathorFitMember(ch))
			return false;
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, DWORD>::const_iterator rest = s_mapPlayerBotBalathorRest.find(pid);
		if (rest != s_mapPlayerBotBalathorRest.end() && (int)(dwNow - rest->second) < 0)
			return false;
		if (IsPlayerBotOnBalathorRun(pid) || IsPlayerBotOnDungeonRun(pid) || IsPlayerBotYoharaCohortPID(pid))
			return false;
		return GetPlayerBotLfgRefusal(ch, state, dwNow) == NULL;
	}

	void GetPlayerBotBalathorSpot(const TPlayerBotBalathorRun& run, DWORD pid, long& x, long& y)
	{
		const SBalathorConfig& cfg = CBalathorManager::Instance().GetConfig();
		size_t i = 0;
		while (i < run.members.size() && run.members[i] != pid)
			++i;
		static const int kRing[8][2] = { { 200, 0 }, { 141, 141 }, { 0, 200 }, { -141, 141 }, { -200, 0 }, { -141, -141 },
				{ 0, -200 }, { 141, -141 } };
		const int r = 1 + (int)(i / 8);
		x = cfg.enter_base_pos.lGX + kRing[i % 8][0] * r;
		y = cfg.enter_base_pos.lGY + kRing[i % 8][1] * r;
	}

	void ReleasePlayerBotBalathorMember(DWORD pid, const char* why, DWORD dwNow)
	{
		std::map<DWORD, TPlayerBotBalathorBot>::iterator b = s_mapPlayerBotBalathorBots.find(pid);
		if (b == s_mapPlayerBotBalathorBots.end())
			return;
		const bool train = b->second.bTrain;
		s_mapPlayerBotBalathorBots.erase(b);
		s_mapPlayerBotBalathorRest[pid] = dwNow + (train ? PLAYERBOT_BALATHOR_TRAIN_REST_MIN_MS +
				(DWORD)number(0, (int)PLAYERBOT_BALATHOR_TRAIN_REST_SPREAD_MS) : PLAYERBOT_BALATHOR_REST_MS);
		if (why)
			sys_log(0, "PLAYERBOT_BALATHOR: member out pid=%u why=%s", pid, why);
	}

	const char* GetPlayerBotBalathorReachedName(int reached)
	{
		static const char* names[] = { "-", "gate", "waves", "crystal", "walls", "balathor", "hidden_balathor", "treasure" };
		return reached >= 0 && reached <= 7 ? names[reached] : "?";
	}

	void EndPlayerBotBalathorRun(TPlayerBotBalathorRun& run, const char* result, DWORD dwNow)
	{
		sys_log(0, "PLAYERBOT_BALATHOR: finished guild=%s gid=%u result=%s reached=%s claim=%d shots=%d pushes=%d members=%u took_s=%u",
				run.strGuild.c_str(), run.dwGuild, result, GetPlayerBotBalathorReachedName(run.iReached), run.iClaim,
				run.iShots, run.iPushes, (unsigned int)run.members.size(), (dwNow - run.dwCalledAt) / 1000);
		const std::vector<DWORD> members = run.members;
		// MT2009_PLUS_BALATHOR_BOT_PARTY_V1: the run's line as every bots' dungeon run's, and its party let go.
		if (run.bParty)
		{
			if (run.iClaim == 99)
				++s_uPlayerBotBalathorPartyWon;
			sys_log(0, "BOT_DGRUN: closed run=%d dungeon=balathor instance=%ld empire=%u result=%s took_s=%u stage=%d stage_s=%s "
					"members=%u leader=%u train=%d",
					run.iRunId, run.lInstance, (unsigned int)run.bEmpire, result, (dwNow - run.dwCalledAt) / 1000, run.iReached,
					GetPlayerBotBalathorReachedName(run.iReached), (unsigned int)members.size(), run.dwMaster, run.bTrain ? 1 : 0);
			LPCHARACTER leader = CHARACTER_MANAGER::instance().FindByPID(run.dwMaster);
			LPPARTY party = leader ? leader->GetParty() : NULL;
			if (party && party->GetLeaderPID() == run.dwMaster && !IsPlayerBotHumanLedParty(party))
				CPartyManager::instance().DeleteParty(party);
		}
		for (size_t i = 0; i < members.size(); ++i)
			ReleasePlayerBotBalathorMember(members[i], NULL, dwNow);
	}

	// MT2009_PLUS_BALATHOR_BOT_PARTY_V1: the bot party made at Dolnarr - the leader's own party (not one it happened to be
	// in), every member a playerbot of the leader's kingdom, fit and standing there. The members in it.
	int MakePlayerBotBalathorParty(TPlayerBotBalathorRun& run, LPCHARACTER leader)
	{
		LPPARTY party = leader->GetParty();
		if (party)
			LeavePlayerBotParty(leader);
		party = CPartyManager::instance().CreateParty(leader);
		if (!party)
			return 0;
		party->Link(leader);
		party->SetParameter(PARTY_EXP_DISTRIBUTION_PARITY);
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			if (run.members[i] == run.dwMaster || !run.arrived.count(run.members[i]))
				continue;
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (!ch || ch->IsDead() || !ch->GetDesc() || !ch->GetDesc()->IsBot() || ch->GetEmpire() != leader->GetEmpire() ||
					!IsPlayerBotBalathorFitMember(ch) || party->GetMemberCount() >= (DWORD)PLAYERBOT_BALATHOR_PARTY_SIZE_MAX)
				continue;
			if (ch->GetParty())
				LeavePlayerBotParty(ch);
			party->Join(ch->GetPlayerID());
			party->Link(ch);
		}
		sys_log(0, "PLAYERBOT_BALATHOR: party made run=%d leader=%s members=%u", run.iRunId, leader->GetName(),
				(unsigned int)party->GetMemberCount());
		return (int)party->GetMemberCount();
	}

	// MT2009_PLUS_BALATHOR_BOT_PARTY_V1: the bots' own registration - the characters' level and the party's size only.
	const char* RegisterPlayerBotBalathorParty(TPlayerBotBalathorRun& run, LPCHARACTER leader)
	{
		const SBalathorConfig& cfg = CBalathorManager::Instance().GetConfig();
		if (!leader || leader->IsDead() || !leader->GetDesc() || !leader->GetDesc()->IsBot() || !IsPlayerBotBalathorFitMember(leader))
			return "leader";
		const int size = MakePlayerBotBalathorParty(run, leader);
		LPPARTY party = leader->GetParty();
		if (!party || size < (int)cfg.bRegisterMinMemberCount)
			return "party_size";
		// Every member of the party a playerbot (the bots' path only), each fit.
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (ch && ch->GetParty() == party && (!ch->GetDesc() || !ch->GetDesc()->IsBot() || !IsPlayerBotBalathorFitMember(ch)))
				return "member";
		}
		if (IsPlayerBotHumanLedParty(party))
			return "person";
		const BYTE r = CBalathorManager::Instance().CreateForBotParty(leader, run.dwGuild);
		return r == 99 ? NULL : (r == 1 ? "open" : "create");
	}

	// The quest's register() for a bot guild, and balathor.teleport for those at Dolnarr.
	bool RegisterPlayerBotBalathorRun(TPlayerBotBalathorRun& run, DWORD dwNow)
	{
		const SBalathorConfig& cfg = CBalathorManager::Instance().GetConfig();
		LPCHARACTER master = CHARACTER_MANAGER::instance().FindByPID(run.dwMaster);
		CGuild* guild = master ? master->GetGuild() : NULL;
		const char* why = NULL;
		if (run.bParty)
		{
			why = RegisterPlayerBotBalathorParty(run, master);
			if (why)
			{
				sys_log(0, "PLAYERBOT_BALATHOR: registration refused party run=%d leader=%s why=%s", run.iRunId,
						master ? master->GetName() : "?", why);
				return false;
			}
		}
		else if (!master || !guild || guild->GetID() != run.dwGuild || guild->GetMasterPID() != run.dwMaster)
			why = "master";
		else if (guild->GetFlag("balathor_channel") != 0 || CBalathorManager::Instance().CanCreate(master) != 99)
			why = "open";
		else if ((DWORD)guild->GetLadderPoint() < cfg.dwRegisterLadderPoint)
			why = "ladder";
		else if ((long long)guild->GetGuildMoneyAvailable() < PLAYERBOT_BALATHOR_BANK_MIN)
			why = "treasury";
		if (why)
		{
			sys_log(0, "PLAYERBOT_BALATHOR: registration refused guild=%s gid=%u why=%s", run.strGuild.c_str(), run.dwGuild, why);
			return false;
		}
		if (!run.bParty)
		{
			if (cfg.dwRegisterLadderPoint > 0)
				guild->ChangeLadderPoint(-(int)cfg.dwRegisterLadderPoint);
			guild->SetFlag("balathor_channel", g_bChannel);
			guild->SetFlag("balathor_cooldown", get_global_time() + cfg.dwRegisterWaitTime);
			if (CBalathorManager::Instance().Create(master) != 99)
			{
				guild->SetFlag("balathor_channel", 0);
				sys_log(0, "PLAYERBOT_BALATHOR: registration refused guild=%s gid=%u why=create", run.strGuild.c_str(), run.dwGuild);
				return false;
			}
		}
		CBalathor* crypt = CBalathorManager::Instance().FindByGID(run.dwGuild);
		if (!crypt)
			return false;
		run.lInstance = crypt->GetMapIndex();
		++s_uPlayerBotBalathorRegistered;
		int in = 0;
		const std::vector<DWORD> members = run.members;
		LPPARTY party = run.bParty ? master->GetParty() : NULL;
		std::string names;
		for (size_t i = 0; i < members.size(); ++i)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(members[i]);
			TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.find(members[i]);
			if (!ch || ch->IsDead() || st == s_mapPlayerBotAIStates.end() || !run.arrived.count(members[i]))
			{
				ReleasePlayerBotBalathorMember(members[i], "not_at_dolnarr", dwNow);
				continue;
			}
			// MT2009_PLUS_BALATHOR_BOT_PARTY_V1: only the party goes in.
			if (run.bParty && (!party || ch->GetParty() != party))
			{
				ReleasePlayerBotBalathorMember(members[i], "not_in_party", dwNow);
				continue;
			}
			ch->SetWarpLocation(cfg.dwEnterMapIndex, cfg.enter_base_pos.lGX / 100, cfg.enter_base_pos.lGY / 100);
			st->second.dwTargetVID = 0;
			ch->SetVictim(NULL);
			ClearPlayerBotRoute(st->second, true);
			s_szPlayerBotTransitionRefusal = NULL;
			const long x = cfg.base_pos.lGX + (long)(in % 4) * 120 - 180;
			const long y = cfg.base_pos.lGY + (long)(in / 4) * 120;
			if (!CPlayerBotManager::instance().WarpBot(ch, x, y, run.lInstance) || ch->GetMapIndex() != run.lInstance)
			{
				sys_log(0, "PLAYERBOT_BALATHOR: way in refused pid=%u name=%s instance=%ld refused=%s", members[i], ch->GetName(),
						run.lInstance, s_szPlayerBotTransitionRefusal ? s_szPlayerBotTransitionRefusal : "?");
				s_szPlayerBotTransitionRefusal = NULL;
				ReleasePlayerBotBalathorMember(members[i], "way_in_refused", dwNow);
				continue;
			}
			s_szPlayerBotTransitionRefusal = NULL;
			SyncPlayerBotBalathorPresence(ch, dwNow);
			if (run.bParty)
			{
				// the YDG run's bonuses for the hour and a bag cell for the chests - the bots stronger, the Krypta unchanged
				BuffPlayerBotYdgMember(ch);
				MakePlayerBotYdgRoom(ch, "balathor");
				if (!names.empty())
					names += ",";
				names += ch->GetName();
			}
			++in;
		}
		run.members.erase(std::remove_if(run.members.begin(), run.members.end(),
				[](DWORD pid) { return s_mapPlayerBotBalathorBots.count(pid) == 0; }), run.members.end());
		if (run.bParty)
		{
			if (in > 0)
				++s_uPlayerBotBalathorPartyEntered;
			sys_log(0, "PLAYERBOT_BALATHOR: registered party run=%d leader=%s key=%u instance=%ld inside=%d registered_total=%u",
					run.iRunId, master->GetName(), run.dwGuild, run.lInstance, in, s_uPlayerBotBalathorRegistered);
			sys_log(0, "BOT_DGRUN: entered run=%d dungeon=balathor instance=%ld empire=%u members=%d fees=0 names=%s",
					run.iRunId, run.lInstance, (unsigned int)run.bEmpire, in, names.c_str());
		}
		else
			sys_log(0, "PLAYERBOT_BALATHOR: registered guild=%s gid=%u master=%s instance=%ld inside=%d ladder_left=%d treasury=%lld sp=%d registered_total=%u",
					run.strGuild.c_str(), run.dwGuild, master->GetName(), run.lInstance, in, guild->GetLadderPoint(),
					(long long)guild->GetGuildMoneyAvailable(), guild->GetSP(), s_uPlayerBotBalathorRegistered);
		run.bPhase = BALATHOR_BOT_INSIDE;
		run.dwPhaseSince = dwNow;
		run.dwStartAt = dwNow + PLAYERBOT_BALATHOR_START_MS;
		return in > 0;
	}

	// The step the Krypta is at, from what stands there (the module's step index is its own).
	int GetPlayerBotBalathorReached(CBalathor* crypt)
	{
		const SBalathorConfig& cfg = CBalathorManager::Instance().GetConfig();
		if (crypt->GetCharacterByFlag("chest"))
			return 7;
		LPCHARACTER dragon = crypt->GetCharacterByFlag("dragon");
		if (dragon)
			return dragon->GetRaceNum() == cfg.dwBossVnum2 ? 6 : 5;
		if (crypt->GetStage() != BALATHOR_STAGE_RUN)
			return 0;
		if (crypt->GetCharacterByFlag("enter_door"))
			return 1;
		if (crypt->GetCharacterByFlag("ice_crystal"))
			return 3;
		return 2;
	}

	// ------------------------------------------------------------ inside

	bool MovePlayerBotBalathorTo(LPCHARACTER ch, TPlayerBotAIState& state, long x, long y, int range, DWORD dwNow)
	{
		if (DISTANCE_APPROX(ch->GetX() - x, ch->GetY() - y) <= range)
			return false;
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		SetPlayerBotAction(state, BOT_ACTION_TRAVEL, dwNow);
		MovePlayerBot(ch, x, y, dwNow, 6, true, false);
		return true;
	}

	// A Fire Egg pushed toward its arrow: the slide the client syncs after a player's knock-back hit
	// (input_main's fire egg sync), up to a wall.
	bool PushPlayerBotBalathorEgg(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotBalathorBot& b, TPlayerBotBalathorRun* run,
			LPCHARACTER egg, long tx, long ty, DWORD dwNow)
	{
		const long ex = egg->GetX(), ey = egg->GetY();
		const float dx = (float)(tx - ex), dy = (float)(ty - ey);
		const float len = sqrtf(dx * dx + dy * dy);
		if (len < 60.0f)
			return false;
		const long sx = ex - (long)(dx / len * 170.0f), sy = ey - (long)(dy / len * 170.0f);
		if (MovePlayerBotBalathorTo(ch, state, sx, sy, 150, dwNow))
			return true;
		if (ch->IsStateMove())
			ch->Stop();
		SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
		if ((int)(dwNow - b.dwNextPush) < 0)
			return true;
		b.dwNextPush = dwNow + PLAYERBOT_BALATHOR_PUSH_MS;
		LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(egg->GetMapIndex());
		float go = 0.0f;
		const float most = std::min((float)PLAYERBOT_BALATHOR_PUSH_STEP, len);
		for (float step = 25.0f; step <= most; step += 25.0f)
		{
			const long x = ex + (long)(dx / len * step), y = ey + (long)(dy / len * step);
			LPSECTREE cell = pMap ? pMap->Find(x, y) : NULL;
			if (!cell || (cell->GetAttribute(x, y) & ATTR_BLOCK))
				break;
			go = step;
		}
		if (go < 25.0f)
			return true;	// against the wall: the module's check takes it as there
		const long nx = ex + (long)(dx / len * go), ny = ey + (long)(dy / len * go);
		ch->SetRotationToXY(ex, ey);
		egg->Show(egg->GetMapIndex(), nx, ny, 0, false);
		if (run)
			++run->iPushes;
		PlayerBotLogThrottled("balathor_push", dwNow, "PLAYERBOT_BALATHOR: egg pushed pid=%u name=%s egg=%u to=(%ld,%ld) left=%d",
				ch->GetPlayerID(), ch->GetName(), (unsigned int)egg->GetVID(), nx, ny, (int)(len - go));
		return true;
	}

	struct FPlayerBotBalathorArrow
	{
		LPCHARACTER m_me;
		DWORD m_dwVnum;
		LPITEM m_found;
		int m_iBest;
		FPlayerBotBalathorArrow(LPCHARACTER me, DWORD vnum) : m_me(me), m_dwVnum(vnum), m_found(NULL),
				m_iBest(PLAYERBOT_BALATHOR_ARROW_RANGE + 1) {}
		void operator()(LPENTITY ent)
		{
			if (!ent || !ent->IsType(ENTITY_ITEM))
				return;
			LPITEM item = (LPITEM)ent;
			if (!item->GetSectree() || item->GetVnum() != m_dwVnum || item->GetMapIndex() != m_me->GetMapIndex() ||
					!item->IsOwnership(m_me))
				return;
			const int d = DISTANCE_APPROX(item->GetX() - m_me->GetX(), item->GetY() - m_me->GetY());
			if (d < m_iBest)
			{
				m_iBest = d;
				m_found = item;
			}
		}
	};

	// The objective: what the step asks, then what attacks the bot, then the nearest.
	LPCHARACTER PickPlayerBotBalathorFoe(LPCHARACTER ch, TPlayerBotAIState& state, CBalathor* crypt, DWORD dwNow)
	{
		const SBalathorConfig& cfg = CBalathorManager::Instance().GetConfig();
		static const char* firstFlags[] = { "dragon_egg_wave", "enter_door", "dragon_egg_1", "dragon_egg_2", "ice_crystal" };
		for (size_t i = 0; i < sizeof(firstFlags) / sizeof(firstFlags[0]); ++i)
		{
			LPCHARACTER c = crypt->GetCharacterByFlag(firstFlags[i]);
			if (c && !c->IsDead() && !c->GetBlockStatus() && c->GetMapIndex() == ch->GetMapIndex())
				return c;
		}
		const TPlayerBotArzDgScan& scan = ScanPlayerBotArzDg(ch->GetMapIndex(), dwNow);
		LPCHARACTER threat = NULL, near = NULL, boss = NULL;
		int dThreat = INT_MAX, dNear = INT_MAX;
		for (size_t i = 0; i < scan.foes.size(); ++i)
		{
			LPCHARACTER c = CHARACTER_MANAGER::instance().Find(scan.foes[i].dwVID);
			if (!c || c->IsDead() || c->IsPC() || IsPlayerBotBalathorNoTarget(c))
				continue;
			if (c->GetRaceNum() == cfg.dwBossVnum2)
			{
				boss = c;
				continue;
			}
			const int d = DISTANCE_APPROX(ch->GetX() - c->GetX(), ch->GetY() - c->GetY());
			if (c->GetVictim() == ch && d < dThreat)
			{
				threat = c;
				dThreat = d;
			}
			if (d < dNear)
			{
				near = c;
				dNear = d;
			}
		}
		if (threat)
			return threat;
		LPCHARACTER cur = state.dwTargetVID ? CHARACTER_MANAGER::instance().Find(state.dwTargetVID) : NULL;
		if (cur && !cur->IsDead() && cur->GetMapIndex() == ch->GetMapIndex() && !IsPlayerBotBalathorNoTarget(cur) &&
				(cur->IsMonster() || cur->IsStone()))
			return cur;
		return boss ? boss : near;
	}

	bool FightPlayerBotBalathor(LPCHARACTER ch, TPlayerBotAIState& state, TPlayerBotBalathorBot& b, TPlayerBotBalathorRun& run,
			CBalathor* crypt, DWORD dwNow)
	{
		const SBalathorConfig& cfg = CBalathorManager::Instance().GetConfig();
		if (KeepPlayerBotTowerAlive(ch, state, dwNow, 85, 50))
			return true;
		// The arrows it carries into the Hwacha (the item's use).
		if ((int)(dwNow - b.dwNextUse) >= 0 && cfg.dwFireArrowVnum)
		{
			const int cell = FindPlayerBotTowerItemCell(ch, cfg.dwFireArrowVnum);
			if (cell >= 0)
			{
				b.dwNextUse = dwNow + 700;
				ch->UseItem(TItemPos(INVENTORY, (WORD)cell));
				return true;
			}
		}
		const BYTE stage = crypt->GetStage();
		if (stage == BALATHOR_STAGE_WAITING)
		{
			if (MovePlayerBotBalathorTo(ch, state, cfg.base_pos.lGX, cfg.base_pos.lGY, 500, dwNow))
				return true;
			SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
			return true;
		}
		if (stage == BALATHOR_STAGE_CLOSE)
		{
			LPCHARACTER chest = crypt->GetCharacterByFlag("chest");
			if (chest && !run.bClaimed)
			{
				if (MovePlayerBotBalathorTo(ch, state, chest->GetX(), chest->GetY(), 300, dwNow))
					return true;
				run.bClaimed = true;
				run.iClaim = crypt->ClaimReward(ch);
				if (run.iClaim == 99)
					++s_uPlayerBotBalathorRewards;
				sys_log(0, "PLAYERBOT_BALATHOR: reward guild=%s gid=%u by=%s claim=%d rewards_total=%u", run.strGuild.c_str(),
						run.dwGuild, ch->GetName(), run.iClaim, s_uPlayerBotBalathorRewards);
				return true;
			}
			state.dwTargetVID = 0;
			ch->SetVictim(NULL);
			if (ch->IsStateMove())
				ch->Stop();
			SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
			return true;
		}
		if (stage != BALATHOR_STAGE_RUN)
			return true;
		const bool gunner = ch->GetPlayerID() == run.dwMaster ||
				!CHARACTER_MANAGER::instance().FindByPID(run.dwMaster) ||
				CHARACTER_MANAGER::instance().FindByPID(run.dwMaster)->GetMapIndex() != ch->GetMapIndex();
		// The Hwacha: repaired when broken, fired when loaded (the click's revive_hwatcha / use_hwatcha).
		LPCHARACTER hwacha = crypt->GetCharacterByFlag("hwatcha");
		if (hwacha && gunner && (crypt->IsHwatchaDead() || crypt->CanUseHwatcha()))
		{
			if (MovePlayerBotBalathorTo(ch, state, hwacha->GetX(), hwacha->GetY(), PLAYERBOT_BALATHOR_HWACHA_RANGE, dwNow))
				return true;
			if ((int)(dwNow - run.dwNextGunner) >= 0)
			{
				run.dwNextGunner = dwNow + 3000;
				if (crypt->IsHwatchaDead())
				{
					const bool ok = crypt->ReviveHwatcha();
					sys_log(0, "PLAYERBOT_BALATHOR: hwacha repaired guild=%s by=%s ok=%d", run.strGuild.c_str(), ch->GetName(), ok ? 1 : 0);
				}
				else if (crypt->CanUseHwatcha())
				{
					crypt->UseHwatcha();
					++run.iShots;
					CGuild* g = ch->GetGuild();
					sys_log(0, "PLAYERBOT_BALATHOR: hwacha fired guild=%s by=%s shot=%d arrows_left=%u guild_sp=%d",
							run.strGuild.c_str(), ch->GetName(), run.iShots, crypt->GetFlag("fire_arrow_count"), g ? g->GetSP() : -1);
				}
			}
			return true;
		}
		// The Fire Eggs into their arrows: the run's second and third (the master fires).
		LPCHARACTER fire1 = crypt->GetCharacterByFlag("flaming_egg_1");
		LPCHARACTER fire2 = crypt->GetCharacterByFlag("flaming_egg_2");
		if (fire1 || fire2)
		{
			int slot = 0;
			for (size_t i = 0, n = 0; i < run.members.size(); ++i)
			{
				LPCHARACTER m = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
				if (!m || m->IsDead() || m->GetMapIndex() != ch->GetMapIndex() || run.members[i] == run.dwMaster)
					continue;
				++n;
				if (run.members[i] == ch->GetPlayerID())
				{
					slot = (int)n;
					break;
				}
			}
			if (slot == 1 && fire1 && PushPlayerBotBalathorEgg(ch, state, b, &run, fire1, cfg.boss_1_egg_pos1.lGX,
					cfg.boss_1_egg_pos1.lGY, dwNow))
				return true;
			if ((slot == 2 || (slot == 1 && !fire1)) && fire2 && PushPlayerBotBalathorEgg(ch, state, b, &run, fire2,
					cfg.boss_1_egg_pos2.lGX, cfg.boss_1_egg_pos2.lGY, dwNow))
				return true;
		}
		LPCHARACTER foe = PickPlayerBotBalathorFoe(ch, state, crypt, dwNow);
		// The arrows on the ground, between the fights (or with nothing on it).
		if (cfg.dwFireArrowVnum && (!foe || foe->GetVictim() != ch) && ch->GetEmptyInventory(1) >= 0 && ch->GetSectree())
		{
			FPlayerBotBalathorArrow f(ch, cfg.dwFireArrowVnum);
			ch->GetSectree()->ForEachAround(f);
			if (f.m_found)
			{
				if (f.m_iBest > 200)
				{
					MovePlayerBotBalathorTo(ch, state, f.m_found->GetX(), f.m_found->GetY(), 150, dwNow);
					return true;
				}
				if (ch->IsStateMove())
					ch->Stop();
				ch->PickupItem(f.m_found->GetVID());
				return true;
			}
		}
		if (foe)
			return FightPlayerBotTowerObjective(ch, state, foe, dwNow);
		state.dwTargetVID = 0;
		ch->SetVictim(NULL);
		LPCHARACTER dragon = crypt->GetCharacterByFlag("dragon");
		if (dragon && MovePlayerBotBalathorTo(ch, state, dragon->GetX(), dragon->GetY(), 1200, dwNow))
			return true;
		if (ch->IsStateMove())
			ch->Stop();
		SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
		return true;
	}

	// The tick: the presence for every bot; the run's own bots held. True while it holds the bot.
	bool ManagePlayerBotBalathorBot(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch)
			return false;
		if (!s_mapPlayerBotBalathorPresence.empty() || (ch->GetMapIndex() >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN &&
				ch->GetMapIndex() / 10000 == PLAYERBOT_BALATHOR_MAP))
			SyncPlayerBotBalathorPresence(ch, dwNow);
		if (s_mapPlayerBotBalathorBots.empty())
			return false;
		std::map<DWORD, TPlayerBotBalathorBot>::iterator bi = s_mapPlayerBotBalathorBots.find(ch->GetPlayerID());
		if (bi == s_mapPlayerBotBalathorBots.end())
			return false;
		TPlayerBotBalathorBot& b = bi->second;
		std::map<DWORD, TPlayerBotBalathorRun>::iterator ri = s_mapPlayerBotBalathorRuns.find(b.dwGuild);
		if (ri == s_mapPlayerBotBalathorRuns.end())
		{
			ReleasePlayerBotBalathorMember(ch->GetPlayerID(), "no_run", dwNow);
			return false;
		}
		TPlayerBotBalathorRun& run = ri->second;
		if (ch->IsDead())
			return false;
		state.dwLastMeaningfulActivityTime = dwNow;
		const SBalathorConfig& cfg = CBalathorManager::Instance().GetConfig();
		const long map = ch->GetMapIndex();
		if (run.bPhase == BALATHOR_BOT_GATHER)
		{
			long x = 0, y = 0;
			GetPlayerBotBalathorSpot(run, ch->GetPlayerID(), x, y);
			if (map != (long)cfg.dwEnterMapIndex)
			{
				if ((int)(dwNow - b.dwNextMove) < 0)
					return true;
				b.dwNextMove = dwNow + 5000;
				if (!TransitionPlayerBotMap(ch, state, cfg.dwEnterMapIndex, x, y, dwNow, "balathor_gather"))
				{
					PlayerBotLogThrottled("balathor_gather_refused", dwNow, "PLAYERBOT_BALATHOR: to Dolnarr refused pid=%u name=%s from=%ld",
							ch->GetPlayerID(), ch->GetName(), map);
					ReleasePlayerBotBalathorMember(ch->GetPlayerID(), "gather_refused", dwNow);
					return false;
				}
				return true;
			}
			if (MovePlayerBotBalathorTo(ch, state, x, y, PLAYERBOT_BALATHOR_SPOT_RANGE, dwNow))
				return true;
			run.arrived.insert(ch->GetPlayerID());
			if (KeepPlayerBotTowerAlive(ch, state, dwNow))
				return true;
			if (ch->IsStateMove())
				ch->Stop();
			SetPlayerBotAction(state, BOT_ACTION_IDLE, dwNow);
			return true;
		}
		// Inside: out of the Krypta now - the send-off, or its own way: the run is over for it.
		if (map != run.lInstance)
		{
			ReleasePlayerBotBalathorMember(ch->GetPlayerID(), "left_crypt", dwNow);
			return false;
		}
		CBalathor* crypt = CBalathorManager::Instance().FindByMapIndex((DWORD)map);
		const bool overdue = !crypt || crypt->GetStage() == BALATHOR_STAGE_NONE ||
				(run.dwClosedAt && dwNow - run.dwClosedAt > PLAYERBOT_BALATHOR_OUT_GRACE_MS) ||
				dwNow - run.dwPhaseSince > PLAYERBOT_BALATHOR_LIMIT_MS + PLAYERBOT_BALATHOR_OUT_GRACE_MS;
		if (overdue)
		{
			if ((int)(dwNow - b.dwNextMove) >= 0)
			{
				b.dwNextMove = dwNow + 5000;
				TransitionPlayerBotMap(ch, state, cfg.dwEnterMapIndex, cfg.enter_base_pos.lGX, cfg.enter_base_pos.lGY, dwNow,
						"balathor_out");
			}
			return true;
		}
		return FightPlayerBotBalathor(ch, state, b, run, crypt, dwNow);
	}

	// ------------------------------------------------------------ the guilds

	struct TPlayerBotBalathorCensus
	{
		int guilds, open, cooldown, level, age, ladder, sp, master, members, memberAge, treasury, deposit, ready;
		TPlayerBotBalathorCensus() : guilds(0), open(0), cooldown(0), level(0), age(0), ladder(0), sp(0), master(0), members(0),
				memberAge(0), treasury(0), deposit(0), ready(0) {}
	};

	// Why this bot guild cannot go now (NULL: it can); the members who would go, the master first.
	const char* CheckPlayerBotBalathorGuild(CGuild* guild, const std::vector<DWORD>& fit, std::vector<DWORD>& out,
			TPlayerBotBalathorCensus& c, bool deep, DWORD dwNow)
	{
		const SBalathorConfig& cfg = CBalathorManager::Instance().GetConfig();
		out.clear();
		const DWORD gid = guild->GetID();
		if (s_mapPlayerBotBalathorRuns.count(gid) || guild->GetFlag("balathor_channel") != 0 ||
				CBalathorManager::Instance().FindByGID(gid))
			return ++c.open, "open";
		if (guild->GetFlag("balathor_cooldown") > get_global_time())
			return ++c.cooldown, "cooldown";
		if ((int)guild->GetLevel() < (int)cfg.bRegisterGuildMinLevel)
			return ++c.level, "guild_level";
		if ((long long)get_global_time() - (long long)GuildSysCreateTime(guild) < (long long)PLAYERBOT_BALATHOR_GUILD_HOURS * 3600)
			return ++c.age, "guild_age";
		if ((DWORD)guild->GetLadderPoint() < cfg.dwRegisterLadderPoint)
			return ++c.ladder, "ladder";
		if (guild->GetSP() < (int)cfg.dwReviveHwatchaRequestSP * PLAYERBOT_BALATHOR_HWACHA_SHOTS)
			return ++c.sp, "guild_sp";
		const DWORD masterPid = guild->GetMasterPID();
		if (std::find(fit.begin(), fit.end(), masterPid) == fit.end())
			return ++c.master, "master";
		if ((int)fit.size() < (int)cfg.bRegisterMinMemberCount)
			return ++c.members, "members";
		if (!deep)
			return NULL;
		// 24 h in the guild (a question to the database each - only for a guild that has everything else).
		const long long now = get_global_time();
		const long long minAge = (long long)PLAYERBOT_BALATHOR_MEMBER_HOURS * 3600;
		if (now - (long long)GuildSysMemberJoinTime(guild, masterPid) < minAge)
			return ++c.memberAge, "member_age";
		out.push_back(masterPid);
		std::vector<DWORD> rest(fit);
		for (size_t i = rest.size(); i > 1; --i)
			std::swap(rest[i - 1], rest[number(0, (int)i - 1)]);
		for (size_t i = 0; i < rest.size() && (int)out.size() < (int)cfg.bRegisterMaxMemberCount; ++i)
			if (rest[i] != masterPid && now - (long long)GuildSysMemberJoinTime(guild, rest[i]) >= minAge)
				out.push_back(rest[i]);
		if ((int)out.size() < (int)cfg.bRegisterMinMemberCount)
		{
			out.clear();
			return ++c.memberAge, "member_age";
		}
		// The treasury that may be spent: the master pays in what it lacks from its own spare gold.
		const long long bank = (long long)guild->GetGuildMoneyAvailable();
		if (bank < PLAYERBOT_BALATHOR_BANK_MIN)
		{
			LPCHARACTER master = CHARACTER_MANAGER::instance().FindByPID(masterPid);
			const long long need = PLAYERBOT_BALATHOR_BANK_MIN - bank + 50000LL;
			const long long spare = master ? (long long)master->GetGold() - (long long)GetPlayerBotReservedGold(master) -
					PLAYERBOT_GUILD_MASTER_RESERVE : 0;
			out.clear();
			if (master && spare >= need)
			{
				GuildDutyDeposit(guild, master, need);
				sys_log(0, "PLAYERBOT_BALATHOR: deposit guild=%s gid=%u master=%s amount=%lld treasury_was=%lld",
						guild->GetName(), gid, master->GetName(), need, bank);
				return ++c.deposit, "treasury_deposit";
			}
			return ++c.treasury, "treasury";
		}
		++c.ready;
		return NULL;
	}

	void UpdatePlayerBotBalathorRun(TPlayerBotBalathorRun& run, DWORD dwNow, bool& over)
	{
		over = false;
		if (run.bPhase == BALATHOR_BOT_GATHER)
		{
			LPCHARACTER master = CHARACTER_MANAGER::instance().FindByPID(run.dwMaster);
			if (!master || !s_mapPlayerBotBalathorBots.count(run.dwMaster))
			{
				EndPlayerBotBalathorRun(run, "master_gone", dwNow);
				over = true;
				return;
			}
			const SBalathorConfig& cfg = CBalathorManager::Instance().GetConfig();
			size_t still = 0;
			for (size_t i = 0; i < run.members.size(); ++i)
				still += s_mapPlayerBotBalathorBots.count(run.members[i]);
			const bool all = run.arrived.size() >= still;
			const bool enough = run.arrived.count(run.dwMaster) && (int)run.arrived.size() >= (int)cfg.bRegisterMinMemberCount;
			if (enough && (all || dwNow - run.dwCalledAt >= PLAYERBOT_BALATHOR_GATHER_MS))
			{
				sys_log(0, "PLAYERBOT_BALATHOR: gathered guild=%s gid=%u at_dolnarr=%u called=%u took_s=%u", run.strGuild.c_str(),
						run.dwGuild, (unsigned int)run.arrived.size(), (unsigned int)run.members.size(), (dwNow - run.dwCalledAt) / 1000);
				if (!RegisterPlayerBotBalathorRun(run, dwNow))
				{
					EndPlayerBotBalathorRun(run, "not_registered", dwNow);
					over = true;
				}
				return;
			}
			if (dwNow - run.dwCalledAt >= PLAYERBOT_BALATHOR_GATHER_MAX_MS || (!enough && still < cfg.bRegisterMinMemberCount))
			{
				EndPlayerBotBalathorRun(run, "not_gathered", dwNow);
				over = true;
			}
			return;
		}
		CBalathor* crypt = CBalathorManager::Instance().FindByMapIndex((DWORD)run.lInstance);
		int inside = 0;
		for (size_t i = 0; i < run.members.size(); ++i)
		{
			LPCHARACTER m = CHARACTER_MANAGER::instance().FindByPID(run.members[i]);
			if (m && m->GetMapIndex() == run.lInstance && s_mapPlayerBotBalathorBots.count(run.members[i]))
				++inside;
		}
		if (inside == 0)
		{
			if (run.dwNoneInsideSince == 0)
				run.dwNoneInsideSince = dwNow;
			// Everybody out (the send-off, or every member's own way): the run is over.
			if (!crypt || crypt->GetStage() == BALATHOR_STAGE_CLOSE || crypt->GetStage() == BALATHOR_STAGE_NONE ||
					dwNow - run.dwNoneInsideSince > PLAYERBOT_BALATHOR_NONE_INSIDE_MS)
			{
				if (crypt && crypt->GetStage() != BALATHOR_STAGE_CLOSE && crypt->GetStage() != BALATHOR_STAGE_NONE)
					crypt->Finish(BALATHOR_FINISH_FAIL_BY_GAMEMASTER);	// the master's "Poddaj"
				EndPlayerBotBalathorRun(run, run.iClaim == 99 ? "reward" : (run.iClaim == 2 ? "no_reward" : "out"), dwNow);
				over = true;
			}
			return;
		}
		run.dwNoneInsideSince = 0;
		if (!crypt)
			return;
		const int reached = GetPlayerBotBalathorReached(crypt);
		if (reached > run.iReached)
		{
			run.iReached = reached;
			sys_log(0, "PLAYERBOT_BALATHOR: reached guild=%s gid=%u step=%s inside=%d in_s=%u", run.strGuild.c_str(), run.dwGuild,
					GetPlayerBotBalathorReachedName(reached), inside, (dwNow - run.dwPhaseSince) / 1000);
			if (run.bParty)	// MT2009_PLUS_BALATHOR_BOT_PARTY_V1
				sys_log(0, "BOT_DGRUN: stage run=%d dungeon=balathor instance=%ld stage=%d (%s) after_s=%u inside=%d", run.iRunId,
						run.lInstance, reached, GetPlayerBotBalathorReachedName(reached), (dwNow - run.dwPhaseSince) / 1000, inside);
		}
		if (crypt->GetStage() == BALATHOR_STAGE_WAITING && !run.bStarted && (int)(dwNow - run.dwStartAt) >= 0)
		{
			LPCHARACTER master = CHARACTER_MANAGER::instance().FindByPID(run.dwMaster);
			if (master && master->GetMapIndex() == run.lInstance && !master->IsDead())
			{
				run.bStarted = true;
				crypt->SetStage(BALATHOR_STAGE_RUN);	// the guide's "Zaczynamy" - the master's
				sys_log(0, "PLAYERBOT_BALATHOR: started guild=%s gid=%u master=%s inside=%d", run.strGuild.c_str(), run.dwGuild,
						master->GetName(), inside);
			}
			else if (dwNow - run.dwStartAt > PLAYERBOT_BALATHOR_NONE_INSIDE_MS)
				crypt->Finish(BALATHOR_FINISH_FAIL_BY_GAMEMASTER);
		}
		if (crypt->GetStage() == BALATHOR_STAGE_CLOSE && run.dwClosedAt == 0)
			run.dwClosedAt = dwNow;
		if (crypt->GetStage() == BALATHOR_STAGE_RUN && dwNow - run.dwPhaseSince > PLAYERBOT_BALATHOR_LIMIT_MS)
		{
			sys_log(0, "PLAYERBOT_BALATHOR: given up guild=%s gid=%u reached=%s (time)", run.strGuild.c_str(), run.dwGuild,
					GetPlayerBotBalathorReachedName(run.iReached));
			crypt->Finish(BALATHOR_FINISH_FAIL_BY_GAMEMASTER);
		}
	}

	// ------------------------------------------------------------ MT2009_PLUS_BALATHOR_BOT_PARTY_V1: the bot parties

	bool IsPlayerBotBalathorPartyTraining()
	{
		return s_kPlayerBotBalathorTrain.parties > 0;
	}

	int GetPlayerBotBalathorPartyCap()
	{
		if (IsPlayerBotBalathorPartyTraining())
			return s_kPlayerBotBalathorTrain.parties;
		return ReadPlayerBotYoharaEnvInt("PLAYERBOT_BALATHOR_PARTIES", 1, 0, 20);
	}

	int GetPlayerBotBalathorPartySize()
	{
		const SBalathorConfig& cfg = CBalathorManager::Instance().GetConfig();
		const int lo = std::max(1, (int)cfg.bRegisterMinMemberCount);
		const int hi = std::max(lo, std::min(PLAYERBOT_BALATHOR_PARTY_SIZE_MAX, (int)cfg.bRegisterMaxMemberCount ?
				(int)cfg.bRegisterMaxMemberCount : PLAYERBOT_BALATHOR_PARTY_SIZE_MAX));
		const int want = IsPlayerBotBalathorPartyTraining() ? s_kPlayerBotBalathorTrain.size : PLAYERBOT_BALATHOR_PARTY_SIZE_MAX;
		return std::max(lo, std::min(hi, want));
	}

	// The file playerbot_balathor_train in the core's directory: "parties <n> [size]" - read when it changed.
	void ReadPlayerBotBalathorTrainFile(DWORD dwNow)
	{
		static DWORD s_dwNext = 0;
		static time_t s_tMtime = (time_t)-1;
		if (s_dwNext != 0 && (int)(dwNow - s_dwNext) < 0)
			return;
		s_dwNext = dwNow + PLAYERBOT_BALATHOR_FILE_MS;
		struct stat st;
		const time_t mtime = stat(PLAYERBOT_BALATHOR_TRAIN_FILE, &st) == 0 ? st.st_mtime : (time_t)0;
		if (mtime == s_tMtime)
			return;
		s_tMtime = mtime;
		TPlayerBotBalathorTrain t;
		FILE* fp = mtime ? fopen(PLAYERBOT_BALATHOR_TRAIN_FILE, "r") : NULL;
		if (fp)
		{
			char line[160];
			while (fgets(line, sizeof(line), fp))
			{
				char cmd[32] = "";
				int a = 0, b = 0;
				const int got = sscanf(line, "%31s %d %d", cmd, &a, &b);
				if (got < 1 || cmd[0] == '#')
					continue;
				if (!strcmp(cmd, "parties") && got >= 2)
				{
					t.parties = std::max(0, std::min(20, a));
					if (got >= 3)
						t.size = std::max(4, std::min(PLAYERBOT_BALATHOR_PARTY_SIZE_MAX, b));
				}
				else
					sys_log(0, "PLAYERBOT_BALATHOR: train unknown line=%s", line);
			}
			fclose(fp);
		}
		s_kPlayerBotBalathorTrain = t;
		sys_log(0, "PLAYERBOT_BALATHOR: train load parties=%d size=%d (cap=%d size=%d) file=%s", t.parties, t.size,
				GetPlayerBotBalathorPartyCap(), GetPlayerBotBalathorPartySize(), mtime ? "yes" : "no");
	}

	DWORD NextPlayerBotBalathorPartyKey()
	{
		for (int guard = 0; guard < 1000; ++guard)
		{
			if (s_dwPlayerBotBalathorPartyKey < BALATHOR_BOT_PARTY_KEY_MIN || s_dwPlayerBotBalathorPartyKey >= 0xFFFFFF00)
				s_dwPlayerBotBalathorPartyKey = BALATHOR_BOT_PARTY_KEY_MIN;
			const DWORD key = s_dwPlayerBotBalathorPartyKey++;
			if (!s_mapPlayerBotBalathorRuns.count(key) && !CBalathorManager::Instance().FindByGID(key))
				return key;
		}
		return 0;
	}

	// The calls of the bot parties: up to the cap at once, the strongest free fit bots of one kingdom a party.
	void PlanPlayerBotBalathorParties(DWORD dwNow, bool on)
	{
		static DWORD s_dwNextPlan = 0, s_dwNextCensus = 0;
		ReadPlayerBotBalathorTrainFile(dwNow);
		const bool train = IsPlayerBotBalathorPartyTraining();
		if (s_dwNextPlan == 0)
		{
			s_dwNextPlan = dwNow + (train ? PLAYERBOT_BALATHOR_TRAIN_PLAN_MS : PLAYERBOT_BALATHOR_FIRST_PLAN_MS);
			s_dwNextCensus = s_dwNextPlan;
		}
		const bool census = (int)(dwNow - s_dwNextCensus) >= 0;
		const bool plan = (int)(dwNow - s_dwNextPlan) >= 0;
		if (!census && !plan)
			return;
		if (plan)
			s_dwNextPlan = dwNow + (train ? PLAYERBOT_BALATHOR_TRAIN_PLAN_MS : PLAYERBOT_BALATHOR_PLAN_MS);
		if (census)
			s_dwNextCensus = dwNow + (train ? 10 * 60 * 1000 : PLAYERBOT_BALATHOR_CENSUS_MS);
		int running = 0;
		for (std::map<DWORD, TPlayerBotBalathorRun>::const_iterator r = s_mapPlayerBotBalathorRuns.begin();
				r != s_mapPlayerBotBalathorRuns.end(); ++r)
			if (r->second.bParty)
				++running;
		const int cap = GetPlayerBotBalathorPartyCap();
		const bool call = plan && on && cap > 0 && running < cap;
		if (!call && !census)
			return;
		const SBalathorConfig& cfg = CBalathorManager::Instance().GetConfig();
		// The pool by kingdom, the strongest first.
		std::vector<std::pair<long long, DWORD> > pool[4];
		int levelFit = 0;
		for (TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.begin(); st != s_mapPlayerBotAIStates.end(); ++st)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(st->first);
			if (!ch || !ch->GetDesc() || !ch->GetDesc()->IsBot() || ch->GetEmpire() < 1 || ch->GetEmpire() > 3)
				continue;
			if (!IsPlayerBotBalathorFitMember(ch))
				continue;
			++levelFit;
			if (IsPlayerBotBalathorCandidate(ch, st->second, dwNow))
				pool[ch->GetEmpire()].push_back(std::make_pair(ScorePlayerBotYdg(ch), st->first));
		}
		const int size = GetPlayerBotBalathorPartySize();
		if (census)
			sys_log(0, "PLAYERBOT_BALATHOR: party census fit_level=%d free=%u/%u/%u size=%d running=%d cap=%d train=%d called=%u "
					"entered=%u rewards=%u on=%d", levelFit, (unsigned int)pool[1].size(), (unsigned int)pool[2].size(),
					(unsigned int)pool[3].size(), size, running, cap, train ? 1 : 0, s_uPlayerBotBalathorPartyCalled,
					s_uPlayerBotBalathorPartyEntered, s_uPlayerBotBalathorPartyWon, on ? 1 : 0);
		if (!call)
			return;
		for (int e = 1; e <= 3; ++e)
			std::sort(pool[e].begin(), pool[e].end(), std::greater<std::pair<long long, DWORD> >());
		size_t used[4] = { 0, 0, 0, 0 };
		for (int calls = 0; calls < PLAYERBOT_BALATHOR_PARTY_CALLS_A_PASS && running < cap; ++calls)
		{
			// the kingdom with the most free fit bots left
			int empire = 0;
			size_t most = 0;
			for (int e = 1; e <= 3; ++e)
				if (pool[e].size() - used[e] > most)
				{
					most = pool[e].size() - used[e];
					empire = e;
				}
			if (empire == 0 || (int)most < (int)cfg.bRegisterMinMemberCount)
				return;
			const DWORD key = NextPlayerBotBalathorPartyKey();
			if (!key)
				return;
			std::vector<DWORD> members;
			for (size_t i = used[empire]; i < pool[empire].size() && (int)members.size() < size; ++i)
				members.push_back(pool[empire][i].second);
			used[empire] += members.size();
			TPlayerBotBalathorRun& run = s_mapPlayerBotBalathorRuns[key];
			run = TPlayerBotBalathorRun();
			run.bParty = true;
			run.bTrain = train;
			run.dwGuild = key;
			run.iRunId = PLAYERBOT_BALATHOR_DGRUN_ID_BASE + (++s_iPlayerBotBalathorPartyRunId);
			run.bEmpire = (BYTE)empire;
			run.dwMaster = members[0];	// the strongest leads (and fires the Hwacha)
			run.members = members;
			run.dwCalledAt = dwNow;
			run.dwPhaseSince = dwNow;
			LPCHARACTER leader = CHARACTER_MANAGER::instance().FindByPID(run.dwMaster);
			char label[64];
			snprintf(label, sizeof(label), "party%d:%s", run.iRunId, leader ? leader->GetName() : "?");
			run.strGuild = label;
			for (size_t k = 0; k < members.size(); ++k)
			{
				TPlayerBotBalathorBot& b = s_mapPlayerBotBalathorBots[members[k]];
				b = TPlayerBotBalathorBot();
				b.dwGuild = key;
				b.bTrain = train;
			}
			++running;
			++s_uPlayerBotBalathorCalled;
			++s_uPlayerBotBalathorPartyCalled;
			sys_log(0, "PLAYERBOT_BALATHOR: party called run=%d key=%u empire=%d leader=%s members=%u free=%u running=%d cap=%d train=%d "
					"called_total=%u", run.iRunId, key, empire, leader ? leader->GetName() : "?", (unsigned int)members.size(),
					(unsigned int)most, running, cap, train ? 1 : 0, s_uPlayerBotBalathorPartyCalled);
		}
	}

	// The runs, the calls and the census - from CPlayerBotManager's update.
	void ManagePlayerBotBalathorRuns(DWORD dwNow)
	{
		static DWORD s_dwStart = 0, s_dwNext = 0, s_dwNextPlan = 0, s_dwNextCensus = 0;
		if (s_dwStart == 0)
		{
			s_dwStart = dwNow ? dwNow : 1;
			s_dwNextPlan = dwNow + PLAYERBOT_BALATHOR_FIRST_PLAN_MS;
			s_dwNextCensus = dwNow + PLAYERBOT_BALATHOR_FIRST_PLAN_MS;
		}
		if (s_dwNext != 0 && (int)(dwNow - s_dwNext) < 0)
			return;
		s_dwNext = dwNow + 1000;
		for (std::map<DWORD, TPlayerBotBalathorRun>::iterator r = s_mapPlayerBotBalathorRuns.begin(); r != s_mapPlayerBotBalathorRuns.end();)
		{
			bool over = false;
			UpdatePlayerBotBalathorRun(r->second, dwNow, over);
			if (over)
				s_mapPlayerBotBalathorRuns.erase(r++);
			else
				++r;
		}
		// MT2009_PLUS_BALATHOR_BOT_PARTY_V1: the bot parties (no guild) - their own clock and cap.
		if (IsPlayerBotBalathorOn())
			PlanPlayerBotBalathorParties(dwNow, IsPlayerBotDgRunOn(dwNow));
		const bool census = (int)(dwNow - s_dwNextCensus) >= 0;
		const bool plan = (int)(dwNow - s_dwNextPlan) >= 0;
		if (!census && !plan)
			return;
		if (plan)
			s_dwNextPlan = dwNow + PLAYERBOT_BALATHOR_PLAN_MS;
		if (census)
			s_dwNextCensus = dwNow + PLAYERBOT_BALATHOR_CENSUS_MS;
		if (!IsPlayerBotBalathorOn())
		{
			if (census)
				sys_log(0, "PLAYERBOT_BALATHOR: census off (the Krypta is not hosted here)");
			return;
		}
		const int cap = ReadPlayerBotYoharaEnvInt("PLAYERBOT_BALATHOR_MAX", 1, 0, 4);
		const bool on = cap > 0 && IsPlayerBotDgRunOn(dwNow);
		int guildRuns = 0;	// MT2009_PLUS_BALATHOR_BOT_PARTY_V1: the bot parties have their own cap
		for (std::map<DWORD, TPlayerBotBalathorRun>::const_iterator r = s_mapPlayerBotBalathorRuns.begin();
				r != s_mapPlayerBotBalathorRuns.end(); ++r)
			if (!r->second.bParty)
				++guildRuns;
		const bool call = plan && on && guildRuns < cap;
		if (!call && !census)
			return;
		// The bot guilds of this core: a bot master standing here, its fit and free bots.
		std::map<DWORD, std::vector<DWORD> > fit;
		std::set<DWORD> guilds;
		for (TPlayerBotAIStateMap::iterator st = s_mapPlayerBotAIStates.begin(); st != s_mapPlayerBotAIStates.end(); ++st)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(st->first);
			if (!ch || !ch->GetDesc() || !ch->GetDesc()->IsBot() || !ch->GetGuild())
				continue;
			CGuild* guild = ch->GetGuild();
			if (guild->GetMasterPID() == st->first)
				guilds.insert(guild->GetID());
			if (IsPlayerBotBalathorCandidate(ch, st->second, dwNow))
				fit[guild->GetID()].push_back(st->first);
		}
		TPlayerBotBalathorCensus c;
		std::vector<DWORD> ready;
		std::vector<DWORD> members;
		for (std::set<DWORD>::const_iterator g = guilds.begin(); g != guilds.end(); ++g)
		{
			CGuild* guild = CGuildManager::instance().FindGuild(*g);
			if (!guild)
				continue;
			++c.guilds;
			static const std::vector<DWORD> s_none;
			std::map<DWORD, std::vector<DWORD> >::const_iterator f = fit.find(*g);
			if (!CheckPlayerBotBalathorGuild(guild, f != fit.end() ? f->second : s_none, members, c, false, dwNow))
				ready.push_back(*g);
		}
		if (census)
			sys_log(0, "PLAYERBOT_BALATHOR: census bot_guilds=%d open=%d cooldown=%d guild_level=%d guild_age=%d ladder=%d guild_sp=%d "
					"master=%d members=%d near_ready=%u runs=%u called=%u registered=%u rewards=%u on=%d",
					c.guilds, c.open, c.cooldown, c.level, c.age, c.ladder, c.sp, c.master, c.members, (unsigned int)ready.size(),
					(unsigned int)s_mapPlayerBotBalathorRuns.size(), s_uPlayerBotBalathorCalled, s_uPlayerBotBalathorRegistered,
					s_uPlayerBotBalathorRewards, on ? 1 : 0);
		if (!call || ready.empty())
			return;
		// One guild of the ready ones, looked at in full (the members' 24 h, the treasury).
		for (size_t i = ready.size(); i > 1; --i)
			std::swap(ready[i - 1], ready[number(0, (int)i - 1)]);
		for (size_t i = 0; i < ready.size() && i < 3; ++i)
		{
			CGuild* guild = CGuildManager::instance().FindGuild(ready[i]);
			if (!guild)
				continue;
			TPlayerBotBalathorCensus deep;
			const char* why = CheckPlayerBotBalathorGuild(guild, fit[ready[i]], members, deep, true, dwNow);
			if (why)
			{
				sys_log(0, "PLAYERBOT_BALATHOR: not yet guild=%s gid=%u why=%s fit=%u", guild->GetName(), ready[i], why,
						(unsigned int)fit[ready[i]].size());
				continue;
			}
			TPlayerBotBalathorRun& run = s_mapPlayerBotBalathorRuns[ready[i]];
			run = TPlayerBotBalathorRun();
			run.dwGuild = ready[i];
			run.strGuild = guild->GetName();
			run.dwMaster = guild->GetMasterPID();
			run.members = members;
			run.dwCalledAt = dwNow;
			run.dwPhaseSince = dwNow;
			for (size_t k = 0; k < members.size(); ++k)
			{
				TPlayerBotBalathorBot& b = s_mapPlayerBotBalathorBots[members[k]];
				b = TPlayerBotBalathorBot();
				b.dwGuild = ready[i];
			}
			++s_uPlayerBotBalathorCalled;
			LPCHARACTER master = CHARACTER_MANAGER::instance().FindByPID(run.dwMaster);
			sys_log(0, "PLAYERBOT_BALATHOR: called guild=%s gid=%u level=%d master=%s members=%u ladder=%d treasury=%lld sp=%d called_total=%u",
					run.strGuild.c_str(), run.dwGuild, (int)guild->GetLevel(), master ? master->GetName() : "?",
					(unsigned int)members.size(), guild->GetLadderPoint(), (long long)guild->GetGuildMoneyAvailable(), guild->GetSP(),
					s_uPlayerBotBalathorCalled);
			break;
		}
	}

	// A move of the run's: to Dolnarr, into its Krypta, out of it.
	bool IsPlayerBotBalathorRunMove(LPCHARACTER ch, long targetMap)
	{
		if (!ch || s_mapPlayerBotBalathorBots.empty())
			return false;
		std::map<DWORD, TPlayerBotBalathorBot>::const_iterator b = s_mapPlayerBotBalathorBots.find(ch->GetPlayerID());
		if (b == s_mapPlayerBotBalathorBots.end())
			return false;
		std::map<DWORD, TPlayerBotBalathorRun>::const_iterator r = s_mapPlayerBotBalathorRuns.find(b->second.dwGuild);
		return r != s_mapPlayerBotBalathorRuns.end() && r->second.lInstance != 0 && targetMap == r->second.lInstance;
	}
#else
	bool IsPlayerBotBalathorInstance(long) { return false; }
	bool IsPlayerBotBalathorPartyFit(LPCHARACTER, long) { return false; }
	bool IsPlayerBotBalathorNoTarget(LPCHARACTER) { return false; }
	bool ManagePlayerBotBalathorBot(LPCHARACTER, TPlayerBotAIState&, DWORD) { return false; }
	void ManagePlayerBotBalathorRuns(DWORD) {}
	bool IsPlayerBotBalathorRunMove(LPCHARACTER, long) { return false; }
#endif

	// MT2009_PLUS_BOT_YOHARA_PDG_V1: the guild lair and maze runs to the other passes (playerbot_dungeon_runs.h,
	// playerbot_party_dungeon.h).
	bool IsPlayerBotOnOwnLairRun(DWORD pid)
	{
		return IsPlayerBotOnBalathorRun(pid) || IsPlayerBotOnLabiryntRun(pid);
	}

	bool IsPlayerBotOwnLairRunMove(LPCHARACTER ch, long targetMap)
	{
		return IsPlayerBotBalathorRunMove(ch, targetMap) || IsPlayerBotLabiryntRunMove(ch, targetMap);
	}
}

#endif
