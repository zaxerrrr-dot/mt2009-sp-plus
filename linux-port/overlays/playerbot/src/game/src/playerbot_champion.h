// MT2009_PLUS_CHAMPION_V1 / MT2009_PLUS_SUNGMA_V1: Poziom Czempiona (conqueror level) and the Sung Ma
// stats - server-patches/czempion/README.md, plan cache/yohara/plan-champion-sungma.md.
//
// The logic follows Ameria's ENABLE_YOHARA_SYSTEM (the only complete public one), the numbers come from the
// GF 26.1.11 client (<map>/sungma_attr.txt) and Owsap v6.2.6 (mob_proto SungMaExp, the quests' names).
// Stage B (MT2009_PLUS_CHAMPION_V2, the Yohara 3.0 exe): the numbers are POINT_CONQUEROR_* / POINT_SUNGMA_* of the
// points packet and point changes (SendInfo), the champion level of everyone travels in the add/update packets
// (dwConquerorLevel); "sungma_map <str> <hp> <move> <immune>" (all 0 off a Sung Ma map) stays a chat command, read
// by the character window's Sung Ma page (root uicharacter.py). Stage A's "champion_info" line and uichampion.py
// are gone (README.md, "Etap B").
//
// Champion data lives in player.player (czempion.sql) through TPlayerTable: conqueror_level, _level_step,
// _exp, _point and sungma_str/hp/move/immune (the real, spent points). The Sung Ma points of a character are
// POINT_SUNGMA_* (server-only points after POINT_PACKET_NUM): the real value plus whatever items or affects
// add later (APPLY_SUNGMA_* comes with Yohara's items). Every requirement is checked on GetPoint().
#ifndef MT2009_PLUS_PLAYERBOT_CHAMPION_H
#define MT2009_PLUS_PLAYERBOT_CHAMPION_H

#include <string>

class CHARACTER;
typedef CHARACTER* LPCHARACTER;

namespace champion
{
	enum
	{
		MAX_LEVEL = 30,			// the wiki's and Ameria's PLAYER_CONQUEROR_LEVEL
		POINTS_PER_LEVEL = 3,	// one at each quarter of the bar, the fourth is the level (Ameria)
		STAT_MAX = 90,			// highest real value of one Sung Ma stat (Ameria: MAX_STAT)
	};

	// The Obrona Statku (Hydra) quest flag that unlocks the Champion: obrona_statku.quest sets it for a
	// person of level 120+ present at the Hydra's death. THE one place that names it - rename it here.
	extern const char* const HYDRA_DONE_FLAG;

	struct SungmaRequirement
	{
		int str, hp, move, immune;
	};

	// A map's requirement (lMapIndex may be a private instance, base*10000+n), NULL off a Sung Ma map.
	// The table (share/locale/<locale>/sungma_table.txt) names maps, map/index gives their numbers (any core's);
	// a name our world does not have never matches - the system stays dormant until a Yohara map comes.
	const SungmaRequirement* MapRequirement(long lMapIndex);
	bool IsSungmaMap(long lMapIndex);
	// Champion experience of a monster (sungma_mob_exp.txt, from Owsap's mob_proto SungMaExp); 0 if none.
	unsigned int MobExp(unsigned int dwRaceVnum);
	// Re-reads both files (GM: /champion reload).
	void Reload();

	unsigned int NextExp(int iLevel);
	// conqueror_exp_rate (event flag, per cent; 0 or unset = 100): the calibration of champion experience.
	int ExpRatePct();

	// 0 ok; 1 already a Champion; 2 level below the server's max level; 3 the Hydra flag missing;
	// 4 less than one full bubble of experience (a quarter of the bar); 5 a bot (bots: not for now).
	int UnlockState(LPCHARACTER ch);
	bool Unlock(LPCHARACTER ch);
	void GainExp(LPCHARACTER ch, unsigned int dwExp);
	// Spends a point on one stat (0 str, 1 hp, 2 move, 3 immune); false when nothing changes.
	bool SpendPoint(LPCHARACTER ch, int idx);
	// Gives back the points of one stat (Nowa Wola 72068-72071; idx as above).
	bool ResetStat(LPCHARACTER ch, int idx);
	void SendInfo(LPCHARACTER ch);
	void SendMap(LPCHARACTER ch);
}

#endif
