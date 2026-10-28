#include "stdafx.h"

#ifdef __BALATHOR__
#include "questmanager.h"
#include "balathor.h"
#include "char.h"
namespace quest
{
	int balathor_is_in_map(lua_State* L)
	{
		bool bResult = false;
		if (lua_isnumber(L, 1))
		{
			if (CBalathorManager::Instance().FindByMapIndex((DWORD)lua_tonumber(L, 1)))
				bResult = true;
		}
		lua_pushboolean(L, bResult);
		return 1;
	}

	int balathor_get_stage(lua_State* L)
	{
		BYTE bStage = BALATHOR_STAGE_NONE;

		if (lua_isnumber(L, 1))
		{
			CBalathor* pBalathor = CBalathorManager::Instance().FindByMapIndex((DWORD)lua_tonumber(L, 1));
			if (pBalathor)
				bStage = pBalathor->GetStage();
		}
		lua_pushnumber(L, bStage);
		return 1;
	}

	int balathor_set_stage(lua_State* L)
	{
		if (lua_isnumber(L, 1) && lua_isnumber(L, 2))
		{
			CBalathor* pBalathor = CBalathorManager::Instance().FindByMapIndex((DWORD)lua_tonumber(L, 1));
			if (pBalathor)
				pBalathor->SetStage((BYTE)lua_tonumber(L, 2));
		}
		return 0;
	}

	int balathor_can_use_hwatcha(lua_State* L)
	{
		bool bResult = false;
		if (lua_isnumber(L, 1))
		{
			CBalathor* pBalathor = CBalathorManager::Instance().FindByMapIndex((DWORD)lua_tonumber(L, 1));
			if (pBalathor)
				bResult = pBalathor->CanUseHwatcha();
		}
		lua_pushboolean(L, bResult);
		return 1;
	}

	int balathor_use_hwatcha(lua_State* L)
	{
		if (lua_isnumber(L, 1))
		{
			CBalathor* pBalathor = CBalathorManager::Instance().FindByMapIndex((DWORD)lua_tonumber(L, 1));
			if (pBalathor)
				pBalathor->UseHwatcha();
		}
		return 0;
	}

	int balathor_revive_hwatcha(lua_State* L)
	{
		bool bResult = false;
		if (lua_isnumber(L, 1))
		{
			CBalathor* pBalathor = CBalathorManager::Instance().FindByMapIndex((DWORD)lua_tonumber(L, 1));
			if (pBalathor)
				bResult = pBalathor->ReviveHwatcha();
		}
		lua_pushboolean(L, bResult);
		return 1;
	}

	int balathor_is_hwatcha_dead(lua_State* L)
	{
		bool bResult = false;
		if (lua_isnumber(L, 1))
		{
			CBalathor* pBalathor = CBalathorManager::Instance().FindByMapIndex((DWORD)lua_tonumber(L, 1));
			if (pBalathor)
				bResult = pBalathor->IsHwatchaDead();
		}
		lua_pushboolean(L, bResult);
		return 1;
	}

	int balathor_get_register_config(lua_State* L)
	{
		const SBalathorConfig& config = CBalathorManager::Instance().GetConfig();
		lua_pushnumber(L, config.bRegisterMinLevel);
		lua_pushnumber(L, config.bRegisterGuildMinLevel);
		lua_pushnumber(L, config.bRegisterMinMemberCount);
		lua_pushnumber(L, config.bRegisterMaxMemberCount);
		lua_pushnumber(L, config.dwRegisterLadderPoint);
		lua_pushnumber(L, config.dwRegisterTicketVnum);
		lua_pushnumber(L, config.dwRegisterWaitTime);
		return 7;
	}

	int balathor_is_guild_dungeon_exist(lua_State* L)
	{
		bool bResult = false;
		if (lua_isnumber(L, 1))
			bResult = CBalathorManager::Instance().IsGuildDungeonExist((DWORD)lua_tonumber(L, 1));
		lua_pushboolean(L, bResult);
		return 1;
	}

	int balathor_teleport(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch)
			CBalathorManager::Instance().Teleport(ch);
		return 0;
	}

	int balathor_warp_enter(lua_State* L)
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch)
			CBalathorManager::Instance().WarpEnter(ch);
		return 0;
	}

	int balathor_can_create(lua_State* L)
	{
		BYTE bResult = 0;
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch)
			bResult = CBalathorManager::Instance().CanCreate(ch);
		lua_pushnumber(L, bResult);
		return 1;
	}

	int balathor_create(lua_State* L)
	{
		BYTE bResult = 0;
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch)
			bResult = CBalathorManager::Instance().Create(ch);
		lua_pushnumber(L, bResult);
		return 1;
	}

	int balathor_give_up(lua_State* L)
	{
		if (lua_isnumber(L, 1))
		{
			CBalathor* pBalathor = CBalathorManager::Instance().FindByMapIndex((DWORD)lua_tonumber(L, 1));
			if (pBalathor)
				pBalathor->Finish(BALATHOR_FINISH_FAIL_BY_GAMEMASTER);
		}
		return 1;
	}

	int balathor_claim_reward(lua_State* L)
	{
		BYTE bResult = 0;
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (ch && lua_isnumber(L, 1))
		{
			CBalathor* pBalathor = CBalathorManager::Instance().FindByMapIndex((DWORD)lua_tonumber(L, 1));
			if (pBalathor)
				bResult = pBalathor->ClaimReward(ch);
		}
		lua_pushnumber(L, bResult);
		return 1;
	}

	void RegisterBalathorFunctionTable()
	{
		luaL_reg balathor_functions[] =
		{
			{ "is_in_map", balathor_is_in_map },
			{ "get_stage", balathor_get_stage },
			{ "set_stage", balathor_set_stage },
			{ "can_use_hwatcha", balathor_can_use_hwatcha },
			{ "use_hwatcha", balathor_use_hwatcha },
			{ "revive_hwatcha", balathor_revive_hwatcha },
			{ "is_hwatcha_dead", balathor_is_hwatcha_dead },
			{ "get_register_config", balathor_get_register_config },
			{ "is_guild_dungeon_exist", balathor_is_guild_dungeon_exist },
			{ "teleport", balathor_teleport },
			{ "warp_enter", balathor_warp_enter },
			{ "can_create", balathor_can_create },
			{ "create", balathor_create },
			{ "give_up", balathor_give_up },
			{ "claim_reward", balathor_claim_reward },
			{ NULL, NULL }
		};

		CQuestManager::instance().AddLuaFunctionTable("balathor", balathor_functions);
	}
};
#endif