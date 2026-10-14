/**
* MT2009_PLUS_CHAMPION_V2 - Poziom Czempiona and the Sung Ma stats in the Yohara 3.0 exe (server-patches/czempion,
* "Etap B"). The points are the server's (Server/common/length.h): 178-183 the element powers of the talismans,
* 184-187 POINT_SUNGMA_STR/HP/MOVE/IMMUNE (= APPLY_SUNGMA_*, an apply is a point in this engine), 188-192
* POINT_CONQUEROR_LEVEL/_LEVEL_STEP/_EXP/_NEXT_EXP/_POINT; the points packet carries all 193 (the server's
* POINT_PACKET_NUM). The champion level of others comes in the add/update packets (dwConquerorLevel,
* NetworkActorManager.cpp), the own one with the points (PythonPlayer.cpp); InstanceBaseEffect.cpp draws it in blue.
*
* Python (the names root's uicharacter.py and GF's uicharacternew.py read):
*   player.CONQUEROR_LEVEL / CONQUEROR_LEVEL_STEP / CONQUEROR_EXP / CONQUEROR_NEXT_EXP / CONQUEROR_POINT,
*   player.SUNGMA_STR / SUNGMA_HP / SUNGMA_MOVE / SUNGMA_IMMUNE (and GF's SUNGMA_INMUNE), player.POINT_* of all 15,
*   player.GetConquerorEXP(), player.GetConquerorNextEXP(), player.GetConquerorLevel(), player.CONQUEROR_LEVEL_MAX,
*   item.APPLY_SUNGMA_STR / _HP / _MOVE / _IMMUNE, item.APPLY_ENCHANT_* , item.LIMIT_CONQUEROR_LEVEL,
*   app.MT2009_CHAMPION_EXE (1: root's constinfo.py reports the 3.0 client version only with this exe).
*
* MT2009_PLUS_YOHARA_EXE2_V1 (the second exe round): points 193-196 POINT_SUNGMA_PER_STR/HP/MOVE/IMMUNE and 197
* POINT_HIT_PCT (Precyzja) after the packet's 193 (POINT_PACKET_NUM; they come as point changes), POINT_MAX_NUM 198:
*   player.SUNGMA_PER_STR / _HP / _MOVE / _IMMUNE, player.HIT_PCT (and player.POINT_* of them), item.APPLY_SUNGMA_PER_*,
*   item.APPLY_HIT_PCT, item.METIN_SUNGMA, item.EQUIPMENT_GLOVE (ENABLE_GLOVE_SYSTEM, PythonItemModule.cpp),
*   effect.FLY_CONQUEROR_EXP, app.MT2009_YOHARA_EXE2 (1: the glove slot, the stones and the points are there).
*/
#include "StdAfx.h"
#include "PythonPlayer.h"
#include "Packet.h"

#ifdef ENABLE_CONQUEROR_LEVEL

// the numbers must be the server's (common/length.h, common/item_length.h of the engine with server-patches/czempion)
static_assert(POINT_ACCEDRAIN_RATE == 177, "POINT_ACCEDRAIN_RATE differs from the server (ENABLE_ACCE_COSTUME_SYSTEM?)");
static_assert(POINT_ENCHANT_ELECT == 178, "the element powers must stay 178-183 (item_proto applytypes of the talismans)");
static_assert(POINT_SUNGMA_STR == 184, "POINT_SUNGMA_STR differs from the server");
static_assert(POINT_CONQUEROR_LEVEL == 188, "POINT_CONQUEROR_LEVEL differs from the server");
static_assert(POINT_PACKET_NUM == 193, "the points packet carries the server's POINT_PACKET_NUM (193) points");
static_assert(POINT_SUNGMA_PER_STR == 193 && POINT_SUNGMA_PER_IMMUNE == 196, "POINT_SUNGMA_PER_* differ from the server (193-196)");
static_assert(POINT_HIT_PCT == 197 && POINT_MAX_NUM == 198, "POINT_HIT_PCT (197) / POINT_MAX_NUM (198) differ from the server");
static_assert(METIN_SUNGMA == 2, "METIN_SUNGMA differs from the server (2)");
static_assert(FLY_CONQUEROR_EXP == 30, "FLY_CONQUEROR_EXP differs from the server (30)");
#ifdef ENABLE_GLOVE_SYSTEM
static_assert(WEAR_GLOVE == 26 && ARMOR_GLOVE == 8 && WEARABLE_GLOVE == (1 << 13), "the glove's numbers differ from the server");
#endif
static_assert(LIMIT_CONQUEROR_LEVEL == 10, "LIMIT_CONQUEROR_LEVEL differs from the server");
static_assert(sizeof(TPacketGCPoints) == 1 + 4 * 193, "the points packet is 773 B on the server");
static_assert(sizeof(TPacketGCCharacterAdditionalInfo) == 70, "GC additional info is 70 B on the server (game -m32, pack(1))");
static_assert(sizeof(TPacketGCCharacterUpdate) == 52, "GC character update is 52 B on the server (game -m32, pack(1))");

namespace
{
	PyObject* playerGetConquerorEXP(PyObject* poSelf, PyObject* poArgs)
	{
		DWORD dwEXP = CPythonPlayer::Instance().GetStatus(POINT_CONQUEROR_EXP);
		return Py_BuildValue("l", dwEXP);
	}

	PyObject* playerGetConquerorNextEXP(PyObject* poSelf, PyObject* poArgs)
	{
		DWORD dwEXP = CPythonPlayer::Instance().GetStatus(POINT_CONQUEROR_NEXT_EXP);
		return Py_BuildValue("l", dwEXP);
	}

	PyObject* playerGetConquerorLevel(PyObject* poSelf, PyObject* poArgs)
	{
		return Py_BuildValue("i", CPythonPlayer::Instance().GetStatus(POINT_CONQUEROR_LEVEL));
	}

	void AddFunctions(const char* c_szModule, PyMethodDef* pMethods)
	{
		PyObject* poModule = PyImport_AddModule(c_szModule);	// borrowed
		if (!poModule)
			return;
		for (PyMethodDef* p = pMethods; p->ml_name; ++p)
			PyModule_AddObject(poModule, p->ml_name, PyCFunction_New(p, NULL));
	}

	void AddInt(const char* c_szModule, const char* c_szName, long lValue)
	{
		PyObject* poModule = PyImport_AddModule(c_szModule);	// borrowed
		if (poModule)
			PyModule_AddIntConstant(poModule, c_szName, lValue);
	}
}

void Mt2009Champion_RegisterPython()
{
	static PyMethodDef s_playerMethods[] =
	{
		{ "GetConquerorEXP",		playerGetConquerorEXP,		METH_VARARGS },
		{ "GetConquerorNextEXP",	playerGetConquerorNextEXP,	METH_VARARGS },
		{ "GetConquerorLevel",		playerGetConquerorLevel,	METH_VARARGS },
		{ NULL, NULL, 0 },
	};
	AddFunctions("player", s_playerMethods);

	AddInt("player", "CONQUEROR_LEVEL", POINT_CONQUEROR_LEVEL);
	AddInt("player", "CONQUEROR_LEVEL_STEP", POINT_CONQUEROR_LEVEL_STEP);
	AddInt("player", "CONQUEROR_EXP", POINT_CONQUEROR_EXP);
	AddInt("player", "CONQUEROR_NEXT_EXP", POINT_CONQUEROR_NEXT_EXP);
	AddInt("player", "CONQUEROR_POINT", POINT_CONQUEROR_POINT);
	AddInt("player", "CONQUEROR_LEVEL_MAX", 30);	// champion::MAX_LEVEL of the server
	AddInt("player", "SUNGMA_STR", POINT_SUNGMA_STR);
	AddInt("player", "SUNGMA_HP", POINT_SUNGMA_HP);
	AddInt("player", "SUNGMA_MOVE", POINT_SUNGMA_MOVE);
	AddInt("player", "SUNGMA_IMMUNE", POINT_SUNGMA_IMMUNE);
	AddInt("player", "SUNGMA_INMUNE", POINT_SUNGMA_IMMUNE);	// GF's spelling (uicharacternew.py)

	AddInt("player", "POINT_CONQUEROR_LEVEL", POINT_CONQUEROR_LEVEL);
	AddInt("player", "POINT_CONQUEROR_LEVEL_STEP", POINT_CONQUEROR_LEVEL_STEP);
	AddInt("player", "POINT_CONQUEROR_EXP", POINT_CONQUEROR_EXP);
	AddInt("player", "POINT_CONQUEROR_NEXT_EXP", POINT_CONQUEROR_NEXT_EXP);
	AddInt("player", "POINT_CONQUEROR_POINT", POINT_CONQUEROR_POINT);
	AddInt("player", "POINT_SUNGMA_STR", POINT_SUNGMA_STR);
	AddInt("player", "POINT_SUNGMA_HP", POINT_SUNGMA_HP);
	AddInt("player", "POINT_SUNGMA_MOVE", POINT_SUNGMA_MOVE);
	AddInt("player", "POINT_SUNGMA_IMMUNE", POINT_SUNGMA_IMMUNE);
	AddInt("player", "POINT_ENCHANT_ELECT", POINT_ENCHANT_ELECT);
	AddInt("player", "POINT_ENCHANT_FIRE", POINT_ENCHANT_FIRE);
	AddInt("player", "POINT_ENCHANT_ICE", POINT_ENCHANT_ICE);
	AddInt("player", "POINT_ENCHANT_WIND", POINT_ENCHANT_WIND);
	AddInt("player", "POINT_ENCHANT_EARTH", POINT_ENCHANT_EARTH);
	AddInt("player", "POINT_ENCHANT_DARK", POINT_ENCHANT_DARK);

	AddInt("item", "APPLY_SUNGMA_STR", POINT_SUNGMA_STR);
	AddInt("item", "APPLY_SUNGMA_HP", POINT_SUNGMA_HP);
	AddInt("item", "APPLY_SUNGMA_MOVE", POINT_SUNGMA_MOVE);
	AddInt("item", "APPLY_SUNGMA_IMMUNE", POINT_SUNGMA_IMMUNE);
	AddInt("item", "APPLY_ENCHANT_ELECT", POINT_ENCHANT_ELECT);
	AddInt("item", "APPLY_ENCHANT_FIRE", POINT_ENCHANT_FIRE);
	AddInt("item", "APPLY_ENCHANT_ICE", POINT_ENCHANT_ICE);
	AddInt("item", "APPLY_ENCHANT_WIND", POINT_ENCHANT_WIND);
	AddInt("item", "APPLY_ENCHANT_EARTH", POINT_ENCHANT_EARTH);
	AddInt("item", "APPLY_ENCHANT_DARK", POINT_ENCHANT_DARK);
	AddInt("item", "LIMIT_CONQUEROR_LEVEL", LIMIT_CONQUEROR_LEVEL);

	AddInt("app", "MT2009_CHAMPION_EXE", 1);

	// MT2009_PLUS_YOHARA_EXE2_V1
	AddInt("player", "SUNGMA_PER_STR", POINT_SUNGMA_PER_STR);
	AddInt("player", "SUNGMA_PER_HP", POINT_SUNGMA_PER_HP);
	AddInt("player", "SUNGMA_PER_MOVE", POINT_SUNGMA_PER_MOVE);
	AddInt("player", "SUNGMA_PER_IMMUNE", POINT_SUNGMA_PER_IMMUNE);
	AddInt("player", "HIT_PCT", POINT_HIT_PCT);
	AddInt("player", "POINT_SUNGMA_PER_STR", POINT_SUNGMA_PER_STR);
	AddInt("player", "POINT_SUNGMA_PER_HP", POINT_SUNGMA_PER_HP);
	AddInt("player", "POINT_SUNGMA_PER_MOVE", POINT_SUNGMA_PER_MOVE);
	AddInt("player", "POINT_SUNGMA_PER_IMMUNE", POINT_SUNGMA_PER_IMMUNE);
	AddInt("player", "POINT_HIT_PCT", POINT_HIT_PCT);
	AddInt("item", "APPLY_SUNGMA_PER_STR", POINT_SUNGMA_PER_STR);
	AddInt("item", "APPLY_SUNGMA_PER_HP", POINT_SUNGMA_PER_HP);
	AddInt("item", "APPLY_SUNGMA_PER_MOVE", POINT_SUNGMA_PER_MOVE);
	AddInt("item", "APPLY_SUNGMA_PER_IMMUNE", POINT_SUNGMA_PER_IMMUNE);
	AddInt("item", "APPLY_HIT_PCT", POINT_HIT_PCT);
	AddInt("item", "METIN_SUNGMA", METIN_SUNGMA);
	AddInt("effect", "FLY_CONQUEROR_EXP", FLY_CONQUEROR_EXP);
	AddInt("app", "MT2009_YOHARA_EXE2", 1);
}
#endif // ENABLE_CONQUEROR_LEVEL
