#include "StdAfx.h"

// MT2009_PLUS_NPC_LOCATION_HELPER_V1 - Lokalizator NPC (Autor: Best Studio): the helper's view of the world map
// (CPythonMiniMap), ported from the package's PythonMiniMap hunks to our exe:
//   * the same atlas image (no "atlas_resize" textures): map-local pixel -> image pixel is x / maxX * imageW, as on
//     the ordinary atlas; the view zooms it (1, 1.5, 2, 2.5, 3; a fit below 1 from python) and pans it inside a
//     viewport (python's window, at least 352x352); everything is clipped to the viewport with a D3D9 scissor rect
//     (this exe has no clip mask);
//   * the atlas of another map (atlasinfo.txt place + locale/<pl>/map/<name>_point.txt marks), the guild areas of the
//     character's map are kept while another map is shown;
//   * the chosen NPC: waypoint + orange mark on the atlas, the arrow effect under the character
//     (d:/ymir work/effect/etc/npc_location/npc_location_direction.mse) until the arrow reaches it (3 m);
//   * the ordinary atlas (helper view off) is drawn exactly as before.
// See client-patches/exe/README.md.

#ifdef ENABLE_NPC_LOCATION_HELPER
#include "../eterLib/StateManager.h"
#include "../EterPack/EterPackManager.h"
#include "../EffectLib/EffectManager.h"
#include "../GameLib/GameUtil.h"

#include "PythonMiniMap.h"
#include "PythonBackground.h"
#include "PythonCharacterManager.h"
#include "PythonGuild.h"
#include "PythonPlayer.h"
#include "PythonNPCLocationHelper.h"

namespace
{
	const float c_afAtlasHelperScaleLevels[] = { 1.0f, 1.5f, 2.0f, 2.5f, 3.0f };
	const int c_iAtlasHelperScaleLevelCount = sizeof(c_afAtlasHelperScaleLevels) / sizeof(c_afAtlasHelperScaleLevels[0]);
	const float c_fAtlasHelperScaleMin = 0.25f;	// python's "whole map fits" scale may go below 1
	const float c_fAtlasHelperScaleMax = 3.0f;

	const char* c_szNPCLocationDirectionEffect = "d:/ymir work/effect/etc/npc_location/npc_location_direction.mse";
	const float c_fNPCLocationDirectionArriveRadius = 300.0f;	// the arrow's head reaches the NPC
	const DWORD c_dwNPCLocationDirectionGraceMS = 400;

	int FindAtlasHelperScaleLevelIndex(float fScale)
	{
		int iBest = 0;
		float fBestDiff = fabsf(c_afAtlasHelperScaleLevels[0] - fScale);
		for (int i = 1; i < c_iAtlasHelperScaleLevelCount; ++i)
		{
			const float fDiff = fabsf(c_afAtlasHelperScaleLevels[i] - fScale);
			if (fDiff < fBestDiff)
			{
				fBestDiff = fDiff;
				iBest = i;
			}
		}
		return iBest;
	}

	float GetNextAtlasHelperScale(float fCurrentScale, bool bScaleUp)
	{
		if (bScaleUp && fCurrentScale < 1.0f - 0.001f)
			return 1.0f;

		const int iIdx = FindAtlasHelperScaleLevelIndex(fCurrentScale);
		if (bScaleUp)
			return c_afAtlasHelperScaleLevels[iIdx < c_iAtlasHelperScaleLevelCount - 1 ? iIdx + 1 : iIdx];
		return c_afAtlasHelperScaleLevels[iIdx > 0 ? iIdx - 1 : iIdx];
	}

	void BuildNPCLocationDirectionEffectMatrix(const TPixelPosition& kPlayerPos, float fTargetX, float fTargetY, D3DXMATRIX* pMat)
	{
		float fAngle = GetDegreeFromPosition2(kPlayerPos.x, kPlayerPos.y, fTargetX, fTargetY);
		fAngle = fmodf(540.0f - fAngle, 360.0f);

		D3DXMatrixRotationYawPitchRoll(pMat, 0.0f, 0.0f, D3DXToRadian(fAngle));
		pMat->_41 = kPlayerPos.x;
		pMat->_42 = -kPlayerPos.y;

		CPythonBackground& rkBG = CPythonBackground::Instance();
		pMat->_43 = rkBG.IsMapOutdoor() ? rkBG.GetHeight(kPlayerPos.x, kPlayerPos.y) : kPlayerPos.z;
	}
}

//////////////////////////////////////////////////////////////////////////////////////////////
// coordinates

void CPythonMiniMap::__MapPosToHelperAtlasImagePos(float fMapX, float fMapY, float* pfImgX, float* pfImgY) const
{
	if (m_fAtlasMaxX <= 0.0f || m_fAtlasMaxY <= 0.0f)
	{
		*pfImgX = 0.0f;
		*pfImgY = 0.0f;
		return;
	}

	*pfImgX = fMapX / m_fAtlasMaxX * m_fAtlasImageSizeX;
	*pfImgY = fMapY / m_fAtlasMaxY * m_fAtlasImageSizeY;
}

void CPythonMiniMap::__CalcAtlasHelperScreenPos(float fMapX, float fMapY, float* pfScreenX, float* pfScreenY) const
{
	float fImgX = 0.0f;
	float fImgY = 0.0f;
	__MapPosToHelperAtlasImagePos(fMapX, fMapY, &fImgX, &fImgY);

	const float fScale = (m_fAtlasHelperScale > 0.0f) ? m_fAtlasHelperScale : 1.0f;
	*pfScreenX = fImgX * fScale - m_fAtlasRenderPosX;
	*pfScreenY = fImgY * fScale - m_fAtlasRenderPosY;
}

float CPythonMiniMap::__GetAtlasHelperViewportW() const
{
	return m_fAtlasHelperViewportW > 0.0f ? m_fAtlasHelperViewportW : (float)SQUARED_ATLAS_SIZE;
}

float CPythonMiniMap::__GetAtlasHelperViewportH() const
{
	return m_fAtlasHelperViewportH > 0.0f ? m_fAtlasHelperViewportH : (float)SQUARED_ATLAS_SIZE;
}

void CPythonMiniMap::__GetAtlasHelperPanExtents(float& fMinX, float& fMaxX, float& fMinY, float& fMaxY) const
{
	const float fViewportW = __GetAtlasHelperViewportW();
	const float fViewportH = __GetAtlasHelperViewportH();
	const float fScaledW = m_fAtlasImageSizeX * m_fAtlasHelperScale;
	const float fScaledH = m_fAtlasImageSizeY * m_fAtlasHelperScale;

	// smaller than the viewport: centred (a negative render pos)
	fMinX = fMaxX = 0.5f * (fScaledW - fViewportW);
	fMinY = fMaxY = 0.5f * (fScaledH - fViewportH);

	if (fScaledW > fViewportW)
	{
		fMinX = 0.0f;
		fMaxX = fScaledW - fViewportW;
	}

	if (fScaledH > fViewportH)
	{
		fMinY = 0.0f;
		fMaxY = fScaledH - fViewportH;
	}
}

void CPythonMiniMap::__ClampAtlasRenderPos()
{
	float fMinX, fMaxX, fMinY, fMaxY;
	__GetAtlasHelperPanExtents(fMinX, fMaxX, fMinY, fMaxY);

	if (m_fAtlasRenderPosX < fMinX)
		m_fAtlasRenderPosX = fMinX;
	if (m_fAtlasRenderPosX > fMaxX)
		m_fAtlasRenderPosX = fMaxX;
	if (m_fAtlasRenderPosY < fMinY)
		m_fAtlasRenderPosY = fMinY;
	if (m_fAtlasRenderPosY > fMaxY)
		m_fAtlasRenderPosY = fMaxY;
}

void CPythonMiniMap::__ApplyAtlasHelperScaleAtPlayerFocal(float fNewScale)
{
	if (fNewScale < 1.0f)
		fNewScale = 1.0f;
	if (fNewScale > c_fAtlasHelperScaleMax)
		fNewScale = c_fAtlasHelperScaleMax;

	const float fOldScale = m_fAtlasHelperScale;
	if (fabsf(fOldScale - fNewScale) < 0.001f)
		return;

	// zoom around the character (on its map), else around the viewport's centre
	float fFocalX = __GetAtlasHelperViewportW() * 0.5f;
	float fFocalY = __GetAtlasHelperViewportH() * 0.5f;

	CInstanceBase* pkInst = CPythonCharacterManager::Instance().GetMainInstancePtr();
	if (pkInst && __IsAtlasHelperShowingCurrentMap())
	{
		TPixelPosition kInstPos;
		pkInst->NEW_GetPixelPosition(&kInstPos);
		__CalcAtlasHelperScreenPos(kInstPos.x, kInstPos.y, &fFocalX, &fFocalY);
	}

	if (fOldScale > 0.001f)
	{
		const float fRatio = fNewScale / fOldScale;
		m_fAtlasRenderPosX = (fFocalX + m_fAtlasRenderPosX) * fRatio - fFocalX;
		m_fAtlasRenderPosY = (fFocalY + m_fAtlasRenderPosY) * fRatio - fFocalY;
	}

	m_fAtlasHelperScale = fNewScale;
	__ClampAtlasRenderPos();
}

//////////////////////////////////////////////////////////////////////////////////////////////
// python's controls

void CPythonMiniMap::SetAtlasHelperScale(float fScale)
{
	if (fScale < c_fAtlasHelperScaleMin)
		fScale = c_fAtlasHelperScaleMin;
	if (fScale > c_fAtlasHelperScaleMax)
		fScale = c_fAtlasHelperScaleMax;

	m_fAtlasHelperScale = fScale;
	__ClampAtlasRenderPos();
}

void CPythonMiniMap::AtlasScaleUp()
{
	if (m_bAtlasNpcHelperView)
		__ApplyAtlasHelperScaleAtPlayerFocal(GetNextAtlasHelperScale(m_fAtlasHelperScale, true));
}

void CPythonMiniMap::AtlasScaleDown()
{
	if (m_bAtlasNpcHelperView)
		__ApplyAtlasHelperScaleAtPlayerFocal(GetNextAtlasHelperScale(m_fAtlasHelperScale, false));
}

void CPythonMiniMap::ChangeAtlasRenderPos(float fX, float fY)
{
	m_fAtlasRenderPosX = fX;
	m_fAtlasRenderPosY = fY;
	__ClampAtlasRenderPos();
}

void CPythonMiniMap::CenterAtlasRenderPos()
{
	float fMinX, fMaxX, fMinY, fMaxY;
	__GetAtlasHelperPanExtents(fMinX, fMaxX, fMinY, fMaxY);
	m_fAtlasRenderPosX = 0.5f * (fMinX + fMaxX);
	m_fAtlasRenderPosY = 0.5f * (fMinY + fMaxY);
}

void CPythonMiniMap::GetAtlasRenderPos(float* pfX, float* pfY) const
{
	*pfX = m_fAtlasRenderPosX;
	*pfY = m_fAtlasRenderPosY;
}

void CPythonMiniMap::GetAtlasPanExtents(float* pfMinX, float* pfMaxX, float* pfMinY, float* pfMaxY) const
{
	float fMinX, fMaxX, fMinY, fMaxY;
	__GetAtlasHelperPanExtents(fMinX, fMaxX, fMinY, fMaxY);
	*pfMinX = fMinX;
	*pfMaxX = fMaxX;
	*pfMinY = fMinY;
	*pfMaxY = fMaxY;
}

void CPythonMiniMap::GetAtlasMaxPos(float* pfMaxX, float* pfMaxY) const
{
	float fMinX, fMinY;
	GetAtlasPanExtents(&fMinX, pfMaxX, &fMinY, pfMaxY);
}

void CPythonMiniMap::ConvertGlobalPosToAtlasPos(float fMapX, float fMapY, float* pfAtlasX, float* pfAtlasY) const
{
	__CalcAtlasHelperScreenPos(fMapX, fMapY, pfAtlasX, pfAtlasY);
}

float CPythonMiniMap::GetAtlasWidthHeightRatio() const
{
	if (m_fAtlasImageSizeY <= 0.0f)
		return 1.0f;
	return m_fAtlasImageSizeX / m_fAtlasImageSizeY;
}

void CPythonMiniMap::SetAtlasHelperViewportSize(float fWidth, float fHeight)
{
	if (fWidth < (float)SQUARED_ATLAS_SIZE)
		fWidth = (float)SQUARED_ATLAS_SIZE;
	if (fHeight < (float)SQUARED_ATLAS_SIZE)
		fHeight = (float)SQUARED_ATLAS_SIZE;

	m_fAtlasHelperViewportW = fWidth;
	m_fAtlasHelperViewportH = fHeight;
	__ClampAtlasRenderPos();
}

void CPythonMiniMap::GetAtlasHelperViewportSize(float* pfWidth, float* pfHeight) const
{
	*pfWidth = __GetAtlasHelperViewportW();
	*pfHeight = __GetAtlasHelperViewportH();
}

void CPythonMiniMap::SetAtlasScreenOrigin(float fScreenX, float fScreenY)
{
	m_fAtlasScreenX = fScreenX;
	m_fAtlasScreenY = fScreenY;
	m_matWorldAtlas._41 = fScreenX;
	m_matWorldAtlas._42 = fScreenY;
}

void CPythonMiniMap::CenterAtlasOnMapPos(float fMapX, float fMapY)
{
	float fImgX = 0.0f;
	float fImgY = 0.0f;
	__MapPosToHelperAtlasImagePos(fMapX, fMapY, &fImgX, &fImgY);

	const float fScale = (m_fAtlasHelperScale > 0.001f) ? m_fAtlasHelperScale : 1.0f;
	m_fAtlasRenderPosX = fImgX * fScale - __GetAtlasHelperViewportW() * 0.5f;
	m_fAtlasRenderPosY = fImgY * fScale - __GetAtlasHelperViewportH() * 0.5f;
	__ClampAtlasRenderPos();
}

//////////////////////////////////////////////////////////////////////////////////////////////
// which map the atlas shows

bool CPythonMiniMap::__IsAtlasHelperShowingCurrentMap() const
{
	if (m_strAtlasHelperDisplayMapName.empty())
		return true;

	CPythonBackground& rkBG = CPythonBackground::Instance();
	if (!rkBG.IsMapOutdoor())
		return false;

	return 0 == _stricmp(m_strAtlasHelperDisplayMapName.c_str(), rkBG.GetMapOutdoorRef().GetName().c_str());
}

void CPythonMiniMap::__ResetAtlasHelperImageScale()
{
	// the helper zooms with its own matrix: the image itself at 1:1 (the ordinary atlas' SetAtlasScale(x, y) undone,
	// its marks moved back with it; python's small atlas sets its scale again when it shows)
	if (m_AtlasImageInstance.IsEmpty())
		return;
#ifdef ENABLE_SET_ATLAS_SCALE
	SetAtlasScale(1.0f, 1.0f);
#else
	m_fAtlasImageSizeX = (float)m_AtlasImageInstance.GetWidth();
	m_fAtlasImageSizeY = (float)m_AtlasImageInstance.GetHeight();
#endif
}

bool CPythonMiniMap::__ReloadCurrentAtlasKeepGuildArea()
{
	// LoadAtlas forgets the guild areas (the server sends them once per map) and opens the atlas window: neither here
	const TGuildAreaInfoVector kGuildAreas = m_GuildAreaInfoVector;
	const bool bShowAtlas = m_bShowAtlas;
	m_bShowAtlas = false;
	const bool bLoaded = LoadAtlas();
	m_bShowAtlas = bShowAtlas;
	m_GuildAreaInfoVector = kGuildAreas;
	return bLoaded;
}

void CPythonMiniMap::SetAtlasNpcHelperView(bool bNpcHelperView)
{
	if (m_bAtlasNpcHelperView == bNpcHelperView)
		return;

	m_bAtlasNpcHelperView = bNpcHelperView;

	if (bNpcHelperView)
		__ResetAtlasHelperImageScale();
	else if (!__IsAtlasHelperShowingCurrentMap())
		__ReloadCurrentAtlasKeepGuildArea();	// back to the character's map

	m_fAtlasHelperScale = 1.0f;
	m_fAtlasRenderPosX = 0.0f;
	m_fAtlasRenderPosY = 0.0f;
	__ClampAtlasRenderPos();
}

bool CPythonMiniMap::LoadAtlasForMapName(const char* c_szMapName)
{
	if (!c_szMapName || !*c_szMapName)
		return false;

	CPythonBackground& rkBG = CPythonBackground::Instance();
	const bool bCurrentMap = rkBG.IsMapOutdoor() && 0 == _stricmp(rkBG.GetMapOutdoorRef().GetName().c_str(), c_szMapName);

	if (bCurrentMap)
	{
		if (!__IsAtlasHelperShowingCurrentMap())
			__ReloadCurrentAtlasKeepGuildArea();
	}
	else
	{
		char szAtlasFileName[1024 + 1];
		snprintf(szAtlasFileName, sizeof(szAtlasFileName), "%s/atlas.sub", c_szMapName);
		if (!CEterPackManager::Instance().isExist(szAtlasFileName))
			snprintf(szAtlasFileName, sizeof(szAtlasFileName), "d:/ymir work/ui/atlas/%s/atlas.sub", c_szMapName);

		m_AtlasImageInstance.Destroy();
		m_bAtlas = false;
		if (CEterPackManager::Instance().isExist(szAtlasFileName))
		{
			CGraphicImage* pkGrpImgAtlas = (CGraphicImage*)CResourceManager::Instance().GetResourcePointer(szAtlasFileName);
			if (pkGrpImgAtlas)
			{
				m_AtlasImageInstance.SetImagePointer(pkGrpImgAtlas);
				m_bAtlas = !pkGrpImgAtlas->IsEmpty();
			}
		}

		m_fAtlasImageSizeX = m_AtlasImageInstance.IsEmpty() ? 0.0f : (float)m_AtlasImageInstance.GetWidth();
		m_fAtlasImageSizeY = m_AtlasImageInstance.IsEmpty() ? 0.0f : (float)m_AtlasImageInstance.GetHeight();

		DWORD dwBaseX = 0, dwBaseY = 0;
		float fMaxX = 0.0f, fMaxY = 0.0f;
		if (!rkBG.GetMapInfoByName(c_szMapName, &dwBaseX, &dwBaseY, &fMaxX, &fMaxY))
		{
			// not in atlasinfo: marks at image scale (better than nothing)
			fMaxX = m_fAtlasImageSizeX > 0.0f ? m_fAtlasImageSizeX : 1.0f;
			fMaxY = m_fAtlasImageSizeY > 0.0f ? m_fAtlasImageSizeY : 1.0f;
		}
		m_dwAtlasBaseX = dwBaseX;
		m_dwAtlasBaseY = dwBaseY;
		m_fAtlasMaxX = fMaxX;
		m_fAtlasMaxY = fMaxY;

		m_strAtlasHelperDisplayMapName = c_szMapName;
		__LoadAtlasMarkInfoForMap(c_szMapName);	// NPC / warp marks only - the guild areas stay the character's map's
	}

	if (m_bAtlasNpcHelperView)
		__ResetAtlasHelperImageScale();

	m_fAtlasHelperScale = 1.0f;
	m_fAtlasRenderPosX = 0.0f;
	m_fAtlasRenderPosY = 0.0f;
	__ClampAtlasRenderPos();

	return m_bAtlas;
}

//////////////////////////////////////////////////////////////////////////////////////////////
// drawing

void CPythonMiniMap::__RenderAtlasForNpcLocationHelper()
{
	if (m_AtlasImageInstance.IsEmpty())
		return;

	const float fScale = (m_fAtlasHelperScale > 0.0f) ? m_fAtlasHelperScale : 1.0f;

	// clip to the viewport (screen pixels): nothing of a zoomed atlas outside python's window
	RECT rcClip;
	rcClip.left = (LONG)m_fAtlasScreenX;
	rcClip.top = (LONG)m_fAtlasScreenY;
	rcClip.right = (LONG)(m_fAtlasScreenX + __GetAtlasHelperViewportW());
	rcClip.bottom = (LONG)(m_fAtlasScreenY + __GetAtlasHelperViewportH());
	RECT rcOldClip;
	const bool bOldClip = ms_lpd3dDevice && SUCCEEDED(ms_lpd3dDevice->GetScissorRect(&rcOldClip));
	if (ms_lpd3dDevice)
		ms_lpd3dDevice->SetScissorRect(&rcClip);
	STATEMANAGER.SaveRenderState(D3DRS_SCISSORTESTENABLE, TRUE);

	D3DXMATRIX matHelper;
	D3DXMATRIX matFinal;
	D3DXMatrixScaling(&matHelper, fScale, fScale, 1.0f);
	matHelper._41 = -m_fAtlasRenderPosX;
	matHelper._42 = -m_fAtlasRenderPosY;
	D3DXMatrixMultiply(&matFinal, &matHelper, &m_matWorldAtlas);
	STATEMANAGER.SetTransform(D3DTS_WORLD, &matFinal);

	const DWORD dwFilter = (fabsf(fScale - 1.0f) < 0.01f) ? D3DTEXF_POINT : D3DTEXF_LINEAR;
	STATEMANAGER.SaveSamplerState(0, D3DSAMP_MINFILTER, dwFilter);
	STATEMANAGER.SaveSamplerState(0, D3DSAMP_MAGFILTER, dwFilter);
	m_AtlasImageInstance.Render();

	STATEMANAGER.SaveRenderState(D3DRS_TEXTUREFACTOR, 0xFFFFFFFF);
	STATEMANAGER.SaveTextureStageState(0, D3DTSS_COLORARG1, D3DTA_TFACTOR);
	STATEMANAGER.SaveTextureStageState(0, D3DTSS_COLORARG2, D3DTA_TEXTURE);
	STATEMANAGER.SaveTextureStageState(0, D3DTSS_COLOROP, D3DTOP_MODULATE);

	__RenderAtlasHelperMarks();

	STATEMANAGER.RestoreRenderState(D3DRS_TEXTUREFACTOR);
	STATEMANAGER.RestoreTextureStageState(0, D3DTSS_COLORARG1);
	STATEMANAGER.RestoreTextureStageState(0, D3DTSS_COLORARG2);
	STATEMANAGER.RestoreTextureStageState(0, D3DTSS_COLOROP);
	STATEMANAGER.RestoreSamplerState(0, D3DSAMP_MINFILTER);
	STATEMANAGER.RestoreSamplerState(0, D3DSAMP_MAGFILTER);
	STATEMANAGER.SetTransform(D3DTS_WORLD, &m_matIdentity);

	STATEMANAGER.RestoreRenderState(D3DRS_SCISSORTESTENABLE);
	if (bOldClip)
		ms_lpd3dDevice->SetScissorRect(&rcOldClip);
}

void CPythonMiniMap::__RenderAtlasHelperMarks()
{
	const bool bCurrentMap = __IsAtlasHelperShowingCurrentMap();
	float fX = 0.0f;
	float fY = 0.0f;

	if (!m_WhiteMark.IsEmpty())
	{
		const float fHalfW = (float)m_WhiteMark.GetWidth() * 0.5f;
		const float fHalfH = (float)m_WhiteMark.GetHeight() * 0.5f;

		// with an NPC chosen only that NPC is marked (as the package)
		if (!m_bNPCSelected)
		{
			STATEMANAGER.SetRenderState(D3DRS_TEXTUREFACTOR, CInstanceBase::GetIndexedNameColor(CInstanceBase::NAMECOLOR_NPC));
			for (TAtlasMarkInfoVectorIterator it = m_AtlasNPCInfoVector.begin(); it != m_AtlasNPCInfoVector.end(); ++it)
			{
				__MapPosToHelperAtlasImagePos(it->m_fX, it->m_fY, &fX, &fY);
				m_WhiteMark.SetPosition(fX - fHalfW, fY - fHalfH);
				m_WhiteMark.Render();
			}

			STATEMANAGER.SetRenderState(D3DRS_TEXTUREFACTOR, CInstanceBase::GetIndexedNameColor(CInstanceBase::NAMECOLOR_WARP));
			for (TAtlasMarkInfoVectorIterator it = m_AtlasWarpInfoVector.begin(); it != m_AtlasWarpInfoVector.end(); ++it)
			{
				__MapPosToHelperAtlasImagePos(it->m_fX, it->m_fY, &fX, &fY);
				m_WhiteMark.SetPosition(fX - fHalfW, fY - fHalfH);
				m_WhiteMark.Render();
			}
		}

#if defined(PARTY_POSITION)
		CInstanceBase* pkInst = CPythonCharacterManager::Instance().GetMainInstancePtr();
		if (bCurrentMap && pkInst && pkInst->IsPartyMember())
		{
			const float v = (1 + sinf(CTimer::Instance().GetCurrentSecond() * 6)) / 5 + 0.8f;
			D3DXCOLOR c(CInstanceBase::GetIndexedNameColor(CInstanceBase::NAMECOLOR_PARTY));
			D3DXCOLOR d(v, v, v, 1);
			D3DXColorModulate(&c, &c, &d);
			STATEMANAGER.SetRenderState(D3DRS_TEXTUREFACTOR, (DWORD)c);

			DWORD dwPID = 0;
			CPythonPlayer::Instance().PartyMemberVIDToPID(pkInst->GetVirtualID(), &dwPID);
			const size_t iPartyMemberCount = CPythonPlayer::Instance().GetPartyMemberCount();
			for (size_t i = 0; i < iPartyMemberCount; ++i)
			{
				const DWORD dwPartyMemberPID = CPythonPlayer::Instance().GetPartyMemberPIDByIndex(i);
				if (dwPID == dwPartyMemberPID)
					continue;
				D3DXVECTOR2 v2Position = { 0.0f, 0.0f };
				CPythonPlayer::Instance().GetPartyMemberPosition(dwPartyMemberPID, &v2Position);
				if (v2Position.x <= 0.0f || v2Position.y <= 0.0f || v2Position.x > m_fAtlasMaxX || v2Position.y > m_fAtlasMaxY)
					continue;
				__MapPosToHelperAtlasImagePos(v2Position.x, v2Position.y, &fX, &fY);
				m_WhiteMark.SetPosition(fX - fHalfW, fY - fHalfH);
				m_WhiteMark.Render();
			}
		}
#endif
	}

	STATEMANAGER.SetSamplerState(0, D3DSAMP_MINFILTER, D3DTEXF_LINEAR);
	STATEMANAGER.SetSamplerState(0, D3DSAMP_MAGFILTER, D3DTEXF_LINEAR);

	// waypoints (quest targets, signals) - the character's map's
	if (bCurrentMap && !m_bNPCSelected)
	{
		STATEMANAGER.SetRenderState(D3DRS_TEXTUREFACTOR, CInstanceBase::GetIndexedNameColor(CInstanceBase::NAMECOLOR_WAYPOINT));
		for (TAtlasMarkInfoVectorIterator it = m_AtlasWayPointInfoVector.begin(); it != m_AtlasWayPointInfoVector.end(); ++it)
		{
			if (it->m_fX <= 0.0f && it->m_fY <= 0.0f)
				continue;
			__MapPosToHelperAtlasImagePos(it->m_fX, it->m_fY, &fX, &fY);
			if (TYPE_TARGET == it->m_byType)
				__RenderMiniWayPointMark((int)fX, (int)fY);
			else
				__RenderWayPointMark((int)fX, (int)fY);
		}
	}

	// the chosen NPC (when the atlas shows its map): the waypoint and a blinking orange square beside it
	bool bSelectedOnShownMap = m_bNPCSelected;
	if (bSelectedOnShownMap && !m_strSelectedMapName.empty())
	{
		std::string strShownMap = m_strAtlasHelperDisplayMapName;
		if (strShownMap.empty() && CPythonBackground::Instance().IsMapOutdoor())
			strShownMap = CPythonBackground::Instance().GetMapOutdoorRef().GetName();
		bSelectedOnShownMap = 0 == _stricmp(m_strSelectedMapName.c_str(), strShownMap.c_str());
	}
	if (bSelectedOnShownMap)
	{
		__MapPosToHelperAtlasImagePos((float)m_lSelectedNPCX, (float)m_lSelectedNPCY, &fX, &fY);
		STATEMANAGER.SetRenderState(D3DRS_TEXTUREFACTOR, 0xFFFFFFFF);
		__RenderWayPointMark((int)fX, (int)fY);
		__RenderMiniWayPointMark((int)fX, (int)fY);

		if (ELTimer_GetMSec() % 5000 <= 4900 && !m_WhiteMark.IsEmpty())
		{
			const float fOrangeScale = (float)ATLAS_HELPER_ORANGE_MARK_SCALE_PERCENT / 100.0f;
			const float fHalfH = (float)m_WhiteMark.GetHeight() * 0.5f * fOrangeScale;
			STATEMANAGER.SetRenderState(D3DRS_TEXTUREFACTOR, D3DCOLOR_XRGB(255, 132, 0));
			m_WhiteMark.SetScale(fOrangeScale, fOrangeScale);
			m_WhiteMark.SetPosition(fX + 3.0f, fY - fHalfH);
			m_WhiteMark.Render();
			m_WhiteMark.SetScale(1.0f, 1.0f);
		}
	}

	// the character: the pulsing circle (no NPC chosen) and the arrow mark, always visible (no blinking)
	CInstanceBase* pkMain = CPythonCharacterManager::Instance().GetMainInstancePtr();
	if (bCurrentMap && pkMain)
	{
		TPixelPosition kInstPos;
		pkMain->NEW_GetPixelPosition(&kInstPos);
		__MapPosToHelperAtlasImagePos(kInstPos.x, kInstPos.y, &fX, &fY);

		STATEMANAGER.SetRenderState(D3DRS_TEXTUREFACTOR, 0xFFFFFFFF);
		if (!m_bNPCSelected)
		{
			CGraphicExpandedImageInstance& rkCircle = m_AtlasHelperMyPositionMarks[(ELTimer_GetMSec() / 120) % ATLAS_HELPER_MY_POSITION_IMAGE_COUNT];
			if (!rkCircle.IsEmpty())
			{
				rkCircle.SetPosition(fX - (float)rkCircle.GetWidth() * 0.5f, fY - (float)rkCircle.GetHeight() * 0.5f);
				rkCircle.Render();
			}
		}

		if (!m_AtlasPlayerMark.IsEmpty())
		{
			float fRotation = 540.0f - pkMain->GetRotation();
			while (fRotation > 360.0f)
				fRotation -= 360.0f;
			while (fRotation < 0.0f)
				fRotation += 360.0f;
			m_fAtlasHelperPlayerRotation = fRotation;

			const float fMarkScale = (float)ATLAS_HELPER_PLAYER_MARK_SCALE_PERCENT / 100.0f;
			m_AtlasPlayerMark.SetScale(fMarkScale, fMarkScale);
			m_AtlasPlayerMark.SetOrigin();
			m_AtlasPlayerMark.SetPosition(fX - (float)m_AtlasPlayerMark.GetWidth() * 0.5f, fY - (float)m_AtlasPlayerMark.GetHeight() * 0.5f);
			m_AtlasPlayerMark.SetRotation(fRotation);
			m_AtlasPlayerMark.Render();
			m_AtlasPlayerMark.SetScale(1.0f, 1.0f);
		}
	}
}

//////////////////////////////////////////////////////////////////////////////////////////////
// the mark under the mouse (miniMap.GetAtlasInfo while the helper view is on)

bool CPythonMiniMap::__GetAtlasHelperInfo(float fScreenX, float fScreenY, std::string & rReturnString, float * pReturnPosX, float * pReturnPosY, DWORD * pdwTextColor, DWORD * pdwGuildID)
{
	const float fScale = (m_fAtlasHelperScale > 0.0f) ? m_fAtlasHelperScale : 1.0f;
	const float fLocalX = fScreenX - m_fAtlasScreenX;
	const float fLocalY = fScreenY - m_fAtlasScreenY;
	if (fLocalX < 0.0f || fLocalY < 0.0f || fLocalX > __GetAtlasHelperViewportW() || fLocalY > __GetAtlasHelperViewportH())
		return false;

	const bool bCurrentMap = __IsAtlasHelperShowingCurrentMap();
	const float fPickHalfW = m_WhiteMark.IsEmpty() ? 6.0f : (float)m_WhiteMark.GetWidth() * 0.5f * fScale + 1.0f;
	const float fPickHalfH = m_WhiteMark.IsEmpty() ? 6.0f : (float)m_WhiteMark.GetHeight() * 0.5f * fScale + 1.0f;
	float fMiniHalfW = fPickHalfW;
	float fMiniHalfH = fPickHalfH;
	if (!m_MiniWayPointGraphicImageInstances[0].IsEmpty())
	{
		fMiniHalfW = (float)m_MiniWayPointGraphicImageInstances[0].GetWidth() * 0.5f * fScale + 1.0f;
		fMiniHalfH = (float)m_MiniWayPointGraphicImageInstances[0].GetHeight() * 0.5f * fScale + 1.0f;
	}

	bool bFound = false;
	float fBestDistSq = FLT_MAX;

	struct SPick
	{
		std::string strName;
		float fX, fY;
		DWORD dwColor, dwGuildID;
	} kBest = { "", 0.0f, 0.0f, 0, 0 };

	auto Consider = [&](float fMapX, float fMapY, const std::string& strName, DWORD dwColor, float fHalfW, float fHalfH)
	{
		if (strName.empty())
			return;
		float fMarkX = 0.0f;
		float fMarkY = 0.0f;
		__CalcAtlasHelperScreenPos(fMapX, fMapY, &fMarkX, &fMarkY);
		const float fDx = fLocalX - fMarkX;
		const float fDy = fLocalY - fMarkY;
		if (fabsf(fDx) > fHalfW || fabsf(fDy) > fHalfH)
			return;
		const float fDistSq = fDx * fDx + fDy * fDy;
		if (fDistSq >= fBestDistSq)
			return;
		fBestDistSq = fDistSq;
		bFound = true;
		kBest.strName = strName;
		kBest.fX = fMapX;
		kBest.fY = fMapY;
		kBest.dwColor = dwColor;
		kBest.dwGuildID = 0;
	};

	CInstanceBase* pkInst = CPythonCharacterManager::Instance().GetMainInstancePtr();
	if (pkInst && bCurrentMap)
	{
		TPixelPosition kInstPos;
		pkInst->NEW_GetPixelPosition(&kInstPos);
		Consider(kInstPos.x, kInstPos.y, pkInst->GetNameString(), (DWORD)D3DXCOLOR(pkInst->GetNameColor()), fPickHalfW, fPickHalfH);
	}

	for (TAtlasMarkInfoVectorIterator it = m_AtlasNPCInfoVector.begin(); it != m_AtlasNPCInfoVector.end(); ++it)
		Consider(it->m_fX, it->m_fY, it->m_strText, CInstanceBase::GetIndexedNameColor(CInstanceBase::NAMECOLOR_NPC), fPickHalfW, fPickHalfH);
	for (TAtlasMarkInfoVectorIterator it = m_AtlasWarpInfoVector.begin(); it != m_AtlasWarpInfoVector.end(); ++it)
		Consider(it->m_fX, it->m_fY, it->m_strText, CInstanceBase::GetIndexedNameColor(CInstanceBase::NAMECOLOR_WARP), fPickHalfW, fPickHalfH);

	if (bCurrentMap)
	{
		for (TAtlasMarkInfoVectorIterator it = m_AtlasWayPointInfoVector.begin(); it != m_AtlasWayPointInfoVector.end(); ++it)
		{
			const bool bTarget = TYPE_TARGET == it->m_byType;
			Consider(it->m_fX, it->m_fY, it->m_strText, CInstanceBase::GetIndexedNameColor(CInstanceBase::NAMECOLOR_WAYPOINT),
				bTarget ? fMiniHalfW : fPickHalfW, bTarget ? fMiniHalfH : fPickHalfH);
		}

#if defined(PARTY_POSITION)
		if (pkInst && pkInst->IsPartyMember())
		{
			DWORD dwPID = 0;
			CPythonPlayer::Instance().PartyMemberVIDToPID(pkInst->GetVirtualID(), &dwPID);
			const size_t iPartyMemberCount = CPythonPlayer::Instance().GetPartyMemberCount();
			for (size_t i = 0; i < iPartyMemberCount; ++i)
			{
				const DWORD dwPartyMemberPID = CPythonPlayer::Instance().GetPartyMemberPIDByIndex(i);
				if (dwPID == dwPartyMemberPID)
					continue;
				D3DXVECTOR2 v2Position = { 0.0f, 0.0f };
				CPythonPlayer::Instance().GetPartyMemberPosition(dwPartyMemberPID, &v2Position);
				if (v2Position.x == 0.0f && v2Position.y == 0.0f)
					continue;
				Consider(v2Position.x, v2Position.y, CPythonPlayer::Instance().GetPartyMemberName(dwPartyMemberPID),
					CInstanceBase::GetIndexedNameColor(CInstanceBase::NAMECOLOR_PARTY), fPickHalfW, fPickHalfH);
			}
		}
#endif

		for (TGuildAreaInfoVectorIterator it = m_GuildAreaInfoVector.begin(); it != m_GuildAreaInfoVector.end(); ++it)
		{
			float fSX0, fSY0, fSX1, fSY1;
			__CalcAtlasHelperScreenPos((float)it->lx, (float)it->ly, &fSX0, &fSY0);
			__CalcAtlasHelperScreenPos((float)(it->lx + it->lwidth), (float)(it->ly + it->lheight), &fSX1, &fSY1);
			const float fMinX = fSX0 < fSX1 ? fSX0 : fSX1;
			const float fMaxX = fSX0 < fSX1 ? fSX1 : fSX0;
			const float fMinY = fSY0 < fSY1 ? fSY0 : fSY1;
			const float fMaxY = fSY0 < fSY1 ? fSY1 : fSY0;
			if (fLocalX < fMinX || fLocalX > fMaxX || fLocalY < fMinY || fLocalY > fMaxY)
				continue;

			const float fDx = fLocalX - (fSX0 + fSX1) * 0.5f;
			const float fDy = fLocalY - (fSY0 + fSY1) * 0.5f;
			const float fDistSq = fDx * fDx + fDy * fDy;
			if (fDistSq >= fBestDistSq)
				continue;

			fBestDistSq = fDistSq;
			bFound = true;
			kBest.dwGuildID = 0;
			if (CPythonGuild::Instance().GetGuildName(it->dwGuildID, &kBest.strName))
				kBest.dwGuildID = it->dwGuildID;
			else
				kBest.strName = "empty_guild_area";
			kBest.fX = (float)(it->lx + it->lwidth / 2);
			kBest.fY = (float)(it->ly + it->lheight / 2);
			kBest.dwColor = CInstanceBase::GetIndexedNameColor(CInstanceBase::NAMECOLOR_PARTY);
		}
	}

	if (!bFound)
		return false;

	rReturnString = kBest.strName;
	*pReturnPosX = kBest.fX;
	*pReturnPosY = kBest.fY;
	*pdwTextColor = kBest.dwColor;
	*pdwGuildID = kBest.dwGuildID;
	return true;
}

//////////////////////////////////////////////////////////////////////////////////////////////
// the chosen NPC and the arrow under the character

bool CPythonMiniMap::__IsSelectedNPCOnCurrentMap() const
{
	CPythonBackground& rkBG = CPythonBackground::Instance();
	if (!rkBG.IsMapOutdoor())
		return false;

	if (!m_strSelectedMapName.empty())
		return 0 == _stricmp(m_strSelectedMapName.c_str(), rkBG.GetMapOutdoorRef().GetName().c_str());

	if (m_lSelectedMapIndex <= 0)
		return true;

	const int iCurrentMapIndex = CPythonNPCLocationHelper::Instance().GetCurrentMapIndex();
	return iCurrentMapIndex <= 0 || iCurrentMapIndex == m_lSelectedMapIndex;
}

void CPythonMiniMap::SelectNPC(long lMapIndex, DWORD dwVnum, long lX, long lY, const char* c_szMapName)
{
	RemoveWayPoint(NPC_LOCATION_HELPER_TARGET_WAYPOINT);

	m_bNPCSelected = true;
	m_lSelectedMapIndex = lMapIndex;
	m_dwSelectedNPCVnum = dwVnum;
	m_lSelectedNPCX = lX;
	m_lSelectedNPCY = lY;
	m_strSelectedMapName = c_szMapName ? c_szMapName : "";

	// no map named and no index: the character's map now (it stays that map after a warp)
	CPythonBackground& rkBG = CPythonBackground::Instance();
	if (m_strSelectedMapName.empty() && lMapIndex <= 0 && rkBG.IsMapOutdoor())
		m_strSelectedMapName = rkBG.GetMapOutdoorRef().GetName();

	m_dwNPCLocationDirectionEffectStartMS = ELTimer_GetMSec();
	if (__IsSelectedNPCOnCurrentMap())
		__SpawnNPCLocationDirectionEffect();
	else
		__ClearNPCLocationDirectionEffect();
}

void CPythonMiniMap::UnselectNPC()
{
	RemoveWayPoint(NPC_LOCATION_HELPER_TARGET_WAYPOINT);
	m_bNPCSelected = false;
	m_lSelectedMapIndex = 0;
	m_strSelectedMapName.clear();
	m_dwSelectedNPCVnum = 0;
	m_lSelectedNPCX = 0;
	m_lSelectedNPCY = 0;
	__ClearNPCLocationDirectionEffect();
}

void CPythonMiniMap::GetSelectedNPCPos(long* plX, long* plY) const
{
	*plX = m_lSelectedNPCX;
	*plY = m_lSelectedNPCY;
}

void CPythonMiniMap::TickNPCLocationDirectionEffect()
{
	if (m_bNPCSelected)
		__UpdateNPCLocationDirectionEffect();
}

void CPythonMiniMap::__ClearNPCLocationDirectionEffect()
{
	if (m_iNPCLocationDirectionEffectIndex >= 0)
	{
		if (CEffectManager::InstancePtr())
			CEffectManager::Instance().DestroyEffectInstance((DWORD)m_iNPCLocationDirectionEffectIndex);
		m_iNPCLocationDirectionEffectIndex = -1;
	}
}

bool CPythonMiniMap::__EnsureNPCLocationDirectionEffectRegistered()
{
	if (m_dwNPCLocationDirectionEffectID != 0)
		return true;

	if (!CEterPackManager::Instance().isExist(c_szNPCLocationDirectionEffect))
		return false;

	DWORD dwID = 0;
	if (!CEffectManager::Instance().RegisterEffect2(c_szNPCLocationDirectionEffect, &dwID, true))
		return false;

	m_dwNPCLocationDirectionEffectID = dwID;
	return m_dwNPCLocationDirectionEffectID != 0;
}

void CPythonMiniMap::__SpawnNPCLocationDirectionEffect()
{
	__ClearNPCLocationDirectionEffect();

	if (!__EnsureNPCLocationDirectionEffectRegistered())
		return;

	CInstanceBase* pkInstMain = CPythonCharacterManager::Instance().GetMainInstancePtr();
	if (!pkInstMain)
		return;

	TPixelPosition kPlayerPos;
	pkInstMain->NEW_GetPixelPosition(&kPlayerPos);

	D3DXMATRIX matEffect;
	BuildNPCLocationDirectionEffectMatrix(kPlayerPos, (float)m_lSelectedNPCX, (float)m_lSelectedNPCY, &matEffect);

	CEffectManager& rkEftMgr = CEffectManager::Instance();
	m_iNPCLocationDirectionEffectIndex = rkEftMgr.CreateEffect(m_dwNPCLocationDirectionEffectID,
		D3DXVECTOR3(matEffect._41, matEffect._42, matEffect._43), D3DXVECTOR3(0.0f, 0.0f, 0.0f));
	if (m_iNPCLocationDirectionEffectIndex < 0)
		return;

	if (!rkEftMgr.SelectEffectInstance((DWORD)m_iNPCLocationDirectionEffectIndex))
	{
		__ClearNPCLocationDirectionEffect();
		return;
	}

	rkEftMgr.SetEffectInstanceGlobalMatrix(matEffect);
}

void CPythonMiniMap::__UpdateNPCLocationDirectionEffect()
{
	if (!__IsSelectedNPCOnCurrentMap())
	{
		__ClearNPCLocationDirectionEffect();
		return;
	}

	CInstanceBase* pkInstMain = CPythonCharacterManager::Instance().GetMainInstancePtr();
	if (!pkInstMain)
	{
		__ClearNPCLocationDirectionEffect();
		return;
	}

	TPixelPosition kPlayerPos;
	pkInstMain->NEW_GetPixelPosition(&kPlayerPos);

	const float fTargetX = (float)m_lSelectedNPCX;
	const float fTargetY = (float)m_lSelectedNPCY;
	const float fDx = kPlayerPos.x - fTargetX;
	const float fDy = kPlayerPos.y - fTargetY;

	if (ELTimer_GetMSec() - m_dwNPCLocationDirectionEffectStartMS >= c_dwNPCLocationDirectionGraceMS
		&& fDx * fDx + fDy * fDy <= c_fNPCLocationDirectionArriveRadius * c_fNPCLocationDirectionArriveRadius)
	{
		UnselectNPC();
		return;
	}

	CEffectManager& rkEftMgr = CEffectManager::Instance();
	if (m_iNPCLocationDirectionEffectIndex < 0 || !rkEftMgr.IsAliveEffect((DWORD)m_iNPCLocationDirectionEffectIndex))
	{
		__SpawnNPCLocationDirectionEffect();
		return;
	}

	if (!rkEftMgr.SelectEffectInstance((DWORD)m_iNPCLocationDirectionEffectIndex))
	{
		__ClearNPCLocationDirectionEffect();
		return;
	}

	D3DXMATRIX matEffect;
	BuildNPCLocationDirectionEffectMatrix(kPlayerPos, fTargetX, fTargetY, &matEffect);
	rkEftMgr.SetEffectInstanceGlobalMatrix(matEffect);
}
#endif
