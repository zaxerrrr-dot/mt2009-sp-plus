#pragma once

#include "Locale.h"
#include "../gamelib/RaceData.h"
#include "../gamelib/ItemData.h"

typedef BYTE TPacketHeader;

enum
{
	/////////////////////////////////////////////////
	// To Server
	// HEADER_BLANK is the not use(for future use)
	HEADER_CG_LOGIN								= 1,
	HEADER_CG_ATTACK							= 2,
	HEADER_CG_CHAT								= 3,
	HEADER_CG_PLAYER_CREATE						= 4,
	HEADER_CG_PLAYER_DESTROY					= 5,
	HEADER_CG_PLAYER_SELECT						= 6,
	HEADER_CG_CHARACTER_MOVE					= 7,
	HEADER_CG_SYNC_POSITION  					= 8,
	HEADER_CG_DIRECT_ENTER						= 9,
	HEADER_CG_ENTERGAME							= 10,
	HEADER_CG_ITEM_USE							= 11,
	HEADER_CG_ITEM_DROP							= 12,
	HEADER_CG_ITEM_MOVE							= 13,
	HEADER_CG_ITEM_PICKUP						= 15,
	HEADER_CG_QUICKSLOT_ADD                     = 16,
	HEADER_CG_QUICKSLOT_DEL                     = 17,
	HEADER_CG_QUICKSLOT_SWAP                    = 18,
	HEADER_CG_WHISPER							= 19,
	HEADER_CG_ITEM_DROP2                        = 20,
	//HEADER_BLANK21								= 21,
	//HEADER_BLANK22								= 22,
	//HEADER_BLANK22								= 23,
	//HEADER_BLANK24								= 24,
	//HEADER_BLANK25								= 25,
	HEADER_CG_ON_CLICK							= 26,
	HEADER_CG_EXCHANGE							= 27,
    HEADER_CG_CHARACTER_POSITION                = 28,
    HEADER_CG_SCRIPT_ANSWER						= 29,
	HEADER_CG_QUEST_INPUT_STRING				= 30,
    HEADER_CG_QUEST_CONFIRM                     = 31,
	//HEADER_BLANK32								= 32,
	//HEADER_BLANK33								= 33,
	//HEADER_BLANK34								= 34,
	//HEADER_BLANK35								= 35,
	//HEADER_BLANK36								= 36,
	//HEADER_BLANK37								= 37,
	//HEADER_BLANK38								= 38,
	//HEADER_BLANK39								= 39,
	//HEADER_BLANK40								= 40,
	HEADER_CG_PVP								= 41,
	//HEADER_BLANK42								= 42,
	//HEADER_BLANK43								= 43,
	//HEADER_BLANK44								= 44,
	//HEADER_BLANK45								= 45,
	//HEADER_BLANK46								= 46,
	//HEADER_BLANK47								= 47,
	//HEADER_BLANK48								= 48,
	//HEADER_BLANK49								= 49,
    HEADER_CG_SHOP								= 50,
	HEADER_CG_FLY_TARGETING						= 51,
	HEADER_CG_USE_SKILL							= 52,
   // HEADER_CG_ADD_FLY_TARGETING                 = 53,
	HEADER_CG_SHOOT								= 54,
	HEADER_CG_MYSHOP                            = 55,
	//HEADER_BLANK56								= 56,
	//HEADER_BLANK57								= 57,
	//HEADER_BLANK58								= 58,
	//HEADER_BLANK59								= 59,
	HEADER_CG_ITEM_USE_TO_ITEM					= 60,
    HEADER_CG_TARGET                            = 61,
	//HEADER_BLANK62								= 62,
	HEADER_CG_REQUEST_INFO_RESPONSE				= 63,
	//HEADER_BLANK64								= 64,
	HEADER_CG_WARP								= 65,
    HEADER_CG_SCRIPT_BUTTON						= 66,
    HEADER_CG_MESSENGER                         = 67,
	//HEADER_BLANK68								= 68,
    HEADER_CG_MALL_CHECKOUT                     = 69,
    HEADER_CG_SAFEBOX_CHECKIN                   = 70,
    HEADER_CG_SAFEBOX_CHECKOUT                  = 71,
    HEADER_CG_PARTY_INVITE                      = 72,
    HEADER_CG_PARTY_INVITE_ANSWER               = 73,
    HEADER_CG_PARTY_REMOVE                      = 74,
    HEADER_CG_PARTY_SET_STATE                   = 75,
    HEADER_CG_PARTY_USE_SKILL                   = 76,
    HEADER_CG_SAFEBOX_ITEM_MOVE                 = 77,
	HEADER_CG_PARTY_PARAMETER                   = 78,
	//HEADER_BLANK68								= 79,
	HEADER_CG_GUILD								= 80,
	HEADER_CG_ANSWER_MAKE_GUILD					= 81,
    HEADER_CG_FISHING                           = 82,
    HEADER_CG_GIVE_ITEM                         = 83,
	//HEADER_BLANK84								= 84,
	//HEADER_BLANK85								= 85,
	//HEADER_BLANK86								= 86,
	//HEADER_BLANK87								= 87,
	//HEADER_BLANK88								= 88,
	//HEADER_BLANK89								= 89,
    HEADER_CG_EMPIRE                            = 90,
	//HEADER_BLANK91								= 91,
	//HEADER_BLANK92								= 92,
	//HEADER_BLANK93								= 93,
	//HEADER_BLANK94								= 94,
	//HEADER_BLANK95								= 95,
    HEADER_CG_REFINE                            = 96,
	//HEADER_BLANK97								= 97,
	//HEADER_BLANK98								= 98,
	//HEADER_BLANK99								= 99,

	HEADER_CG_MARK_LOGIN						= 100,
	HEADER_CG_MARK_CRCLIST						= 101,
	HEADER_CG_MARK_UPLOAD						= 102,
	HEADER_CG_MARK_IDXLIST						= 104,

	HEADER_CG_CRC_REPORT						= 103,

	HEADER_CG_HACK								= 105,
    HEADER_CG_CHANGE_NAME                       = 106,
    HEADER_CG_LOGIN2                            = 109,
	HEADER_CG_DUNGEON							= 110,
	HEADER_CG_LOGIN3							= 111,
	HEADER_CG_GUILD_SYMBOL_UPLOAD				= 112,
	HEADER_CG_GUILD_SYMBOL_CRC					= 113,
	HEADER_CG_SCRIPT_SELECT_ITEM				= 114,
	HEADER_CG_CHECK_VERSION						= 115,
#ifdef ENABLE_IKASHOP_RENEWAL
	HEADER_CG_NEW_OFFLINESHOP					= 119,
#endif

	HEADER_CG_DRAGON_SOUL_REFINE				= 205,
	HEADER_CG_STATE_CHECKER						= 206,

	// MT2009 Plus: target drop and private shop search
	HEADER_CG_TARGET_DROP						= 151,
	HEADER_CG_PRIVATE_SHOP_SEARCH				= 216,
	HEADER_CG_PRIVATE_SHOP_SEARCH_CLOSE			= 217,
	HEADER_CG_PRIVATE_SHOP_SEARCH_BUY_ITEM		= 218,

	// MT2009_PLUS_MINIGAMES_V1 (Owsap v6.2.6 numbers and layouts)
#ifdef ENABLE_MINI_GAME_RUMI
	HEADER_CG_MINI_GAME_RUMI					= 181,
#endif
#ifdef ENABLE_MINI_GAME_YUTNORI
	HEADER_CG_MINI_GAME_YUTNORI					= 182,
#endif
#ifdef ENABLE_FLOWER_EVENT
	HEADER_CG_FLOWER_EVENT						= 187,
#endif
#ifdef ENABLE_SWITCHBOT
	HEADER_CG_SWITCHBOT							= 170,	// MT2009_PLUS_SWITCHBOT_V1 (cg header)
#ifdef ENABLE_FISH_EVENT
	HEADER_CG_FISH_EVENT_SEND					= 219,	// MT2009_PLUS_FISH_PUZZLE_V2 (cg header): the fish puzzle (the package's number)
#endif
#ifdef ENABLE_MT2009_SKILL_COLOR
	HEADER_CG_SKILL_COLOR						= 56,	// MT2009_PLUS_SKILL_COLOR_V1 (cg header): one skill's colour (the package's number)
#endif
#ifdef ENABLE_MT2009_TITLES
	HEADER_CG_TITLE								= 185,	// MT2009_PLUS_TITLES_V1 (cg header): the hello / the title window (the package's number)
#endif
#endif
#ifdef ENABLE_MINI_GAME_CATCH_KING
	HEADER_CG_MINI_GAME_CATCH_KING				= 226,
#endif
#ifdef ENABLE_NPC_LOCATION_HELPER
	HEADER_CG_NPC_LOCATION_HELPER				= 196,	// MT2009_PLUS_NPC_LOCATION_HELPER_V1 (cg header)
#endif
#ifdef ENABLE_GROWTH_PET_SYSTEM
	// MT2009_PLUS_GROWTH_PET_V1 (cg headers): the growth pet (Anka2's numbers, free in ours; 134 is new)
	HEADER_CG_PET_HATCH							= 122,
	HEADER_CG_PET_WINDOW_TYPE					= 123,
	HEADER_CG_PET_WINDOW						= 124,
	HEADER_CG_PET_NAME_CHANGE					= 125,
	HEADER_CG_PET_FEED							= 126,
	HEADER_CG_PET_DETERMINE						= 127,
	HEADER_CG_PET_ATTR_CHANGE					= 128,
	HEADER_CG_PET_REVIVE						= 129,
	HEADER_CG_PET_LEARN_SKILL					= 130,
	HEADER_CG_PET_SKILL_UPGRADE					= 131,
	HEADER_CG_PET_DELETE_SKILL					= 132,
	HEADER_CG_PET_DELETE_ALL_SKILL				= 133,
	HEADER_CG_PET_POTENTIAL						= 134,
#endif

	HEADER_CG_KEY_AGREEMENT						= 0xfb, // _IMPROVED_PACKET_ENCRYPTION_
	HEADER_CG_TIME_SYNC							= 0xfc,
	//HEADER_CG_CLIENT_VERSION2					= 0xf1,
	HEADER_CG_PONG								= 0xfe,
    HEADER_CG_HANDSHAKE                         = 0xff,

	/////////////////////////////////////////////////
	// From Server
	HEADER_GC_CHARACTER_ADD						= 1,
	HEADER_GC_CHARACTER_DEL						= 2,
	HEADER_GC_CHARACTER_MOVE					= 3,
	HEADER_GC_CHAT								= 4,
	HEADER_GC_SYNC_POSITION 					= 5,
	HEADER_GC_LOGIN_SUCCESS3					= 6,
	HEADER_GC_LOGIN_FAILURE						= 7,
	HEADER_GC_PLAYER_CREATE_SUCCESS				= 8,
	HEADER_GC_PLAYER_CREATE_FAILURE				= 9,
	HEADER_GC_PLAYER_DELETE_SUCCESS				= 10,
	HEADER_GC_PLAYER_DELETE_WRONG_SOCIAL_ID		= 11,
	// 12
	HEADER_GC_STUN								= 13,
	HEADER_GC_DEAD								= 14,

	HEADER_GC_MAIN_CHARACTER					= 15,
	HEADER_GC_PLAYER_POINTS						= 16,
	HEADER_GC_PLAYER_POINT_CHANGE				= 17,
	HEADER_GC_CHANGE_SPEED						= 18,
	HEADER_GC_CHARACTER_UPDATE                  = 19,
	HEADER_GC_ITEM_SET							= 20,
	HEADER_GC_ITEM_SET2							= 21,
	HEADER_GC_ITEM_USE							= 22,
	HEADER_GC_ITEM_DROP							= 23,
	HEADER_GC_ITEM_UPDATE						= 25,
	HEADER_GC_ITEM_GROUND_ADD					= 26,
	HEADER_GC_ITEM_GROUND_DEL					= 27,
    HEADER_GC_QUICKSLOT_ADD                     = 28,
    HEADER_GC_QUICKSLOT_DEL                     = 29,
    HEADER_GC_QUICKSLOT_SWAP                    = 30,
	HEADER_GC_ITEM_OWNERSHIP					= 31,
	HEADER_GC_LOGIN_SUCCESS4					= 32,
	HEADER_GC_ITEM_UNBIND_TIME					= 33,
	HEADER_GC_WHISPER							= 34,
	HEADER_GC_ALERT								= 35,

	HEADER_GC_MOTION							= 36,

	HEADER_GC_SHOP							    = 38,
	HEADER_GC_SHOP_SIGN							= 39,

	HEADER_GC_DUEL_START						= 40,
	HEADER_GC_PVP								= 41,
	HEADER_GC_EXCHANGE							= 42,
    HEADER_GC_CHARACTER_POSITION                = 43,

	HEADER_GC_PING								= 44,

	HEADER_GC_SCRIPT							= 45,
    HEADER_GC_QUEST_CONFIRM                     = 46,

	HEADER_GC_MOUNT								= 61,
	HEADER_GC_TARGET_DROP						= 160,
	HEADER_GC_PRIVATE_SHOP_SEARCH				= 216,
	HEADER_GC_PRIVATE_SHOP_SEARCH_OPEN			= 217,
	HEADER_GC_PRIVATE_SHOP_SEARCH_MARK			= 218,
	HEADER_GC_OWNERSHIP                         = 62,
    HEADER_GC_TARGET                            = 63,
	HEADER_GC_WARP								= 65,

	HEADER_GC_GAMEMASTER_TARGET					= 66,
	HEADER_GC_CAPTCHA							= 67,

	HEADER_GC_REQUEST_INFO						= 68,

	HEADER_GC_ADD_FLY_TARGETING                 = 69,
	HEADER_GC_CREATE_FLY						= 70,
	HEADER_GC_FLY_TARGETING						= 71,
	HEADER_GC_SKILL_LEVEL						= 72,
	HEADER_GC_SKILL_COOLTIME_END				= 73,
    HEADER_GC_MESSENGER                         = 74,
	HEADER_GC_GUILD								= 75,
	HEADER_GC_SKILL_LEVEL_NEW					= 76,

    HEADER_GC_PARTY_INVITE                      = 77,
    HEADER_GC_PARTY_ADD                         = 78,
    HEADER_GC_PARTY_UPDATE                      = 79,
    HEADER_GC_PARTY_REMOVE                      = 80,

    HEADER_GC_QUEST_INFO                        = 81,
    HEADER_GC_REQUEST_MAKE_GUILD                = 82,
	HEADER_GC_PARTY_PARAMETER                   = 83,

    HEADER_GC_SAFEBOX_MONEY_CHANGE              = 84,
    HEADER_GC_SAFEBOX_SET                       = 85,
    HEADER_GC_SAFEBOX_DEL                       = 86,
    HEADER_GC_SAFEBOX_WRONG_PASSWORD            = 87,
    HEADER_GC_SAFEBOX_SIZE                      = 88,

    HEADER_GC_FISHING                           = 89,

    HEADER_GC_EMPIRE                            = 90,

    HEADER_GC_PARTY_LINK                        = 91,
    HEADER_GC_PARTY_UNLINK                      = 92,

    HEADER_GC_REFINE_INFORMATION                = 95,

	HEADER_GC_OBSERVER_ADD						= 96,
	HEADER_GC_OBSERVER_REMOVE					= 97,
	HEADER_GC_OBSERVER_MOVE						= 98,
	HEADER_GC_VIEW_EQUIP                        = 99,

	HEADER_GC_MARK_BLOCK						= 100,
	HEADER_GC_MARK_DIFF_DATA                    = 101,
	HEADER_GC_MARK_IDXLIST						= 102,

    HEADER_GC_TIME                              = 106,
    HEADER_GC_CHANGE_NAME                       = 107,

	HEADER_GC_DUNGEON							= 110,
	HEADER_GC_WALK_MODE							= 111,
	HEADER_GC_CHANGE_SKILL_GROUP				= 112,

	// SUPPORT_BGM
	HEADER_GC_MAIN_CHARACTER2_EMPIRE			= 113,
	// END_OF_SUPPORT_BGM

    HEADER_GC_SEPCIAL_EFFECT                    = 114,
	HEADER_GC_NPC_POSITION						= 115,

	HEADER_GC_SPECIAL_SHOP = 116,
	HEADER_GC_NPC_INFO_BOARD = 117,

    HEADER_GC_LOGIN_KEY                         = 118,
    HEADER_GC_REFINE_INFORMATION_NEW            = 119,
    HEADER_GC_CHARACTER_ADD2                    = 120,
    HEADER_GC_CHANNEL                           = 121,

    HEADER_GC_MALL_OPEN                         = 122,
	HEADER_GC_TARGET_UPDATE                     = 123,
	HEADER_GC_TARGET_DELETE                     = 124,
	HEADER_GC_TARGET_CREATE_NEW                 = 125,

	HEADER_GC_AFFECT_ADD                        = 126,
	HEADER_GC_AFFECT_REMOVE                     = 127,

    HEADER_GC_MALL_SET                          = 128,
    HEADER_GC_MALL_DEL                          = 129,
	HEADER_GC_LAND_LIST                         = 130,
	HEADER_GC_LOVER_INFO						= 131,
	HEADER_GC_LOVE_POINT_UPDATE					= 132,
	HEADER_GC_GUILD_SYMBOL_DATA					= 133,
    HEADER_GC_DIG_MOTION                        = 134,

	HEADER_GC_DAMAGE_INFO						= 135,
	HEADER_GC_CHAR_ADDITIONAL_INFO				= 136,

	// SUPPORT_BGM
	HEADER_GC_MAIN_CHARACTER3_BGM				= 137,
	HEADER_GC_MAIN_CHARACTER4_BGM_VOL			= 138,
	// END_OF_SUPPORT_BGM

	HEADER_GC_SET_GOLD = 139,
	HEADER_GC_UPDATE_GOLD = 140,
	HEADER_GC_SPECIAL_FLAG = 141,

	HEADER_GC_ITEMSHOP = 142,
	HEADER_GC_BUSY_ACTION = 143,

	HEADER_GC_VERSION_VERIFIED = 149,

    HEADER_GC_AUTH_SUCCESS                      = 150,
    HEADER_GC_PANAMA_PACK						= 151,

	//HYBRID CRYPT
	HEADER_GC_HYBRIDCRYPT_KEYS					= 152,
	HEADER_GC_HYBRIDCRYPT_SDB					= 153, // SDB means Supplmentary Data Blocks
	//HYBRID CRYPT

	HEADER_GC_FISHING_GAME = 155,
	HEADER_GC_ADD_FLY_SHOOT_TARGETING = 156,
	HEADER_GC_CLEAR_FLY_SHOOT_TARGETING = 157,

#ifdef ENABLE_GUILD_TOKEN_AUTH
	HEADER_GC_GUILD_TOKEN						= 161,
#endif

	HEADER_GC_SPECIFIC_EFFECT					= 208,
	HEADER_GC_DRAGON_SOUL_REFINE				= 209,
	HEADER_GC_RESPOND_CHANNELSTATUS				= 210,
#ifdef ENABLE_IKASHOP_RENEWAL
	HEADER_GC_NEW_OFFLINESHOP					= 214,
#endif
#ifdef ENABLE_INGAME_EVENT_MANAGER
	// MT2009_PLUS_EVENT_MANAGER_V1: the in-game event list (server: playerbot_ingame_events.h).
	// 181, 182, 187, 238 are kept for Rumi, Yut Nori, the Flower Event and Catch the King.
	HEADER_GC_INGAME_EVENT						= 183,
#endif
	// MT2009_PLUS_MINIGAMES_V1 (Owsap v6.2.6 numbers and layouts)
#ifdef ENABLE_MINI_GAME_RUMI
	HEADER_GC_MINI_GAME_RUMI					= 181,
#endif
#ifdef ENABLE_MINI_GAME_YUTNORI
	HEADER_GC_MINI_GAME_YUTNORI					= 182,
#endif
#ifdef ENABLE_FLOWER_EVENT
	HEADER_GC_FLOWER_EVENT						= 187,
#endif
#ifdef ENABLE_SWITCHBOT
	HEADER_GC_SWITCHBOT							= 171,	// MT2009_PLUS_SWITCHBOT_V1 (gc header)
#ifdef ENABLE_FISH_EVENT
	HEADER_GC_FISH_EVENT_INFO					= 223,	// MT2009_PLUS_FISH_PUZZLE_V2 (gc header): the fish puzzle (the package's number)
#endif
#ifdef ENABLE_MT2009_SKILL_COLOR
	HEADER_GC_SKILL_COLOR						= 59,	// MT2009_PLUS_SKILL_COLOR_V1 (gc header): a character's colour of one skill
#endif
#ifdef ENABLE_MT2009_TITLES
	HEADER_GC_TITLE								= 189,	// MT2009_PLUS_TITLES_V1 (gc header): titles - dynamic (TABLE, PLAYER, EQUIPPED, NOTIFY, VISUAL)
#endif
#endif
#ifdef ENABLE_MINI_GAME_CATCH_KING
	HEADER_GC_MINI_GAME_CATCH_KING				= 238,
#endif
#ifdef ENABLE_NPC_LOCATION_HELPER
	HEADER_GC_NPC_LOCATION_HELPER				= 196,	// MT2009_PLUS_NPC_LOCATION_HELPER_V1 (gc header)
#endif
#ifdef ENABLE_12ZI
	HEADER_GC_SEPCIAL_ZODIAC_EFFECT				= 220, // MT2009_PLUS_ZODIAC_V1: the Zodiac bosses' effects (server packet.h)
#endif
#ifdef ENABLE_GROWTH_PET_SYSTEM
	// MT2009_PLUS_GROWTH_PET_V1 (gc headers): the growth pet - NOT Anka2's 173-184 (ours are taken); 235/236 are new
	HEADER_GC_PET								= 224,
	HEADER_GC_PET_SET							= 225,
	HEADER_GC_PET_SET_EXCHANGE					= 226,
	HEADER_GC_PET_DEL							= 227,
	HEADER_GC_PET_SUMMON						= 228,
	HEADER_GC_PET_POINT_CHANGE					= 229,
	HEADER_GC_PET_NAME_CHANGE_RESULT			= 230,
	HEADER_GC_PET_DETERMINE_RESULT				= 231,
	HEADER_GC_PET_ATTR_CHANGE_RESULT			= 232,
	HEADER_GC_PET_SKILL_UPDATE					= 233,
	HEADER_GC_PET_SKILL_COOLTIME				= 234,
	HEADER_GC_PET_LOOK							= 235,
	HEADER_GC_PET_POTENTIAL						= 236,
#endif

	HEADER_GC_KEY_AGREEMENT_COMPLETED			= 0xfa, // _IMPROVED_PACKET_ENCRYPTION_
	HEADER_GC_KEY_AGREEMENT						= 0xfb, // _IMPROVED_PACKET_ENCRYPTION_
	HEADER_GC_HANDSHAKE_OK						= 0xfc, // 252
	HEADER_GC_PHASE								= 0xfd,	// 253
    HEADER_GC_BINDUDP                           = 0xfe, // 254
    HEADER_GC_HANDSHAKE                         = 0xff, // 255
};

enum
{
	ID_MAX_NUM = 30,
	PASS_MAX_NUM = 16,
	CHAT_MAX_NUM = 128,
	PATH_NODE_MAX_NUM = 64,

	PLAYER_PER_ACCOUNT3 = 3,
#ifndef ENABLE_PLAYER_PER_ACCOUNT5
	PLAYER_PER_ACCOUNT4 = 4,
#else
	PLAYER_PER_ACCOUNT4 = 5,
	PLAYER_PER_ACCOUNT5 = 5,
#endif

	PLAYER_ITEM_SLOT_MAX_NUM = 20,

	METIN_SOCKET_COUNT = 6,

	PARTY_AFFECT_SLOT_MAX_NUM = 7,

	GUILD_GRADE_NAME_MAX_LEN = 8,
	GUILD_GRADE_COUNT = 15,
	GULID_COMMENT_MAX_LEN = 50,

	MARK_CRC_NUM = 8*8,
	MARK_DATA_SIZE = 16*12,
	SYMBOL_DATA_SIZE = 128*256,
	QUEST_INPUT_STRING_MAX_NUM = 64,

	PRIVATE_CODE_LENGTH = 8,
};

#pragma pack(push)
#pragma pack(1)

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Mark
typedef struct command_mark_login
{
    BYTE    header;
    DWORD   handle;
    DWORD   random_key;
} TPacketCGMarkLogin;

typedef struct command_mark_upload
{
    BYTE    header;
    DWORD   gid;
    BYTE    image[16*12*4];
#ifdef ENABLE_GUILD_TOKEN_AUTH
    uint64_t	token;
#endif
} TPacketCGMarkUpload;

typedef struct command_mark_idxlist
{
    BYTE    header;
} TPacketCGMarkIDXList;

typedef struct command_mark_crclist
{
    BYTE    header;
    BYTE    imgIdx;
    DWORD   crclist[80];
} TPacketCGMarkCRCList;

typedef struct packet_mark_idxlist
{
    BYTE    header;
	DWORD	bufSize;
    WORD    count;
} TPacketGCMarkIDXList;

typedef struct packet_mark_block
{
    BYTE    header;
    DWORD   bufSize;
	BYTE	imgIdx;
    DWORD   count;
} TPacketGCMarkBlock;

typedef struct command_symbol_upload
{
	BYTE	header;
	WORD	size;
	DWORD	handle;
#ifdef ENABLE_GUILD_TOKEN_AUTH
	uint64_t	token;
#endif
} TPacketCGSymbolUpload;

typedef struct command_symbol_crc
{
	BYTE	header;
	DWORD	dwGuildID;
	DWORD	dwCRC;
	DWORD	dwSize;
} TPacketCGSymbolCRC;

typedef struct packet_symbol_data
{
    BYTE header;
    WORD size;
    DWORD guild_id;
} TPacketGCGuildSymbolData;

//
//
//
typedef struct packet_observer_add
{
	BYTE	header;
	DWORD	vid;
	WORD	x;
	WORD	y;
} TPacketGCObserverAdd;

typedef struct packet_observer_move
{
	BYTE	header;
	DWORD	vid;
	WORD	x;
	WORD	y;
} TPacketGCObserverMove;

typedef struct packet_observer_remove
{
	BYTE	header;
	DWORD	vid;
} TPacketGCObserverRemove;

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// To Server

typedef struct command_checkin
{
	BYTE header;
	char name[ID_MAX_NUM+1];
	char pwd[PASS_MAX_NUM+1];
} TPacketCGCheckin;

typedef struct command_login
{
    BYTE header;
    char name[ID_MAX_NUM + 1];
    char pwd[PASS_MAX_NUM + 1];
} TPacketCGLogin;

typedef struct command_login2
{
	BYTE	header;
	char	name[ID_MAX_NUM + 1];
	DWORD	login_key;
    DWORD	adwClientKey[4];
} TPacketCGLogin2;

typedef struct command_login3
{
    BYTE	header;
    char	name[ID_MAX_NUM + 1];
    char	pwd[PASS_MAX_NUM + 1];
    DWORD	adwClientKey[4];
	char	hwid[HWID_MAX_LEN + 1];
} TPacketCGLogin3;

typedef struct command_direct_enter
{
    BYTE        bHeader;
    char        login[ID_MAX_NUM + 1];
    char        passwd[PASS_MAX_NUM + 1];
    BYTE        index;
} TPacketCGDirectEnter;

typedef struct command_player_select
{
	BYTE	header;
	BYTE	player_index;
} TPacketCGSelectCharacter;

typedef struct command_attack
{
	BYTE	header;
	BYTE	bType;
	DWORD	dwVictimVID;
	BYTE	bCRCMagicCubeProcPiece;
	BYTE	bCRCMagicCubeFilePiece;
} TPacketCGAttack;

typedef struct command_chat
{
	BYTE	header;
	WORD	length;
	BYTE	type;
} TPacketCGChat;

typedef struct command_whisper
{
    BYTE        bHeader;
    WORD        wSize;
    char        szNameTo[CHARACTER_NAME_MAX_LEN + 1];
} TPacketCGWhisper;

enum EBattleMode
{
	BATTLEMODE_ATTACK = 0,
	BATTLEMODE_DEFENSE = 1,
};

typedef struct command_EnterFrontGame
{
	BYTE header;
} TPacketCGEnterFrontGame;

typedef struct command_item_use
{
	BYTE header;
	TItemPos pos;
} TPacketCGItemUse;

typedef struct command_item_use_to_item
{
	BYTE header;
	TItemPos source_pos;
	TItemPos target_pos;
} TPacketCGItemUseToItem;

typedef struct command_item_drop
{
	BYTE  header;
	TItemPos pos;
#ifndef DISABLE_GOLD_PLAYER_DROP
	DWORD elk;
#endif
#if defined(ENABLE_CHEQUE_SYSTEM) && !defined(DISABLE_CHEQUE_DROP)
	DWORD cheque;
#endif
} TPacketCGItemDrop;

typedef struct command_item_drop2
{
    BYTE        header;
    TItemPos	pos;
#ifndef DISABLE_GOLD_PLAYER_DROP
    YANG       gold;
#endif
#if defined(ENABLE_CHEQUE_SYSTEM) && !defined(DISABLE_CHEQUE_DROP)
	DWORD		cheque;
#endif
    ITEM_COUNT        count;
} TPacketCGItemDrop2;

typedef struct command_item_move
{
	BYTE header;
	TItemPos pos;
	TItemPos change_pos;
	ITEM_COUNT num;
} TPacketCGItemMove;

typedef struct command_item_pickup
{
	BYTE header;
	DWORD vid;
} TPacketCGItemPickUp;

typedef struct command_quickslot_add
{
    BYTE        header;
    BYTE        pos;
	TQuickSlot	slot;
}TPacketCGQuickSlotAdd;

typedef struct command_quickslot_del
{
    BYTE        header;
    BYTE        pos;
}TPacketCGQuickSlotDel;

typedef struct command_quickslot_swap
{
    BYTE        header;
    BYTE        pos;
    BYTE        change_pos;
}TPacketCGQuickSlotSwap;

typedef struct command_on_click
{
	BYTE		header;
	DWORD		vid;
} TPacketCGOnClick;

enum {
	SUBHEADER_ITEMSHOP_BALANCE,
	SUBHEADER_ITEMSHOP_REFRESH,
	SUBHEADER_ITEMSHOP_HAPPY_HOUR,
	SUBHEADER_ITEMSHOP_OPEN_AUCTIONS,
	SUBHEADER_ITEMSHOP_UPDATE_AUCTION,
	SUBHEADER_ITEMSHOP_TIME_AUCTION,
	SUBHEADER_ITEMSHOP_USE_VOUCHER,
};

typedef struct SItemShopPromotion
{
	DWORD dwPrice;
	DWORD dwStartTime;
	DWORD dwEndTime;
} TItemShopPromotion;

typedef struct SItemShopTimeAuction
{
	DWORD dwCurrentBuyAmount; // progress if sent to client
	DWORD dwMaxBuyAmount;
	DWORD dwAccountLimit;
	DWORD dwStartTime;
	DWORD dwEndTime;
} TItemShopTimeAuction;

typedef struct SItemShopItem
{
	DWORD dwIndex;
	DWORD dwVnum;
	DWORD dwCount;
	DWORD dwPrice;
	BYTE bCurrency;
	BYTE bMinLevel;
	long	alSockets[ITEM_SOCKET_MAX_NUM];
	TItemShopPromotion promotion;
	TItemShopTimeAuction timeAuction;
} TItemShopItem;

typedef struct packet_itemshop
{
	BYTE	header;
	int	size;
	BYTE	subheader;
} TPacketGCItemShop;

typedef struct packet_itemshop_balance
{
	DWORD dwDragonCoins;
	DWORD dwDragonMarks;
} TPacketGCItemShopBalance;

typedef struct packet_itemshop_happyhour
{
	DWORD dwHappyHourValue;
	DWORD dwEndTime;
} TPacketGCItemShopHappyHour;

typedef struct packet_itemshop_time_auction
{
	DWORD dwEndTime;
} TPacketGCItemShopLatestTimeAuction;


typedef struct packet_itemshop_refresh
{
	WORD count;
} TPacketGCItemShopRefresh;

typedef struct SItemShopUpdateAuctionItem
{
	DWORD dwIndex;
	DWORD dwProgress;
	DWORD dwAccountLimit;
	DWORD dwStartTime;
	DWORD dwEndTime;
} TItemShopUpdateAuctionItem;

struct TPacketGCItemShopUseCodeVoucher
{
	BYTE bResponse;
};

enum
{
    SHOP_SUBHEADER_CG_END,
	SHOP_SUBHEADER_CG_BUY,
	SHOP_SUBHEADER_CG_SELL,
	SHOP_SUBHEADER_CG_SELL2,
};

typedef struct command_shop
{
	BYTE        header;
	BYTE		subheader;
} TPacketCGShop;

enum
{
	EXCHANGE_SUBHEADER_CG_START,			// arg1 == vid of target character
	EXCHANGE_SUBHEADER_CG_ITEM_ADD,			// arg1 == position of item
	EXCHANGE_SUBHEADER_CG_ITEM_DEL,			// arg1 == position of item
	EXCHANGE_SUBHEADER_CG_ELK_ADD,			// arg1 == amount of elk
	EXCHANGE_SUBHEADER_CG_ACCEPT,			// arg1 == not used
	EXCHANGE_SUBHEADER_CG_CANCEL,			// arg1 == not used
#ifdef ENABLE_CHEQUE_SYSTEM
	EXCHANGE_SUBHEADER_CG_CHEQUE_ADD,
#endif
};

typedef struct command_exchange
{
	BYTE		header;
	BYTE		subheader;
	long long		arg1;
	BYTE		arg2;
	TItemPos	Pos;
} TPacketCGExchange;

typedef struct command_position
{
    BYTE        header;
    BYTE        position;
} TPacketCGPosition;

typedef struct command_script_answer
{
    BYTE        header;
	BYTE		answer;
} TPacketCGScriptAnswer;

typedef struct command_script_button
{
    BYTE        header;
	unsigned int			idx;
} TPacketCGScriptButton;

typedef struct command_target
{
    BYTE        header;
    DWORD       dwVID;
} TPacketCGTarget;

typedef struct command_move
{
	BYTE		bHeader;
	BYTE		bFunc;
	BYTE		bArg;
	BYTE		bRot;
	LONG		lX;
	LONG		lY;
	DWORD		dwTime;
} TPacketCGMove;

typedef struct command_sync_position_element
{
    DWORD       dwVID;
    long        lX;
    long        lY;
} TPacketCGSyncPositionElement;

typedef struct command_sync_position
{
    BYTE        bHeader;
	WORD		wSize;
} TPacketCGSyncPosition;

typedef struct command_fly_targeting
{
	BYTE		bHeader;
	DWORD		dwTargetVID;
	long		lX;
	long		lY;
} TPacketCGFlyTargeting;

typedef struct packet_fly_targeting
{
    BYTE        bHeader;
	DWORD		dwShooterVID;
	DWORD		dwTargetVID;
	long		lX;
	long		lY;
} TPacketGCFlyTargeting;

typedef struct packet_fly_clear_targeting
{
	BYTE		bHeader;
	DWORD		dwShooterVID;
} TPacketGCFlyClearTargeting;

typedef struct packet_shoot
{
    BYTE		bHeader;
    BYTE		bType;
} TPacketCGShoot;

typedef struct command_warp
{
	BYTE			bHeader;
} TPacketCGWarp;

enum
{
	MESSENGER_SUBHEADER_GC_LIST,
	MESSENGER_SUBHEADER_GC_LOGIN,
	MESSENGER_SUBHEADER_GC_LOGOUT,
	MESSENGER_SUBHEADER_GC_INVITE,
	MESSENGER_SUBHEADER_GC_BLOCK_LIST,
};

typedef struct packet_messenger
{
    BYTE header;
    WORD size;
    BYTE subheader;
} TPacketGCMessenger;

typedef struct packet_messenger_list_offline
{
    BYTE connected; // always 0
	BYTE length;
} TPacketGCMessengerListOffline;

enum
{
	MESSENGER_CONNECTED_STATE_OFFLINE,
	MESSENGER_CONNECTED_STATE_ONLINE,
};

typedef struct packet_messenger_list_online
{
    BYTE connected;
	BYTE length;
	//BYTE length_char_name;
} TPacketGCMessengerListOnline;

typedef struct packet_messenger_login
{
	//BYTE length_login;
	//BYTE length_char_name;
	BYTE length;
} TPacketGCMessengerLogin;

typedef struct packet_messenger_logout
{
	BYTE length;
} TPacketGCMessengerLogout;

struct TPacketGCMessengerBlockList
{
	DWORD count;
};

struct TPacketGCMessengerBlockItem
{
	char name[PLAYER_NAME_MAX_LEN + 1];
	bool isAdd;
};

enum
{
    MESSENGER_SUBHEADER_CG_ADD_BY_VID,
    MESSENGER_SUBHEADER_CG_ADD_BY_NAME,
    MESSENGER_SUBHEADER_CG_REMOVE,
	MESSENGER_SUBHEADER_CG_INVITE_ANSWER,
	MESSENGER_SUBHEADER_CG_ADD_BLOCK,
	MESSENGER_SUBHEADER_CG_REMOVE_BLOCK,
};

typedef struct command_messenger
{
    BYTE header;
    BYTE subheader;
} TPacketCGMessenger;

typedef struct command_messenger_remove
{
	BYTE length;
} TPacketCGMessengerRemove;

enum
{
	SAFEBOX_MONEY_STATE_SAVE,
	SAFEBOX_MONEY_STATE_WITHDRAW,
};

typedef struct command_safebox_money
{
    BYTE        bHeader;
    BYTE        bState;
    DWORD       dwMoney;
} TPacketCGSafeboxMoney;

typedef struct command_safebox_checkout
{
    BYTE        bHeader;
    BYTE        bSafePos;
    TItemPos	ItemPos;
} TPacketCGSafeboxCheckout;

typedef struct command_safebox_checkin
{
    BYTE        bHeader;
    BYTE        bSafePos;
    TItemPos	ItemPos;
} TPacketCGSafeboxCheckin;

typedef struct command_mall_checkout
{
    BYTE        bHeader;
    BYTE        bMallPos;
    TItemPos	ItemPos;
} TPacketCGMallCheckout;

///////////////////////////////////////////////////////////////////////////////////
// Party

typedef struct command_use_skill
{
    BYTE                bHeader;
    DWORD               dwVnum;
	DWORD				dwTargetVID;
} TPacketCGUseSkill;

typedef struct command_party_invite
{
    BYTE header;
    DWORD vid;
} TPacketCGPartyInvite;

typedef struct command_party_invite_answer
{
    BYTE header;
    DWORD leader_pid;
    BYTE accept;
} TPacketCGPartyInviteAnswer;

typedef struct command_party_remove
{
    BYTE header;
    DWORD pid;
} TPacketCGPartyRemove;

typedef struct command_party_set_state
{
    BYTE byHeader;
    DWORD dwVID;
	BYTE byState;
    BYTE byFlag;
} TPacketCGPartySetState;

typedef struct packet_party_link
{
    BYTE header;
    DWORD pid;
    DWORD vid;
} TPacketGCPartyLink;

typedef struct packet_party_unlink
{
    BYTE header;
    DWORD pid;
	DWORD vid;
} TPacketGCPartyUnlink;

typedef struct command_party_use_skill
{
    BYTE byHeader;
	BYTE bySkillIndex;
    DWORD dwTargetVID;
} TPacketCGPartyUseSkill;

enum
{
	GUILD_SUBHEADER_CG_ADD_MEMBER,
	GUILD_SUBHEADER_CG_REMOVE_MEMBER,
	GUILD_SUBHEADER_CG_CHANGE_GRADE_NAME,
	GUILD_SUBHEADER_CG_CHANGE_GRADE_AUTHORITY,
	GUILD_SUBHEADER_CG_OFFER,
	GUILD_SUBHEADER_CG_POST_COMMENT,
	GUILD_SUBHEADER_CG_DELETE_COMMENT,
	GUILD_SUBHEADER_CG_REFRESH_COMMENT,
	GUILD_SUBHEADER_CG_CHANGE_MEMBER_GRADE,
	GUILD_SUBHEADER_CG_USE_SKILL,
	GUILD_SUBHEADER_CG_CHANGE_MEMBER_GENERAL,
	GUILD_SUBHEADER_CG_GUILD_INVITE_ANSWER,
	GUILD_SUBHEADER_CG_CHARGE_GSP,
	GUILD_SUBHEADER_CG_DEPOSIT_MONEY,
	GUILD_SUBHEADER_CG_WITHDRAW_MONEY,
};

typedef struct command_guild
{
    BYTE byHeader;
	BYTE bySubHeader;
} TPacketCGGuild;

typedef struct command_guild_answer_make_guild
{
	BYTE header;
	char guild_name[GUILD_NAME_MAX_LEN+1];
} TPacketCGAnswerMakeGuild;

typedef struct command_give_item
{
	BYTE byHeader;
	DWORD dwTargetVID;
	TItemPos ItemPos;
	ITEM_COUNT byItemCount;
} TPacketCGGiveItem;

struct TPacketCGSendFishing {
	BYTE header;
	DWORD focusHWND;
	DWORD pythonApplicationHWND;
	BYTE dir;
};

typedef struct SPacketCGHack
{
    BYTE        bHeader;
    char        szBuf[255 + 1];
} TPacketCGHack;

typedef struct command_dungeon
{
	BYTE		bHeader;
	WORD		size;
} TPacketCGDungeon;

// Private Shop
typedef struct SShopItemTable
{
    DWORD		vnum;
	ITEM_COUNT		count;

    TItemPos	pos;
	YANG		price;
#ifdef ENABLE_CHEQUE_SYSTEM
	DWORD		cheque;
#endif
    BYTE		display_pos;
} TShopItemTable;

typedef struct SPacketCGMyShop
{
    BYTE        bHeader;
    char        szSign[SHOP_SIGN_MAX_LEN + 1];
	BYTE		bTimeIndex;
    BYTE        bCount;	// count of TShopItemTable
} TPacketCGMyShop;

typedef struct SPacketCGRefine
{
	BYTE		header;
	BYTE		pos;
	BYTE		type;
} TPacketCGRefine;

typedef struct SPacketCGChangeName
{
    BYTE header;
    BYTE index;
    char name[CHARACTER_NAME_MAX_LEN+1];
} TPacketCGChangeName;

typedef struct command_client_version2
{
	BYTE header;
	char filename[32+1];
	char timestamp[32+1];
} TPacketCGClientVersion2;

typedef struct command_crc_report
{
	BYTE header;
	BYTE byPackMode;
	DWORD dwBinaryCRC32;
	DWORD dwProcessCRC32;
	DWORD dwRootPackCRC32;
} TPacketCGCRCReport;

enum EPartyExpDistributionType
{
    PARTY_EXP_DISTRIBUTION_NON_PARITY,
    PARTY_EXP_DISTRIBUTION_PARITY,
};

typedef struct command_party_parameter
{
    BYTE        bHeader;
    BYTE        bDistributeMode;
} TPacketCGPartyParameter;

typedef struct command_quest_input_string
{
    BYTE        bHeader;
    char		szString[QUEST_INPUT_STRING_MAX_NUM+1];
} TPacketCGQuestInputString;

typedef struct command_quest_confirm
{
    BYTE header;
    BYTE answer;
    DWORD requestPID;
} TPacketCGQuestConfirm;

typedef struct command_script_select_item
{
    BYTE header;
    DWORD selection;
} TPacketCGScriptSelectItem;

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// From Server
enum EPhase
{
    PHASE_CLOSE,
    PHASE_HANDSHAKE,
    PHASE_LOGIN,
    PHASE_SELECT,
    PHASE_LOADING,
    PHASE_GAME,
    PHASE_DEAD,

	PHASE_DBCLIENT_CONNECTING,
    PHASE_DBCLIENT,
    PHASE_P2P,
    PHASE_AUTH,
};

typedef struct packet_phase
{
    BYTE        header;
    BYTE        phase;
} TPacketGCPhase;

typedef struct packet_blank
{
	BYTE		header;
} TPacketGCBlank;

typedef struct packet_blank_dynamic
{
	BYTE		header;
	WORD		size;
} TPacketGCBlankDynamic;

typedef struct packet_header_handshake
{
	BYTE		header;
	DWORD		dwHandshake;
	DWORD		dwTime;
	LONG		lDelta;
} TPacketGCHandshake;

typedef struct packet_header_bindudp
{
	BYTE		header;
	DWORD		addr;
	WORD		port;
} TPacketGCBindUDP;

typedef struct packet_header_dynamic_size
{
	BYTE		header;
	WORD		size;
} TDynamicSizePacketHeader;

#ifdef ENABLE_LARGE_DYNAMIC_PACKETS
typedef struct packet_header_large_dynamic_size
{
	BYTE		header;
	int			size;
} TLargeDynamicSizePacketHeader;
#endif

typedef struct SSimplePlayerInformation
{
    DWORD               dwID;
    char                szName[CHARACTER_NAME_MAX_LEN + 1];
    BYTE                byJob;
    BYTE                byLevel;
    DWORD               dwPlayMinutes;
    BYTE                byST, byHT, byDX, byIQ;
    DWORD               wMainPart; // @fixme502
    BYTE                bChangeName;
    DWORD				wHairPart; // @fixme502
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
	DWORD				wAccePart;
#endif
    BYTE                bDummy[4];
	long				x, y;
	LONG				lAddr;
	WORD				wPort;
	BYTE				bySkillGroup;
} TSimplePlayerInformation;

typedef struct packet_login_success3
{
	BYTE						header;
	TSimplePlayerInformation	akSimplePlayerInformation[PLAYER_PER_ACCOUNT3];
    DWORD						guild_id[PLAYER_PER_ACCOUNT3];
    char						guild_name[PLAYER_PER_ACCOUNT3][GUILD_NAME_MAX_LEN+1];
	DWORD handle;
	DWORD random_key;
} TPacketGCLoginSuccess3;

typedef struct packet_login_success4
{
	BYTE						header;
	TSimplePlayerInformation	akSimplePlayerInformation[PLAYER_PER_ACCOUNT4];
    DWORD						guild_id[PLAYER_PER_ACCOUNT4];
    char						guild_name[PLAYER_PER_ACCOUNT4][GUILD_NAME_MAX_LEN+1];
	DWORD handle;
	DWORD random_key;
} TPacketGCLoginSuccess4;

#ifdef ENABLE_PLAYER_PER_ACCOUNT5
typedef struct packet_login_success5
{
	BYTE						header;
	TSimplePlayerInformation	akSimplePlayerInformation[PLAYER_PER_ACCOUNT5];
    DWORD						guild_id[PLAYER_PER_ACCOUNT5];
    char						guild_name[PLAYER_PER_ACCOUNT5][GUILD_NAME_MAX_LEN+1];
	DWORD handle;
	DWORD random_key;
} TPacketGCLoginSuccess5;
#endif

enum { LOGIN_STATUS_MAX_LEN = 8 };
typedef struct packet_login_failure
{
	BYTE	header;
	char	szStatus[LOGIN_STATUS_MAX_LEN + 1];
} TPacketGCLoginFailure;

typedef struct command_player_create
{
	BYTE        header;
	BYTE        index;
	char        name[CHARACTER_NAME_MAX_LEN + 1];
	WORD        job;
	BYTE		shape;
	BYTE		CON;
	BYTE		INT;
	BYTE		STR;
	BYTE		DEX;
} TPacketCGCreateCharacter;

typedef struct command_player_create_success
{
    BYTE						header;
    BYTE						bAccountCharacterSlot;
    TSimplePlayerInformation	kSimplePlayerInfomation;
} TPacketGCPlayerCreateSuccess;

typedef struct command_create_failure
{
	BYTE	header;
	BYTE	bType;
} TPacketGCCreateFailure;

typedef struct command_player_delete
{
	BYTE        header;
	BYTE        index;
	char		szPrivateCode[PRIVATE_CODE_LENGTH];
} TPacketCGDestroyCharacter;

typedef struct packet_player_delete_success
{
	BYTE        header;
	BYTE        account_index;
} TPacketGCDestroyCharacterSuccess;

enum
{
	ADD_CHARACTER_STATE_DEAD   = (1 << 0),
	ADD_CHARACTER_STATE_SPAWN  = (1 << 1),
	ADD_CHARACTER_STATE_GUNGON = (1 << 2),
	ADD_CHARACTER_STATE_KILLER = (1 << 3),
	ADD_CHARACTER_STATE_PARTY  = (1 << 4),
};

enum EPKModes
{
	PK_MODE_PEACE,
	PK_MODE_REVENGE,
	PK_MODE_FREE,
	PK_MODE_PROTECT,
	PK_MODE_GUILD,
	PK_MODE_MAX_NUM,
};

typedef struct packet_char_additional_info
{
	BYTE    header;
	DWORD   dwVID;
	char    name[CHARACTER_NAME_MAX_LEN + 1];
	DWORD   awPart[PART_MAX_NUM]; // @fixme502
	BYTE	bEmpire;
	DWORD   dwGuildID;
	DWORD   dwLevel;
	short   sAlignment;
	BYTE    bPKMode;
	DWORD   dwMountVnum;
#ifdef ENABLE_QUIVER_SYSTEM
	DWORD	dwArrow;
#endif
#ifdef ENABLE_CONQUEROR_LEVEL
	DWORD	dwConquerorLevel;	// MT2009_PLUS_CHAMPION_V2: Poziom Czempiona (0 = none), the blue level over the head
#endif
} TPacketGCCharacterAdditionalInfo;

typedef struct packet_add_char
{
    BYTE        header;

    DWORD       dwVID;

    float       angle;
    long        x;
    long        y;
    long        z;

	BYTE		bType;
    DWORD       wRaceNum; // @fixme501
    BYTE        bMovingSpeed;
    BYTE        bAttackSpeed;

    BYTE        bStateFlag;
    DWORD       dwAffectFlag[2];
} TPacketGCCharacterAdd;

typedef struct packet_add_char2
{
    BYTE        header;

    DWORD       dwVID;

    char        name[CHARACTER_NAME_MAX_LEN + 1];

    float       angle;
    long        x;
    long        y;
    long        z;

	BYTE		bType;
    DWORD       wRaceNum; // @fixme501
    DWORD       awPart[PART_MAX_NUM]; // @fixme502
    BYTE        bMovingSpeed;
    BYTE        bAttackSpeed;

    BYTE        bStateFlag;
    DWORD       dwAffectFlag[2];
    BYTE        bEmpire;

    DWORD       dwGuild;
    short       sAlignment;
	BYTE		bPKMode;
	DWORD		dwMountVnum;
#ifdef ENABLE_QUIVER_SYSTEM
	DWORD		dwArrow;
#endif
} TPacketGCCharacterAdd2;

typedef struct packet_update_char
{
    BYTE        header;
    DWORD       dwVID;

    DWORD		awPart[PART_MAX_NUM]; // @fixme502
    BYTE        bMovingSpeed;
	BYTE		bAttackSpeed;

    BYTE        bStateFlag;
    DWORD       dwAffectFlag[2];

	DWORD		dwGuildID;
	BYTE		bLevel;
    short       sAlignment;
	BYTE		bPKMode;
	DWORD		dwMountVnum;
#ifdef ENABLE_QUIVER_SYSTEM
	DWORD		dwArrow;
#endif
#ifdef ENABLE_CONQUEROR_LEVEL
	DWORD		dwConquerorLevel;	// MT2009_PLUS_CHAMPION_V2: Poziom Czempiona (0 = none)
#endif
} TPacketGCCharacterUpdate;

typedef struct packet_del_char
{
	BYTE	header;
    DWORD	dwVID;
} TPacketGCCharacterDelete;

typedef struct packet_GlobalTime
{
	BYTE	header;
	float	GlobalTime;
} TPacketGCGlobalTime;

typedef struct packet_chatting
{
	BYTE	header;
	WORD	size;
	BYTE	type;
	DWORD	dwVID;
	BYTE	bEmpire;
} TPacketGCChat;

typedef struct packet_whisper
{
    BYTE        bHeader;
    WORD        wSize;
    BYTE        bType;
    char        szNameFrom[CHARACTER_NAME_MAX_LEN + 1];
} TPacketGCWhisper;

typedef struct packet_stun
{
	BYTE		header;
	DWORD		vid;
} TPacketGCStun;

typedef struct packet_dead
{
	BYTE		header;
	DWORD		vid;
} TPacketGCDead;

typedef struct packet_main_character
{
    BYTE        header;
    DWORD       dwVID;
	DWORD		wRaceNum; // @fixme501
    char        szName[CHARACTER_NAME_MAX_LEN + 1];
    long        lX, lY, lZ;
	BYTE		bySkillGroup;
} TPacketGCMainCharacter;

// SUPPORT_BGM
typedef struct packet_main_character2_empire
{
    BYTE        header;
    DWORD       dwVID;
	DWORD		wRaceNum; // @fixme501
    char        szName[CHARACTER_NAME_MAX_LEN + 1];
    long        lX, lY, lZ;
	BYTE		byEmpire;
	BYTE		bySkillGroup;
} TPacketGCMainCharacter2_EMPIRE;

typedef struct packet_main_character3_bgm
{
	enum
	{
		MUSIC_NAME_MAX_LEN = 24,
	};
    BYTE        header;
    DWORD       dwVID;
	DWORD		wRaceNum; // @fixme501
    char        szUserName[CHARACTER_NAME_MAX_LEN + 1];
	char        szBGMName[MUSIC_NAME_MAX_LEN + 1];
    long        lX, lY, lZ;
	BYTE		byEmpire;
	BYTE		bySkillGroup;
} TPacketGCMainCharacter3_BGM;

typedef struct packet_main_character4_bgm_vol
{
	enum
	{
		MUSIC_NAME_MAX_LEN = 24,
	};
    BYTE        header;
    DWORD       dwVID;
	DWORD		wRaceNum; // @fixme501
    char        szUserName[CHARACTER_NAME_MAX_LEN + 1];
	char        szBGMName[MUSIC_NAME_MAX_LEN + 1];
	float		fBGMVol;
    long        lX, lY, lZ;
	BYTE		byEmpire;
	BYTE		bySkillGroup;
} TPacketGCMainCharacter4_BGM_VOL;
// END_OF_SUPPORT_BGM

typedef struct packet_points
{
    BYTE        header;
    long        points[POINT_PACKET_NUM]; // MT2009_PLUS_YOHARA_EXE2_V1: 193 points (the server's POINT_PACKET_NUM); POINT_MAX_NUM is 198
} TPacketGCPoints;

typedef struct packet_point_change
{
    int         header;

	DWORD		dwVID;
	WORD		Type;	// MT2009_PLUS_WIDE_ATTR_V1 (point change): a POINT_* number up to 512 (server packet.h)

	long        amount;
    long        value;
} TPacketGCPointChange;

typedef struct packet_motion
{
	BYTE		header;
	DWORD		vid;
	DWORD		victim_vid;
	WORD		motion;
} TPacketGCMotion;

typedef struct SPacketGold
{
	BYTE bHeader;
	YANG totalGold;
} TPacketGCGoldUpdate;

typedef struct SPacketBusyAction
{
	BYTE bHeader;
	BYTE bActionType;
	DWORD dwDuration;
	bool bSuccess;
} TPacketGCBusyAction;
	

typedef struct packet_set_item
{
	BYTE		header;
	TItemPos	Cell;
	DWORD		vnum;
	ITEM_COUNT		count;
	long		alSockets[ITEM_SOCKET_SLOT_MAX_NUM];
    TPlayerItemAttribute aAttr[ITEM_ATTRIBUTE_SLOT_MAX_NUM];
#ifdef ENABLE_CHANGELOOK_SYSTEM
	DWORD		dwTransmutation; // MT2009_PLUS_CHANGE_LOOK_V1: the server's last field
#endif
} TPacketGCItemSet;

typedef struct packet_set_item2
{
	BYTE		header;
	TItemPos	Cell;
	DWORD		vnum;
	ITEM_COUNT		count;
	DWORD		flags;
	DWORD		anti_flags;
	bool		highlight;
	long		alSockets[ITEM_SOCKET_SLOT_MAX_NUM];
    TPlayerItemAttribute aAttr[ITEM_ATTRIBUTE_SLOT_MAX_NUM];
#ifdef ENABLE_CHANGELOOK_SYSTEM
	DWORD		dwTransmutation; // MT2009_PLUS_CHANGE_LOOK_V1: the server's last field
#endif
} TPacketGCItemSet2;

typedef struct packet_item_del
{
    BYTE        header;
    BYTE        pos;
} TPacketGCItemDel;

typedef struct packet_use_item
{
	BYTE		header;
	TItemPos	Cell;
	DWORD		ch_vid;
	DWORD		victim_vid;

	DWORD		vnum;
} TPacketGCItemUse;

typedef struct packet_update_item
{
	BYTE		header;
	TItemPos	Cell;
	ITEM_COUNT		count;
	long		alSockets[ITEM_SOCKET_SLOT_MAX_NUM];
    TPlayerItemAttribute aAttr[ITEM_ATTRIBUTE_SLOT_MAX_NUM];
#ifdef ENABLE_CHANGELOOK_SYSTEM
	DWORD		dwTransmutation; // MT2009_PLUS_CHANGE_LOOK_V1: the server's last field
#endif
} TPacketGCItemUpdate;

typedef struct packet_ground_add_item
{
    BYTE        bHeader;
    long        lX;
	long		lY;
	long		lZ;

    DWORD       dwVID;
    DWORD       dwVnum;
	ITEM_COUNT	count;
	BYTE		bIsAttr;
} TPacketGCItemGroundAdd;

typedef struct packet_ground_del_item
{
	BYTE		header;
	DWORD		vid;
} TPacketGCItemGroundDel;

typedef struct packet_item_ownership
{
    BYTE        bHeader;
    DWORD       dwVID;
    char        szName[CHARACTER_NAME_MAX_LEN + 1];
} TPacketGCItemOwnership;

typedef struct packet_quickslot_add
{
    BYTE        header;
    BYTE        pos;
	TQuickSlot	slot;
} TPacketGCQuickSlotAdd;

typedef struct packet_quickslot_del
{
    BYTE        header;
    BYTE        pos;
} TPacketGCQuickSlotDel;

typedef struct packet_quickslot_swap
{
    BYTE        header;
    BYTE        pos;
    BYTE        change_pos;
} TPacketGCQuickSlotSwap;



// MT2009 Plus: byte-exact protocol shared with shop_search_plus.h.
enum { TARGET_DROP_ITEM_COUNT = 70 };

typedef struct packet_cg_target_drop
{
	BYTE header;
} TPacketCGTargetDrop;

typedef struct packet_gc_target_drop
{
	BYTE header;
	WORD raceVnum;
	WORD size;
	DWORD items[TARGET_DROP_ITEM_COUNT];
} TPacketGCTargetDrop;

typedef struct packet_cg_private_shop_search
{
	BYTE header;
	BYTE bJob;
	BYTE bMaskType;
	int iMaskSub;
	int iMinRefine;
	int iMaxRefine;
	int iMinLevel;
	int iMaxLevel;
	long long llMinGold;
	long long llMaxGold;
	char szItemName[33];
} TPacketCGPrivateShopSearch;

typedef struct packet_cg_private_shop_search_close
{
	BYTE header;
} TPacketCGPrivateShopSearchClose;

typedef struct packet_cg_private_shop_search_buy_item
{
	BYTE header;
	DWORD dwShopPID;
	DWORD dwItemID;
	long long llSeenPrice;
} TPacketCGPrivateShopSearchBuyItem;

typedef struct packet_gc_private_shop_search
{
	BYTE header;
	WORD size;
} TPacketGCPrivateShopSearch;

typedef struct packet_gc_private_shop_search_item
{
	TShopItemData item;
	char szSellerName[25];
	DWORD dwShopPID;
	DWORD dwItemID;
	long lMapIndex;
	long lX;
	long lY;
	BYTE bChannel;
} TPacketGCPrivateShopSearchItem;

typedef struct packet_gc_private_shop_search_open
{
	BYTE header;
	BYTE bMode;
} TPacketGCPrivateShopSearchOpen;

typedef struct packet_gc_private_shop_search_mark
{
	BYTE header;
	DWORD dwShopVID;
	long lX;
	long lY;
} TPacketGCPrivateShopSearchMark;

static_assert(sizeof(TPacketGCTargetDrop) == 285, "target drop packet size mismatch");
static_assert(sizeof(TPacketCGPrivateShopSearch) == 72, "private shop search request size mismatch");
static_assert(sizeof(TPacketGCPrivateShopSearchItem) == 103, "private shop search result size mismatch"); // MT2009_PLUS_WIDE_ATTR_V1: 7 bonus lines x 4 B (client-only - the server sends no 216)
static_assert(sizeof(TPacketCGPrivateShopSearchBuyItem) == 17, "private shop search buy size mismatch");
static_assert(sizeof(TPacketGCPrivateShopSearchMark) == 13, "private shop search mark size mismatch");

typedef struct packet_shop_start
{
	BYTE unlockCount;
	bool isPremium;
	struct packet_shop_item		items[SHOP_PLAYER_HOST_ITEM_MAX_NUM];
} TPacketGCShopStart;

typedef struct packet_shop_start_ex
{
	typedef struct sub_packet_shop_tab
	{
		char name[SHOP_TAB_NAME_MAX];
		BYTE coin_type;
		packet_shop_item items[SHOP_HOST_ITEM_MAX_NUM];
	} TSubPacketShopTab;
	DWORD owner_vid;
	BYTE shop_tab_count;
} TPacketGCShopStartEx;

typedef struct packet_shop_update_item
{
	BYTE						pos;
	struct packet_shop_item		item;
} TPacketGCShopUpdateItem;

typedef struct packet_shop_update_price
{
	YANG iElkAmount;
} TPacketGCShopUpdatePrice;

enum EPacketShopSubHeaders
{
	SHOP_SUBHEADER_GC_START,
    SHOP_SUBHEADER_GC_END,
	SHOP_SUBHEADER_GC_UPDATE_ITEM,
	SHOP_SUBHEADER_GC_UPDATE_PRICE,
    SHOP_SUBHEADER_GC_OK,
    SHOP_SUBHEADER_GC_NOT_ENOUGH_MONEY,
    SHOP_SUBHEADER_GC_SOLDOUT,
    SHOP_SUBHEADER_GC_INVENTORY_FULL,
    SHOP_SUBHEADER_GC_INVALID_POS,
	SHOP_SUBHEADER_GC_SOLD_OUT,
	SHOP_SUBHEADER_GC_START_EX,
	SHOP_SUBHEADER_GC_NOT_ENOUGH_MONEY_EX,
#ifdef ENABLE_CHEQUE_SYSTEM
	SHOP_SUBHEADER_GC_NOT_ENOUGH_CHEQUE,
	SHOP_SUBHEADER_GC_NOT_ENOUGH_MONEY_CHEQUE,
#endif
};

typedef struct packet_shop
{
	BYTE        header;
	WORD		size;
	BYTE        subheader;
} TPacketGCShop;

typedef struct packet_exchange
{
    BYTE        header;
    BYTE        subheader;
    BYTE        is_me;
    long long       arg1;
    TItemPos       arg2;
    ITEM_COUNT       arg3;
	TItemPos	arg4;
	long		alValues[ITEM_SOCKET_SLOT_MAX_NUM];
    TPlayerItemAttribute aAttr[ITEM_ATTRIBUTE_SLOT_MAX_NUM];
#ifdef ENABLE_CHANGELOOK_SYSTEM
	DWORD		dwTransmutation; // MT2009_PLUS_CHANGE_LOOK_V1: the server's last field
#endif
} TPacketGCExchange;

enum
{
    EXCHANGE_SUBHEADER_GC_START,			// arg1 == vid
    EXCHANGE_SUBHEADER_GC_ITEM_ADD,			// arg1 == vnum  arg2 == pos  arg3 == count
	EXCHANGE_SUBHEADER_GC_ITEM_DEL,			// arg1 == pos
    EXCHANGE_SUBHEADER_GC_ELK_ADD,			// arg1 == elk
    EXCHANGE_SUBHEADER_GC_ACCEPT,			// arg1 == accept
    EXCHANGE_SUBHEADER_GC_END,				// arg1 == not used
    EXCHANGE_SUBHEADER_GC_ALREADY,			// arg1 == not used
    EXCHANGE_SUBHEADER_GC_LESS_ELK,			// arg1 == not used
#ifdef ENABLE_CHEQUE_SYSTEM
	EXCHANGE_SUBHEADER_GC_CHEQUE_ADD,
	EXCHANGE_SUBHEADER_GC_LESS_CHEQUE,
#endif
};

typedef struct packet_position
{
    BYTE        header;
	DWORD		vid;
    BYTE        position;
} TPacketGCPosition;

typedef struct packet_ping
{
	BYTE		header;
} TPacketGCPing;

typedef struct packet_pong
{
	BYTE		bHeader;
} TPacketCGPong;

typedef struct packet_script
{
    BYTE		header;
    WORD        size;
	BYTE		skin;
    WORD        src_size;
} TPacketGCScript;

enum ETargetSubheader
{
	SUBHEADER_GC_TARGET_ONLY,
	SUBHEADER_GC_TARGET_WITH_DEBUFFS
};

typedef struct packet_target
{
	BYTE	header;
	WORD	size;
	BYTE	subheader;
	DWORD	dwVID;
	BYTE	bHPPercent;
} TPacketGCTarget;

struct STargetDebuff
{
	DWORD affect;
	long duration;
};

typedef struct subpacket_target_debuffs
{
	BYTE affectCount;
} TSubPacketGCTargetDebuffs;

typedef struct packet_damage_info
{
	BYTE header;
	DWORD dwVID;
	BYTE flag;
	int  damage;
} TPacketGCDamageInfo;

typedef struct packet_mount
{
    BYTE        header;
    DWORD       vid;
    DWORD       mount_vid;
    BYTE        pos;
	DWORD		_x, _y;
} TPacketGCMount;

typedef struct packet_change_speed
{
	BYTE		header;
	DWORD		vid;
	WORD		moving_speed;
} TPacketGCChangeSpeed;

typedef struct packet_move
{
	BYTE		bHeader;
	BYTE		bFunc;
	BYTE		bArg;
	BYTE		bRot;
	DWORD		dwVID;
	LONG		lX;
	LONG		lY;
	DWORD		dwTime;
	DWORD		dwDuration;
} TPacketGCMove;

enum
{
	QUEST_SEND_IS_BEGIN         = 1 << 0,
    QUEST_SEND_TITLE            = 1 << 1,
    QUEST_SEND_CLOCK_NAME       = 1 << 2,
    QUEST_SEND_CLOCK_VALUE      = 1 << 3,
    QUEST_SEND_COUNTER_NAME     = 1 << 4,
    QUEST_SEND_COUNTER_VALUE    = 1 << 5,
	QUEST_SEND_ICON_FILE		= 1 << 6,
};

typedef struct packet_quest_info
{
	BYTE header;
	WORD size;
	WORD index;
	BYTE flag;
} TPacketGCQuestInfo;

typedef struct packet_quest_confirm
{
    BYTE header;
    char msg[64+1];
    long timeout;
    DWORD requestPID;
} TPacketGCQuestConfirm;

typedef struct packet_attack
{
    BYTE        header;
    DWORD       dwVID;
    DWORD       dwVictimVID;
    BYTE        bType;
} TPacketGCAttack;

typedef struct packet_c2c
{
	BYTE		header;
	WORD		wSize;
} TPacketGCC2C;

typedef struct packetd_sync_position_element
{
    DWORD       dwVID;
    long        lX;
    long        lY;
} TPacketGCSyncPositionElement;

typedef struct packetd_sync_position
{
    BYTE        bHeader;
    WORD		wSize;
} TPacketGCSyncPosition;

typedef struct packet_ownership
{
    BYTE                bHeader;
    DWORD               dwOwnerVID;
    DWORD               dwVictimVID;
} TPacketGCOwnership;

typedef struct packet_skill_level
{
    BYTE        bHeader;
    BYTE        abSkillLevels[SKILL_MAX_NUM];
} TPacketGCSkillLevel;

typedef struct SPlayerSkill
{
	BYTE bMasterType;
	BYTE bLevel;
	time_t tNextRead;
} TPlayerSkill;

typedef struct packet_skill_level_new
{
	BYTE bHeader;
	TPlayerSkill skills[SKILL_MAX_NUM];
} TPacketGCSkillLevelNew;

// fly
typedef struct packet_fly
{
    BYTE        bHeader;
    BYTE        bType;
    DWORD       dwStartVID;
    DWORD       dwEndVID;
} TPacketGCCreateFly;

enum EPVPModes
{
	PVP_MODE_NONE,
    PVP_MODE_AGREE,
    PVP_MODE_FIGHT,
    PVP_MODE_REVENGE,
};

typedef struct packet_duel_start
{
    BYTE	header ;
    WORD	wSize ;
} TPacketGCDuelStart ;

typedef struct packet_pvp
{
	BYTE		header;
	DWORD		dwVIDSrc;
	DWORD		dwVIDDst;
	BYTE		bMode;
} TPacketGCPVP;

typedef struct packet_skill_cooltime_end
{
	BYTE		header;
	BYTE		bSkill;
} TPacketGCSkillCoolTimeEnd;

typedef struct packet_warp
{
	BYTE			bHeader;
	LONG			lX;
	LONG			lY;
	LONG			lAddr;
	WORD			wPort;
} TPacketGCWarp;

typedef struct packet_party_invite
{
    BYTE header;
    DWORD leader_pid;
} TPacketGCPartyInvite;

typedef struct packet_party_add
{
    BYTE header;
    DWORD pid;
    char name[CHARACTER_NAME_MAX_LEN+1];
} TPacketGCPartyAdd;

typedef struct packet_party_update
{
    BYTE header;
    DWORD pid;
    BYTE state;
    BYTE percent_hp;
    short affects[PARTY_AFFECT_SLOT_MAX_NUM];
#if defined(PARTY_POSITION)
	long x;
	long y;
#endif
} TPacketGCPartyUpdate;

typedef struct packet_party_remove
{
    BYTE header;
    DWORD pid;
} TPacketGCPartyRemove;

typedef TPacketCGSafeboxCheckout TPacketGCSafeboxCheckout;
typedef TPacketCGSafeboxCheckin TPacketGCSafeboxCheckin;

typedef struct packet_safebox_wrong_password
{
    BYTE        bHeader;
} TPacketGCSafeboxWrongPassword;

typedef struct packet_safebox_size
{
	BYTE bHeader;
	BYTE bSize;
} TPacketGCSafeboxSize;

typedef struct packet_safebox_money_change
{
    BYTE bHeader;
    DWORD dwMoney;
} TPacketGCSafeboxMoneyChange;

typedef struct command_empire
{
    BYTE        bHeader;
    BYTE        bEmpire;
} TPacketCGEmpire;

typedef struct packet_empire
{
    BYTE        bHeader;
    BYTE        bEmpire;
} TPacketGCEmpire;

enum
{
	FISHING_SUBHEADER_GC_START,
	FISHING_SUBHEADER_GC_STOP,
	FISHING_SUBHEADER_GC_REACT,
	FISHING_SUBHEADER_GC_SUCCESS,
	FISHING_SUBHEADER_GC_FAIL,
    FISHING_SUBHEADER_GC_FISH,
};

typedef struct packet_fishing
{
    BYTE header;
    BYTE subheader;
    DWORD info;
    BYTE dir;
} TPacketGCFishing;

enum
{
	FISHING_GAME_SUBHEADER_GC_GAME_UPDATE,
	FISHING_GAME_SUBHEADER_GC_PLAYER_UPDATE,
};

typedef struct packet_fishing_game
{
	BYTE header;
	WORD size;
	BYTE subheader;
} TPacketGCFishingGame;

typedef struct packet_fishing_game_update
{
	BYTE        top_bar_pos;
} TPacketGCFishingGameUpdate;

typedef struct packet_fishing_game_player_update
{
	BYTE        player_pos;
} TPacketGCFishingGamePlayerUpdate;


typedef struct paryt_parameter
{
    BYTE        bHeader;
    BYTE        bDistributeMode;
} TPacketGCPartyParameter;

//////////////////////////////////////////////////////////////////////////
// Guild

enum
{
    GUILD_SUBHEADER_GC_LOGIN,
	GUILD_SUBHEADER_GC_LOGOUT,
	GUILD_SUBHEADER_GC_LIST,
	GUILD_SUBHEADER_GC_GRADE,
	GUILD_SUBHEADER_GC_ADD,
	GUILD_SUBHEADER_GC_REMOVE,
	GUILD_SUBHEADER_GC_GRADE_NAME,
	GUILD_SUBHEADER_GC_GRADE_AUTH,
	GUILD_SUBHEADER_GC_INFO,
	GUILD_SUBHEADER_GC_COMMENTS,
    GUILD_SUBHEADER_GC_CHANGE_EXP,
    GUILD_SUBHEADER_GC_CHANGE_MEMBER_GRADE,
	GUILD_SUBHEADER_GC_SKILL_INFO,
	GUILD_SUBHEADER_GC_CHANGE_MEMBER_GENERAL,
	GUILD_SUBHEADER_GC_GUILD_INVITE,
    GUILD_SUBHEADER_GC_WAR,
    GUILD_SUBHEADER_GC_GUILD_NAME,
    GUILD_SUBHEADER_GC_GUILD_WAR_LIST,
    GUILD_SUBHEADER_GC_GUILD_WAR_END_LIST,
    GUILD_SUBHEADER_GC_WAR_POINT,
	GUILD_SUBHEADER_GC_MONEY_CHANGE,
};

typedef struct packet_guild
{
    BYTE header;
    WORD size;
    BYTE subheader;
} TPacketGCGuild;

// SubHeader - Grade
enum
{
    GUILD_AUTH_ADD_MEMBER       = (1 << 0),
    GUILD_AUTH_REMOVE_MEMBER    = (1 << 1),
    GUILD_AUTH_NOTICE           = (1 << 2),
    GUILD_AUTH_SKILL            = (1 << 3),
};

typedef struct packet_guild_sub_grade
{
	char grade_name[GUILD_GRADE_NAME_MAX_LEN+1];
	BYTE auth_flag;
} TPacketGCGuildSubGrade;

typedef struct packet_guild_sub_member
{
	DWORD pid;
	BYTE byGrade;
	BYTE byIsGeneral;
	BYTE byJob;
	BYTE byLevel;
	DWORD dwOffer;
	BYTE byNameFlag;
// if NameFlag is TRUE, name is sent from server.
//	char szName[CHARACTER_ME_MAX_LEN+1];
} TPacketGCGuildSubMember;

typedef struct packet_guild_sub_info
{
    WORD member_count;
    WORD max_member_count;
	DWORD guild_id;
    DWORD master_pid;
    DWORD exp;
    BYTE level;
    char name[GUILD_NAME_MAX_LEN+1];
	YANG gold;
	BYTE hasLand;
} TPacketGCGuildInfo;

typedef struct packet_guild_war
{
    DWORD       dwGuildSelf;
    DWORD       dwGuildOpp;
    BYTE        bType;
    BYTE        bWarState;
} TPacketGCGuildWar;

typedef struct SPacketGuildWarPoint
{
    DWORD dwGainGuildID;
    DWORD dwOpponentGuildID;
    long lPoint;
} TPacketGuildWarPoint;

// SubHeader - Dungeon
enum
{
	DUNGEON_SUBHEADER_GC_TIME_ATTACK_START = 0,
	DUNGEON_SUBHEADER_GC_DESTINATION_POSITION = 1,
};

typedef struct packet_dungeon
{
	BYTE		bHeader;
    WORD		size;
    BYTE		subheader;
} TPacketGCDungeon;

// Private Shop
typedef struct SPacketGCShopSign
{
    BYTE        bHeader;
    DWORD       dwVID;
    char        szSign[SHOP_SIGN_MAX_LEN + 1];
} TPacketGCShopSign;

typedef struct SPacketGCTime
{
    BYTE        bHeader;
    time_t      time;
} TPacketGCTime;

enum
{
    WALKMODE_RUN,
    WALKMODE_WALK,
};

typedef struct SPacketGCWalkMode
{
    BYTE        header;
    DWORD       vid;
    BYTE        mode;
} TPacketGCWalkMode;

typedef struct SPacketGCChangeSkillGroup
{
    BYTE        header;
    BYTE        skill_group;
} TPacketGCChangeSkillGroup;

struct TMaterial
{
    DWORD vnum;
	ITEM_COUNT count;
};

typedef struct SRefineTable
{
    DWORD src_vnum;
    DWORD result_vnum;
    BYTE material_count;
    int cost;
    int prob;
    TMaterial materials[REFINE_MATERIAL_MAX_NUM];
} TRefineTable;

typedef struct SPacketGCRefineInformation
{
	BYTE			header;
	BYTE			pos;
	TRefineTable	refine_table;
} TPacketGCRefineInformation;

typedef struct SPacketGCRefineInformationNew
{
	BYTE			header;
	BYTE			type;
	BYTE			pos;
	TRefineTable	refine_table;
} TPacketGCRefineInformationNew;

typedef struct SPacketGCSpecialEffect
{
    BYTE header;
    BYTE type;
    DWORD vid;
} TPacketGCSpecialEffect;

#ifdef ENABLE_12ZI
// MT2009_PLUS_ZODIAC_V1: 1+1+1+4+4+4 = 15 B, as the server sends it
typedef struct SPacketGCSpecialZodiacEffect
{
	BYTE header;
	BYTE type;
	BYTE type2;
	DWORD vid;
	long x;
	long y;
} TPacketGCSpecialZodiacEffect;
#endif

typedef struct SPacketGCNPCPosition
{
    BYTE header;
	WORD size;
    WORD count;
} TPacketGCNPCPosition;

struct TNPCPosition
{
    BYTE bType;
    char name[CHARACTER_NAME_MAX_LEN+1];
    long x;
    long y;
};

struct TPacketGCDeleteCharacterError
{
	BYTE header;
	BYTE type;
};

typedef struct SPacketGCChangeName
{
    BYTE header;
    DWORD pid;
    char name[CHARACTER_NAME_MAX_LEN+1];
} TPacketGCChangeName;

enum EBlockAction
{
    BLOCK_EXCHANGE              = (1 << 0),
    BLOCK_PARTY_INVITE          = (1 << 1),
    BLOCK_GUILD_INVITE          = (1 << 2),
    BLOCK_WHISPER               = (1 << 3),
    BLOCK_MESSENGER_INVITE      = (1 << 4),
    BLOCK_PARTY_REQUEST         = (1 << 5),
};

typedef struct packet_login_key
{
	BYTE	bHeader;
	DWORD	dwLoginKey;
} TPacketGCLoginKey;

typedef struct packet_auth_success
{
    BYTE        bHeader;
    DWORD       dwLoginKey;
    BYTE        bResult;
} TPacketGCAuthSuccess;

typedef struct packet_channel
{
    BYTE header;
    BYTE channel;
} TPacketGCChannel;

#ifdef ENABLE_GUILD_TOKEN_AUTH
struct TPacketGCGuildToken {
	uint8_t header;
	uint64_t token;
};
#endif

typedef struct SEquipmentItemSet
{
	DWORD		vnum;
	ITEM_COUNT  count;
	long		alSockets[ITEM_SOCKET_SLOT_MAX_NUM];
	TPlayerItemAttribute aAttr[ITEM_ATTRIBUTE_SLOT_MAX_NUM];
} TEquipmentItemSet;

typedef struct pakcet_view_equip
{
    BYTE header;
	DWORD dwVID;
	TEquipmentItemSet equips[WEAR_MAX_NUM];
} TPacketGCViewEquip;

typedef struct SLandPacketElement
{
    DWORD       dwID;
    long        x, y;
    long        width, height;
    DWORD       dwGuildID;
} TLandPacketElement;

typedef struct packet_land_list
{
    BYTE        header;
    WORD        size;
} TPacketGCLandList;

typedef struct SPacketGCTargetCreate
{
    BYTE        bHeader;
    long        lID;
    char        szTargetName[32+1];
} TPacketGCTargetCreate;

enum
{
	CREATE_TARGET_TYPE_NONE,
	CREATE_TARGET_TYPE_LOCATION,
	CREATE_TARGET_TYPE_CHARACTER,
};

typedef struct SPacketGCTargetCreateNew
{
	BYTE		bHeader;
	long		lID;
	char		szTargetName[32+1];
	DWORD		dwVID;
	BYTE		byType;
} TPacketGCTargetCreateNew;

typedef struct SPacketGCTargetUpdate
{
    BYTE        bHeader;
    long        lID;
    long        lX, lY;
} TPacketGCTargetUpdate;

typedef struct SPacketGCTargetDelete
{
    BYTE        bHeader;
    long        lID;
} TPacketGCTargetDelete;

typedef struct SPacketAffectElement
{
    DWORD       dwType;
    WORD        bPointIdxApplyOn;	// MT2009_PLUS_WIDE_ATTR_V1 (affect element): the server's TPacketAffectElement::bApplyOn
    long        lApplyValue;
    DWORD       dwFlag;
    long        lDuration;
    long        lSPCost;
	DWORD		itemVnum;
} TPacketAffectElement;

typedef struct SPacketGCAffectAdd
{
    BYTE bHeader;
    TPacketAffectElement elem;
} TPacketGCAffectAdd;

typedef struct SPacketGCAffectRemove
{
    BYTE bHeader;
    DWORD dwType;
    WORD bApplyOn;	// MT2009_PLUS_WIDE_ATTR_V1 (affect remove)
} TPacketGCAffectRemove;

typedef struct packet_mall_open
{
	BYTE bHeader;
	BYTE bSize;
} TPacketGCMallOpen;

typedef struct packet_lover_info
{
	BYTE bHeader;
	char szName[CHARACTER_NAME_MAX_LEN + 1];
	BYTE byLovePoint;
} TPacketGCLoverInfo;

typedef struct packet_love_point_update
{
	BYTE bHeader;
	BYTE byLovePoint;
} TPacketGCLovePointUpdate;

typedef struct packet_dig_motion
{
    BYTE header;
    DWORD vid;
    DWORD target_vid;
	BYTE count;
} TPacketGCDigMotion;

typedef struct SPacketGCOnTime
{
    BYTE header;
    int ontime;     // sec
} TPacketGCOnTime;

typedef struct SPacketGCResetOnTime
{
    BYTE header;
} TPacketGCResetOnTime;

typedef struct SPacketGCPanamaPack
{
    BYTE    bHeader;
    char    szPackName[256];
    BYTE    abIV[32];
} TPacketGCPanamaPack;

typedef struct SPacketGCHybridCryptKeys
{
private:
	SPacketGCHybridCryptKeys() : m_pStream(NULL) {}

public:
	SPacketGCHybridCryptKeys(int iStreamSize) : iKeyStreamLen(iStreamSize)
	{
		m_pStream = new BYTE[iStreamSize];
	}
	~SPacketGCHybridCryptKeys()
	{
		if( m_pStream )
		{
			delete[] m_pStream;
			m_pStream = NULL;
		}
	}
	static int GetFixedHeaderSize()
	{
		return sizeof(BYTE)+sizeof(WORD)+sizeof(int);
	}

	BYTE	bHeader;
	WORD    wDynamicPacketSize;
	int		iKeyStreamLen;
	BYTE*	m_pStream;
} TPacketGCHybridCryptKeys;

typedef struct SPacketGCHybridSDB
{
private:
	SPacketGCHybridSDB() : m_pStream(NULL) {}

public:
	SPacketGCHybridSDB(int iStreamSize) : iSDBStreamLen(iStreamSize)
	{
		m_pStream = new BYTE[iStreamSize];
	}
	~SPacketGCHybridSDB()
	{
		delete[] m_pStream;
		m_pStream = NULL;
	}
	static int GetFixedHeaderSize()
	{
		return sizeof(BYTE)+sizeof(WORD)+sizeof(int);
	}

	BYTE	bHeader;
	WORD    wDynamicPacketSize;
	int		iSDBStreamLen;
	BYTE*	m_pStream;
} TPacketGCHybridSDB;
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Client To Client

typedef struct packet_state
{
	BYTE			bHeader;
	BYTE			bFunc;
	BYTE			bArg;
	BYTE			bRot;
	DWORD			dwVID;
	DWORD			dwTime;
	TPixelPosition	kPPos;
} TPacketCCState;

// AUTOBAN
typedef struct packet_autoban_quiz
{
    BYTE bHeader;
	BYTE bDuration;
    BYTE bCaptcha[64*32];
    char szQuiz[256];
} TPacketGCAutoBanQuiz;
// END_OF_AUTOBAN

#ifdef _IMPROVED_PACKET_ENCRYPTION_
struct TPacketKeyAgreement
{
	static const int MAX_DATA_LEN = 256;
	BYTE bHeader;
	WORD wAgreedLength;
	WORD wDataLength;
	BYTE data[MAX_DATA_LEN];
};

struct TPacketKeyAgreementCompleted
{
	BYTE bHeader;
	BYTE data[3]; // dummy (not used)
};
#endif // _IMPROVED_PACKET_ENCRYPTION_

typedef struct SPacketGCSpecificEffect
{
	BYTE header;
	DWORD vid;
	char effect_file[128];
} TPacketGCSpecificEffect;

enum EDragonSoulRefineWindowRefineType
{
	DragonSoulRefineWindow_UPGRADE,
	DragonSoulRefineWindow_IMPROVEMENT,
	DragonSoulRefineWindow_REFINE,
};

enum EPacketCGDragonSoulSubHeaderType
{
	DS_SUB_HEADER_OPEN,
	DS_SUB_HEADER_CLOSE,
	DS_SUB_HEADER_DO_UPGRADE,
	DS_SUB_HEADER_DO_IMPROVEMENT,
	DS_SUB_HEADER_DO_REFINE,
	DS_SUB_HEADER_REFINE_FAIL,
	DS_SUB_HEADER_REFINE_FAIL_MAX_REFINE,
	DS_SUB_HEADER_REFINE_FAIL_INVALID_MATERIAL,
	DS_SUB_HEADER_REFINE_FAIL_NOT_ENOUGH_MONEY,
	DS_SUB_HEADER_REFINE_FAIL_NOT_ENOUGH_MATERIAL,
	DS_SUB_HEADER_REFINE_FAIL_TOO_MUCH_MATERIAL,
	DS_SUB_HEADER_REFINE_SUCCEED,
	DS_SUB_HEADER_OPEN_CHANGE_ATTR,
	DS_SUB_HEADER_DO_CHANGE_ATTR,
};

typedef struct SPacketCGDragonSoulRefine
{
	SPacketCGDragonSoulRefine() : header (HEADER_CG_DRAGON_SOUL_REFINE)
	{}
	BYTE header;
	BYTE bSubType;
	TItemPos ItemGrid[DS_REFINE_WINDOW_MAX_NUM];
} TPacketCGDragonSoulRefine;

typedef struct SPacketGCDragonSoulRefine
{
	SPacketGCDragonSoulRefine() : header(HEADER_GC_DRAGON_SOUL_REFINE)
	{}
	BYTE header;
	BYTE bSubType;
	TItemPos Pos;
} TPacketGCDragonSoulRefine;

typedef struct SChannelStatus
{
	WORD nPort; // @fixme024 (max port limit 32767 to 65535)
	BYTE bStatus;
} TChannelStatus;

typedef struct SPacketGCSpecialFlag
{
	BYTE header;
	char cFlag[SPECIAL_FLAG_MAX_LEN + 1];
	long long llValue;
} TPacketGCSpecialFlag;

typedef struct command_check_version
{
	BYTE	header;
	DWORD	dwVersion;
} TPacketCGCheckVersion;

typedef struct packet_version_verified
{
	BYTE	header;
} TPacketGCVersionVerified;

#ifdef ENABLE_ACCE_COSTUME_SYSTEM

enum
{
	HEADER_CG_ACCE = 211,
	HEADER_GC_ACCE = 215,
	ACCE_SUBHEADER_GC_OPEN = 0,
	ACCE_SUBHEADER_GC_CLOSE,
	ACCE_SUBHEADER_GC_ADDED,
	ACCE_SUBHEADER_GC_REMOVED,
	ACCE_SUBHEADER_CG_REFINED,
	ACCE_SUBHEADER_CG_CLOSE = 0,
	ACCE_SUBHEADER_CG_ADD,
	ACCE_SUBHEADER_CG_REMOVE,
	ACCE_SUBHEADER_CG_REFINE,
};

typedef struct SPacketAcce
{
	BYTE	header;
	BYTE	subheader;
	bool	bWindow;
	YANG	dwPrice;
	BYTE	bPos;
	TItemPos	tPos;
	DWORD	dwItemVnum;
	DWORD	dwMinAbs;
	DWORD	dwMaxAbs;
} TPacketAcce;

typedef struct SAcceMaterial
{
	BYTE	bHere;
	WORD	wCell;
} TAcceMaterial;

typedef struct SAcceResult
{
	DWORD	dwItemVnum;
	DWORD	dwMinAbs;
	DWORD	dwMaxAbs;
} TAcceResult;
#endif
#ifdef ENABLE_IKASHOP_RENEWAL
//ACTIONS PACKETS
typedef struct
{
	BYTE header;
#ifdef ENABLE_LARGE_DYNAMIC_PACKETS
	int size;
#else
	WORD size;
#endif
	BYTE subheader;
} TPacketGCNewOfflineshop;

typedef struct {
	BYTE header;
	WORD size;
	BYTE subheader;
} TPacketCGNewOfflineShop;

namespace ikashop
{
	typedef struct SPlayerItem
	{
		DWORD id;
		BYTE window;
		WORD pos;
		DWORD count;
		DWORD vnum;
		long alSockets[ITEM_SOCKET_SLOT_MAX_NUM];
		TPlayerItemAttribute aAttr[ITEM_ATTRIBUTE_SLOT_MAX_NUM];
		DWORD owner;
#ifdef ENABLE_CHANGELOOK_SYSTEM
		DWORD dwTransmutation; // MT2009_PLUS_CHANGE_LOOK_V1: the server's TPlayerItem (common/tables.h) ends with the look
#endif
	} TPlayerItem;

	//patch 08-03-2020
	enum class ExpirationType
	{
		EXPIRE_NONE,
		EXPIRE_REAL_TIME,
		EXPIRE_REAL_TIME_FIRST_USE,
	};

	struct TPriceInfo
	{
		long long yang = 0;
#ifdef ENABLE_CHEQUE_SYSTEM
		int cheque = 0;
#endif
		long long GetTotalYangAmount() const {
			return yang
#ifdef ENABLE_CHEQUE_SYSTEM
				+ static_cast<long long>(cheque) * YANG_PER_CHEQUE
#endif
				;
		}
	};

	struct TShopPlayerItem : public TPlayerItem
	{
		ExpirationType expiration;
	};

	struct TShopItem : public TShopPlayerItem
	{
		TPriceInfo price;
	};

	struct TOfferInfo
	{
		DWORD offerid;
		DWORD ownerid;
		DWORD itemid;
		DWORD buyerid;
		TPriceInfo price;
		bool notified;
		bool accepted;
		char buyername[CHARACTER_NAME_MAX_LEN + 1];
		int64_t datetime;
	};

#ifdef ENABLE_IKASHOP_ENTITIES
	struct TShopSpawn
	{
		int x;
		int y;
		int map;
		BYTE channel;
	};
#endif

	//AUCTION
	struct TAuctionInfo : public TShopItem
	{
		char  ownername[CHARACTER_NAME_MAX_LEN + 1];
		DWORD duration;
	};


	struct TAuctionOfferInfo
	{
		TPriceInfo	price;
		DWORD ownerid;
		DWORD buyerid;
		char buyername[CHARACTER_NAME_MAX_LEN + 1];
		bool seenflag;
		int64_t datetime;
	};

	struct TValutesInfo
	{
		long long yang = 0;

		void operator +=(const TValutesInfo& r)
		{
			yang += r.yang;
		}

		void operator -=(const TValutesInfo& r)
		{
			yang -= r.yang;
		}
	};


	struct TShopInfo
	{
		DWORD ownerid;
		DWORD duration;
		char name[OFFLINE_SHOP_NAME_MAX_LEN + 1];
		char ownerName[PLAYER_NAME_MAX_LEN + 1];
		DWORD count;
#ifdef ENABLE_IKASHOP_ENTITIES
		TShopSpawn spawn;
#endif
		BYTE unlockCount;
		bool isPremium;
	};

	struct TFilterInfo
	{
		BYTE type;
		BYTE subtype;
		char name[ITEM_NAME_MAX_LEN];
		TPriceInfo pricestart;
		TPriceInfo pricend;
		int levelstart;
		int levelend;
		TPlayerItemAttribute attrs[ITEM_ATTRIBUTE_SLOT_NORM_NUM];
		int sashGrade;
		int alchemyGrade;
	};

	struct TShopItemInfo
	{
		TItemPos pos;
		int destpos;
		TPriceInfo price;
	};


	struct TSearchResultInfo : public ikashop::TShopItem
	{
		bool auction;
		char seller_name[OFFLINE_SHOP_NAME_MAX_LEN + 1];
		int duration;
	};

	//AUCTION
	struct TAuctionListElement
	{
		TAuctionInfo auction;
		TPriceInfo actual_best;
		DWORD offercount;
	};

	struct TOfferListElement : public TOfferInfo
	{
		TShopItem item;
		char shopname[OFFLINE_SHOP_NAME_MAX_LEN + 1];
		bool incoming;
	};


#ifdef EXTEND_IKASHOP_PRO
	enum class ENotificationType : uint8_t
	{
		SELLER_SOLD_ITEM,
		SELLER_NEW_OFFER_ON_ITEM,
		SELLER_SHOP_EXPIRED,
		SELLER_ITEM_EXPIRED,
		SELLER_AUCTION_NEW_OFFER,
		SELLER_AUCTION_EXPIRED,
		SELLER_AUCTION_SOLD,
		SELLER_OFFER_CANCELLED,
		BUYER_OFFER_DENIED,
		BUYER_OFFER_ACCEPTED,
		BUYER_OFFER_EXPIRED,
		BUYER_AUCTION_BUY,
		BUYER_AUCTION_RAISE,
		BUYER_AUCTION_LOST,
	};

	struct TNotificationInfo
	{
		DWORD id;
		ENotificationType type;
		DWORD what;
		char who[OFFLINE_SHOP_NAME_MAX_LEN + 1];
		char format[OFFLINESHOP_NOTIFICATION_FORMAT_LEN];
		int64_t datetime;
		bool seenflag;
	};
#endif


	//GAME TO CLIENT
	enum eSubHeaderGC
	{
		SUBHEADER_GC_SHOP_OPEN,
		SUBHEADER_GC_SHOP_OPEN_OWNER,
		SUBHEADER_GC_SHOP_OPEN_OWNER_NO_SHOP,
		SUBHEADER_GC_SHOP_EXPIRED_GUESTING,
		SUBHEADER_GC_SHOP_REMOVE_ITEM_OWNER,
		SUBHEADER_GC_SHOP_REMOVE_ITEM_GUEST,
		SUBHEADER_GC_SHOP_EDIT_ITEM_OWNER,
		SUBHEADER_GC_SHOP_EDIT_ITEM_GUEST,
		SUBHEADER_GC_SHOP_POSITION,

		SUBHEADER_GC_OFFER_LIST,

		SUBHEADER_GC_SHOP_FILTER_RESULT,
		SUBHEADER_GC_SHOP_SAFEBOX_REFRESH,
		SUBHEADER_GC_SHOP_SAFEBOX_REMOVE_ITEM,
		SUBHEADER_GC_SHOP_SAFEBOX_ADD_ITEM,

		//AUCTION
		SUBHEADER_GC_AUCTION_LIST,
		SUBHEADER_GC_OPEN_MY_AUCTION,
		SUBHEADER_GC_OPEN_MY_AUCTION_NO_AUCTION,
		SUBHEADER_GC_OPEN_AUCTION,

		SUBHEDAER_GC_POPUP_MESSAGE,

#ifdef ENABLE_IKASHOP_ENTITIES
		SUBHEADER_GC_INSERT_SHOP_ENTITY,
		SUBHEADER_GC_REMOVE_SHOP_ENTITY,
#endif
		SUBHEADER_GC_BOARD_COUNTERS,
#ifdef EXTEND_IKASHOP_PRO
		SUBHEADER_GC_NOTIFICATION_LIST,
#endif

		SUBHEADER_GC_SEARCH_RESULT_DELETE,
		SUBHEADER_GC_NOTIFY_ITEM_SOLD,
		SUBHEADER_GC_SHOP_SEARCH,
	};

	struct TSubPacketGCShopOpen
	{
		DWORD vid;
		bool	isOwnerOnline;
		TShopInfo shop;
	};

	struct TSubPacketGCShopOpenOwner
	{
		int tax;
		TShopInfo shop;
	};

	struct TSubPacketGCShopExpiredGuesting
	{
		DWORD ownerid;
	};

	struct TSubPacketGCShopRemoveItem
	{
		DWORD itemid;
	};

	struct TSubPacketGCShopEditItem
	{
		DWORD itemid;
		TPriceInfo price;
	};

	struct TSubPacketGCShopPosition
	{
		DWORD vid;
		long x;
		long y;
	};

	struct TSubPacketGCShopFilterResult
	{
		DWORD count;
	};

	struct TSubPacketGCShopOfferList
	{
		DWORD offercount;
	};

	struct TSubPacketGCShopSafeboxRefresh
	{
		TValutesInfo valute;
		DWORD itemcount;
	};

	struct TSubPacketGCShopSafeboxRemoveItem
	{
		DWORD itemid;
	};

	struct TSubPacketGCShoppingSafeboxAddItem
	{
		TShopPlayerItem item;
	};

	//AUCTION
	struct TSubPacketGCAuctionList
	{
		DWORD count;
	};

	struct TSubPacketGCAuctionOpen
	{
		TAuctionInfo auction;
		DWORD offercount;
	};

	struct TSubPacketGCPopupMessage
	{
		static constexpr inline auto MESSAGE_LEN = 80;
		char localeString[MESSAGE_LEN];
	};

#ifdef ENABLE_IKASHOP_ENTITIES
	struct TSubPacketGCInsertShopEntity
	{
		DWORD vid;
		char name[OFFLINE_SHOP_NAME_MAX_LEN + 1];
		char ownerName[PLAYER_NAME_MAX_LEN + 1];
		int type;
		int x, y, z;
	};

	struct TSubPacketGCRemoveShopEntity
	{
		DWORD vid;
	};
#endif

	struct TSubPacketGCBoardCounters
	{
		int safebox;
		int offers;
		int auction;
#ifdef EXTEND_IKASHOP_PRO
		int notification;
#endif
	};

#ifdef EXTEND_IKASHOP_PRO
	struct TSubPacketGCNotificationList
	{
		DWORD count;
	};
#endif

	// CLIENT TO GAME
	enum eSubHeaderCG
	{
		SUBHEADER_CG_SHOP_REOPEN,
		SUBHEADER_CG_SHOP_FORCE_CLOSE,
		SUBHEADER_CG_SHOP_REQUEST_SHOPLIST,
		SUBHEADER_CG_SHOP_OPEN,
		SUBHEADER_CG_SHOP_OPEN_OWNER,
		SUBHEADER_CG_SHOP_BUY_ITEM,
		SUBHEADER_CG_SHOP_CHANGE_NAME,

		SUBHEADER_CG_SHOP_ADD_ITEM,
		SUBHEADER_CG_SHOP_REMOVE_ITEM,
		SUBHEADER_CG_SHOP_REMOVE_ALL_ITEM,
		SUBHEADER_CG_SHOP_EDIT_ITEM,

		SUBHEADER_CG_SHOP_FILTER_REQUEST,
		SUBHEADER_CG_SHOP_SEARCH_FILL_REQUEST,

		SUBHEADER_CG_SHOP_OFFER_CREATE,
		SUBHEADER_CG_SHOP_OFFER_ACCEPT,
		SUBHEADER_CG_SHOP_OFFER_CANCEL,
		SUBHEADER_CG_SHOP_REQUEST_OFFER_LIST,

		SUBHEADER_CG_SHOP_SAFEBOX_OPEN,
		SUBHEADER_CG_SHOP_SAFEBOX_GET_ITEM,
		SUBHEADER_CG_SHOP_SAFEBOX_GET_VALUTES,
		SUBHEADER_CG_SHOP_SAFEBOX_CLOSE,

		//AUCTION
		SUBHEADER_CG_AUCTION_LIST_REQUEST,
		SUBHEADER_CG_AUCTION_OPEN_REQUEST,
		SUBHEADER_CG_MY_AUCTION_OPEN_REQUEST,
		SUBHEADER_CG_MY_AUCTION_CLOSE,
		SUBHEADER_CG_MY_AUCTION_CANCEL,
		SUBHEADER_CG_CREATE_AUCTION,
		SUBHEADER_CG_AUCTION_ADD_OFFER,
		SUBHEADER_CG_EXIT_FROM_AUCTION,

		SUBHEADER_CG_CLOSE_MY_SHOP_BOARD,
		SUBHEADER_CG_CLOSE_OFFER_LIST,
		SUBHEADER_CG_CLOSE_SHOP_GUEST,
#ifdef ENABLE_IKASHOP_ENTITIES
		SUBHEADER_CG_CLICK_ENTITY,
		SUBHEADER_CG_FIND_MY_SHOP,
#ifdef EXTEND_IKASHOP_PRO
		SUBHEADER_CG_MOVE_SHOP_ENTITY,
#endif
#endif

#ifdef EXTEND_IKASHOP_PRO
		SUBHEADER_CG_NOTIFICATION_LIST_REQUEST,
		SUBHEADER_CG_NOTIFICATION_LIST_CLOSE,
		SUBHEADER_CG_SHOP_SEARCH,
		SUBHEADER_CG_REQUEST_EDIT,
#endif
	};

	struct TSubPacketCGShopReopen
	{
		char name[OFFLINE_SHOP_NAME_MAX_LEN + 1];
		BYTE bTimeIndex;
	};

	struct TSubPacketCGShopOpen
	{
		DWORD ownerid;
	};

	struct TSubPacketCGAddItem
	{
		TItemPos pos;
		TPriceInfo price;
		int destpos;
	};

	struct TSubPacketCGRemoveItem
	{
		DWORD itemid;
	};

	struct TSubPacketCGEditItem
	{
		DWORD itemid;
		TPriceInfo price;
	};

	struct TSubPacketCGFilterRequest
	{
		TFilterInfo filter;
	};

	struct TSubPacketCGOfferCreate
	{
		TOfferInfo offer;
	};

	struct TSubPacketCGOfferAccept
	{
		DWORD offerid;
	};

	struct TSubPacketCGOfferCancel
	{
		DWORD offerid;
		DWORD ownerid;
	};

	struct TSubPacketCGShopSafeboxGetItem
	{
		DWORD itemid;
	};

	struct TSubPacketCGShopBuyItem
	{
		DWORD ownerid;
		DWORD itemid;
		bool searching;
		long long seenprice;
	};

	struct TSubPacketCGChangeName
	{
		char name[OFFLINE_SHOP_NAME_MAX_LEN + 1];
	};

	struct TSubPacketCGShopSearchItem
	{
		DWORD itemVnum;
		int socket0;
	};

	struct TSubPacketCGShopRequestEdit
	{
		bool bIsEdit;
	};

	//AUCTION
	struct TSubPacketCGAuctionOpenRequest
	{
		DWORD ownerid;
	};

	struct TSubPacketCGAuctionCreate
	{
		TItemPos pos;
		TPriceInfo startprice;
	};

	struct TSubPacketCGAuctionAddOffer
	{
		DWORD ownerid;
		TPriceInfo price;
	};

	struct TSubPacketCGAuctionExitFrom
	{
		DWORD ownerid;
	};

#ifdef ENABLE_IKASHOP_ENTITIES
	struct TSubPacketCGShopClickEntity
	{
		DWORD vid;
	};
#endif

	struct TSubPacketGCShopNotifyItemSold
	{
		DWORD itemVnum;
		ITEM_COUNT count;
		YANG price;
	};

	struct TSubPacketGCShopSearchItem
	{
		DWORD itemCount;
	};

	struct TSubPacketGCShopSearchItemShop
	{
		DWORD shopVid;
		long x;
		long y;
	};

}

#endif

typedef struct SRefineMaterial
{
	DWORD vnum;
	ITEM_COUNT count;
} TRefineMaterial;

typedef struct SSpecialShopLimit
{
	BYTE type;
	int value;
} TSpecialShopLimit;

typedef struct SSpecialShopItemClient
{
	DWORD vnum;
	DWORD itemVnum;
	ITEM_COUNT count;
	int rarePct;
	BYTE priceType;
	int price;
	TRefineMaterial items[SPECIAL_SHOP_MAX_ITEM_COUNT];
	TSpecialShopLimit limits[SPECIAL_SHOP_MAX_LIMIT];
} TSpecialShopItemClient;

// special shop
enum {
	SUBHEADER_GC_SPECIAL_SHOP_OPEN,
	SUBHEADER_GC_SPECIAL_SHOP_BUY,
};

typedef struct SPacketCGSpecialShop
{
	BYTE header;
	int size;
	BYTE subheader;
} TPacketGCSpecialShop;

struct TSubPacketCGSpecialShopOpen
{
	BYTE count;
	BYTE fraction;
};

struct TSubPacketCGSpecialShopBuy
{
	DWORD vnum;
};
// end special shop


// npc info board

enum {
	SUBHEADER_GC_NPC_INFO_REPUTATION,
};

struct TPacketCGNpcInfoBoard
{
	BYTE header;
	int size;
	BYTE subheader;
	DWORD vid;
};

struct TSubPacketCGNpcInfoReputation
{
	BYTE fraction;
};

// end npc info board

// request info
struct TPacketGCRequestInfo
{
	BYTE header;
	BYTE type;
};

struct TPacketCGRequestInfoResponse
{
	BYTE header;
	BYTE type;
	char arg1[255+1];
	char arg2[255+1];
};
//end of request info

// CAPTCHA
// SERVER -> CLIENT
enum {
	SUBHEADER_GC_CAPTCHA_START,
	SUBHEADER_GC_CAPTCHA_STOP,
	SUBHEADER_GC_CAPTCHA_CHANGE,
	SUBHEADER_GC_CAPTCHA_ATTEMPT,
	SUBHEADER_GC_CAPTCHA_GM_START,
	SUBHEADER_GC_CAPTCHA_GM_REQUEST_CHANGE,
	SUBHEADER_GC_CAPTCHA_GM_FEEDBACK,
};

struct TPacketGCCaptcha
{
	BYTE header;
	int size;
	BYTE subheader;
};

struct TSubPacketGCCaptchaImage
{
	DWORD imageSize;
};

struct TSubPacketGCCaptchaMeta
{
	DWORD captchaExpireTime;
	BYTE attemptCount;
};

struct TSubPacketGCCaptchaGMWho
{
	DWORD pid;
	char name[PLAYER_NAME_MAX_LEN + 1];
};

struct TSubPacketGCCaptchaGMCode
{
	char code[CAPTCHA_MAX_LEN + 1];
};

struct TSubPacketGCCaptchaGMFeedback
{
	BYTE type;
	char arg1[CAPTCHA_MAX_LEN + 1];
	int arg2;
};
// end of CAPTCHA

// GAMEMASTER TARGET
struct TPacketGCGamemasterTarget
{
	BYTE header;
	DWORD pid;
	char playerName[PLAYER_NAME_MAX_LEN + 1];
	DWORD aid;
	char accountName[CHARACTER_NAME_MAX_LEN + 1];
	bool isPremium;
};
// END OF GAMEMASTER TARGET

#ifdef ENABLE_INGAME_EVENT_MANAGER
// MT2009_PLUS_EVENT_MANAGER_V1: the in-game event list, the server's packet.h to the byte.
// An event is a key ("catchking", "rumi", "easter" ...): the exe only keeps
// the list; names, icons and windows are python's (uiingameevent.py).
enum
{
	INGAME_EVENT_KEY_MAX_LEN = 24,
	INGAME_EVENT_SUBHEADER_GC_LIST = 0,	// the whole list, in place of what the client had
	INGAME_EVENT_SUBHEADER_GC_UPDATE = 1,	// these events changed, the rest stays
};

typedef struct SPacketGCInGameEvent
{
	BYTE	header;
	WORD	size;		// dynamic: this and count x TPacketGCInGameEventInfo
	BYTE	subheader;
	BYTE	count;
} TPacketGCInGameEvent;

typedef struct SPacketGCInGameEventInfo
{
	char	key[INGAME_EVENT_KEY_MAX_LEN + 1];
	BYTE	enable;
	DWORD	start_time;
	DWORD	end_time;
	DWORD	reward_end_time;
	int		value;
} TPacketGCInGameEventInfo;
#endif

/////////////////////////////////////////////////////////////////////////////////////////////////////
// MT2009_PLUS_MINIGAMES_V1: Owsap v6.2.6 mini game packets (layouts identical to Owsap's server
// packet.h, pack(1); BOOL = 4 bytes). See client-patches/exe/MINIGAMES.md.
#ifdef ENABLE_MINI_GAME_CATCH_KING
enum EMiniGameCatchKingCGSubHeader
{
	CATCHKING_CG_START,
	CATCHKING_CG_CLICK_HAND,
	CATCHKING_CG_CLICK_CARD,
	CATCHKING_CG_REWARD,
#ifdef ENABLE_CATCH_KING_EVENT_FLAG_RENEWAL
	CATCHKING_CG_REQUEST_QUEST_FLAG,
#endif
};

enum EMiniGameCatchKingGCSubHeader
{
	CATCHKING_GC_START,
	CATCHKING_GC_SET_CARD,
	CATCHKING_GC_RESULT_FIELD,
	CATCHKING_GC_SET_END_CARD,
	CATCHKING_GC_REWARD,
#ifdef ENABLE_CATCH_KING_EVENT_FLAG_RENEWAL
	CATCHKING_GC_SET_CARD_PIECE_FLAG,
	CATCHKING_GC_SET_CARD_FLAG,
	CATCHKING_GC_SET_QUEST_FLAG,
	CATCHKING_GC_NO_MORE_GAIN,
#endif
};

typedef struct SPacketCGMiniGameCatchKing
{
	BYTE bHeader;
	BYTE bSubHeader;
	BYTE bSubArgument;
} TPacketCGMiniGameCatchKing;

typedef struct SPacketGCMiniGameCatchKing
{
	BYTE bHeader;
	WORD wSize;
	BYTE bSubHeader;
} TPacketGCMiniGameCatchKing;

typedef struct SPacketGCMiniGameCatchKingResult
{
	DWORD dwPoints;
	BYTE bRowType;
	BYTE bCardPos;
	BYTE bCardValue;
	bool bKeepFieldCard;
	bool bDestroyHandCard;
	bool bGetReward;
	bool bIsFiveNearBy;
} TPacketGCMiniGameCatchKingResult;

typedef struct SPacketGCMiniGameCatchKingSetEndCard
{
	BYTE bCardPos;
	BYTE bCardValue;
} TPacketGCMiniGameCatchKingSetEndCard;

#ifdef ENABLE_CATCH_KING_EVENT_FLAG_RENEWAL
typedef struct SPacketGCMiniGameCatchKingQuestFlag
{
	WORD wPieceCount, wPackCount;
} TPacketGCMiniGameCatchKingQuestFlag;
#endif
#endif

#ifdef ENABLE_MINI_GAME_RUMI
enum EMiniGameRumiCGSubHeader
{
	RUMI_CG_SUBHEADER_END,
	RUMI_CG_SUBHEADER_START,
	RUMI_CG_SUBHEADER_DECK_CARD_CLICK,
	RUMI_CG_SUBHEADER_HAND_CARD_CLICK,
	RUMI_CG_SUBHEADER_FIELD_CARD_CLICK,
#ifdef ENABLE_OKEY_EVENT_FLAG_RENEWAL
	RUMI_CG_SUBHEADER_REQUEST_QUEST_FLAG,
#endif
};

enum EMiniGameRumiGCSubHeader
{
	RUMI_GC_SUBHEADER_END,
	RUMI_GC_SUBHEADER_START,
	RUMI_GC_SUBHEADER_SET_DECK,
	RUMI_GC_SUBHEADER_SET_SCORE,
	RUMI_GC_SUBHEADER_MOVE_CARD,
#ifdef ENABLE_OKEY_EVENT_FLAG_RENEWAL
	RUMI_GC_SUBHEADER_SET_CARD_PIECE_FLAG,
	RUMI_GC_SUBHEADER_SET_CARD_FLAG,
	RUMI_GC_SUBHEADER_SET_QUEST_FLAG,
	RUMI_GC_SUBHEADER_NO_MORE_GAIN,
#endif
};

typedef struct SPacketCGMiniGameRumi
{
	BYTE bHeader;
	BYTE bSubHeader;
	BOOL bUseCard;
	BYTE bIndex;
	SPacketCGMiniGameRumi() : bHeader(HEADER_CG_MINI_GAME_RUMI), bSubHeader(RUMI_CG_SUBHEADER_END), bUseCard(FALSE), bIndex(0) {}
} TPacketCGMiniGameRumi;

typedef struct SPacketGCMiniGameRumiSetDeck
{
	BYTE bDeckCount;
} TPacketGCMiniGameRumiSetDeck;

typedef struct SPacketGCMiniGameRumiMoveCard
{
	BYTE bSrcPos, bSrcIndex, bSrcColor, bSrcNumber;
	BYTE bDstPos, bDstIndex, bDstColor, bDstNumber;
} TPacketGCMiniGameRumiMoveCard;

typedef struct SPacketGCMiniGameRumiSetScore
{
	WORD wScore, wTotalScore;
} TPacketGCMiniGameRumiSetScore;

#ifdef ENABLE_OKEY_EVENT_FLAG_RENEWAL
typedef struct SPacketGCMiniGameRumiQuestFlag
{
	WORD wCardPieceCount, wCardCount;
} TPacketGCMiniGameRumiQuestFlag;
#endif

typedef struct SPacketGCMiniGameRumi
{
	BYTE bHeader;
	WORD wSize;
	BYTE bSubHeader;
} TPacketGCMiniGameRumi;
#endif

#ifdef ENABLE_MINI_GAME_YUTNORI
enum EMiniGameYutnoriGCSubHeader
{
	YUTNORI_GC_SUBHEADER_START,
	YUTNORI_GC_SUBHEADER_STOP,
	YUTNORI_GC_SUBHEADER_SET_PROB,
	YUTNORI_GC_SUBHEADER_THROW,
	YUTNORI_GC_SUBHEADER_MOVE,
	YUTNORI_GC_SUBHEADER_AVAILABLE_AREA,
	YUTNORI_GC_SUBHEADER_PUSH_CATCH_YUT,
	YUTNORI_GC_SUBHEADER_SET_SCORE,
	YUTNORI_GC_SUBHEADER_SET_REMAIN_COUNT,
	YUTNORI_GC_SUBHEADER_PUSH_NEXT_TURN,
#ifdef ENABLE_YUTNORI_EVENT_FLAG_RENEWAL
	YUTNORI_GC_SUBHEADER_SET_YUT_PIECE_FLAG,
	YUTNORI_GC_SUBHEADER_SET_YUT_BOARD_FLAG,
	YUTNORI_GC_SUBHEADER_SET_QUEST_FLAG,
	YUTNORI_GC_SUBHEADER_NO_MORE_GAIN,
#endif
};

enum EMiniGameYutnoriCGSubHeader
{
	YUTNORI_CG_SUBHEADER_START,
	YUTNORI_CG_SUBHEADER_GIVEUP,
	YUTNORI_CG_SUBHEADER_SET_PROB,
	YUTNORI_CG_SUBHEADER_CLICK_CHAR,
	YUTNORI_CG_SUBHEADER_THROW,
	YUTNORI_CG_SUBHEADER_MOVE,
	YUTNORI_CG_SUBHEADER_REQUEST_COM_ACTION,
	YUTNORI_CG_SUBHEADER_REWARD,
#ifdef ENABLE_YUTNORI_EVENT_FLAG_RENEWAL
	YUTNORI_CG_SUBHEADER_REQUEST_QUEST_FLAG,
#endif
};

typedef struct SPacketCGMiniGameYutnori
{
	BYTE bHeader;
	BYTE bSubHeader;
	BYTE bArgument;
} TPacketCGMiniGameYutnori;

typedef struct SPacketGCMiniGameYutnori
{
	BYTE bHeader;
	WORD wSize;
	BYTE bSubHeader;
} TPacketGCMiniGameYutnori;

typedef struct SPacketGCMiniGameYutnoriSetProb { BYTE bProbIndex; } TPacketGCMiniGameYutnoriSetProb;
typedef struct SPacketGCMiniGameYutnoriThrowYut { bool bPC; BYTE bYut; } TPacketGCMiniGameYutnoriThrowYut;
typedef struct SPacketGCMiniGameYutnoriMoveYut
{
	bool bPC;
	BYTE bUnitIndex;
	bool bIsCatch;
	BYTE bStartIndex;
	BYTE bDestIndex;
} TPacketGCMiniGameYutnoriMoveYut;
typedef struct SPacketGCMiniGameYutnoriAvailableArea { BYTE bPlayerIndex; BYTE bAvailableIndex; } TPacketGCMiniGameYutnoriAvailableArea;
typedef struct SPacketGCMiniGameYutnoriPushCatchYut { bool bPC; BYTE bUnitIndex; } TPacketGCMiniGameYutnoriPushCatchYut;
typedef struct SPacketGCMiniGameYutnoriSetScore { WORD wScore; } TPacketGCMiniGameYutnoriSetScore;
typedef struct SPacketGCMiniGameYutnoriSetRemainCount { BYTE bRemainCount; } TPacketGCMiniGameYutnoriSetRemainCount;
typedef struct SPacketGCMiniGameYutnoriPushNextTurn { bool bPC; BYTE bState; } TPacketGCMiniGameYutnoriPushNextTurn;
#ifdef ENABLE_YUTNORI_EVENT_FLAG_RENEWAL
typedef struct SPacketGCMiniGameYutnoriQuestFlag { WORD wYutPieceCount; WORD wYutBoardCount; } TPacketGCMiniGameYutnoriQuestFlag;
#endif
#endif

#ifdef ENABLE_FLOWER_EVENT
enum EFlowerEventShootType
{
	SHOOT_ENVELOPE,
	SHOOT_CHRYSANTHEMUM,
	SHOOT_MAY_BELL,
	SHOOT_DAFFODIL,
	SHOOT_LILY,
	SHOOT_SUNFLOWER,
	SHOOT_TYPE_MAX,
};

enum EFlowerEventMisc
{
	FLOWER_EVENT_SHOOT_ENVELOPE_NEED_COUNT = 1,
	FLOWER_EVENT_SHOOT_NEED_COUNT = 10,
	FLOWER_EVENT_NEED_INVENTORY_SPACE = 1,
	FLOWER_EVENT_EXCHANGE_COOLTIME_SEC = 1,
	MAX_FLOWER_EVENT_ITEM_COUNT = 99999,
};

enum EFlowerEventChatType
{
	FLOWER_EVENT_CHAT_TYPE_NOT_ENOUGH_SHOOT_COUNT,
	FLOWER_EVENT_CHAT_TYPE_NOT_ENOUGH_EVENTORY_SPACE,
	FLOWER_EVENT_CHAT_TYPE_NOT_ENOUGH_SHOOT_ENVELOPE,
	FLOWER_EVENT_CHAT_TYPE_GET_SHOOT_ENVELOPE,
	FLOWER_EVENT_CHAT_TYPE_GET_SHOOT_CHRYSANTHEMUM,
	FLOWER_EVENT_CHAT_TYPE_GET_SHOOT_MAY_BELL,
	FLOWER_EVENT_CHAT_TYPE_GET_SHOOT_DAFFODIL,
	FLOWER_EVENT_CHAT_TYPE_GET_SHOOT_LILY,
	FLOWER_EVENT_CHAT_TYPE_GET_SHOOT_SUNFLOWER,
	FLOWER_EVENT_CHAT_TYPE_ITEM_FULL_AND_NOT_USE,
	FLOWER_EVENT_CHAT_TYPE_GET_SHOOT_CHRYSANTHEMUM_COUNT,
	FLOWER_EVENT_CHAT_TYPE_GET_SHOOT_MAY_BELL_COUNT,
	FLOWER_EVENT_CHAT_TYPE_GET_SHOOT_DAFFODIL_COUNT,
	FLOWER_EVENT_CHAT_TYPE_GET_SHOOT_LILY_COUNT,
	FLOWER_EVENT_CHAT_TYPE_GET_SHOOT_SUNFLOWER_COUNT,
	FLOWER_EVENT_CHAT_TYPE_ENVELOPE_MAX,
	FLOWER_EVENT_CHAT_TYPE_MAX,
};

enum EPacketGCFlowerEvent
{
	FLOWER_EVENT_SUBHEADER_GC_INFO_ALL,
	FLOWER_EVENT_SUBHEADER_GC_GET_INFO,
	FLOWER_EVENT_SUBHEADER_GC_UPDATE_INFO
};

typedef struct SPacketGCFlowerEvent
{
	BYTE bHeader;
	BYTE bSubHeader;
	BYTE bChatType;
	BYTE bShootType;
	int aiShootCount[SHOOT_TYPE_MAX + 1];
} TPacketGCFlowerEvent;

enum EPacketCGFlowerEvent
{
	FLOWER_EVENT_SUBHEADER_CG_INFO_ALL,
	FLOWER_EVENT_SUBHEADER_CG_EXCHANGE
};

typedef struct SPacketCGFlowerEvent
{
	BYTE bHeader;
	BYTE bSubHeader;
	BYTE bShootType;
	BYTE bExchangeKey;
} TPacketCGFlowerEvent;
#endif

#ifdef ENABLE_SWITCHBOT
// MT2009_PLUS_SWITCHBOT_V1 (structs): Ameria's switchbot - the server's packet.h (server-patches/switchbot) the same
struct TSwitchbotAttributeAlternativeTable
{
	TPlayerItemAttribute attributes[SWITCHBOT_ATTR_COUNT];

	bool IsConfigured() const
	{
		for (int i = 0; i < SWITCHBOT_ATTR_COUNT; ++i)
		{
			if (attributes[i].bType && attributes[i].sValue)
				return true;
		}

		return false;
	}
};

struct TSwitchbotTable
{
	DWORD player_id;
	bool active[SWITCHBOT_SLOT_COUNT];
	bool finished[SWITCHBOT_SLOT_COUNT];
	DWORD items[SWITCHBOT_SLOT_COUNT];
	TSwitchbotAttributeAlternativeTable alternatives[SWITCHBOT_SLOT_COUNT][SWITCHBOT_ALTERNATIVE_COUNT];
};

struct TSwitchbotAttributeInfo
{
	BYTE attribute_set;
	int apply_num;
	int max_value;
};

enum ECGSwitchbotSubheader
{
	SUBHEADER_CG_SWITCHBOT_START,
	SUBHEADER_CG_SWITCHBOT_STOP,
};

typedef struct SPacketCGSwitchbot
{
	BYTE header;
	WORD size;
	BYTE subheader;
	BYTE slot;
} TPacketCGSwitchbot;	// + 5 alternatives at START

enum EGCSwitchbotSubheader
{
	SUBHEADER_GC_SWITCHBOT_UPDATE,
	SUBHEADER_GC_SWITCHBOT_UPDATE_ITEM,
	SUBHEADER_GC_SWITCHBOT_SEND_ATTRIBUTE_INFORMATION,
};

typedef struct SPacketGCSwitchbot
{
	BYTE header;
	WORD size;
	BYTE subheader;
	BYTE slot;
} TPacketGCSwitchbot;

typedef struct SSwitchbotUpdateItem
{
	BYTE	slot;
	DWORD	vnum;
	DWORD	count;
	int		alSockets[ITEM_SOCKET_SLOT_MAX_NUM];
	TPlayerItemAttribute aAttr[ITEM_ATTRIBUTE_SLOT_MAX_NUM];
	WORD	CellInven;
} TSwitchbotUpdateItem;
#endif

#ifdef ENABLE_NPC_LOCATION_HELPER
// MT2009_PLUS_NPC_LOCATION_HELPER_V1 (Lokalizator NPC, Autor: Best Studio): the same layout as the server's packet.h
// (fixed-size ints - the server is not 32-bit-long). x/y = local position in metres (point file value / 100).
enum ENPCLocationHelperCGSubHeader
{
	NPC_LOCATION_HELPER_CG_REQUEST_STATUS,
	NPC_LOCATION_HELPER_CG_WARP_TO_NPC,
	NPC_LOCATION_HELPER_CG_USE_TICKET,
	NPC_LOCATION_HELPER_CG_REQUEST_GUILD_LAND,
};

enum ENPCLocationHelperGCSubHeader
{
	NPC_LOCATION_HELPER_GC_STATUS,
	NPC_LOCATION_HELPER_GC_WARP_RESULT,
	NPC_LOCATION_HELPER_GC_GUILD_LAND,
};

typedef struct command_npc_location_helper_cg
{
	BYTE	header;
	BYTE	subheader;
	int		mapIndex;
	DWORD	vnum;
	int		x;
	int		y;
} TPacketCGNPCLocationHelper;

typedef struct command_npc_location_helper_gc
{
	BYTE	header;
	BYTE	subheader;
	BYTE	result;
	BYTE	active;
	DWORD	cooldownRemain;
	int		mapIndex;	// STATUS: the character's map index (0 = unknown); WARP_RESULT: the target's
	DWORD	vnum;
	int		x;
	int		y;
} TPacketGCNPCLocationHelper;
#endif

#ifdef ENABLE_FISH_EVENT
// MT2009_PLUS_FISH_PUZZLE_V2 (packets): the fish puzzle - byte for byte the server's (server-patches/fishpuzzle, fish_puzzle.cpp).
// CG 219: this head, then BOX_USE: BYTE window, WORD cell | SHAPE_ADD: BYTE cell, then the sequence byte.
enum
{
	FISH_EVENT_SUBHEADER_BOX_USE,
	FISH_EVENT_SUBHEADER_SHAPE_ADD,
	FISH_EVENT_SUBHEADER_GC_REWARD,
	FISH_EVENT_SUBHEADER_GC_ENABLE,
};

typedef struct SPacketCGFishEvent
{
	BYTE	bHeader;
	BYTE	bSubheader;
} TPacketCGFishEvent;

typedef struct SPacketGCFishEventInfo
{
	BYTE	bHeader;
	BYTE	bSubheader;
	DWORD	dwFirstArg;
	DWORD	dwSecondArg;
} TPacketGCFishEventInfo;
#endif

#ifdef ENABLE_MT2009_SKILL_COLOR
// MT2009_PLUS_SKILL_COLOR_V1 (structs): Kolor umiejetnosci - as the server's packet.h (server-patches/skillcolor). A colour
// is 0 (the effect's own) or 0xFFrrggbb; layer n colours the effect's particle system n (the 5th also every later one).
enum
{
	SKILL_COLOR_LAYERS = 5,
	SKILL_COLOR_TYPE_OWN = 0,	// the character's own colour of the skill
	SKILL_COLOR_TYPE_BUFF = 1,	// the colour of the shaman buff it carries (its caster's; 94/95/96/110/111)
};

typedef struct SPacketCGSkillColor
{
	BYTE	bHeader;
	WORD	wSkillVnum;
	DWORD	adwColor[SKILL_COLOR_LAYERS];
} TPacketCGSkillColor;

typedef struct SPacketGCSkillColor
{
	BYTE	bHeader;
	DWORD	dwVID;
	BYTE	bType;
	WORD	wSkillVnum;
	DWORD	adwColor[SKILL_COLOR_LAYERS];
} TPacketGCSkillColor;
#endif

#ifdef ENABLE_GROWTH_PET_SYSTEM
// MT2009_PLUS_GROWTH_PET_V1 (structs): System zwierzat domowych - identical on both sides (contract SPEC.md, the server's
// packet.h in server-patches/pety). Anka2's layout except: feed / revive positions are TItemPos (any inventory window),
// bLocked is a BYTE, the champion points, GC 235 PET_LOOK, GC 236 / CG 134 the potential slots.
enum EGrowthPet
{
	GROWTH_PET_NAME_MIN = 4,
	GROWTH_PET_NAME_MAX = 20,			// name bytes (cp1250); the packets carry char[21]
	GROWTH_PET_SKILL_SLOTS = 3,			// Anka2 PET_SKILL_COUNT_MAX
	GROWTH_PET_SKILL_LEVEL_MAX = 20,	// PET_GROWTH_SKILL_LEVEL_MAX
	GROWTH_PET_FEED_SLOTS = 9,			// PET_FEED_SLOT_MAX
	GROWTH_PET_REVIVE_SLOTS = 10,		// PET_REVIVE_MATERIAL_SLOT_MAX
	GROWTH_PET_POTENTIAL_SLOTS = 2,
	GROWTH_PET_MAX_LEVEL = 105,
	GROWTH_PET_CHAMPION_MAX_LEVEL = 30,
	GROWTH_PET_HATCHING_MONEY = 100000,
	GROWTH_PET_SKILL_UPGRADE_PRICE = 2000000,
	GROWTH_PET_EVOL_MAX = 6,			// 1 Mlody, 2 Dziki, 3 Dzielny, 4 Bohaterski, 5 Przebudzony, 6 Mocny
	GROWTH_PET_SKILL_OPEN_EVOL_LEVEL = 4,
};

enum EGrowthPetPoints	// index into dwPoints[]
{
	POINT_UPBRINGING_PET_LEVEL,				// 0
	POINT_UPBRINGING_PET_EXP,				// 1 mob exp of the current level
	POINT_UPBRINGING_PET_ITEM_EXP,			// 2 item exp of the current level
	POINT_UPBRINGING_PET_NEXT_EXP,			// 3 mob + item exp the level needs
	POINT_UPBRINGING_PET_EVOL_LEVEL,		// 4 1..6
	POINT_UPBRINGING_PET_HP,				// 5 0.001 %
	POINT_UPBRINGING_PET_DEF_GRADE,			// 6 0.001 %
	POINT_UPBRINGING_PET_SP,				// 7 0.001 %
	POINT_UPBRINGING_DURATION,				// 8 unix time the life ends
	POINT_UPBRINGING_MAX_DURATION,			// 9 seconds of a full life
	POINT_UPBRINGING_BIRTHDAY,				// 10 unix time
	POINT_UPBRINGING_CHAMPION_LEVEL,		// 11 0 = none, 1..30
	POINT_UPBRINGING_CHAMPION_EXP,			// 12
	POINT_UPBRINGING_CHAMPION_ITEM_EXP,		// 13
	POINT_UPBRINGING_CHAMPION_NEXT_EXP,		// 14
	POINT_UPBRINGING_CHAMPION_RES,			// 15 0.001 %
	POINT_UPBRINGING_CHAMPION_BLOCK_PEN,	// 16 0.001 %
	POINT_UPBRINGING_CHAMPION_PRECISION,	// 17 0.001 %
	POINT_UPBRINGING_TYPE,					// 18 1..8 after Sfera Losu, else 0
	POINT_UPBRINGING_SKILL_SLOTS,			// 19 1..3
	POINT_UPBRINGING_MAX_NUM,				// 20
};

enum EGrowthPetSubheader	// TPacketGCPet.subheader (Anka2's order, 13-15 new)
{
	SUBHEADER_PET_EGG_USE_SUCCESS,				// 0
	SUBHEADER_PET_EGG_USE_FAILED_BECAUSE_NAME,	// 1
	SUBHEADER_PET_EGG_USE_FAILED_TIMEOVER,		// 2
	SUBHEADER_PET_UNSUMMON,						// 3
	SUBHEADER_PET_FEED_FAILED,					// 4
	SUBHEADER_PET_FEED_SUCCESS,					// 5
	SUBHEADER_PET_REVIVE_FAILED,				// 6
	SUBHEADER_PET_REVIVE_SUCCESS,				// 7
	SUBHEADER_PET_NAME_CHANGE_FAILED,			// 8
	SUBHEADER_PET_NAME_CHANGE_SUCCESS,			// 9
	SUBHEADER_PET_WINDOW_TYPE_INFO,				// 10
	SUBHEADER_PET_WINDOW_TYPE_ATTR_CHANGE,		// 11
	SUBHEADER_PET_WINDOW_TYPE_PREMIUM_FEED,		// 12
	SUBHEADER_PET_EVOLVE_SUCCESS,				// 13 python PetEvolveResult(1)
	SUBHEADER_PET_POTENTIAL_FAILED,				// 14 python PetPotentialResult(0)
	SUBHEADER_PET_POTENTIAL_SUCCESS,			// 15 python PetPotentialResult(1)
};

enum EGrowthPetWindow { PET_WINDOW_HATCH, PET_WINDOW_NAME_CHANGE };	// TPacketCGPetWindow.window
enum EGrowthPetWindowType { PET_WINDOW_INFO, PET_WINDOW_ATTR_CHANGE, PET_WINDOW_PRIMIUM_FEEDSTUFF };	// CG 123 type
enum EGrowthPetFeed { FEED_LIFE_TIME_EVENT, FEED_EVOL_EVENT, FEED_EXP_EVENT, FEED_BUTTON_MAX };	// TPacketCGPetFeed.index
enum EGrowthPetPotentialAction { PET_POTENTIAL_INSERT = 0, PET_POTENTIAL_REMOVE = 1 };

typedef struct SGrowthPetSkillInfo
{
	BYTE	bLocked;
	BYTE	bSkill;
	BYTE	bLevel;
	DWORD	dwCooltime;
} TGrowthPetSkillInfo;

typedef struct SPacketGCPet
{
	BYTE	header;
	BYTE	subheader;
} TPacketGCPet;

typedef struct SPacketGCPetSet	// GC 225 (own pets) / GC 226 (the exchange partner's)
{
	BYTE	header;
	DWORD	dwID;				// pet id (= socket 2 of its seal / bag)
	DWORD	dwSummonItemVnum;	// the seal's vnum, also for a pet in a bag
	char	szName[GROWTH_PET_NAME_MAX + 1];
	TGrowthPetSkillInfo aSkill[GROWTH_PET_SKILL_SLOTS];
	DWORD	dwPoints[POINT_UPBRINGING_MAX_NUM];
} TPacketGCPetSet;

typedef struct SPacketGCPetDelete
{
	BYTE	header;
	DWORD	dwID;
} TPacketGCPetDelete;

typedef struct SPacketGCPetSummon
{
	BYTE	header;
	DWORD	dwID;
} TPacketGCPetSummon;

typedef struct SPacketGCPetPointUpdate
{
	BYTE	header;
	DWORD	dwID;
	BYTE	bPoint;
	DWORD	dwValue;
} TPacketGCPetPointUpdate;

typedef struct SPacketGCPetNameChangeResult
{
	BYTE	header;
	BYTE	subheader;
	DWORD	dwID;
	char	szName[GROWTH_PET_NAME_MAX + 1];
} TPacketGCPetNameChangeResult;

typedef struct SPacketGCPetDetermineResult
{
	BYTE	header;
	BYTE	type;
} TPacketGCPetDetermineResult;

typedef struct SPacketGCPetAttrChangeResult
{
	BYTE	header;
	BYTE	type;
	TItemPos pos;
} TPacketGCPetAttrChangeResult;

typedef struct SGrowthPetSkillUpdate
{
	BYTE	bLocked;
	BYTE	bSkill;
	BYTE	bLevel;
	DWORD	dwCooltime;
	BYTE	bSkillFormula1[GROWTH_PET_SKILL_LEVEL_MAX];	// activation chance % at skill level 1..20
	WORD	wSkillFormula2[GROWTH_PET_SKILL_LEVEL_MAX];	// the value at skill level 1..20, in tenths
	BYTE	bSkillFormula3[GROWTH_PET_SKILL_LEVEL_MAX];	// duration in tenths of a second, 0 = none
} TGrowthPetSkillUpdate;

typedef struct SPacketGCPetSkillUpdate
{
	BYTE	header;
	DWORD	dwID;
	TGrowthPetSkillUpdate aSkill[GROWTH_PET_SKILL_SLOTS];
} TPacketGCPetSkillUpdate;

typedef struct SPacketGCPetSkillCooltime
{
	BYTE	header;
	DWORD	dwID;
	BYTE	bSlot;
	DWORD	dwCooltime;
} TPacketGCPetSkillCooltime;

typedef struct SPacketGCPetLook	// GC 235: a growth pet's look for every viewer
{
	BYTE	header;
	DWORD	dwVID;
	WORD	wScalePct;		// the model scale in per cent (100 = as is)
	BYTE	bEvolution;		// 1..6
	BYTE	bType78;		// 1: a pet of type 7/8 (a glow effect may come later; unused now)
} TPacketGCPetLook;

typedef struct SGrowthPetPotentialSlot
{
	DWORD	dwEggVnum;
	BYTE	bSkill;
	BYTE	bLevel;
	DWORD	dwEndTime;
} TGrowthPetPotentialSlot;

typedef struct SPacketGCPetPotential	// GC 236
{
	BYTE	header;
	DWORD	dwID;
	BYTE	bOpenSlots;
	TGrowthPetPotentialSlot aSlot[GROWTH_PET_POTENTIAL_SLOTS];
} TPacketGCPetPotential;

typedef struct SPacketCGPetHatch
{
	BYTE	header;
	char	name[GROWTH_PET_NAME_MAX + 1];
	TItemPos eggPos;
} TPacketCGPetHatch;

typedef struct SPacketCGPetWindow
{
	BYTE	header;
	BYTE	window;
	BYTE	state;
} TPacketCGPetWindow;

typedef struct SPacketCGPetWindowType
{
	BYTE	header;
	BYTE	type;
} TPacketCGPetWindowType;

typedef struct SPacketCGPetFeed
{
	BYTE	header;
	BYTE	index;
	TItemPos pos[GROWTH_PET_FEED_SLOTS];
	WORD	count[GROWTH_PET_FEED_SLOTS];
} TPacketCGPetFeed;

typedef struct SPacketCGPetDetermine
{
	BYTE	header;
	TItemPos determinePos;
} TPacketCGPetDetermine;

typedef struct SPacketCGPetAttrChange
{
	BYTE	header;
	TItemPos upBringingPos;
	TItemPos attrChangePos;
} TPacketCGPetAttrChange;

typedef struct SPacketCGPetRevive
{
	BYTE	header;
	TItemPos upBringingPos;
	TItemPos pos[GROWTH_PET_REVIVE_SLOTS];
	WORD	count[GROWTH_PET_REVIVE_SLOTS];
} TPacketCGPetRevive;

typedef struct SPacketCGPetLearnSkill
{
	BYTE	header;
	BYTE	slotIndex;
	TItemPos learnSkillPos;
} TPacketCGPetLearnSkill;

typedef struct SPacketCGPetSkillUpgrade
{
	BYTE	header;
	BYTE	slotIndex;
} TPacketCGPetSkillUpgrade;

typedef struct SPacketCGPetDeleteSkill
{
	BYTE	header;
	BYTE	slotIndex;
	TItemPos deleteSkillPos;
} TPacketCGPetDeleteSkill;

typedef struct SPacketCGPetDeleteAllSkill
{
	BYTE	header;
	TItemPos deleteAllSkillPos;
} TPacketCGPetDeleteAllSkill;

typedef struct SPacketCGPetNameChange
{
	BYTE	header;
	char	name[GROWTH_PET_NAME_MAX + 1];
	TItemPos changeNamePos;
	TItemPos upBringingPos;
} TPacketCGPetNameChange;

typedef struct SPacketCGPetPotential	// CG 134
{
	BYTE	header;
	BYTE	action;		// PET_POTENTIAL_INSERT / PET_POTENTIAL_REMOVE
	BYTE	slot;
	TItemPos eggPos;
} TPacketCGPetPotential;
#endif

#ifdef ENABLE_MT2009_TITLES
// MT2009_PLUS_TITLES_V1 (structs): Tytuly - as the server's packet.h (server-patches/tytuly); the sizes: Mt2009Titles.cpp static_assert
enum
{
	TITLE_CG_OPEN = 0,
	TITLE_CG_EQUIP = 1,
	TITLE_CG_UNEQUIP = 2,
	TITLE_GC_TABLE = 0,
	TITLE_GC_PLAYER = 1,
	TITLE_GC_EQUIPPED = 2,
	TITLE_GC_NOTIFY = 3,
	TITLE_GC_VISUAL = 4,
	TITLE_NAME_LEN = 32,
	TITLE_CONDITION_LEN = 160,
	TITLE_EFFECT_LEN = 96,
};

typedef struct SPacketCGTitle
{
	BYTE	bHeader;
	BYTE	bSubHeader;
	DWORD	dwTitle;
} TPacketCGTitle;

typedef struct SPacketGCTitle
{
	BYTE	bHeader;
	WORD	wSize;
	BYTE	bSubHeader;
	WORD	wCount;
} TPacketGCTitle;

typedef struct SPacketGCTitleRow
{
	DWORD	dwTitle;
	BYTE	bType;
	BYTE	bPermanent;
	WORD	wResource;
	DWORD	dwDuration;
	DWORD	dwColor;
	short	sEffectZ;
	char	szName[TITLE_NAME_LEN + 1];
	char	szCondition[TITLE_CONDITION_LEN + 1];
	char	szEffect[TITLE_EFFECT_LEN + 1];
} TPacketGCTitleRow;

typedef struct SPacketGCTitleOwned
{
	DWORD	dwTitle;
	DWORD	dwEndTime;
} TPacketGCTitleOwned;

typedef struct SPacketGCTitleNotify
{
	BYTE	bMessage;
	DWORD	dwTitle;
} TPacketGCTitleNotify;

typedef struct SPacketGCTitleVisual
{
	DWORD	dwVID;
	DWORD	dwTitle;
} TPacketGCTitleVisual;
#endif

#pragma pack(pop)

#ifdef ENABLE_FISH_EVENT
static_assert(sizeof(TPacketCGFishEvent) == 2 && sizeof(TPacketGCFishEventInfo) == 10, "fish event packets (server packet.h)");
#endif
#ifdef ENABLE_MT2009_SKILL_COLOR
static_assert(sizeof(TPacketCGSkillColor) == 23 && sizeof(TPacketGCSkillColor) == 28, "skill colour packets (server packet.h)");
#endif

#ifdef ENABLE_NPC_LOCATION_HELPER
static_assert(sizeof(TPacketCGNPCLocationHelper) == 18, "CG NPC location helper must be 18 bytes (server packet.h)");
static_assert(sizeof(TPacketGCNPCLocationHelper) == 24, "GC NPC location helper must be 24 bytes (server packet.h)");
#endif

#ifdef ENABLE_MINI_GAME_RUMI
static_assert(sizeof(TPacketCGMiniGameRumi) == 7, "CG Rumi must be 7 bytes (Owsap)");
#endif
#ifdef ENABLE_FLOWER_EVENT
static_assert(sizeof(TPacketGCFlowerEvent) == 32, "GC Flower must be 32 bytes (Owsap)");
static_assert(sizeof(TPacketCGFlowerEvent) == 4, "CG Flower must be 4 bytes (Owsap)");
#endif
#ifdef ENABLE_SWITCHBOT
// MT2009_PLUS_SWITCHBOT_V1 (sizes): the server's static_assert the same
static_assert(sizeof(TPacketCGSwitchbot) == 5 && sizeof(TPacketGCSwitchbot) == 5, "switchbot packets must be 5 bytes");
// MT2009_PLUS_WIDE_ATTR_V1 (switchbot sizes): a bonus line is 4 B (WORD type + short value) - the server's packet.h the same
static_assert(sizeof(TSwitchbotUpdateItem) == 51, "switchbot update item must be 51 bytes");
static_assert(sizeof(TSwitchbotAttributeAlternativeTable) == 20 && sizeof(TSwitchbotTable) == 534 && sizeof(TSwitchbotAttributeInfo) == 9, "switchbot tables");
static_assert(sizeof(TPlayerItemAttribute) == 4 && sizeof(TPacketAffectElement) == 26 && sizeof(TPacketGCAffectRemove) == 7, "MT2009_PLUS_WIDE_ATTR_V1: two-byte bonus type / affect point");
static_assert(sizeof(TPacketGCPointChange) == 18 && sizeof(TShopItemData) == 57 && sizeof(SEquipmentItemSet) == 48 && sizeof(ikashop::TFilterInfo) == 86, "MT2009_PLUS_WIDE_ATTR_V1: point change 18 B, shop item 57 B, view equipment item 48 B, Ikarus search filter 86 B (server packet.h)");
#endif
#ifdef ENABLE_MINI_GAME_CATCH_KING
static_assert(sizeof(TPacketGCMiniGameCatchKingResult) == 11, "CatchKing result must be 11 bytes (Owsap)");
#endif
#ifdef ENABLE_GROWTH_PET_SYSTEM
// MT2009_PLUS_GROWTH_PET_V1 (sizes): SPEC.md - the server's packet.h asserts the same
static_assert(sizeof(TItemPos) == 3, "growth pet: TItemPos must be BYTE + WORD");
static_assert(ITEM_PET == 37, "growth pet: item type ITEM_PET must be 37 (item.ITEM_TYPE_GROWTH_PET)");
static_assert(sizeof(TGrowthPetSkillInfo) == 7 && sizeof(TPacketGCPet) == 2 && sizeof(TPacketGCPetSet) == 131, "growth pet GC 224/225");
static_assert(sizeof(TPacketGCPetDelete) == 5 && sizeof(TPacketGCPetSummon) == 5 && sizeof(TPacketGCPetPointUpdate) == 10, "growth pet GC 227-229");
static_assert(sizeof(TPacketGCPetNameChangeResult) == 27 && sizeof(TPacketGCPetDetermineResult) == 2 && sizeof(TPacketGCPetAttrChangeResult) == 5, "growth pet GC 230-232");
static_assert(sizeof(TGrowthPetSkillUpdate) == 87 && sizeof(TPacketGCPetSkillUpdate) == 266 && sizeof(TPacketGCPetSkillCooltime) == 10, "growth pet GC 233/234");
static_assert(sizeof(TPacketGCPetLook) == 9 && sizeof(TGrowthPetPotentialSlot) == 10 && sizeof(TPacketGCPetPotential) == 26, "growth pet GC 235/236");
static_assert(sizeof(TPacketCGPetHatch) == 25 && sizeof(TPacketCGPetWindow) == 3 && sizeof(TPacketCGPetWindowType) == 2, "growth pet CG 122-124");
static_assert(sizeof(TPacketCGPetFeed) == 47 && sizeof(TPacketCGPetDetermine) == 4 && sizeof(TPacketCGPetAttrChange) == 7, "growth pet CG 126-128");
static_assert(sizeof(TPacketCGPetRevive) == 54 && sizeof(TPacketCGPetLearnSkill) == 5 && sizeof(TPacketCGPetSkillUpgrade) == 2, "growth pet CG 129-131");
static_assert(sizeof(TPacketCGPetDeleteSkill) == 5 && sizeof(TPacketCGPetDeleteAllSkill) == 4 && sizeof(TPacketCGPetNameChange) == 28, "growth pet CG 125/132/133");
static_assert(sizeof(TPacketCGPetPotential) == 6, "growth pet CG 134");
#endif
//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f

// Files shared by GameCore.top
