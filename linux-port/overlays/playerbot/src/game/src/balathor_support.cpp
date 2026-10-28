// MT2009_PLUS_BALATHOR_V1: Krypta Balathora (author: dracaryS) - the author's small helpers that the package
// puts into guild.cpp, guild_manager.cpp, questlua_guild.cpp and utils.cpp, kept here so those engine files
// only get the declarations (server-patches/balathor). guild.get_near_count / get_near_pids / get_flag /
// set_flag / get_level are added to the "guild" quest table (RegisterBalathorGuildFunctions, called from
// questlua.cpp next to RegisterBalathorFunctionTable).
#include "stdafx.h"

#ifdef __BALATHOR__
#include <string>
#include <vector>
#include "utils.h"
#include "char.h"
#include "guild.h"
#include "guild_manager.h"
#include "questmanager.h"
#include "config.h"
#include "balathor.h"

// "1d 2h 3m 4s" (only the parts that are not 0), "0s" for nothing.
std::string SecToTime(int sec)
{
	if (sec <= 0)
		return "0s";
	const int parts[4] = { sec / 86400, (sec % 86400) / 3600, (sec % 3600) / 60, sec % 60 };
	const char* units[4] = { "d", "h", "m", "s" };
	std::string text;
	for (int i = 0; i < 4; ++i)
	{
		if (parts[i] <= 0)
			continue;
		if (!text.empty())
			text += " ";
		text += std::to_string(parts[i]);
		text += units[i];
	}
	return text;
}

// A guild's own event flag "?.<name>_<guild id>" (the db core does not store "?.balathor_channel_*").
int CGuildManager::GetFlag(DWORD dwID, const char* szFlag)
{
	char szBuf[64];
	snprintf(szBuf, sizeof(szBuf), "?.%s_%u", szFlag, dwID);
	return quest::CQuestManager::instance().GetEventFlag(szBuf);
}

void CGuildManager::SetFlag(DWORD dwID, const char* szFlag, int iValue)
{
	char szBuf[64];
	snprintf(szBuf, sizeof(szBuf), "?.%s_%u", szFlag, dwID);
	quest::CQuestManager::instance().RequestSetEventFlag(szBuf, iValue);
	quest::CQuestManager::instance().SetEventFlag(szBuf, iValue);
}

int CGuild::GetFlag(const char* szFlag)
{
	return CGuildManager::instance().GetFlag(GetID(), szFlag);
}

void CGuild::SetFlag(const char* szFlag, int iValue)
{
	CGuildManager::instance().SetFlag(GetID(), szFlag, iValue);
}

// chExcept and the members of this guild online on the same map within fNeedDistance of it, as player IDs
// (chExcept first). The package put chExcept's VID first - a player ID is what the quest's
// q.begin_other_pc_block needs.
void CGuild::GetNearMemberCount(std::vector<DWORD>& vecPlayers, float fNeedDistance, LPCHARACTER chExcept)
{
	if (!chExcept)
		return;
	vecPlayers.emplace_back(chExcept->GetPlayerID());

	const long lMapIndex = chExcept->GetMapIndex();
	const long lX = chExcept->GetX();
	const long lY = chExcept->GetY();

	for (auto it = m_memberOnline.begin(); it != m_memberOnline.end(); ++it)
	{
		LPCHARACTER ch = *it;
		if (!ch || ch == chExcept || ch->GetMapIndex() != lMapIndex)
			continue;
		if (DISTANCE_APPROX(ch->GetX() - lX, ch->GetY() - lY) < fNeedDistance)
			vecPlayers.emplace_back(ch->GetPlayerID());
	}
}

namespace quest
{
	static CGuild* BalathorQuestGuild()
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		return ch ? ch->GetGuild() : NULL;
	}

	static int guild_get_near_count(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		CGuild* pGuild = BalathorQuestGuild();
		std::vector<DWORD> vecPlayers;
		if (pGuild)
			pGuild->GetNearMemberCount(vecPlayers, 2500.0f, ch);
		lua_pushnumber(L, vecPlayers.size());
		return 1;
	}

	static int guild_get_near_pids(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		CGuild* pGuild = BalathorQuestGuild();
		if (!pGuild)
			return 0;
		std::vector<DWORD> vecPlayers;
		pGuild->GetNearMemberCount(vecPlayers, 2500.0f, ch);
		if (!lua_checkstack(L, (int) vecPlayers.size()))
			return 0;
		for (const auto& pid : vecPlayers)
			lua_pushnumber(L, pid);
		return (int) vecPlayers.size();
	}

	static int guild_get_flag(lua_State* L)
	{
		CGuild* pGuild = BalathorQuestGuild();
		int iResult = 0;
		if (pGuild && lua_isstring(L, 1))
			iResult = pGuild->GetFlag(lua_tostring(L, 1));
		lua_pushnumber(L, iResult);
		return 1;
	}

	static int guild_set_flag(lua_State* L)
	{
		CGuild* pGuild = BalathorQuestGuild();
		if (pGuild && lua_isstring(L, 1) && lua_isnumber(L, 2))
			pGuild->SetFlag(lua_tostring(L, 1), (int) lua_tonumber(L, 2));
		return 0;
	}

	static int guild_get_level(lua_State* L)
	{
		CGuild* pGuild = BalathorQuestGuild();
		lua_pushnumber(L, pGuild ? pGuild->GetLevel() : 0);
		return 1;
	}

	// balathor.is_open(): the lair's map (balathor.json map_index, 420) is hosted by this core - false while
	// M2_BALATHOR_ON is 0 (bin/m2-render-config), so the quest offers nothing then.
	static int balathor_is_open(lua_State* L)
	{
		const DWORD dwMapIndex = CBalathorManager::Instance().GetConfig().dwMapIndex;
		lua_pushboolean(L, dwMapIndex != 0 && map_allow_find(dwMapIndex));
		return 1;
	}

	static void BalathorAddToTable(lua_State* L, const char* table, const luaL_reg* reg)
	{
		lua_getglobal(L, table);
		if (!lua_istable(L, -1))
		{
			lua_pop(L, 1);
			sys_err("BALATHOR: the quest table %s does not exist", table);
			return;
		}
		for (; reg->name; ++reg)
		{
			// a function the line already has (a later guild patch) is kept
			lua_pushstring(L, reg->name);
			lua_rawget(L, -2);
			const bool bHas = !lua_isnil(L, -1);
			lua_pop(L, 1);
			if (bHas)
				continue;
			lua_pushstring(L, reg->name);
			lua_pushcfunction(L, reg->func);
			lua_rawset(L, -3);
		}
		lua_pop(L, 1);
	}

	// questlua.cpp calls it inside namespace quest, after RegisterGuildFunctionTable and
	// RegisterBalathorFunctionTable made the tables.
	void RegisterBalathorGuildFunctions()
	{
		static const luaL_reg guild_add[] =
		{
			{ "get_near_count",	guild_get_near_count },
			{ "get_near_pids",	guild_get_near_pids },
			{ "get_flag",		guild_get_flag },
			{ "set_flag",		guild_set_flag },
			{ "get_level",		guild_get_level },
			{ NULL, NULL }
		};
		static const luaL_reg balathor_add[] =
		{
			{ "is_open",		balathor_is_open },
			{ NULL, NULL }
		};
		lua_State* L = CQuestManager::instance().GetLuaState();
		BalathorAddToTable(L, "guild", guild_add);
		BalathorAddToTable(L, "balathor", balathor_add);
	}
}
#endif
