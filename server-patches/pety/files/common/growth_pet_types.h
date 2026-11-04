#ifndef __INC_MT2009_GROWTH_PET_TYPES_H__
#define __INC_MT2009_GROWTH_PET_TYPES_H__

// MT2009_PLUS_GROWTH_PET_V1 - System Zwierzat Domowych (server-patches/pety/README.md).
// Shared by the game and the db core: tables.h includes this file inside its #pragma pack(1), so every struct here
// is packed the same on both sides. Installed into common/ by server-patches/pety/apply_pety.py (overwritten when it
// differs, so a change here reaches a patched tree). The exe has the client side in
// client-patches/exe/UserInterface/Packet.h (MT2009_PLUS_GROWTH_PET_V1).

enum EGrowthPetLimits
{
	GROWTH_PET_NAME_MIN = 4,
	GROWTH_PET_NAME_MAX = 20,			// bytes (CP1250)
	GROWTH_PET_SKILL_SLOTS = 3,
	GROWTH_PET_SKILL_LEVEL_MAX = 20,
	GROWTH_PET_FEED_SLOTS = 9,
	GROWTH_PET_REVIVE_SLOTS = 10,
	GROWTH_PET_POTENTIAL_SLOTS = 2,
	GROWTH_PET_MAX_LEVEL = 105,
	GROWTH_PET_CHAMPION_MAX_LEVEL = 30,
	GROWTH_PET_LOAD_MAX = 64,			// pets one GD load request names
};

enum EGrowthPetState
{
	GROWTH_PET_STATE_NONE = 0,
	GROWTH_PET_STATE_UPBRINGING = 1,	// in a seal (the bag, the storeroom - wherever the seal is)
	GROWTH_PET_STATE_BAG = 2,			// packed in a Klatka Transportowa (55002)
	GROWTH_PET_STATE_PENDING = 3,		// an old-system pet waiting for its seal (given at its owner's next login)
};

enum EGrowthPetLoadReason
{
	GROWTH_PET_LOAD_ITEMS = 1,		// the seals / cages a character holds (login, storeroom, a seal that came in)
	GROWTH_PET_LOAD_PENDING = 2,	// the state-3 rows of a pid (dwPID); adwID unused
	GROWTH_PET_LOAD_UNPACK = 3,		// the pet of a cage being opened (dwParam = the cage's item id)
};

typedef struct SGrowthPetSkill
{
	BYTE bLocked;		// 1 = the slot is closed for this pet
	BYTE bSkill;		// 1..23, 0 = empty
	BYTE bLevel;		// 1..GROWTH_PET_SKILL_LEVEL_MAX
	DWORD dwCooltime;	// unix time the auto skill is ready again (not saved)
} TGrowthPetSkill;

typedef struct SGrowthPetPotential
{
	DWORD dwEggVnum;	// the egg put in (0 = empty)
	BYTE bSkill;		// the skill it gave
	DWORD dwEndTime;	// the egg's own end time: the skill lasts as long as the egg would have
} TGrowthPetPotential;

typedef struct SGrowthPet
{
	DWORD dwID;
	DWORD dwOwner;			// the pid that saved it last (state 3: the pid that gets it)
	DWORD dwVnum;			// the seal's vnum (the species)
	BYTE bState;
	char szName[GROWTH_PET_NAME_MAX + 1];
	BYTE bSize;
	DWORD dwLevel;
	BYTE bLevelStep;
	BYTE bEvolution;		// 1..6 (Mlody, Dziki, Dzielny, Bohaterski, Przebudzony, Mocny)
	BYTE bType;				// 1..8, 0 = not rolled yet (an old-system pet: the game finalises it)
	BYTE bTypeKnown;		// the owner used Sfera Losu Zwierzaka on it
	DWORD dwHP;				// the owner's bonuses, 0.001 %
	DWORD dwSP;
	DWORD dwDef;
	DWORD dwHPApply;		// an even type's fixed gains (0.001 %)
	DWORD dwSPApply;
	DWORD dwDefApply;
	DWORD dwAgeApply;
	TGrowthPetSkill aSkill[GROWTH_PET_SKILL_SLOTS];
	unsigned long long ullExp;			// mob exp of the level
	unsigned long long ullItemExp;		// item exp of the level
	long long llBirthday;	// unix time
	long long llEndTime;	// unix time its life ends
	long long llMaxTime;	// seconds of a full life
	// the champion pet (Przebudzony / Mocny)
	DWORD dwChampionLevel;
	unsigned long long ullChampionExp;
	unsigned long long ullChampionItemExp;
	DWORD dwChampionRes;		// Wola SungMa (ODP), 0.001 %
	DWORD dwChampionBlockPen;	// Przebicie bloku
	DWORD dwChampionPrecision;	// Precyzja
	DWORD dwChampionResApply;	// an even type's fixed gains
	DWORD dwChampionBlockPenApply;
	DWORD dwChampionPrecisionApply;
	TGrowthPetPotential aPotential[GROWTH_PET_POTENTIAL_SLOTS];
} TGrowthPet;

// GD 149 / DG 185: a load by ids (or the pending pets of a pid).
typedef struct SPacketGDGrowthPetLoad
{
	DWORD dwPID;
	BYTE bReason;		// EGrowthPetLoadReason
	DWORD dwParam;
	BYTE bCount;
	DWORD adwID[GROWTH_PET_LOAD_MAX];
} TPacketGDGrowthPetLoad;

typedef struct SPacketDGGrowthPetLoad
{
	DWORD dwPID;
	BYTE bReason;
	DWORD dwParam;
	WORD wCount;		// TGrowthPet[wCount] follow
} TPacketDGGrowthPetLoad;

// GD 148
typedef struct SPacketGDGrowthPetDelete
{
	DWORD dwID;
} TPacketGDGrowthPetDelete;

// The skill proto (player.growth_pet_skill_proto; DG 186 after the boot packet): the wiki's tables.
typedef struct SGrowthPetSkillTable
{
	DWORD dwPetVnum;	// the seal's vnum, 0 = every species
	BYTE bSkill;
	char szName[32 + 1];
	BYTE bType;			// EGrowthPetSkillUse
	DWORD dwCooldown;
	char szPointOn[32];
	char szUnit[8];
	DWORD adwValue[8];		// the skill level 20 value at pet level 105, per type 1..8
	DWORD adwCurve[20];		// skill levels 1..20 at pet level 105 (no specialty)
	BYTE abGrowLevel[8];	// pet levels at which a level-20 value grows by one unit; 0-terminated; all 0 = continuous
	BYTE abActivate[20];	// chance % of an auto skill by skill level
	BYTE abDuration[20];	// tenths of a second by skill level
} TGrowthPetSkillTable;

enum EGrowthPetSkillUse
{
	GROWTH_PET_SKILL_USE_NONE = 0,
	GROWTH_PET_SKILL_USE_PASSIVE = 1,
	GROWTH_PET_SKILL_USE_AUTO = 2,
};

#endif
