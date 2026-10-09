/**
* MT2009_PLUS_ZODIAC_V1 - Swiatynia Zodiaku (Autor: Digi Rasta, nowy-system 0.35.0; the system after WLsj24's
* ZodiacTemple). GC 220 (the bosses' effects around a point), the 15 Zodiac SE_* of the special effect packet,
* chrmgr.IsDead / IsPC and the constants the Zodiac scripts read (app.ENABLE_12ZI, chat.CHAT_TYPE_*MISSION,
* chr.NEW_AFFECT_CZ_UNLIMIT_ENTER, chrmgr.EFFECT_*). wndMgr.SetCoolTimeImageBox / SetStartCoolTimeImageBox
* (the floor timer's ring) are MT2009_PLUS_MINIGAMES_V1's (EterPythonLib), not repeated here.
*/
#include "StdAfx.h"
#include "PythonCharacterManager.h"
#include "PythonNetworkStream.h"
#include "InstanceBase.h"
#include "../EffectLib/EffectManager.h"
#include "Mt2009Zodiak.h"

#ifdef ENABLE_12ZI

// the ids must be the same as in the server's common/length.h
static_assert(CHAT_TYPE_MISSION == 13, "CHAT_TYPE_MISSION differs from the server");
static_assert(SE_SKILL_DAMAGE_ZONE == 39, "SE_SKILL_DAMAGE_ZONE differs from the server (ENABLE_ACCE_COSTUME_SYSTEM?)");
static_assert(SE_SKILL_SAFE_ZONE_SMALL - SE_SKILL_DAMAGE_ZONE == CInstanceBase::EFFECT_SKILL_SAFE_ZONE_SMALL - CInstanceBase::EFFECT_SKILL_DAMAGE_ZONE,
	"SE_* and EFFECT_* of the zodiac effects must be in the same order");
static_assert(sizeof(TPacketGCSpecialZodiacEffect) == 15, "GC 220 is 15 B on the server (game built with -m32, #pragma pack(1))");

DWORD Mt2009Zodiak_EffectFromSE(BYTE bType)
{
	if (bType < SE_SKILL_DAMAGE_ZONE || bType > SE_SKILL_SAFE_ZONE_SMALL)
		return (DWORD)-1;

	return CInstanceBase::EFFECT_SKILL_DAMAGE_ZONE + (bType - SE_SKILL_DAMAGE_ZONE);
}

void CInstanceBase::AttachSpecialZodiacEffect(DWORD eEftType, long lX, long lY)
{
	if (eEftType >= EFFECT_NUM)
		return;

	const D3DXMATRIX& c_rmatGlobal = m_GraphicThingInstance.GetTransform();

	D3DXMATRIX matrix;
	D3DXMatrixIdentity(&matrix);
	matrix._41 = float(lX);
	matrix._42 = -float(lY);
	matrix._43 = c_rmatGlobal._43;

	DWORD dwEffectCRC = ms_adwCRCAffectEffect[eEftType];
	DWORD dwEffectIndex = CEffectManager::Instance().GetEmptyIndex();
	CEffectManager::Instance().CreateEffectInstance(dwEffectIndex, dwEffectCRC);
	CEffectManager::Instance().SelectEffectInstance(dwEffectIndex);
	CEffectManager::Instance().SetEffectInstanceGlobalMatrix(matrix);
}

bool CPythonNetworkStream::RecvSpecialZodiacEffect()
{
	TPacketGCSpecialZodiacEffect kPacket;
	if (!AutoRecv(kPacket))
		return false;

	CInstanceBase* pInstance = CPythonCharacterManager::Instance().GetInstancePtr(kPacket.vid);
	if (!pInstance)
		return true;

	const BYTE abyType[2] = { kPacket.type, kPacket.type2 };
	for (int i = 0; i < 2; ++i)
	{
		if (!abyType[i])
			continue;

		const DWORD dwEffect = Mt2009Zodiak_EffectFromSE(abyType[i]);
		if ((DWORD)-1 == dwEffect)
		{
			TraceError("TPacketGCSpecialZodiacEffect: %d is not a zodiac effect", abyType[i]);
			continue;
		}

		pInstance->AttachSpecialZodiacEffect(dwEffect, kPacket.x, kPacket.y);
	}

	return true;
}

namespace
{
	PyObject* chrmgrIsDead(PyObject* poSelf, PyObject* poArgs)
	{
		int iVID;
		if (!PyTuple_GetInteger(poArgs, 0, &iVID))
			return Py_BadArgument();

		CInstanceBase* pInstance = CPythonCharacterManager::Instance().GetInstancePtr(iVID);
		return Py_BuildValue("i", (pInstance && pInstance->IsDead()) ? 1 : 0);
	}

	PyObject* chrmgrIsPC(PyObject* poSelf, PyObject* poArgs)
	{
		int iVID;
		if (!PyTuple_GetInteger(poArgs, 0, &iVID))
			return Py_BadArgument();

		CInstanceBase* pInstance = CPythonCharacterManager::Instance().GetInstancePtr(iVID);
		return Py_BuildValue("i", (pInstance && pInstance->IsPC()) ? 1 : 0);
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

void Mt2009Zodiak_RegisterPython()
{
	static PyMethodDef s_chrmgrMethods[] =
	{
		{ "IsDead",	chrmgrIsDead,	METH_VARARGS },
		{ "IsPC",	chrmgrIsPC,		METH_VARARGS },
		{ NULL, NULL, 0 },
	};
	AddFunctions("chrmgr", s_chrmgrMethods);

	AddInt("app", "ENABLE_12ZI", 1);
	AddInt("app", "ENABLE_CHAT_MISSION_ALTERNATIVE", 0);

	AddInt("chat", "CHAT_TYPE_MISSION", CHAT_TYPE_MISSION);
	AddInt("chat", "CHAT_TYPE_SUB_MISSION", CHAT_TYPE_SUB_MISSION);
	AddInt("chat", "CHAT_TYPE_CLEAR_MISSION", CHAT_TYPE_CLEAR_MISSION);

	AddInt("chr", "NEW_AFFECT_CZ_UNLIMIT_ENTER", 600);	// AFFECT_CZ_UNLIMIT_ENTER of the server

	AddInt("chrmgr", "EFFECT_SKILL_DAMAGE_ZONE", CInstanceBase::EFFECT_SKILL_DAMAGE_ZONE);
	AddInt("chrmgr", "EFFECT_SKILL_SAFE_ZONE", CInstanceBase::EFFECT_SKILL_SAFE_ZONE);
	AddInt("chrmgr", "EFFECT_METEOR", CInstanceBase::EFFECT_METEOR);
	AddInt("chrmgr", "EFFECT_BEAD_RAIN", CInstanceBase::EFFECT_BEAD_RAIN);
	AddInt("chrmgr", "EFFECT_FALL_ROCK", CInstanceBase::EFFECT_FALL_ROCK);
	AddInt("chrmgr", "EFFECT_ARROW_RAIN", CInstanceBase::EFFECT_ARROW_RAIN);
	AddInt("chrmgr", "EFFECT_HORSE_DROP", CInstanceBase::EFFECT_HORSE_DROP);
	AddInt("chrmgr", "EFFECT_EGG_DROP", CInstanceBase::EFFECT_EGG_DROP);
	AddInt("chrmgr", "EFFECT_DEAPO_BOOM", CInstanceBase::EFFECT_DEAPO_BOOM);
	AddInt("chrmgr", "EFFECT_SKILL_DAMAGE_ZONE_BIG", CInstanceBase::EFFECT_SKILL_DAMAGE_ZONE_BIG);
	AddInt("chrmgr", "EFFECT_SKILL_DAMAGE_ZONE_MIDDLE", CInstanceBase::EFFECT_SKILL_DAMAGE_ZONE_MIDDLE);
	AddInt("chrmgr", "EFFECT_SKILL_DAMAGE_ZONE_SMALL", CInstanceBase::EFFECT_SKILL_DAMAGE_ZONE_SMALL);
	AddInt("chrmgr", "EFFECT_SKILL_SAFE_ZONE_BIG", CInstanceBase::EFFECT_SKILL_SAFE_ZONE_BIG);
	AddInt("chrmgr", "EFFECT_SKILL_SAFE_ZONE_MIDDLE", CInstanceBase::EFFECT_SKILL_SAFE_ZONE_MIDDLE);
	AddInt("chrmgr", "EFFECT_SKILL_SAFE_ZONE_SMALL", CInstanceBase::EFFECT_SKILL_SAFE_ZONE_SMALL);
}
#endif // ENABLE_12ZI
