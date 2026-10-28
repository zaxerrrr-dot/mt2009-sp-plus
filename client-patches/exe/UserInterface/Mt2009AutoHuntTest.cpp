/**
* MT2009_PLUS_AUTOHUNT_TEST_V1 - the TEST auto hunt (Alt+H, root uiautohunt_test.py), ported from the "Oto Av" package
* the owner uploaded on 28 October 2026 (its client ENABLE_AUTO_HUNTER_SYSTEM: PythonPlayer UpdateAuto / AutoHuntTimer /
* AutoReserveUse, PythonCharacterManager AutoHuntingGetMob, the range effect, the green name, walking through monsters).
* Our own Auto Lowy (root uiautohunt.py + the server's /autohunt_target) stay as they are; root never runs both at once.
*
* The exe runs the whole hunt each frame (CPythonPlayer::Update, after the auto attack):
*   target - the nearest living monster the client sees (and a Metin stone with "Kamienie"), by rank (pawn ... king,
*            a bit each) and level; within the range around the character, or around the start point with "Zasieg"
*            on; no wall of the map on the straight line to it; nobody else's - a moving player who stands closer to it
*            within 15 m leaves it to him. Its name turns green and the client's own auto attack (__Update_AutoAttack,
*            the "click on a monster" walk-and-swing) does the fighting.
*   stuck  - 3 s without 0.3 m of way and no swing, or 15 s without a swing: the target is left and skipped for 10 s.
*   skills - 12 slots, each cast again after its own time (at least the skill's cooldown); an attack skill only at a
*            target in reach (2.5 m, with a bow 25 m), a toggle only while it is off; one skill a second.
*   items  - 12 slots: an HP / SP potion (USE_POTION / USE_POTION_NODELAY with value0 / value1) once the bar is at or
*            under the slot's %, then every 0.4 s until full; a buff item (USE_ABILITY_UP, USE_AFFECT) or a dew (BLEND)
*            every N seconds.
*   range  - d:/ymir work/effect/etc/auto_hunt/auto_hunt_range_01.mse on the ground while root shows it (scale range/10000).
*   while running, the character walks through monsters and stones (GameLib CActorInstance::TestActorCollision).
* Changes against the package: the range is a real limit (it was capped at 50 m), "Zasieg" anchors the area at the start
* point (the package's switch did nothing), inventory cell 0 can hold an item, the stuck target is really skipped (the
* package picked it again at once), any HP/SP potion counts (not only 27001-27008 / 70390-70391), no premium affect (the
* package's NEW_AFFECT_AUTO 814 from the items 20170-20173) - root asks the server instead (server-patches/autohunttest).
* No packet is new or changed: only the normal attack, skill, target and item-use packets.
*
* Python (player module):
*   AutoHuntTestStart(on)                     start / stop; AutoHuntTestIsRunning() -> 0/1
*   AutoHuntTestSetOptions(attack, skills, items, anchor)
*   AutoHuntTestSetFilter(rankMask, stones, minLevel, maxLevel)    rank bit 0 pawn ... 5 king
*   AutoHuntTestSetRange(range)               the hunt's range (game units, 100 = 1 m)
*   AutoHuntTestShowRange(range)              the ground circle (0 hides it)
*   AutoHuntTestSetSkillSlot(slot, skillSlot) -> the skill's time (s), 0 = not usable (slot 0-11; skillSlot 0 empties)
*   AutoHuntTestSetItemSlot(slot, cell)       -> the default value (% or s), 0 = not usable (slot 0-11; cell -1 empties)
*   AutoHuntTestSetSlotValue(slot, value)     slot 0-11 skills, 12-23 items; a skill never under its cooldown
*   AutoHuntTestGetSlot(slot) -> (pos, value) pos -1 = empty
*   AutoHuntTestClearSlots(which)             0 all, 1 skills, 2 items
*   AutoHuntTestGetTarget() -> vid, AutoHuntTestGetStartPosition() -> (x, y)
*   player.AUTOHUNT_TEST_SKILL_SLOTS (12), player.AUTOHUNT_TEST_ITEM_SLOTS (12)
*/
#include "StdAfx.h"
#include "PythonPlayer.h"
#include "PythonCharacterManager.h"
#include "PythonNonPlayer.h"
#include "PythonNetworkStream.h"
#include "PythonSkill.h"
#include "PythonTextTail.h"
#include "../EffectLib/EffectManager.h"
#include "../GameLib/ItemManager.h"
#include "../eterbase/Timer.h"

#include <float.h>

#ifdef ENABLE_MT2009_AUTOHUNT_TEST

namespace
{
	const char* const	AUTOHUNT_TEST_RANGE_EFFECT = "d:/ymir work/effect/etc/auto_hunt/auto_hunt_range_01.mse";
	const float			AUTOHUNT_TEST_EFFECT_RADIUS = 10000.0f;	// the effect's circle at scale 1 (the package)
	const float			AUTOHUNT_TEST_OTHER_PLAYER = 1500.0f;	// a moving player this near a monster may own it
	const float			AUTOHUNT_TEST_MELEE_REACH = 250.0f;
	const float			AUTOHUNT_TEST_BOW_REACH = 2500.0f;
	const DWORD			AUTOHUNT_TEST_STUCK_STEP_MS = 1000;
	const int			AUTOHUNT_TEST_STUCK_STEPS = 3;
	const float			AUTOHUNT_TEST_STUCK_WAY_SQ = 900.0f;	// 30 units
	const DWORD			AUTOHUNT_TEST_NO_SWING_MS = 15000;
	const DWORD			AUTOHUNT_TEST_SKIP_MS = 10000;
	const DWORD			AUTOHUNT_TEST_SEARCH_MS = 250;
	const DWORD			AUTOHUNT_TEST_POTION_MS = 400;
	const DWORD			AUTOHUNT_TEST_NO_POS = 0xffffffff;

	enum
	{
		ITEM_KIND_NONE,
		ITEM_KIND_HP,
		ITEM_KIND_SP,
		ITEM_KIND_TIMED,
	};

	int ItemKind(CItemData* pItem)
	{
		if (!pItem)
			return ITEM_KIND_NONE;
		if (pItem->GetType() == ITEM_BLEND)
			return ITEM_KIND_TIMED;
		if (pItem->GetType() != ITEM_USE)
			return ITEM_KIND_NONE;
		switch (pItem->GetSubType())
		{
			case USE_POTION:
			case USE_POTION_NODELAY:
				if (pItem->GetValue(0) > 0)
					return ITEM_KIND_HP;
				if (pItem->GetValue(1) > 0)
					return ITEM_KIND_SP;
				return ITEM_KIND_NONE;
			case USE_ABILITY_UP:
			case USE_AFFECT:
				return ITEM_KIND_TIMED;
		}
		return ITEM_KIND_NONE;
	}

	// the slot's default: 50 % for a potion, the buff's own time, 600 s for a dew (the package)
	DWORD ItemDefaultValue(CItemData* pItem)
	{
		switch (ItemKind(pItem))
		{
			case ITEM_KIND_HP:
			case ITEM_KIND_SP:
				return 50;
			case ITEM_KIND_TIMED:
				if (pItem->GetType() == ITEM_BLEND)
					return 600;
				if (pItem->GetSubType() == USE_ABILITY_UP)
					return (DWORD)std::max<long>(0, pItem->GetValue(1));
				return (DWORD)std::max<long>(0, pItem->GetValue(3));
		}
		return 0;
	}

	CItemData* ItemDataAt(DWORD dwCell)
	{
		const DWORD dwVnum = CPythonPlayer::Instance().GetItemIndex(TItemPos(INVENTORY, dwCell));
		CItemData* pItem = NULL;
		if (!dwVnum || !CItemManager::Instance().GetItemDataPointer(dwVnum, &pItem))
			return NULL;
		return pItem;
	}

	float DistanceSq2D(const TPixelPosition& a, const TPixelPosition& b)
	{
		const float dx = a.x - b.x;
		const float dy = a.y - b.y;
		return dx * dx + dy * dy;
	}
}

void CInstanceBase::SetAutoHuntTestTarget(bool bFlag)
{
	if (m_isAutoHuntTestTarget == bFlag)
		return;
	m_isAutoHuntTestTarget = bFlag;
	CPythonTextTail::Instance().SetCharacterTextTailColor(GetVirtualID(), GetNameColor());
}

void CInstanceBase::SetAutoHuntTestPass(bool bFlag)
{
	m_GraphicThingInstance.SetAutoHuntTestPass(bFlag);
}

void CPythonPlayer::AutoHuntTest_Reset()
{
	if (m_kAutoHuntTest.dwRangeEffect)
		CEffectManager::Instance().DestroyEffectInstance(m_kAutoHuntTest.dwRangeEffect);
	m_kAutoHuntTest = SAutoHuntTest();
	for (int i = 0; i < AUTOHUNT_TEST_SLOTS; ++i)
		m_kAutoHuntTest.aSlot[i].dwPos = AUTOHUNT_TEST_NO_POS;
}

DWORD CPythonPlayer::__AutoHuntTest_SkillTime(DWORD dwSkillSlotPos)
{
	const DWORD dwSkillIndex = GetSkillIndex(dwSkillSlotPos);
	CPythonSkill::SSkillData* pSkillData;
	if (!dwSkillIndex || !CPythonSkill::Instance().GetSkillData(dwSkillIndex, &pSkillData))
		return 0;
	if (CPythonSkill::SKILL_TYPE_GUILD == pSkillData->byType || !pSkillData->IsCanUseSkill())
		return 0;
	const float fPercent = GetSkillCurrentEfficientPercentage(dwSkillSlotPos);
	DWORD dwTime = pSkillData->GetSkillCoolTime(fPercent);
	if (!dwTime)
		dwTime = pSkillData->GetDuration(fPercent);
	return dwTime;
}

DWORD CPythonPlayer::AutoHuntTest_SetSkillSlot(int iSlot, DWORD dwSkillSlotPos)
{
	if (iSlot < 0 || iSlot >= AUTOHUNT_TEST_SKILL_SLOTS)
		return 0;
	SAutoHuntTestSlot& rkSlot = m_kAutoHuntTest.aSlot[iSlot];
	rkSlot.dwPos = AUTOHUNT_TEST_NO_POS;
	rkSlot.dwValue = 0;
	rkSlot.dwNextSec = 0;
	if (!dwSkillSlotPos || dwSkillSlotPos >= SKILL_MAX_NUM)
		return 0;
	const DWORD dwTime = __AutoHuntTest_SkillTime(dwSkillSlotPos);
	if (!dwTime)
		return 0;
	// one skill in one slot (the package)
	for (int i = 0; i < AUTOHUNT_TEST_SKILL_SLOTS; ++i)
		if (m_kAutoHuntTest.aSlot[i].dwPos == dwSkillSlotPos)
			m_kAutoHuntTest.aSlot[i].dwPos = AUTOHUNT_TEST_NO_POS;
	rkSlot.dwPos = dwSkillSlotPos;
	rkSlot.dwValue = dwTime;
	return dwTime;
}

DWORD CPythonPlayer::AutoHuntTest_SetItemSlot(int iSlot, DWORD dwCell)
{
	if (iSlot < 0 || iSlot >= AUTOHUNT_TEST_ITEM_SLOTS)
		return 0;
	SAutoHuntTestSlot& rkSlot = m_kAutoHuntTest.aSlot[AUTOHUNT_TEST_SKILL_SLOTS + iSlot];
	rkSlot.dwPos = AUTOHUNT_TEST_NO_POS;
	rkSlot.dwValue = 0;
	rkSlot.dwNextSec = 0;
	if (dwCell == AUTOHUNT_TEST_NO_POS || dwCell >= c_Inventory_Count)
		return 0;
	const DWORD dwValue = ItemDefaultValue(ItemDataAt(dwCell));
	if (!dwValue)
		return 0;
	for (int i = AUTOHUNT_TEST_SKILL_SLOTS; i < AUTOHUNT_TEST_SLOTS; ++i)
		if (m_kAutoHuntTest.aSlot[i].dwPos == dwCell)
			m_kAutoHuntTest.aSlot[i].dwPos = AUTOHUNT_TEST_NO_POS;
	rkSlot.dwPos = dwCell;
	rkSlot.dwValue = dwValue;
	return dwValue;
}

void CPythonPlayer::AutoHuntTest_SetSlotValue(int iSlot, DWORD dwValue)
{
	if (iSlot < 0 || iSlot >= AUTOHUNT_TEST_SLOTS)
		return;
	SAutoHuntTestSlot& rkSlot = m_kAutoHuntTest.aSlot[iSlot];
	if (rkSlot.dwPos == AUTOHUNT_TEST_NO_POS)
		return;
	if (iSlot < AUTOHUNT_TEST_SKILL_SLOTS)
		dwValue = (std::max)(dwValue, __AutoHuntTest_SkillTime(rkSlot.dwPos));	// never under the cooldown
	else if (ItemKind(ItemDataAt(rkSlot.dwPos)) != ITEM_KIND_TIMED)
		dwValue = std::min<DWORD>(dwValue, 100);								// a potion's %
	rkSlot.dwValue = dwValue;
}

void CPythonPlayer::AutoHuntTest_Start(bool bOn)
{
	SAutoHuntTest& r = m_kAutoHuntTest;
	if (bOn == r.bRunning)
		return;
	CInstanceBase* pkInstMain = NEW_GetMainActorPtr();
	if (bOn)
	{
		if (!pkInstMain)
			return;
		r.bRunning = true;
		pkInstMain->NEW_GetPixelPosition(&r.kStart);
		r.kStuckPos = r.kStart;
		r.iStuck = 0;
		r.dwSkipVID = 0;
		r.dwNextSearchMs = 0;
		r.dwLastSwingMs = r.dwStuckCheckMs = ELTimer_GetMSec();
		r.bHpLow = r.bSpLow = false;
		for (int i = 0; i < AUTOHUNT_TEST_SLOTS; ++i)
			r.aSlot[i].dwNextSec = 0;
		pkInstMain->SetAutoHuntTestPass(true);
		return;
	}
	r.bRunning = false;
	__AutoHuntTest_DropTarget();
	if (pkInstMain)
		pkInstMain->SetAutoHuntTestPass(false);
}

void CPythonPlayer::AutoHuntTest_ShowRange(float fRange)
{
	SAutoHuntTest& r = m_kAutoHuntTest;
	CEffectManager& rkEftMgr = CEffectManager::Instance();
	if (fRange <= 0.0f)
	{
		if (r.dwRangeEffect)
			rkEftMgr.DestroyEffectInstance(r.dwRangeEffect);
		r.dwRangeEffect = 0;
		r.fShownRange = 0.0f;
		return;
	}
	r.fShownRange = fRange;
	if (r.dwRangeEffect)
		return;
	CInstanceBase* pkInstMain = NEW_GetMainActorPtr();
	DWORD dwCRC = 0;
	if (!pkInstMain || !rkEftMgr.RegisterEffect2(AUTOHUNT_TEST_RANGE_EFFECT, &dwCRC))
		return;
	TPixelPosition kPos;
	pkInstMain->NEW_GetPixelPosition(&kPos);
	const int iEffect = rkEftMgr.CreateEffect(dwCRC, D3DXVECTOR3(kPos.x, -kPos.y, kPos.z), D3DXVECTOR3(0.0f, 0.0f, 0.0f));
	r.dwRangeEffect = iEffect > 0 ? (DWORD)iEffect : 0;
	__AutoHuntTest_UpdateRangeEffect();
}

void CPythonPlayer::__AutoHuntTest_UpdateRangeEffect()
{
	SAutoHuntTest& r = m_kAutoHuntTest;
	CInstanceBase* pkInstMain = NEW_GetMainActorPtr();
	CEffectManager& rkEftMgr = CEffectManager::Instance();
	if (!pkInstMain || !rkEftMgr.SelectEffectInstance(r.dwRangeEffect))
		return;
	TPixelPosition kPos;
	pkInstMain->NEW_GetPixelPosition(&kPos);
	if (r.bRunning && r.bAnchor)
	{
		kPos.x = r.kStart.x;
		kPos.y = r.kStart.y;
	}
	const float fScale = r.fShownRange / AUTOHUNT_TEST_EFFECT_RADIUS;
	D3DXMATRIX matScale, matTrans;
	D3DXMatrixScaling(&matScale, fScale, fScale, fScale);
	D3DXMatrixTranslation(&matTrans, kPos.x, -kPos.y, kPos.z);
	rkEftMgr.SetEffectInstanceGlobalMatrix(matScale * matTrans);
}

void CPythonPlayer::__AutoHuntTest_DropTarget()
{
	SAutoHuntTest& r = m_kAutoHuntTest;
	if (!r.dwTargetVID)
		return;
	CInstanceBase* pkTarget = CPythonCharacterManager::Instance().GetInstancePtr(r.dwTargetVID);
	if (pkTarget)
		pkTarget->SetAutoHuntTestTarget(false);
	if (m_dwAutoAttackTargetVID == r.dwTargetVID)
	{
		__ClearAutoAttackTargetActorID();
		__ClearReservedAction();
	}
	if (__GetTargetVID() == r.dwTargetVID)
		__ClearTarget();
	r.dwTargetVID = 0;
}

CInstanceBase* CPythonPlayer::__AutoHuntTest_FindTarget(CInstanceBase* pkInstMain)
{
	SAutoHuntTest& r = m_kAutoHuntTest;
	CPythonCharacterManager& rkChrMgr = CPythonCharacterManager::Instance();
	IPhysicsWorld* pWorld = IPhysicsWorld::GetPhysicsWorld();
	const DWORD dwNowMs = ELTimer_GetMSec();

	TPixelPosition kCenter;
	pkInstMain->NEW_GetPixelPosition(&kCenter);
	if (r.bAnchor)
		kCenter = r.kStart;
	const float fRangeSq = r.fRange * r.fRange;
	const D3DXVECTOR3& v3Src = pkInstMain->GetGraphicThingInstanceRef().GetPosition();

	float fBest = FLT_MAX;
	CInstanceBase* pkBest = NULL;
	for (CPythonCharacterManager::CharacterIterator it = rkChrMgr.CharacterInstanceBegin(); it != rkChrMgr.CharacterInstanceEnd(); ++it)
	{
		CInstanceBase* pkInst = *it;
		if (!pkInst || pkInst == pkInstMain || pkInst->IsDead())
			continue;
		if (pkInst->GetVirtualID() == r.dwSkipVID && dwNowMs < r.dwSkipUntilMs)
			continue;
		if (pkInst->IsStone())
		{
			if (!r.bStones)
				continue;
		}
		else if (pkInst->IsEnemy())
		{
			const CPythonNonPlayer::TMobTable* pMob = CPythonNonPlayer::Instance().GetTable(pkInst->GetVirtualNumber());
			if (!pMob)
				continue;
			const int iRank = pMob->bRank <= 5 ? pMob->bRank : 0;
			if (!(r.byRankMask & (1 << iRank)))
				continue;
			if (pMob->bLevel < r.iMinLevel || pMob->bLevel > r.iMaxLevel)
				continue;
		}
		else
			continue;

		TPixelPosition kPos;
		pkInst->NEW_GetPixelPosition(&kPos);
		if (DistanceSq2D(kPos, kCenter) > fRangeSq)
			continue;
		const float fDist = pkInstMain->GetDistance(pkInst);
		if (fDist >= fBest)
			continue;
		if (!pkInstMain->IsAttackableInstance(*pkInst))
			continue;

		// somebody else's: a moving player nearer to it than we are (the package's GetClosestPCInstance)
		bool bTaken = false;
		for (CPythonCharacterManager::CharacterIterator itPC = rkChrMgr.CharacterInstanceBegin(); itPC != rkChrMgr.CharacterInstanceEnd(); ++itPC)
		{
			CInstanceBase* pkPC = *itPC;
			if (!pkPC || pkPC == pkInstMain || pkPC == pkInst || !pkPC->IsPC() || pkPC->IsWaiting() || pkPC->IsDead())
				continue;
			const float fPC = pkInst->GetDistance(pkPC);
			if (fPC < AUTOHUNT_TEST_OTHER_PLAYER && fPC < fDist)
			{
				bTaken = true;
				break;
			}
		}
		if (bTaken)
			continue;

		// a wall of the map on the straight line (the package: 100 steps of the physics world)
		if (pWorld)
		{
			const D3DXVECTOR3 v3Dst(kPos.x, -kPos.y, v3Src.z);
			const D3DXVECTOR3 v3Step = (v3Dst - v3Src) / 100.0f;
			D3DXVECTOR3 v3Check = v3Src;
			bool bBlocked = false;
			for (int i = 0; i < 100; ++i, v3Check += v3Step)
			{
				if (pWorld->isPhysicalCollision(v3Check))
				{
					bBlocked = true;
					break;
				}
			}
			if (bBlocked)
				continue;
		}

		fBest = fDist;
		pkBest = pkInst;
	}
	return pkBest;
}

void CPythonPlayer::__AutoHuntTest_UseSkills(CInstanceBase* pkInstMain)
{
	SAutoHuntTest& r = m_kAutoHuntTest;
	const DWORD dwNowSec = (DWORD)CTimer::Instance().GetCurrentSecond();
	if (pkInstMain->IsUsingSkill() || r.dwLastSkillSec == dwNowSec)
		return;
	for (int i = 0; i < AUTOHUNT_TEST_SKILL_SLOTS; ++i)
	{
		SAutoHuntTestSlot& rkSlot = r.aSlot[i];
		if (rkSlot.dwPos == AUTOHUNT_TEST_NO_POS || !rkSlot.dwValue || rkSlot.dwNextSec > dwNowSec)
			continue;
		const DWORD dwSlotPos = rkSlot.dwPos;
		CPythonSkill::SSkillData* pSkillData;
		if (!CPythonSkill::Instance().GetSkillData(GetSkillIndex(dwSlotPos), &pSkillData))
			continue;
		if (IsSkillCoolTime(dwSlotPos))
			continue;
		if (pSkillData->IsAttackSkill())
		{
			CInstanceBase* pkTarget = __GetAliveTargetInstancePtr();
			if (!m_dwAutoAttackTargetVID || !pkTarget || pkTarget->IsStun())
				continue;
			const float fReach = pSkillData->IsNeedBow() ? AUTOHUNT_TEST_BOW_REACH : AUTOHUNT_TEST_MELEE_REACH;
			if (pkInstMain->GetDistance(pkTarget) > fReach)
				continue;
		}
		else if (IsToggleSkill(dwSlotPos) && IsSkillActive(dwSlotPos))
			continue;
		if (__UseSkill(dwSlotPos))
		{
			rkSlot.dwNextSec = dwNowSec + rkSlot.dwValue + 1;
			r.dwLastSkillSec = dwNowSec;
			return;
		}
	}
}

void CPythonPlayer::__AutoHuntTest_UseItems()
{
	SAutoHuntTest& r = m_kAutoHuntTest;
	const DWORD dwNowSec = (DWORD)CTimer::Instance().GetCurrentSecond();
	const DWORD dwNowMs = ELTimer_GetMSec();
	CPythonNetworkStream& rkNet = CPythonNetworkStream::Instance();

	const long lMaxHP = GetStatus(POINT_MAX_HP);
	const long lMaxSP = GetStatus(POINT_MAX_SP);
	const long lHP = GetStatus(POINT_HP);
	const long lSP = GetStatus(POINT_SP);
	if (lMaxHP > 0 && lHP + GetStatus(POINT_HP_RECOVERY) >= lMaxHP)
		r.bHpLow = false;
	if (lMaxSP > 0 && lSP + GetStatus(POINT_SP_RECOVERY) >= lMaxSP)
		r.bSpLow = false;

	bool bHpUsed = false;
	bool bSpUsed = false;
	for (int i = AUTOHUNT_TEST_SKILL_SLOTS; i < AUTOHUNT_TEST_SLOTS; ++i)
	{
		SAutoHuntTestSlot& rkSlot = r.aSlot[i];
		if (rkSlot.dwPos == AUTOHUNT_TEST_NO_POS || !rkSlot.dwValue)
			continue;
		CItemData* pItem = ItemDataAt(rkSlot.dwPos);
		const TItemPos kCell(INVENTORY, rkSlot.dwPos);
		switch (ItemKind(pItem))
		{
			case ITEM_KIND_HP:
				if (lMaxHP <= 0 || bHpUsed)
					break;
				if (lHP * 100 / lMaxHP <= (long)rkSlot.dwValue)
					r.bHpLow = true;
				if (r.bHpLow && dwNowMs >= r.dwHpPotionMs)
				{
					rkNet.SendItemUsePacket(kCell);
					r.dwHpPotionMs = dwNowMs + AUTOHUNT_TEST_POTION_MS;
					bHpUsed = true;
				}
				break;
			case ITEM_KIND_SP:
				if (lMaxSP <= 0 || bSpUsed)
					break;
				if (lSP * 100 / lMaxSP <= (long)rkSlot.dwValue)
					r.bSpLow = true;
				if (r.bSpLow && dwNowMs >= r.dwSpPotionMs)
				{
					rkNet.SendItemUsePacket(kCell);
					r.dwSpPotionMs = dwNowMs + AUTOHUNT_TEST_POTION_MS;
					bSpUsed = true;
				}
				break;
			case ITEM_KIND_TIMED:
				if (rkSlot.dwNextSec <= dwNowSec)
				{
					rkNet.SendItemUsePacket(kCell);
					rkSlot.dwNextSec = dwNowSec + rkSlot.dwValue;
				}
				break;
		}
	}
}

void CPythonPlayer::AutoHuntTest_Update()
{
	SAutoHuntTest& r = m_kAutoHuntTest;
	if (r.dwRangeEffect)
		__AutoHuntTest_UpdateRangeEffect();
	if (!r.bRunning)
		return;

	CInstanceBase* pkInstMain = NEW_GetMainActorPtr();
	if (!pkInstMain)
	{
		AutoHuntTest_Start(false);
		return;
	}
	pkInstMain->SetAutoHuntTestPass(true);
	if (pkInstMain->IsDead())
	{
		__AutoHuntTest_DropTarget();	// root stands up again (/restart_here) when asked to
		return;
	}

	const DWORD dwNowMs = ELTimer_GetMSec();
	if (pkInstMain->IsAttacking() || pkInstMain->IsUsingSkill())
		r.dwLastSwingMs = dwNowMs;

	if (r.bItems)
		__AutoHuntTest_UseItems();
	if (r.bSkills)
		__AutoHuntTest_UseSkills(pkInstMain);

	// the player clicked another monster, or the auto attack let ours go: that one is no longer ours
	if (r.dwTargetVID && r.dwTargetVID != m_dwAutoAttackTargetVID)
	{
		CInstanceBase* pkOld = CPythonCharacterManager::Instance().GetInstancePtr(r.dwTargetVID);
		if (pkOld)
			pkOld->SetAutoHuntTestTarget(false);
		r.dwTargetVID = 0;
	}
	if (!r.bAttack)
	{
		__AutoHuntTest_DropTarget();
		return;
	}

	if (m_dwAutoAttackTargetVID)
	{
		CInstanceBase* pkTarget = NEW_FindActorPtr(m_dwAutoAttackTargetVID);
		if (!pkTarget || pkTarget->IsDead())
		{
			__AutoHuntTest_DropTarget();
			__ClearAutoAttackTargetActorID();
		}
		else if (r.dwTargetVID)
		{
			if (pkInstMain->IsAttacking())
				r.iStuck = 0;
			else if (dwNowMs - r.dwStuckCheckMs >= AUTOHUNT_TEST_STUCK_STEP_MS)
			{
				TPixelPosition kPos;
				pkInstMain->NEW_GetPixelPosition(&kPos);
				r.iStuck = DistanceSq2D(kPos, r.kStuckPos) < AUTOHUNT_TEST_STUCK_WAY_SQ ? r.iStuck + 1 : 0;
				r.kStuckPos = kPos;
				r.dwStuckCheckMs = dwNowMs;
			}
			const DWORD dwSwingMs = (std::max)(r.dwLastSwingMs, r.dwTargetSinceMs);
			if (r.iStuck >= AUTOHUNT_TEST_STUCK_STEPS || dwNowMs - dwSwingMs >= AUTOHUNT_TEST_NO_SWING_MS)
			{
				r.dwSkipVID = r.dwTargetVID;
				r.dwSkipUntilMs = dwNowMs + AUTOHUNT_TEST_SKIP_MS;
				__AutoHuntTest_DropTarget();
			}
		}
	}

	if (m_dwAutoAttackTargetVID || dwNowMs < r.dwNextSearchMs)
		return;
	CInstanceBase* pkNew = __AutoHuntTest_FindTarget(pkInstMain);
	if (!pkNew)
	{
		r.dwNextSearchMs = dwNowMs + AUTOHUNT_TEST_SEARCH_MS;
		return;
	}
	const DWORD dwVID = pkNew->GetVirtualID();
	SetTarget(dwVID);
	__SetAutoAttackTargetActorID(dwVID);
	pkNew->SetAutoHuntTestTarget(true);
	r.dwTargetVID = dwVID;
	r.dwTargetSinceMs = dwNowMs;
	r.iStuck = 0;
	r.dwStuckCheckMs = dwNowMs;
	pkInstMain->NEW_GetPixelPosition(&r.kStuckPos);
}

namespace
{
	PyObject* playerAutoHuntTestStart(PyObject* poSelf, PyObject* poArgs)
	{
		int iOn;
		if (!PyTuple_GetInteger(poArgs, 0, &iOn))
			return Py_BuildException();
		CPythonPlayer::Instance().AutoHuntTest_Start(iOn != 0);
		return Py_BuildValue("i", CPythonPlayer::Instance().m_kAutoHuntTest.bRunning ? 1 : 0);
	}

	PyObject* playerAutoHuntTestIsRunning(PyObject* poSelf, PyObject* poArgs)
	{
		return Py_BuildValue("i", CPythonPlayer::Instance().m_kAutoHuntTest.bRunning ? 1 : 0);
	}

	PyObject* playerAutoHuntTestSetOptions(PyObject* poSelf, PyObject* poArgs)
	{
		int iAttack, iSkills, iItems, iAnchor;
		if (!PyTuple_GetInteger(poArgs, 0, &iAttack) || !PyTuple_GetInteger(poArgs, 1, &iSkills) ||
			!PyTuple_GetInteger(poArgs, 2, &iItems) || !PyTuple_GetInteger(poArgs, 3, &iAnchor))
			return Py_BuildException();
		CPythonPlayer::SAutoHuntTest& r = CPythonPlayer::Instance().m_kAutoHuntTest;
		r.bAttack = iAttack != 0;
		r.bSkills = iSkills != 0;
		r.bItems = iItems != 0;
		r.bAnchor = iAnchor != 0;
		return Py_BuildNone();
	}

	PyObject* playerAutoHuntTestSetFilter(PyObject* poSelf, PyObject* poArgs)
	{
		int iMask, iStones, iMin, iMax;
		if (!PyTuple_GetInteger(poArgs, 0, &iMask) || !PyTuple_GetInteger(poArgs, 1, &iStones) ||
			!PyTuple_GetInteger(poArgs, 2, &iMin) || !PyTuple_GetInteger(poArgs, 3, &iMax))
			return Py_BuildException();
		CPythonPlayer::SAutoHuntTest& r = CPythonPlayer::Instance().m_kAutoHuntTest;
		r.byRankMask = (BYTE)(iMask & 0x3f);
		r.bStones = iStones != 0;
		r.iMinLevel = (std::min)(iMin, iMax);
		r.iMaxLevel = (std::max)(iMin, iMax);
		return Py_BuildNone();
	}

	PyObject* playerAutoHuntTestSetRange(PyObject* poSelf, PyObject* poArgs)
	{
		float fRange;
		if (!PyTuple_GetFloat(poArgs, 0, &fRange))
			return Py_BuildException();
		CPythonPlayer::Instance().m_kAutoHuntTest.fRange = (std::max)(100.0f, fRange);
		return Py_BuildNone();
	}

	PyObject* playerAutoHuntTestShowRange(PyObject* poSelf, PyObject* poArgs)
	{
		float fRange;
		if (!PyTuple_GetFloat(poArgs, 0, &fRange))
			return Py_BuildException();
		CPythonPlayer::Instance().AutoHuntTest_ShowRange(fRange);
		return Py_BuildNone();
	}

	PyObject* playerAutoHuntTestSetSkillSlot(PyObject* poSelf, PyObject* poArgs)
	{
		int iSlot, iPos;
		if (!PyTuple_GetInteger(poArgs, 0, &iSlot) || !PyTuple_GetInteger(poArgs, 1, &iPos))
			return Py_BuildException();
		return Py_BuildValue("i", (int)CPythonPlayer::Instance().AutoHuntTest_SetSkillSlot(iSlot, iPos > 0 ? (DWORD)iPos : 0));
	}

	PyObject* playerAutoHuntTestSetItemSlot(PyObject* poSelf, PyObject* poArgs)
	{
		int iSlot, iCell;
		if (!PyTuple_GetInteger(poArgs, 0, &iSlot) || !PyTuple_GetInteger(poArgs, 1, &iCell))
			return Py_BuildException();
		return Py_BuildValue("i", (int)CPythonPlayer::Instance().AutoHuntTest_SetItemSlot(iSlot, iCell >= 0 ? (DWORD)iCell : AUTOHUNT_TEST_NO_POS));
	}

	PyObject* playerAutoHuntTestSetSlotValue(PyObject* poSelf, PyObject* poArgs)
	{
		int iSlot, iValue;
		if (!PyTuple_GetInteger(poArgs, 0, &iSlot) || !PyTuple_GetInteger(poArgs, 1, &iValue))
			return Py_BuildException();
		CPythonPlayer::Instance().AutoHuntTest_SetSlotValue(iSlot, iValue > 0 ? (DWORD)iValue : 0);
		return Py_BuildNone();
	}

	PyObject* playerAutoHuntTestGetSlot(PyObject* poSelf, PyObject* poArgs)
	{
		int iSlot;
		if (!PyTuple_GetInteger(poArgs, 0, &iSlot))
			return Py_BuildException();
		if (iSlot < 0 || iSlot >= CPythonPlayer::AUTOHUNT_TEST_SLOTS)
			return Py_BuildValue("(ii)", -1, 0);
		const CPythonPlayer::SAutoHuntTestSlot& rkSlot = CPythonPlayer::Instance().m_kAutoHuntTest.aSlot[iSlot];
		if (rkSlot.dwPos == AUTOHUNT_TEST_NO_POS)
			return Py_BuildValue("(ii)", -1, 0);
		return Py_BuildValue("(ii)", (int)rkSlot.dwPos, (int)rkSlot.dwValue);
	}

	PyObject* playerAutoHuntTestClearSlots(PyObject* poSelf, PyObject* poArgs)
	{
		int iWhich;
		if (!PyTuple_GetInteger(poArgs, 0, &iWhich))
			return Py_BuildException();
		CPythonPlayer::SAutoHuntTest& r = CPythonPlayer::Instance().m_kAutoHuntTest;
		for (int i = 0; i < CPythonPlayer::AUTOHUNT_TEST_SLOTS; ++i)
		{
			const bool bSkill = i < CPythonPlayer::AUTOHUNT_TEST_SKILL_SLOTS;
			if (iWhich == 0 || (iWhich == 1 && bSkill) || (iWhich == 2 && !bSkill))
			{
				r.aSlot[i].dwPos = AUTOHUNT_TEST_NO_POS;
				r.aSlot[i].dwValue = 0;
				r.aSlot[i].dwNextSec = 0;
			}
		}
		return Py_BuildNone();
	}

	PyObject* playerAutoHuntTestGetTarget(PyObject* poSelf, PyObject* poArgs)
	{
		return Py_BuildValue("i", (int)CPythonPlayer::Instance().m_kAutoHuntTest.dwTargetVID);
	}

	PyObject* playerAutoHuntTestGetStartPosition(PyObject* poSelf, PyObject* poArgs)
	{
		const TPixelPosition& kStart = CPythonPlayer::Instance().m_kAutoHuntTest.kStart;
		return Py_BuildValue("(ff)", kStart.x, kStart.y);
	}
}

void Mt2009AutoHuntTest_RegisterPython()
{
	static PyMethodDef s_methods[] =
	{
		{ "AutoHuntTestStart",				playerAutoHuntTestStart,			METH_VARARGS },
		{ "AutoHuntTestIsRunning",			playerAutoHuntTestIsRunning,		METH_VARARGS },
		{ "AutoHuntTestSetOptions",			playerAutoHuntTestSetOptions,		METH_VARARGS },
		{ "AutoHuntTestSetFilter",			playerAutoHuntTestSetFilter,		METH_VARARGS },
		{ "AutoHuntTestSetRange",			playerAutoHuntTestSetRange,			METH_VARARGS },
		{ "AutoHuntTestShowRange",			playerAutoHuntTestShowRange,		METH_VARARGS },
		{ "AutoHuntTestSetSkillSlot",		playerAutoHuntTestSetSkillSlot,		METH_VARARGS },
		{ "AutoHuntTestSetItemSlot",		playerAutoHuntTestSetItemSlot,		METH_VARARGS },
		{ "AutoHuntTestSetSlotValue",		playerAutoHuntTestSetSlotValue,		METH_VARARGS },
		{ "AutoHuntTestGetSlot",			playerAutoHuntTestGetSlot,			METH_VARARGS },
		{ "AutoHuntTestClearSlots",			playerAutoHuntTestClearSlots,		METH_VARARGS },
		{ "AutoHuntTestGetTarget",			playerAutoHuntTestGetTarget,		METH_VARARGS },
		{ "AutoHuntTestGetStartPosition",	playerAutoHuntTestGetStartPosition,	METH_VARARGS },
		{ NULL, NULL, 0 },
	};
	PyObject* poModule = PyImport_AddModule("player");	// borrowed
	if (!poModule)
		return;
	for (PyMethodDef* p = s_methods; p->ml_name; ++p)
		PyModule_AddObject(poModule, p->ml_name, PyCFunction_New(p, NULL));
	PyModule_AddIntConstant(poModule, "AUTOHUNT_TEST_SKILL_SLOTS", CPythonPlayer::AUTOHUNT_TEST_SKILL_SLOTS);
	PyModule_AddIntConstant(poModule, "AUTOHUNT_TEST_ITEM_SLOTS", CPythonPlayer::AUTOHUNT_TEST_ITEM_SLOTS);
}

#endif
