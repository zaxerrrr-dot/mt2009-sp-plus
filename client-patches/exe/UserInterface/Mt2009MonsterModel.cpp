/**
* MT2009_PLUS_MONSTER_CARD_MODEL_V1 - the Monster Cards' 3D preview (Autor: Digi Rasta: the idea and the python
* API player.Mt2009Model* of his nowy-system 0.28 exe, Mt2009Window.cpp; root/monstercard.py calls it).
* The model is a CInstanceBase (race scale, body colour); its texture is CRenderTargetManager's (device reset
* safe). Drawn as Digi Rasta's view drew it: in the render target window's own render (UI::CRenderTarget's
* render hook), the target, viewport, camera matrices, light and states set here and put back, then the
* texture drawn into the window. (The first port drew it in RenderGame through the camera manager, as the
* Yut Nori model - the window stayed empty in game, 2026-10-07.)
*
*   player.Mt2009ModelSelect(race)   the model of a race (1) or nothing (0: no race data -> the card picture)
*   player.Mt2009ModelShow(on)       drawn or not
*   player.Mt2009ModelRotation(deg)  turned (the window's left/right buttons)
*   player.Mt2009ModelZoom(in)       closer / farther
*   player.Mt2009ModelUpDown(up)     the view up / down
*   player.Mt2009ModelReset()        zoom, height and turn as at the start
*   player.Mt2009ModelMotion()       the race's next motion, once, then its idle again
*   app.RENDER_TARGET_INDEX_ILLUSTRATED  the render target index (wndMgr.SetRenderTarget)
**/

#include "StdAfx.h"

#if defined(ENABLE_MONSTER_CARD_MODEL) && defined(RENDER_TARGET)
#include "../EterLib/Camera.h"
#include "../EterLib/GrpBase.h"
#include "../EterLib/RenderTargetManager.h"
#include "../EterLib/StateManager.h"
#include "../EterPythonLib/PythonWindow.h"
#include "../GameLib/RaceData.h"
#include "../GameLib/RaceManager.h"
#include "../GameLib/RaceMotionData.h"

#include "PythonApplication.h"
#include "InstanceBase.h"

#include <cmath>

namespace
{
	// the render target's size: twice the card window's view (240x306), drawn scaled into it
	const DWORD TEXTURE_WIDTH = 480;
	const DWORD TEXTURE_HEIGHT = 612;
	const float VIEW_FOV = 30.0f;
	const float VIEW_PITCH = 10.0f;			// the camera a little above the model
	const DWORD MODEL_VID = 0xFFFFFF01;		// its own text tail key, apart from the Yut Nori model (VID 0)
	const int TARGET_INDEX = CRenderTargetManager::RENDER_TARGET_INDEX_ILLUSTRATED;
	const int DIAG_SELECT_LOGS = 8;			// syserr diagnostics: the first selects, then failures only

	struct CDeviceAccess : public CGraphicBase
	{
		static LPDIRECT3DDEVICE9 Device()	{ return ms_lpd3dDevice; }
		static D3DXMATRIX& View()			{ return ms_matView; }
		static D3DXMATRIX& Proj()			{ return ms_matProj; }
		static D3DXMATRIX& InverseView()	{ return ms_matInverseView; }
	};

	// render states set for the model and put back after it (Get/Set: the actor itself uses the
	// one-level Save/Restore of some of them)
	struct SStateValue
	{
		D3DRENDERSTATETYPE eType;
		DWORD dwValue;
		DWORD dwOld;
	};

	class CMonsterModelView
	{
		public:
			CMonsterModelView() : m_pModel(NULL), m_dwRace(0), m_bShow(false), m_bFramed(false), m_fHeight(0.0f),
				m_fRadius(0.0f), m_fZoom(1.0f), m_fLift(0.0f), m_fRotation(0.0f), m_iMotion(-1), m_bOnceMotion(false),
				m_iSelectLogs(0), m_bRenderLogged(false), m_bFailLogged(false), m_bWatchdogLogged(false),
				m_dwShowTime(0), m_dwLastDraw(0)
			{
			}

			void Destroy()
			{
				delete m_pModel;
				m_pModel = NULL;
				m_dwRace = 0;
				m_bFramed = false;
				m_iMotion = -1;
				m_bOnceMotion = false;
			}

			bool Select(DWORD dwRace)
			{
				if (m_pModel && m_dwRace == dwRace)
				{
					Reset();
					return true;
				}
				Destroy();
				if (dwRace == 0xFFFFFFFF)
				{
					// the window's own call: closing, or a card below class 1 (no preview by design)
					if (m_iSelectLogs < DIAG_SELECT_LOGS)
					{
						++m_iSelectLogs;
						TraceError("Mt2009MonsterModel: select none (0xFFFFFFFF: window closed or card class 0)");
					}
					return false;
				}

				CRaceData* pRaceData;
				if (!CRaceManager::Instance().GetRaceDataPointer(dwRace, &pRaceData))
				{
					TraceError("Mt2009MonsterModel: race %u has no race data (npclist / msm) - the card picture", dwRace);
					return false;	// no model in the client: the card picture
				}

				CRenderTargetManager& rkRTMgr = CRenderTargetManager::Instance();
				if (!rkRTMgr.GetRenderTargetTexture(TARGET_INDEX) && !rkRTMgr.CreateA8R8G8B8Texture(TEXTURE_WIDTH, TEXTURE_HEIGHT, TARGET_INDEX))
				{
					TraceError("Mt2009MonsterModel: cannot create the render target %ux%u (index %d)", TEXTURE_WIDTH, TEXTURE_HEIGHT, TARGET_INDEX);
					return false;
				}

				CInstanceBase::SCreateData kCreateData{};
				kCreateData.m_bType = CActorInstance::TYPE_OBJECT;
				kCreateData.m_dwRace = dwRace;
				kCreateData.m_dwVID = MODEL_VID;
				kCreateData.m_dwMovSpd = 100;
				kCreateData.m_dwAtkSpd = 100;

				CInstanceBase* pModel = new CInstanceBase();
				if (!pModel->Create(kCreateData))
				{
					TraceError("Mt2009MonsterModel: race %u - CInstanceBase::Create failed", dwRace);
					delete pModel;
					return false;
				}
				pModel->DetachTextTail();	// a name over a model in no world
				pModel->SetLODLimits(0, 100.0f);
				pModel->SetAlwaysRender(true);
				pModel->NEW_SetPixelPosition(TPixelPosition(0.0f, 0.0f, 0.0f));
				pModel->Refresh(CRaceMotionData::NAME_WAIT, true);

				m_pModel = pModel;
				m_dwRace = dwRace;
				m_bRenderLogged = false;
				m_bFailLogged = false;
				Reset();

				if (m_iSelectLogs < DIAG_SELECT_LOGS)
				{
					++m_iSelectLogs;
					m_pModel->Transform();
					CActorInstance* pActor = m_pModel->GetGraphicThingInstancePtr();
					D3DXVECTOR3 v3Center(0.0f, 0.0f, 0.0f);
					float fRadius = 0.0f;
					const bool bSphere = pActor->GetBoundingSphere(v3Center, fRadius);
					TraceError("Mt2009MonsterModel: select race %u ok - sphere %d center %.1f %.1f %.1f radius %.1f height %.1f, target index %d",
						dwRace, bSphere ? 1 : 0, v3Center.x, v3Center.y, v3Center.z, fRadius, pActor->GetHeight(), TARGET_INDEX);
				}
				return true;
			}

			void Show(bool bShow)
			{
				if (bShow && !m_bShow)
				{
					m_dwShowTime = ELTimer_GetMSec();
					m_bWatchdogLogged = false;
				}
				m_bShow = bShow;
			}

			void Reset()
			{
				m_fZoom = 1.0f;
				m_fLift = 0.0f;
				Rotate(0.0f);
			}

			// the camera looks from -y; a model at rotation 0 faces away from it
			void Rotate(float fDegree)
			{
				m_fRotation = std::fmod(fDegree + 180.0f, 360.0f);
				if (m_pModel)
					m_pModel->SetRotation(m_fRotation);
			}

			void Zoom(bool bIn)
			{
				m_fZoom *= bIn ? 0.96f : 1.04f;
				m_fZoom = m_fZoom < 0.35f ? 0.35f : (m_fZoom > 2.5f ? 2.5f : m_fZoom);
			}

			void Lift(bool bUp)
			{
				m_fLift += bUp ? 0.02f : -0.02f;
				m_fLift = m_fLift < -0.6f ? -0.6f : (m_fLift > 0.6f ? 0.6f : m_fLift);
			}

			// the next motion the race has, played once; then the idle (Animate)
			void NextMotion()
			{
				if (!m_pModel)
					return;
				static const WORD s_awMotions[] =
				{
					CRaceMotionData::NAME_WALK, CRaceMotionData::NAME_RUN, CRaceMotionData::NAME_NORMAL_ATTACK,
					CRaceMotionData::NAME_COMBO_ATTACK_1, CRaceMotionData::NAME_COMBO_ATTACK_2,
					CRaceMotionData::NAME_SPECIAL_1, CRaceMotionData::NAME_SPECIAL_2, CRaceMotionData::NAME_SPECIAL_3,
					CRaceMotionData::NAME_SPAWN, CRaceMotionData::NAME_DAMAGE,
				};
				const int iCount = int(_countof(s_awMotions));
				CRaceData* pRaceData;
				if (!CRaceManager::Instance().GetRaceDataPointer(m_dwRace, &pRaceData))
					return;
				for (int i = 1; i <= iCount; ++i)
				{
					const int iMotion = (m_iMotion + i + iCount) % iCount;
					MOTION_KEY key;
					if (!pRaceData->GetMotionKey(CRaceMotionData::MODE_GENERAL, s_awMotions[iMotion], &key))
						continue;
					m_iMotion = iMotion;
					m_pModel->Refresh(s_awMotions[iMotion], false);
					m_bOnceMotion = true;
					return;
				}
			}

			// the game loop: only a diagnostic - shown, yet no render target window drew it
			void Watchdog()
			{
				if (!m_bShow || !m_pModel || m_bWatchdogLogged)
					return;
				const DWORD dwNow = ELTimer_GetMSec();
				if (dwNow - m_dwShowTime < 3000 || (m_dwLastDraw && dwNow - m_dwLastDraw < 3000))
					return;
				m_bWatchdogLogged = true;
				TraceError("Mt2009MonsterModel: race %u shown for 3 s but no render target window with index %d drew it (wndMgr.SetRenderTarget index? window hidden?)",
					m_dwRace, TARGET_INDEX);
			}

			// the render target window's render (UI pass): the model into the texture, the texture into the window
			void Draw(const RECT& rcWindow, const RECT* pClipRect)
			{
				if (!m_bShow || !m_pModel)
					return;
				m_dwLastDraw = ELTimer_GetMSec();

				const long lWidth = rcWindow.right - rcWindow.left;
				const long lHeight = rcWindow.bottom - rcWindow.top;
				if (lWidth < 8 || lHeight < 8)
				{
					FailOnce("the window is %ldx%ld", lWidth, lHeight);
					return;
				}

				LPDIRECT3DDEVICE9 pDevice = CDeviceAccess::Device();
				if (!pDevice || pDevice->TestCooperativeLevel() != D3D_OK)
					return;

				CRenderTargetManager& rkRTMgr = CRenderTargetManager::Instance();
				CGraphicRenderTargetTexture* pTexture = rkRTMgr.GetRenderTargetTexture(TARGET_INDEX);
				if (!pTexture || !pTexture->GetRenderTargetTexture())
				{
					FailOnce("no render target texture (index %ld)", TARGET_INDEX);
					return;
				}

				Animate();
				CActorInstance* pActor = m_pModel->GetGraphicThingInstancePtr();
				pActor->INSTANCEBASE_Deform();

				const float fAspect = float(lWidth) / float(lHeight);
				float fDistance, fTargetZ;
				Frame(fAspect, fDistance, fTargetZ);

				D3DVIEWPORT9 kOldViewport;
				pDevice->GetViewport(&kOldViewport);
				if (!rkRTMgr.ChangeRenderTarget(TARGET_INDEX))
				{
					FailOnce("ChangeRenderTarget(%ld) failed", TARGET_INDEX);
					return;
				}
				D3DVIEWPORT9 kViewport = { 0, 0, TEXTURE_WIDTH, TEXTURE_HEIGHT, 0.0f, 1.0f };
				pDevice->SetViewport(&kViewport);
				pDevice->Clear(0, NULL, D3DCLEAR_TARGET | D3DCLEAR_ZBUFFER, 0x00000000, 1.0f, 0);

				RenderModel(pDevice, fAspect, fDistance, fTargetZ);
				MarkModelOpaque();

				rkRTMgr.ResetRenderTarget();
				pDevice->SetViewport(&kOldViewport);

				if (!m_bRenderLogged)
				{
					m_bRenderLogged = true;
					TraceError("Mt2009MonsterModel: first draw race %u - window %ld,%ld %ldx%ld, clip %d, distance %.1f target z %.1f radius %.1f height %.1f framed %d, actor shown %d alpha %.2f",
						m_dwRace, rcWindow.left, rcWindow.top, lWidth, lHeight, pClipRect ? 1 : 0, fDistance, fTargetZ, m_fRadius, m_fHeight,
						m_bFramed ? 1 : 0, pActor->isShow() ? 1 : 0, pActor->GetAlphaValue());
				}

				// the texture into the window, as the UI draws
				CPythonGraphic::Instance().SetInterfaceRenderState();
				RECT rcDraw = rcWindow;
				pTexture->SetRenderingRect(&rcDraw);
				STATEMANAGER.SaveTextureStageState(0, D3DTSS_COLORARG1, D3DTA_TEXTURE);
				STATEMANAGER.SaveTextureStageState(0, D3DTSS_COLOROP, D3DTOP_SELECTARG1);
				STATEMANAGER.SaveTextureStageState(0, D3DTSS_ALPHAARG1, D3DTA_TEXTURE);
				STATEMANAGER.SaveTextureStageState(0, D3DTSS_ALPHAOP, D3DTOP_SELECTARG1);
				STATEMANAGER.SaveTextureStageState(1, D3DTSS_COLOROP, D3DTOP_DISABLE);
				STATEMANAGER.SaveTextureStageState(1, D3DTSS_ALPHAOP, D3DTOP_DISABLE);
				STATEMANAGER.SaveSamplerState(0, D3DSAMP_MINFILTER, D3DTEXF_LINEAR);
				STATEMANAGER.SaveSamplerState(0, D3DSAMP_MAGFILTER, D3DTEXF_LINEAR);
				pTexture->Render(const_cast<RECT*>(pClipRect));
				STATEMANAGER.RestoreSamplerState(0, D3DSAMP_MAGFILTER);
				STATEMANAGER.RestoreSamplerState(0, D3DSAMP_MINFILTER);
				STATEMANAGER.RestoreTextureStageState(1, D3DTSS_ALPHAOP);
				STATEMANAGER.RestoreTextureStageState(1, D3DTSS_COLOROP);
				STATEMANAGER.RestoreTextureStageState(0, D3DTSS_ALPHAOP);
				STATEMANAGER.RestoreTextureStageState(0, D3DTSS_ALPHAARG1);
				STATEMANAGER.RestoreTextureStageState(0, D3DTSS_COLOROP);
				STATEMANAGER.RestoreTextureStageState(0, D3DTSS_COLORARG1);
				STATEMANAGER.SetTexture(0, NULL);
			}

		private:
			void FailOnce(const char* c_szFormat, long a = 0, long b = 0)
			{
				if (m_bFailLogged)
					return;
				m_bFailLogged = true;
				char szBuf[256];
				_snprintf(szBuf, sizeof(szBuf), c_szFormat, a, b);
				szBuf[sizeof(szBuf) - 1] = '\0';
				TraceError("Mt2009MonsterModel: race %u not drawn - %s", m_dwRace, szBuf);
			}

			// its motion, once a frame it is drawn
			void Animate()
			{
				m_pModel->Transform();
				m_pModel->GetGraphicThingInstancePtr()->RotationProcess();
				if (m_bOnceMotion && m_pModel->GetGraphicThingInstancePtr()->IsMotionDone())
				{
					m_bOnceMotion = false;
					m_pModel->Refresh(CRaceMotionData::NAME_WAIT, true);
				}
			}

			// framed once, from the idle pose: its motions do not shake the camera; the height fills about
			// 70% of the view, a wide model (its sphere) the width
			void Frame(float fAspect, float& fDistance, float& fTargetZ)
			{
				CActorInstance* pActor = m_pModel->GetGraphicThingInstancePtr();
				if (!m_bFramed)
				{
					D3DXVECTOR3 v3Center(0.0f, 0.0f, 0.0f);
					float fRadius = 0.0f;
					const bool bSphere = pActor->GetBoundingSphere(v3Center, fRadius) && fRadius >= 1.0f;
					float fHeight = pActor->GetHeight();
					if (!bSphere)
						fRadius = fHeight >= 1.0f ? fHeight * 0.6f : 100.0f;
					if (fHeight < 1.0f)
						fHeight = fRadius * 1.6f;
					m_fRadius = fRadius;
					m_fHeight = fHeight;
					m_bFramed = bSphere;
				}
				const float fTanHalf = std::tan(D3DXToRadian(VIEW_FOV) / 2.0f);
				fDistance = m_fHeight * 0.72f / fTanHalf;
				const float fWide = m_fRadius * 0.55f / (fTanHalf * fAspect);
				if (fWide > fDistance)
					fDistance = fWide;
				fDistance *= m_fZoom;
				fTargetZ = m_fHeight * (0.45f + m_fLift);
			}

			// own view/projection (right-handed, as the game camera), light and states; all put back
			void RenderModel(LPDIRECT3DDEVICE9 pDevice, float fAspect, float fDistance, float fTargetZ)
			{
				const float fPitch = D3DXToRadian(VIEW_PITCH);
				const D3DXVECTOR3 v3Target(0.0f, 0.0f, fTargetZ);
				const D3DXVECTOR3 v3Eye(0.0f, -fDistance * std::cos(fPitch), fTargetZ + fDistance * std::sin(fPitch));
				const D3DXVECTOR3 v3Up(0.0f, 0.0f, 1.0f);
				D3DXMATRIX matView, matProj;
				D3DXMatrixLookAtRH(&matView, &v3Eye, &v3Target, &v3Up);
				D3DXMatrixPerspectiveFovRH(&matProj, D3DXToRadian(VIEW_FOV), fAspect, 10.0f, fDistance * 4.0f + 2000.0f);

				const D3DXMATRIX matOldView = CDeviceAccess::View();
				const D3DXMATRIX matOldProj = CDeviceAccess::Proj();
				const D3DXMATRIX matOldInverseView = CDeviceAccess::InverseView();
				D3DXMATRIX matOldViewT, matOldProjT, matOldWorldT;
				STATEMANAGER.GetTransform(D3DTS_VIEW, &matOldViewT);
				STATEMANAGER.GetTransform(D3DTS_PROJECTION, &matOldProjT);
				STATEMANAGER.GetTransform(D3DTS_WORLD, &matOldWorldT);

				CDeviceAccess::View() = matView;
				CDeviceAccess::Proj() = matProj;
				D3DXMatrixInverse(&CDeviceAccess::InverseView(), NULL, &matView);
				STATEMANAGER.SetTransform(D3DTS_VIEW, &matView);
				STATEMANAGER.SetTransform(D3DTS_PROJECTION, &matProj);

				// a light from the camera, as Digi Rasta's view
				D3DLIGHT9 kOldLight;
				STATEMANAGER.GetLight(0, &kOldLight);
				BOOL bOldLight = FALSE;
				pDevice->GetLightEnable(0, &bOldLight);
				D3DLIGHT9 kLight;
				ZeroMemory(&kLight, sizeof(kLight));
				kLight.Type = D3DLIGHT_DIRECTIONAL;
				kLight.Diffuse = D3DXCOLOR(1.0f, 1.0f, 1.0f, 1.0f);
				kLight.Ambient = D3DXCOLOR(0.6f, 0.6f, 0.6f, 1.0f);
				const D3DXVECTOR3 v3Sight = v3Target - v3Eye;
				D3DXVec3Normalize((D3DXVECTOR3*)&kLight.Direction, &v3Sight);
				STATEMANAGER.SetLight(0, &kLight);
				pDevice->LightEnable(0, TRUE);

				D3DMATERIAL9 kOldMaterial;
				STATEMANAGER.GetMaterial(&kOldMaterial);
				D3DMATERIAL9 kMaterial;
				ZeroMemory(&kMaterial, sizeof(kMaterial));
				kMaterial.Diffuse = D3DXCOLOR(1.0f, 1.0f, 1.0f, 1.0f);
				kMaterial.Ambient = D3DXCOLOR(1.0f, 1.0f, 1.0f, 1.0f);
				STATEMANAGER.SetMaterial(&kMaterial);

				SStateValue akStates[] =
				{
					{ D3DRS_LIGHTING, TRUE, 0 },
					{ D3DRS_ZENABLE, TRUE, 0 },
					{ D3DRS_ZWRITEENABLE, TRUE, 0 },
					{ D3DRS_ZFUNC, D3DCMP_LESSEQUAL, 0 },
					{ D3DRS_ALPHABLENDENABLE, FALSE, 0 },
					{ D3DRS_ALPHATESTENABLE, FALSE, 0 },
					{ D3DRS_FOGENABLE, FALSE, 0 },
					{ D3DRS_STENCILENABLE, FALSE, 0 },
					{ D3DRS_AMBIENT, 0xff999999, 0 },
					{ D3DRS_COLORWRITEENABLE, D3DCOLORWRITEENABLE_RED | D3DCOLORWRITEENABLE_GREEN | D3DCOLORWRITEENABLE_BLUE | D3DCOLORWRITEENABLE_ALPHA, 0 },
				};
				const int iStates = int(_countof(akStates));
				for (int i = 0; i < iStates; ++i)
				{
					STATEMANAGER.GetRenderState(akStates[i].eType, &akStates[i].dwOld);
					STATEMANAGER.SetRenderState(akStates[i].eType, akStates[i].dwValue);
				}
				DWORD dwOldMin, dwOldMag, dwOldMip;
				STATEMANAGER.GetSamplerState(0, D3DSAMP_MINFILTER, &dwOldMin);
				STATEMANAGER.GetSamplerState(0, D3DSAMP_MAGFILTER, &dwOldMag);
				STATEMANAGER.GetSamplerState(0, D3DSAMP_MIPFILTER, &dwOldMip);
				STATEMANAGER.SetSamplerState(0, D3DSAMP_MINFILTER, D3DTEXF_LINEAR);
				STATEMANAGER.SetSamplerState(0, D3DSAMP_MAGFILTER, D3DTEXF_LINEAR);
				STATEMANAGER.SetSamplerState(0, D3DSAMP_MIPFILTER, D3DTEXF_LINEAR);
				STATEMANAGER.SetTexture(1, NULL);

				m_pModel->Render();

				STATEMANAGER.SetSamplerState(0, D3DSAMP_MIPFILTER, dwOldMip);
				STATEMANAGER.SetSamplerState(0, D3DSAMP_MAGFILTER, dwOldMag);
				STATEMANAGER.SetSamplerState(0, D3DSAMP_MINFILTER, dwOldMin);
				for (int i = iStates - 1; i >= 0; --i)
					STATEMANAGER.SetRenderState(akStates[i].eType, akStates[i].dwOld);
				STATEMANAGER.SetMaterial(&kOldMaterial);
				STATEMANAGER.SetLight(0, &kOldLight);
				pDevice->LightEnable(0, bOldLight);

				STATEMANAGER.SetTransform(D3DTS_WORLD, &matOldWorldT);
				STATEMANAGER.SetTransform(D3DTS_PROJECTION, &matOldProjT);
				STATEMANAGER.SetTransform(D3DTS_VIEW, &matOldViewT);
				CDeviceAccess::View() = matOldView;
				CDeviceAccess::Proj() = matOldProj;
				CDeviceAccess::InverseView() = matOldInverseView;
			}

			// The model's alpha is its textures' (cut-out masks, not how solid it is): the texture shown in the
			// window would let the board through the model. Every pixel the model drew (depth under the far
			// plane) gets alpha 1, the cleared rest keeps 0 - a full quad near the far plane, depth test GREATER,
			// writing alpha only.
			void MarkModelOpaque()
			{
				D3DXMATRIX matOrtho, matIdentity;
				D3DXMatrixOrthoOffCenterLH(&matOrtho, 0.0f, float(TEXTURE_WIDTH), float(TEXTURE_HEIGHT), 0.0f, 0.0f, 1.0f);
				D3DXMatrixIdentity(&matIdentity);
				STATEMANAGER.SaveTransform(D3DTS_PROJECTION, &matOrtho);
				STATEMANAGER.SaveTransform(D3DTS_VIEW, &matIdentity);
				STATEMANAGER.SaveTransform(D3DTS_WORLD, &matIdentity);
				STATEMANAGER.SaveRenderState(D3DRS_LIGHTING, FALSE);
				STATEMANAGER.SaveRenderState(D3DRS_ZENABLE, TRUE);
				STATEMANAGER.SaveRenderState(D3DRS_ZWRITEENABLE, FALSE);
				STATEMANAGER.SaveRenderState(D3DRS_ZFUNC, D3DCMP_GREATER);
				STATEMANAGER.SaveRenderState(D3DRS_ALPHABLENDENABLE, FALSE);
				STATEMANAGER.SaveRenderState(D3DRS_ALPHATESTENABLE, FALSE);
				STATEMANAGER.SaveRenderState(D3DRS_FOGENABLE, FALSE);
				STATEMANAGER.SaveRenderState(D3DRS_CULLMODE, D3DCULL_NONE);
				STATEMANAGER.SaveRenderState(D3DRS_COLORWRITEENABLE, D3DCOLORWRITEENABLE_ALPHA);
				STATEMANAGER.SetTexture(0, NULL);
				STATEMANAGER.SetTexture(1, NULL);
				STATEMANAGER.SaveTextureStageState(0, D3DTSS_COLOROP, D3DTOP_SELECTARG1);
				STATEMANAGER.SaveTextureStageState(0, D3DTSS_COLORARG1, D3DTA_DIFFUSE);
				STATEMANAGER.SaveTextureStageState(0, D3DTSS_ALPHAOP, D3DTOP_SELECTARG1);
				STATEMANAGER.SaveTextureStageState(0, D3DTSS_ALPHAARG1, D3DTA_DIFFUSE);
				STATEMANAGER.SaveTextureStageState(1, D3DTSS_COLOROP, D3DTOP_DISABLE);
				STATEMANAGER.SaveTextureStageState(1, D3DTSS_ALPHAOP, D3DTOP_DISABLE);

				CPythonGraphic::Instance().SetDiffuseColor(1.0f, 1.0f, 1.0f, 1.0f);
				CPythonGraphic::Instance().RenderBar2d(0.0f, 0.0f, float(TEXTURE_WIDTH) + 1.0f, float(TEXTURE_HEIGHT) + 1.0f, 0.9999f);

				STATEMANAGER.RestoreTextureStageState(1, D3DTSS_ALPHAOP);
				STATEMANAGER.RestoreTextureStageState(1, D3DTSS_COLOROP);
				STATEMANAGER.RestoreTextureStageState(0, D3DTSS_ALPHAARG1);
				STATEMANAGER.RestoreTextureStageState(0, D3DTSS_ALPHAOP);
				STATEMANAGER.RestoreTextureStageState(0, D3DTSS_COLORARG1);
				STATEMANAGER.RestoreTextureStageState(0, D3DTSS_COLOROP);
				STATEMANAGER.RestoreRenderState(D3DRS_COLORWRITEENABLE);
				STATEMANAGER.RestoreRenderState(D3DRS_CULLMODE);
				STATEMANAGER.RestoreRenderState(D3DRS_FOGENABLE);
				STATEMANAGER.RestoreRenderState(D3DRS_ALPHATESTENABLE);
				STATEMANAGER.RestoreRenderState(D3DRS_ALPHABLENDENABLE);
				STATEMANAGER.RestoreRenderState(D3DRS_ZFUNC);
				STATEMANAGER.RestoreRenderState(D3DRS_ZWRITEENABLE);
				STATEMANAGER.RestoreRenderState(D3DRS_ZENABLE);
				STATEMANAGER.RestoreRenderState(D3DRS_LIGHTING);
				STATEMANAGER.RestoreTransform(D3DTS_WORLD);
				STATEMANAGER.RestoreTransform(D3DTS_VIEW);
				STATEMANAGER.RestoreTransform(D3DTS_PROJECTION);
			}

			CInstanceBase* m_pModel;
			DWORD m_dwRace;
			bool m_bShow;
			bool m_bFramed;
			float m_fHeight;
			float m_fRadius;
			float m_fZoom;
			float m_fLift;
			float m_fRotation;
			int m_iMotion;
			bool m_bOnceMotion;
			int m_iSelectLogs;
			bool m_bRenderLogged;
			bool m_bFailLogged;
			bool m_bWatchdogLogged;
			DWORD m_dwShowTime;
			DWORD m_dwLastDraw;
	};

	CMonsterModelView s_kView;

	// UI::CRenderTarget's render hook: the Monster Cards' index is drawn here (nothing while hidden)
	bool RenderTargetHook(int iIndex, const RECT& rcWindow, const RECT* pClipRect)
	{
		if (iIndex != TARGET_INDEX)
			return false;
		s_kView.Draw(rcWindow, pClipRect);
		return true;
	}

	PyObject* playerMt2009ModelShow(PyObject* poSelf, PyObject* poArgs)
	{
		int iShow;
		if (!PyTuple_GetInteger(poArgs, 0, &iShow))
			return Py_BuildException();
		s_kView.Show(iShow != 0);
		return Py_BuildNone();
	}

	PyObject* playerMt2009ModelSelect(PyObject* poSelf, PyObject* poArgs)
	{
		unsigned long ulRace;
		if (!PyTuple_GetUnsignedLong(poArgs, 0, &ulRace))
			return Py_BuildException();
		return Py_BuildValue("i", s_kView.Select(DWORD(ulRace)) ? 1 : 0);
	}

	PyObject* playerMt2009ModelRotation(PyObject* poSelf, PyObject* poArgs)
	{
		float fDegree;
		if (!PyTuple_GetFloat(poArgs, 0, &fDegree))
			return Py_BuildException();
		s_kView.Rotate(fDegree);
		return Py_BuildNone();
	}

	PyObject* playerMt2009ModelZoom(PyObject* poSelf, PyObject* poArgs)
	{
		int iIn;
		if (!PyTuple_GetInteger(poArgs, 0, &iIn))
			return Py_BuildException();
		s_kView.Zoom(iIn != 0);
		return Py_BuildNone();
	}

	PyObject* playerMt2009ModelUpDown(PyObject* poSelf, PyObject* poArgs)
	{
		int iUp;
		if (!PyTuple_GetInteger(poArgs, 0, &iUp))
			return Py_BuildException();
		s_kView.Lift(iUp != 0);
		return Py_BuildNone();
	}

	PyObject* playerMt2009ModelReset(PyObject* poSelf, PyObject* poArgs)
	{
		s_kView.Reset();
		return Py_BuildNone();
	}

	PyObject* playerMt2009ModelMotion(PyObject* poSelf, PyObject* poArgs)
	{
		s_kView.NextMotion();
		return Py_BuildNone();
	}
}

// PythonApplication.cpp: the game loop (a diagnostic only; the model is drawn by its window) and the end.
void Mt2009MonsterModel_Update()	{ s_kView.Watchdog(); }
void Mt2009MonsterModel_Destroy()	{ s_kView.Destroy(); }

// UserInterface.cpp (RunMainScript's module init).
void Mt2009MonsterModel_RegisterPython()
{
	static PyMethodDef s_playerMethods[] =
	{
		{ "Mt2009ModelShow",		playerMt2009ModelShow,		METH_VARARGS, NULL },
		{ "Mt2009ModelSelect",		playerMt2009ModelSelect,	METH_VARARGS, NULL },
		{ "Mt2009ModelRotation",	playerMt2009ModelRotation,	METH_VARARGS, NULL },
		{ "Mt2009ModelZoom",		playerMt2009ModelZoom,		METH_VARARGS, NULL },
		{ "Mt2009ModelUpDown",		playerMt2009ModelUpDown,	METH_VARARGS, NULL },
		{ "Mt2009ModelReset",		playerMt2009ModelReset,		METH_VARARGS, NULL },
		{ "Mt2009ModelMotion",		playerMt2009ModelMotion,	METH_VARARGS, NULL },
		{ NULL, NULL, 0, NULL },
	};
	UI::CRenderTarget::SetRenderHook(&RenderTargetHook);

	PyObject* poModule = PyImport_AddModule("player");	// borrowed; initPlayer adds to the same module
	if (!poModule)
		return;
	for (PyMethodDef* p = s_playerMethods; p->ml_name; ++p)
		PyModule_AddObject(poModule, p->ml_name, PyCFunction_New(p, NULL));
}
#else
void Mt2009MonsterModel_RegisterPython() {}
#endif
