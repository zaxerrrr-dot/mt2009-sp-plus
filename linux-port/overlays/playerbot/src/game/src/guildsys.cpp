// MT2009_PLUS_GUILDSYS_V1 - the guild system update (guildsys.h, server-patches/guildsys/README.md). On the Guild
// Systems package compiled by Nazox (GUILD_NEW_LEVEL_40, GUILD_SKILLBOOK, the join date of GUILD_DONATE_ATTENDANCE),
// written anew for our engine: no new packet, no new item type, nothing the old client cannot live with.
//
// Changes against the package:
//  - GUILD_SKILLBOOK: the package's book LOWERS a random guild skill (a new item type 37 - ours is the pet's) and
//    gives the point back. Here the books RAISE Balathor's three guild skills (158-160, which skill points cannot
//    raise) and the forget book gives back every point of the skills 151-157 at once (no random skill, no choice
//    window); all four are ITEM_USE / USE_SPECIAL items of guildsys.sql, the leader's only.
//  - GUILD_NEW_LEVEL_40: our own experience table for 21-40 (the package's skipped its level 20 and put
//    16 800 000 at index 40), the ladder table of the db core to 40 as well, the member limit as before level 20.
//  - the join date: an INVISIBLE column of guild_member (the db core's positional INSERT stays valid) read by the
//    quest functions, not a new field of every member packet.
#include "stdafx.h"
#include <algorithm>
#include <map>
#include <vector>
#include "constants.h"
#include "config.h"
#include "utils.h"
#include "char.h"
#include "item.h"
#include "affect.h"
#include "skill.h"
#include "guild.h"
#include "guild_manager.h"
#include "db.h"
#include "log.h"
#include "questlua.h"
#include "questmanager.h"
#include "guildsys.h"

// CGuild names this struct its friend (guild.h, MT2009_PLUS_GUILDSYS_V1 (friend)): the skill array, the points and the
// online members are private and the engine has no setter that skips the skill point.
struct GuildSysAccess
{
	static BYTE GetSkill(CGuild* g, unsigned int idx) { return g->m_data.abySkill[idx]; }
	static void SetSkill(CGuild* g, unsigned int idx, BYTE v) { g->m_data.abySkill[idx] = v; }
	static BYTE GetPoints(CGuild* g) { return g->m_data.skill_point; }
	static void SetPoints(CGuild* g, BYTE v) { g->m_data.skill_point = v; }

	static std::vector<LPCHARACTER> Online(CGuild* g)
	{
		return std::vector<LPCHARACTER>(g->m_memberOnline.begin(), g->m_memberOnline.end());
	}

	// what CGuild::SkillLevelUp does after a change: this core's row and members, the db core (which tells the
	// other cores - HEADER_DG_GUILD_SKILL_UPDATE -> CGuild::UpdateSkill)
	static void Publish(CGuild* g)
	{
		g->ComputeGuildPoints();
		g->SaveSkill();
		g->SendDBSkillUpdate();
		std::vector<LPCHARACTER> v = Online(g);
		for (size_t i = 0; i < v.size(); ++i)
			if (v[i] && v[i]->GetDesc())	// a bot has no connection
				g->SendSkillInfoPacket(v[i]);
	}
};

namespace
{
	unsigned int SkillIndex(unsigned int dwVnum)
	{
		return dwVnum - GUILD_SKILL_START;
	}

	// the share of a level a Balathor skill's affect gives: 10 % a level (100 % at 10)
	long ImmuneChance(int iLevel)
	{
		return MINMAX(0, iLevel * 10, 100);
	}

	const char* SkillName(unsigned int dwVnum)
	{
		switch (dwVnum)
		{
			case GUILDSYS_SKILL_STORM:		return "Burza Balathora";
			case GUILDSYS_SKILL_WILL:		return "Wola Balathora";
			case GUILDSYS_SKILL_FIRMNESS:	return "Nieugi\xeato\x9c\xe6 Balathora";
		}
		return "umiej\xeatno\x9c\xe6 gildii";
	}

	bool AffectImmune(LPCHARACTER ch, unsigned int dwVnum)
	{
		CAffect* pAff = ch->FindAffect(dwVnum);
		return pAff && number(1, 100) <= pAff->lApplyValue;
	}

	// the leader's book: the guild, its leader, a word to the reader when not
	CGuild* LeaderGuild(LPCHARACTER ch)
	{
		CGuild* g = ch->GetGuild();
		if (!g)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Nie nale\xbfysz do gildii.");
			return NULL;
		}
		if (g->GetMasterPID() != ch->GetPlayerID())
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "T\xea ksi\xeag\xea mo\xbf" "e przeczyta\xe6 tylko lider gildii.");
			return NULL;
		}
		return g;
	}

	bool ReadSkillBook(LPCHARACTER ch, LPITEM item, unsigned int dwVnum)
	{
		CGuild* g = LeaderGuild(ch);
		if (!g)
			return false;

		const CSkillProto* pkSk = CSkillManager::instance().Get(dwVnum);
		const int iMax = pkSk ? MIN((int)pkSk->bMaxLevel, (int)GUILDSYS_SKILL_MAX_LEVEL) : (int)GUILDSYS_SKILL_MAX_LEVEL;
		const unsigned int idx = SkillIndex(dwVnum);
		const int iLevel = GuildSysAccess::GetSkill(g, idx);
		if (iLevel >= iMax)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "%s: ta umiej\xeatno\x9c\xe6 gildii ma ju\xbf najwy\xbfszy poziom.", SkillName(dwVnum));
			return false;
		}

		GuildSysAccess::SetSkill(g, idx, (BYTE)(iLevel + 1));
		GuildSysAccess::Publish(g);

		char szHint[64];
		snprintf(szHint, sizeof(szHint), "guild %u skill %u level %d", g->GetID(), dwVnum, iLevel + 1);
		LogManager::instance().ItemLog(ch, item, "GUILD_SKILL_BOOK", szHint);
		item->SetCount(item->GetCount() - 1);

		ch->ChatPacket(CHAT_TYPE_INFO, "Gildia nauczy\xb3" "a si\xea: %s (poziom %d/%d).", SkillName(dwVnum), iLevel + 1, iMax);
		sys_log(0, "GUILDSYS: book %s[%u] guild %s[%u] skill %u -> %d", ch->GetName(), ch->GetPlayerID(), g->GetName(),
				g->GetID(), dwVnum, iLevel + 1);
		return true;
	}

	// Ksiega Zapomnienia Gildii: every point of 151-157 back (the book-only 158-160 stay)
	bool ReadForgetBook(LPCHARACTER ch, LPITEM item)
	{
		CGuild* g = LeaderGuild(ch);
		if (!g)
			return false;

		int iRefund = 0;
		for (unsigned int v = GUILD_SKILL_START; v <= GUILD_SKILL_END; ++v)
			if (!GuildSysBookOnlySkill(v))
				iRefund += GuildSysAccess::GetSkill(g, SkillIndex(v));

		if (iRefund <= 0)
		{
			ch->ChatPacket(CHAT_TYPE_INFO, "Gildia nie ma rozdanych punkt\xf3w umiej\xeatno\x9c" "ci.");
			return false;
		}

		for (unsigned int v = GUILD_SKILL_START; v <= GUILD_SKILL_END; ++v)
			if (!GuildSysBookOnlySkill(v))
				GuildSysAccess::SetSkill(g, SkillIndex(v), 0);
		GuildSysAccess::SetPoints(g, (BYTE)MIN(255, GuildSysAccess::GetPoints(g) + iRefund));
		GuildSysAccess::Publish(g);

		char szHint[64];
		snprintf(szHint, sizeof(szHint), "guild %u points %d", g->GetID(), iRefund);
		LogManager::instance().ItemLog(ch, item, "GUILD_SKILL_FORGET", szHint);
		item->SetCount(item->GetCount() - 1);

		ch->ChatPacket(CHAT_TYPE_INFO, "Gildia odzyska\xb3" "a punkty umiej\xeatno\x9c" "ci: %d.", iRefund);
		sys_log(0, "GUILDSYS: forget book %s[%u] guild %s[%u] points %d", ch->GetName(), ch->GetPlayerID(), g->GetName(),
				g->GetID(), iRefund);
		return true;
	}

	// one number of a query (0 when the query fails - the column is not there before guildsys.sql - or no row)
	bool QueryUInt(unsigned int& out, const char* c_pszQuery)
	{
		std::unique_ptr<SQLMsg> msg(DBManager::instance().DirectQuery("%s", c_pszQuery));
		if (!msg.get() || msg->uiSQLErrno != 0 || !msg->Get() || !msg->Get()->pSQLResult)
		{
			static bool s_bWarned = false;
			if (!s_bWarned)
			{
				s_bWarned = true;
				sys_err("GUILDSYS: query failed (guildsys.sql not applied?): %s", c_pszQuery);
			}
			out = 0;
			return true;	// treated as "old"
		}
		if (msg->Get()->uiNumRows == 0)
			return false;
		MYSQL_ROW row = mysql_fetch_row(msg->Get()->pSQLResult);
		out = (row && row[0]) ? (unsigned int)strtoul(row[0], NULL, 10) : 0;
		return true;
	}
}

bool GuildSysIsBalathorMap(long lMapIndex)
{
	const long lBase = lMapIndex >= 10000 ? lMapIndex / 10000 : lMapIndex;
	return lBase == GUILDSYS_BALATHOR_MAP;
}

bool GuildSysSkillMapAllowed(long lMapIndex)
{
	return GuildSysIsBalathorMap(lMapIndex);
}

bool GuildSysBookOnlySkill(unsigned int dwVnum)
{
	return dwVnum >= GUILDSYS_SKILL_STORM && dwVnum <= GUILDSYS_SKILL_FIRMNESS;
}

bool GuildSysUseSkill(CGuild* g, LPCHARACTER ch, unsigned int dwVnum, int iNeededSP)
{
	if (!g || !ch)
		return false;

	const bool bBalathor = GuildSysBookOnlySkill(dwVnum);
	const bool bLair = GuildSysIsBalathorMap(ch->GetMapIndex());
	if (!bBalathor && !bLair)
		return false;	// the engine's own (the arena while at war, the teleport)

	if (!bLair && !g->UnderAnyWar())
	{
		ch->ChatPacket(CHAT_TYPE_INFO, "[Gildia] Tej umiej\xeatno\x9c" "ci mo\xbfna u\xbfy\xe6 tylko podczas wojny gildii albo w Krypcie Balathora.");
		return true;
	}

	CSkillProto* pkSk = CSkillManager::instance().Get(dwVnum);
	if (!pkSk)
		return true;

	const int iLevel = g->GetSkillLevel(dwVnum);
	g->SendDBSkillUpdate(-iNeededSP);

	long lDuration = 0;
	if (bBalathor)
	{
		const double k = pkSk->bMaxLevel ? 1.0 * iLevel / pkSk->bMaxLevel : 0.0;
		pkSk->kDurationPoly.SetVar("k", k);
		lDuration = (long)pkSk->kDurationPoly.Eval();
		if (lDuration <= 0)
			lDuration = 300;
	}

	// the members on the caster's map (the engine's own loop takes every member online, wherever he is)
	const long lMapIndex = ch->GetMapIndex();
	std::vector<LPCHARACTER> v = GuildSysAccess::Online(g);
	for (size_t i = 0; i < v.size(); ++i)
	{
		LPCHARACTER victim = v[i];
		if (!victim || victim->GetMapIndex() != lMapIndex || victim->IsDead())
			continue;

		victim->RemoveAffect(dwVnum);
		if (bBalathor)
			victim->AddAffect(dwVnum, POINT_NONE, ImmuneChance(iLevel), 0, lDuration, 0, true);
		else
			ch->ComputeSkill(dwVnum, victim, (BYTE)iLevel);
	}

	sys_log(0, "GUILDSYS: skill %u level %d by %s[%u] guild %s[%u] map %ld", dwVnum, iLevel, ch->GetName(),
			ch->GetPlayerID(), g->GetName(), g->GetID(), lMapIndex);
	return true;
}

bool GuildSysUseItem(LPCHARACTER ch, LPITEM item)
{
	if (!ch || !item)
		return false;

	switch (item->GetVnum())
	{
		case GUILDSYS_BOOK_STORM:		return ReadSkillBook(ch, item, GUILDSYS_SKILL_STORM);
		case GUILDSYS_BOOK_WILL:		return ReadSkillBook(ch, item, GUILDSYS_SKILL_WILL);
		case GUILDSYS_BOOK_FIRMNESS:	return ReadSkillBook(ch, item, GUILDSYS_SKILL_FIRMNESS);
		case GUILDSYS_BOOK_FORGET:		return ReadForgetBook(ch, item);
	}
	return false;
}

bool GuildSysIsImmune(LPCHARACTER ch, unsigned int dwImmuneFlag)
{
	if (!ch || !ch->IsPC())
		return false;

	switch (dwImmuneFlag)
	{
		case IMMUNE_STUN:
			return AffectImmune(ch, GUILDSYS_SKILL_STORM) || AffectImmune(ch, GUILDSYS_SKILL_WILL);
		case IMMUNE_SLOW:
			return AffectImmune(ch, GUILDSYS_SKILL_STORM);
		case IMMUNE_ROOT:
		case GUILDSYS_IMMUNE_FREEZE:
			return AffectImmune(ch, GUILDSYS_SKILL_WILL);
		case IMMUNE_FALL:
			return AffectImmune(ch, GUILDSYS_SKILL_FIRMNESS);
	}
	return false;
}

bool GuildSysResistPush(LPCHARACTER ch)
{
	return ch && ch->IsPC() && AffectImmune(ch, GUILDSYS_SKILL_FIRMNESS);
}

unsigned int GuildSysCreateTime(CGuild* g)
{
	if (!g)
		return 0;

	static std::map<DWORD, unsigned int> s_mapCreate;
	std::map<DWORD, unsigned int>::const_iterator it = s_mapCreate.find(g->GetID());
	if (it != s_mapCreate.end())
		return it->second;

	char szQuery[128];
	snprintf(szQuery, sizeof(szQuery), "SELECT create_time FROM guild%s WHERE id=%u", get_table_postfix(), g->GetID());
	unsigned int t = 0;
	if (!QueryUInt(t, szQuery))
		return (unsigned int)get_global_time();	// not written yet: a guild of this moment
	s_mapCreate[g->GetID()] = t;
	return t;
}

unsigned int GuildSysMemberJoinTime(CGuild* g, unsigned int dwPID)
{
	if (!g || !dwPID || !g->GetMember(dwPID))
		return 0;

	char szQuery[160];
	snprintf(szQuery, sizeof(szQuery), "SELECT join_time FROM guild_member%s WHERE pid=%u AND guild_id=%u",
			get_table_postfix(), dwPID, g->GetID());
	unsigned int t = 0;
	if (!QueryUInt(t, szQuery))
		return (unsigned int)get_global_time();	// the db core has not written the join yet
	return t;
}

int GuildSysCheckRequirements(LPCHARACTER ch, int iMinLevel, int iMinGuildHours, int iMinMemberHours, long long llMinBank)
{
	CGuild* g = ch ? ch->GetGuild() : NULL;
	if (!g)
		return 1;
	if (g->GetLevel() < iMinLevel)
		return 2;

	const long long now = get_global_time();
	if (iMinGuildHours > 0 && now - (long long)GuildSysCreateTime(g) < (long long)iMinGuildHours * 3600)
		return 3;
	if (iMinMemberHours > 0 && now - (long long)GuildSysMemberJoinTime(g, ch->GetPlayerID()) < (long long)iMinMemberHours * 3600)
		return 4;
	if (llMinBank > 0 && (long long)g->GetGuildMoneyAvailable() < llMinBank)
		return 5;
	return 0;
}

// ---------------------------------------------------------------- quest functions (questlua_guild.cpp's list)
namespace quest
{
	namespace
	{
		CGuild* QuestGuild()
		{
			LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
			return ch ? ch->GetGuild() : NULL;
		}

		// the pid argument (or the quest's character): his guild and pid
		CGuild* PidGuild(lua_State* L, int iArg, DWORD& dwPID)
		{
			LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
			dwPID = lua_isnumber(L, iArg) ? (DWORD)lua_tonumber(L, iArg) : (ch ? ch->GetPlayerID() : 0);
			if (!dwPID)
				return NULL;
			if (ch && ch->GetPlayerID() == dwPID)
				return ch->GetGuild();
			return CGuildManager::instance().GetLinkedGuild(dwPID);
		}
	}

	// guild.get_level() - the level of the character's guild, 0 without one
	int guildsys_get_level(lua_State* L)
	{
		CGuild* g = QuestGuild();
		lua_pushnumber(L, g ? g->GetLevel() : 0);
		return 1;
	}

	// guild.create_time() - unix time the character's guild was founded (0: before guildsys.sql or no guild)
	int guildsys_create_time(lua_State* L)
	{
		CGuild* g = QuestGuild();
		lua_pushnumber(L, g ? GuildSysCreateTime(g) : 0);
		return 1;
	}

	// guild.age() - seconds since the guild was founded (-1 without a guild)
	int guildsys_age(lua_State* L)
	{
		CGuild* g = QuestGuild();
		lua_pushnumber(L, g ? (double)(get_global_time() - (long long)GuildSysCreateTime(g)) : -1);
		return 1;
	}

	// guild.member_join_time([pid]) - unix time the character (or pid) joined his guild (0: before guildsys.sql or no guild)
	int guildsys_member_join_time(lua_State* L)
	{
		DWORD dwPID = 0;
		CGuild* g = PidGuild(L, 1, dwPID);
		lua_pushnumber(L, g ? GuildSysMemberJoinTime(g, dwPID) : 0);
		return 1;
	}

	// guild.member_age([pid]) - seconds the character (or pid) has been in his guild (-1 without a guild)
	int guildsys_member_age(lua_State* L)
	{
		DWORD dwPID = 0;
		CGuild* g = PidGuild(L, 1, dwPID);
		lua_pushnumber(L, g ? (double)(get_global_time() - (long long)GuildSysMemberJoinTime(g, dwPID)) : -1);
		return 1;
	}

	// guild.get_bank() - the treasury yang that may be spent (guild.treasury_available's value)
	int guildsys_get_bank(lua_State* L)
	{
		CGuild* g = QuestGuild();
		lua_pushnumber(L, g ? (double)g->GetGuildMoneyAvailable() : 0);
		return 1;
	}

	// guild.check_requirements(min_level, min_guild_hours, min_member_hours, min_bank) - 0 OK, 1 no guild, 2 level,
	// 3 the guild too young, 4 the character too short in it, 5 the treasury too small
	int guildsys_check_requirements(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		const int iLevel = lua_isnumber(L, 1) ? (int)lua_tonumber(L, 1) : 0;
		const int iGuildHours = lua_isnumber(L, 2) ? (int)lua_tonumber(L, 2) : 0;
		const int iMemberHours = lua_isnumber(L, 3) ? (int)lua_tonumber(L, 3) : 0;
		const long long llBank = lua_isnumber(L, 4) ? (long long)lua_tonumber(L, 4) : 0;
		lua_pushnumber(L, GuildSysCheckRequirements(ch, iLevel, iGuildHours, iMemberHours, llBank));
		return 1;
	}
}
