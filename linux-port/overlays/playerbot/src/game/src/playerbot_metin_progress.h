#ifndef __INC_METIN2_PLAYERBOT_METIN_PROGRESS_H__
#define __INC_METIN2_PLAYERBOT_METIN_PROGRESS_H__

// MT2009_PLUS_METIN_PROGRESS_V1 - "Metiny progresowe" (the owner, 8 November 2026): a map crowded with bots gets more
// Metins. The night after the test world's reset 2000 bots stood at the level-35 gate of the progression checklist
// (ten Metins, playerbot_progression_rules.h) with 0-2 broken after an hour - 965 bots on Orc Valley shared its few
// stones. Per map and per core (each core hosts its own instance of a map and counts its own bots on it):
//
//   bots on the map     extra Metins of EACH stone kind of that map's own regen
//     up to 50          none (the regen as it is)
//     51-100            +2
//     101-200           +3
//     201-300           +6
//     301 and more      +10 (the owner's 300-500 tier, kept above 500 too: a map that full needs them most)
//
// The owner's example: M2 on channel 1 with 450 bots and three kinds of stone (25, 30, 35) -> 3 x 10 = 30 Metins on top
// of the regen's. Players profit too - the Metins are the regen's own vnums, with their own drops and exp.
//
//   * The kinds: the vnums of CHAR_TYPE_STONE among the members of the map's regen lines marked is_stone
//     (regen.cpp / regenmetin: stone.txt and every 's' line, groups and groups of groups too), read from regen_list
//     on the first pass; the Demon Tower's quest stones and the event stones are left out (playerbot_types.h).
//     Instances and dungeon maps are never touched.
//   * Where: a random cell anywhere on the map, at most PLAYERBOT_METIN_PROGRESS_TRIES draws a stone: not blocked,
//     not water, not a safe zone, a PLAYERBOT_METIN_PROGRESS_EDGE margin from the map's edge, no pocket of the bots'
//     grid (an enclosed area, playerbot_navigation.h) and on ground connected to one of the map's own stone spots
//     (IsPlayerBotReachable from a regen stone line's centre), PLAYERBOT_METIN_PROGRESS_SPOT_GAP from those spots and
//     PLAYERBOT_METIN_PROGRESS_STONE_GAP from the other extra Metins.
//   * When: the bots are counted every PLAYERBOT_METIN_PROGRESS_PASS_MS. A tier that asks for more puts the
//     difference down at once (as a regen does at boot). A killed extra Metin is put down again after the SAME
//     respawn time as the map's own Metins of that kind (the owner's correction of 8 November: "po prostu jest ich
//     wtedy wiecej") - the shortest regen interval of the map's stone lines of that vnum, read through the regen's
//     own rule (GetSpawnDelay, then fastMetinSpawn<map> / fastMetinSpawn: MAX(3, delay * flag / 100)). A tier that
//     asks for fewer kills nothing: the living ones stand, and the dead are not replaced beyond the new target.
//   * The count is the owner's tier, not multiplied by m2_metin_count (the regen's own x2..x4 stays the regen's).
//   * The bots: every extra Metin is entered in the known-Metin registry (RememberPlayerBotMetin) as it is put down,
//     so the stone hunters and the gate's Metin expeditions find it as they find the regen's.
//
// Switch: event flag m2_metin_progress_off 1 (nothing new is put down; the living stand). Tiers: env
// PLAYERBOT_METIN_PROGRESS_TIERS "50:2,100:3,200:6,300:10" (a tier holds above its number of bots), read once.
// Log: METIN_PROGRESS: kinds (at the first pass), spawned / replaced (throttled), census per map every 10 minutes
// (bots, tier, kinds, extra target, alive, pending, spawned, replaced, failed).
//
// An implementation fragment: include it once, from playerbot_manager.cpp, after playerbot_movement.h.

#if defined(PLAYERBOT_ENGINE_MT2009)

#include "regen.h"
#include "dungeon.h"

extern LPREGEN regen_list;

namespace
{
	const DWORD PLAYERBOT_METIN_PROGRESS_PASS_MS = 60 * 1000;
	const DWORD PLAYERBOT_METIN_PROGRESS_CENSUS_MS = 10 * 60 * 1000;
	const int PLAYERBOT_METIN_PROGRESS_TRIES = 80;
	const int PLAYERBOT_METIN_PROGRESS_EDGE = 1500;
	const int PLAYERBOT_METIN_PROGRESS_SPOT_GAP = 1500;
	const int PLAYERBOT_METIN_PROGRESS_STONE_GAP = 2500;
	const int PLAYERBOT_METIN_PROGRESS_MAX_TIERS = 8;
	// at most this many put down a pass over all maps (a tier's first fill spreads over a few minutes, no hitch)
	const int PLAYERBOT_METIN_PROGRESS_SPAWNS_PER_PASS = 40;

	struct TPlayerBotMetinProgressTier
	{
		int bots;	// held above this many bots
		int extra;	// of each kind
	};

	struct TPlayerBotMetinProgressKind
	{
		DWORD vnum;
		DWORD delaySec;	// the shortest of the map's lines of this vnum (GetSpawnDelay before the flag)
		const REGEN* line;	// one of them, for its GetSpawnDelay
		std::vector<DWORD> vids;	// the living extra Metins
		std::vector<DWORD> due;	// a dead one's replacement time each (get_dword_time)
		unsigned int spawned, replaced, failed;
		TPlayerBotMetinProgressKind() : vnum(0), delaySec(0), line(NULL), spawned(0), replaced(0), failed(0) {}
	};

	struct TPlayerBotMetinProgressMap
	{
		long mapIndex;
		std::vector<TPlayerBotMetinProgressKind> kinds;
		std::vector<std::pair<long, long> > spots;	// the centres of the regen's stone lines
		int lastTarget;
		int lastBots;
		DWORD nextCensus;
		TPlayerBotMetinProgressMap() : mapIndex(0), lastTarget(0), lastBots(0), nextCensus(0) {}
	};

	std::map<long, TPlayerBotMetinProgressMap> s_mapPlayerBotMetinProgress;
	bool s_bPlayerBotMetinProgressRead = false;
	DWORD s_dwPlayerBotMetinProgressNextPass = 0;
	TPlayerBotMetinProgressTier s_aPlayerBotMetinProgressTiers[PLAYERBOT_METIN_PROGRESS_MAX_TIERS];
	int s_iPlayerBotMetinProgressTierCount = 0;

	void ReadPlayerBotMetinProgressTiers()
	{
		static const TPlayerBotMetinProgressTier defaults[] = { { 50, 2 }, { 100, 3 }, { 200, 6 }, { 300, 10 } };
		s_iPlayerBotMetinProgressTierCount = 0;
		const char* env = std::getenv("PLAYERBOT_METIN_PROGRESS_TIERS");
		if (env && *env)
		{
			std::string s(env);
			size_t pos = 0;
			while (pos < s.size() && s_iPlayerBotMetinProgressTierCount < PLAYERBOT_METIN_PROGRESS_MAX_TIERS)
			{
				size_t comma = s.find(',', pos);
				const std::string part = s.substr(pos, comma == std::string::npos ? std::string::npos : comma - pos);
				const size_t colon = part.find(':');
				if (colon != std::string::npos)
				{
					const int bots = atoi(part.substr(0, colon).c_str());
					const int extra = atoi(part.substr(colon + 1).c_str());
					if (bots >= 0 && extra >= 0 && extra <= 50)
					{
						s_aPlayerBotMetinProgressTiers[s_iPlayerBotMetinProgressTierCount].bots = bots;
						s_aPlayerBotMetinProgressTiers[s_iPlayerBotMetinProgressTierCount].extra = extra;
						++s_iPlayerBotMetinProgressTierCount;
					}
				}
				if (comma == std::string::npos)
					break;
				pos = comma + 1;
			}
		}
		if (s_iPlayerBotMetinProgressTierCount == 0)
			for (size_t i = 0; i < sizeof(defaults) / sizeof(defaults[0]); ++i)
				s_aPlayerBotMetinProgressTiers[s_iPlayerBotMetinProgressTierCount++] = defaults[i];
		std::string shown;
		for (int i = 0; i < s_iPlayerBotMetinProgressTierCount; ++i)
		{
			char buf[32];
			snprintf(buf, sizeof(buf), "%s>%d:+%d", i ? "," : "", s_aPlayerBotMetinProgressTiers[i].bots,
					s_aPlayerBotMetinProgressTiers[i].extra);
			shown += buf;
		}
		sys_log(0, "METIN_PROGRESS: tiers %s (%s)", shown.c_str(), env && *env ? "PLAYERBOT_METIN_PROGRESS_TIERS" : "defaults");
	}

	int GetPlayerBotMetinProgressExtra(int bots, int* tierOut)
	{
		int extra = 0, tier = 0;
		for (int i = 0; i < s_iPlayerBotMetinProgressTierCount; ++i)
			if (bots > s_aPlayerBotMetinProgressTiers[i].bots && s_aPlayerBotMetinProgressTiers[i].extra >= extra)
			{
				extra = s_aPlayerBotMetinProgressTiers[i].extra;
				tier = i + 1;
			}
		if (tierOut)
			*tierOut = tier;
		return extra;
	}

	void CollectPlayerBotMetinProgressMembers(const REGEN* regen, std::vector<DWORD>& vnums)
	{
		vnums.clear();
		if (regen->type == REGEN_TYPE_GROUP)
		{
			CMobGroup* group = CMobManager::instance().GetGroup(regen->vnum);
			if (group)
				vnums = group->GetMemberVector();
		}
		else if (regen->type == REGEN_TYPE_GROUP_GROUP)
		{
			const std::vector<DWORD>* groups = CMobManager::instance().GetGroupGroupMembers(regen->vnum);
			if (!groups)
				return;
			for (size_t i = 0; i < groups->size(); ++i)
			{
				CMobGroup* group = CMobManager::instance().GetGroup((*groups)[i]);
				if (group)
					vnums.insert(vnums.end(), group->GetMemberVector().begin(), group->GetMemberVector().end());
			}
		}
		else if (regen->type == REGEN_TYPE_MOB || regen->type == REGEN_TYPE_ANYWHERE)
			vnums.push_back((DWORD)regen->vnum);
	}

	// The map's kinds of stone, from this core's regen (it holds only the maps this core hosts).
	void ReadPlayerBotMetinProgressKinds()
	{
		s_bPlayerBotMetinProgressRead = true;
		ReadPlayerBotMetinProgressTiers();
		std::vector<DWORD> members;
		for (LPREGEN regen = regen_list; regen; regen = regen->next)
		{
			if (!regen->is_stone || regen->lMapIndex <= 0 || regen->lMapIndex >= PLAYERBOT_INSTANCE_MAP_INDEX_MIN ||
					CDungeonManager::instance().FindByMapIndex(regen->lMapIndex))
				continue;
			CollectPlayerBotMetinProgressMembers(regen, members);
			for (size_t m = 0; m < members.size(); ++m)
			{
				const DWORD vnum = members[m];
				const CMob* mob = CMobManager::instance().Get(vnum);
				if (!mob || mob->m_table.bType != CHAR_TYPE_STONE || IsPlayerBotDungeonTriggerStone(vnum) ||
						IsPlayerBotEventStone(vnum))
					continue;
				TPlayerBotMetinProgressMap& pm = s_mapPlayerBotMetinProgress[regen->lMapIndex];
				pm.mapIndex = regen->lMapIndex;
				const std::pair<long, long> centre((regen->sx + regen->ex) / 2, (regen->sy + regen->ey) / 2);
				if (std::find(pm.spots.begin(), pm.spots.end(), centre) == pm.spots.end())
					pm.spots.push_back(centre);
				const DWORD delay = regen->endTime > 0 ? (regen->time + regen->endTime) / 2 : regen->time;
				TPlayerBotMetinProgressKind* kind = NULL;
				for (size_t k = 0; k < pm.kinds.size(); ++k)
					if (pm.kinds[k].vnum == vnum)
						kind = &pm.kinds[k];
				if (!kind)
				{
					pm.kinds.push_back(TPlayerBotMetinProgressKind());
					kind = &pm.kinds.back();
					kind->vnum = vnum;
					kind->delaySec = delay;
					kind->line = regen;
				}
				else if (delay > 0 && (kind->delaySec == 0 || delay < kind->delaySec))
				{
					kind->delaySec = delay;
					kind->line = regen;
				}
			}
		}
		for (std::map<long, TPlayerBotMetinProgressMap>::iterator it = s_mapPlayerBotMetinProgress.begin();
				it != s_mapPlayerBotMetinProgress.end(); ++it)
		{
			std::string kinds;
			for (size_t k = 0; k < it->second.kinds.size(); ++k)
			{
				char buf[48];
				snprintf(buf, sizeof(buf), "%s%u/%us", k ? "," : "", it->second.kinds[k].vnum, it->second.kinds[k].delaySec);
				kinds += buf;
			}
			sys_log(0, "METIN_PROGRESS: kinds map=%ld spots=%u kinds=%s", it->first,
					(unsigned int)it->second.spots.size(), kinds.c_str());
		}
	}

	// The respawn time of the map's own Metins of this kind, by the regen's rule (regen_event).
	DWORD GetPlayerBotMetinProgressDelayMs(long mapIndex, const TPlayerBotMetinProgressKind& kind)
	{
		DWORD delay = kind.delaySec;
		if (kind.line && kind.line->endTime > 0)
			delay = number(kind.line->time, kind.line->endTime);
		if (delay == 0)
			delay = 300;
		quest::CQuestManager& q = quest::CQuestManager::instance();
		int flag = MINMAX(0, q.GetEventFlag(("fastMetinSpawn" + std::to_string(mapIndex)).c_str()), 100);
		if (flag == 0)
			flag = MINMAX(0, q.GetEventFlag("fastMetinSpawn"), 100);
		if (flag)
			delay = MAX(3, delay * flag / 100);
		return delay * 1000U;
	}

	bool IsPlayerBotMetinProgressSpotGood(const TPlayerBotMetinProgressMap& pm, long x, long y)
	{
		const long map = pm.mapIndex;
		if (IsPlayerBotPositionBlocked(map, x, y) || IsPlayerBotPositionWater(map, x, y) || IsPlayerBotSafeZone(map, x, y))
			return false;
		for (size_t i = 0; i < pm.spots.size(); ++i)
			if (DISTANCE_APPROX(x - pm.spots[i].first, y - pm.spots[i].second) < PLAYERBOT_METIN_PROGRESS_SPOT_GAP)
				return false;
		for (size_t k = 0; k < pm.kinds.size(); ++k)
			for (size_t v = 0; v < pm.kinds[k].vids.size(); ++v)
			{
				LPCHARACTER stone = CHARACTER_MANAGER::instance().Find(pm.kinds[k].vids[v]);
				if (stone && DISTANCE_APPROX(x - stone->GetX(), y - stone->GetY()) < PLAYERBOT_METIN_PROGRESS_STONE_GAP)
					return false;
			}
		CPlayerBotNavigation& navigation = CPlayerBotNavigation::instance(map);
		if (navigation.Init(map) && navigation.IsInPocketWorld(x, y))
			return false;
		// on ground joined to one of the map's own stone spots (an anchor that is itself on open ground)
		for (size_t i = 0; i < pm.spots.size(); ++i)
			if (IsPlayerBotReachable(map, pm.spots[i].first, pm.spots[i].second, x, y))
				return true;
		return false;
	}

	LPCHARACTER SpawnPlayerBotMetinProgressStone(TPlayerBotMetinProgressMap& pm, TPlayerBotMetinProgressKind& kind, DWORD dwNow)
	{
		LPSECTREE_MAP sectreeMap = SECTREE_MANAGER::instance().GetMap(pm.mapIndex);
		if (!sectreeMap)
			return NULL;
		const TMapSetting& s = sectreeMap->m_setting;
		const int margin = PLAYERBOT_METIN_PROGRESS_EDGE;
		if (s.iWidth <= margin * 2 || s.iHeight <= margin * 2)
			return NULL;
		for (int t = 0; t < PLAYERBOT_METIN_PROGRESS_TRIES; ++t)
		{
			const long x = s.iBaseX + margin + number(0, s.iWidth - margin * 2 - 1);
			const long y = s.iBaseY + margin + number(0, s.iHeight - margin * 2 - 1);
			if (!IsPlayerBotMetinProgressSpotGood(pm, x, y))
				continue;
			LPCHARACTER stone = CHARACTER_MANAGER::instance().SpawnMob(kind.vnum, pm.mapIndex, x, y, 0, false, -1, true);
			if (!stone)
				continue;
			kind.vids.push_back(stone->GetVID());
			RememberPlayerBotMetin(stone, dwNow);
			return stone;
		}
		++kind.failed;
		return NULL;
	}

	void ManagePlayerBotMetinProgress(DWORD dwNow)
	{
		if (s_dwPlayerBotMetinProgressNextPass != 0 && (int)(dwNow - s_dwPlayerBotMetinProgressNextPass) < 0)
			return;
		s_dwPlayerBotMetinProgressNextPass = dwNow + PLAYERBOT_METIN_PROGRESS_PASS_MS;
		if (!s_bPlayerBotMetinProgressRead)
		{
			// the regen is loaded with the maps, before the first bot is in the game
			if (!regen_list)
				return;
			ReadPlayerBotMetinProgressKinds();
		}
		const bool off = quest::CQuestManager::instance().GetEventFlag("m2_metin_progress_off") != 0;
		int budget = PLAYERBOT_METIN_PROGRESS_SPAWNS_PER_PASS;
		for (std::map<long, TPlayerBotMetinProgressMap>::iterator it = s_mapPlayerBotMetinProgress.begin();
				it != s_mapPlayerBotMetinProgress.end(); ++it)
		{
			TPlayerBotMetinProgressMap& pm = it->second;
			const int bots = GetPlayerBotsOnMap(pm.mapIndex);
			int tier = 0;
			const int target = off ? 0 : GetPlayerBotMetinProgressExtra(bots, &tier);
			int aliveAll = 0, pendingAll = 0;
			for (size_t k = 0; k < pm.kinds.size(); ++k)
			{
				TPlayerBotMetinProgressKind& kind = pm.kinds[k];
				// the dead: a replacement after the regen's respawn time
				for (size_t v = 0; v < kind.vids.size(); )
				{
					LPCHARACTER stone = CHARACTER_MANAGER::instance().Find(kind.vids[v]);
					if (!stone || stone->IsDead() || stone->GetMapIndex() != pm.mapIndex || !stone->IsStone() ||
							stone->GetRaceNum() != kind.vnum)
					{
						kind.due.push_back(dwNow + GetPlayerBotMetinProgressDelayMs(pm.mapIndex, kind));
						kind.vids.erase(kind.vids.begin() + v);
					}
					else
						++v;
				}
				// fewer asked for: the living stand, the replacements beyond the target are dropped (the latest first)
				std::sort(kind.due.begin(), kind.due.end(), [dwNow](DWORD a, DWORD b) { return (int)(a - dwNow) < (int)(b - dwNow); });
				while (!kind.due.empty() && (int)(kind.vids.size() + kind.due.size()) > target)
					kind.due.pop_back();
				// more asked for: the difference at once
				int fresh = target - (int)(kind.vids.size() + kind.due.size());
				while (fresh-- > 0 && budget > 0)
				{
					--budget;
					LPCHARACTER stone = SpawnPlayerBotMetinProgressStone(pm, kind, dwNow);
					if (!stone)
						break;
					++kind.spawned;
					PlayerBotLogThrottled("metin_progress_spawn", dwNow,
							"METIN_PROGRESS: spawned map=%ld vnum=%u pos=(%ld,%ld) bots=%d tier=%d target=%d alive=%u",
							pm.mapIndex, kind.vnum, stone->GetX(), stone->GetY(), bots, tier, target,
							(unsigned int)kind.vids.size());
				}
				// the replacements that are due
				while (budget > 0 && !kind.due.empty() && (int)(dwNow - kind.due.front()) >= 0 && (int)kind.vids.size() < target)
				{
					--budget;
					LPCHARACTER stone = SpawnPlayerBotMetinProgressStone(pm, kind, dwNow);
					if (!stone)
					{
						kind.due.front() = dwNow + PLAYERBOT_METIN_PROGRESS_PASS_MS;	// no ground found: next pass
						break;
					}
					kind.due.erase(kind.due.begin());
					++kind.replaced;
					PlayerBotLogThrottled("metin_progress_replace", dwNow,
							"METIN_PROGRESS: replaced map=%ld vnum=%u pos=(%ld,%ld) bots=%d tier=%d target=%d alive=%u",
							pm.mapIndex, kind.vnum, stone->GetX(), stone->GetY(), bots, tier, target,
							(unsigned int)kind.vids.size());
				}
				aliveAll += (int)kind.vids.size();
				pendingAll += (int)kind.due.size();
			}
			pm.lastTarget = target;
			pm.lastBots = bots;
			if (pm.nextCensus == 0 || (int)(dwNow - pm.nextCensus) >= 0)
			{
				pm.nextCensus = dwNow + PLAYERBOT_METIN_PROGRESS_CENSUS_MS;
				unsigned int spawned = 0, replaced = 0, failed = 0;
				for (size_t k = 0; k < pm.kinds.size(); ++k)
				{
					spawned += pm.kinds[k].spawned;
					replaced += pm.kinds[k].replaced;
					failed += pm.kinds[k].failed;
				}
				if (bots > 0 || aliveAll > 0 || pendingAll > 0)
					sys_log(0, "METIN_PROGRESS: census map=%ld bots=%d tier=%d kinds=%u extra_each=%d extra_target=%d alive=%d pending=%d spawned=%u replaced=%u failed=%u off=%d",
							pm.mapIndex, bots, tier, (unsigned int)pm.kinds.size(), target, target * (int)pm.kinds.size(),
							aliveAll, pendingAll, spawned, replaced, failed, off ? 1 : 0);
			}
		}
	}
}

#endif

#endif
