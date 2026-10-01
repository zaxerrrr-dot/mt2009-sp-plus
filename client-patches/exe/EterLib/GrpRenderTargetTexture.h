#pragma once
// MT2009_PLUS_MINIGAMES_V1: render target texture (after Owsap v6.2.6 / blackdragonx61), Direct3D 9 port.

#if defined(RENDER_TARGET)
#include "GrpTexture.h"

class CGraphicRenderTargetTexture : public CGraphicTexture
{
public:
	CGraphicRenderTargetTexture();
	virtual ~CGraphicRenderTargetTexture();

	void Initialize();
	void Destroy();

	bool Create(DWORD width, DWORD height, D3DFORMAT format, D3DFORMAT depthFormat);
	void CreateTextures();
	bool CreateRenderTexture(DWORD width, DWORD height, D3DFORMAT format);
	bool CreateRenderDepthStencil(DWORD width, DWORD height, D3DFORMAT depthFormat);
	bool SetRenderTarget();
	void ResetRenderTarget();
	void SetRenderingRect(RECT* rect);
	const RECT& GetRenderingRect() const;
	LPDIRECT3DTEXTURE9 GetRenderTargetTexture() const;
	void ReleaseTextures();
	static void Clear(D3DCOLOR color);

	void Render(RECT* pClipRect = NULL) const;

private:
	LPDIRECT3DTEXTURE9 m_lpd3dRenderTexture;
	LPDIRECT3DSURFACE9 m_lpd3dRenderTargetSurface;
	LPDIRECT3DSURFACE9 m_lpd3dDepthSurface;
	LPDIRECT3DSURFACE9 m_lpd3dOriginalRenderTarget;
	LPDIRECT3DSURFACE9 m_lpd3dOldDepthBufferSurface;

	D3DFORMAT m_d3dFormat;
	D3DFORMAT m_depthStencilFormat;

	RECT m_renderRect;
};
#endif
