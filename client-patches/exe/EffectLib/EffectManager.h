#pragma once

#include "EffectInstance.h"
#ifdef ENABLE_DAMAGE_PRINT_IMPROVE
#include <set> // MT2009_PLUS_DAMAGE_PRINT_V1
#endif

class CEffectManager : public CScreen, public CSingleton<CEffectManager>
{
	public:
		enum EEffectType
		{
			EFFECT_TYPE_NONE				= 0,
			EFFECT_TYPE_PARTICLE			= 1,
			EFFECT_TYPE_ANIMATION_TEXTURE	= 2,
			EFFECT_TYPE_MESH				= 3,
			EFFECT_TYPE_SIMPLE_LIGHT		= 4,

			EFFECT_TYPE_MAX_NUM				= 4,
		};

		typedef std::map<DWORD, CEffectData*> TEffectDataMap;
		typedef std::map<DWORD, CEffectInstance*> TEffectInstanceMap;

	public:
		CEffectManager();
		virtual ~CEffectManager();

		void Destroy();

		void UpdateSound();
		void Update();
		void Render();
		void Mt2009RenderOne(DWORD dwInstanceIndex); // MT2009_PLUS_WIKI_V1: one instance (a preview's effect)

		void GetInfo(std::string* pstInfo);

		bool IsAliveEffect(DWORD dwInstanceIndex);

		// Register
		BOOL RegisterEffect(const char * c_szFileName,bool isExistDelete=false,bool isNeedCache=false);
		BOOL RegisterEffect2(const char * c_szFileName, DWORD* pdwRetCRC, bool isNeedCache=false);

		void DeleteAllInstances();

		// Usage
#ifdef ENABLE_MT2009_SKILL_COLOR
		// MT2009_PLUS_SKILL_COLOR_V1: c_pdwSkillColor - a skill's five colours for the new instance (NULL: its own)
		int CreateEffect(DWORD dwID, const D3DXVECTOR3 & c_rv3Position, const D3DXVECTOR3 & c_rv3Rotation, const DWORD * c_pdwSkillColor = NULL);
#else
		int CreateEffect(DWORD dwID, const D3DXVECTOR3 & c_rv3Position, const D3DXVECTOR3 & c_rv3Rotation);
#endif
		int CreateEffect(const char * c_szFileName, const D3DXVECTOR3 & c_rv3Position, const D3DXVECTOR3 & c_rv3Rotation);

#ifdef ENABLE_MT2009_SKILL_COLOR
		void CreateEffectInstance(DWORD dwInstanceIndex, DWORD dwID, const DWORD * c_pdwSkillColor = NULL);	// MT2009_PLUS_SKILL_COLOR_V1
#else
		void CreateEffectInstance(DWORD dwInstanceIndex, DWORD dwID);
#endif
		BOOL SelectEffectInstance(DWORD dwInstanceIndex);
		bool DestroyEffectInstance(DWORD dwInstanceIndex);
		void DeactiveEffectInstance(DWORD dwInstanceIndex);

		void SetEffectTextures(DWORD dwID,std::vector<string> textures);
		void SetEffectInstancePosition(const D3DXVECTOR3 & c_rv3Position);
		void SetEffectInstanceRotation(const D3DXVECTOR3 & c_rv3Rotation);
		void SetEffectInstanceGlobalMatrix(const D3DXMATRIX & c_rmatGlobal);

		void ShowEffect();
		void HideEffect();

#ifdef __ENABLE_STEALTH_FIX__
		void ApplyAlwaysHidden();
		void ReleaseAlwaysHidden();
#endif

		// Temporary function
		DWORD GetRandomEffect();
		int GetEmptyIndex();
		bool GetEffectData(DWORD dwID, CEffectData ** ppEffect);
		bool GetEffectData(DWORD dwID, const CEffectData ** c_ppEffect);

		void CreateUnsafeEffectInstance(DWORD dwEffectDataID, CEffectInstance ** ppEffectInstance);
		bool DestroyUnsafeEffectInstance(CEffectInstance * pEffectInstance);

#ifdef ENABLE_DAMAGE_PRINT_IMPROVE
		// MT2009_PLUS_DAMAGE_PRINT_V1 (Damage Print Improve v26.0.5): the damage marks live in their own set, drawn after the world
		// without the depth test (CPythonApplication::RenderDamageEffect), not in the instance map
		void CreateDamageEffect(DWORD dwID, const D3DXVECTOR3 & c_rv3Position, const D3DXVECTOR3 & c_rv3Rotation);
		void SetSingleParticleTexture(DWORD dwID, const char * c_szTexturePath);
		bool IsDamageEffectSetEmpty() const { return m_DamageEffectSet.empty(); }
		void UpdateDamageEffect();
		void RenderDamageEffect();
#endif

		int GetRenderingEffectCount();

	protected:
		void __Initialize();

		void __DestroyEffectInstanceMap();
		void __DestroyEffectCacheMap();
		void __DestroyEffectDataMap();
#ifdef ENABLE_DAMAGE_PRINT_IMPROVE
		void __DestroyDamageEffectSet(); // MT2009_PLUS_DAMAGE_PRINT_V1
#endif

	protected:
		bool m_isDisableSortRendering;
		TEffectDataMap					m_kEftDataMap;
		TEffectInstanceMap				m_kEftInstMap;
		TEffectInstanceMap				m_kEftCacheMap;

		CEffectInstance *				m_pSelectedEffectInstance;
#ifdef ENABLE_DAMAGE_PRINT_IMPROVE
		std::set<CEffectInstance *>		m_DamageEffectSet; // MT2009_PLUS_DAMAGE_PRINT_V1
#endif
};
//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f

// Files shared by GameCore.top
