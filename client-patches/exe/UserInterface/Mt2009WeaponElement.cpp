/**
* MT2009_PLUS_WEAPON_ELEMENT_V1 - Zaczarowanie Zywiolu Broni in the Yohara 3.x exe (server-patches/zywiolbroni; based on
* the "[System] Elemental Spell" package by WorldArd - its CInstanceBase::AttachElementEffect, rewritten). Only the
* element's effect on the weapon is the exe's: the scrolls, the windows and the tooltips are root's (welem.py,
* uiweaponelement.py), and the server tells which characters show it with a chat command ("WELEMFX <vid> <type>",
* sent when a character comes into view and when its weapon / enchant changes) instead of the package's byte in the
* character packets - no packet changes, an old exe simply draws nothing.
*
* The server sends a type only for an enchant +3 on a weapon with its refine "stars" (the wiki's level rules and the
* transmutation rule); the exe draws it only while the weapon shows its refine effect too (m_swordRefineEffectRight /
* Left - __GetRefinedEffect just attached them in SetWeapon), so both always appear together: a weapon costume, a
* polymorph or an animal wear (no refine effect) shows none.
*
* Python:
*   chrmgr.RegisterWeaponElementEffect(type, kind, file)  the effect of element <type> (1 Blyskawica, 2 Ogien, 3 Lod,
*                                           4 Wiatr, 5 Ziemia, 6 Mrok) on a weapon of <kind>: 0 sword / two-handed
*                                           ("element0x_*.mse"), 1 fan ("_f"), 2 bow ("_b", left hand), 3 dagger (both
*                                           hands) / bell ("_s"), 4 claw (both hands, "_w") - as the refine effects
*                                           (PythonPlayerSettingsModule.cpp: sword_7*.mse); "" removes it
*   chrmgr.SetWeaponElement(vid, type)      an actor's element (0: none); kept in the actor's network data, so the
*                                           instance made again (it comes into sight, a mount, an armour shape) gets
*                                           it back; 1 when the actor is known
*   chrmgr.GetWeaponElement(vid)            the element of an actor's instance (0: none / no instance)
* Arrows and quivers never get one (the package gave an arrow the dagger's effect).
*/
#include "StdAfx.h"
#include "InstanceBase.h"
#include "NetworkActorManager.h"
#include "PythonCharacterManager.h"
#include "../EffectLib/EffectManager.h"
#include "../GameLib/ItemManager.h"

#include <algorithm>
#include <string>

#if defined(ENABLE_MT2009_WEAPON_ELEMENT) && defined(ENABLE_MT2009_AURA)

namespace
{
	enum
	{
		WELEM_TYPE_MAX = 6,
		WELEM_KIND_SWORD = 0,	// one-handed sword, two-handed
		WELEM_KIND_FAN,
		WELEM_KIND_BOW,			// on the left hand
		WELEM_KIND_SMALL,		// dagger (both hands), bell
		WELEM_KIND_CLAW,		// both hands
		WELEM_KIND_MAX,
	};

	std::string s_astrWeaponElementEffects[WELEM_TYPE_MAX + 1][WELEM_KIND_MAX];	// [type][kind] -> .mse

	// the kind of a weapon (-1: no element effect) and whether it has a second one in the left hand
	int WeaponElementKind(CItemData* pItem, bool& bLeftToo, bool& bLeftOnly)
	{
		bLeftToo = bLeftOnly = false;
		if (!pItem || pItem->GetType() != ITEM_WEAPON)
			return -1;
		switch (pItem->GetSubType())
		{
			case WEAPON_DAGGER:
				bLeftToo = true;
				return WELEM_KIND_SMALL;
			case WEAPON_BELL:
				return WELEM_KIND_SMALL;
			case WEAPON_FAN:
				return WELEM_KIND_FAN;
			case WEAPON_BOW:
				bLeftOnly = true;
				return WELEM_KIND_BOW;
#ifdef ENABLE_WOLFMAN_CHARACTER
			case WEAPON_CLAW:
				bLeftToo = true;
				return WELEM_KIND_CLAW;
#endif
			case WEAPON_SWORD:
			case WEAPON_TWO_HANDED:
				return WELEM_KIND_SWORD;
			default:	// arrows, quivers, a mount spear: never
				return -1;
		}
	}
}

bool CInstanceBase::RegisterWeaponElementEffect(DWORD dwType, DWORD dwKind, const char* c_szFileName)
{
	if (dwType < 1 || dwType > WELEM_TYPE_MAX || dwKind >= WELEM_KIND_MAX)
		return false;
	std::string strFile(c_szFileName ? c_szFileName : "");
	std::replace(strFile.begin(), strFile.end(), '\\', '/');
	s_astrWeaponElementEffects[dwType][dwKind] = strFile;
	return true;
}

void CInstanceBase::__ClearWeaponElementEffect()
{
	for (int i = 0; i < 2; ++i)
	{
		if (m_dwWeaponElementEffect[i])
		{
			__DetachEffect(m_dwWeaponElementEffect[i]);
			m_dwWeaponElementEffect[i] = 0;
		}
	}
}

void CInstanceBase::__AttachWeaponElementEffect()
{
	__ClearWeaponElementEffect();
	if (!m_dwWeaponElement || m_dwWeaponElement > WELEM_TYPE_MAX || !IsPC() || IsPoly() || __IsShapeAnimalWear() ||
			IsInvisibility())
		return;
	// only beside the weapon's refine "stars" (SetWeapon attached them just before)
	if (!m_swordRefineEffectRight && !m_swordRefineEffectLeft)
		return;
	CItemData* pItem = NULL;
	if (!CItemManager::Instance().GetItemDataPointer(GetPart(CRaceData::EQUIP_PART_WEAPON), &pItem) || !pItem)
		return;
	bool bLeftToo, bLeftOnly;
	const int iKind = WeaponElementKind(pItem, bLeftToo, bLeftOnly);
	if (iKind < 0)
		return;
	const std::string& rstrFile = s_astrWeaponElementEffects[m_dwWeaponElement][iKind];
	if (rstrFile.empty())
		return;
	const char* c_szFile = rstrFile.c_str();
	if (!CEffectManager::Instance().RegisterEffect(c_szFile, false, false))
		return;
	const char* c_szBone = NULL;
	if (!bLeftOnly && m_GraphicThingInstance.GetAttachingBoneName(CRaceData::EQUIP_PART_WEAPON, &c_szBone) && c_szBone)
		m_dwWeaponElementEffect[0] = m_GraphicThingInstance.AttachEffectByName(0, c_szBone, c_szFile);
	c_szBone = NULL;
	if ((bLeftToo || bLeftOnly) && m_GraphicThingInstance.GetAttachingBoneName(CRaceData::EQUIP_PART_WEAPON_LEFT, &c_szBone) && c_szBone)
		m_dwWeaponElementEffect[1] = m_GraphicThingInstance.AttachEffectByName(0, c_szBone, c_szFile);
}

void CInstanceBase::SetWeaponElement(DWORD dwType)
{
	if (dwType > WELEM_TYPE_MAX)
		dwType = 0;
	if (m_dwWeaponElement == dwType && (m_dwWeaponElementEffect[0] || m_dwWeaponElementEffect[1] || !dwType))
		return;
	m_dwWeaponElement = dwType;
	__AttachWeaponElementEffect();
}

bool CNetworkActorManager::SetActorWeaponElement(DWORD dwVID, DWORD dwType)
{
	SNetworkActorData* pkData = __FindActorData(dwVID);
	if (pkData)
		pkData->m_dwWeaponElement = dwType;
	CInstanceBase* pkInst = CPythonCharacterManager::Instance().GetInstancePtr(dwVID);
	if (pkInst)
		pkInst->SetWeaponElement(dwType);
	return pkData || pkInst;
}

PyObject* chrmgrRegisterWeaponElementEffect(PyObject* poSelf, PyObject* poArgs)
{
	int iType;
	if (!PyTuple_GetInteger(poArgs, 0, &iType))
		return Py_BadArgument();
	int iKind;
	if (!PyTuple_GetInteger(poArgs, 1, &iKind))
		return Py_BadArgument();
	char* szFileName;
	if (!PyTuple_GetString(poArgs, 2, &szFileName))
		return Py_BadArgument();
	if (iType < 0 || iKind < 0)
		return Py_BuildValue("i", 0);
	return Py_BuildValue("i", CInstanceBase::RegisterWeaponElementEffect((DWORD) iType, (DWORD) iKind, szFileName) ? 1 : 0);
}

PyObject* chrmgrSetWeaponElement(PyObject* poSelf, PyObject* poArgs)
{
	int iVID;
	if (!PyTuple_GetInteger(poArgs, 0, &iVID))
		return Py_BadArgument();
	int iType;
	if (!PyTuple_GetInteger(poArgs, 1, &iType))
		return Py_BadArgument();
	if (iType < 0 || iType > WELEM_TYPE_MAX)
		iType = 0;
	if (CNetworkActorManager::ms_pkAuraInstance)
		return Py_BuildValue("i", CNetworkActorManager::ms_pkAuraInstance->SetActorWeaponElement((DWORD) iVID, (DWORD) iType) ? 1 : 0);
	CInstanceBase* pkInst = CPythonCharacterManager::Instance().GetInstancePtr(iVID);
	if (!pkInst)
		return Py_BuildValue("i", 0);
	pkInst->SetWeaponElement((DWORD) iType);
	return Py_BuildValue("i", 1);
}

PyObject* chrmgrGetWeaponElement(PyObject* poSelf, PyObject* poArgs)
{
	int iVID;
	if (!PyTuple_GetInteger(poArgs, 0, &iVID))
		return Py_BadArgument();
	CInstanceBase* pkInst = CPythonCharacterManager::Instance().GetInstancePtr(iVID);
	return Py_BuildValue("i", pkInst ? (int) pkInst->GetWeaponElement() : 0);
}

#endif // ENABLE_MT2009_WEAPON_ELEMENT && ENABLE_MT2009_AURA
