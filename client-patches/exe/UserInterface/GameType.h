#pragma once
#include "../GameLib/ItemData.h"

struct SAffects
{
	enum
	{
		AFFECT_MAX_NUM = 32,
	};

	SAffects() : dwAffects(0) {}
	SAffects(const DWORD & c_rAffects)
	{
		__SetAffects(c_rAffects);
	}
	int operator = (const DWORD & c_rAffects)
	{
		__SetAffects(c_rAffects);
	}

	BOOL IsAffect(BYTE byIndex)
	{
		return dwAffects & (1 << byIndex);
	}

	void __SetAffects(const DWORD & c_rAffects)
	{
		dwAffects = c_rAffects;
	}

	DWORD dwAffects;
};

extern std::string g_strGuildSymbolPathName;

constexpr DWORD c_Name_Max_Length = 64;
constexpr DWORD c_FileName_Max_Length = 128;
constexpr DWORD c_Short_Name_Max_Length = 32;

constexpr DWORD c_Inventory_Page_Column = 5;
constexpr DWORD c_Inventory_Page_Row = 9;
constexpr DWORD c_Inventory_Page_Size = c_Inventory_Page_Column*c_Inventory_Page_Row; // x*y
constexpr DWORD c_ItemSlot_Count = c_Inventory_Page_Size * INVENTORY_PAGE_COUNT;
constexpr DWORD c_Equipment_Count = 12;

constexpr DWORD c_Equipment_Start = c_ItemSlot_Count;

constexpr DWORD c_Equipment_Body	= c_Equipment_Start + WEAR_BODY;
constexpr DWORD c_Equipment_Head	= c_Equipment_Start + WEAR_HEAD;
constexpr DWORD c_Equipment_Shoes	= c_Equipment_Start + WEAR_FOOTS;
constexpr DWORD c_Equipment_Wrist	= c_Equipment_Start + WEAR_WRIST;
constexpr DWORD c_Equipment_Weapon	= c_Equipment_Start + WEAR_WEAPON;
constexpr DWORD c_Equipment_Neck	= c_Equipment_Start + WEAR_NECK;
constexpr DWORD c_Equipment_Ear		= c_Equipment_Start + WEAR_EAR;
constexpr DWORD c_Equipment_Unique1	= c_Equipment_Start + WEAR_UNIQUE1;
constexpr DWORD c_Equipment_Unique2	= c_Equipment_Start + WEAR_UNIQUE2;
constexpr DWORD c_Equipment_Arrow	= c_Equipment_Start + WEAR_ARROW;
constexpr DWORD c_Equipment_Shield	= c_Equipment_Start + WEAR_SHIELD;

#ifdef ENABLE_NEW_EQUIPMENT_SYSTEM
constexpr DWORD c_New_Equipment_Start = c_Equipment_Start + WEAR_BELT;
constexpr DWORD c_New_Equipment_Count = 1;
constexpr DWORD c_Equipment_Belt  = c_Equipment_Start + WEAR_BELT;
#endif
#ifdef ENABLE_PENDANT_SYSTEM
constexpr DWORD c_Equipment_Pendant  = c_Equipment_Start + WEAR_PENDANT;
#endif
#ifdef ENABLE_GLOVE_SYSTEM
constexpr DWORD c_Equipment_Glove  = c_Equipment_Start + WEAR_GLOVE;
#endif

#ifdef ENABLE_COSTUME_SYSTEM
	const DWORD c_Costume_Slot_Start	= c_Equipment_Start + WEAR_COSTUME_BODY;
	const DWORD	c_Costume_Slot_Body		= c_Costume_Slot_Start + COSTUME_BODY;
	const DWORD	c_Costume_Slot_Hair		= c_Costume_Slot_Start + COSTUME_HAIR;
#ifdef ENABLE_MOUNT_COSTUME_SYSTEM
	const DWORD	c_Costume_Slot_Mount	= c_Costume_Slot_Start + COSTUME_MOUNT;
#endif
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
	const DWORD	c_Costume_Slot_Acce		= c_Costume_Slot_Start + COSTUME_ACCE;
#endif

#if defined(ENABLE_WEAPON_COSTUME_SYSTEM) || defined(ENABLE_ACCE_COSTUME_SYSTEM)
	const DWORD c_Costume_Slot_Count	= 4;
#elif defined(ENABLE_MOUNT_COSTUME_SYSTEM)
	const DWORD c_Costume_Slot_Count	= 3;
#else
	const DWORD c_Costume_Slot_Count	= 2;
#endif

	const DWORD c_Costume_Slot_End		= c_Costume_Slot_Start + c_Costume_Slot_Count;

#ifdef ENABLE_WEAPON_COSTUME_SYSTEM
	const DWORD	c_Costume_Slot_Weapon	= c_Equipment_Start + WEAR_COSTUME_WEAPON; // c_Costume_Slot_End + 1;
#endif

#endif

#ifdef ENABLE_MT2009_BUFFI_COSTUME
// MT2009_PLUS_BUFFI_V2: Buffi's costume slots - the equipment cells of WEAR_BUFFI_BODY ... WEAR_BUFFI_SASH (28-31;
// root/uibuffi.py: item.BUFFI_SLOT_*). Inside the wear cells, so no cell after them moves.
constexpr DWORD c_Buffi_Slot_Start	= c_Equipment_Start + WEAR_BUFFI_BODY;
constexpr DWORD c_Buffi_Slot_Body	= c_Equipment_Start + WEAR_BUFFI_BODY;
constexpr DWORD c_Buffi_Slot_Head	= c_Equipment_Start + WEAR_BUFFI_HEAD;
constexpr DWORD c_Buffi_Slot_Weapon	= c_Equipment_Start + WEAR_BUFFI_WEAPON;
constexpr DWORD c_Buffi_Slot_Sash	= c_Equipment_Start + WEAR_BUFFI_SASH;
constexpr DWORD c_Buffi_Slot_Count	= 4;
static_assert(WEAR_BUFFI_SASH < WEAR_MAX_NUM, "Buffi's costume slots must stay inside the wear cells");
static_assert(WEAR_BUFFI_BODY > WEAR_GLOVE, "Buffi's costume slots after the glove");
#endif

const DWORD c_Wear_Max = WEAR_MAX_NUM;
const DWORD c_DragonSoul_Equip_Start = c_ItemSlot_Count + c_Wear_Max;
const DWORD c_DragonSoul_Equip_Slot_Max = DS_SLOT_MAX;
const DWORD c_DragonSoul_Equip_End = c_DragonSoul_Equip_Start + c_DragonSoul_Equip_Slot_Max * DRAGON_SOUL_DECK_MAX_NUM;

const DWORD c_DragonSoul_Equip_Reserved_Count = c_DragonSoul_Equip_Slot_Max * 3;

#ifdef ENABLE_NEW_EQUIPMENT_SYSTEM
	const DWORD c_Belt_Inventory_Slot_Start = c_DragonSoul_Equip_End + c_DragonSoul_Equip_Reserved_Count;
	const DWORD c_Belt_Inventory_Width = 4;
	const DWORD c_Belt_Inventory_Height= 4;
	const DWORD c_Belt_Inventory_Slot_Count = c_Belt_Inventory_Width * c_Belt_Inventory_Height;
	const DWORD c_Belt_Inventory_Slot_End = c_Belt_Inventory_Slot_Start + c_Belt_Inventory_Slot_Count;

	const DWORD c_Inventory_Count	= c_Belt_Inventory_Slot_End;
#else
	const DWORD c_Inventory_Count	= c_DragonSoul_Equip_End;
#endif

const DWORD c_DragonSoul_Inventory_Start = 0;
const DWORD c_DragonSoul_Inventory_Box_Size = 32;
const DWORD c_DragonSoul_Inventory_Count = DS_SLOT_MAX * DRAGON_SOUL_GRADE_MAX * c_DragonSoul_Inventory_Box_Size;
const DWORD c_DragonSoul_Inventory_End = c_DragonSoul_Inventory_Start + c_DragonSoul_Inventory_Count;
#ifdef ENABLE_SPECIAL_STORAGE
// MT2009_PLUS_EKWIPUNEK_V1 (sizes): the category storages' pages (Server/common/length.h)
const DWORD c_Special_Inventory_Page_Size = SPECIAL_INVENTORY_PAGE_SIZE;
const DWORD c_Special_Inventory_Page_Count = SPECIAL_INVENTORY_PAGE_COUNT;
const DWORD c_Special_ItemSlot_Count = SPECIAL_INVENTORY_MAX_NUM;
#endif

enum EDSRefineType
{
	DS_REFINE_TYPE_GRADE,
	DS_REFINE_TYPE_STEP,
	DS_REFINE_TYPE_STRENGTH,
	DS_REFINE_TYPE_CHANGE_ATTR,
	DS_REFINE_TYPE_MAX,
};

enum ESlotType
{
	SLOT_TYPE_NONE,
	SLOT_TYPE_INVENTORY,
	SLOT_TYPE_SKILL,
	SLOT_TYPE_EMOTION,
	SLOT_TYPE_SHOP,
	SLOT_TYPE_EXCHANGE_OWNER,
	SLOT_TYPE_EXCHANGE_TARGET,
	SLOT_TYPE_QUICK_SLOT,
	SLOT_TYPE_SAFEBOX,
	SLOT_TYPE_PRIVATE_SHOP,
	SLOT_TYPE_MALL,
	SLOT_TYPE_DRAGON_SOUL_INVENTORY,
#ifdef ENABLE_SPECIAL_STORAGE
	// MT2009_PLUS_EKWIPUNEK_V1 (slot types): the category storages' windows (root/uiekwipunek.py)
	SLOT_TYPE_UPGRADE_INVENTORY,
	SLOT_TYPE_BOOK_INVENTORY,
	SLOT_TYPE_STONE_INVENTORY,
	SLOT_TYPE_CHANGE_INVENTORY,
	SLOT_TYPE_CHEST_INVENTORY,
#endif
#ifdef ENABLE_SWITCHBOT
	SLOT_TYPE_SWITCHBOT,	// MT2009_PLUS_SWITCHBOT_V1 (slot type): root/uiswitchbot.py
#endif
	SLOT_TYPE_MAX,
};

#pragma pack (push, 1)
#define WORD_MAX 0xffff

#pragma pack(pop)

const DWORD c_QuickBar_Line_Count = 3;
const DWORD c_QuickBar_Slot_Count = 12;

const float c_Idle_WaitTime = 5.0f;

const int c_Monster_Race_Start_Number = 6;
const int c_Monster_Model_Start_Number = 20001;

const float c_fAttack_Delay_Time = 0.2f;
const float c_fHit_Delay_Time = 0.1f;
const float c_fCrash_Wave_Time = 0.2f;
const float c_fCrash_Wave_Distance = 3.0f;

const float c_fHeight_Step_Distance = 50.0f;

enum
{
	DISTANCE_TYPE_FOUR_WAY,
	DISTANCE_TYPE_EIGHT_WAY,
	DISTANCE_TYPE_ONE_WAY,
	DISTANCE_TYPE_MAX_NUM,
};

const float c_fMagic_Script_Version = 1.0f;
const float c_fSkill_Script_Version = 1.0f;
const float c_fMagicSoundInformation_Version = 1.0f;
const float c_fBattleCommand_Script_Version = 1.0f;
const float c_fEmotionCommand_Script_Version = 1.0f;
const float c_fActive_Script_Version = 1.0f;
const float c_fPassive_Script_Version = 1.0f;

// Used by PushMove
const float c_fWalkDistance = 175.0f;
const float c_fRunDistance = 310.0f;

#define FILE_MAX_LEN 128

enum
{
	ITEM_SOCKET_SLOT_MAX_NUM = 3,
	// refactored attribute slot begin
	ITEM_ATTRIBUTE_SLOT_NORM_NUM	= 5,
	ITEM_ATTRIBUTE_SLOT_RARE_NUM	= 2,

	ITEM_ATTRIBUTE_SLOT_NORM_START	= 0,
	ITEM_ATTRIBUTE_SLOT_NORM_END	= ITEM_ATTRIBUTE_SLOT_NORM_START + ITEM_ATTRIBUTE_SLOT_NORM_NUM,

	ITEM_ATTRIBUTE_SLOT_RARE_START	= ITEM_ATTRIBUTE_SLOT_NORM_END,
	ITEM_ATTRIBUTE_SLOT_RARE_END	= ITEM_ATTRIBUTE_SLOT_RARE_START + ITEM_ATTRIBUTE_SLOT_RARE_NUM,

	ITEM_ATTRIBUTE_SLOT_MAX_NUM		= ITEM_ATTRIBUTE_SLOT_RARE_END, // 7
	// refactored attribute slot end
};

#pragma pack(push)
#pragma pack(1)

typedef struct SQuickSlot
{
	BYTE Type;
	WORD Position;
} TQuickSlot;

// Client/server ABI guards for the 2.0.14 four-page inventory migration.
// They also protect the horse and custom seven-slot Dragon Soul ranges from
// silently drifting when another system adds wear positions.
static_assert(sizeof(TQuickSlot) == 3, "quickslot must be BYTE + WORD");
static_assert(INVENTORY_DEFAULT_MAX_NUM == 180, "four normal inventory pages required");
static_assert(INVENTORY_MAX_NUM == 225, "horse inventory must occupy cells 180..224");
static_assert(c_DragonSoul_Equip_Start == 257, "Dragon Soul equipment range mismatch");
static_assert(DRAGON_SOUL_EQUIP_SLOT_END == 271, "seven-slot Dragon Soul decks required");

typedef struct TPlayerItemAttribute
{
    BYTE        bType;
    short       sValue;
} TPlayerItemAttribute;

typedef struct packet_item
{
    DWORD       vnum;
	ITEM_COUNT        count;
	DWORD		flags;
	DWORD		anti_flags;
	long		alSockets[ITEM_SOCKET_SLOT_MAX_NUM];
    TPlayerItemAttribute aAttr[ITEM_ATTRIBUTE_SLOT_MAX_NUM];
#ifdef ENABLE_CHANGELOOK_SYSTEM
	DWORD		dwTransmutationVnum; // MT2009_PLUS_CHANGE_LOOK_V1: the look (0: none); not a packet struct
#endif
} TItemData;

typedef struct packet_shop_item
{
    DWORD       vnum;
    YANG       price;
#ifdef ENABLE_CHEQUE_SYSTEM
	DWORD		cheque;
#endif
	ITEM_COUNT        count;
	BYTE		display_pos;
	long		alSockets[ITEM_SOCKET_SLOT_MAX_NUM];
    TPlayerItemAttribute aAttr[ITEM_ATTRIBUTE_SLOT_MAX_NUM];
} TShopItemData;

#pragma pack(pop)

inline float GetSqrtDistance(int ix1, int iy1, int ix2, int iy2) // By sqrt
{
	float dx, dy;

	dx = float(ix1 - ix2);
	dy = float(iy1 - iy2);

	return sqrtf(dx*dx + dy*dy);
}

// DEFAULT_FONT
std::string GetDefaultFontName();
std::string GetLargeFontName();
std::string GetDefaultFontNameOnly();
std::string GetDefaultFontSizeOnly();
int GetDefaultFontSizeNumber();
void DefaultFont_Startup();
void DefaultFont_Cleanup();
void DefaultFont_SetName(const char * c_szFontName, const char* c_szLargeFontName);
CResource* DefaultFont_GetResource();
CResource* DefaultItalicFont_GetResource();
CResource* LargeFont_GetResource();
// END_OF_DEFAULT_FONT

void SetGuildSymbolPath(const char * c_szPathName);
const char * GetGuildSymbolFileName(DWORD dwGuildID);
BYTE SlotTypeToInvenType(BYTE bSlotType);
//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f

// Files shared by GameCore.top
