#ifndef __INC_METIN2_PLAYERBOT_SPIDER3_BOTS_H__
#define __INC_METIN2_PLAYERBOT_SPIDER3_BOTS_H__

// MT2009_PLUS_SPIDER3_BOTS_V1 - the bots in the third Spider Dungeon (217, metin2_map_spiderdungeon_03).
//
// The owner, 28 October 2026: "the bots that do very well on V2 (map 71) move on to V3". V3 is V2's
// level band again (the five Best. poison spiders of 60-68, 2071-2075) with about twice the health
// and the level-65 weapons up to +5 in the drop - harder ground, not higher ground. So V3 is not a
// rung of the level draw: it replaces V2 in a bot's draw (GetPlayerBotFrontierMapForLevel,
// playerbot_travel.h) once the bot has shown in V2 that it is strong enough there, and gives it back
// when it is not any more. "Very well" is read from what this core sees of the bot in V2:
//  * its level is in V3's band (the panel's map table, row "spider3": 66-80 - the upper half of V2's
//    60-68 and on to the Forest's / Doyyumhwaji's 80, past V2's 78);
//  * its gear is V3's (IsPlayerBotSpiderGearReady: weapon +7, body armour +6, a helmet, a weapon of
//    its level, 60 red potions - V2 asks +6 / +5 / 40);
//  * its record in V2 since this core started: PLAYERBOT_SPIDER3_V2_KILLS kills there and at least
//    PLAYERBOT_SPIDER3_V2_KILLS_PER_DEATH of them for every death there (300 kills and at most two
//    deaths, 450 and three ...).
// A bot so promoted stays promoted while its level and gear hold. It is sent back to V2 when it falls
// PLAYERBOT_SPIDER3_DEMOTE_DEATHS times in V3 within PLAYERBOT_SPIDER3_DEMOTE_WINDOW_MS - its V2 record
// starts again and V3 is shut for it for PLAYERBOT_SPIDER3_DEMOTE_PAUSE_MS. The record lives in the
// core's memory; a bot that finds itself in V3 after a restart keeps its place there (it was promoted).
// The road in and out is V2's (IsPlayerBotSpiderMap): the desert's Kuahlo gate and a server-side move
// to V3's Town.txt, or straight from V2 - a bot never takes the warp NPCs 10097 / 10098.
//
// The log: PLAYERBOT_SPIDER3 (promoted / kept after restart / left / demoted, and a census every ten
// minutes: bots on V2 and V3, promoted, levels, kills and deaths in V3).
//
// Included by playerbot_manager.cpp before playerbot_travel.h, in its anonymous namespace.

#include <map>

namespace
{
	// playerbot_travel.h
	bool IsPlayerBotSpiderGearReady(LPCHARACTER ch, long map);

	const DWORD PLAYERBOT_SPIDER3_V2_KILLS = 300;
	const DWORD PLAYERBOT_SPIDER3_V2_KILLS_PER_DEATH = 150;
	const int PLAYERBOT_SPIDER3_DEMOTE_DEATHS = 3;
	const DWORD PLAYERBOT_SPIDER3_DEMOTE_WINDOW_MS = 30 * 60 * 1000;
	const DWORD PLAYERBOT_SPIDER3_DEMOTE_PAUSE_MS = 2 * 60 * 60 * 1000;
	const DWORD PLAYERBOT_SPIDER3_CENSUS_MS = 10 * 60 * 1000;

	struct TPlayerBotSpider3Record
	{
		DWORD dwV2Kills;
		DWORD dwV2Deaths;
		DWORD dwV3Kills;
		DWORD dwV3Deaths;
		DWORD adwV3DeathAt[PLAYERBOT_SPIDER3_DEMOTE_DEATHS];
		bool bPromoted;
		DWORD dwShutUntil;
		TPlayerBotSpider3Record() : dwV2Kills(0), dwV2Deaths(0), dwV3Kills(0), dwV3Deaths(0), bPromoted(false),
				dwShutUntil(0)
		{
			for (int i = 0; i < PLAYERBOT_SPIDER3_DEMOTE_DEATHS; ++i)
				adwV3DeathAt[i] = 0;
		}
	};

	std::map<DWORD, TPlayerBotSpider3Record> s_mapPlayerBotSpider3;
	DWORD s_dwPlayerBotSpider3CensusAt = 0;
	DWORD s_uPlayerBotSpider3Promotions = 0;
	DWORD s_uPlayerBotSpider3Demotions = 0;
	DWORD s_uPlayerBotSpider3Left = 0;
	DWORD s_uPlayerBotSpider3V3Kills = 0;
	DWORD s_uPlayerBotSpider3V3Deaths = 0;

	bool IsPlayerBotSpider3Bot(LPCHARACTER ch)
	{
		return ch && ch->IsPC() && s_mapPlayerBotAIStates.find(ch->GetPlayerID()) != s_mapPlayerBotAIStates.end();
	}

	bool IsPlayerBotSpider3LevelOpen(int level)
	{
		using namespace playerbot_progression;
		return level >= (int)MapFrom(MAP_SPIDER3) && level <= (int)MapTo(MAP_SPIDER3);
	}

	// BattlePassOnKill (playerbot_battlepass.h): a bot's kill in V2 or V3.
	void NotePlayerBotSpider3Kill(LPCHARACTER killer, LPCHARACTER victim)
	{
		if (!killer || !victim || victim->IsPC() || !IsPlayerBotSpider3Bot(killer))
			return;
		const long map = killer->GetMapIndex();
		if (map == PLAYERBOT_MAP_SPIDER_V2)
			++s_mapPlayerBotSpider3[killer->GetPlayerID()].dwV2Kills;
		else if (map == PLAYERBOT_MAP_SPIDER_V3)
		{
			++s_mapPlayerBotSpider3[killer->GetPlayerID()].dwV3Kills;
			++s_uPlayerBotSpider3V3Kills;
		}
	}

	// The death pass (playerbot_survival.h): a bot fallen in V2 or V3.
	void NotePlayerBotSpider3Death(LPCHARACTER ch, DWORD dwNow)
	{
		if (!ch)
			return;
		const long map = ch->GetMapIndex();
		if (map != PLAYERBOT_MAP_SPIDER_V2 && map != PLAYERBOT_MAP_SPIDER_V3)
			return;
		TPlayerBotSpider3Record& r = s_mapPlayerBotSpider3[ch->GetPlayerID()];
		if (map == PLAYERBOT_MAP_SPIDER_V2)
		{
			++r.dwV2Deaths;
			return;
		}
		++r.dwV3Deaths;
		++s_uPlayerBotSpider3V3Deaths;
		for (int i = 0; i + 1 < PLAYERBOT_SPIDER3_DEMOTE_DEATHS; ++i)
			r.adwV3DeathAt[i] = r.adwV3DeathAt[i + 1];
		r.adwV3DeathAt[PLAYERBOT_SPIDER3_DEMOTE_DEATHS - 1] = dwNow ? dwNow : 1;
		const DWORD oldest = r.adwV3DeathAt[0];
		if (r.bPromoted && oldest != 0 && dwNow - oldest <= PLAYERBOT_SPIDER3_DEMOTE_WINDOW_MS)
		{
			r.bPromoted = false;
			r.dwV2Kills = 0;
			r.dwV2Deaths = 0;
			for (int i = 0; i < PLAYERBOT_SPIDER3_DEMOTE_DEATHS; ++i)
				r.adwV3DeathAt[i] = 0;
			r.dwShutUntil = dwNow + PLAYERBOT_SPIDER3_DEMOTE_PAUSE_MS;
			if (!r.dwShutUntil)
				r.dwShutUntil = 1;
			++s_uPlayerBotSpider3Demotions;
			sys_log(0, "PLAYERBOT_SPIDER3: demoted pid=%u name=%s level=%u deaths_in_window=%d window_min=%u v3_kills=%u v3_deaths=%u back_in_min=%u",
					ch->GetPlayerID(), ch->GetName(), (unsigned int)ch->GetLevel(), PLAYERBOT_SPIDER3_DEMOTE_DEATHS,
					(unsigned int)(PLAYERBOT_SPIDER3_DEMOTE_WINDOW_MS / 60000), r.dwV3Kills, r.dwV3Deaths,
					(unsigned int)(PLAYERBOT_SPIDER3_DEMOTE_PAUSE_MS / 60000));
		}
	}

	int GetPlayerBotSpider3WornPlus(LPCHARACTER ch, BYTE wear)
	{
		LPITEM item = ch ? ch->GetWear(wear) : NULL;
		return item ? (int)item->GetRefineLevel() : -1;
	}

	void LogPlayerBotSpider3Census(DWORD dwNow)
	{
		if (s_dwPlayerBotSpider3CensusAt != 0 && dwNow - s_dwPlayerBotSpider3CensusAt < PLAYERBOT_SPIDER3_CENSUS_MS)
			return;
		s_dwPlayerBotSpider3CensusAt = dwNow ? dwNow : 1;
		unsigned int onV2 = 0, onV3 = 0, promoted = 0, shut = 0, recordReady = 0;
		int minLevel = 0, maxLevel = 0;
		for (TPlayerBotAIStateMap::const_iterator it = s_mapPlayerBotAIStates.begin(); it != s_mapPlayerBotAIStates.end(); ++it)
		{
			LPCHARACTER ch = CHARACTER_MANAGER::instance().FindByPID(it->first);
			if (!ch)
				continue;
			const long map = ch->GetMapIndex();
			if (map == PLAYERBOT_MAP_SPIDER_V2)
				++onV2;
			else if (map == PLAYERBOT_MAP_SPIDER_V3)
			{
				++onV3;
				const int level = (int)ch->GetLevel();
				if (minLevel == 0 || level < minLevel)
					minLevel = level;
				if (level > maxLevel)
					maxLevel = level;
			}
			std::map<DWORD, TPlayerBotSpider3Record>::const_iterator r = s_mapPlayerBotSpider3.find(it->first);
			if (r == s_mapPlayerBotSpider3.end())
				continue;
			if (r->second.bPromoted)
				++promoted;
			else if (r->second.dwShutUntil != 0 && (int)(r->second.dwShutUntil - dwNow) > 0)
				++shut;
			else if (r->second.dwV2Kills >= PLAYERBOT_SPIDER3_V2_KILLS &&
					r->second.dwV2Deaths * PLAYERBOT_SPIDER3_V2_KILLS_PER_DEATH <= r->second.dwV2Kills)
				++recordReady;
		}
		sys_log(0, "PLAYERBOT_SPIDER3: census hosted=%d band=%u-%u on_v2=%u on_v3=%u v3_levels=%d-%d promoted=%u "
				"v2_record_met_not_promoted=%u shut=%u promotions=%u demotions=%u left=%u v3_kills=%u v3_deaths=%u",
				IsPlayerBotMapHostedHere(PLAYERBOT_MAP_SPIDER_V3) ? 1 : 0,
				(unsigned int)playerbot_progression::MapFrom(playerbot_progression::MAP_SPIDER3),
				(unsigned int)playerbot_progression::MapTo(playerbot_progression::MAP_SPIDER3),
				onV2, onV3, minLevel, maxLevel, promoted, recordReady, shut, s_uPlayerBotSpider3Promotions,
				s_uPlayerBotSpider3Demotions, s_uPlayerBotSpider3Left, s_uPlayerBotSpider3V3Kills, s_uPlayerBotSpider3V3Deaths);
		s_uPlayerBotSpider3V3Kills = 0;
		s_uPlayerBotSpider3V3Deaths = 0;
	}

	// The draw's answer with V3 in V2's place for a promoted bot, V2 in V3's for one that is not
	// (GetPlayerBotFrontierMapForLevel, playerbot_travel.h). Any other map passes through.
	long PlayerBotSpider3Map(LPCHARACTER ch, long map, DWORD dwNow)
	{
		if (!ch || (map != PLAYERBOT_MAP_SPIDER_V2 && map != PLAYERBOT_MAP_SPIDER_V3))
			return map;
		// MT2009_PLUS_SPIDER3_SWITCH_V1: with M2_SPIDER3_ON=0 no core hosts 217 - V2 stays V2, no census.
		if (!IsPlayerBotMapHostedHere(PLAYERBOT_MAP_SPIDER_V3))
			return PLAYERBOT_MAP_SPIDER_V2;
		LogPlayerBotSpider3Census(dwNow);
		const DWORD pid = ch->GetPlayerID();
		std::map<DWORD, TPlayerBotSpider3Record>::iterator it = s_mapPlayerBotSpider3.find(pid);
		const bool fresh = it == s_mapPlayerBotSpider3.end();
		TPlayerBotSpider3Record& r = s_mapPlayerBotSpider3[pid];
		const int level = (int)ch->GetLevel();
		const bool shut = r.dwShutUntil != 0 && (int)(r.dwShutUntil - dwNow) > 0;
		const bool levelOk = IsPlayerBotSpider3LevelOpen(level);
		const bool gearOk = IsPlayerBotSpiderGearReady(ch, PLAYERBOT_MAP_SPIDER_V3);
		if (fresh && ch->GetMapIndex() == PLAYERBOT_MAP_SPIDER_V3 && levelOk && gearOk)
		{
			r.bPromoted = true;
			sys_log(0, "PLAYERBOT_SPIDER3: kept after restart pid=%u name=%s level=%d", pid, ch->GetName(), level);
		}
		if (!r.bPromoted && !shut && levelOk && gearOk && r.dwV2Kills >= PLAYERBOT_SPIDER3_V2_KILLS &&
				r.dwV2Deaths * PLAYERBOT_SPIDER3_V2_KILLS_PER_DEATH <= r.dwV2Kills)
		{
			r.bPromoted = true;
			for (int i = 0; i < PLAYERBOT_SPIDER3_DEMOTE_DEATHS; ++i)
				r.adwV3DeathAt[i] = 0;
			++s_uPlayerBotSpider3Promotions;
			sys_log(0, "PLAYERBOT_SPIDER3: promoted pid=%u name=%s level=%d v2_kills=%u v2_deaths=%u weapon_plus=%d armour_plus=%d",
					pid, ch->GetName(), level, r.dwV2Kills, r.dwV2Deaths, GetPlayerBotSpider3WornPlus(ch, WEAR_WEAPON),
					GetPlayerBotSpider3WornPlus(ch, WEAR_BODY));
		}
		else if (r.bPromoted && (!levelOk || !gearOk))
		{
			r.bPromoted = false;
			r.dwV2Kills = 0;
			r.dwV2Deaths = 0;
			++s_uPlayerBotSpider3Left;
			sys_log(0, "PLAYERBOT_SPIDER3: left pid=%u name=%s level=%d reason=%s v3_kills=%u v3_deaths=%u",
					pid, ch->GetName(), level, !levelOk ? "level" : "gear", r.dwV3Kills, r.dwV3Deaths);
		}
		if (r.bPromoted)
			return PLAYERBOT_MAP_SPIDER_V3;
		return map == PLAYERBOT_MAP_SPIDER_V3 ? PLAYERBOT_MAP_SPIDER_V2 : map;
	}
}

#endif
