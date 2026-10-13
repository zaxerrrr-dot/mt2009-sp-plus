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
#include "sectree_manager.h"
#include "questmanager.h"
#include "questlua.h"
#include "locale_service.h"
#include "priv_manager.h"
#include "log.h"
#include "utils.h"
#include "cmd.h"
#include "affect.h"

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

	// ---- data files -------------------------------------------------------------------------------------

	struct TState
	{
		bool loaded = false;
		std::map<std::string, SungmaRequirement> byName;	// lower-case map name -> requirement
		std::map<long, const SungmaRequirement*> byIndex;	// base map index -> requirement (or NULL)
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
			// sungma_table.txt: <map name> <str> <hp> <move> <immune>
			std::ifstream in((base + "/sungma_table.txt").c_str());
			std::istringstream line;
			while (in && NextDataLine(in, line))
			{
				std::string name;
				SungmaRequirement r = { 0, 0, 0, 0 };
				if (!(line >> name >> r.str >> r.hp >> r.move >> r.immune))
					continue;
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
		sys_log(0, "CHAMPION: %u Sung Ma map(s) named, %u monster(s) with champion experience",
				(unsigned)st.byName.size(), (unsigned)st.mobExp.size());
	}

	void Reload()
	{
		Load();
	}

	const SungmaRequirement* MapRequirement(long lMapIndex)
	{
		TState& st = State();
		if (!st.loaded)
			Load();
		if (st.byName.empty() || lMapIndex <= 0)
			return NULL;
		const long lBase = lMapIndex >= 10000 ? lMapIndex / 10000 : lMapIndex;
		std::map<long, const SungmaRequirement*>::const_iterator it = st.byIndex.find(lBase);
		if (it != st.byIndex.end())
			return it->second;
		const SungmaRequirement* pReq = NULL;
		const TMapRegion* pRegion = SECTREE_MANAGER::instance().GetMapRegion(lBase);
		if (pRegion)
		{
			std::map<std::string, SungmaRequirement>::const_iterator n = st.byName.find(Lower(pRegion->strMapName));
			if (n != st.byName.end())
				pReq = &n->second;
			// The cache only remembers maps this core hosts: another core's map is asked again.
			st.byIndex[lBase] = pReq;
		}
		return pReq;
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

namespace champion
{
	static const BYTE s_aStatPoint[4] = { POINT_SUNGMA_STR, POINT_SUNGMA_HP, POINT_SUNGMA_MOVE, POINT_SUNGMA_IMMUNE };
	static const char* const s_aStatName[4] = { "Sila", "Witalnosc", "Odpornosc", "Inteligencja" };

	static bool IsBotCharacter(LPCHARACTER ch)
	{
		return ch && ch->GetDesc() && ch->GetDesc()->IsBot();
	}

	void SendInfo(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC() || !ch->GetDesc() || IsBotCharacter(ch))
			return;
		ch->ChatPacket(CHAT_TYPE_COMMAND, "champion_info %d %u %u %d %d %d %d %d %d",
				(int)ch->GetConquerorLevel(), ch->GetConquerorExp(), ch->GetConquerorNextExp(), ch->GetConquerorPoint(),
				ch->GetPoint(POINT_SUNGMA_STR), ch->GetPoint(POINT_SUNGMA_HP), ch->GetPoint(POINT_SUNGMA_MOVE),
				ch->GetPoint(POINT_SUNGMA_IMMUNE), (int)ch->GetConquerorLevelStep());
	}

	void SendMap(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC() || !ch->GetDesc() || IsBotCharacter(ch))
			return;
		const SungmaRequirement* pReq = MapRequirement(ch->GetMapIndex());
		if (!pReq)
		{
			ch->ChatPacket(CHAT_TYPE_COMMAND, "sungma_map 0 0 0 0");
			return;
		}
		ch->ChatPacket(CHAT_TYPE_COMMAND, "sungma_map %d %d %d %d", pReq->str, pReq->hp, pReq->move, pReq->immune);
		if (ch->GetConquerorLevel() < 1)
			ch->ChatPacket(CHAT_TYPE_INFO, "To ziemia Sung Ma: bez Poziomu Czempiona nie zranisz tutejszych potworow.");
		else if (ch->GetPoint(POINT_SUNGMA_STR) < pReq->str || ch->GetPoint(POINT_SUNGMA_HP) < pReq->hp ||
				ch->GetPoint(POINT_SUNGMA_MOVE) < pReq->move || ch->GetPoint(POINT_SUNGMA_IMMUNE) < pReq->immune)
			ch->ChatPacket(CHAT_TYPE_INFO, "Ziemia Sung Ma wymaga: Sila %d, Witalnosc %d, Odpornosc %d, Inteligencja %d - "
					"przy brakach Twoja sila slabnie o polowe.", pReq->str, pReq->hp, pReq->move, pReq->immune);
	}

	int UnlockState(LPCHARACTER ch)
	{
		if (!ch || !ch->IsPC())
			return 5;
		if (IsBotCharacter(ch))
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

		if (bLevelUp)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Poziom Czempiona: %d.", iLevel);
			char hint[64];
			snprintf(hint, sizeof(hint), "level %d points %d", iLevel, iPoints);
			LogManager::instance().CharLog(ch, iLevel, "CHAMPION_LEVELUP", hint);
			ch->Save();
		}
		else if (iPoints > iOldPoints)
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
		if (!to || !dwBase || !to->IsPC() || to->GetConquerorLevel() < 1 || IsBotCharacter(to))
			return;
		if (to->FindAffect(AFFECT_EXP_BLOCK))
			return;
		const int iBonus = MAX(0, 100 + CPrivManager::instance().GetPriv(to, PRIV_EXP_PCT) + to->GetPoint(POINT_EXP) +
				to->GetPoint(POINT_MALL_EXPBONUS));
		unsigned long long exp = (unsigned long long)dwBase * iBonus / 100 * ExpRatePct() / 100;
		const unsigned int dwCap = MAX(1u, to->GetConquerorNextExp() / 10);
		if (exp > dwCap)
			exp = dwCap;
		if (!exp)
			exp = 1;
		GainExp(to, (unsigned int)exp);
		if (pkVictim)
			pkVictim->CreateFly(FLY_EXP, to);
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

// ---- engine hooks (server-patches/czempion/edits.json) ----------------------------------------------------

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
	if (pReq && ch->GetPoint(POINT_SUNGMA_HP) < pReq->hp)
		return iMaxHP / 2;
	return iMaxHP;
}

// char.cpp GetLimitPoint(POINT_MOV_SPEED): Sung Ma movement below the requirement halves the speed.
int ChampionMoveSpeed(const CHARACTER* ch, int iSpeed)
{
	if (!ch || !ch->IsPC())
		return iSpeed;
	const champion::SungmaRequirement* pReq = champion::MapRequirement(ch->GetMapIndex());
	if (pReq && ch->GetPoint(POINT_SUNGMA_MOVE) < pReq->move)
		return iSpeed / 2;
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
	if (pAttacker->GetPoint(POINT_SUNGMA_STR) < pReq->str)
		return iDam / 2;
	return iDam;
}

// char_resist.cpp AttackedByPoison / AttackedByFire / AttackedByBleeding: a person's poison, fire and bleeding
// on a monster of a Sung Ma map take hold half as often while Sung Ma intelligence is below the requirement
// (Ameria halves the attacker's chance; here one check for blows and skills alike).
bool ChampionImmuneBlocks(LPCHARACTER pkAttacker, LPCHARACTER pkVictim)
{
	if (!pkAttacker || !pkVictim || !pkAttacker->IsPC() || pkVictim->IsPC())
		return false;
	const champion::SungmaRequirement* pReq = champion::MapRequirement(pkAttacker->GetMapIndex());
	if (!pReq || pkAttacker->GetPoint(POINT_SUNGMA_IMMUNE) >= pReq->immune)
		return false;
	return number(1, 2) == 1;
}

// input_login.cpp Entergame: the Sung Ma penalties counted on this map, the client told the numbers.
void ChampionOnLogin(LPCHARACTER ch)
{
	if (!ch || !ch->IsPC() || champion::IsBotCharacter(ch))
		return;
	if (champion::IsSungmaMap(ch->GetMapIndex()))
	{
		ch->ComputePoints();
		ch->PointsPacket();
	}
	champion::SendInfo(ch);
	champion::SendMap(ch);
}

DWORD CHARACTER::GetConquerorNextExp() const
{
	return champion::NextExp(GetConquerorLevel());
}

// ---- commands ---------------------------------------------------------------------------------------------

// "/conqueror_stat smh_str|smh_hp|smh_move|smh_inmune" - the names GF's uicharacternew.py sends (Stage B);
// "/conqueror_stat info" - the numbers again (root uichampion.py, Stage A).
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

// GM: "/champion" (state), "/champion level|exp|points <n>", "/champion stat <0-3> <n>", "/champion unlock"
// (no conditions), "/champion reset", "/champion give <exp>", "/champion reload" (the two data files).
ACMD(do_champion)
{
	char arg1[256], arg2[256], arg3[256];
	const char* rest = two_arguments(argument, arg1, sizeof(arg1), arg2, sizeof(arg2));
	one_argument(rest, arg3, sizeof(arg3));
	if (!ch)
		return;

	int n = 0;
	str_to_number(n, arg2);
	if (!strcmp(arg1, "reload"))
	{
		champion::Reload();
		ch->ChatPacket(CHAT_TYPE_INFO, "champion: data reloaded");
	}
	else if (!strcmp(arg1, "unlock"))
	{
		if (ch->GetConquerorLevel() < 1)
		{
			ch->SetConquerorLevel(1);
			ch->SetConquerorLevelStep(0);
			ch->SetConquerorExp(0);
		}
	}
	else if (!strcmp(arg1, "level"))
	{
		ch->SetConquerorLevel((BYTE)MINMAX(0, n, (int)champion::MAX_LEVEL));
		ch->SetConquerorLevelStep(0);
		ch->SetConquerorExp(0);
	}
	else if (!strcmp(arg1, "exp") && n >= 0)
		ch->SetConquerorExp((DWORD)n);
	else if (!strcmp(arg1, "give") && n > 0)
		champion::GainExp(ch, (unsigned int)n);
	else if (!strcmp(arg1, "points"))
		ch->SetConquerorPoint(MAX(0, n));
	else if (!strcmp(arg1, "stat") && n >= 0 && n <= 3)
	{
		int v = 0;
		str_to_number(v, arg3);
		const BYTE aPoint[4] = { POINT_SUNGMA_STR, POINT_SUNGMA_HP, POINT_SUNGMA_MOVE, POINT_SUNGMA_IMMUNE };
		ch->SetRealPoint(aPoint[n], MINMAX(0, v, 255));
	}
	else if (!strcmp(arg1, "reset"))
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
	ch->ComputePoints();
	ch->PointsPacket();
	ch->UpdatePacket();
	const champion::SungmaRequirement* pReq = champion::MapRequirement(ch->GetMapIndex());
	ch->ChatPacket(CHAT_TYPE_INFO, "champion: lv %d step %d exp %u/%u points %d | sungma real %d %d %d %d, now %d %d %d %d | "
			"map %ld %s (%d %d %d %d) | unlock state %d | rate %d%%",
			(int)ch->GetConquerorLevel(), (int)ch->GetConquerorLevelStep(), ch->GetConquerorExp(), ch->GetConquerorNextExp(),
			ch->GetConquerorPoint(), ch->GetRealPoint(POINT_SUNGMA_STR), ch->GetRealPoint(POINT_SUNGMA_HP),
			ch->GetRealPoint(POINT_SUNGMA_MOVE), ch->GetRealPoint(POINT_SUNGMA_IMMUNE), ch->GetPoint(POINT_SUNGMA_STR),
			ch->GetPoint(POINT_SUNGMA_HP), ch->GetPoint(POINT_SUNGMA_MOVE), ch->GetPoint(POINT_SUNGMA_IMMUNE),
			ch->GetMapIndex(), pReq ? "sungma" : "-", pReq ? pReq->str : 0, pReq ? pReq->hp : 0, pReq ? pReq->move : 0,
			pReq ? pReq->immune : 0, champion::UnlockState(ch), champion::ExpRatePct());
	champion::SendInfo(ch);
	champion::SendMap(ch);
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
	lua_State* L = CQuestManager::instance().GetLuaState();
	ChampionAddToTable(L, "pc", pc_add);
	ChampionAddToTable(L, "npc", npc_add);
}

#endif // ENABLE_CONQUEROR_LEVEL
