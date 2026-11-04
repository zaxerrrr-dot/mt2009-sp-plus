/**
* MT2009_PLUS_TITLES_V1 - Tytuly in the Yohara 3.x exe (the owner's package "Official Title System Renewal" - rebuilt;
* server-patches/tytuly/README.md has the whole picture).
*
* A character wears one title; every client around draws it with his name:
*   - TYPE_NAMEPLATE: the title's name on a three-part plate above the name (the guild line, the personality line) -
*     left / middle (stretched to the name) / right picture from d:/ymir work/ui/game/title/titles/title_<res>.sub
*     ("left_image", "middle_image", "right_image"), and when the .sub names "sprites" an animated banner behind it
*     (sprites_<res>/00..NN.sub, "sprites_count", "sprite_size_x/y");
*   - TYPE_EFFECT: an effect over the head (the title's effect file, attached to the actor - put on again when the
*     instance is made again: into sight, a mount, a shape);
*   - TYPE_TEXT: the name only.
* The catalogue (names, kinds, resources, effects, colours) comes from the server (GC 189 TABLE) - no locale files.
*
* Packets: CG 185 HEADER_CG_TITLE (6 B + the sequence byte): OPEN when the game phase starts (the hello - only a client
* that said it gets GC 189; the server's answer is the catalogue, the owned titles, the worn one and the titles of
* everyone in sight) and from the window (refresh), EQUIP, UNEQUIP. GC 189 HEADER_GC_TITLE (dynamic): TABLE, PLAYER,
* EQUIPPED, NOTIFY, VISUAL (vid, title).
*
* The window's preview: the selected title's effect drawn into the render target RENDER_TARGET_INDEX (titleSystem's
* constant) over the window's background picture, through UI::CRenderTarget's render hook (chained with the Monster
* Cards' one), with its own camera (the particles face it) - nothing in the effect manager's map, so the world never
* draws it twice (the package changed EffectLib for that).
*
* Python (module titleSystem):
*   SetHandler(obj)            obj.OnTitleNotify(message, title), obj.OnTitleRefresh()
*   RequestOpen()              the window asks for the data again
*   RequestEquip(title)        0 = take off
*   GetTitles()                [(title, type, name, condition, permanent, duration, resource, color), ...] (catalogue order)
*   GetOwned()                 [(title, end_time), ...] (end_time 0 = for good)
*   GetEquipped()              the worn title (0 none)
*   IsDataReceived()           the catalogue came
*   GetPlate(resource)         (left, middle, right, sprite dir, sprite count, sprite width, sprite height) or ()
*   SetShowOthers(on), GetShowOthers()   the others' titles drawn or not (the player's own always)
*   PreviewSelect(title), PreviewShow(on), RENDER_TARGET_INDEX
*   app.MT2009_TITLES_EXE = 1
*/
#include "StdAfx.h"

#ifdef ENABLE_MT2009_TITLES
#include "InstanceBase.h"
#include "PythonCharacterManager.h"
#include "PythonNetworkStream.h"
#include "PythonApplication.h"
#include "../EterPack/EterPackManager.h"
#include "../EterBase/FileLoader.h"
#include "../EterLib/Camera.h"
#include "../EterLib/GrpBase.h"
#include "../EterLib/GrpScreen.h"
#include "../EterLib/GrpTextInstance.h"
#include "../EterLib/GrpExpandedImageInstance.h"
#include "../EterLib/ResourceManager.h"
#include "../EterLib/StateManager.h"
#include "../EffectLib/EffectManager.h"
#include "../EffectLib/EffectInstance.h"
#if defined(RENDER_TARGET)
#include "../EterLib/RenderTargetManager.h"
#include "../EterPythonLib/PythonWindow.h"
#endif

#include <cmath>
#include <map>
#include <string>
#include <vector>

static_assert(sizeof(TPacketCGTitle) == 6 && sizeof(TPacketGCTitle) == 6 && sizeof(TPacketGCTitleRow) == 309 &&
	sizeof(TPacketGCTitleOwned) == 8 && sizeof(TPacketGCTitleNotify) == 5 && sizeof(TPacketGCTitleVisual) == 8,
	"title packets (server packet.h)");

extern CGraphicText * ms_pFont;	// PythonTextTail.cpp: the name tails' font

namespace
{
	enum
	{
		TYPE_TEXT = 1,
		TYPE_EFFECT = 3,
		TYPE_NAMEPLATE = 4,
	};

	const float EFFECT_HEAD_Z = 70.0f;			// the effect over the head (the package's height)
	const DWORD SPRITE_FRAME_MS = 160;			// the banner's frame time (the package's)
	const float PLATE_LINE_GAP = 28.0f;			// the plate's centre above the top text line (the package's 28)
	const float PLATE_LINE_GAP_EXTRA = 35.0f;	// ... when there is a guild / personality line above the name
	const int PREVIEW_TARGET = 40;				// the preview's render target index (not one of RenderTargetManager's)
	const DWORD PREVIEW_TEX_W = 448;			// twice the window's preview (224 x 346)
	const DWORD PREVIEW_TEX_H = 692;
	const float PREVIEW_VIEW_W = 224.0f;		// world units the preview shows across
	const float PREVIEW_CENTER_Z = 40.0f;		// the preview looks at this height of the effect
	const unsigned char PREVIEW_CAMERA = 201;	// its own camera (CCameraManager::AddCamera)
	const char * const PREVIEW_BACKGROUND = "d:/ymir work/ui/game/title/window/model_view_background.sub";

	struct STitle
	{
		DWORD dwIndex;
		BYTE bType;
		bool bPermanent;
		WORD wResource;
		DWORD dwDuration;
		DWORD dwColor;
		short sEffectZ;
		std::string stName;
		std::string stCondition;
		std::string stEffect;
		DWORD dwEffectCRC;		// registered once (0 = not yet / none)
		bool bEffectTried;
	};

	struct SPlate
	{
		bool bLoaded;
		bool bPlate;
		std::string stLeft, stMiddle, stRight;
		std::string stSprites;	// the frames' folder (d:/ymir work/...), "" none
		int iSpriteCount, iSpriteW, iSpriteH;
		SPlate() : bLoaded(false), bPlate(false), iSpriteCount(0), iSpriteW(0), iSpriteH(0) {}
	};

	// who wears what (VISUAL), and the effect put on that instance
	struct SWear
	{
		DWORD dwTitle;
		CInstanceBase * pkInst;
		DWORD dwEffect;		// the actor's attached effect index (0 none)
		float fEffectZ;
		SWear() : dwTitle(0), pkInst(NULL), dwEffect(0), fEffectZ(0.0f) {}
	};

	// the name tail's pictures of a VID
	struct STail
	{
		DWORD dwTitle;
		CGraphicTextInstance * pText;
		CGraphicExpandedImageInstance * pLeft;
		CGraphicExpandedImageInstance * pMiddle;
		CGraphicExpandedImageInstance * pRight;
		CGraphicExpandedImageInstance * pSprite;
		WORD wResource;
		int iFrame;
		DWORD dwNextFrame;
		bool bShown;	// arranged this frame (Render draws only those)
		STail() : dwTitle(0), pText(NULL), pLeft(NULL), pMiddle(NULL), pRight(NULL), pSprite(NULL), wResource(0), iFrame(0),
			dwNextFrame(0), bShown(false) {}
	};

	std::vector<DWORD> s_kOrder;
	std::map<DWORD, STitle> s_kTitles;
	std::map<WORD, SPlate> s_kPlates;
	std::map<DWORD, DWORD> s_kOwned;	// title -> end time
	DWORD s_dwEquipped = 0;
	bool s_bDataReceived = false;
	bool s_bShowOthers = true;
	PyObject * s_poHandler = NULL;
	std::map<DWORD, SWear> s_kWear;
	std::map<DWORD, STail> s_kTails;

	const STitle * FindTitle(DWORD dwIndex)
	{
		std::map<DWORD, STitle>::const_iterator it = s_kTitles.find(dwIndex);
		return it == s_kTitles.end() ? NULL : &it->second;
	}

	void CallHandler(const char * c_szFunc, PyObject * poArgs)
	{
		if (s_poHandler && Py_IsInitialized())
			PyCallClassMemberFunc(s_poHandler, c_szFunc, poArgs);
		else
			Py_XDECREF(poArgs);
	}

	std::string Trim(const std::string & s)
	{
		const size_t a = s.find_first_not_of(" \t\r\n\"");
		if (a == std::string::npos)
			return "";
		const size_t b = s.find_last_not_of(" \t\r\n\"");
		return s.substr(a, b - a + 1);
	}

	// "ui/game/..." / "effect/..." -> "d:/ymir work/ui/game/...", backslashes -> slashes
	std::string YmirPath(std::string s)
	{
		for (size_t i = 0; i < s.size(); ++i)
			if (s[i] == '\\')
				s[i] = '/';
		if (s.empty() || s.find(':') != std::string::npos)
			return s;
		return std::string("d:/ymir work/") + s;
	}

	// title_<res>.sub: "key<tab>value" lines (not a sub image - the package's own format)
	const SPlate & Plate(WORD wResource)
	{
		SPlate & p = s_kPlates[wResource];
		if (p.bLoaded)
			return p;
		p.bLoaded = true;
		char szPath[128];
		_snprintf(szPath, sizeof(szPath), "d:/ymir work/ui/game/title/titles/title_%04u.sub", (unsigned int) wResource);
		szPath[sizeof(szPath) - 1] = '\0';
		CMappedFile kFile;
		LPCVOID pData = NULL;
		if (!CEterPackManager::Instance().Get(kFile, szPath, &pData) || !pData)
			return p;
		CMemoryTextFileLoader kLoader;
		kLoader.Bind(kFile.Size(), pData);
		for (DWORD i = 0; i < kLoader.GetLineCount(); ++i)
		{
			const std::string & c_rLine = kLoader.GetLineString(i);
			if (c_rLine.empty() || c_rLine[0] == '#')
				continue;
			const size_t sep = c_rLine.find_first_of(" \t");
			if (sep == std::string::npos)
				continue;
			const std::string stKey = c_rLine.substr(0, sep);
			const std::string stValue = Trim(c_rLine.substr(sep + 1));
			if (stKey == "left_image")
				p.stLeft = YmirPath(stValue);
			else if (stKey == "middle_image")
				p.stMiddle = YmirPath(stValue);
			else if (stKey == "right_image")
				p.stRight = YmirPath(stValue);
			else if (stKey == "sprites")
				p.stSprites = YmirPath(stValue);
			else if (stKey == "sprites_count")
				p.iSpriteCount = atoi(stValue.c_str());
			else if (stKey == "sprite_size_x")
				p.iSpriteW = atoi(stValue.c_str());
			else if (stKey == "sprite_size_y")
				p.iSpriteH = atoi(stValue.c_str());
		}
		p.bPlate = !p.stLeft.empty() && !p.stMiddle.empty() && !p.stRight.empty();
		if (!p.stSprites.empty() && p.stSprites[p.stSprites.size() - 1] != '/')
			p.stSprites += "/";
		if (p.iSpriteCount <= 0 || p.iSpriteCount > 99)
			p.stSprites.clear();
		return p;
	}

	CGraphicImage * Image(const std::string & c_rPath)
	{
		if (c_rPath.empty())
			return NULL;
		CResource * pRes = CResourceManager::Instance().GetResourcePointer(c_rPath.c_str());
		if (!pRes || !pRes->IsType(CGraphicImage::Type()))
			return NULL;
		return static_cast<CGraphicImage *>(pRes);
	}

	CGraphicImage * SpriteFrame(const SPlate & p, int iFrame)
	{
		char szPath[192];
		_snprintf(szPath, sizeof(szPath), "%s%02d.sub", p.stSprites.c_str(), iFrame);
		szPath[sizeof(szPath) - 1] = '\0';
		return Image(szPath);
	}

	DWORD EffectCRC(STitle & t)
	{
		if (!t.bEffectTried)
		{
			t.bEffectTried = true;
			t.dwEffectCRC = 0;
			if (!t.stEffect.empty() && !CEffectManager::Instance().RegisterEffect2(t.stEffect.c_str(), &t.dwEffectCRC, true))
			{
				TraceError("Mt2009Titles: title %u - effect %s not loaded", t.dwIndex, t.stEffect.c_str());
				t.dwEffectCRC = 0;
			}
		}
		return t.dwEffectCRC;
	}

	bool IsMainVID(DWORD dwVID)
	{
		CInstanceBase * pkMain = CPythonCharacterManager::Instance().GetMainInstancePtr();
		return pkMain && pkMain->GetVirtualID() == dwVID;
	}

	// ------------------------------------------------------------------------------------------- name tail pictures

	void ClearTail(STail & t)
	{
		if (t.pText)
			CGraphicTextInstance::Delete(t.pText);
		if (t.pLeft)
			CGraphicExpandedImageInstance::Delete(t.pLeft);
		if (t.pMiddle)
			CGraphicExpandedImageInstance::Delete(t.pMiddle);
		if (t.pRight)
			CGraphicExpandedImageInstance::Delete(t.pRight);
		if (t.pSprite)
			CGraphicExpandedImageInstance::Delete(t.pSprite);
		t = STail();
	}

	CGraphicExpandedImageInstance * NewImage(CGraphicImage * pImage)
	{
		if (!pImage)
			return NULL;
		CGraphicExpandedImageInstance * p = CGraphicExpandedImageInstance::New();
		p->SetImagePointer(pImage);
		return p;
	}

	// the tail's pictures for a title (none for an effect title, or a title the catalogue does not know yet)
	void BuildTail(STail & t, DWORD dwTitle)
	{
		ClearTail(t);
		t.dwTitle = dwTitle;
		const STitle * pTitle = FindTitle(dwTitle);
		if (!pTitle || pTitle->bType == TYPE_EFFECT || !ms_pFont)
			return;
		t.pText = CGraphicTextInstance::New();
		t.pText->SetTextPointer(ms_pFont);
		t.pText->SetOutline(true);
		t.pText->SetHorizonalAlign(CGraphicTextInstance::HORIZONTAL_ALIGN_CENTER);
		t.pText->SetVerticalAlign(CGraphicTextInstance::VERTICAL_ALIGN_CENTER);
		t.pText->SetValue(pTitle->stName.c_str());
		const DWORD c = pTitle->dwColor ? pTitle->dwColor : 0xFFD6E3F3;
		t.pText->SetColor(((c >> 16) & 0xff) / 255.0f, ((c >> 8) & 0xff) / 255.0f, (c & 0xff) / 255.0f, 1.0f);
		t.pText->Update();
		if (pTitle->bType != TYPE_NAMEPLATE)
			return;
		const SPlate & p = Plate(pTitle->wResource);
		if (p.bPlate)
		{
			t.pLeft = NewImage(Image(p.stLeft));
			t.pMiddle = NewImage(Image(p.stMiddle));
			t.pRight = NewImage(Image(p.stRight));
			if (!t.pLeft || !t.pMiddle || !t.pRight)	// a picture missing: the name alone
			{
				CGraphicExpandedImageInstance ** apPart[3] = { &t.pLeft, &t.pMiddle, &t.pRight };
				for (int i = 0; i < 3; ++i)
					if (*apPart[i])
					{
						CGraphicExpandedImageInstance::Delete(*apPart[i]);
						*apPart[i] = NULL;
					}
			}
		}
		if (!p.stSprites.empty())
		{
			t.pSprite = NewImage(SpriteFrame(p, 0));
			t.wResource = pTitle->wResource;
			t.iFrame = 0;
			t.dwNextFrame = ELTimer_GetMSec() + SPRITE_FRAME_MS;
		}
	}

	// ---------------------------------------------------------------------------------- over-head effects (sync)

	void DetachWear(SWear & w)
	{
		if (w.dwEffect && w.pkInst && CPythonCharacterManager::Instance().GetInstancePtr(w.pkInst->GetVirtualID()) == w.pkInst)
			w.pkInst->GetGraphicThingInstanceRef().DettachEffect(w.dwEffect);
		w.dwEffect = 0;
		w.pkInst = NULL;
	}

	// each frame: every worn effect title on its current instance (a new instance gets it again)
	void SyncEffects()
	{
		CPythonCharacterManager & rkChrMgr = CPythonCharacterManager::Instance();
		CEffectManager & rkEftMgr = CEffectManager::Instance();
		for (std::map<DWORD, SWear>::iterator it = s_kWear.begin(); it != s_kWear.end(); ++it)
		{
			SWear & w = it->second;
			CInstanceBase * pkInst = rkChrMgr.GetInstancePtr(it->first);
			std::map<DWORD, STitle>::iterator ft = s_kTitles.find(w.dwTitle);
			const bool bWant = pkInst && pkInst->IsPC() && ft != s_kTitles.end() && ft->second.bType == TYPE_EFFECT &&
				!pkInst->IsInvisibility() && (s_bShowOthers || IsMainVID(it->first));
			if (!bWant)
			{
				if (w.dwEffect)
					DetachWear(w);
				continue;
			}
			const float fZ = pkInst->GetBaseHeight() + pkInst->GetGraphicThingInstanceRef().GetHeight() + EFFECT_HEAD_Z + ft->second.sEffectZ;
			const bool bAlive = w.dwEffect && w.pkInst == pkInst && rkEftMgr.IsAliveEffect(w.dwEffect);
			if (bAlive && fabsf(fZ - w.fEffectZ) < 5.0f)
				continue;
			if (bAlive)
				DetachWear(w);
			w.dwEffect = 0;
			const DWORD dwCRC = EffectCRC(ft->second);
			if (!dwCRC)
				continue;
			const D3DXVECTOR3 v3Pos(0.0f, 0.0f, fZ);
			w.dwEffect = pkInst->GetGraphicThingInstanceRef().AttachEffectByID(0, NULL, dwCRC, &v3Pos);
			w.pkInst = pkInst;
			w.fEffectZ = fZ;
		}
	}

	void ClearWear()
	{
		for (std::map<DWORD, SWear>::iterator it = s_kWear.begin(); it != s_kWear.end(); ++it)
			DetachWear(it->second);
		s_kWear.clear();
		for (std::map<DWORD, STail>::iterator it = s_kTails.begin(); it != s_kTails.end(); ++it)
			ClearTail(it->second);
		s_kTails.clear();
	}

	// ----------------------------------------------------------------------------------------------- the preview
#if defined(RENDER_TARGET)
	struct CMatrixAccess : public CGraphicBase
	{
		static LPDIRECT3DDEVICE9 Device()	{ return ms_lpd3dDevice; }
		static D3DXMATRIX & View()			{ return ms_matView; }
		static D3DXMATRIX & Proj()			{ return ms_matProj; }
		static D3DXMATRIX & InverseView()	{ return ms_matInverseView; }
	};

	UI::CRenderTarget::TRenderHook s_pfnPrevHook = NULL;
	DWORD s_dwPreviewTitle = 0;
	bool s_bPreviewShow = false;
	CEffectInstance * s_pkPreview = NULL;
	CGraphicImageInstance * s_pkPreviewBackground = NULL;
	bool s_bCameraAdded = false;

	void PreviewDestroyEffect()
	{
		if (s_pkPreview)
			CEffectManager::Instance().DestroyUnsafeEffectInstance(s_pkPreview);
		s_pkPreview = NULL;
	}

	void PreviewCreateEffect()
	{
		PreviewDestroyEffect();
		std::map<DWORD, STitle>::iterator it = s_kTitles.find(s_dwPreviewTitle);
		if (it == s_kTitles.end() || it->second.bType != TYPE_EFFECT)
			return;
		const DWORD dwCRC = EffectCRC(it->second);
		if (!dwCRC)
			return;
		CEffectManager::Instance().CreateUnsafeEffectInstance(dwCRC, &s_pkPreview);
		if (!s_pkPreview)
			return;
		D3DXMATRIX m;
		D3DXMatrixIdentity(&m);
		s_pkPreview->SetGlobalMatrix(m);
		s_pkPreview->Show();
	}

	// the game loop: the preview's effect lives on (an effect that ended starts again)
	void PreviewUpdate()
	{
		if (!s_bPreviewShow || !s_dwPreviewTitle)
			return;
		if (!s_pkPreview)
			PreviewCreateEffect();
		if (!s_pkPreview)
			return;
		s_pkPreview->Update();
		if (!s_pkPreview->isAlive())
			PreviewCreateEffect();
	}

	void PreviewDraw(const RECT & rcWindow, const RECT * pClipRect)
	{
		CRenderTargetManager & rkRTMgr = CRenderTargetManager::Instance();
		if (!rkRTMgr.GetRenderTargetTexture(PREVIEW_TARGET) && !rkRTMgr.CreateA8R8G8B8Texture(PREVIEW_TEX_W, PREVIEW_TEX_H, PREVIEW_TARGET))
			return;
		CGraphicRenderTargetTexture * pTexture = rkRTMgr.GetRenderTargetTexture(PREVIEW_TARGET);
		if (!pTexture || !pTexture->GetRenderTargetTexture())
			return;
		LPDIRECT3DDEVICE9 pDevice = CMatrixAccess::Device();
		if (!pDevice || pDevice->TestCooperativeLevel() != D3D_OK)
			return;

		D3DVIEWPORT9 kOldViewport;
		pDevice->GetViewport(&kOldViewport);
		if (!rkRTMgr.ChangeRenderTarget(PREVIEW_TARGET))
			return;
		D3DVIEWPORT9 kViewport = { 0, 0, PREVIEW_TEX_W, PREVIEW_TEX_H, 0.0f, 1.0f };
		pDevice->SetViewport(&kViewport);
		pDevice->Clear(0, NULL, D3DCLEAR_TARGET | D3DCLEAR_ZBUFFER, 0x00000000, 1.0f, 0);

		const D3DXMATRIX matOldView = CMatrixAccess::View();
		const D3DXMATRIX matOldProj = CMatrixAccess::Proj();
		const D3DXMATRIX matOldInverseView = CMatrixAccess::InverseView();
		D3DXMATRIX matOldViewT, matOldProjT, matOldWorldT;
		STATEMANAGER.GetTransform(D3DTS_VIEW, &matOldViewT);
		STATEMANAGER.GetTransform(D3DTS_PROJECTION, &matOldProjT);
		STATEMANAGER.GetTransform(D3DTS_WORLD, &matOldWorldT);

		// the window's background into the texture (2D, the texture's pixels)
		if (!s_pkPreviewBackground)
		{
			CGraphicImage * pImage = Image(PREVIEW_BACKGROUND);
			if (pImage)
			{
				s_pkPreviewBackground = CGraphicImageInstance::New();
				s_pkPreviewBackground->SetImagePointer(pImage);
			}
		}
		if (s_pkPreviewBackground && !s_pkPreviewBackground->IsEmpty())
		{
			D3DXMATRIX matOrtho, matIdentity;
			D3DXMatrixOrthoOffCenterLH(&matOrtho, 0.0f, float(PREVIEW_TEX_W), float(PREVIEW_TEX_H), 0.0f, 0.0f, 1.0f);
			D3DXMatrixIdentity(&matIdentity);
			CPythonGraphic::Instance().SetInterfaceRenderState();
			STATEMANAGER.SetTransform(D3DTS_PROJECTION, &matOrtho);
			STATEMANAGER.SetTransform(D3DTS_VIEW, &matIdentity);
			STATEMANAGER.SetTransform(D3DTS_WORLD, &matIdentity);
			const int iW = s_pkPreviewBackground->GetWidth(), iH = s_pkPreviewBackground->GetHeight();
			s_pkPreviewBackground->SetPosition(0.0f, 0.0f);
			s_pkPreviewBackground->SetScale(iW > 0 ? float(PREVIEW_TEX_W) / iW : 1.0f, iH > 0 ? float(PREVIEW_TEX_H) / iH : 1.0f);
			s_pkPreviewBackground->Render();
		}

		// the effect: its own camera (the particles face it), an orthographic view of PREVIEW_VIEW_W units across
		if (s_pkPreview)
		{
			CCameraManager & rkCamMgr = CCameraManager::Instance();
			if (!s_bCameraAdded)
			{
				rkCamMgr.AddCamera(PREVIEW_CAMERA);	// false when it is there already - either way it is
				s_bCameraAdded = true;
			}
			rkCamMgr.SetCurrentCamera(PREVIEW_CAMERA);
			CCamera * pCam = rkCamMgr.GetCurrentCamera();
			if (pCam)
			{
				pCam->SetViewParams(D3DXVECTOR3(0.0f, -1000.0f, PREVIEW_CENTER_Z), D3DXVECTOR3(0.0f, 0.0f, PREVIEW_CENTER_Z),
					D3DXVECTOR3(0.0f, 0.0f, 1.0f));
				CPythonGraphic::Instance().UpdateViewMatrix();
				const float fViewH = PREVIEW_VIEW_W * float(PREVIEW_TEX_H) / float(PREVIEW_TEX_W);
				D3DXMatrixOrthoRH(&CMatrixAccess::Proj(), PREVIEW_VIEW_W, fViewH, -10000.0f, 10000.0f);
				STATEMANAGER.SetTransform(D3DTS_PROJECTION, &CMatrixAccess::Proj());
				D3DXMATRIX matIdentity;
				D3DXMatrixIdentity(&matIdentity);
				STATEMANAGER.SetTransform(D3DTS_WORLD, &matIdentity);

				Frustum kOldFrustum = CScreen::GetFrustum();
				D3DXMATRIX matViewProj = CMatrixAccess::View() * CMatrixAccess::Proj();
				CScreen::GetFrustum().BuildViewFrustum(matViewProj);

				DWORD dwOldFog = FALSE, dwOldLighting = FALSE, dwOldZ = FALSE;
				STATEMANAGER.GetRenderState(D3DRS_FOGENABLE, &dwOldFog);
				STATEMANAGER.GetRenderState(D3DRS_LIGHTING, &dwOldLighting);
				STATEMANAGER.GetRenderState(D3DRS_ZENABLE, &dwOldZ);
				STATEMANAGER.SetRenderState(D3DRS_FOGENABLE, FALSE);
				STATEMANAGER.SetRenderState(D3DRS_LIGHTING, FALSE);
				STATEMANAGER.SetRenderState(D3DRS_ZENABLE, FALSE);
				STATEMANAGER.SetTexture(1, NULL);
				s_pkPreview->Render();
				STATEMANAGER.SetRenderState(D3DRS_ZENABLE, dwOldZ);
				STATEMANAGER.SetRenderState(D3DRS_LIGHTING, dwOldLighting);
				STATEMANAGER.SetRenderState(D3DRS_FOGENABLE, dwOldFog);

				CScreen::GetFrustum() = kOldFrustum;
			}
			rkCamMgr.ResetToPreviousCamera();
		}

		STATEMANAGER.SetTransform(D3DTS_WORLD, &matOldWorldT);
		STATEMANAGER.SetTransform(D3DTS_PROJECTION, &matOldProjT);
		STATEMANAGER.SetTransform(D3DTS_VIEW, &matOldViewT);
		CMatrixAccess::View() = matOldView;
		CMatrixAccess::Proj() = matOldProj;
		CMatrixAccess::InverseView() = matOldInverseView;

		rkRTMgr.ResetRenderTarget();
		pDevice->SetViewport(&kOldViewport);

		// the texture into the window, as the UI draws (Mt2009MonsterModel.cpp the same)
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
		pTexture->Render(const_cast<RECT *>(pClipRect));
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

	// UI::CRenderTarget's render hook: the preview's index here, any other to the hook before (the Monster Cards')
	bool RenderTargetHook(int iIndex, const RECT & rcWindow, const RECT * pClipRect)
	{
		if (iIndex != PREVIEW_TARGET)
			return s_pfnPrevHook ? s_pfnPrevHook(iIndex, rcWindow, pClipRect) : false;
		if (s_bPreviewShow)
			PreviewDraw(rcWindow, pClipRect);
		return true;
	}
#endif

	// ------------------------------------------------------------------------------------------------------ python

	PyObject * titleSetHandler(PyObject * poSelf, PyObject * poArgs)
	{
		PyObject * poHandler = NULL;
		if (!PyTuple_GetObject(poArgs, 0, &poHandler))
			return Py_BuildException();
		if (poHandler == Py_None)
			poHandler = NULL;
		Py_XINCREF(poHandler);
		Py_XDECREF(s_poHandler);
		s_poHandler = poHandler;
		return Py_BuildNone();
	}

	PyObject * titleRequestOpen(PyObject * poSelf, PyObject * poArgs)
	{
		CPythonNetworkStream::Instance().SendTitlePacket(TITLE_CG_OPEN, 0);
		return Py_BuildNone();
	}

	PyObject * titleRequestEquip(PyObject * poSelf, PyObject * poArgs)
	{
		int iTitle = 0;
		if (!PyTuple_GetInteger(poArgs, 0, &iTitle))
			return Py_BuildException();
		CPythonNetworkStream::Instance().SendTitlePacket(iTitle > 0 ? TITLE_CG_EQUIP : TITLE_CG_UNEQUIP, iTitle > 0 ? (DWORD) iTitle : 0);
		return Py_BuildNone();
	}

	PyObject * titleGetTitles(PyObject * poSelf, PyObject * poArgs)
	{
		PyObject * poList = PyList_New(0);
		for (size_t i = 0; i < s_kOrder.size(); ++i)
		{
			const STitle * t = FindTitle(s_kOrder[i]);
			if (!t)
				continue;
			PyObject * poRow = Py_BuildValue("(iissiiiI)", (int) t->dwIndex, (int) t->bType, t->stName.c_str(), t->stCondition.c_str(),
				t->bPermanent ? 1 : 0, (int) t->dwDuration, (int) t->wResource, (unsigned int) t->dwColor);
			PyList_Append(poList, poRow);
			Py_DECREF(poRow);
		}
		return poList;
	}

	PyObject * titleGetOwned(PyObject * poSelf, PyObject * poArgs)
	{
		PyObject * poList = PyList_New(0);
		for (std::map<DWORD, DWORD>::const_iterator it = s_kOwned.begin(); it != s_kOwned.end(); ++it)
		{
			PyObject * poRow = Py_BuildValue("(iI)", (int) it->first, (unsigned int) it->second);
			PyList_Append(poList, poRow);
			Py_DECREF(poRow);
		}
		return poList;
	}

	PyObject * titleGetEquipped(PyObject * poSelf, PyObject * poArgs)
	{
		return Py_BuildValue("i", (int) s_dwEquipped);
	}

	PyObject * titleIsDataReceived(PyObject * poSelf, PyObject * poArgs)
	{
		return Py_BuildValue("i", s_bDataReceived ? 1 : 0);
	}

	PyObject * titleGetPlate(PyObject * poSelf, PyObject * poArgs)
	{
		int iResource = 0;
		if (!PyTuple_GetInteger(poArgs, 0, &iResource) || iResource < 0 || iResource > 0xffff)
			return Py_BuildException();
		const SPlate & p = Plate((WORD) iResource);
		if (!p.bPlate)
			return Py_BuildValue("()");
		return Py_BuildValue("(ssssiii)", p.stLeft.c_str(), p.stMiddle.c_str(), p.stRight.c_str(), p.stSprites.c_str(),
			p.stSprites.empty() ? 0 : p.iSpriteCount, p.iSpriteW, p.iSpriteH);
	}

	PyObject * titleSetShowOthers(PyObject * poSelf, PyObject * poArgs)
	{
		int iShow = 1;
		if (!PyTuple_GetInteger(poArgs, 0, &iShow))
			return Py_BuildException();
		s_bShowOthers = iShow != 0;
		return Py_BuildNone();
	}

	PyObject * titleGetShowOthers(PyObject * poSelf, PyObject * poArgs)
	{
		return Py_BuildValue("i", s_bShowOthers ? 1 : 0);
	}

	PyObject * titlePreviewSelect(PyObject * poSelf, PyObject * poArgs)
	{
		int iTitle = 0;
		if (!PyTuple_GetInteger(poArgs, 0, &iTitle))
			return Py_BuildException();
#if defined(RENDER_TARGET)
		if ((DWORD) iTitle != s_dwPreviewTitle)
		{
			s_dwPreviewTitle = iTitle > 0 ? (DWORD) iTitle : 0;
			PreviewDestroyEffect();
		}
		const STitle * t = FindTitle(s_dwPreviewTitle);
		return Py_BuildValue("i", t && t->bType == TYPE_EFFECT && !t->stEffect.empty() ? 1 : 0);
#else
		return Py_BuildValue("i", 0);
#endif
	}

	PyObject * titlePreviewShow(PyObject * poSelf, PyObject * poArgs)
	{
		int iShow = 0;
		if (!PyTuple_GetInteger(poArgs, 0, &iShow))
			return Py_BuildException();
#if defined(RENDER_TARGET)
		s_bPreviewShow = iShow != 0;
		if (!s_bPreviewShow)
			PreviewDestroyEffect();
#endif
		return Py_BuildNone();
	}
}

// ---------------------------------------------------------------------------------------------- CPythonNetworkStream

bool CPythonNetworkStream::SendTitlePacket(BYTE bSubHeader, DWORD dwTitle)
{
	TPacketCGTitle kPacket;
	kPacket.bHeader = HEADER_CG_TITLE;
	kPacket.bSubHeader = bSubHeader;
	kPacket.dwTitle = dwTitle;
	if (!Send(sizeof(kPacket), &kPacket))
	{
		Tracef("SendTitlePacket Error\n");
		return false;
	}
	return SendSequence();
}

bool CPythonNetworkStream::RecvTitlePacket()
{
	TPacketGCTitle kPacket;
	if (!Recv(sizeof(kPacket), &kPacket))
		return false;
	if (kPacket.wSize < sizeof(kPacket))
		return false;
	std::vector<char> kData(kPacket.wSize - sizeof(kPacket));
	if (!kData.empty() && !Recv((int) kData.size(), &kData[0]))
		return false;
	const size_t uSize = kData.size();
	const char * c_pData = kData.empty() ? NULL : &kData[0];

	switch (kPacket.bSubHeader)
	{
		case TITLE_GC_TABLE:
		{
			if (uSize < kPacket.wCount * sizeof(TPacketGCTitleRow))
				break;
			s_kOrder.clear();
			std::map<DWORD, STitle> kOld;
			kOld.swap(s_kTitles);
			for (WORD i = 0; i < kPacket.wCount; ++i)
			{
				TPacketGCTitleRow r;
				memcpy(&r, c_pData + i * sizeof(TPacketGCTitleRow), sizeof(r));
				r.szName[sizeof(r.szName) - 1] = '\0';
				r.szCondition[sizeof(r.szCondition) - 1] = '\0';
				r.szEffect[sizeof(r.szEffect) - 1] = '\0';
				STitle t;
				t.dwIndex = r.dwTitle;
				t.bType = r.bType;
				t.bPermanent = r.bPermanent != 0;
				t.wResource = r.wResource;
				t.dwDuration = r.dwDuration;
				t.dwColor = r.dwColor;
				t.sEffectZ = r.sEffectZ;
				t.stName = r.szName;
				t.stCondition = r.szCondition;
				t.stEffect = r.szEffect;
				t.dwEffectCRC = 0;
				t.bEffectTried = false;
				std::map<DWORD, STitle>::const_iterator o = kOld.find(t.dwIndex);
				if (o != kOld.end() && o->second.stEffect == t.stEffect)
				{
					t.dwEffectCRC = o->second.dwEffectCRC;
					t.bEffectTried = o->second.bEffectTried;
				}
				s_kTitles[t.dwIndex] = t;
				s_kOrder.push_back(t.dwIndex);
			}
			s_bDataReceived = true;
			// the tails are built again (names / plates may have changed)
			for (std::map<DWORD, STail>::iterator it = s_kTails.begin(); it != s_kTails.end(); ++it)
				it->second.dwTitle = 0xFFFFFFFF;
			break;
		}

		case TITLE_GC_PLAYER:
		{
			if (uSize < kPacket.wCount * sizeof(TPacketGCTitleOwned))
				break;
			s_kOwned.clear();
			for (WORD i = 0; i < kPacket.wCount; ++i)
			{
				TPacketGCTitleOwned r;
				memcpy(&r, c_pData + i * sizeof(TPacketGCTitleOwned), sizeof(r));
				s_kOwned[r.dwTitle] = r.dwEndTime;
			}
			break;
		}

		case TITLE_GC_EQUIPPED:
		{
			if (uSize < sizeof(DWORD))
				break;
			memcpy(&s_dwEquipped, c_pData, sizeof(DWORD));
			CallHandler("OnTitleRefresh", Py_BuildValue("()"));
			break;
		}

		case TITLE_GC_NOTIFY:
		{
			if (uSize < sizeof(TPacketGCTitleNotify))
				break;
			TPacketGCTitleNotify r;
			memcpy(&r, c_pData, sizeof(r));
			CallHandler("OnTitleNotify", Py_BuildValue("(ii)", (int) r.bMessage, (int) r.dwTitle));
			break;
		}

		case TITLE_GC_VISUAL:
		{
			if (uSize < sizeof(TPacketGCTitleVisual))
				break;
			TPacketGCTitleVisual r;
			memcpy(&r, c_pData, sizeof(r));
			std::map<DWORD, SWear>::iterator it = s_kWear.find(r.dwVID);
			if (!r.dwTitle)
			{
				if (it != s_kWear.end())
				{
					DetachWear(it->second);
					s_kWear.erase(it);
				}
				break;
			}
			if (it == s_kWear.end())
				it = s_kWear.insert(std::make_pair(r.dwVID, SWear())).first;
			else if (it->second.dwTitle != r.dwTitle)
				DetachWear(it->second);
			it->second.dwTitle = r.dwTitle;
			break;
		}

		default:
			Tracef("RecvTitlePacket: unknown sub-header %u\n", (unsigned int) kPacket.bSubHeader);
			break;
	}
	return true;
}

// ------------------------------------------------------------------------------------------------------------ hooks

// PythonNetworkStreamPhaseGame.cpp SetGamePhase: a new game (login, warp) - the hello; what the old one knew goes
void Mt2009Titles_OnGamePhase()
{
	ClearWear();
	s_kOwned.clear();
	s_dwEquipped = 0;
	CPythonNetworkStream::Instance().SendTitlePacket(TITLE_CG_OPEN, 0);
}

// PythonApplication.cpp UpdateGame: the worn effects on their instances, the banners' frames, the preview's effect
void Mt2009Titles_Update()
{
	SyncEffects();
	const DWORD dwNow = ELTimer_GetMSec();
	for (std::map<DWORD, STail>::iterator it = s_kTails.begin(); it != s_kTails.end(); ++it)
	{
		STail & t = it->second;
		if (!t.pSprite || !t.wResource || dwNow < t.dwNextFrame)
			continue;
		const SPlate & p = Plate(t.wResource);
		if (p.stSprites.empty())
			continue;
		const int iNext = (t.iFrame + 1) % p.iSpriteCount;
		CGraphicImage * pImage = SpriteFrame(p, iNext);
		if (pImage)
		{
			t.pSprite->SetImagePointer(pImage);
			t.iFrame = iNext;
		}
		t.dwNextFrame = dwNow + SPRITE_FRAME_MS;
	}
#if defined(RENDER_TARGET)
	PreviewUpdate();
#endif
}

// PythonTextTail.cpp ArrangeTextTail: a shown character tail - its title's pictures above the top text line (the name,
// or the guild / personality line over it); fLineAbove: how far that line is over the name (0 = none)
void Mt2009Titles_ArrangeTail(DWORD dwVID, float x, float y, float z, float fLineAbove)
{
	std::map<DWORD, SWear>::const_iterator w = s_kWear.find(dwVID);
	std::map<DWORD, STail>::iterator ti = s_kTails.find(dwVID);
	const DWORD dwTitle = (w != s_kWear.end() && (s_bShowOthers || IsMainVID(dwVID))) ? w->second.dwTitle : 0;
	if (!dwTitle)
	{
		if (ti != s_kTails.end())
		{
			ClearTail(ti->second);
			s_kTails.erase(ti);
		}
		return;
	}
	if (ti == s_kTails.end())
		ti = s_kTails.insert(std::make_pair(dwVID, STail())).first;
	STail & t = ti->second;
	if (t.dwTitle != dwTitle || (!t.pText && FindTitle(dwTitle) && FindTitle(dwTitle)->bType != TYPE_EFFECT))
		BuildTail(t, dwTitle);
	t.bShown = t.pText != NULL;
	if (!t.bShown)
		return;

	int iTextW = 0, iTextH = 0;
	t.pText->GetTextSize(&iTextW, &iTextH);
	const float fCenterY = floorf(y - (fLineAbove > 0.0f ? fLineAbove + PLATE_LINE_GAP_EXTRA : PLATE_LINE_GAP));
	if (t.pLeft && t.pMiddle && t.pRight)
	{
		const float fLW = float(t.pLeft->GetWidth());
		const float fH = float(t.pLeft->GetHeight());
		const float fMiddle = float(iTextW);
		const float fTop = floorf(fCenterY - fH / 2.0f);
		const int iMiddleSrc = t.pMiddle->GetWidth();
		t.pLeft->SetPosition(floorf(x - fMiddle / 2.0f - fLW), fTop);
		t.pMiddle->SetPosition(floorf(x - fMiddle / 2.0f), fTop);
		t.pMiddle->SetScale(iMiddleSrc > 0 ? fMiddle / float(iMiddleSrc) : 1.0f, 1.0f);
		t.pRight->SetPosition(floorf(x + fMiddle / 2.0f), fTop);
		if (t.pSprite)
		{
			const SPlate & p = Plate(t.wResource);
			const float fSW = float(p.iSpriteW > 0 ? p.iSpriteW : t.pSprite->GetWidth());
			const float fSH = float(p.iSpriteH > 0 ? p.iSpriteH : t.pSprite->GetHeight());
			t.pSprite->SetPosition(floorf(x - fSW / 2.0f), floorf(fTop + fH - fSH - 3.0f));
		}
	}
	else if (t.pSprite)
	{
		const float fSW = float(t.pSprite->GetWidth()), fSH = float(t.pSprite->GetHeight());
		t.pSprite->SetPosition(floorf(x - fSW / 2.0f), floorf(fCenterY + 10.0f - fSH));
	}
	t.pText->SetPosition(x, fCenterY, z);
	t.pText->Update();
}

// PythonTextTail.cpp Render: after the name - the banner, the plate, the title's name
void Mt2009Titles_RenderTail(DWORD dwVID)
{
	std::map<DWORD, STail>::iterator ti = s_kTails.find(dwVID);
	if (ti == s_kTails.end() || !ti->second.bShown)
		return;
	STail & t = ti->second;
	if (t.pSprite)
		t.pSprite->Render();
	if (t.pLeft && t.pMiddle && t.pRight)
	{
		t.pLeft->Render();
		t.pMiddle->Render();
		t.pRight->Render();
	}
	if (t.pText)
		t.pText->Render();
	t.bShown = false;
}

// PythonTextTail.cpp DeleteCharacterTextTail / Clear: the tail's pictures go with it (VID 0: all)
void Mt2009Titles_DeleteTail(DWORD dwVID)
{
	if (!dwVID)
	{
		for (std::map<DWORD, STail>::iterator it = s_kTails.begin(); it != s_kTails.end(); ++it)
			ClearTail(it->second);
		s_kTails.clear();
		return;
	}
	std::map<DWORD, STail>::iterator ti = s_kTails.find(dwVID);
	if (ti == s_kTails.end())
		return;
	ClearTail(ti->second);
	s_kTails.erase(ti);
}

// PythonApplication.cpp Destroy
void Mt2009Titles_Destroy()
{
	ClearWear();
	Py_XDECREF(s_poHandler);
	s_poHandler = NULL;
#if defined(RENDER_TARGET)
	PreviewDestroyEffect();
	if (s_pkPreviewBackground)
		CGraphicImageInstance::Delete(s_pkPreviewBackground);
	s_pkPreviewBackground = NULL;
#endif
}

// UserInterface.cpp, after the modules: module titleSystem, app.MT2009_TITLES_EXE, the render target hook
void Mt2009Titles_RegisterPython()
{
	static PyMethodDef s_methods[] =
	{
		{ "SetHandler",			titleSetHandler,		METH_VARARGS },
		{ "RequestOpen",		titleRequestOpen,		METH_VARARGS },
		{ "RequestEquip",		titleRequestEquip,		METH_VARARGS },
		{ "GetTitles",			titleGetTitles,			METH_VARARGS },
		{ "GetOwned",			titleGetOwned,			METH_VARARGS },
		{ "GetEquipped",		titleGetEquipped,		METH_VARARGS },
		{ "IsDataReceived",		titleIsDataReceived,	METH_VARARGS },
		{ "GetPlate",			titleGetPlate,			METH_VARARGS },
		{ "SetShowOthers",		titleSetShowOthers,		METH_VARARGS },
		{ "GetShowOthers",		titleGetShowOthers,		METH_VARARGS },
		{ "PreviewSelect",		titlePreviewSelect,		METH_VARARGS },
		{ "PreviewShow",		titlePreviewShow,		METH_VARARGS },
		{ NULL, NULL, 0 },
	};
	PyObject * poModule = Py_InitModule("titleSystem", s_methods);
	PyModule_AddIntConstant(poModule, "TYPE_TEXT", TYPE_TEXT);
	PyModule_AddIntConstant(poModule, "TYPE_EFFECT", TYPE_EFFECT);
	PyModule_AddIntConstant(poModule, "TYPE_NAMEPLATE", TYPE_NAMEPLATE);
#if defined(RENDER_TARGET)
	PyModule_AddIntConstant(poModule, "RENDER_TARGET_INDEX", PREVIEW_TARGET);
	s_pfnPrevHook = UI::CRenderTarget::GetRenderHook();
	UI::CRenderTarget::SetRenderHook(&RenderTargetHook);
#else
	PyModule_AddIntConstant(poModule, "RENDER_TARGET_INDEX", -1);
#endif
	PyObject * poApp = PyImport_AddModule("app");	// borrowed
	if (poApp)
		PyModule_AddIntConstant(poApp, "MT2009_TITLES_EXE", 1);
}
#else
void Mt2009Titles_RegisterPython() {}
#endif
