#pragma once

#include "PythonBackground.h"

class CPythonMiniMap : public CScreen, public CSingleton<CPythonMiniMap>
{
	public:
		enum
		{
			EMPIRE_NUM = 4,

			MINI_WAYPOINT_IMAGE_COUNT = 12,
			WAYPOINT_IMAGE_COUNT = 15,
			TARGET_MARK_IMAGE_COUNT = 2,
		};
		enum
		{
			TYPE_OPC,
			TYPE_OPCPVP,
			TYPE_OPCPVPSELF,
			TYPE_NPC,
			TYPE_MONSTER,
			TYPE_WARP,
			TYPE_WAYPOINT,
			TYPE_PARTY,
			TYPE_EMPIRE,
			TYPE_EMPIRE_END = TYPE_EMPIRE + EMPIRE_NUM,
			TYPE_TARGET,
			TYPE_COUNT,
		};

	public:
		CPythonMiniMap();
		virtual ~CPythonMiniMap();

		void Destroy();
		bool Create();

		bool IsAtlas();
		bool CanShow();
		bool CanShowAtlas();

		void SetMiniMapSize(float fWidth, float fHeight);
		void SetScale(float fScale);
		void ScaleUp();
		void ScaleDown();

		void SetCenterPosition(float fCenterX, float fCenterY);

		void Update(float fCenterX, float fCenterY);
		void Render(float fScreenX, float fScreenY);

		void Show();
		void Hide();

		bool GetPickedInstanceInfo(float fScreenX, float fScreenY, std::string & rReturnName, float * pReturnPosX, float * pReturnPosY, DWORD * pdwTextColor);

		// Atlas
		bool LoadAtlas();
		void UpdateAtlas();
		void RenderAtlas(float fScreenX, float fScreenY);
		void ShowAtlas();
		void HideAtlas();

		bool GetAtlasInfo(float fScreenX, float fScreenY, std::string & rReturnString, float * pReturnPosX, float * pReturnPosY, DWORD * pdwTextColor, DWORD * pdwGuildID);
		bool GetAtlasSize(float * pfSizeX, float * pfSizeY);
		bool GetAtlasMaxSize(float* pfSizeX, float* pfSizeY);

		void AddObserver(DWORD dwVID, float fSrcX, float fSrcY);
		void MoveObserver(DWORD dwVID, float fDstX, float fDstY);
		void RemoveObserver(DWORD dwVID);
		// WayPoint
		void AddWayPoint(BYTE byType, DWORD dwID, float fX, float fY, std::string strText, DWORD dwChrVID=0);
		void RemoveWayPoint(DWORD dwID);

		// SignalPoint
		void AddSignalPoint(float fX, float fY);
		void ClearAllSignalPoint();

		void RegisterAtlasWindow(PyObject* poHandler);
		void UnregisterAtlasWindow();
		void OpenAtlasWindow();
		void SetAtlasCenterPosition(int x, int y);

		// NPC List
		void ClearAtlasMarkInfo();
		void RegisterAtlasMark(BYTE byType, const char * c_szName, long lx, long ly);

		// Guild
		void ClearGuildArea();
		void RegisterGuildArea(DWORD dwID, DWORD dwGuildID, long x, long y, long width, long height);
		DWORD GetGuildAreaID(DWORD x, DWORD y);

		// Target
		void CreateTarget(int iID, const char * c_szName);
		void CreateTarget(int iID, const char * c_szName, long x, long y);
		void CreateTarget(int iID, const char * c_szName, DWORD dwVID);
		void UpdateTarget(int iID, int ix, int iy);
		void DeleteTarget(int iID);
#ifdef ENABLE_SET_ATLAS_SCALE
		void SetAtlasScale(float fx, float fy);
		void UpdateAtlasMarks(D3DXVECTOR2 oldScale);
#endif
#ifdef ENABLE_NPC_LOCATION_HELPER
		// MT2009_PLUS_NPC_LOCATION_HELPER_V1 (Lokalizator NPC, Autor: Best Studio): the helper's atlas view - the same
		// atlas image, zoomed (1..3) and panned inside a viewport, NPC marks of any map, the chosen NPC's mark and the
		// arrow under the character. Positions are map-local pixels (as the atlas marks); "render pos" is the
		// top-left of the viewport inside the zoomed image.
		enum
		{
			SQUARED_ATLAS_SIZE = 352,
			ATLAS_TYPE_SMALL = 0,
			ATLAS_TYPE_NPC_LOCATION_HELPER = 1,
			ATLAS_TYPE_DONT_SHOW = 2,
			NPC_LOCATION_HELPER_TARGET_WAYPOINT = 0x4E4C4801,
			ATLAS_HELPER_MY_POSITION_IMAGE_COUNT = 7,
			ATLAS_HELPER_PLAYER_MARK_SCALE_PERCENT = 150,
			ATLAS_HELPER_ORANGE_MARK_SCALE_PERCENT = 140,
		};

		bool LoadAtlasForMapName(const char* c_szMapName);
		void SetAtlasNpcHelperView(bool bNpcHelperView);
		bool IsAtlasNpcHelperView() const { return m_bAtlasNpcHelperView; }
		bool IsShowAtlas() const { return m_bShowAtlas; }

		void SetAtlasHelperScale(float fScale);
		float GetAtlasHelperScale() const { return m_fAtlasHelperScale; }
		void AtlasScaleUp();
		void AtlasScaleDown();
		void ChangeAtlasRenderPos(float fX, float fY);
		void CenterAtlasRenderPos();
		void GetAtlasRenderPos(float* pfX, float* pfY) const;
		void GetAtlasPanExtents(float* pfMinX, float* pfMaxX, float* pfMinY, float* pfMaxY) const;
		void GetAtlasMaxPos(float* pfMaxX, float* pfMaxY) const;
		void ConvertGlobalPosToAtlasPos(float fMapX, float fMapY, float* pfAtlasX, float* pfAtlasY) const;
		float GetAtlasWidthHeightRatio() const;
		void SetAtlasHelperViewportSize(float fWidth, float fHeight);
		void GetAtlasHelperViewportSize(float* pfWidth, float* pfHeight) const;
		void SetAtlasScreenOrigin(float fScreenX, float fScreenY);
		void CenterAtlasOnMapPos(float fMapX, float fMapY);

		void SelectNPC(long lMapIndex, DWORD dwVnum, long lX, long lY, const char* c_szMapName);
		void UnselectNPC();
		bool IsNPCSelected() const { return m_bNPCSelected; }
		void GetSelectedNPCPos(long* plX, long* plY) const;
		void TickNPCLocationDirectionEffect();
#endif

	protected:
		void __Initialize();
		void __SetPosition();
		void __LoadAtlasMarkInfo();
#ifdef ENABLE_NPC_LOCATION_HELPER
		void __LoadAtlasMarkInfoForMap(const char* c_szMapName);
		void __MapPosToHelperAtlasImagePos(float fMapX, float fMapY, float* pfImgX, float* pfImgY) const;
		void __CalcAtlasHelperScreenPos(float fMapX, float fMapY, float* pfScreenX, float* pfScreenY) const;
		void __GetAtlasHelperPanExtents(float& fMinX, float& fMaxX, float& fMinY, float& fMaxY) const;
		void __ClampAtlasRenderPos();
		float __GetAtlasHelperViewportW() const;
		float __GetAtlasHelperViewportH() const;
		void __ApplyAtlasHelperScaleAtPlayerFocal(float fNewScale);
		void __ResetAtlasHelperImageScale();
		bool __ReloadCurrentAtlasKeepGuildArea();
		bool __IsAtlasHelperShowingCurrentMap() const;
		bool __IsSelectedNPCOnCurrentMap() const;
		void __RenderAtlasForNpcLocationHelper();
		void __RenderAtlasHelperMarks();
		bool __GetAtlasHelperInfo(float fScreenX, float fScreenY, std::string & rReturnString, float * pReturnPosX, float * pReturnPosY, DWORD * pdwTextColor, DWORD * pdwGuildID);
		bool __EnsureNPCLocationDirectionEffectRegistered();
		void __ClearNPCLocationDirectionEffect();
		void __SpawnNPCLocationDirectionEffect();
		void __UpdateNPCLocationDirectionEffect();
#endif

		void __RenderWayPointMark(int ixCenter, int iyCenter);
		void __RenderMiniWayPointMark(int ixCenter, int iyCenter);
		void __RenderTargetMark(int ixCenter, int iyCenter);

		void __GlobalPositionToAtlasPosition(long lx, long ly, float * pfx, float * pfy);

	protected:
		// Atlas
		typedef struct SAtlasMarkInfo
		{
			BYTE m_byType;
			DWORD m_dwID; // For WayPoint
			float m_fX;
			float m_fY;
			float m_fScreenX;
			float m_fScreenY;
			float m_fMiniMapX;
			float m_fMiniMapY;
			DWORD m_dwChrVID;
			std::string m_strText;
		} TAtlasMarkInfo;

		// GuildArea
		typedef struct SGuildAreaInfo
		{
			DWORD dwGuildID;
			long lx, ly;
			long lwidth, lheight;

			float fsxRender, fsyRender;
			float fexRender, feyRender;
		} TGuildAreaInfo;

		struct SObserver
		{
			float fCurX;
			float fCurY;
			float fSrcX;
			float fSrcY;
			float fDstX;
			float fDstY;

			DWORD dwSrcTime;
			DWORD dwDstTime;
		};

		typedef struct SMarkPosition
		{
			float	m_fX;
			float	m_fY;
			UINT	m_eNameColor;
		} TMarkPosition;

		typedef std::vector<TMarkPosition>				TInstanceMarkPositionVector;
		typedef TInstanceMarkPositionVector::iterator	TInstancePositionVectorIterator;

	protected:
		bool __GetWayPoint(DWORD dwID, TAtlasMarkInfo ** ppkInfo);
		void __UpdateWayPoint(TAtlasMarkInfo * pkInfo, int ix, int iy);

	protected:
		float							m_fWidth;
		float							m_fHeight;

		float							m_fScale;

		float							m_fCenterX;
		float							m_fCenterY;

		float							m_fCenterCellX;
		float							m_fCenterCellY;

		float							m_fScreenX;
		float							m_fScreenY;

		float							m_fMiniMapRadius;

		LPDIRECT3DTEXTURE9				m_lpMiniMapTexture[AROUND_AREA_NUM];

		CGraphicImageInstance			m_MiniMapFilterGraphicImageInstance;
		CGraphicExpandedImageInstance	m_MiniMapCameraraphicImageInstance;

		CGraphicExpandedImageInstance	m_PlayerMark;
		CGraphicImageInstance			m_WhiteMark;

		TInstanceMarkPositionVector		m_PartyPCPositionVector;
		TInstanceMarkPositionVector		m_OtherPCPositionVector;
		TInstanceMarkPositionVector		m_NPCPositionVector;
		TInstanceMarkPositionVector		m_MonsterPositionVector;
		TInstanceMarkPositionVector		m_WarpPositionVector;
		std::map<DWORD, SObserver>		m_kMap_dwVID_kObserver;

		bool							m_bAtlas;
		bool							m_bShow;

		CGraphicVertexBuffer			m_VertexBuffer;
		CGraphicIndexBuffer				m_IndexBuffer;

		D3DXMATRIX						m_matIdentity;
		D3DXMATRIX						m_matWorld;
		D3DXMATRIX						m_matMiniMapCover;

		bool							m_bShowAtlas;
		CGraphicImageInstance			m_AtlasImageInstance;
		D3DXMATRIX						m_matWorldAtlas;
		CGraphicExpandedImageInstance	m_AtlasPlayerMark;

		float							m_fAtlasScreenX;
		float							m_fAtlasScreenY;

		DWORD							m_dwAtlasBaseX;
		DWORD							m_dwAtlasBaseY;

		float							m_fAtlasMaxX;
		float							m_fAtlasMaxY;

		float							m_fAtlasImageSizeX;
		float							m_fAtlasImageSizeY;

		typedef std::vector<TAtlasMarkInfo>		TAtlasMarkInfoVector;
		typedef TAtlasMarkInfoVector::iterator	TAtlasMarkInfoVectorIterator;
		typedef std::vector<TGuildAreaInfo>		TGuildAreaInfoVector;
		typedef TGuildAreaInfoVector::iterator	TGuildAreaInfoVectorIterator;
		TAtlasMarkInfoVectorIterator			m_AtlasMarkInfoVectorIterator;
		TAtlasMarkInfoVector					m_AtlasNPCInfoVector;
		TAtlasMarkInfoVector					m_AtlasWarpInfoVector;

		// WayPoint
		CGraphicExpandedImageInstance			m_MiniWayPointGraphicImageInstances[MINI_WAYPOINT_IMAGE_COUNT];
		CGraphicExpandedImageInstance			m_WayPointGraphicImageInstances[WAYPOINT_IMAGE_COUNT];
		CGraphicExpandedImageInstance			m_TargetMarkGraphicImageInstances[TARGET_MARK_IMAGE_COUNT];
		CGraphicImageInstance					m_GuildAreaFlagImageInstance;
		TAtlasMarkInfoVector					m_AtlasWayPointInfoVector;
		TGuildAreaInfoVector					m_GuildAreaInfoVector;

		// SignalPoint
		struct TSignalPoint
		{
			D3DXVECTOR2 v2Pos;
			unsigned int id;
		};
		std::vector<TSignalPoint>				m_SignalPointVector;

		PyObject*							m_poHandler;

#ifdef ENABLE_NPC_LOCATION_HELPER
		// MT2009_PLUS_NPC_LOCATION_HELPER_V1
		bool							m_bAtlasNpcHelperView;
		std::string						m_strAtlasHelperDisplayMapName;	// "" = the map the character is on
		float							m_fAtlasHelperScale;
		float							m_fAtlasHelperViewportW;
		float							m_fAtlasHelperViewportH;
		float							m_fAtlasRenderPosX;
		float							m_fAtlasRenderPosY;
		float							m_fAtlasHelperPlayerRotation;
		bool							m_bNPCSelected;
		long							m_lSelectedMapIndex;
		std::string						m_strSelectedMapName;
		DWORD							m_dwSelectedNPCVnum;
		long							m_lSelectedNPCX;
		long							m_lSelectedNPCY;
		DWORD							m_dwNPCLocationDirectionEffectID;
		DWORD							m_dwNPCLocationDirectionEffectStartMS;
		int								m_iNPCLocationDirectionEffectIndex;
		CGraphicExpandedImageInstance	m_AtlasHelperMyPositionMarks[ATLAS_HELPER_MY_POSITION_IMAGE_COUNT];
#endif
};
//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f

// Files shared by GameCore.top
