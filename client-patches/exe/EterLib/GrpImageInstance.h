#pragma once

#include "GrpImage.h"
#include "GrpIndexBuffer.h"
#include "GrpVertexBufferDynamic.h"
#include "Pool.h"

class CGraphicImageInstance
{
	public:
		static DWORD Type();
		BOOL IsType(DWORD dwType);

	public:
		CGraphicImageInstance();
		virtual ~CGraphicImageInstance();

		void Destroy();

		void Render(RECT* pClipRect = NULL);

		void SetDiffuseColor(float fr, float fg, float fb, float fa);
		void SetPosition(float fx, float fy);

		void SetImagePointer(CGraphicImage* pImage);
		void ReloadImagePointer(CGraphicImage* pImage);
		bool IsEmpty() const;

		int GetWidth();
		int GetHeight();

		CGraphicTexture * GetTexturePointer();
		const CGraphicTexture &	GetTextureReference() const;
		CGraphicImage * GetGraphicImagePointer();

		bool operator == (const CGraphicImageInstance & rhs) const;

#ifdef ENABLE_SET_ATLAS_SCALE
#ifdef ENABLE_OWSAP_WNDMGR_EX
		virtual void SetScale(float fx, float fy); // MT2009_PLUS_MINIGAMES_V1: virtual (expanded image has its own scale)
#else
		void SetScale(float fx, float fy);
#endif
		void SetScale(D3DXVECTOR2 v2Scale);
		const D3DXVECTOR2& GetScale() const;
		void SetScalePercent(BYTE byPercent);
		void SetScalePivotCenter(bool bScalePivotCenter);
#endif

#ifdef ENABLE_OWSAP_WNDMGR_EX
		// MT2009_PLUS_MINIGAMES_V1
		void LeftRightReverse();
		void RenderCoolTime(float fCoolTime);
		D3DXCOLOR& GetDiffuseColor() { return m_DiffuseColor; }
	protected:
		void __RenderCoolTime(float fCoolTime, const D3DXVECTOR2& v2Scale);
		bool m_bLeftRightReverse;
#endif

	protected:
		void Initialize();

		virtual void OnRender(RECT* pClipRect);
		virtual void OnSetImagePointer();

		virtual BOOL OnIsType(DWORD dwType);

	protected:
		D3DXCOLOR m_DiffuseColor;
		D3DXVECTOR2 m_v2Position;

		CGraphicImage::TRef m_roImage;

#ifdef ENABLE_SET_ATLAS_SCALE
		D3DXVECTOR2 m_v2Scale;
		bool m_bScalePivotCenter;
#endif

	public:
		static void CreateSystem(UINT uCapacity);
		static void DestroySystem();

		static CGraphicImageInstance* New();
		static void Delete(CGraphicImageInstance* pkImgInst);

		static CDynamicPool<CGraphicImageInstance>		ms_kPool;
};
//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f

// Files shared by GameCore.top
