/**
* MT2009_PLUS_MINIGAMES_V1: Yut Nori 3D thrower (race 20505) drawn into a render target.
* After Owsap v6.2.6 PythonYutnoriManager (author blackdragonx61 / Mali).
* Changes: the render target texture is created on first use (app.YutnoriCreate) instead of at start,
* a missing model/texture is not fatal, motion-done is reported even if the model cannot be shown.
**/

#include "StdAfx.h"

#if defined(ENABLE_MINI_GAME_YUTNORI)
#include "../EterLib/Camera.h"
#include "../EterLib/RenderTargetManager.h"
#include "../GameLib/RaceMotionData.h"

#include "PythonApplication.h"
#include "PythonYutnoriManager.h"

CPythonYutnoriManager::CPythonYutnoriManager()
{
	m_pModelInstance = nullptr;
	Initialize();
}

CPythonYutnoriManager::~CPythonYutnoriManager()
{
	Destroy();
}

void CPythonYutnoriManager::Initialize()
{
	m_pModelInstance = nullptr;
	m_bShow = false;
	m_bMotionProcess = true;
	m_bMotionDoneProcess = false;
	m_fAlpha = 1.0f;
	m_fColorAlpha = 0.0f;

	m_dColor = D3DXCOLOR(0.0f, 0.0f, 0.0f, 0.0f);

	m_MotionVec.clear();
	m_MotionVec.reserve(6);
	m_MotionVec.push_back(CRaceMotionData::NAME_WAIT);
	m_MotionVec.push_back(CRaceMotionData::NAME_STAND_UP);
	m_MotionVec.push_back(CRaceMotionData::NAME_DEAD);
	m_MotionVec.push_back(CRaceMotionData::NAME_NORMAL_ATTACK);
	m_MotionVec.push_back(CRaceMotionData::NAME_SPAWN);
	m_MotionVec.push_back(CRaceMotionData::NAME_SPECIAL_1);
}

void CPythonYutnoriManager::Destroy()
{
	if (m_pModelInstance)
	{
		delete m_pModelInstance;
		m_pModelInstance = nullptr;
	}

	m_bShow = false;
	m_bMotionProcess = true;
	m_bMotionDoneProcess = false;
	m_fAlpha = 1.0f;
	m_fColorAlpha = 0.0f;
	m_dColor = D3DXCOLOR(0.0f, 0.0f, 0.0f, 0.0f);
}

bool CPythonYutnoriManager::Create(DWORD dwWidth, DWORD dwHeight)
{
	CRenderTargetManager& rkRTMgr = CRenderTargetManager::Instance();
	if (!rkRTMgr.GetRenderTargetTexture(CRenderTargetManager::RENDER_TARGET_INDEX_YUTNORI))
	{
		if (!rkRTMgr.CreateA8R8G8B8Texture(dwWidth, dwHeight, CRenderTargetManager::RENDER_TARGET_INDEX_YUTNORI))
			TraceError("CPythonYutnoriManager::Create - cannot create the render target %ux%u", dwWidth, dwHeight);
	}

	if (!m_pModelInstance)
	{
		if (!CreateModelInstance())
		{
			TraceError("CPythonYutnoriManager::Create - cannot create race %d", YUTNORI_MODEL_RACE);
			return false;
		}

		SelectModel();
	}
	return true;
}

void CPythonYutnoriManager::Reset() const
{
	RECT rectRender;
	if (!CRenderTargetManager::Instance().GetRenderTargetRect(CRenderTargetManager::RENDER_TARGET_INDEX_YUTNORI, &rectRender))
		return;

	if (!CRenderTargetManager::Instance().ChangeRenderTarget(CRenderTargetManager::RENDER_TARGET_INDEX_YUTNORI))
		return;

	CRenderTargetManager::Instance().ClearRenderTarget();
	CPythonGraphic::Instance().ClearDepthBuffer();
	CRenderTargetManager::Instance().ResetRenderTarget();
}

bool CPythonYutnoriManager::CreateModelInstance()
{
	if (m_pModelInstance)
		return true;

	CInstanceBase::SCreateData kCreateData{};
	kCreateData.m_dwMovSpd = 100;
	kCreateData.m_dwAtkSpd = 100;
	kCreateData.m_bType = CActorInstance::TYPE_OBJECT;
	kCreateData.m_dwRace = YUTNORI_MODEL_RACE;

	CInstanceBase* pModel = new CInstanceBase();
	if (!pModel->Create(kCreateData))
	{
		delete pModel;
		return false;
	}

	m_pModelInstance = pModel;
	return true;
}

void CPythonYutnoriManager::SelectModel() const
{
	if (!m_pModelInstance)
		return;

	m_pModelInstance->Refresh(CRaceMotionData::NAME_WAIT, true);
	m_pModelInstance->SetLODLimits(0, 100.0f);
	m_pModelInstance->SetAlwaysRender(true);
	m_pModelInstance->SetRotation(0.0f);
	m_pModelInstance->NEW_SetPixelPosition(TPixelPosition(0.0f, 0.0f, 0.0f));

	CCameraManager::Instance().SetCurrentCamera(CCameraManager::DEFAULT_YUTNORI_CAMERA);
	CCamera* pCam = CCameraManager::Instance().GetCurrentCamera();
	if (pCam)
		pCam->SetTargetHeight(m_pModelInstance->GetGraphicThingInstancePtr()->GetHeight());
	CCameraManager::Instance().ResetToPreviousCamera();
}

void CPythonYutnoriManager::UpdateModel()
{
	if (!m_bShow)
		return;

	if (!m_pModelInstance)
		return;

	if (m_bMotionProcess)
	{
		m_pModelInstance->Transform();
		m_pModelInstance->GetGraphicThingInstancePtr()->RotationProcess();

		if (!m_pModelInstance->GetGraphicThingInstancePtr()->IsMotionDone())
			return;

		NotifyMotionDone();

		m_bMotionProcess = false;
		m_bMotionDoneProcess = true;
		m_fAlpha = 1.0f;

		m_pModelInstance->SetAlpha(m_fAlpha);
	}
	else if (m_bMotionDoneProcess)
	{
		m_fColorAlpha -= 0.01f;
		if (m_fColorAlpha <= 0.0f)
			m_fColorAlpha = 0.0f;

		m_dColor.a = m_fColorAlpha;

		m_fAlpha -= 0.01f;
		if (m_fAlpha <= 0.0f)
			m_fAlpha = 0.0f;

		m_pModelInstance->SetAlpha(m_fAlpha);

		if (m_fColorAlpha == 0.0f && m_fAlpha == 0.0f)
		{
			SetShow(false);
			m_bMotionDoneProcess = false;
		}
	}
}

void CPythonYutnoriManager::DeformModel() const
{
	if (!m_bShow)
		return;

	if (!m_pModelInstance)
		return;

	m_pModelInstance->Deform();
}

void CPythonYutnoriManager::RenderModel() const
{
	if (!m_bShow)
		return;

	if (!m_pModelInstance)
		return;

	RECT rectRender;
	if (!CRenderTargetManager::Instance().GetRenderTargetRect(CRenderTargetManager::RENDER_TARGET_INDEX_YUTNORI, &rectRender))
		return;

	const long lWidth = rectRender.right - rectRender.left;
	const long lHeight = rectRender.bottom - rectRender.top;
	if (lWidth <= 0 || lHeight <= 0)
		return;

	if (!CRenderTargetManager::Instance().ChangeRenderTarget(CRenderTargetManager::RENDER_TARGET_INDEX_YUTNORI))
		return;

	CRenderTargetManager::Instance().ClearRenderTarget(m_dColor);

	CPythonGraphic::Instance().ClearDepthBuffer();
	const float fFov = CPythonGraphic::Instance().GetFOV();
	const float fAspect = CPythonGraphic::Instance().GetAspect();
	const float fNearY = CPythonGraphic::Instance().GetNearY();
	const float fFarY = CPythonGraphic::Instance().GetFarY();

	const DWORD dwFog = STATEMANAGER.GetRenderState(D3DRS_FOGENABLE);
	STATEMANAGER.SetRenderState(D3DRS_FOGENABLE, FALSE);

	CCameraManager::Instance().SetCurrentCamera(CCameraManager::DEFAULT_YUTNORI_CAMERA);
	CCamera* pCam = CCameraManager::Instance().GetCurrentCamera();

	CPythonGraphic::Instance().PushState();

	if (pCam)
	{
		pCam->SetViewParams(
			D3DXVECTOR3(0.0f, -170.0f, 0.0f),
			D3DXVECTOR3(0.0f, 0.0f, 0.0f),
			D3DXVECTOR3(0.0f, 0.0f, 1.0f)
		);
		pCam->Pitch(90.0f);
		CPythonApplication::Instance().SetYutnoriCameraPosition();
	}

	// Owsap used lWidth / lHeight (integer division)
	CPythonGraphic::Instance().SetPerspective(30.0f, static_cast<float>(lWidth / lHeight), 100.0f, 15000.0f);

	m_pModelInstance->Render();

	CCameraManager::Instance().ResetToPreviousCamera();
	CPythonGraphic::Instance().PopState();
	CPythonGraphic::Instance().SetPerspective(fFov, fAspect, fNearY, fFarY);
	CRenderTargetManager::Instance().ResetRenderTarget();
	STATEMANAGER.SetRenderState(D3DRS_FOGENABLE, dwFog);
}

bool CPythonYutnoriManager::ChangeMotion(DWORD dwMotionIndex)
{
	if (dwMotionIndex >= m_MotionVec.size())
		return false;

	if (!m_pModelInstance)
	{
		// no model (missing race 20505): let the game go on
		NotifyMotionDone();
		return false;
	}

	if (m_pModelInstance->IsWalking())
		m_pModelInstance->EndWalking();

	m_pModelInstance->Refresh(m_MotionVec[dwMotionIndex], false);

	m_bMotionProcess = true;
	m_bMotionDoneProcess = false;
	m_fAlpha = 1.0f;

	m_pModelInstance->SetAlpha(m_fAlpha);
	m_fColorAlpha = 0.7f;

	m_dColor = D3DXCOLOR(0.0f, 0.0f, 0.0f, m_fColorAlpha);

	return true;
}

void CPythonYutnoriManager::NotifyMotionDone() const
{
	CPythonPlayer::Instance().YutnoriNotifyMotionDone();
}

void CPythonYutnoriManager::SetShow(bool bShow)
{
	m_bShow = bShow;

	if (!m_bShow)
		Reset();
}
#endif
