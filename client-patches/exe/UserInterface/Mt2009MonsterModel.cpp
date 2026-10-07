/**
* MT2009_PLUS_MONSTER_CARD_MODEL_V1 - the Monster Cards' 3D preview (Autor: Digi Rasta: the idea and the python
* API player.Mt2009Model* of his nowy-system 0.28 exe, Mt2009Window.cpp; root/monstercard.py calls it).
* Our own code on our render target infrastructure (the Owsap/Yut Nori port: CRenderTargetManager,
* UI::CRenderTarget, CInstanceBase as in PythonYutnoriManager.cpp) - none of his render-to-texture code.
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
#include "../EterLib/RenderTargetManager.h"
#include "../EterLib/StateManager.h"
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

	class CMonsterModelView
	{
		public:
			CMonsterModelView() : m_pModel(NULL), m_dwRace(0), m_bShow(false), m_bFramed(false), m_fHeight(0.0f),
				m_fRadius(0.0f), m_fZoom(1.0f), m_fLift(0.0f), m_fRotation(0.0f), m_iMotion(-1), m_bOnceMotion(false)
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
					return false;

				CRaceData* pRaceData;
				if (!CRaceManager::Instance().GetRaceDataPointer(dwRace, &pRaceData))
					return false;	// no model in the client: the card picture

				CRenderTargetManager& rkRTMgr = CRenderTargetManager::Instance();
				if (!rkRTMgr.GetRenderTargetTexture(TARGET_INDEX) && !rkRTMgr.CreateA8R8G8B8Texture(TEXTURE_WIDTH, TEXTURE_HEIGHT, TARGET_INDEX))
				{
					TraceError("Mt2009MonsterModel: cannot create the render target %ux%u", TEXTURE_WIDTH, TEXTURE_HEIGHT);
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
				Reset();
				return true;
			}

			void Show(bool bShow)
			{
				m_bShow = bShow;
				if (!bShow)
					Clear();
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

			// the next motion the race has, played once; then the idle (Update)
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

			void Update()
			{
				if (!m_bShow || !m_pModel)
					return;
				m_pModel->Transform();
				m_pModel->GetGraphicThingInstancePtr()->RotationProcess();
				if (m_bOnceMotion && m_pModel->GetGraphicThingInstancePtr()->IsMotionDone())
				{
					m_bOnceMotion = false;
					m_pModel->Refresh(CRaceMotionData::NAME_WAIT, true);
				}
			}

			void Deform()
			{
				if (m_bShow && m_pModel)
					m_pModel->Deform();
			}

			void Render()
			{
				if (!m_bShow || !m_pModel)
					return;

				CRenderTargetManager& rkRTMgr = CRenderTargetManager::Instance();
				RECT rcView;
				if (!rkRTMgr.GetRenderTargetRect(TARGET_INDEX, &rcView))
					return;
				const long lWidth = rcView.right - rcView.left;
				const long lHeight = rcView.bottom - rcView.top;
				if (lWidth <= 0 || lHeight <= 0)
					return;
				const float fAspect = float(lWidth) / float(lHeight);

				CActorInstance* pActor = m_pModel->GetGraphicThingInstancePtr();
				if (!m_bFramed)
				{
					// framed once, from the idle pose: its motions do not shake the camera
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

				// the height fills about 70% of the view, a wide model (its sphere) the width
				const float fTanHalf = std::tan(D3DXToRadian(VIEW_FOV) / 2.0f);
				float fDistance = m_fHeight * 0.72f / fTanHalf;
				const float fWide = m_fRadius * 0.55f / (fTanHalf * fAspect);
				if (fWide > fDistance)
					fDistance = fWide;
				fDistance *= m_fZoom;
				const float fTargetZ = m_fHeight * (0.45f + m_fLift);

				if (!rkRTMgr.ChangeRenderTarget(TARGET_INDEX))
					return;
				rkRTMgr.ClearRenderTarget(0x00000000);

				CPythonGraphic& rkGraphic = CPythonGraphic::Instance();
				rkGraphic.ClearDepthBuffer();
				const float fOldFov = rkGraphic.GetFOV();
				const float fOldAspect = rkGraphic.GetAspect();
				const float fOldNear = rkGraphic.GetNearY();
				const float fOldFar = rkGraphic.GetFarY();
				const DWORD dwFog = STATEMANAGER.GetRenderState(D3DRS_FOGENABLE);
				STATEMANAGER.SetRenderState(D3DRS_FOGENABLE, FALSE);

				CCameraManager::Instance().SetCurrentCamera(CCameraManager::DEFAULT_MONSTER_MODEL_CAMERA);
				rkGraphic.PushState();
				rkGraphic.SetPositionCamera(0.0f, 0.0f, fTargetZ, fDistance, VIEW_PITCH, 0.0f);
				rkGraphic.SetPerspective(VIEW_FOV, fAspect, 10.0f, fDistance * 4.0f + 2000.0f);

				m_pModel->Render();
				MarkModelOpaque();

				CCameraManager::Instance().ResetToPreviousCamera();
				rkGraphic.PopState();
				rkGraphic.SetPerspective(fOldFov, fOldAspect, fOldNear, fOldFar);
				rkRTMgr.ResetRenderTarget();
				STATEMANAGER.SetRenderState(D3DRS_FOGENABLE, dwFog);
			}

		private:
			void Clear()
			{
				CRenderTargetManager& rkRTMgr = CRenderTargetManager::Instance();
				if (!rkRTMgr.ChangeRenderTarget(TARGET_INDEX))
					return;
				rkRTMgr.ClearRenderTarget(0x00000000);
				rkRTMgr.ResetRenderTarget();
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
				STATEMANAGER.SaveRenderState(D3DRS_CULLMODE, D3DCULL_NONE);
				STATEMANAGER.SaveRenderState(D3DRS_COLORWRITEENABLE, D3DCOLORWRITEENABLE_ALPHA);
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
	};

	CMonsterModelView s_kView;

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

// PythonApplication.cpp: the game loop (next to the Yut Nori model) and the end.
void Mt2009MonsterModel_Update()	{ s_kView.Update(); }
void Mt2009MonsterModel_Deform()	{ s_kView.Deform(); }
void Mt2009MonsterModel_Render()	{ s_kView.Render(); }
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
	PyObject* poModule = PyImport_AddModule("player");	// borrowed; initPlayer adds to the same module
	if (!poModule)
		return;
	for (PyMethodDef* p = s_playerMethods; p->ml_name; ++p)
		PyModule_AddObject(poModule, p->ml_name, PyCFunction_New(p, NULL));
}
#else
void Mt2009MonsterModel_RegisterPython() {}
#endif
