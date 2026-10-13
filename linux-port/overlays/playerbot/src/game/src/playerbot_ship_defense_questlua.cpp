// MT2009_PLUS_SHIP_DEFENSE_V1: Obrona Statku - the quests' "dw" module (Owsap's
// questlua_defense_wave.cpp, rewritten for playerbot_ship_defense.h; server-patches/shipdefense).
// The quest makes the instance itself (d.new_jump_pids to 367, as our other dungeons): the ship
// binds to it when the first person comes aboard. Registered from questlua.cpp (edits.json).
//
//   dw.cfg(name)              a setting: event flag "shipdef_<name>" or its default (min_level 90,
//                             party_only 0, fee 5000000, cooldown 0, daily_limit 10 ...)
//   dw.map_index()            367
//   dw.count()                ships on this core
//   dw.find(map_index)        true when that instance has a ship
//   dw.start()                the wheel: wave 1's countdown (false when already started)
//   dw.is_started()           true from the start on
//   dw.wave() / dw.state()    0-4 / 0 idle, 1 countdown, 2 running, 3 between, 4 won, 5 lost, 6 closed
//   dw.mast_hp_pct()          the mast's HP in per cent
//   dw.set_alliance_hp_pct(n) a plank on the mast: +n% HP (repair_pct when n is 0), stuns the person
//   dw.close()                ends the ship and sends everyone back where they came from
#include "stdafx.h"
#include "questlua.h"
#include "questmanager.h"
#include "char.h"
#include "dungeon.h"
#include "playerbot_ship_defense.h"

namespace quest
{
	static CShipDefense* dw_current_ship()
	{
		LPCHARACTER ch = CQuestManager::instance().GetCurrentCharacterPtr();
		if (!ch)
			return NULL;
		return CShipDefenseManager::instance().Attach(ch->GetMapIndex());
	}

	int dw_cfg(lua_State* L)
	{
		if (!lua_isstring(L, 1))
		{
			lua_pushnumber(L, 0);
			return 1;
		}
		lua_pushnumber(L, ship_defense::Cfg(lua_tostring(L, 1)));
		return 1;
	}

	int dw_map_index(lua_State* L)
	{
		lua_pushnumber(L, ship_defense::MAP_INDEX);
		return 1;
	}

	int dw_count(lua_State* L)
	{
		lua_pushnumber(L, (double)CShipDefenseManager::instance().Count());
		return 1;
	}

	int dw_find(lua_State* L)
	{
		const long lMapIndex = lua_isnumber(L, 1) ? (long)lua_tonumber(L, 1) : 0;
		lua_pushboolean(L, CShipDefenseManager::instance().Attach(lMapIndex) != NULL);
		return 1;
	}

	int dw_start(lua_State* L)
	{
		CShipDefense* pShip = dw_current_ship();
		lua_pushboolean(L, pShip && pShip->Start());
		return 1;
	}

	int dw_is_started(lua_State* L)
	{
		CShipDefense* pShip = dw_current_ship();
		lua_pushboolean(L, pShip && pShip->IsStarted());
		return 1;
	}

	int dw_wave(lua_State* L)
	{
		CShipDefense* pShip = dw_current_ship();
		lua_pushnumber(L, pShip ? pShip->GetWave() : 0);
		return 1;
	}

	int dw_state(lua_State* L)
	{
		CShipDefense* pShip = dw_current_ship();
		lua_pushnumber(L, pShip ? pShip->GetState() : ship_defense::STATE_CLOSED);
		return 1;
	}

	int dw_mast_hp_pct(lua_State* L)
	{
		CShipDefense* pShip = dw_current_ship();
		lua_pushnumber(L, pShip ? pShip->GetMastHPPct() : 0);
		return 1;
	}

	int dw_set_alliance_hp_pct(lua_State* L)
	{
		CShipDefense* pShip = dw_current_ship();
		int iPct = lua_isnumber(L, 1) ? (int)lua_tonumber(L, 1) : 0;
		if (iPct <= 0)
			iPct = ship_defense::Cfg("repair_pct");
		lua_pushboolean(L, pShip && pShip->Repair(CQuestManager::instance().GetCurrentCharacterPtr(), iPct));
		return 1;
	}

	int dw_close(lua_State* L)
	{
		CShipDefense* pShip = dw_current_ship();
		if (pShip)
			pShip->Close(true);
		return 0;
	}

	void RegisterShipDefenseFunctionTable()
	{
		luaL_reg dw_functions[] =
		{
			{ "cfg",			dw_cfg			},
			{ "map_index",			dw_map_index		},
			{ "count",			dw_count		},
			{ "find",			dw_find			},
			{ "start",			dw_start		},
			{ "is_started",			dw_is_started		},
			{ "wave",			dw_wave			},
			{ "state",			dw_state		},
			{ "mast_hp_pct",		dw_mast_hp_pct		},
			{ "set_alliance_hp_pct",	dw_set_alliance_hp_pct	},
			{ "close",			dw_close		},
			{ NULL,				NULL			}
		};

		CQuestManager::instance().AddLuaFunctionTable("dw", dw_functions);
	}
}
