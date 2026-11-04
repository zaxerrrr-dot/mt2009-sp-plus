/*
* MT2009_PLUS_GROWTH_PET_V1 - System zwierzat domowych (the official growth pet) in the Yohara 3.x exe.
*
* Ported from the Anka2 client sources (ENABLE_GROWTH_PET_SYSTEM / ENABLE_UPBRINGING_PET_CONQUEROR_LEVEL) to the contract
* shared with the server (server-patches/pety) and root (SPEC.md):
*   - GC 224-236 (Packet.h; NOT Anka2's 173-184), CG 122-134, all fixed size;
*   - the pets of the owner (GC 225) and of the exchange partner (GC 226) per pet id in CPythonPlayer;
*   - feed / revive positions are TItemPos (any inventory window), the champion points, GC 236 / CG 134 the potential slots;
*   - GC 235 PET_LOOK: a growth pet's model scale for every viewer (kept per VID in CNetworkActorManager, applied to each new
*     instance of it). Anka2's own scale (SetPetLevel: level * 0.2) and its IsGrowthPet char type are NOT ported - the server
*     spawns the pet as an ordinary pet NPC and sends its scale with GC 235.
*   - pet_skill.txt (locale/<language>/pet_skill.txt, tab separated: id, name, icon, PASSIVE|AUTO, description, cooldown).
*
* Python (registered from UserInterface.cpp after the modules):
*   net:    SendPetHatchingPacket(name, window, cell), SendPetHatchingWindowPacket(state), SendPetNameChangeWindowPacket(state),
*           SendPetWindowType(type), SendPetFeedPacket(index, [(window, cell, count), ...]), SendPetAttrDetermine(window, cell),
*           SendPetAttrChange(sealWindow, sealCell, itemWindow, itemCell), SendPetRevive(sealWindow, sealCell,
*           [(window, cell, count), ...]), SendPetLearnSkill(slot, window, cell), SendPetSkillUpgradeRequest(slot),
*           SendPetDeleteSkill(slot, window, cell), SendPetDeleteAllSkill(window, cell),
*           SendPetNameChangePacket(name, scrollWindow, scrollCell, sealWindow, sealCell), SendPetPotential(action, slot,
*           window, cell), CheckUsePetItem()
*   player: GetPetItem(petId) -> (vnum, level, evolution, hp, def, sp, lifeEnd, maxLife, birthday, exp, itemExp, nextExp,
*           championLevel, championExp, championItemExp, championNextExp, res, blockPen, precision, type, skillSlots, name),
*           GetPetSkill(petId, slot) -> (skill, level, cooltime), GetPetSkillByIndex(petId, slot, skillLevel) ->
*           (activatePct, valueTenths, durationTenths), GetPetPotential(petId, slot) -> (eggVnum, skill, level, endTime),
*           GetPetPotentialSlots(petId), GetPetLifeTime(petId) -> (lifeEnd, maxLife), GetPetExpPoints(petId) ->
*           (exp, mobExpNeeded, itemExp, itemExpNeeded), GetPetChampionExpPoints(petId) (the same for the champion level),
*           IsPetExchange(petId), GetActivePetItemId(), GetActivePetItemVNum(), GetPetItemVNumInBag(petId),
*           SetOpenPetHatchingWindow / SetOpenPetNameChangeWindow / SetOpenPetFeedWindow(bool),
*           IsOpenPetHatchingWindow / IsOpenPetFeedWindow / IsOpenPetNameChangeWindow(), the PET_* / FEED_* /
*           POINT_UPBRINGING_* constants
*   skill:  GetPetSkillInfo(id) -> (name, description, type, cooldown), GetPetSkillIconImage(id), GetPetSkillIconPath(id),
*           PET_SKILL_USE_TYPE_NONE / PASSIVE / AUTO / MAX
*   item:   ITEM_TYPE_GROWTH_PET (= ITEM_PET 37), PET_EGG .. PET_PRIMIUM_FEEDSTUFF, EGG_USE_*, PET_EGG_USE_*, NAME_CHANGE_USE_*,
*           PET_NAME_MIN_SIZE / PET_NAME_MAX_SIZE, PET_HATCHING_MONEY, PET_ATTR_CHANGE_ITEMVNUM, ITEM_ANTIFLAG_PETFEED (0)
*   app:    ENABLE_GROWTH_PET_SYSTEM, ENABLE_UPBRINGING_PET_CONQUEROR_LEVEL, MT2009_GROWTH_PET_EXE (root constinfo.py)
* The game window's callbacks: PetHatchingWindowCommand(i), PetFeedReuslt(i) [sic], PetReviveResult(i),
* PetWindowTypeResult(i), PetNameChangeWindowCommand(i), PetAffectShowerRefresh(), PetAttrDetermineResult(type),
* PetAttrChangeResult(cell, type), PetEvolveResult(i), PetPotentialResult(i), PetPotentialRefresh(petId),
* PetInfoRefresh(petId) (after GC 225/226 / 227 / 229 / 230 success / 233 / 236).
*/
#include "StdAfx.h"

#ifdef ENABLE_GROWTH_PET_SYSTEM

#include "Packet.h"
#include "PythonNetworkStream.h"
#include "PythonPlayer.h"
#include "PythonCharacterManager.h"
#include "NetworkActorManager.h"
#include "InstanceBase.h"
#include "../EterPack/EterPackManager.h"
#include "../GameLib/RaceManager.h"
#include "../GameLib/RaceData.h"

namespace
{
	enum
	{
		PET_SKILL_USE_TYPE_NONE,
		PET_SKILL_USE_TYPE_PASSIVE,
		PET_SKILL_USE_TYPE_AUTO,
		PET_SKILL_USE_TYPE_MAX,
	};

	enum
	{
		PET_SKILL_TOKEN_INDEX,
		PET_SKILL_TOKEN_NAME,
		PET_SKILL_TOKEN_ICON_NAME,
		PET_SKILL_TOKEN_TYPE,
		PET_SKILL_TOKEN_DESCRIPTION,
		PET_SKILL_TOKEN_COOLDOWN,
		PET_SKILL_TOKEN_MAX_NUM,
	};

	// Anka2's CItemData / GameType.h values root's growth pet windows use
	enum
	{
		EGG_USE_SUCCESS = 0,
		EGG_USE_FAILED_BECAUSE_NAME = 1,
		EGG_USE_FAILED_TIMEOVER = 2,
		PET_EGG_USE_TRUE = 0,
		PET_EGG_USE_FAILED_BECAUSE_TRADING = 1,
		PET_EGG_USE_FAILED_BECAUSE_SHOP_OPEN = 2,
		PET_EGG_USE_FAILED_BECAUSE_MALL_OPEN = 3,
		PET_EGG_USE_FAILED_BECAUSE_SAFEBOX_OPEN = 4,
		NAME_CHANGE_USE_SUCCESS = 0,
		NAME_CHANGE_USE_FAILED_BECAUSE_NAME = 1,
		PET_ATTR_DETERMINE_ITEM = 55032,
		PET_ATTR_CHANGE_ITEM = 55033,
		LIFE_TIME_FLASH_MIN_TIME = 3600,
		SPECIAL_EVOL_MIN_AGE = 2592000,
	};

	struct SPetSkillProto
	{
		std::string		strName;
		std::string		strIconFileName;
		DWORD			dwType;
		std::string		strDescription;
		DWORD			dwCooldown;
		CGraphicImage*	pImage;
		bool			bImageLoaded;
	};
	std::map<DWORD, SPetSkillProto> s_kPetSkillProto;

	CPythonPlayer::SGrowthPet* FindPet(int iPetID)
	{
		return CPythonPlayer::Instance().GrowthPet_Find((DWORD) iPetID);
	}

	// one position of a feed / revive list: (window, cell, count) or [window, cell, count]
	bool SeqInt(PyObject* poSeq, Py_ssize_t i, long* plValue)
	{
		PyObject* poItem = PySequence_GetItem(poSeq, i);	// new reference
		if (!poItem)
			return false;
		const long lValue = PyInt_AsLong(poItem);
		Py_DECREF(poItem);
		if (lValue == -1 && PyErr_Occurred())
			return false;
		*plValue = lValue;
		return true;
	}

	// [(window, cell, count), ...] or Anka2's old form: [cell, ...] (+ [count, ...]) in the main inventory
	bool ParsePosList(PyObject* poList, PyObject* poCounts, size_t uMax, std::vector<std::pair<TItemPos, WORD> >& rkOut)
	{
		if (!poList || !PySequence_Check(poList))
			return false;
		const Py_ssize_t n = PySequence_Size(poList);
		for (Py_ssize_t i = 0; i < n && rkOut.size() < uMax; ++i)
		{
			PyObject* poItem = PySequence_GetItem(poList, i);	// new reference
			if (!poItem)
				return false;
			long lWindow = INVENTORY, lCell = 0, lCount = 0;
			bool bOk = true;
			if (PySequence_Check(poItem) && PySequence_Size(poItem) >= 3)
				bOk = SeqInt(poItem, 0, &lWindow) && SeqInt(poItem, 1, &lCell) && SeqInt(poItem, 2, &lCount);
			else
			{
				lCell = PyInt_AsLong(poItem);
				if (lCell == -1 && PyErr_Occurred())
					bOk = false;
				else if (poCounts && PySequence_Check(poCounts) && i < PySequence_Size(poCounts))
					bOk = SeqInt(poCounts, i, &lCount);
			}
			Py_DECREF(poItem);
			if (!bOk)
				return false;
			if (lWindow < 0 || lWindow > 0xff || lCell < 0 || lCell > 0xffff || lCount < 0)
				continue;
			rkOut.push_back(std::make_pair(TItemPos((BYTE) lWindow, (WORD) lCell), (WORD) std::min<long>(lCount, 0xffff)));
		}
		return true;
	}

	void CopyName(char* szDst, size_t uSize, const char* c_szSrc)
	{
		memset(szDst, 0, uSize);
		if (c_szSrc)
			strncpy(szDst, c_szSrc, uSize - 1);
	}
}

// ------------------------------------------------------------------------------------------------------- pet_skill.txt

bool Mt2009GrowthPet_LoadSkillTable(const char* c_szFileName)
{
	const VOID* pvData;
	CMappedFile kFile;
	if (!CEterPackManager::Instance().Get(kFile, c_szFileName, &pvData))
		return false;

	s_kPetSkillProto.clear();

	CMemoryTextFileLoader textFileLoader;
	textFileLoader.Bind(kFile.Size(), pvData);

	CTokenVector kTokens;
	for (DWORD i = 0; i < textFileLoader.GetLineCount(); ++i)
	{
		if (!textFileLoader.SplitLineByTab(i, &kTokens))
			continue;
		if (kTokens.empty() || kTokens[0].empty() || kTokens[0][0] == '#')
			continue;
		if (kTokens.size() < PET_SKILL_TOKEN_MAX_NUM)
		{
			TraceError("pet_skill.txt(%s) line %u: %u columns, %d needed", c_szFileName, i + 1, (UINT) kTokens.size(), (int) PET_SKILL_TOKEN_MAX_NUM);
			continue;
		}
		const DWORD dwIndex = (DWORD) atoi(kTokens[PET_SKILL_TOKEN_INDEX].c_str());
		if (!dwIndex)
		{
			TraceError("pet_skill.txt(%s) line %u: bad skill id", c_szFileName, i + 1);
			continue;
		}
		const std::string& c_rstrType = kTokens[PET_SKILL_TOKEN_TYPE];
		DWORD dwType = PET_SKILL_USE_TYPE_NONE;
		if (c_rstrType == "PASSIVE")
			dwType = PET_SKILL_USE_TYPE_PASSIVE;
		else if (c_rstrType == "AUTO")
			dwType = PET_SKILL_USE_TYPE_AUTO;
		else
			TraceError("pet_skill.txt(%s) line %u: type %s (PASSIVE / AUTO)", c_szFileName, i + 1, c_rstrType.c_str());

		SPetSkillProto& r = s_kPetSkillProto[dwIndex];
		r.strName = kTokens[PET_SKILL_TOKEN_NAME];
		r.strIconFileName = kTokens[PET_SKILL_TOKEN_ICON_NAME].empty() ? std::string() : "d:/ymir work/ui/skill/pet/" + kTokens[PET_SKILL_TOKEN_ICON_NAME] + ".sub";
		r.dwType = dwType;
		r.strDescription = kTokens[PET_SKILL_TOKEN_DESCRIPTION];
		r.dwCooldown = (DWORD) atoi(kTokens[PET_SKILL_TOKEN_COOLDOWN].c_str());
		r.pImage = NULL;
		r.bImageLoaded = false;
	}
	Tracenf("pet_skill.txt: %u growth pet skills from %s", (UINT) s_kPetSkillProto.size(), c_szFileName);
	return true;
}

// ------------------------------------------------------------------------------------------------------- CPythonPlayer

void CPythonPlayer::GrowthPet_Clear()
{
	m_kGrowthPet.clear();
	m_kGrowthPetPotential.clear();
	m_dwGrowthPetActiveID = 0;
	m_bGrowthPetHatchingWindow = false;
	m_bGrowthPetNameChangeWindow = false;
	m_bGrowthPetFeedWindow = false;
}

void CPythonPlayer::GrowthPet_Set(const TPacketGCPetSet& c_rkPacket, bool bExchange)
{
	SGrowthPet& r = m_kGrowthPet[c_rkPacket.dwID];
	SGrowthPet kOld = r;	// a pet known before: its skills' level tables (GC 233) stay while the skill is the same
	const bool bKnown = r.dwID == c_rkPacket.dwID && c_rkPacket.dwID != 0;

	char szName[GROWTH_PET_NAME_MAX + 1];
	memcpy(szName, c_rkPacket.szName, GROWTH_PET_NAME_MAX);
	szName[GROWTH_PET_NAME_MAX] = '\0';

	r.dwID = c_rkPacket.dwID;
	r.dwSummonItemVnum = c_rkPacket.dwSummonItemVnum;
	r.strName = szName;
	memcpy(r.adwPoints, c_rkPacket.dwPoints, sizeof(r.adwPoints));
	r.bExchange = bExchange;
	for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
	{
		SGrowthPetSkill& s = r.aSkill[i];
		const TGrowthPetSkillInfo& c_rkInfo = c_rkPacket.aSkill[i];
		if (!bKnown || kOld.aSkill[i].bSkill != c_rkInfo.bSkill)
		{
			memset(s.abFormula1, 0, sizeof(s.abFormula1));
			memset(s.awFormula2, 0, sizeof(s.awFormula2));
			memset(s.abFormula3, 0, sizeof(s.abFormula3));
		}
		s.bLocked = c_rkInfo.bLocked;
		s.bSkill = c_rkInfo.bSkill;
		s.bLevel = c_rkInfo.bLevel;
		s.dwCooltime = c_rkInfo.dwCooltime;
	}
}

CPythonPlayer::SGrowthPet* CPythonPlayer::GrowthPet_Find(DWORD dwID)
{
	std::map<DWORD, SGrowthPet>::iterator f = m_kGrowthPet.find(dwID);
	return f == m_kGrowthPet.end() ? NULL : &f->second;
}

void CPythonPlayer::GrowthPet_Delete(DWORD dwID)
{
	m_kGrowthPet.erase(dwID);
	m_kGrowthPetPotential.erase(dwID);
	if (m_dwGrowthPetActiveID == dwID)
		m_dwGrowthPetActiveID = 0;
}

void CPythonPlayer::GrowthPet_ClearExchange()
{
	for (std::map<DWORD, SGrowthPet>::iterator it = m_kGrowthPet.begin(); it != m_kGrowthPet.end(); )
	{
		if (it->second.bExchange)
		{
			m_kGrowthPetPotential.erase(it->first);
			m_kGrowthPet.erase(it++);
		}
		else
			++it;
	}
}

void CPythonPlayer::GrowthPet_SetPoint(DWORD dwID, BYTE bPoint, DWORD dwValue)
{
	SGrowthPet* p = GrowthPet_Find(dwID);
	if (p && bPoint < POINT_UPBRINGING_MAX_NUM)
		p->adwPoints[bPoint] = dwValue;
}

void CPythonPlayer::GrowthPet_SetSkills(DWORD dwID, const TGrowthPetSkillUpdate* c_pkSkill)
{
	SGrowthPet* p = GrowthPet_Find(dwID);
	if (!p)
		return;
	for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
	{
		SGrowthPetSkill& s = p->aSkill[i];
		s.bLocked = c_pkSkill[i].bLocked;
		s.bSkill = c_pkSkill[i].bSkill;
		s.bLevel = c_pkSkill[i].bLevel;
		s.dwCooltime = c_pkSkill[i].dwCooltime;
		memcpy(s.abFormula1, c_pkSkill[i].bSkillFormula1, sizeof(s.abFormula1));
		memcpy(s.awFormula2, c_pkSkill[i].wSkillFormula2, sizeof(s.awFormula2));
		memcpy(s.abFormula3, c_pkSkill[i].bSkillFormula3, sizeof(s.abFormula3));
	}
}

void CPythonPlayer::GrowthPet_SetSkillCooltime(DWORD dwID, BYTE bSlot, DWORD dwCooltime)
{
	SGrowthPet* p = GrowthPet_Find(dwID);
	if (p && bSlot < GROWTH_PET_SKILL_SLOTS)
		p->aSkill[bSlot].dwCooltime = dwCooltime;
}

void CPythonPlayer::GrowthPet_SetPotential(const TPacketGCPetPotential& c_rkPacket)
{
	SGrowthPetPotential& r = m_kGrowthPetPotential[c_rkPacket.dwID];
	r.bOpenSlots = c_rkPacket.bOpenSlots;
	memcpy(r.aSlot, c_rkPacket.aSlot, sizeof(r.aSlot));
}

const CPythonPlayer::SGrowthPetPotential* CPythonPlayer::GrowthPet_FindPotential(DWORD dwID) const
{
	std::map<DWORD, SGrowthPetPotential>::const_iterator f = m_kGrowthPetPotential.find(dwID);
	return f == m_kGrowthPetPotential.end() ? NULL : &f->second;
}

// ------------------------------------------------------------------------------------------------ CNetworkActorManager

void CNetworkActorManager::Mt2009SetGrowthPetLook(DWORD dwVID, WORD wScalePct)
{
	if (!wScalePct)
		wScalePct = 100;
	if (wScalePct > 1000)
		wScalePct = 1000;

	// GC 235 may come before the add packet (or for an actor never shown): keep it, but never let the map grow without end
	if (m_kMt2009GrowthPetScale.size() >= 1024 && m_kMt2009GrowthPetScale.find(dwVID) == m_kMt2009GrowthPetScale.end())
	{
		for (std::map<DWORD, WORD>::iterator it = m_kMt2009GrowthPetScale.begin(); it != m_kMt2009GrowthPetScale.end(); )
		{
			if (m_kNetActorDict.find(it->first) == m_kNetActorDict.end())
				m_kMt2009GrowthPetScale.erase(it++);
			else
				++it;
		}
	}
	m_kMt2009GrowthPetScale[dwVID] = wScalePct;

	CInstanceBase* pkInst = CPythonCharacterManager::Instance().GetInstancePtr(dwVID);
	if (pkInst)
		__Mt2009ApplyGrowthPetLook(dwVID, pkInst);
}

// the pet NPC's own race scale (npc scale table) times the per cent of GC 235 - 100 % leaves the model as it is
void CNetworkActorManager::__Mt2009ApplyGrowthPetLook(DWORD dwVID, CInstanceBase* pkInst)
{
	std::map<DWORD, WORD>::const_iterator f = m_kMt2009GrowthPetScale.find(dwVID);
	if (!pkInst || f == m_kMt2009GrowthPetScale.end() || pkInst->IsPC())
		return;

	float fX = 1.0f, fY = 1.0f, fZ = 1.0f;
	CRaceData* pRaceData;
	if (CRaceManager::Instance().GetRaceDataPointer(pkInst->GetRace(), &pRaceData))
	{
		const CRaceData::SScale kScale = pRaceData->GetScale();
		fX = kScale.scaleX;
		fY = kScale.scaleY;
		fZ = kScale.scaleZ;
	}
	const float fPct = float(f->second) / 100.0f;
	CActorInstance* pkActor = pkInst->GetGraphicThingInstancePtr();
	if (!pkActor)
		return;
	pkActor->SetScale(fX * fPct, fY * fPct, fZ * fPct, true);
	pkActor->UpdateBoundingSphere();
}

// ---------------------------------------------------------------------------------------------- CPythonNetworkStream

void CPythonNetworkStream::__GrowthPetCallGame(const char* c_szFunc, PyObject* poArgs)
{
	PyCallClassMemberFunc(m_apoPhaseWnd[PHASE_WINDOW_GAME], c_szFunc, poArgs);
}

bool CPythonNetworkStream::RecvGrowthPet()
{
	TPacketGCPet kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;

	switch (kPacket.subheader)
	{
		case SUBHEADER_PET_EGG_USE_SUCCESS:
			__GrowthPetCallGame("PetHatchingWindowCommand", Py_BuildValue("(i)", (int) EGG_USE_SUCCESS));
			break;
		case SUBHEADER_PET_EGG_USE_FAILED_BECAUSE_NAME:
			__GrowthPetCallGame("PetHatchingWindowCommand", Py_BuildValue("(i)", (int) EGG_USE_FAILED_BECAUSE_NAME));
			break;
		case SUBHEADER_PET_EGG_USE_FAILED_TIMEOVER:
			__GrowthPetCallGame("PetHatchingWindowCommand", Py_BuildValue("(i)", (int) EGG_USE_FAILED_TIMEOVER));
			break;
		case SUBHEADER_PET_UNSUMMON:
		{
			const DWORD dwOld = CPythonPlayer::Instance().GrowthPet_GetActive();
			CPythonPlayer::Instance().GrowthPet_SetActive(0);
			__RefreshInventoryWindow();
			__GrowthPetCallGame("PetAffectShowerRefresh", Py_BuildValue("()"));
			if (dwOld)
				__GrowthPetCallGame("PetInfoRefresh", Py_BuildValue("(i)", (int) dwOld));
			break;
		}
		case SUBHEADER_PET_FEED_FAILED:
			__GrowthPetCallGame("PetFeedReuslt", Py_BuildValue("(i)", FALSE));
			break;
		case SUBHEADER_PET_FEED_SUCCESS:
			__GrowthPetCallGame("PetFeedReuslt", Py_BuildValue("(i)", TRUE));
			break;
		case SUBHEADER_PET_REVIVE_FAILED:
			__GrowthPetCallGame("PetReviveResult", Py_BuildValue("(i)", FALSE));
			break;
		case SUBHEADER_PET_REVIVE_SUCCESS:
			__GrowthPetCallGame("PetReviveResult", Py_BuildValue("(i)", TRUE));
			break;
		case SUBHEADER_PET_NAME_CHANGE_FAILED:
			__GrowthPetCallGame("PetNameChangeWindowCommand", Py_BuildValue("(i)", (int) NAME_CHANGE_USE_FAILED_BECAUSE_NAME));
			break;
		case SUBHEADER_PET_NAME_CHANGE_SUCCESS:
			__GrowthPetCallGame("PetNameChangeWindowCommand", Py_BuildValue("(i)", (int) NAME_CHANGE_USE_SUCCESS));
			break;
		case SUBHEADER_PET_WINDOW_TYPE_INFO:
			__GrowthPetCallGame("PetWindowTypeResult", Py_BuildValue("(i)", (int) PET_WINDOW_INFO));
			break;
		case SUBHEADER_PET_WINDOW_TYPE_ATTR_CHANGE:
			__GrowthPetCallGame("PetWindowTypeResult", Py_BuildValue("(i)", (int) PET_WINDOW_ATTR_CHANGE));
			break;
		case SUBHEADER_PET_WINDOW_TYPE_PREMIUM_FEED:
			__GrowthPetCallGame("PetWindowTypeResult", Py_BuildValue("(i)", (int) PET_WINDOW_PRIMIUM_FEEDSTUFF));
			break;
		case SUBHEADER_PET_EVOLVE_SUCCESS:
			__GrowthPetCallGame("PetEvolveResult", Py_BuildValue("(i)", TRUE));
			break;
		case SUBHEADER_PET_POTENTIAL_FAILED:
			__GrowthPetCallGame("PetPotentialResult", Py_BuildValue("(i)", FALSE));
			break;
		case SUBHEADER_PET_POTENTIAL_SUCCESS:
			__GrowthPetCallGame("PetPotentialResult", Py_BuildValue("(i)", TRUE));
			break;
		default:
			TraceError("RecvGrowthPet: unknown subheader %u", kPacket.subheader);
			break;
	}
	return true;
}

bool CPythonNetworkStream::RecvGrowthPetSet(bool bExchange)
{
	TPacketGCPetSet kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;
	CPythonPlayer::Instance().GrowthPet_Set(kPacket, bExchange);
	__GrowthPetCallGame("PetInfoRefresh", Py_BuildValue("(i)", (int) kPacket.dwID));
	return true;
}

bool CPythonNetworkStream::RecvGrowthPetDelete()
{
	TPacketGCPetDelete kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;
	const bool bActive = CPythonPlayer::Instance().GrowthPet_GetActive() == kPacket.dwID;
	CPythonPlayer::Instance().GrowthPet_Delete(kPacket.dwID);
	if (bActive)
		__GrowthPetCallGame("PetAffectShowerRefresh", Py_BuildValue("()"));
	__GrowthPetCallGame("PetInfoRefresh", Py_BuildValue("(i)", (int) kPacket.dwID));
	return true;
}

bool CPythonNetworkStream::RecvGrowthPetSummon()
{
	TPacketGCPetSummon kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;
	CPythonPlayer::Instance().GrowthPet_SetActive(kPacket.dwID);
	__RefreshInventoryWindow();
	__GrowthPetCallGame("PetAffectShowerRefresh", Py_BuildValue("()"));
	__GrowthPetCallGame("PetInfoRefresh", Py_BuildValue("(i)", (int) kPacket.dwID));
	return true;
}

bool CPythonNetworkStream::RecvGrowthPetPointChange()
{
	TPacketGCPetPointUpdate kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;
	CPythonPlayer::Instance().GrowthPet_SetPoint(kPacket.dwID, kPacket.bPoint, kPacket.dwValue);
	__GrowthPetCallGame("PetInfoRefresh", Py_BuildValue("(i)", (int) kPacket.dwID));
	return true;
}

bool CPythonNetworkStream::RecvGrowthPetNameChangeResult()
{
	TPacketGCPetNameChangeResult kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;

	if (SUBHEADER_PET_NAME_CHANGE_SUCCESS == kPacket.subheader)
	{
		char szName[GROWTH_PET_NAME_MAX + 1];
		memcpy(szName, kPacket.szName, GROWTH_PET_NAME_MAX);
		szName[GROWTH_PET_NAME_MAX] = '\0';
		CPythonPlayer::SGrowthPet* p = CPythonPlayer::Instance().GrowthPet_Find(kPacket.dwID);
		if (p)
			p->strName = szName;
		__GrowthPetCallGame("PetNameChangeWindowCommand", Py_BuildValue("(i)", (int) NAME_CHANGE_USE_SUCCESS));
		__GrowthPetCallGame("PetInfoRefresh", Py_BuildValue("(i)", (int) kPacket.dwID));
	}
	else
		__GrowthPetCallGame("PetNameChangeWindowCommand", Py_BuildValue("(i)", (int) NAME_CHANGE_USE_FAILED_BECAUSE_NAME));
	return true;
}

bool CPythonNetworkStream::RecvGrowthPetDetermineResult()
{
	TPacketGCPetDetermineResult kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;
	__GrowthPetCallGame("PetAttrDetermineResult", Py_BuildValue("(i)", (int) kPacket.type));
	return true;
}

bool CPythonNetworkStream::RecvGrowthPetAttrChangeResult()
{
	TPacketGCPetAttrChangeResult kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;
	__GrowthPetCallGame("PetAttrChangeResult", Py_BuildValue("(ii)", (int) kPacket.pos.cell, (int) kPacket.type));
	return true;
}

bool CPythonNetworkStream::RecvGrowthPetSkillUpdate()
{
	TPacketGCPetSkillUpdate kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;
	CPythonPlayer::Instance().GrowthPet_SetSkills(kPacket.dwID, kPacket.aSkill);
	__GrowthPetCallGame("PetAffectShowerRefresh", Py_BuildValue("()"));
	__GrowthPetCallGame("PetInfoRefresh", Py_BuildValue("(i)", (int) kPacket.dwID));
	return true;
}

bool CPythonNetworkStream::RecvGrowthPetSkillCooltime()
{
	TPacketGCPetSkillCooltime kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;
	CPythonPlayer::Instance().GrowthPet_SetSkillCooltime(kPacket.dwID, kPacket.bSlot, kPacket.dwCooltime);
	return true;
}

bool CPythonNetworkStream::RecvGrowthPetLook()
{
	TPacketGCPetLook kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;
	m_rokNetActorMgr->Mt2009SetGrowthPetLook(kPacket.dwVID, kPacket.wScalePct);
	return true;
}

bool CPythonNetworkStream::RecvGrowthPetPotential()
{
	TPacketGCPetPotential kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;
	CPythonPlayer::Instance().GrowthPet_SetPotential(kPacket);
	__GrowthPetCallGame("PetPotentialRefresh", Py_BuildValue("(i)", (int) kPacket.dwID));
	__GrowthPetCallGame("PetInfoRefresh", Py_BuildValue("(i)", (int) kPacket.dwID));
	return true;
}

bool CPythonNetworkStream::SendPetHatchingPacket(const char* c_szName, TItemPos eggPos)
{
	TPacketCGPetHatch kPacket;
	kPacket.header = HEADER_CG_PET_HATCH;
	CopyName(kPacket.name, sizeof(kPacket.name), c_szName);
	kPacket.eggPos = eggPos;
	if (!Send(sizeof(kPacket), &kPacket))
		return false;
	return SendSequence();
}

bool CPythonNetworkStream::SendPetWindowType(BYTE bType)
{
	TPacketCGPetWindowType kPacket;
	kPacket.header = HEADER_CG_PET_WINDOW_TYPE;
	kPacket.type = bType;
	if (!Send(sizeof(kPacket), &kPacket))
		return false;
	return SendSequence();
}

bool CPythonNetworkStream::SendPetWindowPacket(BYTE bWindow, bool bState)
{
	TPacketCGPetWindow kPacket;
	kPacket.header = HEADER_CG_PET_WINDOW;
	kPacket.window = bWindow;
	kPacket.state = bState ? 1 : 0;
	if (!Send(sizeof(kPacket), &kPacket))
		return false;
	return SendSequence();
}

bool CPythonNetworkStream::SendPetNameChangePacket(const char* c_szName, TItemPos changeNamePos, TItemPos upBringingPos)
{
	TPacketCGPetNameChange kPacket;
	kPacket.header = HEADER_CG_PET_NAME_CHANGE;
	CopyName(kPacket.name, sizeof(kPacket.name), c_szName);
	kPacket.changeNamePos = changeNamePos;
	kPacket.upBringingPos = upBringingPos;
	if (!Send(sizeof(kPacket), &kPacket))
		return false;
	return SendSequence();
}

bool CPythonNetworkStream::SendPetFeedPacket(BYTE bIndex, const std::vector<std::pair<TItemPos, WORD> >& c_rkItems)
{
	TPacketCGPetFeed kPacket;
	memset(&kPacket, 0, sizeof(kPacket));
	kPacket.header = HEADER_CG_PET_FEED;
	kPacket.index = bIndex;
	for (size_t i = 0; i < c_rkItems.size() && i < GROWTH_PET_FEED_SLOTS; ++i)
	{
		kPacket.pos[i] = c_rkItems[i].first;
		kPacket.count[i] = c_rkItems[i].second;
	}
	if (!Send(sizeof(kPacket), &kPacket))
		return false;
	return SendSequence();
}

bool CPythonNetworkStream::SendPetAttrDetermine(TItemPos determinePos)
{
	TPacketCGPetDetermine kPacket;
	kPacket.header = HEADER_CG_PET_DETERMINE;
	kPacket.determinePos = determinePos;
	if (!Send(sizeof(kPacket), &kPacket))
		return false;
	return SendSequence();
}

bool CPythonNetworkStream::SendPetAttrChange(TItemPos upBringingPos, TItemPos attrChangePos)
{
	TPacketCGPetAttrChange kPacket;
	kPacket.header = HEADER_CG_PET_ATTR_CHANGE;
	kPacket.upBringingPos = upBringingPos;
	kPacket.attrChangePos = attrChangePos;
	if (!Send(sizeof(kPacket), &kPacket))
		return false;
	return SendSequence();
}

bool CPythonNetworkStream::SendPetRevive(TItemPos upBringingPos, const std::vector<std::pair<TItemPos, WORD> >& c_rkItems)
{
	TPacketCGPetRevive kPacket;
	memset(&kPacket, 0, sizeof(kPacket));
	kPacket.header = HEADER_CG_PET_REVIVE;
	kPacket.upBringingPos = upBringingPos;
	for (size_t i = 0; i < c_rkItems.size() && i < GROWTH_PET_REVIVE_SLOTS; ++i)
	{
		kPacket.pos[i] = c_rkItems[i].first;
		kPacket.count[i] = c_rkItems[i].second;
	}
	if (!Send(sizeof(kPacket), &kPacket))
		return false;
	return SendSequence();
}

bool CPythonNetworkStream::SendPetLearnSkill(BYTE bSlot, TItemPos learnSkillPos)
{
	TPacketCGPetLearnSkill kPacket;
	kPacket.header = HEADER_CG_PET_LEARN_SKILL;
	kPacket.slotIndex = bSlot;
	kPacket.learnSkillPos = learnSkillPos;
	if (!Send(sizeof(kPacket), &kPacket))
		return false;
	return SendSequence();
}

bool CPythonNetworkStream::SendPetSkillUpgradeRequest(BYTE bSlot)
{
	TPacketCGPetSkillUpgrade kPacket;
	kPacket.header = HEADER_CG_PET_SKILL_UPGRADE;
	kPacket.slotIndex = bSlot;
	if (!Send(sizeof(kPacket), &kPacket))
		return false;
	return SendSequence();
}

bool CPythonNetworkStream::SendPetDeleteSkill(BYTE bSlot, TItemPos deleteSkillPos)
{
	TPacketCGPetDeleteSkill kPacket;
	kPacket.header = HEADER_CG_PET_DELETE_SKILL;
	kPacket.slotIndex = bSlot;
	kPacket.deleteSkillPos = deleteSkillPos;
	if (!Send(sizeof(kPacket), &kPacket))
		return false;
	return SendSequence();
}

bool CPythonNetworkStream::SendPetDeleteAllSkill(TItemPos deleteAllSkillPos)
{
	TPacketCGPetDeleteAllSkill kPacket;
	kPacket.header = HEADER_CG_PET_DELETE_ALL_SKILL;
	kPacket.deleteAllSkillPos = deleteAllSkillPos;
	if (!Send(sizeof(kPacket), &kPacket))
		return false;
	return SendSequence();
}

bool CPythonNetworkStream::SendPetPotential(BYTE bAction, BYTE bSlot, TItemPos eggPos)
{
	TPacketCGPetPotential kPacket;
	kPacket.header = HEADER_CG_PET_POTENTIAL;
	kPacket.action = bAction;
	kPacket.slot = bSlot;
	kPacket.eggPos = eggPos;
	if (!Send(sizeof(kPacket), &kPacket))
		return false;
	return SendSequence();
}

// -------------------------------------------------------------------------------------------------------- python: net

namespace
{
	bool GetPos(PyObject* poArgs, int iWindowArg, TItemPos* pkPos)
	{
		int iWindow, iCell;
		if (!PyTuple_GetInteger(poArgs, iWindowArg, &iWindow) || !PyTuple_GetInteger(poArgs, iWindowArg + 1, &iCell))
			return false;
		*pkPos = TItemPos((BYTE) iWindow, (WORD) iCell);
		return true;
	}
}

// net.SendPetHatchingPacket(name, window, cell)
PyObject* netSendPetHatchingPacket(PyObject* poSelf, PyObject* poArgs)
{
	char* szName;
	TItemPos kPos;
	if (!PyTuple_GetString(poArgs, 0, &szName) || !GetPos(poArgs, 1, &kPos))
		return Py_BuildException();
	CPythonNetworkStream::Instance().SendPetHatchingPacket(szName, kPos);
	return Py_BuildNone();
}

// net.SendPetHatchingWindowPacket(state)
PyObject* netSendPetHatchingWindowPacket(PyObject* poSelf, PyObject* poArgs)
{
	bool bState;
	if (!PyTuple_GetBoolean(poArgs, 0, &bState))
		return Py_BuildException();
	CPythonNetworkStream::Instance().SendPetWindowPacket(PET_WINDOW_HATCH, bState);
	return Py_BuildNone();
}

// net.SendPetNameChangeWindowPacket(state) - Anka2 sent PET_WINDOW_HATCH here (its bug); ours the name change window
PyObject* netSendPetNameChangeWindowPacket(PyObject* poSelf, PyObject* poArgs)
{
	bool bState;
	if (!PyTuple_GetBoolean(poArgs, 0, &bState))
		return Py_BuildException();
	CPythonNetworkStream::Instance().SendPetWindowPacket(PET_WINDOW_NAME_CHANGE, bState);
	return Py_BuildNone();
}

// net.SendPetWindowType(type)
PyObject* netSendPetWindowType(PyObject* poSelf, PyObject* poArgs)
{
	int iType;
	if (!PyTuple_GetInteger(poArgs, 0, &iType))
		return Py_BuildException();
	CPythonNetworkStream::Instance().SendPetWindowType((BYTE) iType);
	return Py_BuildNone();
}

// net.SendPetFeedPacket(index, [(window, cell, count), ...]) - up to 9; FEED_EVOL_EVENT: an empty list
PyObject* netSendPetFeedPacket(PyObject* poSelf, PyObject* poArgs)
{
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BuildException();
	PyObject* poList = PyTuple_Size(poArgs) > 1 ? PyTuple_GetItem(poArgs, 1) : NULL;
	PyObject* poCounts = PyTuple_Size(poArgs) > 2 ? PyTuple_GetItem(poArgs, 2) : NULL;
	std::vector<std::pair<TItemPos, WORD> > kItems;
	if (poList && !ParsePosList(poList, poCounts, GROWTH_PET_FEED_SLOTS, kItems))
		return Py_BuildException("SendPetFeedPacket(index, [(window, cell, count), ...])");
	CPythonNetworkStream::Instance().SendPetFeedPacket((BYTE) iIndex, kItems);
	return Py_BuildNone();
}

// net.SendPetAttrDetermine(window, cell)
PyObject* netSendPetAttrDetermine(PyObject* poSelf, PyObject* poArgs)
{
	TItemPos kPos;
	if (!GetPos(poArgs, 0, &kPos))
		return Py_BuildException();
	CPythonNetworkStream::Instance().SendPetAttrDetermine(kPos);
	return Py_BuildNone();
}

// net.SendPetAttrChange(sealWindow, sealCell, itemWindow, itemCell)
PyObject* netSendPetAttrChange(PyObject* poSelf, PyObject* poArgs)
{
	TItemPos kSeal, kItem;
	if (!GetPos(poArgs, 0, &kSeal) || !GetPos(poArgs, 2, &kItem))
		return Py_BuildException();
	CPythonNetworkStream::Instance().SendPetAttrChange(kSeal, kItem);
	return Py_BuildNone();
}

// net.SendPetRevive(sealWindow, sealCell, [(window, cell, count), ...]) - up to 10
PyObject* netSendPetRevive(PyObject* poSelf, PyObject* poArgs)
{
	TItemPos kSeal;
	if (!GetPos(poArgs, 0, &kSeal))
		return Py_BuildException();
	PyObject* poList = PyTuple_Size(poArgs) > 2 ? PyTuple_GetItem(poArgs, 2) : NULL;
	std::vector<std::pair<TItemPos, WORD> > kItems;
	if (poList && !ParsePosList(poList, NULL, GROWTH_PET_REVIVE_SLOTS, kItems))
		return Py_BuildException("SendPetRevive(sealWindow, sealCell, [(window, cell, count), ...])");
	CPythonNetworkStream::Instance().SendPetRevive(kSeal, kItems);
	return Py_BuildNone();
}

// net.SendPetLearnSkill(slot, window, cell)
PyObject* netSendPetLearnSkill(PyObject* poSelf, PyObject* poArgs)
{
	int iSlot;
	TItemPos kPos;
	if (!PyTuple_GetInteger(poArgs, 0, &iSlot) || !GetPos(poArgs, 1, &kPos))
		return Py_BuildException();
	CPythonNetworkStream::Instance().SendPetLearnSkill((BYTE) iSlot, kPos);
	return Py_BuildNone();
}

// net.SendPetSkillUpgradeRequest(slot)
PyObject* netSendPetSkillUpgradeRequest(PyObject* poSelf, PyObject* poArgs)
{
	int iSlot;
	if (!PyTuple_GetInteger(poArgs, 0, &iSlot))
		return Py_BuildException();
	CPythonNetworkStream::Instance().SendPetSkillUpgradeRequest((BYTE) iSlot);
	return Py_BuildNone();
}

// net.SendPetDeleteSkill(slot, window, cell)
PyObject* netSendPetDeleteSkill(PyObject* poSelf, PyObject* poArgs)
{
	int iSlot;
	TItemPos kPos;
	if (!PyTuple_GetInteger(poArgs, 0, &iSlot) || !GetPos(poArgs, 1, &kPos))
		return Py_BuildException();
	CPythonNetworkStream::Instance().SendPetDeleteSkill((BYTE) iSlot, kPos);
	return Py_BuildNone();
}

// net.SendPetDeleteAllSkill(window, cell)
PyObject* netSendPetDeleteAllSkill(PyObject* poSelf, PyObject* poArgs)
{
	TItemPos kPos;
	if (!GetPos(poArgs, 0, &kPos))
		return Py_BuildException();
	CPythonNetworkStream::Instance().SendPetDeleteAllSkill(kPos);
	return Py_BuildNone();
}

// net.SendPetNameChangePacket(name, scrollWindow, scrollCell, sealWindow, sealCell)
PyObject* netSendPetNameChangePacket(PyObject* poSelf, PyObject* poArgs)
{
	char* szName;
	TItemPos kScroll, kSeal;
	if (!PyTuple_GetString(poArgs, 0, &szName) || !GetPos(poArgs, 1, &kScroll) || !GetPos(poArgs, 3, &kSeal))
		return Py_BuildException();
	CPythonNetworkStream::Instance().SendPetNameChangePacket(szName, kScroll, kSeal);
	return Py_BuildNone();
}

// net.SendPetPotential(action, slot, window, cell) - PET_POTENTIAL_INSERT (an egg into the slot) / PET_POTENTIAL_REMOVE
PyObject* netSendPetPotential(PyObject* poSelf, PyObject* poArgs)
{
	int iAction, iSlot;
	TItemPos kPos;
	if (!PyTuple_GetInteger(poArgs, 0, &iAction) || !PyTuple_GetInteger(poArgs, 1, &iSlot) || !GetPos(poArgs, 2, &kPos))
		return Py_BuildException();
	CPythonNetworkStream::Instance().SendPetPotential((BYTE) iAction, (BYTE) iSlot, kPos);
	return Py_BuildNone();
}

// net.CheckUsePetItem() - Anka2's: the server checks it
PyObject* netCheckUsePetItem(PyObject* poSelf, PyObject* poArgs)
{
	return Py_BuildValue("i", (int) PET_EGG_USE_TRUE);
}

// ----------------------------------------------------------------------------------------------------- python: player

// player.GetPetItem(petId) -> (vnum, level, evolution, hp, def, sp, lifeEnd, maxLife, birthday, exp, itemExp, nextExp,
//   championLevel, championExp, championItemExp, championNextExp, res, blockPen, precision, type, skillSlots, name)
// hp / def / sp / res / blockPen / precision in 0.001 % (1555 = 1.555 %); an unknown pet: zeros and ""
PyObject* playerGetPetItem(PyObject* poSelf, PyObject* poArgs)
{
	int iPetID;
	if (!PyTuple_GetInteger(poArgs, 0, &iPetID))
		return Py_BadArgument();
	const CPythonPlayer::SGrowthPet* p = FindPet(iPetID);
	if (!p)
		return Py_BuildValue("iiiiiiiiiiiiiiiiiiiiis", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "");
	const DWORD* d = p->adwPoints;
	return Py_BuildValue("iiiiiiiiiiiiiiiiiiiiis",
		(int) p->dwSummonItemVnum,
		(int) d[POINT_UPBRINGING_PET_LEVEL],
		(int) d[POINT_UPBRINGING_PET_EVOL_LEVEL],
		(int) d[POINT_UPBRINGING_PET_HP],
		(int) d[POINT_UPBRINGING_PET_DEF_GRADE],
		(int) d[POINT_UPBRINGING_PET_SP],
		(int) d[POINT_UPBRINGING_DURATION],
		(int) d[POINT_UPBRINGING_MAX_DURATION],
		(int) d[POINT_UPBRINGING_BIRTHDAY],
		(int) d[POINT_UPBRINGING_PET_EXP],
		(int) d[POINT_UPBRINGING_PET_ITEM_EXP],
		(int) d[POINT_UPBRINGING_PET_NEXT_EXP],
		(int) d[POINT_UPBRINGING_CHAMPION_LEVEL],
		(int) d[POINT_UPBRINGING_CHAMPION_EXP],
		(int) d[POINT_UPBRINGING_CHAMPION_ITEM_EXP],
		(int) d[POINT_UPBRINGING_CHAMPION_NEXT_EXP],
		(int) d[POINT_UPBRINGING_CHAMPION_RES],
		(int) d[POINT_UPBRINGING_CHAMPION_BLOCK_PEN],
		(int) d[POINT_UPBRINGING_CHAMPION_PRECISION],
		(int) d[POINT_UPBRINGING_TYPE],
		(int) d[POINT_UPBRINGING_SKILL_SLOTS],
		p->strName.c_str());
}

// player.GetPetSkill(petId, slot) -> (skill, level, cooltime); Anka2's player.GetPetSkill(petId) -> (openSlots, skill0,
// level0, cooltime0, skill1, level1, cooltime1, skill2, level2, cooltime2)
PyObject* playerGetPetSkill(PyObject* poSelf, PyObject* poArgs)
{
	int iPetID;
	if (!PyTuple_GetInteger(poArgs, 0, &iPetID))
		return Py_BadArgument();
	const CPythonPlayer::SGrowthPet* p = FindPet(iPetID);
	int iSlot;
	if (PyTuple_Size(poArgs) > 1)
	{
		if (!PyTuple_GetInteger(poArgs, 1, &iSlot))
			return Py_BadArgument();
		if (!p || iSlot < 0 || iSlot >= GROWTH_PET_SKILL_SLOTS)
			return Py_BuildValue("iii", 0, 0, 0);
		const CPythonPlayer::SGrowthPetSkill& s = p->aSkill[iSlot];
		return Py_BuildValue("iii", (int) s.bSkill, (int) s.bLevel, (int) s.dwCooltime);
	}
	if (!p)
		return Py_BuildValue("iiiiiiiiii", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
	int iOpen = 0;
	for (int i = 0; i < GROWTH_PET_SKILL_SLOTS; ++i)
		if (!p->aSkill[i].bLocked)
			++iOpen;
	return Py_BuildValue("iiiiiiiiii", iOpen,
		(int) p->aSkill[0].bSkill, (int) p->aSkill[0].bLevel, (int) p->aSkill[0].dwCooltime,
		(int) p->aSkill[1].bSkill, (int) p->aSkill[1].bLevel, (int) p->aSkill[1].dwCooltime,
		(int) p->aSkill[2].bSkill, (int) p->aSkill[2].bLevel, (int) p->aSkill[2].dwCooltime);
}

// player.GetPetSkillByIndex(petId, slot, skillLevel 1..20) -> (activatePct, valueTenths, durationTenths) from GC 233
PyObject* playerGetPetSkillByIndex(PyObject* poSelf, PyObject* poArgs)
{
	int iPetID, iSlot, iLevel;
	if (!PyTuple_GetInteger(poArgs, 0, &iPetID) || !PyTuple_GetInteger(poArgs, 1, &iSlot))
		return Py_BadArgument();
	const CPythonPlayer::SGrowthPet* p = FindPet(iPetID);
	if (PyTuple_Size(poArgs) < 3)
	{
		// Anka2's form: (skill, level, now1, now2, now3, next1, next2, next3, hasNext)
		if (!p || iSlot < 0 || iSlot >= GROWTH_PET_SKILL_SLOTS)
			return Py_BuildValue("iiiiiiiii", 0, 0, 0, 0, 0, 0, 0, 0, 0);
		const CPythonPlayer::SGrowthPetSkill& s = p->aSkill[iSlot];
		const int iLevel = s.bLevel > GROWTH_PET_SKILL_LEVEL_MAX ? GROWTH_PET_SKILL_LEVEL_MAX : s.bLevel;
		const int iNow = iLevel > 0 ? iLevel - 1 : 0;
		const int iNext = iNow + 1 < GROWTH_PET_SKILL_LEVEL_MAX ? iNow + 1 : GROWTH_PET_SKILL_LEVEL_MAX - 1;
		return Py_BuildValue("iiiiiiiii", (int) s.bSkill, (int) s.bLevel,
			(int) s.abFormula1[iNow], (int) s.awFormula2[iNow], (int) s.abFormula3[iNow],
			(int) s.abFormula1[iNext], (int) s.awFormula2[iNext], (int) s.abFormula3[iNext],
			s.bLevel < GROWTH_PET_SKILL_LEVEL_MAX ? 1 : 0);
	}
	if (!PyTuple_GetInteger(poArgs, 2, &iLevel))
		return Py_BadArgument();
	if (!p || iSlot < 0 || iSlot >= GROWTH_PET_SKILL_SLOTS || iLevel < 1 || iLevel > GROWTH_PET_SKILL_LEVEL_MAX)
		return Py_BuildValue("iii", 0, 0, 0);
	const CPythonPlayer::SGrowthPetSkill& s = p->aSkill[iSlot];
	return Py_BuildValue("iii", (int) s.abFormula1[iLevel - 1], (int) s.awFormula2[iLevel - 1], (int) s.abFormula3[iLevel - 1]);
}

// player.GetPetPotential(petId, slot) -> (eggVnum, skill, level, endTime)
PyObject* playerGetPetPotential(PyObject* poSelf, PyObject* poArgs)
{
	int iPetID, iSlot;
	if (!PyTuple_GetInteger(poArgs, 0, &iPetID) || !PyTuple_GetInteger(poArgs, 1, &iSlot))
		return Py_BadArgument();
	const CPythonPlayer::SGrowthPetPotential* p = CPythonPlayer::Instance().GrowthPet_FindPotential((DWORD) iPetID);
	if (!p || iSlot < 0 || iSlot >= GROWTH_PET_POTENTIAL_SLOTS)
		return Py_BuildValue("iiii", 0, 0, 0, 0);
	const TGrowthPetPotentialSlot& s = p->aSlot[iSlot];
	return Py_BuildValue("iiii", (int) s.dwEggVnum, (int) s.bSkill, (int) s.bLevel, (int) s.dwEndTime);
}

// player.GetPetPotentialSlots(petId) -> open potential slots (0..2)
PyObject* playerGetPetPotentialSlots(PyObject* poSelf, PyObject* poArgs)
{
	int iPetID;
	if (!PyTuple_GetInteger(poArgs, 0, &iPetID))
		return Py_BadArgument();
	const CPythonPlayer::SGrowthPetPotential* p = CPythonPlayer::Instance().GrowthPet_FindPotential((DWORD) iPetID);
	return Py_BuildValue("i", p ? (int) p->bOpenSlots : 0);
}

// player.GetPetLifeTime(petId) -> (lifeEnd, maxLife)
PyObject* playerGetPetLifeTime(PyObject* poSelf, PyObject* poArgs)
{
	int iPetID;
	if (!PyTuple_GetInteger(poArgs, 0, &iPetID))
		return Py_BadArgument();
	const CPythonPlayer::SGrowthPet* p = FindPet(iPetID);
	if (!p)
		return Py_BuildValue("ii", 0, 0);
	return Py_BuildValue("ii", (int) p->adwPoints[POINT_UPBRINGING_DURATION], (int) p->adwPoints[POINT_UPBRINGING_MAX_DURATION]);
}

namespace
{
	// SPEC.md: mob part = NEXT * 9 / 10, item part = NEXT - mob part
	PyObject* BuildExpPoints(const CPythonPlayer::SGrowthPet* p, int iExp, int iItemExp, int iNext)
	{
		if (!p)
			return Py_BuildValue("iiii", 0, 0, 0, 0);
		const DWORD dwNext = p->adwPoints[iNext];
		const DWORD dwMob = (DWORD) ((unsigned long long) dwNext * 9 / 10);
		return Py_BuildValue("iiii", (int) p->adwPoints[iExp], (int) dwMob, (int) p->adwPoints[iItemExp], (int) (dwNext - dwMob));
	}
}

// player.GetPetExpPoints(petId) -> (exp, mobExpNeeded, itemExp, itemExpNeeded)
PyObject* playerGetPetExpPoints(PyObject* poSelf, PyObject* poArgs)
{
	int iPetID;
	if (!PyTuple_GetInteger(poArgs, 0, &iPetID))
		return Py_BadArgument();
	return BuildExpPoints(FindPet(iPetID), POINT_UPBRINGING_PET_EXP, POINT_UPBRINGING_PET_ITEM_EXP, POINT_UPBRINGING_PET_NEXT_EXP);
}

// player.GetPetChampionExpPoints(petId) -> (championExp, mobExpNeeded, championItemExp, itemExpNeeded)
PyObject* playerGetPetChampionExpPoints(PyObject* poSelf, PyObject* poArgs)
{
	int iPetID;
	if (!PyTuple_GetInteger(poArgs, 0, &iPetID))
		return Py_BadArgument();
	return BuildExpPoints(FindPet(iPetID), POINT_UPBRINGING_CHAMPION_EXP, POINT_UPBRINGING_CHAMPION_ITEM_EXP, POINT_UPBRINGING_CHAMPION_NEXT_EXP);
}

// player.IsPetExchange(petId) -> 1: the exchange partner's pet (GC 226)
PyObject* playerIsPetExchange(PyObject* poSelf, PyObject* poArgs)
{
	int iPetID;
	if (!PyTuple_GetInteger(poArgs, 0, &iPetID))
		return Py_BadArgument();
	const CPythonPlayer::SGrowthPet* p = FindPet(iPetID);
	return Py_BuildValue("i", p && p->bExchange ? 1 : 0);
}

// player.GetActivePetItemId() -> the summoned pet's id (0: none)
PyObject* playerGetActivePetItemId(PyObject* poSelf, PyObject* poArgs)
{
	return Py_BuildValue("i", (int) CPythonPlayer::Instance().GrowthPet_GetActive());
}

// player.GetActivePetItemVNum() -> the summoned pet's seal vnum (0: none)
PyObject* playerGetActivePetItemVNum(PyObject* poSelf, PyObject* poArgs)
{
	const CPythonPlayer::SGrowthPet* p = CPythonPlayer::Instance().GrowthPet_Find(CPythonPlayer::Instance().GrowthPet_GetActive());
	return Py_BuildValue("i", p ? (int) p->dwSummonItemVnum : 0);
}

// player.GetPetItemVNumInBag(petId) -> the seal vnum of a pet (also one in a bag)
PyObject* playerGetPetItemVNumInBag(PyObject* poSelf, PyObject* poArgs)
{
	int iPetID;
	if (!PyTuple_GetInteger(poArgs, 0, &iPetID))
		return Py_BadArgument();
	const CPythonPlayer::SGrowthPet* p = FindPet(iPetID);
	return Py_BuildValue("i", p ? (int) p->dwSummonItemVnum : 0);
}

PyObject* playerSetOpenPetHatchingWindow(PyObject* poSelf, PyObject* poArgs)
{
	bool bOpen;
	if (!PyTuple_GetBoolean(poArgs, 0, &bOpen))
		return Py_BadArgument();
	CPythonPlayer::Instance().m_bGrowthPetHatchingWindow = bOpen;
	return Py_BuildNone();
}

PyObject* playerSetOpenPetNameChangeWindow(PyObject* poSelf, PyObject* poArgs)
{
	bool bOpen;
	if (!PyTuple_GetBoolean(poArgs, 0, &bOpen))
		return Py_BadArgument();
	CPythonPlayer::Instance().m_bGrowthPetNameChangeWindow = bOpen;
	return Py_BuildNone();
}

PyObject* playerSetOpenPetFeedWindow(PyObject* poSelf, PyObject* poArgs)
{
	bool bOpen;
	if (!PyTuple_GetBoolean(poArgs, 0, &bOpen))
		return Py_BadArgument();
	CPythonPlayer::Instance().m_bGrowthPetFeedWindow = bOpen;
	return Py_BuildNone();
}

PyObject* playerIsOpenPetHatchingWindow(PyObject* poSelf, PyObject* poArgs)
{
	return Py_BuildValue("i", CPythonPlayer::Instance().m_bGrowthPetHatchingWindow ? 1 : 0);
}

PyObject* playerIsOpenPetNameChangeWindow(PyObject* poSelf, PyObject* poArgs)
{
	return Py_BuildValue("i", CPythonPlayer::Instance().m_bGrowthPetNameChangeWindow ? 1 : 0);
}

PyObject* playerIsOpenPetFeedWindow(PyObject* poSelf, PyObject* poArgs)
{
	return Py_BuildValue("i", CPythonPlayer::Instance().m_bGrowthPetFeedWindow ? 1 : 0);
}

// ------------------------------------------------------------------------------------------------------ python: skill

namespace
{
	SPetSkillProto* FindPetSkill(int iIndex)
	{
		std::map<DWORD, SPetSkillProto>::iterator f = s_kPetSkillProto.find((DWORD) iIndex);
		return f == s_kPetSkillProto.end() ? NULL : &f->second;
	}
}

// skill.GetPetSkillInfo(id) -> (name, description, type, cooldown)
PyObject* skillGetPetSkillInfo(PyObject* poSelf, PyObject* poArgs)
{
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BadArgument();
	const SPetSkillProto* p = FindPetSkill(iIndex);
	if (!p)
		return Py_BuildValue("ssii", "", "", 0, 0);
	return Py_BuildValue("ssii", p->strName.c_str(), p->strDescription.c_str(), (int) p->dwType, (int) p->dwCooldown);
}

// skill.GetPetSkillIconImage(id) -> the image handle (0: none), loaded on first use
PyObject* skillGetPetSkillIconImage(PyObject* poSelf, PyObject* poArgs)
{
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BadArgument();
	SPetSkillProto* p = FindPetSkill(iIndex);
	if (!p)
		return Py_BuildValue("i", 0);
	if (!p->bImageLoaded)
	{
		p->bImageLoaded = true;
		if (!p->strIconFileName.empty())
			p->pImage = (CGraphicImage*) CResourceManager::Instance().GetResourcePointer(p->strIconFileName.c_str());
	}
	return Py_BuildValue("i", p->pImage);
}

// skill.GetPetSkillIconPath(id) -> "d:/ymir work/ui/skill/pet/<icon>.sub" ("": none)
PyObject* skillGetPetSkillIconPath(PyObject* poSelf, PyObject* poArgs)
{
	int iIndex;
	if (!PyTuple_GetInteger(poArgs, 0, &iIndex))
		return Py_BadArgument();
	const SPetSkillProto* p = FindPetSkill(iIndex);
	return Py_BuildValue("s", p ? p->strIconFileName.c_str() : "");
}

// --------------------------------------------------------------------------------------------------- registration

namespace
{
	void AddMethods(const char* c_szModule, PyMethodDef* pkMethods)
	{
		PyObject* poModule = PyImport_AddModule(c_szModule);	// borrowed
		if (!poModule)
			return;
		for (PyMethodDef* p = pkMethods; p->ml_name; ++p)
			PyModule_AddObject(poModule, p->ml_name, PyCFunction_New(p, NULL));
	}

	struct SIntConstant
	{
		const char*	c_szName;
		long		lValue;
	};

	void AddConstants(const char* c_szModule, const SIntConstant* c_pkConstants)
	{
		PyObject* poModule = PyImport_AddModule(c_szModule);	// borrowed
		if (!poModule)
			return;
		for (const SIntConstant* p = c_pkConstants; p->c_szName; ++p)
			PyModule_AddIntConstant(poModule, p->c_szName, p->lValue);
	}
}

// UserInterface.cpp, after the modules (as Mt2009SkillColor_RegisterPython)
void Mt2009GrowthPet_RegisterPython()
{
	static PyMethodDef s_netMethods[] =
	{
		{ "SendPetHatchingPacket",			netSendPetHatchingPacket,			METH_VARARGS },
		{ "SendPetHatchingWindowPacket",	netSendPetHatchingWindowPacket,		METH_VARARGS },
		{ "SendPetNameChangeWindowPacket",	netSendPetNameChangeWindowPacket,	METH_VARARGS },
		{ "SendPetWindowType",				netSendPetWindowType,				METH_VARARGS },
		{ "SendPetFeedPacket",				netSendPetFeedPacket,				METH_VARARGS },
		{ "SendPetAttrDetermine",			netSendPetAttrDetermine,			METH_VARARGS },
		{ "SendPetAttrChange",				netSendPetAttrChange,				METH_VARARGS },
		{ "SendPetRevive",					netSendPetRevive,					METH_VARARGS },
		{ "SendPetLearnSkill",				netSendPetLearnSkill,				METH_VARARGS },
		{ "SendPetSkillUpgradeRequest",		netSendPetSkillUpgradeRequest,		METH_VARARGS },
		{ "SendPetDeleteSkill",				netSendPetDeleteSkill,				METH_VARARGS },
		{ "SendPetDeleteAllSkill",			netSendPetDeleteAllSkill,			METH_VARARGS },
		{ "SendPetNameChangePacket",		netSendPetNameChangePacket,			METH_VARARGS },
		{ "SendPetPotential",				netSendPetPotential,				METH_VARARGS },
		{ "CheckUsePetItem",				netCheckUsePetItem,					METH_VARARGS },
		{ NULL, NULL, 0 },
	};
	static PyMethodDef s_playerMethods[] =
	{
		{ "GetPetItem",						playerGetPetItem,					METH_VARARGS },
		{ "GetPetSkill",					playerGetPetSkill,					METH_VARARGS },
		{ "GetPetSkillByIndex",				playerGetPetSkillByIndex,			METH_VARARGS },
		{ "GetPetPotential",				playerGetPetPotential,				METH_VARARGS },
		{ "GetPetPotentialSlots",			playerGetPetPotentialSlots,			METH_VARARGS },
		{ "GetPetLifeTime",					playerGetPetLifeTime,				METH_VARARGS },
		{ "GetPetExpPoints",				playerGetPetExpPoints,				METH_VARARGS },
		{ "GetPetChampionExpPoints",		playerGetPetChampionExpPoints,		METH_VARARGS },
		{ "IsPetExchange",					playerIsPetExchange,				METH_VARARGS },
		{ "GetActivePetItemId",				playerGetActivePetItemId,			METH_VARARGS },
		{ "GetActivePetItemVNum",			playerGetActivePetItemVNum,			METH_VARARGS },
		{ "GetPetItemVNumInBag",			playerGetPetItemVNumInBag,			METH_VARARGS },
		{ "SetOpenPetHatchingWindow",		playerSetOpenPetHatchingWindow,		METH_VARARGS },
		{ "SetOpenPetNameChangeWindow",		playerSetOpenPetNameChangeWindow,	METH_VARARGS },
		{ "SetOpenPetFeedWindow",			playerSetOpenPetFeedWindow,			METH_VARARGS },
		{ "IsOpenPetHatchingWindow",		playerIsOpenPetHatchingWindow,		METH_VARARGS },
		{ "IsOpenPetNameChangeWindow",		playerIsOpenPetNameChangeWindow,	METH_VARARGS },
		{ "IsOpenPetFeedWindow",			playerIsOpenPetFeedWindow,			METH_VARARGS },
		{ NULL, NULL, 0 },
	};
	static PyMethodDef s_skillMethods[] =
	{
		{ "GetPetSkillInfo",				skillGetPetSkillInfo,				METH_VARARGS },
		{ "GetPetSkillIconImage",			skillGetPetSkillIconImage,			METH_VARARGS },
		{ "GetPetSkillIconPath",			skillGetPetSkillIconPath,			METH_VARARGS },
		{ NULL, NULL, 0 },
	};
	AddMethods("net", s_netMethods);
	AddMethods("player", s_playerMethods);
	AddMethods("skill", s_skillMethods);

	static const SIntConstant s_akPlayer[] =
	{
		{ "PET_FEED_SLOT_MAX",					GROWTH_PET_FEED_SLOTS },
		{ "PET_REVIVE_MATERIAL_SLOT_MAX",		GROWTH_PET_REVIVE_SLOTS },
		{ "PET_SKILL_COUNT_MAX",				GROWTH_PET_SKILL_SLOTS },
		{ "PET_GROWTH_SKILL_LEVEL_MAX",			GROWTH_PET_SKILL_LEVEL_MAX },
		{ "PET_GROWTH_EVOL_MAX",				GROWTH_PET_EVOL_MAX },
		{ "PET_GROWTH_SKILL_OPEN_EVOL_LEVEL",	GROWTH_PET_SKILL_OPEN_EVOL_LEVEL },
		{ "PET_POTENTIAL_SLOT_MAX",				GROWTH_PET_POTENTIAL_SLOTS },
		{ "PET_MAX_LEVEL",						GROWTH_PET_MAX_LEVEL },
		{ "PET_CHAMPION_MAX_LEVEL",				GROWTH_PET_CHAMPION_MAX_LEVEL },
		{ "PET_HATCHING_MONEY",					GROWTH_PET_HATCHING_MONEY },
		{ "PET_SKILL_UPGRADE_PRICE",			GROWTH_PET_SKILL_UPGRADE_PRICE },
		{ "PET_NAME_MIN_SIZE",					GROWTH_PET_NAME_MIN },
		{ "PET_NAME_MAX_SIZE",					GROWTH_PET_NAME_MAX },
		{ "LIFE_TIME_FLASH_MIN_TIME",			LIFE_TIME_FLASH_MIN_TIME },
		{ "SPECIAL_EVOL_MIN_AGE",				SPECIAL_EVOL_MIN_AGE },
		{ "PET_ATTR_DETERMINE_ITEM",			PET_ATTR_DETERMINE_ITEM },
		{ "PET_ATTR_CHANGE_ITEM",				PET_ATTR_CHANGE_ITEM },
		{ "FEED_LIFE_TIME_EVENT",				FEED_LIFE_TIME_EVENT },
		{ "FEED_EVOL_EVENT",					FEED_EVOL_EVENT },
		{ "FEED_EXP_EVENT",						FEED_EXP_EVENT },
		{ "FEED_BUTTON_MAX",					FEED_BUTTON_MAX },
		{ "PET_WINDOW_INFO",					PET_WINDOW_INFO },
		{ "PET_WINDOW_ATTR_CHANGE",				PET_WINDOW_ATTR_CHANGE },
		{ "PET_WINDOW_PRIMIUM_FEEDSTUFF",		PET_WINDOW_PRIMIUM_FEEDSTUFF },
		{ "PET_WINDOW_HATCH",					PET_WINDOW_HATCH },
		{ "PET_WINDOW_NAME_CHANGE",				PET_WINDOW_NAME_CHANGE },
		{ "PET_POTENTIAL_INSERT",				PET_POTENTIAL_INSERT },
		{ "PET_POTENTIAL_REMOVE",				PET_POTENTIAL_REMOVE },
		{ "POINT_UPBRINGING_PET_LEVEL",			POINT_UPBRINGING_PET_LEVEL },
		{ "POINT_UPBRINGING_PET_EXP",			POINT_UPBRINGING_PET_EXP },
		{ "POINT_UPBRINGING_PET_ITEM_EXP",		POINT_UPBRINGING_PET_ITEM_EXP },
		{ "POINT_UPBRINGING_PET_NEXT_EXP",		POINT_UPBRINGING_PET_NEXT_EXP },
		{ "POINT_UPBRINGING_PET_EVOL_LEVEL",	POINT_UPBRINGING_PET_EVOL_LEVEL },
		{ "POINT_UPBRINGING_PET_HP",			POINT_UPBRINGING_PET_HP },
		{ "POINT_UPBRINGING_PET_DEF_GRADE",		POINT_UPBRINGING_PET_DEF_GRADE },
		{ "POINT_UPBRINGING_PET_SP",			POINT_UPBRINGING_PET_SP },
		{ "POINT_UPBRINGING_DURATION",			POINT_UPBRINGING_DURATION },
		{ "POINT_UPBRINGING_MAX_DURATION",		POINT_UPBRINGING_MAX_DURATION },
		{ "POINT_UPBRINGING_BIRTHDAY",			POINT_UPBRINGING_BIRTHDAY },
		{ "POINT_UPBRINGING_CHAMPION_LEVEL",	POINT_UPBRINGING_CHAMPION_LEVEL },
		{ "POINT_UPBRINGING_CHAMPION_EXP",		POINT_UPBRINGING_CHAMPION_EXP },
		{ "POINT_UPBRINGING_CHAMPION_ITEM_EXP",	POINT_UPBRINGING_CHAMPION_ITEM_EXP },
		{ "POINT_UPBRINGING_CHAMPION_NEXT_EXP",	POINT_UPBRINGING_CHAMPION_NEXT_EXP },
		{ "POINT_UPBRINGING_CHAMPION_RES",		POINT_UPBRINGING_CHAMPION_RES },
		{ "POINT_UPBRINGING_CHAMPION_BLOCK_PEN",	POINT_UPBRINGING_CHAMPION_BLOCK_PEN },
		{ "POINT_UPBRINGING_CHAMPION_PRECISION",	POINT_UPBRINGING_CHAMPION_PRECISION },
		{ "POINT_UPBRINGING_TYPE",				POINT_UPBRINGING_TYPE },
		{ "POINT_UPBRINGING_SKILL_SLOTS",		POINT_UPBRINGING_SKILL_SLOTS },
		{ "POINT_UPBRINGING_MAX_NUM",			POINT_UPBRINGING_MAX_NUM },
		{ NULL, 0 },
	};
	AddConstants("player", s_akPlayer);

	static const SIntConstant s_akSkill[] =
	{
		{ "PET_SKILL_USE_TYPE_NONE",	PET_SKILL_USE_TYPE_NONE },
		{ "PET_SKILL_USE_TYPE_PASSIVE",	PET_SKILL_USE_TYPE_PASSIVE },
		{ "PET_SKILL_USE_TYPE_AUTO",	PET_SKILL_USE_TYPE_AUTO },
		{ "PET_SKILL_USE_TYPE_MAX",		PET_SKILL_USE_TYPE_MAX },
		{ NULL, 0 },
	};
	AddConstants("skill", s_akSkill);

	static const SIntConstant s_akItem[] =
	{
		{ "ITEM_TYPE_GROWTH_PET",					ITEM_PET },
		{ "PET_EGG",								PET_EGG },
		{ "PET_UPBRINGING",							PET_UPBRINGING },
		{ "PET_BAG",								PET_BAG },
		{ "PET_FEEDSTUFF",							PET_FEEDSTUFF },
		{ "PET_SKILL",								PET_SKILL },
		{ "PET_SKILL_DEL_BOOK",						PET_SKILL_DEL_BOOK },
		{ "PET_NAME_CHANGE",						PET_NAME_CHANGE },
		{ "PET_EXPFOOD",							PET_EXPFOOD },
		{ "PET_SKILL_ALL_DEL_BOOK",					PET_SKILL_ALL_DEL_BOOK },
		{ "PET_EXPFOOD_PER",						PET_EXPFOOD_PER },
		{ "PET_ATTR_DETERMINE",						PET_ATTR_DETERMINE },
		{ "PET_ATTR_CHANGE",						PET_ATTR_CHANGE },
		{ "PET_PAY",								PET_PAY },
		{ "PET_PRIMIUM_FEEDSTUFF",					PET_PRIMIUM_FEEDSTUFF },
		{ "ITEM_ANTIFLAG_PETFEED",					0 },	// SPEC.md: not used - every egg / seal may be fed
		{ "EGG_USE_SUCCESS",						EGG_USE_SUCCESS },
		{ "EGG_USE_FAILED_BECAUSE_NAME",			EGG_USE_FAILED_BECAUSE_NAME },
		{ "EGG_USE_FAILED_TIMEOVER",				EGG_USE_FAILED_TIMEOVER },
		{ "PET_EGG_USE_TRUE",						PET_EGG_USE_TRUE },
		{ "PET_EGG_USE_FAILED_BECAUSE_TRADING",		PET_EGG_USE_FAILED_BECAUSE_TRADING },
		{ "PET_EGG_USE_FAILED_BECAUSE_SHOP_OPEN",	PET_EGG_USE_FAILED_BECAUSE_SHOP_OPEN },
		{ "PET_EGG_USE_FAILED_BECAUSE_MALL_OPEN",	PET_EGG_USE_FAILED_BECAUSE_MALL_OPEN },
		{ "PET_EGG_USE_FAILED_BECAUSE_SAFEBOX_OPEN",	PET_EGG_USE_FAILED_BECAUSE_SAFEBOX_OPEN },
		{ "NAME_CHANGE_USE_SUCCESS",				NAME_CHANGE_USE_SUCCESS },
		{ "NAME_CHANGE_USE_FAILED_BECAUSE_NAME",	NAME_CHANGE_USE_FAILED_BECAUSE_NAME },
		{ "PET_NAME_MIN_SIZE",						GROWTH_PET_NAME_MIN },
		{ "PET_NAME_MAX_SIZE",						GROWTH_PET_NAME_MAX },
		{ "PET_HATCHING_MONEY",						GROWTH_PET_HATCHING_MONEY },
		{ "PET_ATTR_CHANGE_ITEMVNUM",				PET_ATTR_CHANGE_ITEM },
		{ NULL, 0 },
	};
	AddConstants("item", s_akItem);

	static const SIntConstant s_akApp[] =
	{
		{ "ENABLE_GROWTH_PET_SYSTEM",				1 },
#ifdef ENABLE_UPBRINGING_PET_CONQUEROR_LEVEL
		{ "ENABLE_UPBRINGING_PET_CONQUEROR_LEVEL",	1 },
#else
		{ "ENABLE_UPBRINGING_PET_CONQUEROR_LEVEL",	0 },
#endif
		// root's constinfo.py: the client version gate - an exe without this cannot read GC 224-236
		{ "MT2009_GROWTH_PET_EXE",					1 },
		{ NULL, 0 },
	};
	AddConstants("app", s_akApp);
}

#endif
