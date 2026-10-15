/**
* MT2009_PLUS_AURA_V1 - Szata Aury in the Yohara 3.0 exe (server-patches/aura; Owsap v6.2.6 __AURA_COSTUME_SYSTEM__'s
* CInstanceBase::SetAura, Autor: Owsap). Only the effect of the outfit on the characters is the exe's: the outfit's
* slot, windows and tooltip are root's (uiaura.py), and the server tells who wears which outfit with a chat command
* ("AURA view <vid> <vnum>", sent when a character comes into view and when its outfit changes) instead of Owsap's
* PART_AURA in the character packets - no packet changes, an old exe simply draws nothing.
*
* Python:
*   chrmgr.RegisterAuraEffect(vnum, file)   the outfit's effect (.mse; root: d:/ymir work/pc/common/effect/aura/...)
*   chrmgr.SetAura(vid, vnum)               the outfit an actor wears (0: none); kept in the actor's network data,
*                                           so the instance made again (it comes into sight, a mount, a new armour
*                                           shape) gets it back; 1 when the actor is known
*   chrmgr.GetAura(vid)                     the outfit of an actor's instance (0: none / no instance)
* The effect hangs on "Bip01 Spine2" (Owsap) and is not drawn on a polymorphed or an animal-wear character.
*/
#include "StdAfx.h"
#include "InstanceBase.h"
#include "NetworkActorManager.h"
#include "PythonCharacterManager.h"
#include "../EffectLib/EffectManager.h"

#include <algorithm>
#include <map>
#include <string>

#ifdef ENABLE_MT2009_AURA

CNetworkActorManager* CNetworkActorManager::ms_pkAuraInstance = NULL;

namespace
{
	std::map<DWORD, std::string> s_kAuraEffects;	// vnum -> .mse
}

bool CInstanceBase::RegisterAuraEffect(DWORD dwVnum, const char* c_szFileName)
{
	if (!dwVnum)
		return false;
	if (!c_szFileName || !*c_szFileName)
	{
		s_kAuraEffects.erase(dwVnum);
		return true;
	}
	std::string strFile(c_szFileName);
	std::replace(strFile.begin(), strFile.end(), '\\', '/');
	s_kAuraEffects[dwVnum] = strFile;
	return true;
}

void CInstanceBase::__AttachAuraEffect()
{
	if (m_dwAuraEffect)
	{
		__DetachEffect(m_dwAuraEffect);
		m_dwAuraEffect = 0;
	}
	if (!m_dwAuraVnum || !IsPC() || IsPoly() || __IsShapeAnimalWear())
		return;
	std::map<DWORD, std::string>::const_iterator it = s_kAuraEffects.find(m_dwAuraVnum);
	if (it == s_kAuraEffects.end())
		return;
	const char* c_szFile = it->second.c_str();
	if (!CEffectManager::Instance().RegisterEffect(c_szFile, false, false))
		return;
	m_dwAuraEffect = m_GraphicThingInstance.AttachEffectByName(0, "Bip01 Spine2", c_szFile);
}

void CInstanceBase::SetAura(DWORD dwVnum)
{
	if (m_dwAuraVnum == dwVnum && (m_dwAuraEffect || !dwVnum))
		return;
	m_dwAuraVnum = dwVnum;
	__AttachAuraEffect();
}

bool CNetworkActorManager::SetActorAura(DWORD dwVID, DWORD dwVnum)
{
	SNetworkActorData* pkData = __FindActorData(dwVID);
	if (pkData)
		pkData->m_dwAura = dwVnum;
	CInstanceBase* pkInst = CPythonCharacterManager::Instance().GetInstancePtr(dwVID);
	if (pkInst)
		pkInst->SetAura(dwVnum);
	return pkData || pkInst;
}

PyObject* chrmgrRegisterAuraEffect(PyObject* poSelf, PyObject* poArgs)
{
	int iVnum;
	if (!PyTuple_GetInteger(poArgs, 0, &iVnum))
		return Py_BadArgument();
	char* szFileName;
	if (!PyTuple_GetString(poArgs, 1, &szFileName))
		return Py_BadArgument();
	return Py_BuildValue("i", CInstanceBase::RegisterAuraEffect((DWORD) iVnum, szFileName) ? 1 : 0);
}

PyObject* chrmgrSetAura(PyObject* poSelf, PyObject* poArgs)
{
	int iVID;
	if (!PyTuple_GetInteger(poArgs, 0, &iVID))
		return Py_BadArgument();
	int iVnum;
	if (!PyTuple_GetInteger(poArgs, 1, &iVnum))
		return Py_BadArgument();
	if (iVnum < 0)
		iVnum = 0;
	if (CNetworkActorManager::ms_pkAuraInstance)
		return Py_BuildValue("i", CNetworkActorManager::ms_pkAuraInstance->SetActorAura((DWORD) iVID, (DWORD) iVnum) ? 1 : 0);
	CInstanceBase* pkInst = CPythonCharacterManager::Instance().GetInstancePtr(iVID);
	if (!pkInst)
		return Py_BuildValue("i", 0);
	pkInst->SetAura((DWORD) iVnum);
	return Py_BuildValue("i", 1);
}

PyObject* chrmgrGetAura(PyObject* poSelf, PyObject* poArgs)
{
	int iVID;
	if (!PyTuple_GetInteger(poArgs, 0, &iVID))
		return Py_BadArgument();
	CInstanceBase* pkInst = CPythonCharacterManager::Instance().GetInstancePtr(iVID);
	return Py_BuildValue("i", pkInst ? (int) pkInst->GetAura() : 0);
}

#endif // ENABLE_MT2009_AURA
