#pragma once

#include "InstanceBase.h"

struct SNetworkActorData
{
	std::string m_stName;

	CAffectFlagContainer	m_kAffectFlags;

	BYTE	m_bType;
	DWORD	m_dwVID;
	DWORD	m_dwStateFlags;
	DWORD	m_dwEmpireID;
	DWORD	m_dwRace;
	DWORD	m_dwMovSpd;
	DWORD	m_dwAtkSpd;
	FLOAT	m_fRot;
	LONG	m_lCurX;
	LONG	m_lCurY;
	LONG	m_lSrcX;
	LONG	m_lSrcY;
	LONG	m_lDstX;
	LONG	m_lDstY;

	DWORD	m_dwServerSrcTime;
	DWORD	m_dwClientSrcTime;
	DWORD	m_dwDuration;

	DWORD	m_dwArmor;
	DWORD	m_dwWeapon;
	DWORD	m_dwHair;
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
	DWORD	m_dwAcce;
#endif
#ifdef ENABLE_QUIVER_SYSTEM
	DWORD	m_dwArrow;
#endif
#ifdef ENABLE_MT2009_AURA
	DWORD	m_dwAura;	// MT2009_PLUS_AURA_V1: the outfit's vnum ("AURA view", chrmgr.SetAura), 0 none
#endif
#ifdef ENABLE_MT2009_WEAPON_ELEMENT
	DWORD	m_dwWeaponElement;	// MT2009_PLUS_WEAPON_ELEMENT_V1: "WELEMFX", chrmgr.SetWeaponElement (0 none, 1..6)
#endif

	DWORD	m_dwOwnerVID;

	short	m_sAlignment;
	BYTE	m_byPKMode;
	DWORD	m_dwMountVnum;

	DWORD	m_dwGuildID;
	DWORD	m_dwLevel;
#ifdef ENABLE_CONQUEROR_LEVEL
	DWORD	m_dwConquerorLevel;	// MT2009_PLUS_CHAMPION_V2
#endif

	SNetworkActorData();

	void SetDstPosition(DWORD dwServerTime, LONG lDstX, LONG lDstY, DWORD dwDuration);
	void SetPosition(LONG lPosX, LONG lPosY);
	void UpdatePosition();

	// NETWORK_ACTOR_DATA_COPY
	SNetworkActorData(const SNetworkActorData& src);
	void operator=(const SNetworkActorData& src);
	void __copy__(const SNetworkActorData& src);
	// END_OF_NETWORK_ACTOR_DATA_COPY
};

struct SNetworkMoveActorData
{
	DWORD	m_dwVID;
	DWORD	m_dwTime;
	LONG	m_lPosX;
	LONG	m_lPosY;
	float	m_fRot;
	DWORD	m_dwFunc;
	DWORD	m_dwArg;
	DWORD	m_dwDuration;

	SNetworkMoveActorData()
	{
		m_dwVID=0;
		m_dwTime=0;
		m_fRot=0.0f;
		m_lPosX=0;
		m_lPosY=0;
		m_dwFunc=0;
		m_dwArg=0;
		m_dwDuration=0;
	}
};

struct SNetworkUpdateActorData
{
	DWORD m_dwVID;
	DWORD m_dwGuildID;
	DWORD m_dwArmor;
	DWORD m_dwWeapon;
	DWORD m_dwHair;
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
	DWORD	m_dwAcce;
#endif
#ifdef ENABLE_QUIVER_SYSTEM
	DWORD m_dwArrow;
#endif
	DWORD m_dwMovSpd;
	DWORD m_dwAtkSpd;
	DWORD m_dwLevel;
#ifdef ENABLE_CONQUEROR_LEVEL
	DWORD m_dwConquerorLevel;	// MT2009_PLUS_CHAMPION_V2
#endif
	short m_sAlignment;
	BYTE m_byPKMode;
	DWORD m_dwMountVnum;
	DWORD m_dwStateFlags;
	CAffectFlagContainer m_kAffectFlags;

	SNetworkUpdateActorData()
	{
#ifdef ENABLE_CONQUEROR_LEVEL
		m_dwConquerorLevel = 0;
#endif
		m_dwGuildID=0;
		m_dwVID=0;
		m_dwArmor=0;
		m_dwWeapon=0;
		m_dwHair=0;
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
		m_dwAcce = 0;
#endif
#ifdef ENABLE_QUIVER_SYSTEM
		m_dwArrow=0;
#endif
		m_dwMovSpd=0;
		m_dwAtkSpd=0;
		m_dwLevel = 0;
		m_sAlignment=0;
		m_byPKMode=0;
		m_dwMountVnum=0;
		m_dwStateFlags=0;
		m_kAffectFlags.Clear();
	}
};

class CPythonCharacterManager;

class CNetworkActorManager : public CReferenceObject
{
	public:
		CNetworkActorManager();
		virtual ~CNetworkActorManager();

		void Destroy();

		void SetMainActorVID(DWORD dwVID);

		void RemoveActor(DWORD dwVID);
		void AppendActor(const SNetworkActorData& c_rkNetActorData);
		void UpdateActor(const SNetworkUpdateActorData& c_rkNetUpdateActorData);
		void MoveActor(const SNetworkMoveActorData& c_rkNetMoveActorData);

		void SyncActor(DWORD dwVID, LONG lPosX, LONG lPosY);
		void SetActorOwner(DWORD dwOwnerVID, DWORD dwVictimVID);
#ifdef ENABLE_MT2009_AURA
		// MT2009_PLUS_AURA_V1: the aura outfit of an actor (kept for its instance's re-creation), Mt2009Aura.cpp
		bool SetActorAura(DWORD dwVID, DWORD dwVnum);
		static CNetworkActorManager* ms_pkAuraInstance;	// the one the network stream owns (python's way in)
#endif
#ifdef ENABLE_MT2009_WEAPON_ELEMENT
		// MT2009_PLUS_WEAPON_ELEMENT_V1: the weapon element of an actor (kept for its instance's re-creation)
		bool SetActorWeaponElement(DWORD dwVID, DWORD dwType);
#endif
#ifdef ENABLE_MT2009_SKILL_COLOR
		// MT2009_PLUS_SKILL_COLOR_V1: an actor's colour of one skill (GC 59; kept per VID for its instance's re-creation,
		// Mt2009SkillColor.cpp)
		void Mt2009SetSkillColor(DWORD dwVID, BYTE bType, WORD wSkillVnum, const DWORD* c_pdwColor);
#endif

		void Update();

	protected:
		void __OLD_Update();

		void __UpdateMainActor();

		bool __IsVisiblePos(LONG lPosX, LONG lPosY, DWORD dwRace = 0);
		bool __IsVisibleActor(const SNetworkActorData& c_rkNetActorData);
		bool __IsMainActorVID(DWORD dwVID);

		void __RemoveAllGroundItems();
		void __RemoveAllActors();
		void __RemoveDynamicActors();
		void __RemoveCharacterManagerActor(SNetworkActorData& rkNetActorData);

		SNetworkActorData* __FindActorData(DWORD dwVID);

		CInstanceBase* __AppendCharacterManagerActor(SNetworkActorData& rkNetActorData);
		CInstanceBase* __FindActor(SNetworkActorData& rkNetActorData);
		CInstanceBase* __FindActor(SNetworkActorData& rkNetActorData, LONG lDstX, LONG lDstY);

		CPythonCharacterManager& __GetCharacterManager();

	protected:
		DWORD m_dwMainVID;

		LONG m_lMainPosX;
		LONG m_lMainPosY;

		std::map<DWORD, SNetworkActorData> m_kNetActorDict;
#ifdef ENABLE_MT2009_SKILL_COLOR
		void __Mt2009ApplySkillColors(DWORD dwVID, CInstanceBase* pkInst);	// MT2009_PLUS_SKILL_COLOR_V1
		std::map<DWORD, std::map<DWORD, CActorInstance::SMt2009SkillColor> > m_kMt2009SkillColor;	// VID -> (type << 16) | vnum
#endif
};
//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f

// Files shared by GameCore.top
