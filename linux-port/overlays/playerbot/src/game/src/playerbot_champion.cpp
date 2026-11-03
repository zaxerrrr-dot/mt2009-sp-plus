// MT2009_PLUS_CHAMPION_V1 / MT2009_PLUS_SUNGMA_V1: Poziom Czempiona and the Sung Ma stats (playerbot_champion.h,
// server-patches/czempion/README.md). New file outside the engine's own; the hooks are server-patches/czempion
// (edits.json). Everything that touches CHARACTER is in #ifdef ENABLE_CONQUEROR_LEVEL (the last edit of the
// patch defines it); the map table and the monsters' experience build without it, so the bots' map filters
// (champion::IsSungmaMap) link either way.
#include "stdafx.h"
#include "playerbot_champion.h"
#include "constants.h"
#include "config.h"
#include "char.h"
#include "char_manager.h"
#include "desc.h"
#include "party.h"
#include "questmanager.h"
#include "questlua.h"
#include "locale_service.h"
#include "priv_manager.h"
#include "log.h"
#include "utils.h"
#include "cmd.h"
#include "affect.h"
#include "packet.h"
#include "dungeon.h"
#include "sectree_manager.h"
#include "playerbot_yohara_gear.h"
#include "p2p.h"
#include "db.h"
#include "buffer_manager.h"

#include <cctype>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

namespace champion
{
	// The Hydra's flag (obrona_statku.quest, cache/yohara/plan-hydra.md): set for a person of level 120+
	// present when the Hydra dies. The only place in the engine that names it.
	const char* const HYDRA_DONE_FLAG = "obrona_statku.completed_at_120";

	// Ameria's exp_table_conqueror_common: the experience from level n to n+1 (30 = the top, no more).
	static const unsigned int s_aExpTable[MAX_LEVEL + 1] =
	{
		0,
		433400, 1300204, 2600413, 4334029, 6501054, 9101490, 12135339, 15602603, 19503284, 23837384,
		28604905, 33805849, 39440218, 45508014, 52009239, 58943895, 66311984, 74113508, 82348469, 91016869,
		100118710, 109653994, 119622723, 130024899, 140860524, 152129600, 163832129, 175968113, 188537554,
		0,
	};

	unsigned int NextExp(int iLevel)
	{
		if (iLevel < 1 || iLevel >= MAX_LEVEL)
			return 0;
		return s_aExpTable[iLevel];
	}

	int ExpRatePct()
	{
		const int iRate = quest::CQuestManager::instance().GetEventFlag("conqueror_exp_rate");
		if (iRate <= 0)
			return 100;
		return MIN(iRate, 100000);
	}

	// MT2009_PLUS_BOT_YOHARA_MAPS_V1: conqueror_exp_rate_bot (event flag, per cent; 0 or unset = 100) - the bots'
	// champion experience on top of conqueror_exp_rate (plan-boty-yohara.md, D4).
	int BotExpRatePct()
	{
		const int iRate = quest::CQuestManager::instance().GetEventFlag("conqueror_exp_rate_bot");
		if (iRate <= 0)
			return 100;
		return MIN(iRate, 100000);
	}

	// ---- data files -------------------------------------------------------------------------------------

	struct TState
	{
		bool loaded = false;
		std::map<std::string, SungmaRequirement> byName;	// lower-case map name -> requirement
		std::map<long, const SungmaRequirement*> byIndex;	// map index (map/index) -> requirement
		std::map<unsigned int, unsigned int> mobExp;
	};

	static TState& State()
	{
		static TState s;
		return s;
	}

	static std::string Lower(std::string s)
	{
		for (size_t i = 0; i < s.size(); ++i)
			s[i] = (char)std::tolower((unsigned char)s[i]);
		return s;
	}

	static bool NextDataLine(std::istream& in, std::istringstream& line)
	{
		std::string s;
		while (std::getline(in, s))
		{
			if (!s.empty() && s[s.size() - 1] == '\r')
				s.erase(s.size() - 1);
			const size_t first = s.find_first_not_of(" \t");
			if (first == std::string::npos || s[first] == '#' || s.compare(first, 2, "//") == 0)
				continue;
			line.clear();
			line.str(s);
			return true;
		}
		return false;
	}

	static void Load()
	{
		TState& st = State();
		st.loaded = true;
		st.byName.clear();
		st.byIndex.clear();
		st.mobExp.clear();

		const std::string base = LocaleService_GetBasePath();
		{
			// sungma_table.txt: <map name> <str> <hp> <move> <immune> [<hit_pct>] (MT2009_PLUS_PRECISION_V1: the 6th
			// column, the map's Precyzja; a line without it asks none)
			std::ifstream in((base + "/sungma_table.txt").c_str());
			std::istringstream line;
			while (in && NextDataLine(in, line))
			{
				std::string name;
				SungmaRequirement r = { 0, 0, 0, 0, 0 };
				if (!(line >> name >> r.str >> r.hp >> r.move >> r.immune))
					continue;
				if (!(line >> r.hit))
					r.hit = 0;
				st.byName[Lower(name)] = r;
			}
		}
		{
			// sungma_mob_exp.txt: <vnum> <champion exp>
			std::ifstream in((base + "/sungma_mob_exp.txt").c_str());
			std::istringstream line;
			while (in && NextDataLine(in, line))
			{
				unsigned int vnum = 0, exp = 0;
				if ((line >> vnum >> exp) && vnum && exp)
					st.mobExp[vnum] = exp;
			}
		}
		{
			// map/index: <index> <map name> - every map of the world, whichever core hosts it (the bots' map
			// filter asks about maps of other cores too).
			std::ifstream in((LocaleService_GetMapPath() + "/index").c_str());
			std::istringstream line;
			while (in && !st.byName.empty() && NextDataLine(in, line))
			{
				long lIndex = 0;
				std::string name;
				if (!(line >> lIndex >> name) || lIndex <= 0)
					continue;
				std::map<std::string, SungmaRequirement>::const_iterator n = st.byName.find(Lower(name));
				if (n != st.byName.end())
					st.byIndex[lIndex] = &n->second;
			}
		}
		sys_log(0, "CHAMPION: %u Sung Ma map(s) named, %u of them in map/index, %u monster(s) with champion experience",
				(unsigned)st.byName.size(), (unsigned)st.byIndex.size(), (unsigned)st.mobExp.size());
	}

	void Reload()
	{
		Load();
	}

	// MT2009_PLUS_YOHARA_DUNG4_V1 (sungma): a dungeon instance's own requirement, set by its quest (d.set_sungma) -
	// Wieza Sung Mahi's floors ask more every five floors (pl-wiki "Wieza Sung Mahi": 35/25/35/55 .. 70/58/70/90)
	// than the map's one line in sungma_table.txt. Keyed by the instance's map index (base*10000+n); the quest sets
	// it when an instance starts (an index comes back with a new instance of the same map only) and clears it.
	static std::map<long, SungmaRequirement>& InstanceTable()
	{
		static std::map<long, SungmaRequirement> s;
		return s;
	}

	void SetInstanceRequirement(long lMapIndex, const SungmaRequirement* pReq)
	{
		if (lMapIndex < 10000)
			return;
		if (pReq)
			InstanceTable()[lMapIndex] = *pReq;
		else
			InstanceTable().erase(lMapIndex);
	}

	const SungmaRequirement* MapRequirement(long lMapIndex)
	{
		TState& st = State();
		if (!st.loaded)
			Load();
		if (lMapIndex >= 10000)
		{
			std::map<long, SungmaRequirement>::const_iterator o = InstanceTable().find(lMapIndex);
			if (o != InstanceTable().end())
				return &o->second;
		}
		if (st.byIndex.empty() || lMapIndex <= 0)
			return NULL;
		const long lBase = lMapIndex >= 10000 ? lMapIndex / 10000 : lMapIndex;
		std::map<long, const SungmaRequirement*>::const_iterator it = st.byIndex.find(lBase);
		return it == st.byIndex.end() ? NULL : it->second;
	}

	bool IsSungmaMap(long lMapIndex)
	{
		return MapRequirement(lMapIndex) != NULL;
	}

	unsigned int MobExp(unsigned int dwRaceVnum)
	{
		TState& st = State();
		if (!st.loaded)
			Load();
		std::map<unsigned int, unsigned int>::const_iterator it = st.mobExp.find(dwRaceVnum);
		return it == st.mobExp.end() ? 0 : it->second;
	}
}

#ifdef ENABLE_CONQUEROR_LEVEL

// MT2009_PLUS_CHAMPION_V2: Stage B - the numbers the Yohara 3.0 exe has (client-patches/exe/Server/common/length.h,
// UserInterface/Mt2009Champion.cpp asserts the same).
static_assert(POINT_ENCHANT_ELECT == 178, "the element powers must stay 178-183 (the talismans' item_proto applytypes)");
static_assert(POINT_SUNGMA_STR == 184 && POINT_SUNGMA_IMMUNE == 187, "POINT_SUNGMA_* = APPLY_SUNGMA_* 184-187 (exe)");
static_assert(POINT_CONQUEROR_LEVEL == 188 && POINT_CONQUEROR_POINT == 192, "POINT_CONQUEROR_* 188-192 (exe)");
static_assert(POINT_PACKET_NUM == 193, "the points packet carries 193 points (the exe's POINT_PACKET_NUM)");
// MT2009_PLUS_PRECISION_V1: POINT_SUNGMA_PER_* 193-196 and POINT_HIT_PCT 197 follow it (POINT_MAX_NUM 198) - sent as
// point changes (SendInfo, PointChange), asserted in playerbot_yohara_gear.cpp.
static_assert(LIMIT_CONQUEROR_LEVEL == 10, "LIMIT_CONQUEROR_LEVEL is 10 in the exe");
static_assert(sizeof(TPacketGCPoints) == 1 + 4 * 193, "the points packet the exe reads (773 B)");
static_assert(sizeof(TPacketGCCharacterAdditionalInfo) == 70, "GC additional info as the exe reads it (70 B)");
static_assert(sizeof(TPacketGCCharacterUpdate) == 52, "GC character update as the exe reads it (52 B)");

// char.cpp PointsPacket (MT2009_PLUS_CHAMPION_V2 (points packet)): the champion's numbers are fields of m_points,
// not points; the Sung Ma stats are points and travel in PointsPacket's own loop.
void ChampionFillPoints(LPCHARACTER ch, INT* aiPoints)
{
	const bool bReal = ch && ch->IsPC() && ch->GetConquerorLevel() >= 1;
	aiPoints[POINT_CONQUEROR_LEVEL] = bReal ? ch->GetConquerorLevel() : 0;
	aiPoints[POINT_CONQUEROR_LEVEL_STEP] = bReal ? ch->GetConquerorLevelStep() : 0;
	aiPoints[POINT_CONQUEROR_EXP] = bReal ? (INT)ch->GetConquerorExp() : 0;
	aiPoints[POINT_CONQUEROR_NEXT_EXP] = bReal ? (INT)ch->GetConquerorNextExp() : 0;
	aiPoints[POINT_CONQUEROR_POINT] = bReal ? ch->GetConquerorPoint() : 0;
}

namespace champion
{
	static const BYTE s_aStatPoint[4] = { POINT_SUNGMA_STR, POINT_SUNGMA_HP, POINT_SUNGMA_MOVE, POINT_SUNGMA_IMMUNE };
	static const char* const s_aStatName[4] = { "Sila", "Witalnosc", "Odpornosc", "Inteligencja" };

	static bool IsBotCharacter(LPCHARACTER ch)
	{
		return ch && ch->GetDesc() && ch->GetDesc()->IsBot();
	}

	// MT2009_PLUS_CHAMPION_V2: Stage B - the numbers go as points (the exe's POINT_CONQUEROR_*/POINT_SUNGMA_*, the
	// character window's Sung Ma page reads player.GetStatus); Stage A's "champion_info" chat line is gone (a 3.0
	// client only - older ones are refused at login, server_version in m2-render-config).
	static void SendPoint(LPCHARACTER ch, BYTE bType, long lValue)
	{
		TPacketGCPointChange pack;
		pack.header = HEADER_GC_CHARACTER_POINT_CHANGE;
		pack.dwVID = ch->GetVID();
		pack.type = bType;
		pack.amount = 0;
		pack.value = lValue;
		ch->GetDesc()->Packet(&pack, sizeof(pack));
	}

	void SendInfo(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC() || !ch->GetDesc() || IsBotCharacter(ch))
			return;
		INT aiPoints[POINT_PACKET_NUM] = {};
		ChampionFillPoints(ch, aiPoints);
		for (int i = POINT_CONQUEROR_LEVEL; i <= POINT_CONQUEROR_POINT; ++i)
			SendPoint(ch, (BYTE)i, aiPoints[i]);
		for (int i = 0; i < 4; ++i)
			SendPoint(ch, s_aStatPoint[i], ch->GetPoint(s_aStatPoint[i]));
		// MT2009_PLUS_PRECISION_V1: the Sung Ma per cent bonuses and Precyzja (not in the points packet)
		for (int i = POINT_SUNGMA_PER_STR; i <= POINT_HIT_PCT; ++i)
			SendPoint(ch, (BYTE)i, ch->GetPoint((BYTE)i));
	}

	void SendMap(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC() || !ch->GetDesc() || IsBotCharacter(ch))
			return;
		const SungmaRequirement* pReq = MapRequirement(ch->GetMapIndex());
		if (!pReq)
		{
			ch->ChatPacket(CHAT_TYPE_COMMAND, "sungma_map 0 0 0 0 0");
			return;
		}
		// MT2009_PLUS_PRECISION_V1: the 5th number is the map's Precyzja (root: the Sung Ma page, the affect bar)
		ch->ChatPacket(CHAT_TYPE_COMMAND, "sungma_map %d %d %d %d %d", pReq->str, pReq->hp, pReq->move, pReq->immune,
				pReq->hit);
		if (ch->GetConquerorLevel() < 1)
			ch->ChatPacket(CHAT_TYPE_INFO, "To ziemia Sung Ma: bez Poziomu Czempiona nie zranisz tutejszych potworow.");
		else if (yohara_gear::SungmaEffective(ch, POINT_SUNGMA_STR) < pReq->str ||
				yohara_gear::SungmaEffective(ch, POINT_SUNGMA_HP) < pReq->hp ||
				yohara_gear::SungmaEffective(ch, POINT_SUNGMA_MOVE) < pReq->move ||
				yohara_gear::SungmaEffective(ch, POINT_SUNGMA_IMMUNE) < pReq->immune)
			ch->ChatPacket(CHAT_TYPE_INFO, "Ziemia Sung Ma wymaga: Sila %d, Witalnosc %d, Odpornosc %d, Inteligencja %d - "
					"przy brakach Twoja sila slabnie o polowe.", pReq->str, pReq->hp, pReq->move, pReq->immune);
	}

	int UnlockState(LPCHARACTER ch)
	{
		// MT2009_PLUS_BOT_CHAMPION_V1: a bot too (the owner, 22 October: "boty ida do posagu po poziom
		// Czempiona") - the statue's errand of the Hydra's bots (playerbot_yohara_bots.h) asks the same
		// conditions; 5 is left for what is not a person.
		if (!ch || !ch->IsPC())
			return 5;
		if (ch->GetConquerorLevel() >= 1)
			return 1;
		if (ch->GetLevel() < gPlayerMaxLevel)
			return 2;
		if (ch->GetQuestFlag(HYDRA_DONE_FLAG) <= 0)
			return 3;
		// One full bubble of the bar (the bar has four): 625 000 000 at level 120.
		if (ch->GetExp() < ch->GetNextExp() / 4)
			return 4;
		return 0;
	}

	bool Unlock(LPCHARACTER ch)
	{
		if (UnlockState(ch) != 0)
			return false;
		ch->SetConquerorLevel(1);
		ch->SetConquerorLevelStep(0);
		ch->SetConquerorExp(0);
		ch->SetConquerorPoint(0);
		ch->Save();
		LogManager::instance().CharLog(ch, 1, "CHAMPION_UNLOCK", "");
		SendInfo(ch);
		ch->UpdatePacket();	// MT2009_PLUS_CHAMPION_V2: the blue level over the head for everyone around
		SendMap(ch);
		return true;
	}

	void GainExp(LPCHARACTER ch, unsigned int dwExp)
	{
		if (!ch || !dwExp)
			return;
		int iLevel = ch->GetConquerorLevel();
		if (iLevel < 1 || iLevel >= MAX_LEVEL)
			return;

		unsigned long long total = (unsigned long long)ch->GetConquerorExp() + dwExp;
		int iStep = MIN((int)ch->GetConquerorLevelStep(), (int)POINTS_PER_LEVEL);
		int iPoints = ch->GetConquerorPoint();
		bool bLevelUp = false;

		while (iLevel < MAX_LEVEL && total >= NextExp(iLevel))
		{
			// The quarters of this level not yet paid (crossed in one go) and the level itself.
			iPoints += (int)POINTS_PER_LEVEL - iStep;
			total -= NextExp(iLevel);
			++iLevel;
			iStep = 0;
			bLevelUp = true;
		}
		if (iLevel >= MAX_LEVEL)
			total = 0;
		else
		{
			const unsigned int q = NextExp(iLevel) / 4;
			const int iNewStep = q ? (int)MIN((unsigned long long)POINTS_PER_LEVEL, total / q) : 0;
			if (iNewStep > iStep)
			{
				iPoints += iNewStep - iStep;
				iStep = iNewStep;
			}
		}

		const int iOldPoints = ch->GetConquerorPoint();
		ch->SetConquerorLevel((BYTE)iLevel);
		ch->SetConquerorLevelStep((BYTE)iStep);
		ch->SetConquerorExp((DWORD)total);
		ch->SetConquerorPoint(iPoints);

		// MT2009_PLUS_BOT_CHAMPION_V1: no chat lines for a bot (its client is none).
		const bool bBot = IsBotCharacter(ch);
		if (bLevelUp)
		{
			if (!bBot)
				ch->ChatPacket(CHAT_TYPE_INFO, "Poziom Czempiona: %d.", iLevel);
			char hint[64];
			snprintf(hint, sizeof(hint), "level %d points %d", iLevel, iPoints);
			LogManager::instance().CharLog(ch, iLevel, "CHAMPION_LEVELUP", hint);
			ch->Save();
			ch->UpdatePacket();	// MT2009_PLUS_CHAMPION_V2: the new champion level over the head
		}
		else if (iPoints > iOldPoints && !bBot)
			ch->ChatPacket(CHAT_TYPE_INFO, "Masz nowy punkt statystyk Sung Ma (wolne: %d).", iPoints);
		SendInfo(ch);
	}

	static void Refresh(LPCHARACTER ch)
	{
		ch->ComputePoints();
		ch->PointsPacket();
		ch->UpdatePacket();
		SendInfo(ch);
	}

	bool SpendPoint(LPCHARACTER ch, int idx)
	{
		if (!ch || idx < 0 || idx > 3)
			return false;
		if (ch->GetConquerorLevel() < 1)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Statystyki Sung Ma ma tylko Czempion.");
			return false;
		}
		if (ch->GetConquerorPoint() <= 0)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Nie masz wolnych punktow Sung Ma.");
			return false;
		}
		const BYTE bPoint = s_aStatPoint[idx];
		if (ch->GetRealPoint(bPoint) >= (int)STAT_MAX)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "%s Sung Ma ma juz najwyzsza wartosc (%d).", s_aStatName[idx], (int)STAT_MAX);
			return false;
		}
		ch->SetRealPoint(bPoint, ch->GetRealPoint(bPoint) + 1);
		ch->SetConquerorPoint(ch->GetConquerorPoint() - 1);
		Refresh(ch);
		return true;
	}

	bool ResetStat(LPCHARACTER ch, int idx)
	{
		if (!ch || idx < 0 || idx > 3 || ch->GetConquerorLevel() < 1)
			return false;
		const BYTE bPoint = s_aStatPoint[idx];
		const int iOld = ch->GetRealPoint(bPoint);
		if (iOld <= 0)
			return false;
		ch->SetRealPoint(bPoint, 0);
		ch->SetConquerorPoint(ch->GetConquerorPoint() + iOld);
		Refresh(ch);
		char hint[64];
		snprintf(hint, sizeof(hint), "stat %d value %d points %d", idx, iOld, ch->GetConquerorPoint());
		LogManager::instance().CharLog(ch, idx, "CHAMPION_RESET_STAT", hint);
		return true;
	}

	// One kill's share of champion experience, with the experience bonuses of the person (event, items, mall)
	// and the calibration flag conqueror_exp_rate; at most a tenth of the bar per kill, as ordinary experience.
	static void GiveExp(LPCHARACTER pkVictim, LPCHARACTER to, unsigned int dwBase)
	{
		// MT2009_PLUS_BOT_CHAMPION_V1: a bot Champion earns it as a person does.
		if (!to || !dwBase || !to->IsPC() || to->GetConquerorLevel() < 1)
			return;
		if (to->FindAffect(AFFECT_EXP_BLOCK))
			return;
		// MT2009_PLUS_PD_BONUS_V1 (champion exp): the items' experience too - the rings, the lollipops, the amulets and the
		// costume sets (POINT_RAMADAN_CANDY_BONUS_EXP, server-patches/pdbonus), as the ordinary GiveExp counts them; the
		// Champion's bar heard only the potions and the mounts (POINT_MALL_EXPBONUS).
		const int iBonus = MAX(0, 100 + CPrivManager::instance().GetPriv(to, PRIV_EXP_PCT) + to->GetPoint(POINT_EXP) +
				to->GetPoint(POINT_MALL_EXPBONUS) + to->GetPoint(POINT_RAMADAN_CANDY_BONUS_EXP));
		unsigned long long exp = (unsigned long long)dwBase * iBonus / 100 * ExpRatePct() / 100;
		// MT2009_PLUS_BOT_YOHARA_MAPS_V1: a bot's own calibration on top (conqueror_exp_rate_bot, per cent; 0/unset = 100 -
		// a bot earns as a person does; the plan's D4: the night's measure sets it).
		if (IsBotCharacter(to))
			exp = exp * BotExpRatePct() / 100;
		const unsigned int dwCap = MAX(1u, to->GetConquerorNextExp() / 10);
		if (exp > dwCap)
			exp = dwCap;
		if (!exp)
			exp = 1;
		GainExp(to, (unsigned int)exp);
		if (pkVictim)
			pkVictim->CreateFly(FLY_CONQUEROR_EXP, to);	// MT2009_PLUS_PRECISION_V1: the champion's own (orange) fly
	}

	struct FPartyChampions
	{
		LPCHARACTER victim;
		std::vector<LPCHARACTER> members;

		explicit FPartyChampions(LPCHARACTER v) : victim(v) {}

		void operator () (LPCHARACTER ch)
		{
			if (!ch || !ch->IsPC() || ch->GetMapIndex() != victim->GetMapIndex() || ch->GetConquerorLevel() < 1)
				return;
			if (DISTANCE_APPROX(ch->GetX() - victim->GetX(), ch->GetY() - victim->GetY()) > PARTY_DEFAULT_RANGE)
				return;
			members.push_back(ch);
		}
	};
}

// ---- MT2009_PLUS_SUNGMA_BONUS_V1: the Will above a map's requirement ------------------------------------------------
// The owner, 27 October 2026 - as on the global servers (the m2-helper FAQ of the Sung Ma stats): on a Sung Ma map
// (sungma_table.txt) the effective Will (yohara_gear::SungmaEffective, the one the penalties judge) above the map's
// requirement is worth: Sila +0.01% damage at the map's monsters a point; Witalnosc +5.33 max HP a point; Odpornosc +1
// movement speed every 100; Inteligencja +1% stun and +1% slow chance (a normal hit's AttackAffect) every 100. Below the
// requirement the penalties stay as they are (Inteligencja's is the poison / fire / bleeding one, untouched).
// Recounted as the penalties are: the damage and the stun/slow at each blow, the max HP at each POINT_MAX_HP count
// (MT2009_PLUS_SUNGMA_HP_ORDER_V1 recounts it at each Witalnosc change), the speed at each GetLimitPoint (and the
// client told at each Odpornosc change: edits.json MT2009_PLUS_SUNGMA_BONUS_V1 (move speed packet)); a map change
// goes through the login (ChampionOnLogin: ComputePoints).
namespace champion
{
	const int SUNGMA_BONUS_DAMAGE_PER_10000 = 1;	// Sila: a point = 0.01%
	const int SUNGMA_BONUS_HP_PER_100 = 533;		// Witalnosc: a point = 5.33 HP
	const int SUNGMA_BONUS_MOVE_STEP = 100;		// Odpornosc: +1 speed every 100
	const int SUNGMA_BONUS_AFFECT_STEP = 100;		// Inteligencja: +1% stun / slow every 100

	// The effective Will above this map's requirement (0 off a Sung Ma map or at / below it). what: 0 str, 1 hp,
	// 2 move, 3 immune.
	int SungmaSurplus(const CHARACTER* ch, int what)
	{
		if (!ch || !ch->IsPC() || what < 0 || what > 3)
			return 0;
		const SungmaRequirement* pReq = MapRequirement(ch->GetMapIndex());
		if (!pReq)
			return 0;
		const int aReq[4] = { pReq->str, pReq->hp, pReq->move, pReq->immune };
		const int iSurplus = yohara_gear::SungmaEffective(ch, (unsigned char)(POINT_SUNGMA_STR + what)) - aReq[what];
		return iSurplus > 0 ? iSurplus : 0;
	}
}


// char_battle.cpp CHARACTER::DistributeExp, before the ordinary experience (a Yohara monster has none): the
// champion experience of a monster killed on a Sung Ma map, shared by damage like the ordinary one - a party's
// share evenly among its Champions near the kill.
void ChampionDistributeExp(LPCHARACTER pkVictim)
{
	if (!pkVictim || pkVictim->IsPC() || !champion::IsSungmaMap(pkVictim->GetMapIndex()))
		return;
	const unsigned int dwBase = champion::MobExp(pkVictim->GetRaceNum());
	if (!dwBase)
		return;

	long long llTotal = 0;
	std::vector<std::pair<LPCHARACTER, long long> > solo;
	std::map<LPPARTY, long long> parties;
	const CHARACTER::TDamageMap& rDamage = pkVictim->Mt2009PlusGetDamageMap();
	for (CHARACTER::TDamageMap::const_iterator it = rDamage.begin(); it != rDamage.end(); ++it)
	{
		if (it->second.iTotalDamage <= 0)
			continue;
		LPCHARACTER pAttacker = CHARACTER_MANAGER::instance().Find(it->first);
		if (!pAttacker || !pAttacker->IsPC() || pAttacker->GetMapIndex() != pkVictim->GetMapIndex())
			continue;
		if (DISTANCE_APPROX(pAttacker->GetX() - pkVictim->GetX(), pAttacker->GetY() - pkVictim->GetY()) > 5000)
			continue;
		llTotal += it->second.iTotalDamage;
		if (pAttacker->GetParty())
			parties[pAttacker->GetParty()] += it->second.iTotalDamage;
		else
			solo.push_back(std::make_pair(pAttacker, (long long)it->second.iTotalDamage));
	}
	if (llTotal <= 0)
		return;

	for (size_t i = 0; i < solo.size(); ++i)
	{
		const unsigned int dwShare = (unsigned int)((dwBase * solo[i].second + llTotal / 2) / llTotal);
		champion::GiveExp(pkVictim, solo[i].first, MAX(1u, dwShare));
	}
	for (std::map<LPPARTY, long long>::const_iterator it = parties.begin(); it != parties.end(); ++it)
	{
		champion::FPartyChampions f(pkVictim);
		it->first->ForEachOnlineMember(f);
		if (f.members.empty())
			continue;
		const unsigned long long llShare = (dwBase * it->second + llTotal / 2) / llTotal;
		const unsigned int dwEach = MAX(1u, (unsigned int)(llShare / f.members.size()));
		for (size_t i = 0; i < f.members.size(); ++i)
			champion::GiveExp(pkVictim, f.members[i], dwEach);
	}
}

// char.cpp PointChange(POINT_MAX_HP): Sung Ma HP below the map's requirement halves the maximum HP.
int ChampionMaxHP(const CHARACTER* ch, int iMaxHP)
{
	if (!ch || !ch->IsPC())
		return iMaxHP;
	const champion::SungmaRequirement* pReq = champion::MapRequirement(ch->GetMapIndex());
	if (pReq && yohara_gear::SungmaEffective(ch, POINT_SUNGMA_HP) < pReq->hp)
		return iMaxHP / 2;
	// MT2009_PLUS_SUNGMA_BONUS_V1: Witalnosc above the requirement - +5.33 max HP a point.
	if (pReq)
		iMaxHP += champion::SungmaSurplus(ch, 1) * champion::SUNGMA_BONUS_HP_PER_100 / 100;
	return iMaxHP;
}

// char.cpp GetLimitPoint(POINT_MOV_SPEED): Sung Ma movement below the requirement halves the speed.
int ChampionMoveSpeed(const CHARACTER* ch, int iSpeed)
{
	if (!ch || !ch->IsPC())
		return iSpeed;
	const champion::SungmaRequirement* pReq = champion::MapRequirement(ch->GetMapIndex());
	if (pReq && yohara_gear::SungmaEffective(ch, POINT_SUNGMA_MOVE) < pReq->move)
		return iSpeed / 2;
	// MT2009_PLUS_SUNGMA_BONUS_V1: Odpornosc above the requirement - +1 speed every 100 (GetLimitPoint's cap after it).
	if (pReq)
		iSpeed += champion::SungmaSurplus(ch, 2) / champion::SUNGMA_BONUS_MOVE_STEP;
	return iSpeed;
}

// battle.cpp battle_is_attackable: on a Sung Ma map a person without a Champion level cannot attack monsters.
bool ChampionCanAttack(LPCHARACTER ch, LPCHARACTER victim)
{
	if (!ch || !victim || !ch->IsPC() || victim->IsPC())
		return true;
	if (ch->GetConquerorLevel() >= 1)
		return true;
	return !champion::IsSungmaMap(ch->GetMapIndex());
}

// char_battle.cpp CHARACTER::Damage: a person's blow at a monster on a Sung Ma map - halved when Sung Ma
// strength is below the requirement, blocked (-1) without a Champion level.
int ChampionDamage(LPCHARACTER pkVictim, LPCHARACTER pAttacker, int iDam)
{
	if (!pkVictim || !pAttacker || !pAttacker->IsPC() || pkVictim->IsPC())
		return iDam;
	const champion::SungmaRequirement* pReq = champion::MapRequirement(pAttacker->GetMapIndex());
	if (!pReq)
		return iDam;
	if (pAttacker->GetConquerorLevel() < 1)
		return -1;
	// MT2009_PLUS_PRECISION_V1: the map's Precyzja (pl-wiki "Precyzja": "Proboja go trafic, postac zacznie chybiac" -
	// blows, arrows and skills alike; Owsap: (hit_pct - precision) * 100 / hit_pct per cent of them) - a stone
	// (a Metin) is never missed.
	// MT2009_PLUS_BOT_YOHARA_MAPS_V1: every bot counts as one of the top Precyzja - the owner, 22 October: "wszystkie boty
	// domyslnie maja miec maksymalny poziom Precyzji. Ten system ich nie dotyczy" - a bot's blow never misses.
	if (pReq->hit > 0 && !pkVictim->IsStone() && !champion::IsBotCharacter(pAttacker))
	{
		const int iPrecision = MAX(0, (int) pAttacker->GetPoint(POINT_HIT_PCT));
		if (iPrecision < pReq->hit && number(1, 100) <= (pReq->hit - iPrecision) * 100 / pReq->hit)
			return -1;
	}
	if (yohara_gear::SungmaEffective(pAttacker, POINT_SUNGMA_STR) < pReq->str)
		return iDam / 2;
	// MT2009_PLUS_SUNGMA_BONUS_V1: Sila above the requirement - +0.01% damage a point.
	const int iSurplus = champion::SungmaSurplus(pAttacker, 0);
	if (iSurplus > 0 && iDam > 0)
		iDam = (int)((long long)iDam * (10000 + iSurplus * champion::SUNGMA_BONUS_DAMAGE_PER_10000) / 10000);
	return iDam;
}

// MT2009_PLUS_SUNGMA_BONUS_V1: battle.h AttackAffect (a normal hit's stun / slow): a person's chance at a monster of a
// Sung Ma map grows by 1% every 100 of Inteligencja above the requirement.
int ChampionAffectBonus(LPCHARACTER pkAttacker, LPCHARACTER pkVictim, BYTE bAttPoint)
{
	if ((bAttPoint != POINT_STUN_PCT && bAttPoint != POINT_SLOW_PCT) || !pkAttacker || !pkVictim ||
			!pkAttacker->IsPC() || pkVictim->IsPC())
		return 0;
	return champion::SungmaSurplus(pkAttacker, 3) / champion::SUNGMA_BONUS_AFFECT_STEP;
}

// char_resist.cpp AttackedByPoison / AttackedByFire / AttackedByBleeding: a person's poison, fire and bleeding
// on a monster of a Sung Ma map take hold half as often while Sung Ma intelligence is below the requirement
// (Ameria halves the attacker's chance; here one check for blows and skills alike).
bool ChampionImmuneBlocks(LPCHARACTER pkAttacker, LPCHARACTER pkVictim)
{
	if (!pkAttacker || !pkVictim || !pkAttacker->IsPC() || pkVictim->IsPC())
		return false;
	const champion::SungmaRequirement* pReq = champion::MapRequirement(pkAttacker->GetMapIndex());
	if (!pReq || yohara_gear::SungmaEffective(pkAttacker, POINT_SUNGMA_IMMUNE) >= pReq->immune)
		return false;
	return number(1, 2) == 1;
}

namespace champion
{
	static void GmPendingApply(LPCHARACTER ch);	// MT2009_PLUS_CHAMPION_TARGET_V1 (below do_champion)
}

// input_login.cpp Entergame: the Sung Ma penalties counted on this map, the client told the numbers.
void ChampionOnLogin(LPCHARACTER ch)
{
	// MT2009_PLUS_BOT_CHAMPION_V1: a bot's Sung Ma penalties are counted too (SendInfo/SendMap pass bots by).
	if (!ch || !ch->IsPC())
		return;
	champion::GmPendingApply(ch);	// MT2009_PLUS_CHAMPION_TARGET_V1: a GM's changes left while it was offline
	if (champion::IsSungmaMap(ch->GetMapIndex()))
	{
		ch->ComputePoints();
		ch->PointsPacket();
	}
	champion::SendInfo(ch);
	champion::SendMap(ch);
}

// ---- MT2009_PLUS_PRECISION_SKILL_V1: the passive skill Precyzja ---------------------------------------------------
// pl-wiki "Precyzja" / "Ksiega Precyzji": a passive skill of every character, read from Ksiega Precyzji (50325) from
// Champion level 1, 0 -> P (40); a successful read is a level (1 -> M1 20 books, M1 -> G1 10, G1 -> P 10 - de wiki:
// "erfolgreiche"). SKILL_PRECISION is GF's vnum 246 (its client's skilltable row, icon hit_attribute). The read is
// LearnSkillByBook's passive one (the books' wait m2_book_wait, Zwoj Egzorcyzmu, the learn-chance potions);
// Rada Pustelnika multiplies its chance by 2.5 (35% -> 87%), as with the class books (MT2009_PLUS_RADA_PUSTELNIKA_V1). Its bonus is the wiki's table (GF's 0.4*k+16*k on the skill
// power, but the wiki's +4 at level 11), part of POINT_HIT_PCT (char.cpp ComputePoints, server-patches/precyzja).
// Bots: only a bot Champion (MT2009_PLUS_BOT_CHAMPION_V1: the statue's errand of the Hydra's bots), as a person.
static const int PRECISION_BOOK_PCT = 35;	// a read's chance - the class books' base (LearnSkillByBook)
static const int s_aPrecisionBonus[SKILL_MAX_LEVEL + 1] =
{
	0,
	0, 0, 1, 1, 1, 2, 2, 2, 3, 3,			// 1-10
	4, 4, 4, 4, 5, 5, 5, 6, 6,				// 11-19
	8, 8, 8, 9, 9, 9, 10, 10, 11, 11,		// M1-M10
	13, 13, 14, 14, 15, 16, 16, 17, 18, 18,	// G1-G10
	20,										// P
};
static_assert(sizeof(s_aPrecisionBonus) / sizeof(s_aPrecisionBonus[0]) == 41, "levels 0-40");
static_assert(SKILL_PRECISION < SKILL_MAX_NUM, "SKILL_PRECISION in the skill table (the exe's SKILL_MAX_NUM too)");

int PrecisionSkillBonus(const CHARACTER* ch)
{
	if (!ch || !ch->IsPC())
		return 0;
	// MT2009_PLUS_BOT_YOHARA_MAPS_V1: a bot has Precyzja P by default, no book needed (its blows never miss either -
	// ChampionDamage); the bonus is P's in its POINT_HIT_PCT.
	if (ch->GetDesc() && ch->GetDesc()->IsBot())
		return s_aPrecisionBonus[SKILL_MAX_LEVEL];
	return s_aPrecisionBonus[MINMAX(0, ch->GetSkillLevel(SKILL_PRECISION), (int) SKILL_MAX_LEVEL)];
}

static void PrecisionLevelName(int iLevel, char* szBuf, size_t size)
{
	if (iLevel >= 40)
		snprintf(szBuf, size, "P");
	else if (iLevel >= 30)
		snprintf(szBuf, size, "G%d", iLevel - 29);
	else if (iLevel >= 20)
		snprintf(szBuf, size, "M%d", iLevel - 19);
	else
		snprintf(szBuf, size, "%d", iLevel);
}

// char_item.cpp (book): 1 - the book was read (used up), 0 - not read.
int PrecisionReadBook(CHARACTER* ch)
{
	if (!ch || !ch->IsPC())
		return 0;
	if (ch->IsPolymorphed())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, LC_TEXT("You cannot read books while transformed."));
		return 0;
	}
	// MT2009_PLUS_BOT_YOHARA_MAPS_V1: a bot has Precyzja P already (PrecisionSkillBonus) - no book is used up on it.
	if (ch->GetDesc() && ch->GetDesc()->IsBot())
		return 0;
	// MT2009_PLUS_BOT_CHAMPION_V1: a bot Champion may read it too.
	if (ch->GetConquerorLevel() < 1)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Ksiege Precyzji przeczytasz od 1. Poziomu Czempiona.");
		return 0;
	}
	const int iBefore = ch->GetSkillLevel(SKILL_PRECISION);
	if (iBefore >= SKILL_MAX_LEVEL)
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "Twoja Precyzja ma juz najwyzszy poziom (P).");
		return 0;
	}
	// MT2009_PLUS_RADA_PUSTELNIKA_V1 (precyzja): Rada Pustelnika no longer makes the read certain here - LearnSkillByBook
	// multiplies this chance by 2.5 under it, at most 100 (server-patches/radapustelnika), as for every passive book.
	const DWORD dwPct = PRECISION_BOOK_PCT;
	if (!ch->LearnSkillByBook(SKILL_PRECISION, dwPct))
		return 0;
	const int iAfter = ch->GetSkillLevel(SKILL_PRECISION);
	if (iAfter != iBefore)
	{
		char szLevel[8];
		PrecisionLevelName(iAfter, szLevel, sizeof(szLevel));
		ch->ChatPacket(CHAT_TYPE_INFO, "Precyzja: poziom %s, bonus Precyzji +%d.", szLevel, PrecisionSkillBonus(ch));
		champion::SendInfo(ch);
	}
	return 1;
}

DWORD CHARACTER::GetConquerorNextExp() const
{
	return champion::NextExp(GetConquerorLevel());
}

// ---- commands ---------------------------------------------------------------------------------------------

// "/conqueror_stat smh_str|smh_hp|smh_move|smh_inmune" - the names GF's uicharacternew.py and root's uicharacter.py
// (the Sung Ma page) send; "/conqueror_stat info" - the numbers and the map's requirements again.
ACMD(do_conqueror_stat)
{
	char arg1[256];
	one_argument(argument, arg1, sizeof(arg1));
	if (!ch || !ch->IsPC())
		return;
	if (!*arg1 || !strcmp(arg1, "info"))
	{
		champion::SendInfo(ch);
		champion::SendMap(ch);
		return;
	}
	int idx = -1;
	if (!strcmp(arg1, "smh_str"))
		idx = 0;
	else if (!strcmp(arg1, "smh_hp"))
		idx = 1;
	else if (!strcmp(arg1, "smh_move"))
		idx = 2;
	else if (!strcmp(arg1, "smh_inmune") || !strcmp(arg1, "smh_immune"))
		idx = 3;
	if (idx < 0)
		return;
	champion::SpendPoint(ch, idx);
}

// ---- MT2009_PLUS_CHAMPION_TARGET_V1: "/champion <nick> ..." (poprawki 3.0.4 pt 6) -----------------------------
// Every subcommand of /champion also takes a character's name before it: "/champion <nick> level 30". Without a
// name (or with the GM's own) it acts on the GM, as before. The target:
//   * on this core - changed at once, its window told (champion_info / sungma_map), the GM gets its state line;
//   * online on another core (P2P_MANAGER's CCI) - HEADER_GG_CHAMPION_CMD (server-patches/czempion,
//     MT2009_PLUS_CHAMPION_TARGET_V1) to that core, which runs it there and sends the state line back to the GM
//     (a chat packet relayed through the GM's core, as a whisper is);
//   * offline - the change waits in quest flags "champion_gm.<what>" (the quest table, which the db core never
//     caches - player columns would be overwritten by its player cache for 10 minutes after a logout) and
//     ChampionOnLogin applies them at the character's next entry to the game, then clears them.
namespace champion
{
	static const char* const GM_FLAG = "champion_gm";

	// a subcommand's name (anything else after "/champion" is a character's name)
	static bool GmIsSub(const char* s)
	{
		static const char* const a[] = { "reload", "unlock", "level", "exp", "give", "points", "stat", "reset" };
		for (size_t i = 0; i < sizeof(a) / sizeof(a[0]); ++i)
			if (!strcmp(s, a[i]))
				return true;
		return false;
	}

	// one subcommand on a character of this core: false = none (state only) or not understood (nothing changed)
	static bool GmApply(LPCHARACTER ch, const char* sub, int n, int v)
	{
		if (!strcmp(sub, "unlock"))
		{
			if (ch->GetConquerorLevel() < 1)
			{
				ch->SetConquerorLevel(1);
				ch->SetConquerorLevelStep(0);
				ch->SetConquerorExp(0);
			}
		}
		else if (!strcmp(sub, "level"))
		{
			// The points a character would have earned on its way to this level (3 per level, level 1 starts
			// with none), less what it has already spent - "/champion level 30" gives 87 to spend.
			const int iLevel = MINMAX(0, n, (int)MAX_LEVEL);
			const int iSpent = ch->GetRealPoint(POINT_SUNGMA_STR) + ch->GetRealPoint(POINT_SUNGMA_HP) +
				ch->GetRealPoint(POINT_SUNGMA_MOVE) + ch->GetRealPoint(POINT_SUNGMA_IMMUNE);
			ch->SetConquerorLevel((BYTE)iLevel);
			ch->SetConquerorLevelStep(0);
			ch->SetConquerorExp(0);
			ch->SetConquerorPoint(MAX(0, MAX(0, iLevel - 1) * POINTS_PER_LEVEL - iSpent));
		}
		else if (!strcmp(sub, "exp") && n >= 0)
			ch->SetConquerorExp((DWORD)n);
		else if (!strcmp(sub, "give") && n > 0)
			GainExp(ch, (unsigned int)n);
		else if (!strcmp(sub, "points"))
			ch->SetConquerorPoint(MAX(0, n));
		else if (!strcmp(sub, "stat") && n >= 0 && n <= 3)
		{
			const BYTE aPoint[4] = { POINT_SUNGMA_STR, POINT_SUNGMA_HP, POINT_SUNGMA_MOVE, POINT_SUNGMA_IMMUNE };
			ch->SetRealPoint(aPoint[n], MINMAX(0, v, 255));
		}
		else if (!strcmp(sub, "reset"))
		{
			ch->SetConquerorLevel(0);
			ch->SetConquerorLevelStep(0);
			ch->SetConquerorExp(0);
			ch->SetConquerorPoint(0);
			ch->SetRealPoint(POINT_SUNGMA_STR, 0);
			ch->SetRealPoint(POINT_SUNGMA_HP, 0);
			ch->SetRealPoint(POINT_SUNGMA_MOVE, 0);
			ch->SetRealPoint(POINT_SUNGMA_IMMUNE, 0);
		}
		else
			return false;
		return true;
	}

	static void GmRefresh(LPCHARACTER ch)
	{
		ch->ComputePoints();
		ch->PointsPacket();
		ch->UpdatePacket();
		SendInfo(ch);
		SendMap(ch);
	}

	// the state line of "/champion" (prefix "champion" for the GM's own, "champion <nick>" for another's)
	static void GmState(LPCHARACTER ch, const char* szPrefix, char* buf, size_t size)
	{
		const SungmaRequirement* pReq = MapRequirement(ch->GetMapIndex());
		snprintf(buf, size, "%s: lv %d step %d exp %u/%u points %d | sungma real %d %d %d %d, now %d %d %d %d | "
				"map %ld %s (%d %d %d %d hit %d) | precyzja %d, per %d %d %d %d | unlock state %d | rate %d%%", szPrefix,
				(int)ch->GetConquerorLevel(), (int)ch->GetConquerorLevelStep(), ch->GetConquerorExp(), ch->GetConquerorNextExp(),
				ch->GetConquerorPoint(), ch->GetRealPoint(POINT_SUNGMA_STR), ch->GetRealPoint(POINT_SUNGMA_HP),
				ch->GetRealPoint(POINT_SUNGMA_MOVE), ch->GetRealPoint(POINT_SUNGMA_IMMUNE), ch->GetPoint(POINT_SUNGMA_STR),
				ch->GetPoint(POINT_SUNGMA_HP), ch->GetPoint(POINT_SUNGMA_MOVE), ch->GetPoint(POINT_SUNGMA_IMMUNE),
				ch->GetMapIndex(), pReq ? "sungma" : "-", pReq ? pReq->str : 0, pReq ? pReq->hp : 0, pReq ? pReq->move : 0,
				pReq ? pReq->immune : 0, pReq ? pReq->hit : 0, ch->GetPoint(POINT_HIT_PCT), ch->GetPoint(POINT_SUNGMA_PER_STR),
				ch->GetPoint(POINT_SUNGMA_PER_HP), ch->GetPoint(POINT_SUNGMA_PER_MOVE), ch->GetPoint(POINT_SUNGMA_PER_IMMUNE),
				UnlockState(ch), ExpRatePct());
	}

	// a line for the GM by name: here, or relayed to the core that holds the GM (a chat packet, as a whisper goes)
	static void GmTell(const char* szGM, const char* szText)
	{
		LPCHARACTER gm = CHARACTER_MANAGER::instance().FindPC(szGM);
		if (gm)
		{
			gm->ChatPacket(CHAT_TYPE_INFO, "%s", szText);
			return;
		}
		CCI* pkCCI = P2P_MANAGER::instance().Find(szGM);
		if (!pkCCI || !pkCCI->pkDesc)
			return;
		size_t len = strlen(szText);
		if (len > CHAT_MAX_LEN)
			len = CHAT_MAX_LEN;
		TPacketGCChat pack;
		pack.header = HEADER_GC_CHAT;
		pack.size = (WORD)(sizeof(pack) + len);
		pack.type = CHAT_TYPE_INFO;
		pack.id = 0;
		pack.bEmpire = pkCCI->bEmpire;
		TEMP_BUFFER buf;
		buf.write(&pack, sizeof(pack));
		buf.write(szText, len);
		pkCCI->pkDesc->SetRelay(szGM);
		pkCCI->pkDesc->Packet(buf.read_peek(), buf.size());
		pkCCI->pkDesc->SetRelay("");
	}

	// the target is on this core: the change, its window, the GM's state line (szGM: the GM's name, maybe elsewhere)
	static void GmRunOn(LPCHARACTER tch, const char* sub, int n, int v, const char* szGM)
	{
		const bool bKnown = !*sub || GmApply(tch, sub, n, v);
		if (*sub && bKnown)
			GmRefresh(tch);
		char szPrefix[CHARACTER_NAME_MAX_LEN + 16];
		snprintf(szPrefix, sizeof(szPrefix), "champion %s", tch->GetName());
		char szLine[CHAT_MAX_LEN + 1];
		if (!bKnown)
			snprintf(szLine, sizeof(szLine), "champion %s: nieznana komenda lub zle argumenty (%s) - nic nie zmieniono", tch->GetName(), sub);
		else
			GmState(tch, szPrefix, szLine, sizeof(szLine));
		GmTell(szGM, szLine);
		if (*sub && bKnown)
			sys_log(0, "CHAMPION_GM: %s -> %s: %s %d %d", szGM, tch->GetName(), sub, n, v);
	}

	// the target is offline: the change waits in its quest flags (champion_gm.<what>) for its next login
	static void GmOffline(LPCHARACTER gm, const char* szName, const char* sub, int n, int v)
	{
		char szEsc[CHARACTER_NAME_MAX_LEN * 2 + 1];
		DBManager::instance().EscapeString(szEsc, sizeof(szEsc), szName, strnlen(szName, CHARACTER_NAME_MAX_LEN));
		std::unique_ptr<SQLMsg> pMsg(DBManager::instance().DirectQuery("SELECT id, name, conqueror_level, conqueror_exp, conqueror_point, "
				"sungma_str, sungma_hp, sungma_move, sungma_immune FROM player%s WHERE name = '%s'", get_table_postfix(), szEsc));
		SQLResult* pRes = pMsg ? pMsg->Get() : NULL;
		MYSQL_ROW row = (pRes && pRes->uiNumRows > 0) ? mysql_fetch_row(pRes->pSQLResult) : NULL;
		if (!row || !row[0])
		{
			gm->ChatPacket(CHAT_TYPE_INFO, "champion: nie ma postaci %s", szName);
			return;
		}
		DWORD dwPID = 0;
		str_to_number(dwPID, row[0]);
		const char* szReal = row[1] ? row[1] : szName;
		if (!*sub)
		{
			gm->ChatPacket(CHAT_TYPE_INFO, "champion %s (offline, baza): lv %s exp %s points %s | sungma real %s %s %s %s", szReal,
					row[2] ? row[2] : "?", row[3] ? row[3] : "?", row[4] ? row[4] : "?", row[5] ? row[5] : "?",
					row[6] ? row[6] : "?", row[7] ? row[7] : "?", row[8] ? row[8] : "?");
			return;
		}

		// the flag and its value (+1: a flag of 0 is no flag)
		char szState[16];
		long lValue = 0;
		if (!strcmp(sub, "unlock") || !strcmp(sub, "reset"))
		{
			strlcpy(szState, sub, sizeof(szState));
			lValue = 1;
		}
		else if (!strcmp(sub, "level"))
		{
			strlcpy(szState, "level", sizeof(szState));
			lValue = MINMAX(0, n, (int)MAX_LEVEL) + 1;
		}
		else if (!strcmp(sub, "exp") && n >= 0)
		{
			strlcpy(szState, "exp", sizeof(szState));
			lValue = (long)MIN(n, 2000000000) + 1;
		}
		else if (!strcmp(sub, "points"))
		{
			strlcpy(szState, "points", sizeof(szState));
			lValue = (long)MINMAX(0, n, 30000) + 1;
		}
		else if (!strcmp(sub, "stat") && n >= 0 && n <= 3)
		{
			snprintf(szState, sizeof(szState), "stat%d", n);
			lValue = MINMAX(0, v, 255) + 1;
		}
		else if (!strcmp(sub, "give") && n > 0)
		{
			// the experience waiting adds up
			strlcpy(szState, "give", sizeof(szState));
			long lHave = 0;
			std::unique_ptr<SQLMsg> pOld(DBManager::instance().DirectQuery("SELECT lValue FROM quest%s WHERE dwPID = %u AND "
					"szName = '%s' AND szState = 'give'", get_table_postfix(), dwPID, GM_FLAG));
			SQLResult* pOldRes = pOld ? pOld->Get() : NULL;
			MYSQL_ROW oldRow = (pOldRes && pOldRes->uiNumRows > 0) ? mysql_fetch_row(pOldRes->pSQLResult) : NULL;
			if (oldRow && oldRow[0])
				str_to_number(lHave, oldRow[0]);
			lValue = MIN((long)2000000000, MAX(0L, lHave) + (long)n);
		}
		else
		{
			gm->ChatPacket(CHAT_TYPE_INFO, "champion %s: nieznana komenda lub zle argumenty (%s) - nic nie zmieniono", szReal, sub);
			return;
		}

		// a reset first takes back whatever else was waiting (it would undo it at the login anyway)
		if (!strcmp(sub, "reset"))
			DBManager::instance().DirectQuery("DELETE FROM quest%s WHERE dwPID = %u AND szName = '%s'", get_table_postfix(), dwPID, GM_FLAG);
		DBManager::instance().DirectQuery("REPLACE INTO quest%s (dwPID, szName, szState, lValue) VALUES (%u, '%s', '%s', %ld)",
				get_table_postfix(), dwPID, GM_FLAG, szState, lValue);
		gm->ChatPacket(CHAT_TYPE_INFO, "champion %s: postac offline - zmiana (%s) zapisana, wejdzie przy jej nastepnym wejsciu do gry",
				szReal, sub);
		sys_log(0, "CHAMPION_GM: %s -> %s (offline, pid %u): %s.%s = %ld", gm->GetName(), szReal, dwPID, GM_FLAG, szState, lValue);
	}

	// ChampionOnLogin: the changes a GM left while the character was away (GmOffline), in a fixed order
	static void GmPendingApply(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC())
			return;
		static const char* const aState[] = { "reset", "unlock", "level", "stat0", "stat1", "stat2", "stat3", "exp", "points", "give" };
		bool bAny = false;
		for (size_t i = 0; i < sizeof(aState) / sizeof(aState[0]); ++i)
		{
			const std::string strFlag = std::string(GM_FLAG) + "." + aState[i];
			const int iValue = ch->GetQuestFlag(strFlag);
			if (iValue <= 0)
				continue;
			ch->SetQuestFlag(strFlag, 0);
			bAny = true;
			if (!strncmp(aState[i], "stat", 4))
				GmApply(ch, "stat", aState[i][4] - '0', iValue - 1);
			else if (!strcmp(aState[i], "give"))
				GmApply(ch, "give", iValue, 0);
			else
				GmApply(ch, aState[i], iValue - 1, 0);
			sys_log(0, "CHAMPION_GM: %s at login: %s (%d)", ch->GetName(), aState[i], iValue);
		}
		if (bAny)
			GmRefresh(ch);
	}
}

// GM: "/champion [<nick>]" (state), "/champion [<nick>] level <n>" (with the points earned up to it),
// "/champion [<nick>] exp|points <n>", "/champion [<nick>] stat <0-3> <n>", "/champion [<nick>] unlock" (no
// conditions), "/champion [<nick>] reset", "/champion [<nick>] give <exp>", "/champion reload" (the two data files).
// Without <nick> - the GM's own character (MT2009_PLUS_CHAMPION_TARGET_V1 above).
ACMD(do_champion)
{
	if (!ch)
		return;
	char arg1[256], arg2[256], arg3[256], arg4[256];
	const char* rest = two_arguments(argument, arg1, sizeof(arg1), arg2, sizeof(arg2));
	two_arguments(rest, arg3, sizeof(arg3), arg4, sizeof(arg4));

	// "/champion <nick> <sub> <n> <v>": the name first, the rest moves one place on
	const bool bTarget = *arg1 && !champion::GmIsSub(arg1);
	char szName[256] = "";
	const char* sub = arg1;
	const char* szN = arg2;
	const char* szV = arg3;
	if (bTarget)
	{
		strlcpy(szName, arg1, sizeof(szName));
		sub = arg2;
		szN = arg3;
		szV = arg4;
	}
	int n = 0, v = 0;
	str_to_number(n, szN);
	str_to_number(v, szV);

	if (!strcmp(sub, "reload"))
	{
		champion::Reload();
		ch->ChatPacket(CHAT_TYPE_INFO, "champion: data reloaded");
		return;
	}

	if (bTarget && strcasecmp(szName, ch->GetName()))
	{
		if (strlen(szName) > CHARACTER_NAME_MAX_LEN)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "champion: nie ma postaci %s", szName);
			return;
		}
		LPCHARACTER tch = CHARACTER_MANAGER::instance().FindPC(szName);
		if (tch && tch->IsPC())
		{
			champion::GmRunOn(tch, sub, n, v, ch->GetName());
			return;
		}
		CCI* pkCCI = P2P_MANAGER::instance().Find(szName);
		if (pkCCI && pkCCI->pkDesc)
		{
			TPacketGGChampionCmd p;
			memset(&p, 0, sizeof(p));
			p.bHeader = HEADER_GG_CHAMPION_CMD;
			strlcpy(p.szTarget, pkCCI->szName, sizeof(p.szTarget));
			strlcpy(p.szGM, ch->GetName(), sizeof(p.szGM));
			snprintf(p.szArgs, sizeof(p.szArgs), "%s %s %s", sub, szN, szV);
			pkCCI->pkDesc->SetRelay("");
			pkCCI->pkDesc->Packet(&p, sizeof(p));
			ch->ChatPacket(CHAT_TYPE_INFO, "champion %s: postac na innym rdzeniu (kanal %d) - komenda wyslana", pkCCI->szName,
					(int)pkCCI->bChannel);
			return;
		}
		champion::GmOffline(ch, szName, sub, n, v);
		return;
	}

	// the GM's own character, as before
	if (*sub && !champion::GmApply(ch, sub, n, v))
		ch->ChatPacket(CHAT_TYPE_INFO, "champion: nieznana komenda lub zle argumenty (%s) - nic nie zmieniono", sub);
	champion::GmRefresh(ch);
	char szLine[CHAT_MAX_LEN + 1];
	champion::GmState(ch, "champion", szLine, sizeof(szLine));
	ch->ChatPacket(CHAT_TYPE_INFO, "%s", szLine);
}

// input_p2p.cpp, HEADER_GG_CHAMPION_CMD (MT2009_PLUS_CHAMPION_TARGET_V1): a GM's "/champion <nick> ..." from another
// core for a character of this one; the state line goes back to the GM.
void ChampionP2P(const char* c_pData)
{
	const TPacketGGChampionCmd* p = reinterpret_cast<const TPacketGGChampionCmd*>(c_pData);
	char szTarget[CHARACTER_NAME_MAX_LEN + 1], szGM[CHARACTER_NAME_MAX_LEN + 1], szArgs[sizeof(p->szArgs) + 1];
	strlcpy(szTarget, p->szTarget, sizeof(szTarget));
	strlcpy(szGM, p->szGM, sizeof(szGM));
	memcpy(szArgs, p->szArgs, sizeof(p->szArgs));
	szArgs[sizeof(p->szArgs)] = '\0';
	LPCHARACTER tch = CHARACTER_MANAGER::instance().FindPC(szTarget);
	if (!tch || !tch->IsPC())
	{
		char szLine[CHAT_MAX_LEN + 1];
		snprintf(szLine, sizeof(szLine), "champion %s: postac zmienila rdzen lub wyszla - powtorz komende", szTarget);
		champion::GmTell(szGM, szLine);
		return;
	}
	char sub[256], arg2[256], arg3[256];
	const char* rest = two_arguments(szArgs, sub, sizeof(sub), arg2, sizeof(arg2));
	one_argument(rest, arg3, sizeof(arg3));
	int n = 0, v = 0;
	str_to_number(n, arg2);
	str_to_number(v, arg3);
	champion::GmRunOn(tch, sub, n, v, szGM);
}

// ---- quest functions (Owsap's names, quest/functions/pc.func and questlua_npc.cpp) -------------------------

namespace quest
{
	static LPCHARACTER ChampionPC()
	{
		return CQuestManager::instance().GetCurrentCharacterPtr();
	}

	static int pc_get_conqueror_level(lua_State* L)
	{
		LPCHARACTER ch = ChampionPC();
		lua_pushnumber(L, ch ? ch->GetConquerorLevel() : 0);
		return 1;
	}

	static int pc_get_conqueror_exp(lua_State* L)
	{
		LPCHARACTER ch = ChampionPC();
		lua_pushnumber(L, ch ? (double)ch->GetConquerorExp() : 0);
		return 1;
	}

	static int pc_get_conqueror_next_exp(lua_State* L)
	{
		LPCHARACTER ch = ChampionPC();
		lua_pushnumber(L, ch ? (double)ch->GetConquerorNextExp() : 0);
		return 1;
	}

	static int pc_get_conqueror_point(lua_State* L)
	{
		LPCHARACTER ch = ChampionPC();
		lua_pushnumber(L, ch ? ch->GetConquerorPoint() : 0);
		return 1;
	}

	// pc.get_conqueror_unlock_state(): champion::UnlockState (0 = may become a Champion).
	static int pc_get_conqueror_unlock_state(lua_State* L)
	{
		lua_pushnumber(L, champion::UnlockState(ChampionPC()));
		return 1;
	}

	// pc.set_conqueror(): becomes a Champion when every condition holds (true), else false.
	static int pc_set_conqueror(lua_State* L)
	{
		lua_pushboolean(L, champion::Unlock(ChampionPC()));
		return 1;
	}

	static int pc_give_conqueror_exp(lua_State* L)
	{
		LPCHARACTER ch = ChampionPC();
		if (ch && lua_isnumber(L, 1) && lua_tonumber(L, 1) > 0)
			champion::GainExp(ch, (unsigned int)lua_tonumber(L, 1));
		return 0;
	}

	static int ChampionPushStat(lua_State* L, BYTE bPoint)
	{
		LPCHARACTER ch = ChampionPC();
		lua_pushnumber(L, ch ? ch->GetRealPoint(bPoint) : 0);
		return 1;
	}

	static int pc_get_sungma_str(lua_State* L) { return ChampionPushStat(L, POINT_SUNGMA_STR); }
	static int pc_get_sungma_vit(lua_State* L) { return ChampionPushStat(L, POINT_SUNGMA_HP); }
	static int pc_get_sungma_res(lua_State* L) { return ChampionPushStat(L, POINT_SUNGMA_MOVE); }
	static int pc_get_sungma_int(lua_State* L) { return ChampionPushStat(L, POINT_SUNGMA_IMMUNE); }

	// pc.reset_sungma_status(idx): 0 str, 1 vit (hp), 2 res (move), 3 int (immune) - Nowa Wola 72068-72071.
	static int pc_reset_sungma_status(lua_State* L)
	{
		const int idx = lua_isnumber(L, 1) ? (int)lua_tonumber(L, 1) : -1;
		lua_pushboolean(L, champion::ResetStat(ChampionPC(), idx));
		return 1;
	}

	static int npc_get_sungma_exp(lua_State* L)
	{
		LPCHARACTER npc = CQuestManager::instance().GetCurrentNPCCharacterPtr();
		lua_pushnumber(L, npc ? champion::MobExp(npc->GetRaceNum()) : 0);
		return 1;
	}

	// MT2009_PLUS_YOHARA_DUNG4_V1 (sungma): d.set_sungma(str, hp, move, immune) - the current dungeon instance's Sung Ma
	// requirement in place of its map's (Wieza Sung Mahi: every floor's), told to everyone inside at once (the
	// character window's "sungma_map" and the penalty notice); d.clear_sungma() - the map's own again.
	struct FChampionSendMap
	{
		void operator()(LPENTITY ent)
		{
			if (ent && ent->IsType(ENTITY_CHARACTER))
			{
				LPCHARACTER ch = (LPCHARACTER) ent;
				if (ch->IsPC())
					champion::SendMap(ch);
			}
		}
	};

	static void ChampionTellDungeon(long lMapIndex)
	{
		LPSECTREE_MAP pMap = SECTREE_MANAGER::instance().GetMap(lMapIndex);
		if (pMap)
		{
			FChampionSendMap f;
			pMap->for_each(f);
		}
	}

	static int d_set_sungma(lua_State* L)
	{
		LPDUNGEON pDungeon = CQuestManager::instance().GetCurrentDungeon();
		if (!pDungeon || !lua_isnumber(L, 1) || !lua_isnumber(L, 2) || !lua_isnumber(L, 3) || !lua_isnumber(L, 4))
			return 0;
		champion::SungmaRequirement r;
		r.str = MINMAX(0, (int) lua_tonumber(L, 1), champion::STAT_MAX);
		r.hp = MINMAX(0, (int) lua_tonumber(L, 2), champion::STAT_MAX);
		r.move = MINMAX(0, (int) lua_tonumber(L, 3), champion::STAT_MAX);
		r.immune = MINMAX(0, (int) lua_tonumber(L, 4), champion::STAT_MAX);
		// MT2009_PLUS_PRECISION_V1: d.set_sungma(str, hp, move, immune[, hit_pct])
		r.hit = lua_isnumber(L, 5) ? MINMAX(0, (int) lua_tonumber(L, 5), 100) : 0;
		champion::SetInstanceRequirement(pDungeon->GetMapIndex(), &r);
		ChampionTellDungeon(pDungeon->GetMapIndex());
		return 0;
	}

	static int d_clear_sungma(lua_State* L)
	{
		LPDUNGEON pDungeon = CQuestManager::instance().GetCurrentDungeon();
		if (!pDungeon)
			return 0;
		champion::SetInstanceRequirement(pDungeon->GetMapIndex(), NULL);
		ChampionTellDungeon(pDungeon->GetMapIndex());
		return 0;
	}

	static void ChampionAddToTable(lua_State* L, const char* table, const luaL_reg* reg)
	{
		lua_getglobal(L, table);
		if (!lua_istable(L, -1))
		{
			lua_pop(L, 1);
			sys_err("CHAMPION: the quest table %s does not exist", table);
			return;
		}
		for (; reg->name; ++reg)
		{
			lua_pushstring(L, reg->name);
			lua_pushcfunction(L, reg->func);
			lua_rawset(L, -3);
		}
		lua_pop(L, 1);
	}
}

// questlua.cpp CQuestManager::InitializeLua, after the pc and npc tables are made.
void RegisterChampionFunctions()
{
	using namespace quest;
	static const luaL_reg pc_add[] =
	{
		{ "get_conqueror_level",		pc_get_conqueror_level },
		{ "get_conqueror_exp",			pc_get_conqueror_exp },
		{ "get_conqueror_next_exp",		pc_get_conqueror_next_exp },
		{ "get_conqueror_point",		pc_get_conqueror_point },
		{ "get_conqueror_unlock_state",	pc_get_conqueror_unlock_state },
		{ "set_conqueror",				pc_set_conqueror },
		{ "give_conqueror_exp",			pc_give_conqueror_exp },
		{ "give_conqueror_exp2",		pc_give_conqueror_exp },
		{ "get_sungma_str",				pc_get_sungma_str },
		{ "get_sungma_vit",				pc_get_sungma_vit },
		{ "get_sungma_res",				pc_get_sungma_res },
		{ "get_sungma_int",				pc_get_sungma_int },
		{ "reset_sungma_status",		pc_reset_sungma_status },
		{ NULL, NULL }
	};
	static const luaL_reg npc_add[] =
	{
		{ "get_sungma_exp",				npc_get_sungma_exp },
		{ NULL, NULL }
	};
	// MT2009_PLUS_YOHARA_DUNG4_V1 (sungma): the "d" table is made before (RegisterDungeonFunctionTable)
	static const luaL_reg d_add[] =
	{
		{ "set_sungma",					d_set_sungma },
		{ "clear_sungma",				d_clear_sungma },
		{ NULL, NULL }
	};
	lua_State* L = CQuestManager::instance().GetLuaState();
	ChampionAddToTable(L, "pc", pc_add);
	ChampionAddToTable(L, "npc", npc_add);
	ChampionAddToTable(L, "d", d_add);
}

#endif // ENABLE_CONQUEROR_LEVEL

#ifndef ENABLE_CONQUEROR_LEVEL
// input_p2p.cpp calls it (MT2009_PLUS_CHAMPION_TARGET_V1); without the champion level there is nothing to do
void ChampionP2P(const char*)
{
}
#endif

// MT2009_PLUS_RIPOSTY_V1: Riposty i Dopalacze's pc.* functions (playerbot_riposty.cpp) ride on the hook below.
void RegisterRipostyFunctions();

// questlua.cpp declares and calls it inside namespace quest (a block-scope declaration there names
// quest::RegisterChampionFunctions), so that is the name the linker looks for.
namespace quest
{
	void RegisterChampionFunctions()
	{
		::RegisterChampionFunctions();
		::RegisterRipostyFunctions();	// MT2009_PLUS_RIPOSTY_V1
	}
}
