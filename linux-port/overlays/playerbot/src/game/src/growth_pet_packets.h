#ifndef __INC_MT2009_GROWTH_PET_PACKETS_H__
#define __INC_MT2009_GROWTH_PET_PACKETS_H__

// MT2009_PLUS_GROWTH_PET_V1 (packets): System Zwierzat Domowych - the client <-> game packets (server-patches/pety,
// README.md). Included by packet.h inside its #pragma pack(1) (the edit "MT2009_PLUS_GROWTH_PET_V1 (structs)"); the exe
// has the same layouts and static_asserts in client-patches/exe/UserInterface/Packet.h. The header numbers are in
// packet.h's enums: CG 122-134, GC 224-236.

enum EGrowthPetPoints
{
	POINT_UPBRINGING_PET_LEVEL,
	POINT_UPBRINGING_PET_EXP,
	POINT_UPBRINGING_PET_ITEM_EXP,
	POINT_UPBRINGING_PET_NEXT_EXP,
	POINT_UPBRINGING_PET_EVOL_LEVEL,
	POINT_UPBRINGING_PET_HP,
	POINT_UPBRINGING_PET_DEF_GRADE,
	POINT_UPBRINGING_PET_SP,
	POINT_UPBRINGING_DURATION,
	POINT_UPBRINGING_MAX_DURATION,
	POINT_UPBRINGING_BIRTHDAY,
	POINT_UPBRINGING_CHAMPION_LEVEL,
	POINT_UPBRINGING_CHAMPION_EXP,
	POINT_UPBRINGING_CHAMPION_ITEM_EXP,
	POINT_UPBRINGING_CHAMPION_NEXT_EXP,
	POINT_UPBRINGING_CHAMPION_RES,
	POINT_UPBRINGING_CHAMPION_BLOCK_PEN,
	POINT_UPBRINGING_CHAMPION_PRECISION,
	POINT_UPBRINGING_TYPE,
	POINT_UPBRINGING_SKILL_SLOTS,
	POINT_UPBRINGING_MAX_NUM
};

enum EGrowthPetSubheader
{
	SUBHEADER_PET_EGG_USE_SUCCESS,
	SUBHEADER_PET_EGG_USE_FAILED_BECAUSE_NAME,
	SUBHEADER_PET_EGG_USE_FAILED_TIMEOVER,
	SUBHEADER_PET_UNSUMMON,
	SUBHEADER_PET_FEED_FAILED,
	SUBHEADER_PET_FEED_SUCCESS,
	SUBHEADER_PET_REVIVE_FAILED,
	SUBHEADER_PET_REVIVE_SUCCESS,
	SUBHEADER_PET_NAME_CHANGE_FAILED,
	SUBHEADER_PET_NAME_CHANGE_SUCCESS,
	SUBHEADER_PET_WINDOW_TYPE_INFO,
	SUBHEADER_PET_WINDOW_TYPE_ATTR_CHANGE,
	SUBHEADER_PET_WINDOW_TYPE_PREMIUM_FEED,
	SUBHEADER_PET_EVOLVE_SUCCESS,
	SUBHEADER_PET_POTENTIAL_FAILED,
	SUBHEADER_PET_POTENTIAL_SUCCESS,
};

enum EGrowthPetWindow { PET_WINDOW_HATCH, PET_WINDOW_NAME_CHANGE };
enum EGrowthPetWindowType { PET_WINDOW_INFO, PET_WINDOW_ATTR_CHANGE, PET_WINDOW_PRIMIUM_FEEDSTUFF };
enum EGrowthPetFeed { FEED_LIFE_TIME_EVENT, FEED_EVOL_EVENT, FEED_EXP_EVENT };
enum EGrowthPetPotentialAction { PET_POTENTIAL_INSERT = 0, PET_POTENTIAL_REMOVE = 1 };

typedef struct SGrowthPetSkillInfo { BYTE bLocked; BYTE bSkill; BYTE bLevel; DWORD dwCooltime; } TGrowthPetSkillInfo;

typedef struct SPacketGCPet { BYTE header; BYTE subheader; } TPacketGCPet;
typedef struct SPacketGCPetSet
{
	BYTE header;
	DWORD dwID;
	DWORD dwSummonItemVnum;
	char szName[GROWTH_PET_NAME_MAX + 1];
	TGrowthPetSkillInfo aSkill[GROWTH_PET_SKILL_SLOTS];
	DWORD dwPoints[POINT_UPBRINGING_MAX_NUM];
} TPacketGCPetSet;
typedef struct SPacketGCPetDelete { BYTE header; DWORD dwID; } TPacketGCPetDelete;
typedef struct SPacketGCPetSummon { BYTE header; DWORD dwID; } TPacketGCPetSummon;
typedef struct SPacketGCPetPointUpdate { BYTE header; DWORD dwID; BYTE bPoint; DWORD dwValue; } TPacketGCPetPointUpdate;
typedef struct SPacketGCPetNameChangeResult { BYTE header; BYTE subheader; DWORD dwID; char szName[GROWTH_PET_NAME_MAX + 1]; } TPacketGCPetNameChangeResult;
typedef struct SPacketGCPetDetermineResult { BYTE header; BYTE type; } TPacketGCPetDetermineResult;
typedef struct SPacketGCPetAttrChangeResult { BYTE header; BYTE type; TItemPos pos; } TPacketGCPetAttrChangeResult;
typedef struct SGrowthPetSkillUpdate
{
	BYTE bLocked;
	BYTE bSkill;
	BYTE bLevel;
	DWORD dwCooltime;
	BYTE bSkillFormula1[GROWTH_PET_SKILL_LEVEL_MAX];	// activation chance % by skill level (auto skills)
	WORD wSkillFormula2[GROWTH_PET_SKILL_LEVEL_MAX];	// the value by skill level (unit per skill - README)
	BYTE bSkillFormula3[GROWTH_PET_SKILL_LEVEL_MAX];	// duration, tenths of a second
} TGrowthPetSkillUpdate;
typedef struct SPacketGCPetSkillUpdate { BYTE header; DWORD dwID; TGrowthPetSkillUpdate aSkill[GROWTH_PET_SKILL_SLOTS]; } TPacketGCPetSkillUpdate;
typedef struct SPacketGCPetSkillCooltime { BYTE header; DWORD dwID; BYTE bSlot; DWORD dwCooltime; } TPacketGCPetSkillCooltime;
typedef struct SPacketGCPetLook { BYTE header; DWORD dwVID; WORD wScalePct; BYTE bEvolution; BYTE bType78; } TPacketGCPetLook;
typedef struct SGrowthPetPotentialSlot { DWORD dwEggVnum; BYTE bSkill; BYTE bLevel; DWORD dwEndTime; } TGrowthPetPotentialSlot;
typedef struct SPacketGCPetPotential { BYTE header; DWORD dwID; BYTE bOpenSlots; TGrowthPetPotentialSlot aSlot[GROWTH_PET_POTENTIAL_SLOTS]; } TPacketGCPetPotential;

typedef struct SPacketCGPetHatch { BYTE header; char name[GROWTH_PET_NAME_MAX + 1]; TItemPos eggPos; } TPacketCGPetHatch;
typedef struct SPacketCGPetWindow { BYTE header; BYTE window; BYTE state; } TPacketCGPetWindow;
typedef struct SPacketCGPetWindowType { BYTE header; BYTE type; } TPacketCGPetWindowType;
typedef struct SPacketCGPetFeed { BYTE header; BYTE index; TItemPos pos[GROWTH_PET_FEED_SLOTS]; WORD count[GROWTH_PET_FEED_SLOTS]; } TPacketCGPetFeed;
typedef struct SPacketCGPetDetermine { BYTE header; TItemPos determinePos; } TPacketCGPetDetermine;
typedef struct SPacketCGPetAttrChange { BYTE header; TItemPos upBringingPos; TItemPos attrChangePos; } TPacketCGPetAttrChange;
typedef struct SPacketCGPetRevive { BYTE header; TItemPos upBringingPos; TItemPos pos[GROWTH_PET_REVIVE_SLOTS]; WORD count[GROWTH_PET_REVIVE_SLOTS]; } TPacketCGPetRevive;
typedef struct SPacketCGPetLearnSkill { BYTE header; BYTE slotIndex; TItemPos learnSkillPos; } TPacketCGPetLearnSkill;
typedef struct SPacketCGPetSkillUpgrade { BYTE header; BYTE slotIndex; } TPacketCGPetSkillUpgrade;
typedef struct SPacketCGPetDeleteSkill { BYTE header; BYTE slotIndex; TItemPos deleteSkillPos; } TPacketCGPetDeleteSkill;
typedef struct SPacketCGPetDeleteAllSkill { BYTE header; TItemPos deleteAllSkillPos; } TPacketCGPetDeleteAllSkill;
typedef struct SPacketCGPetNameChange { BYTE header; char name[GROWTH_PET_NAME_MAX + 1]; TItemPos changeNamePos; TItemPos upBringingPos; } TPacketCGPetNameChange;
typedef struct SPacketCGPetPotential { BYTE header; BYTE action; BYTE slot; TItemPos eggPos; } TPacketCGPetPotential;

static_assert(sizeof(TItemPos) == 3, "TItemPos is 3 bytes in the pet packets");
static_assert(sizeof(TPacketGCPet) == 2 && sizeof(TPacketGCPetSet) == 131 && sizeof(TPacketGCPetDelete) == 5 &&
		sizeof(TPacketGCPetSummon) == 5 && sizeof(TPacketGCPetPointUpdate) == 10 && sizeof(TPacketGCPetNameChangeResult) == 27 &&
		sizeof(TPacketGCPetDetermineResult) == 2 && sizeof(TPacketGCPetAttrChangeResult) == 5 &&
		sizeof(TGrowthPetSkillUpdate) == 87 && sizeof(TPacketGCPetSkillUpdate) == 266 && sizeof(TPacketGCPetSkillCooltime) == 10 &&
		sizeof(TPacketGCPetLook) == 9 && sizeof(TPacketGCPetPotential) == 26, "growth pet GC packets (exe the same)");
static_assert(sizeof(TPacketCGPetHatch) == 25 && sizeof(TPacketCGPetWindow) == 3 && sizeof(TPacketCGPetWindowType) == 2 &&
		sizeof(TPacketCGPetFeed) == 47 && sizeof(TPacketCGPetDetermine) == 4 && sizeof(TPacketCGPetAttrChange) == 7 &&
		sizeof(TPacketCGPetRevive) == 54 && sizeof(TPacketCGPetLearnSkill) == 5 && sizeof(TPacketCGPetSkillUpgrade) == 2 &&
		sizeof(TPacketCGPetDeleteSkill) == 5 && sizeof(TPacketCGPetDeleteAllSkill) == 4 && sizeof(TPacketCGPetNameChange) == 28 &&
		sizeof(TPacketCGPetPotential) == 6, "growth pet CG packets (exe the same)");

#endif
