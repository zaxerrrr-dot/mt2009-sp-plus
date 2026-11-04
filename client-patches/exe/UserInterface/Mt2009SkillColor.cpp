/**
* MT2009_PLUS_SKILL_COLOR_V1 - Kolor umiejetnosci in the Yohara 3.x exe (the owner's package "SKILL_COLOR_SYSTEM by OSWAP
* (FULL)", V1.0.1.4 - rebuilt; server-patches/skillcolor/README.md has the whole picture).
*
* A character's colour of a skill: five layers (0 = the effect's own colour, else 0xFFrrggbb) - layer n colours the n-th
* particle system of the skill's effect, the 5th also every later one. Each particle keeps its alpha and its brightness
* and takes the colour's hue (CParticleInstance::Mt2009SkillColorTint) - the instance's colour, never the loaded .mse
* (the package rewrote the shared effect data at every instance and so needed a copy of every effect per player name,
* GetCaseCRC32(name + file)). What is coloured:
*   - every effect, effect on the target and flying object (and its hit) of the skill's motions: the skill's motion
*     indexes of every grade (CPythonSkill GradeData / wMotionIndex / wMotionIndexForMe) -> CActorInstance's map, read
*     by the motion events (ActorInstanceMotionEvent.cpp) - the same for the player himself and for everyone he sees
*     (the server sends a viewer the colours after the character's add packet);
*   - Burzowy Szpon's jumps and Ognisty Duch's shots (the server's fly packets, CFlyingManager::CreateIndexedFly);
*   - the affect effects: the self buffs (Berserk 3, Aura Miecza 4 - the weapon's glow, Silne Cialo 19, Krycie Sie 34,
*     Bezszelestny Chod 49, Czarowane Ostrze 63, Strach 64, Czarowana Zbroja 65, Ognisty Duch 78, Mroczna Ochrona 79)
*     in the character's own colour, the shaman buffs (94 95 96 110 111) in the colour of whoever cast them (the
*     server's SKILL_COLOR_TYPE_BUFF - a Buffi's: its owner's colour of the Buffi skill). An effect already on is put
*     on again in the new colour.
* Not the riposty / dopalacze (passive) nor the Buffi skills 164-167 themselves (no motion on the owner: the Buffi casts
* them, its own colours come from the server as the shaman skills').
*
* Packets: GC 59 HEADER_GC_SKILL_COLOR (28 B, CNetworkActorManager keeps them per VID: an instance made again - into
* sight, a mount - gets them back), CG 56 HEADER_CG_SKILL_COLOR (23 B, + the sequence byte).
*
* Python:
*   player.SetSkillColor(vnum, c1, c2, c3, c4, c5)  the window's choice to the server: each -1 (the effect's own) or
*                                                   0xRRGGBB; the server answers with GC 59 (the window reads it back)
*   player.GetSkillColor(vnum)                      the main character's five colours of a skill, the same -1 / 0xRRGGBB
*   app.ENABLE_SKILL_COLOR_SYSTEM = 1, app.MT2009_SKILL_COLOR_EXE = 1 (constinfo.py: client 1.3.2)
*/
#include "StdAfx.h"
#include "InstanceBase.h"
#include "NetworkActorManager.h"
#include "PythonCharacterManager.h"
#include "PythonNetworkStream.h"
#include "PythonPlayer.h"
#include "PythonSkill.h"
#include "../GameLib/RaceMotionData.h"

#ifdef ENABLE_MT2009_SKILL_COLOR

namespace
{
	inline DWORD Key(BYTE bType, WORD wVnum)
	{
		return ((DWORD) bType << 16) | wVnum;
	}

	bool IsDefault(const DWORD * c)
	{
		for (int i = 0; i < SKILL_COLOR_LAYERS; ++i)
			if (c[i])
				return false;
		return true;
	}

	// an affect effect -> the skill whose colour it wears (type, vnum); false: none
	bool AffectSkill(UINT eAffect, BYTE & bType, WORD & wVnum)
	{
		bType = SKILL_COLOR_TYPE_OWN;
		switch (eAffect)
		{
			case AFF_SKILL_BERSERK:			wVnum = 3; return true;		// Berserk
			case AFF_SKILL_STRONG_BODY:
			case AFF_SKILL_STRONG_BODY_WITH_FALL:	wVnum = 19; return true;	// Silne Cialo
			case AFF_SKILL_STEALTH:			wVnum = 34; return true;	// Krycie Sie
			case AFF_SKILL_FEATHER_WALK:		wVnum = 49; return true;	// Bezszelestny Chod
			case AFF_SKILL_ENCHANTED_BLADE:	wVnum = 63; return true;	// Czarowane Ostrze
			case AFF_SKILL_TERROR:			wVnum = 64; return true;	// Strach
			case AFF_SKILL_ENCHANTED_ARMOR:	wVnum = 65; return true;	// Czarowana Zbroja
			case AFF_SKILL_FLAME_SPIRIT:		wVnum = 78; return true;	// Ognisty Duch
			case AFF_SKILL_MANASHIELD:		wVnum = 79; return true;	// Mroczna Ochrona
		}
		bType = SKILL_COLOR_TYPE_BUFF;
		switch (eAffect)
		{
			case AFF_SKILL_BLESSING:			wVnum = 94; return true;	// Blogoslawienstwo
			case AFF_SKILL_REFLECT:			wVnum = 95; return true;	// Odbicie
			case AFF_SKILL_DRAGON_HELP:		wVnum = 96; return true;	// Pomoc Smoka
			case AFF_SKILL_SWIFTNESS:		wVnum = 110; return true;	// Zwinnosc
			case AFF_SKILL_ATTACK_UP:		wVnum = 111; return true;	// Zwiekszenie Ataku
		}
		return false;
	}
}

// ---------------------------------------------------------------------------------------------------- CInstanceBase

void CInstanceBase::Mt2009SetSkillColor(BYTE bType, WORD wSkillVnum, const DWORD * c_pdwColor)
{
	const DWORD dwKey = Key(bType, wSkillVnum);
	if (!c_pdwColor || IsDefault(c_pdwColor))
	{
		if (!m_kMt2009SkillColor.erase(dwKey))
			return;
	}
	else
	{
		CActorInstance::SMt2009SkillColor & r = m_kMt2009SkillColor[dwKey];
		if (!memcmp(r.adwColor, c_pdwColor, sizeof(r.adwColor)))
			return;
		memcpy(r.adwColor, c_pdwColor, sizeof(r.adwColor));
	}

	if (SKILL_COLOR_TYPE_OWN == bType)
		__Mt2009RefreshSkillColorMotions();

	// an effect of this skill already on: on again, in the new colour
	for (UINT eAffect = 0; eAffect < AFF_BITS_MAX; ++eAffect)
	{
		BYTE bAffType;
		WORD wAffVnum;
		if (!AffectSkill(eAffect, bAffType, wAffVnum) || bAffType != bType || wAffVnum != wSkillVnum)
			continue;
		if (!m_adwCRCAffectEffect[eAffect])
			continue;
		__DetachEffect(m_adwCRCAffectEffect[eAffect]);
		m_adwCRCAffectEffect[eAffect] = __AttachEffect(EFFECT_AFFECT + eAffect);
	}
	if (SKILL_COLOR_TYPE_OWN == bType && 4 == wSkillVnum && m_kWarrior.m_dwGeomgyeongEffect)
		__Warrior_SetGeomgyeongAffect(true);	// Aura Miecza: the weapon's glow again
}

const DWORD * CInstanceBase::Mt2009GetSkillColor(BYTE bType, WORD wSkillVnum) const
{
	std::map<DWORD, CActorInstance::SMt2009SkillColor>::const_iterator it = m_kMt2009SkillColor.find(Key(bType, wSkillVnum));
	return it == m_kMt2009SkillColor.end() ? NULL : it->second.adwColor;
}

// the server's fly packet (Burzowy Szpon's next target, Ognisty Duch's shot) from this character
const DWORD * CInstanceBase::Mt2009GetSkillColorOfFly(DWORD dwFlyIndex) const
{
	if (FLY_CHAIN_LIGHTNING == dwFlyIndex)
		return Mt2009GetSkillColor(SKILL_COLOR_TYPE_OWN, 108);
	if (FLY_SKILL_FLAME_SPIRIT == dwFlyIndex)
		return Mt2009GetSkillColor(SKILL_COLOR_TYPE_OWN, 78);
	return NULL;
}

// __AttachEffect: the colour of an affect effect / Aura Miecza's weapon glow (NULL: its own)
const DWORD * CInstanceBase::__Mt2009SkillColorOfEffect(UINT eEftType) const
{
	if (m_kMt2009SkillColor.empty())
		return NULL;
	if (EFFECT_WEAPON + WEAPON_ONEHAND == eEftType || EFFECT_WEAPON + WEAPON_TWOHAND == eEftType)
		return Mt2009GetSkillColor(SKILL_COLOR_TYPE_OWN, 4);
	if (eEftType < EFFECT_AFFECT || eEftType >= EFFECT_AFFECT_END)
		return NULL;
	BYTE bType;
	WORD wVnum;
	if (!AffectSkill(eEftType - EFFECT_AFFECT, bType, wVnum))
		return NULL;
	return Mt2009GetSkillColor(bType, wVnum);
}

// the actor's motion -> colour map from the own colours: every motion index of every grade of each skill (the Buffi
// skills 164-167 never move the owner - the Buffi shows them, coloured as the shaman skills by the server)
void CInstanceBase::__Mt2009RefreshSkillColorMotions()
{
	m_GraphicThingInstance.Mt2009ClearSkillColors();
	for (std::map<DWORD, CActorInstance::SMt2009SkillColor>::const_iterator it = m_kMt2009SkillColor.begin(); it != m_kMt2009SkillColor.end(); ++it)
	{
		if ((it->first >> 16) != SKILL_COLOR_TYPE_OWN)
			continue;
		const WORD wVnum = (WORD) (it->first & 0xffff);
		if (wVnum >= 164 && wVnum <= 167)
			continue;
		CPythonSkill::TSkillData * pSkillData;
		if (!CPythonSkill::Instance().GetSkillData(wVnum, &pSkillData))
			continue;
		if (pSkillData->wMotionIndex)
			m_GraphicThingInstance.Mt2009SetSkillColorOfMotion(pSkillData->wMotionIndex, it->second.adwColor);
		if (pSkillData->wMotionIndexForMe)
			m_GraphicThingInstance.Mt2009SetSkillColorOfMotion(pSkillData->wMotionIndexForMe, it->second.adwColor);
		for (int g = 0; g < CPythonSkill::SKILL_EFFECT_COUNT; ++g)
			if (pSkillData->GradeData[g].wMotionIndex)
				m_GraphicThingInstance.Mt2009SetSkillColorOfMotion(pSkillData->GradeData[g].wMotionIndex, it->second.adwColor);
	}
}

// --------------------------------------------------------------------------------------------- CNetworkActorManager

void CNetworkActorManager::Mt2009SetSkillColor(DWORD dwVID, BYTE bType, WORD wSkillVnum, const DWORD * c_pdwColor)
{
	if (m_kNetActorDict.find(dwVID) == m_kNetActorDict.end() && dwVID != m_dwMainVID)
		return;	// not an actor of ours (yet) - the server sends it again with its add packet
	std::map<DWORD, CActorInstance::SMt2009SkillColor> & rkSet = m_kMt2009SkillColor[dwVID];
	if (IsDefault(c_pdwColor))
		rkSet.erase(Key(bType, wSkillVnum));
	else
		memcpy(rkSet[Key(bType, wSkillVnum)].adwColor, c_pdwColor, sizeof(DWORD) * SKILL_COLOR_LAYERS);
	if (rkSet.empty())
		m_kMt2009SkillColor.erase(dwVID);
	CInstanceBase * pkInst = CPythonCharacterManager::Instance().GetInstancePtr(dwVID);
	if (pkInst)
		pkInst->Mt2009SetSkillColor(bType, wSkillVnum, c_pdwColor);
}

// a new instance of the actor (into sight, a mount, a shape): its colours again
void CNetworkActorManager::__Mt2009ApplySkillColors(DWORD dwVID, CInstanceBase * pkInst)
{
	std::map<DWORD, std::map<DWORD, CActorInstance::SMt2009SkillColor> >::const_iterator f = m_kMt2009SkillColor.find(dwVID);
	if (!pkInst || f == m_kMt2009SkillColor.end())
		return;
	for (std::map<DWORD, CActorInstance::SMt2009SkillColor>::const_iterator it = f->second.begin(); it != f->second.end(); ++it)
		pkInst->Mt2009SetSkillColor((BYTE) (it->first >> 16), (WORD) (it->first & 0xffff), it->second.adwColor);
}

// ---------------------------------------------------------------------------------------------- CPythonNetworkStream

bool CPythonNetworkStream::RecvSkillColorPacket()
{
	TPacketGCSkillColor kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;
	for (int i = 0; i < SKILL_COLOR_LAYERS; ++i)
		if (kPacket.adwColor[i] && (kPacket.adwColor[i] >> 24) != 0xff)
			kPacket.adwColor[i] = 0;
	m_rokNetActorMgr->Mt2009SetSkillColor(kPacket.dwVID, kPacket.bType, kPacket.wSkillVnum, kPacket.adwColor);
	return true;
}

bool CPythonNetworkStream::SendSkillColorPacket(WORD wSkillVnum, const DWORD * c_pdwColor)
{
	if (!__CanActMainInstance())
		return true;

	TPacketCGSkillColor kPacket;
	kPacket.bHeader = HEADER_CG_SKILL_COLOR;
	kPacket.wSkillVnum = wSkillVnum;
	memcpy(kPacket.adwColor, c_pdwColor, sizeof(kPacket.adwColor));
	if (!Send(sizeof(kPacket), &kPacket))
	{
		Tracef("SendSkillColorPacket Error\n");
		return false;
	}
	return SendSequence();
}

// -------------------------------------------------------------------------------------------------------- python

// player.SetSkillColor(vnum, c1, c2, c3, c4, c5): -1 = the effect's own, else 0xRRGGBB
PyObject * playerSetSkillColor(PyObject * poSelf, PyObject * poArgs)
{
	int iVnum;
	if (!PyTuple_GetInteger(poArgs, 0, &iVnum) || iVnum <= 0 || iVnum > 0xffff)
		return Py_BuildException();
	DWORD adwColor[SKILL_COLOR_LAYERS];
	for (int i = 0; i < SKILL_COLOR_LAYERS; ++i)
	{
		int iColor;
		if (!PyTuple_GetInteger(poArgs, 1 + i, &iColor) || iColor < -1 || iColor > 0xffffff)
			return Py_BuildException();
		adwColor[i] = iColor < 0 ? 0 : (0xff000000 | (DWORD) iColor);
	}
	CPythonNetworkStream::Instance().SendSkillColorPacket((WORD) iVnum, adwColor);
	return Py_BuildNone();
}

// player.GetSkillColor(vnum) -> (c1, c2, c3, c4, c5): -1 = the effect's own, else 0xRRGGBB
PyObject * playerGetSkillColor(PyObject * poSelf, PyObject * poArgs)
{
	int iVnum;
	if (!PyTuple_GetInteger(poArgs, 0, &iVnum))
		return Py_BuildException();
	int aiColor[SKILL_COLOR_LAYERS] = { -1, -1, -1, -1, -1 };
	CInstanceBase * pkMain = CPythonPlayer::Instance().NEW_GetMainActorPtr();
	const DWORD * c = (pkMain && iVnum > 0 && iVnum <= 0xffff) ? pkMain->Mt2009GetSkillColor(SKILL_COLOR_TYPE_OWN, (WORD) iVnum) : NULL;
	for (int i = 0; c && i < SKILL_COLOR_LAYERS; ++i)
		aiColor[i] = c[i] ? (int) (c[i] & 0xffffff) : -1;
	return Py_BuildValue("(iiiii)", aiColor[0], aiColor[1], aiColor[2], aiColor[3], aiColor[4]);
}

// UserInterface.cpp, after the modules (as Mt2009Champion_RegisterPython): player.SetSkillColor / GetSkillColor and the
// app constants root checks
void Mt2009SkillColor_RegisterPython()
{
	static PyMethodDef s_playerMethods[] =
	{
		{ "SetSkillColor",	playerSetSkillColor,	METH_VARARGS },
		{ "GetSkillColor",	playerGetSkillColor,	METH_VARARGS },
		{ NULL, NULL, 0 },
	};
	PyObject * poPlayer = PyImport_AddModule("player");	// borrowed
	if (poPlayer)
		for (PyMethodDef * p = s_playerMethods; p->ml_name; ++p)
			PyModule_AddObject(poPlayer, p->ml_name, PyCFunction_New(p, NULL));
	PyObject * poApp = PyImport_AddModule("app");	// borrowed
	if (poApp)
	{
		PyModule_AddIntConstant(poApp, "ENABLE_SKILL_COLOR_SYSTEM", 1);
		// root's constinfo.py says client 1.3.2 only with this exe: the auth core (M2_CLIENT_MIN_VERSION 1010302) refuses
		// an older one with "UPDATE" before a GC 59 it cannot read reaches it
		PyModule_AddIntConstant(poApp, "MT2009_SKILL_COLOR_EXE", 1);
	}
}

#endif
