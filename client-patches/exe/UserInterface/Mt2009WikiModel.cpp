/**
* MT2009_PLUS_WIKI_V1 - the 3D previews of the in-game wiki (root uiwiki.py / wikiui.py, the owner's Valiant2 wiki
* package) and of the item tooltip (root uitooltip.py, MT2009_PLUS_TOOLTIP_MODEL_PREVIEW_V1, the owner's "Render Target
* 2.0" package): python module "renderTarget" with the Render Target 2.0 / Valiant2 names, many views at once.
*
* Built on our own render target path (Mt2009MonsterModel.cpp, the Monster Cards): every view is drawn by its window
* (UI::CRenderTarget's render hook, chained before the Titles' and the Monster Cards' hooks) - the model into the view's
* own CRenderTargetManager texture (index >= CRenderTargetManager::RENDER_TARGET_INDEX_MT2009_FREE, device-reset safe),
* then the texture into the window. A character race (0-7) is a TYPE_PC instance with its parts (armour / costume,
* weapon / weapon skin, hair costume, sash, aura - CInstanceBase::Create + SetAura); any other race (a monster, a
* mount, a pet) a TYPE_OBJECT one, as the Monster Cards'. The effects attached to the model (refine glow +7.., the
* shining table, the sash and aura effects - the "RenderTarget_Shining" part) are drawn with it through
* CActorInstance::Mt2009RenderAttachingEffects under the view's own frustum.
*
*   renderTarget.GetFreeIndex(lo, hi)            a free view number (lo..hi, at least RENDER_TARGET_INDEX_MT2009_FREE)
*   renderTarget.Destroy(i)                      the view and its texture gone
*   renderTarget.SelectModel(i, race)            the model of a race (parts cleared); 1 / 0 (no race data)
*   renderTarget.SetModel(i, race, armour, weapon, hairItem, sash, aura)   all at once (item vnums, 0 = none); 1 / 0
*   renderTarget.SetArmor(i, vnum) SetWeapon(i, vnum) SetHair(i, vnum[, isValue]) SetAcce(i, vnum) SetAura(i, vnum)
*   renderTarget.SetVisibility(i, show)  IsShow(i)  ResetModel(i)
*   renderTarget.SetBackground(i, image)         drawn into the view behind the model ("" = none, the board shows)
*   renderTarget.SetRotation(i, auto)  Rotate(i, degrees)  Zoom(i, in)  UpDown(i, up)  ResetView(i)  Motion(i)
*   renderTarget.SetEffect(i)                    the refine glow again (Render Target 2.0's ChangeEffect)
*   app.ENABLE_RENDER_TARGET_WIKI = 1
*
* A hair costume item gives its hair number (value 3) unless isValue says the number itself is given. A view no
* window draws costs nothing but the model in memory.
**/

#include "StdAfx.h"

#if defined(ENABLE_MT2009_WIKI) && defined(RENDER_TARGET)
#include "../EterLib/Camera.h"
#include "../EterLib/GrpBase.h"
#include "../EterLib/GrpScreen.h"
#include "../EterLib/GrpImageInstance.h"
#include "../EterLib/ResourceManager.h"
#include "../EterLib/RenderTargetManager.h"
#include "../EterLib/StateManager.h"
#include "../EterPythonLib/PythonWindow.h"
#include "../GameLib/RaceData.h"
#include "../GameLib/RaceManager.h"
#include "../GameLib/RaceMotionData.h"
#include "../GameLib/ItemManager.h"

#include "PythonApplication.h"
#include "InstanceBase.h"

#include <cmath>
#include <map>
#include <string>

namespace
{
	const float VIEW_FOV = 30.0f;
	const float VIEW_PITCH = 8.0f;
	const DWORD MODEL_VID_BASE = 0xFFFFE000;	// own text tail keys, apart from the Monster Cards' (0xFFFFFF01)
	const DWORD TEXTURE_MAX = 1024;
	const DWORD PLAYER_RACE_MAX = 8;

	struct CDeviceAccess : public CGraphicBase
	{
		static LPDIRECT3DDEVICE9 Device()	{ return ms_lpd3dDevice; }
		static D3DXMATRIX& View()			{ return ms_matView; }
		static D3DXMATRIX& Proj()			{ return ms_matProj; }
		static D3DXMATRIX& InverseView()	{ return ms_matInverseView; }
	};

	struct SStateValue
	{
		D3DRENDERSTATETYPE eType;
		DWORD dwValue;
		DWORD dwOld;
	};

	CGraphicImage* LoadImage(const std::string& c_rPath)
	{
		if (c_rPath.empty())
			return NULL;
		CResource* pRes = CResourceManager::Instance().GetResourcePointer(c_rPath.c_str());
		if (!pRes || !pRes->IsType(CGraphicImage::Type()))
			return NULL;
		return static_cast<CGraphicImage*>(pRes);
	}

	class CWikiModelView
	{
		public:
			CWikiModelView(int iIndex) : m_iIndex(iIndex), m_pModel(NULL), m_dwRace(0xFFFFFFFF), m_dwArmor(0),
				m_dwWeapon(0), m_dwHair(0), m_dwAcce(0), m_dwAura(0), m_bShow(true), m_bAutoRotate(true),
				m_bFramed(false), m_fHeight(0.0f), m_fRadius(0.0f), m_fZoom(1.0f), m_fLift(0.0f), m_fRotation(0.0f),
				m_iMotion(-1), m_bOnceMotion(false), m_dwLastTime(0), m_dwTexW(0), m_dwTexH(0), m_pkBackground(NULL),
				m_bDrawLogged(false)
			{
			}

			~CWikiModelView()
			{
				DestroyModel();
				if (m_pkBackground)
					CGraphicImageInstance::Delete(m_pkBackground);
				m_pkBackground = NULL;
				if (m_dwTexW)
					CRenderTargetManager::Instance().RemoveRenderTargetTexture(m_iIndex);
			}

			void DestroyModel()
			{
				delete m_pModel;
				m_pModel = NULL;
				m_bFramed = false;
				m_iMotion = -1;
				m_bOnceMotion = false;
			}

			void Reset()
			{
				DestroyModel();
				m_dwRace = 0xFFFFFFFF;
				m_dwArmor = m_dwWeapon = m_dwHair = m_dwAcce = m_dwAura = 0;
			}

			bool Select(DWORD dwRace)
			{
				m_dwArmor = m_dwWeapon = m_dwHair = m_dwAcce = m_dwAura = 0;
				m_dwRace = dwRace;
				ResetView();
				return Build();
			}

			bool SetAll(DWORD dwRace, DWORD dwArmor, DWORD dwWeapon, DWORD dwHair, DWORD dwAcce, DWORD dwAura)
			{
				if (m_pModel && dwRace == m_dwRace && dwArmor == m_dwArmor && dwWeapon == m_dwWeapon && dwHair == m_dwHair &&
						dwAcce == m_dwAcce && dwAura == m_dwAura)
					return true;
				const bool bNewRace = dwRace != m_dwRace;
				m_dwRace = dwRace;
				m_dwArmor = dwArmor;
				m_dwWeapon = dwWeapon;
				m_dwHair = dwHair;
				m_dwAcce = dwAcce;
				m_dwAura = dwAura;
				if (bNewRace)
					ResetView();
				return Build();
			}

			void SetArmor(DWORD dwVnum)		{ if (m_dwArmor != dwVnum) { m_dwArmor = dwVnum; Build(); } }
			void SetWeapon(DWORD dwVnum)	{ if (m_dwWeapon != dwVnum) { m_dwWeapon = dwVnum; Build(); } }
			void SetHairValue(DWORD dwHair)	{ if (m_dwHair != dwHair) { m_dwHair = dwHair; Build(); } }
			void SetAcce(DWORD dwVnum)		{ if (m_dwAcce != dwVnum) { m_dwAcce = dwVnum; Build(); } }
			void SetAura(DWORD dwVnum)		{ if (m_dwAura != dwVnum) { m_dwAura = dwVnum; Build(); } }
			void Rebuild()					{ Build(); }

			void Show(bool bShow)			{ m_bShow = bShow; }
			bool IsShow() const				{ return m_bShow; }
			void SetAutoRotate(bool bOn)	{ m_bAutoRotate = bOn; }

			void SetBackground(const char* c_szPath)
			{
				if (m_pkBackground)
					CGraphicImageInstance::Delete(m_pkBackground);
				m_pkBackground = NULL;
				CGraphicImage* pImage = LoadImage(c_szPath ? c_szPath : "");
				if (!pImage)
					return;
				m_pkBackground = CGraphicImageInstance::New();
				m_pkBackground->SetImagePointer(pImage);
			}

			void ResetView()
			{
				m_fZoom = 1.0f;
				m_fLift = 0.0f;
				Rotate(0.0f);
			}

			// the camera looks from -y; a model at rotation 0 faces away from it
			void Rotate(float fDegree)
			{
				m_fRotation = std::fmod(fDegree + 180.0f, 360.0f);
				if (m_fRotation < 0.0f)
					m_fRotation += 360.0f;
				if (m_pModel)
					m_pModel->SetRotation(m_fRotation);
			}

			void Turn(float fDegree)		{ Rotate(m_fRotation - 180.0f + fDegree); }

			void Zoom(bool bIn)
			{
				m_fZoom *= bIn ? 0.92f : 1.08f;
				m_fZoom = m_fZoom < 0.35f ? 0.35f : (m_fZoom > 2.5f ? 2.5f : m_fZoom);
			}

			void Lift(bool bUp)
			{
				m_fLift += bUp ? 0.03f : -0.03f;
				m_fLift = m_fLift < -0.6f ? -0.6f : (m_fLift > 0.6f ? 0.6f : m_fLift);
			}

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
				const WORD wMode = m_pModel->GetGraphicThingInstancePtr()->GetMotionMode();
				for (int i = 1; i <= iCount; ++i)
				{
					const int iMotion = (m_iMotion + i + iCount) % iCount;
					MOTION_KEY key;
					if (!pRaceData->GetMotionKey(wMode, s_awMotions[iMotion], &key) &&
							!pRaceData->GetMotionKey(CRaceMotionData::MODE_GENERAL, s_awMotions[iMotion], &key))
						continue;
					m_iMotion = iMotion;
					m_pModel->Refresh(s_awMotions[iMotion], false);
					m_bOnceMotion = true;
					return;
				}
			}

			// the window's render (UI pass): the model into the view's texture, the texture into the window
			void Draw(const RECT& rcWindow, const RECT* pClipRect)
			{
				if (!m_bShow || !m_pModel)
					return;

				const long lWidth = rcWindow.right - rcWindow.left;
				const long lHeight = rcWindow.bottom - rcWindow.top;
				if (lWidth < 8 || lHeight < 8)
					return;

				LPDIRECT3DDEVICE9 pDevice = CDeviceAccess::Device();
				if (!pDevice || pDevice->TestCooperativeLevel() != D3D_OK)
					return;

				if (!EnsureTexture(DWORD(lWidth), DWORD(lHeight)))
					return;
				CRenderTargetManager& rkRTMgr = CRenderTargetManager::Instance();
				CGraphicRenderTargetTexture* pTexture = rkRTMgr.GetRenderTargetTexture(m_iIndex);
				if (!pTexture || !pTexture->GetRenderTargetTexture())
					return;

				Animate();
				CActorInstance* pActor = m_pModel->GetGraphicThingInstancePtr();
				pActor->INSTANCEBASE_Deform();

				const float fAspect = float(lWidth) / float(lHeight);
				float fDistance, fTargetZ;
				Frame(fAspect, fDistance, fTargetZ);

				D3DVIEWPORT9 kOldViewport;
				pDevice->GetViewport(&kOldViewport);
				if (!rkRTMgr.ChangeRenderTarget(m_iIndex))
					return;
				D3DVIEWPORT9 kViewport = { 0, 0, m_dwTexW, m_dwTexH, 0.0f, 1.0f };
				pDevice->SetViewport(&kViewport);
				pDevice->Clear(0, NULL, D3DCLEAR_TARGET | D3DCLEAR_ZBUFFER, 0x00000000, 1.0f, 0);

				const bool bBackground = DrawBackground();
				if (bBackground)	// the picture's quad wrote the depth buffer: the model must not lose to it
					pDevice->Clear(0, NULL, D3DCLEAR_ZBUFFER, 0x00000000, 1.0f, 0);
				RenderModel(pDevice, fAspect, fDistance, fTargetZ);
				if (!bBackground)
					MarkModelOpaque();

				rkRTMgr.ResetRenderTarget();
				pDevice->SetViewport(&kOldViewport);

				if (!m_bDrawLogged)
				{
					m_bDrawLogged = true;
					static int s_iLogs = 0;
					if (s_iLogs++ < 12)
						TraceError("Mt2009WikiModel: view %d race %u (armour %u weapon %u hair %u sash %u aura %u) - window %ldx%ld, texture %ux%u, distance %.1f target z %.1f height %.1f radius %.1f, alpha %.2f, background %d",
							m_iIndex, m_dwRace, m_dwArmor, m_dwWeapon, m_dwHair, m_dwAcce, m_dwAura, lWidth, lHeight, m_dwTexW, m_dwTexH,
							fDistance, fTargetZ, m_fHeight, m_fRadius, pActor->GetAlphaValue(), bBackground ? 1 : 0);
				}

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
			bool IsPlayerRace() const { return m_dwRace < PLAYER_RACE_MAX; }

			bool Build()
			{
				DestroyModel();
				if (m_dwRace == 0xFFFFFFFF)
					return false;

				CRaceData* pRaceData;
				if (!CRaceManager::Instance().GetRaceDataPointer(m_dwRace, &pRaceData))
				{
					TraceError("Mt2009WikiModel: race %u has no race data (npclist / msm)", m_dwRace);
					return false;
				}

				CInstanceBase::SCreateData kCreateData{};
				kCreateData.m_bType = IsPlayerRace() ? CActorInstance::TYPE_PC : CActorInstance::TYPE_OBJECT;
				kCreateData.m_dwRace = m_dwRace;
				kCreateData.m_dwVID = MODEL_VID_BASE + DWORD(m_iIndex & 0xFFF);
				kCreateData.m_dwMovSpd = 100;
				kCreateData.m_dwAtkSpd = 100;
				if (IsPlayerRace())
				{
					kCreateData.m_dwArmor = m_dwArmor;
					kCreateData.m_dwWeapon = m_dwWeapon;
					kCreateData.m_dwHair = m_dwHair;
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
					kCreateData.m_dwAcce = m_dwAcce;
#endif
				}

				CInstanceBase* pModel = new CInstanceBase();
				if (!pModel->Create(kCreateData))
				{
					TraceError("Mt2009WikiModel: race %u - CInstanceBase::Create failed", m_dwRace);
					delete pModel;
					return false;
				}
				pModel->DetachTextTail();
				pModel->SetLODLimits(0, 100.0f);
				pModel->SetAlwaysRender(true);
				// no fade-in (Create blends the alpha in over 0.5 s of the actor's local time - a preview is shown at once)
				pModel->GetGraphicThingInstancePtr()->SetAlphaValue(1.0f);
				pModel->GetGraphicThingInstancePtr()->BlendAlphaValue(1.0f, 0.0f);
				pModel->NEW_SetPixelPosition(TPixelPosition(0.0f, 0.0f, 0.0f));
#ifdef ENABLE_MT2009_AURA
				if (IsPlayerRace() && m_dwAura)
					pModel->SetAura(m_dwAura);
#endif
				pModel->Refresh(CRaceMotionData::NAME_WAIT, true);
				pModel->SetRotation(m_fRotation);
				m_pModel = pModel;
				m_dwLastTime = ELTimer_GetMSec();
				m_bDrawLogged = false;
				return true;
			}

			bool EnsureTexture(DWORD dwWidth, DWORD dwHeight)
			{
				// twice the window, at most TEXTURE_MAX a side (the aspect kept)
				float fScale = 2.0f;
				if (dwWidth * fScale > TEXTURE_MAX)
					fScale = float(TEXTURE_MAX) / float(dwWidth);
				if (dwHeight * fScale > TEXTURE_MAX)
					fScale = float(TEXTURE_MAX) / float(dwHeight);
				const DWORD dwTexW = DWORD(dwWidth * fScale);
				const DWORD dwTexH = DWORD(dwHeight * fScale);
				CRenderTargetManager& rkRTMgr = CRenderTargetManager::Instance();
				if (m_dwTexW == dwTexW && m_dwTexH == dwTexH && rkRTMgr.GetRenderTargetTexture(m_iIndex))
					return true;
				rkRTMgr.RemoveRenderTargetTexture(m_iIndex);
				m_dwTexW = m_dwTexH = 0;
				if (!rkRTMgr.CreateA8R8G8B8Texture(dwTexW, dwTexH, m_iIndex))
				{
					static int s_iLogs = 0;
					if (s_iLogs++ < 4)
						TraceError("Mt2009WikiModel: cannot create the render target %ux%u (index %d)", dwTexW, dwTexH, m_iIndex);
					return false;
				}
				m_dwTexW = dwTexW;
				m_dwTexH = dwTexH;
				return true;
			}

			void Animate()
			{
				const DWORD dwNow = ELTimer_GetMSec();
				if (m_bAutoRotate)
				{
					const float fStep = float(dwNow - m_dwLastTime) * 0.036f;	// a turn in 10 s
					m_fRotation = std::fmod(m_fRotation + fStep, 360.0f);
					m_pModel->SetRotation(m_fRotation);
				}
				m_dwLastTime = dwNow;
				m_pModel->Transform();
				CActorInstance* pActor = m_pModel->GetGraphicThingInstancePtr();
				pActor->RotationProcess();
				pActor->UpdateAttachingInstances();
				if (m_bOnceMotion && pActor->IsMotionDone())
				{
					m_bOnceMotion = false;
					m_pModel->Refresh(CRaceMotionData::NAME_WAIT, true);
				}
			}

			void Frame(float fAspect, float& fDistance, float& fTargetZ)
			{
				CActorInstance* pActor = m_pModel->GetGraphicThingInstancePtr();
				if (!m_bFramed)
				{
					if (IsPlayerRace())
					{
						// a character: always its own size (a sash, a long weapon or a mount part must not shrink it,
						// and its race height - CRaceManager caches the first one - is never asked from here)
						m_fHeight = 190.0f;
						m_fRadius = 120.0f;
						m_bFramed = true;
					}
					else
					{
						D3DXVECTOR3 v3Center(0.0f, 0.0f, 0.0f);
						float fRadius = 0.0f;
						bool bSphere = pActor->GetBoundingSphere(v3Center, fRadius) && fRadius >= 1.0f && fRadius < 5000.0f;
						float fHeight = pActor->GetHeight();
						if (!bSphere)
							fRadius = fHeight >= 1.0f && fHeight < 8000.0f ? fHeight * 0.6f : 120.0f;
						if (fHeight < 1.0f || fHeight > 8000.0f)	// no bound box yet (or none): from the sphere
						{
							fHeight = fRadius * 1.6f;
							bSphere = false;
						}
						m_fRadius = fRadius;
						m_fHeight = fHeight;
						m_bFramed = bSphere;
					}
				}
				const float fTanHalf = std::tan(D3DXToRadian(VIEW_FOV) / 2.0f);
				fDistance = m_fHeight * 0.68f / fTanHalf;
				const float fWide = m_fRadius * 0.55f / (fTanHalf * fAspect);
				if (fWide > fDistance)
					fDistance = fWide;
				fDistance *= m_fZoom;
				fTargetZ = m_fHeight * (0.47f + m_fLift);
			}

			bool DrawBackground()
			{
				if (!m_pkBackground || m_pkBackground->IsEmpty())
					return false;
				D3DXMATRIX matOrtho, matIdentity;
				D3DXMatrixOrthoOffCenterLH(&matOrtho, 0.0f, float(m_dwTexW), float(m_dwTexH), 0.0f, 0.0f, 1.0f);
				D3DXMatrixIdentity(&matIdentity);
				CPythonGraphic::Instance().SetInterfaceRenderState();
				STATEMANAGER.SaveTransform(D3DTS_PROJECTION, &matOrtho);
				STATEMANAGER.SaveTransform(D3DTS_VIEW, &matIdentity);
				STATEMANAGER.SaveTransform(D3DTS_WORLD, &matIdentity);
				const int iW = m_pkBackground->GetWidth(), iH = m_pkBackground->GetHeight();
				m_pkBackground->SetPosition(0.0f, 0.0f);
				m_pkBackground->SetScale(iW > 0 ? float(m_dwTexW) / iW : 1.0f, iH > 0 ? float(m_dwTexH) / iH : 1.0f);
				m_pkBackground->Render();
				STATEMANAGER.RestoreTransform(D3DTS_WORLD);
				STATEMANAGER.RestoreTransform(D3DTS_VIEW);
				STATEMANAGER.RestoreTransform(D3DTS_PROJECTION);
				return true;
			}

			// own view/projection (right-handed, as the game camera), light and states; all put back. The attached
			// effects after the model, under a frustum of this view (their particles test it).
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

				// the effects (refine glow, shining table, sash / aura effects): the particles test CScreen's frustum
				{
					Frustum kOldFrustum = CScreen::GetFrustum();
					D3DXMATRIX matViewProj = matView * matProj;
					CScreen::GetFrustum().BuildViewFrustum(matViewProj);
					DWORD dwOldFog = FALSE, dwOldLighting = FALSE;
					STATEMANAGER.GetRenderState(D3DRS_FOGENABLE, &dwOldFog);
					STATEMANAGER.GetRenderState(D3DRS_LIGHTING, &dwOldLighting);
					STATEMANAGER.SetRenderState(D3DRS_FOGENABLE, FALSE);
					STATEMANAGER.SetRenderState(D3DRS_LIGHTING, FALSE);
					STATEMANAGER.SetTexture(1, NULL);
					D3DXMATRIX matIdentity;
					D3DXMatrixIdentity(&matIdentity);
					STATEMANAGER.SetTransform(D3DTS_WORLD, &matIdentity);
					m_pModel->GetGraphicThingInstancePtr()->Mt2009RenderAttachingEffects();
					STATEMANAGER.SetRenderState(D3DRS_LIGHTING, dwOldLighting);
					STATEMANAGER.SetRenderState(D3DRS_FOGENABLE, dwOldFog);
					CScreen::GetFrustum() = kOldFrustum;
				}

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

			// no background: every pixel the model drew gets alpha 1 (Mt2009MonsterModel.cpp MarkModelOpaque)
			void MarkModelOpaque()
			{
				D3DXMATRIX matOrtho, matIdentity;
				D3DXMatrixOrthoOffCenterLH(&matOrtho, 0.0f, float(m_dwTexW), float(m_dwTexH), 0.0f, 0.0f, 1.0f);
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
				CPythonGraphic::Instance().RenderBar2d(0.0f, 0.0f, float(m_dwTexW) + 1.0f, float(m_dwTexH) + 1.0f, 0.9999f);

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

			int m_iIndex;
			CInstanceBase* m_pModel;
			DWORD m_dwRace;
			DWORD m_dwArmor;
			DWORD m_dwWeapon;
			DWORD m_dwHair;
			DWORD m_dwAcce;
			DWORD m_dwAura;
			bool m_bShow;
			bool m_bAutoRotate;
			bool m_bFramed;
			float m_fHeight;
			float m_fRadius;
			float m_fZoom;
			float m_fLift;
			float m_fRotation;
			int m_iMotion;
			bool m_bOnceMotion;
			DWORD m_dwLastTime;
			DWORD m_dwTexW;
			DWORD m_dwTexH;
			CGraphicImageInstance* m_pkBackground;
			bool m_bDrawLogged;
	};

	typedef std::map<int, CWikiModelView*> TViewMap;
	TViewMap s_kViews;
	UI::CRenderTarget::TRenderHook s_pfnPrevHook = NULL;

	CWikiModelView* GetView(int iIndex, bool bCreate)
	{
		TViewMap::iterator it = s_kViews.find(iIndex);
		if (it != s_kViews.end())
			return it->second;
		if (!bCreate || iIndex < CRenderTargetManager::RENDER_TARGET_INDEX_MT2009_FREE)
			return NULL;
		CWikiModelView* pView = new CWikiModelView(iIndex);
		s_kViews[iIndex] = pView;
		return pView;
	}

	bool RenderTargetHook(int iIndex, const RECT& rcWindow, const RECT* pClipRect)
	{
		CWikiModelView* pView = GetView(iIndex, false);
		if (!pView)
			return s_pfnPrevHook ? s_pfnPrevHook(iIndex, rcWindow, pClipRect) : false;
		pView->Draw(rcWindow, pClipRect);
		return true;
	}

	// a hair costume item -> its hair number (value 3); a number below 1000 is taken as the number itself
	DWORD HairValue(DWORD dwVnum, bool bIsValue)
	{
		if (!dwVnum || bIsValue)
			return dwVnum;
		CItemData* pItemData;
		if (!CItemManager::Instance().GetItemDataPointer(dwVnum, &pItemData))
			return dwVnum < 1000 ? dwVnum : 0;
		return DWORD(pItemData->GetValue(3));
	}

	int ArgIndex(PyObject* poArgs)
	{
		int iIndex = -1;
		PyTuple_GetInteger(poArgs, 0, &iIndex);
		return iIndex;
	}

	DWORD ArgDword(PyObject* poArgs, int iPos)
	{
		int iValue = 0;
		if (!PyTuple_GetInteger(poArgs, iPos, &iValue))
			return 0;
		return iValue < 0 ? 0 : DWORD(iValue);
	}

	PyObject* rtGetFreeIndex(PyObject* poSelf, PyObject* poArgs)
	{
		int iLow = CRenderTargetManager::RENDER_TARGET_INDEX_MT2009_FREE, iHigh = iLow + 100000;
		PyTuple_GetInteger(poArgs, 0, &iLow);
		PyTuple_GetInteger(poArgs, 1, &iHigh);
		if (iLow < CRenderTargetManager::RENDER_TARGET_INDEX_MT2009_FREE)
			iLow = CRenderTargetManager::RENDER_TARGET_INDEX_MT2009_FREE;
		for (int i = iLow; i <= iHigh; ++i)
			if (s_kViews.find(i) == s_kViews.end())
			{
				GetView(i, true);
				return Py_BuildValue("i", i);
			}
		return Py_BuildValue("i", -1);
	}

	PyObject* rtDestroy(PyObject* poSelf, PyObject* poArgs)
	{
		const int iIndex = ArgIndex(poArgs);
		TViewMap::iterator it = s_kViews.find(iIndex);
		if (it != s_kViews.end())
		{
			delete it->second;
			s_kViews.erase(it);
		}
		return Py_BuildNone();
	}

	PyObject* rtSelectModel(PyObject* poSelf, PyObject* poArgs)
	{
		CWikiModelView* pView = GetView(ArgIndex(poArgs), true);
		if (!pView)
			return Py_BuildValue("i", 0);
		return Py_BuildValue("i", pView->Select(ArgDword(poArgs, 1)) ? 1 : 0);
	}

	PyObject* rtSetModel(PyObject* poSelf, PyObject* poArgs)
	{
		CWikiModelView* pView = GetView(ArgIndex(poArgs), true);
		if (!pView)
			return Py_BuildValue("i", 0);
		return Py_BuildValue("i", pView->SetAll(ArgDword(poArgs, 1), ArgDword(poArgs, 2), ArgDword(poArgs, 3),
			HairValue(ArgDword(poArgs, 4), false), ArgDword(poArgs, 5), ArgDword(poArgs, 6)) ? 1 : 0);
	}

	PyObject* rtSetArmor(PyObject* poSelf, PyObject* poArgs)
	{
		if (CWikiModelView* pView = GetView(ArgIndex(poArgs), false))
			pView->SetArmor(ArgDword(poArgs, 1));
		return Py_BuildNone();
	}

	PyObject* rtSetWeapon(PyObject* poSelf, PyObject* poArgs)
	{
		if (CWikiModelView* pView = GetView(ArgIndex(poArgs), false))
			pView->SetWeapon(ArgDword(poArgs, 1));
		return Py_BuildNone();
	}

	PyObject* rtSetHair(PyObject* poSelf, PyObject* poArgs)
	{
		int iIsValue = 0;
		PyTuple_GetInteger(poArgs, 2, &iIsValue);
		if (CWikiModelView* pView = GetView(ArgIndex(poArgs), false))
			pView->SetHairValue(HairValue(ArgDword(poArgs, 1), iIsValue != 0));
		return Py_BuildNone();
	}

	PyObject* rtSetAcce(PyObject* poSelf, PyObject* poArgs)
	{
		if (CWikiModelView* pView = GetView(ArgIndex(poArgs), false))
			pView->SetAcce(ArgDword(poArgs, 1));
		return Py_BuildNone();
	}

	PyObject* rtSetAura(PyObject* poSelf, PyObject* poArgs)
	{
		if (CWikiModelView* pView = GetView(ArgIndex(poArgs), false))
			pView->SetAura(ArgDword(poArgs, 1));
		return Py_BuildNone();
	}

	PyObject* rtSetEffect(PyObject* poSelf, PyObject* poArgs)
	{
		if (CWikiModelView* pView = GetView(ArgIndex(poArgs), false))
			pView->Rebuild();
		return Py_BuildNone();
	}

	PyObject* rtSetVisibility(PyObject* poSelf, PyObject* poArgs)
	{
		int iShow = 1;
		PyTuple_GetInteger(poArgs, 1, &iShow);
		if (CWikiModelView* pView = GetView(ArgIndex(poArgs), false))
			pView->Show(iShow != 0);
		return Py_BuildNone();
	}

	PyObject* rtIsShow(PyObject* poSelf, PyObject* poArgs)
	{
		CWikiModelView* pView = GetView(ArgIndex(poArgs), false);
		return Py_BuildValue("i", pView && pView->IsShow() ? 1 : 0);
	}

	PyObject* rtResetModel(PyObject* poSelf, PyObject* poArgs)
	{
		if (CWikiModelView* pView = GetView(ArgIndex(poArgs), false))
			pView->Reset();
		return Py_BuildNone();
	}

	PyObject* rtSetBackground(PyObject* poSelf, PyObject* poArgs)
	{
		char* szPath = NULL;
		if (!PyTuple_GetString(poArgs, 1, &szPath))
			szPath = NULL;
		if (CWikiModelView* pView = GetView(ArgIndex(poArgs), true))
			pView->SetBackground(szPath);
		return Py_BuildNone();
	}

	PyObject* rtSetRotation(PyObject* poSelf, PyObject* poArgs)
	{
		int iOn = 1;
		PyTuple_GetInteger(poArgs, 1, &iOn);
		if (CWikiModelView* pView = GetView(ArgIndex(poArgs), false))
			pView->SetAutoRotate(iOn != 0);
		return Py_BuildNone();
	}

	PyObject* rtRotate(PyObject* poSelf, PyObject* poArgs)
	{
		float fDegree = 0.0f;
		PyTuple_GetFloat(poArgs, 1, &fDegree);
		if (CWikiModelView* pView = GetView(ArgIndex(poArgs), false))
			pView->Turn(fDegree);
		return Py_BuildNone();
	}

	PyObject* rtZoom(PyObject* poSelf, PyObject* poArgs)
	{
		int iIn = 1;
		PyTuple_GetInteger(poArgs, 1, &iIn);
		if (CWikiModelView* pView = GetView(ArgIndex(poArgs), false))
			pView->Zoom(iIn != 0);
		return Py_BuildNone();
	}

	PyObject* rtUpDown(PyObject* poSelf, PyObject* poArgs)
	{
		int iUp = 1;
		PyTuple_GetInteger(poArgs, 1, &iUp);
		if (CWikiModelView* pView = GetView(ArgIndex(poArgs), false))
			pView->Lift(iUp != 0);
		return Py_BuildNone();
	}

	PyObject* rtResetView(PyObject* poSelf, PyObject* poArgs)
	{
		if (CWikiModelView* pView = GetView(ArgIndex(poArgs), false))
			pView->ResetView();
		return Py_BuildNone();
	}

	PyObject* rtMotion(PyObject* poSelf, PyObject* poArgs)
	{
		if (CWikiModelView* pView = GetView(ArgIndex(poArgs), false))
			pView->NextMotion();
		return Py_BuildNone();
	}
}

// PythonApplication.cpp: the end of the application (before the managers go).
void Mt2009WikiModel_Destroy()
{
	for (TViewMap::iterator it = s_kViews.begin(); it != s_kViews.end(); ++it)
		delete it->second;
	s_kViews.clear();
}

// UserInterface.cpp (RunMainScript's module init) - after the Monster Cards' and the Titles' hooks.
void Mt2009WikiModel_RegisterPython()
{
	static PyMethodDef s_methods[] =
	{
		{ "GetFreeIndex",	rtGetFreeIndex,		METH_VARARGS, NULL },
		{ "Destroy",		rtDestroy,			METH_VARARGS, NULL },
		{ "SelectModel",	rtSelectModel,		METH_VARARGS, NULL },
		{ "SetModel",		rtSetModel,			METH_VARARGS, NULL },
		{ "SetArmor",		rtSetArmor,			METH_VARARGS, NULL },
		{ "SetWeapon",		rtSetWeapon,		METH_VARARGS, NULL },
		{ "SetHair",		rtSetHair,			METH_VARARGS, NULL },
		{ "ChangeHair",		rtSetHair,			METH_VARARGS, NULL },
		{ "SetAcce",		rtSetAcce,			METH_VARARGS, NULL },
		{ "SetAura",		rtSetAura,			METH_VARARGS, NULL },
		{ "SetEffect",		rtSetEffect,		METH_VARARGS, NULL },
		{ "ChangeEffect",	rtSetEffect,		METH_VARARGS, NULL },
		{ "SetVisibility",	rtSetVisibility,	METH_VARARGS, NULL },
		{ "IsShow",			rtIsShow,			METH_VARARGS, NULL },
		{ "ResetModel",		rtResetModel,		METH_VARARGS, NULL },
		{ "SetBackground",	rtSetBackground,	METH_VARARGS, NULL },
		{ "SetRotation",	rtSetRotation,		METH_VARARGS, NULL },
		{ "Rotate",			rtRotate,			METH_VARARGS, NULL },
		{ "Zoom",			rtZoom,				METH_VARARGS, NULL },
		{ "UpDown",			rtUpDown,			METH_VARARGS, NULL },
		{ "ResetView",		rtResetView,		METH_VARARGS, NULL },
		{ "Motion",			rtMotion,			METH_VARARGS, NULL },
		{ NULL, NULL, 0, NULL },
	};
	s_pfnPrevHook = UI::CRenderTarget::GetRenderHook();
	UI::CRenderTarget::SetRenderHook(&RenderTargetHook);
	Py_InitModule("renderTarget", s_methods);
}
#else
void Mt2009WikiModel_RegisterPython() {}
void Mt2009WikiModel_Destroy() {}
#endif
