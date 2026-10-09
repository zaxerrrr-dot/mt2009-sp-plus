#pragma once

//////////////////////////////////////////////////////////////////////////
// ### Default Ymir Macros ###
#define LOCALE_SERVICE_EUROPE
#define ENABLE_COSTUME_SYSTEM
//#define ENABLE_ENERGY_SYSTEM
#define ENABLE_DRAGON_SOUL_SYSTEM
#define ENABLE_NEW_EQUIPMENT_SYSTEM // MT2009_PLUS_BELTS_V1: the belt inventory (Autor: Digi Rasta, nowy-system v0.27.0)
// ### Default Ymir Macros ###
//////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////
// ### New From LocaleInc ###
//#define ENABLE_SEQUENCE_SYSTEM
#define ENABLE_PACK_GET_CHECK
#define ENABLE_PROTOSTRUCT_AUTODETECT
//#define ENABLE_PLAYER_PER_ACCOUNT5
#define ENABLE_LEVEL_IN_TRADE
//#define ENABLE_DICE_SYSTEM
#define ENABLE_EXTEND_INVEN_SYSTEM
#define ENABLE_LVL115_ARMOR_EFFECT
#define ENABLE_SLOT_WINDOW_EX
#define ENABLE_TEXT_LEVEL_REFRESH
#define ENABLE_USE_COSTUME_ATTR
#define ENABLE_DISCORD_RPC
//#define ENABLE_PET_SYSTEM_EX
#define ENABLE_LOCALE_EX
#define ENABLE_NO_DSS_QUALIFICATION
//#define ENABLE_NO_SELL_PRICE_DIVIDED_BY_5
#define ENABLE_PENDANT_SYSTEM // MT2009_PLUS_ELEMENTS_V1: the talisman slot (Autor: Digi Rasta, Zywioly i talizmany, nowy-system 0.28.0)
//#define ENABLE_GLOVE_SYSTEM
#define ENABLE_MOVE_CHANNEL
//#define ENABLE_QUIVER_SYSTEM
#define ENABLE_RACE_HEIGHT
#define ENABLE_ELEMENTAL_TARGET // MT2009_PLUS_ELEMENTS_V1: the target's element icon (root/uitarget.py)
#define ENABLE_INGAME_CONSOLE
#define ENABLE_4TH_AFF_SKILL_DESC
#define ENABLE_LOCALE_COMMON
#define ENABLE_GUILD_TOKEN_AUTH
#define ENABLE_DS_GRADE_MYTH
#define ENABLE_DS_SET
#define ENABLE_DS_CHANGE_ATTR
#define ENABLE_DS_7_SLOT
//#define ENABLE_CONQUEROR_UI

#define ENABLE_NEW_EVENT_STRUCT
#ifdef ENABLE_NEW_EVENT_STRUCT
#define USE_NEW_EVENT_TEXT_AUTO_Y
#endif

//#define WJ_SHOW_MOB_INFO
#ifdef WJ_SHOW_MOB_INFO
#define ENABLE_SHOW_MOBAIFLAG
#define ENABLE_SHOW_MOBLEVEL
#define WJ_SHOW_MOB_INFO_EX
#endif
// ### New From LocaleInc ###
//////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////
// ### From GameLib ###
//#define ENABLE_WOLFMAN_CHARACTER
#ifdef ENABLE_WOLFMAN_CHARACTER
// #define DISABLE_WOLFMAN_ON_CREATE
#endif
// #define ENABLE_MAGIC_REDUCTION_SYSTEM
#define ENABLE_MOUNT_COSTUME_SYSTEM
#define ENABLE_WEAPON_COSTUME_SYSTEM
// ### From GameLib ###
//////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////
// ### New System Defines - Extended Version ###

// if is define ENABLE_ACCE_COSTUME_SYSTEM the players can use shoulder sash
#define ENABLE_ACCE_COSTUME_SYSTEM
#ifdef ENABLE_ACCE_COSTUME_SYSTEM
// #define USE_ACCE_ABSORB_WITH_NO_NEGATIVE_BONUS
#endif

// if you want use SetMouseWheelScrollEvent or you want use mouse wheel to move the scrollbar
#define ENABLE_MOUSEWHEEL_EVENT

//if you want to see highlighted a new item when dropped or when exchanged
#define ENABLE_HIGHLIGHT_NEW_ITEM

// it shows emojis in the textlines
#define ENABLE_EMOJI_SYSTEM

// effects while hidden won't show up
#define __ENABLE_STEALTH_FIX__

#define ENABLE_SET_ATLAS_SCALE
#define PARTY_POSITION

// circle dots in minimap instead of squares
//#define ENABLE_MINIMAP_WHITEMARK_CIRCLE
//#define ENABLE_MINIMAP_TELEPORT_CLICK // click on minimap as gm to warp directly

// enable the won system as a currency
//#define ENABLE_CHEQUE_SYSTEM
#ifdef ENABLE_CHEQUE_SYSTEM
#define DISABLE_CHEQUE_DROP
#define ENABLE_WON_EXCHANGE_WINDOW
#endif

// for debug: print received packets
// #define ENABLE_PRINT_RECV_PACKET_DEBUG

// ### New System Defines - Extended Version ###
//////////////////////////////////////////////////////////////////////////
//martysama0134's 4e4e75d8b719b9240e033009cf4d7b0f


// MT2009
#ifndef _RELEASE
#define MT2009_CINEMATIC
#endif

#ifndef MT2009_CINEMATIC
#define ENABLE_CANSEEHIDDENTHING_FOR_GM
#endif

//#define DEBUG_CYTHON
//#if defined(_DEBUG) && !defined(DEBUG_CYTHON)
//#define ENABLE_DEBUG_PACK_UNPACKED
//#else
////#define __USE_CYTHON__
////#define __THEMIDA__
//#define ENABLE_DEBUG_PACK_UNPACKED
//#endif

#define ENABLE_DISCORD_RPC

//#ifdef __USE_CYTHON__
//#define __CYTHON_PYD__
//#define __EXTRA_CYTHON__
//#endif

#define ENABLE_IKASHOP_RENEWAL
#define ENABLE_IKASHOP_ENTITIES
#define EXTEND_IKASHOP_PRO
#define EXTEND_IKASHOP_ULTIMATE
#define ENABLE_LARGE_DYNAMIC_PACKETS
// MT2009_PLUS_EVENT_MANAGER_V1: the in-game event list (HEADER_GC_INGAME_EVENT 183, python module
// ingameEventSystem, PythonInGameEventSystemManager.cpp).
#define ENABLE_INGAME_EVENT_MANAGER

// MT2009_PLUS_MINIGAMES_V1: Owsap v6.2.6 mini games (Rumi/Okey CG+GC 181, Yut Nori CG+GC 182,
// Catch the King CG 226 / GC 238, Flower Event CG+GC 187), see client-patches/exe/MINIGAMES.md.
#define ENABLE_MINI_GAME_RUMI
#define ENABLE_OKEY_EVENT_FLAG_RENEWAL
#define ENABLE_MINI_GAME_YUTNORI
#define ENABLE_YUTNORI_EVENT_FLAG_RENEWAL
#define ENABLE_MINI_GAME_CATCH_KING
#define ENABLE_CATCH_KING_EVENT_FLAG_RENEWAL
#define ENABLE_FLOWER_EVENT
// Owsap ui widgets / wndMgr functions (MoveImageBox, MoveScaleImageBox, MoveTextLine, Circle,
// ResetFrame + OnKeyFrame, EnableFlash, slot cover/highlight images, ...).
#define ENABLE_OWSAP_WNDMGR_EX
// Render target window (wndMgr.RegisterRenderTarget, app.RENDER_TARGET_INDEX_*); the 3D Yut Nori thrower.
#define RENDER_TARGET
// wndMgr.SetWheelTopWindow / ClearWheelTopWindow (OnMouseWheelButtonUp/Down of that window).
#define ENABLE_MOUSE_WHEEL_TOP_WINDOW

// MT2009_PLUS_DAMAGE_INFO_GUARD_V1: RecvDamageInfoPacket no longer dereferences a missing
// character (random client shutdowns in combat).
#define ENABLE_DAMAGE_INFO_NULL_GUARD
// MT2009_PLUS_RECV_TIME_BUDGET_V1: GamePhase reads past 8 packets a frame for up to 5 ms
// (crowds of bots; the archer's extra arrows fly with the shot).
#define ENABLE_RECV_TIME_BUDGET

// MT2009_PLUS_RANK_POINTS_V1: the rank of Punkty Rangi (server: playerbot_rank_points.h) in the alignment
// title's place over a character - chrmgr.RegisterRankTitle(tier, name, r, g, b), chrmgr.SetRankTitle(vid, tier)
// (root/rankpoints.py); tier 0 is the alignment title as before.
#define ENABLE_RANK_TITLE

// MT2009_PLUS_AREZZO_COSTUME_SETS_V1: glow effects of items by vnum (gamedata/shiningtable.txt, CItemManager::LoadShiningTable),
// attached when a character wears the item - the Arezzo weapon skins' and costumes' glows
// (CInstanceBase::SetWeapon / SetArmor). No packet, no python; without the file nothing changes.
#define ENABLE_ITEM_SHINING_TABLE

// MT2009_PLUS_ACCE_INITIAL_PLACEMENT_V1: a sash model whose place on the back is its InitialPlacement
// (root bone = identity; Arezzo's "me_w" wings) is drawn with it (EterGrnLib/ThingInstance.cpp).
// OFF since MT2009_PLUS_AREZZO_COSTUME_SETS_V4 (7.10.2026): the four "me_w" sash skins (85213, 85219, 85220,
// 85221) are removed from the game - no rotation fix placed them right - so nothing needs the correction;
// the code stays behind the flag, and without it the exe no longer stats acce_fix.txt every 2 s.
// #define ENABLE_ACCE_INITIAL_PLACEMENT

// MT2009_PLUS_YANG_LIMITS_V1 (Autor: Digi Rasta, nowy-system 0.26.0, limity Yang): yang in a trade in 64 bits
// (exchange.GetElkFrom*, net.SendExchangeElkAddPacket - the packet always carried a long long) and
// player.GOLD_MAX / EXCHANGE_GOLD_MAX / SHOP_PRICE_MAX as the server has them (common/length.h there).
#define ENABLE_MT2009_YANG_LIMITS
#define MT2009_YANG_GOLD_MAX 100000000000LL
#define MT2009_YANG_EXCHANGE_GOLD_MAX 10000000000LL
#define MT2009_YANG_SHOP_PRICE_MAX 50000000000LL

#define __BL_CLIP_MASK__

#define ENABLE_FIX_MOBS_LAG
#define CINEMATIC_CAMERA
//#define LEV_ANTICHEAT

// ---- Digi Rasta picks, nowy-system 0.28 (the owner, 7 October) --------------------------------------
// MT2009_PLUS_FEMALE_TITLES_V1 (Autor: Digi Rasta, Extended-Alignment): the female forms of the alignment
// titles and of the ranks of Punkty Rangi over a woman - chrmgr.RegisterTitleNameFemale(grade, name),
// chrmgr.RegisterRankTitleFemale(tier, name) (root/rankpoints.py, introloading.py).
#define ENABLE_FEMALE_TITLES
// MT2009_PLUS_DIGI_CLIENT_QOL_V1 (Autor: Digi Rasta): app.SetHideEffects, app.SetChatLog, chrmgr.SetShopsVisible
// for the "Opcje dodatkowe" tab (UserInterface/Mt2009ClientQol.cpp, EffectLib/EffectInstance.cpp,
// PythonIkarusShop.cpp, PythonChat.cpp).
#define ENABLE_DIGI_CLIENT_QOL
// MT2009_PLUS_MONSTER_CARD_MODEL_V1 (Autor: Digi Rasta): the Monster Cards' 3D preview, player.Mt2009Model*
// and app.RENDER_TARGET_INDEX_ILLUSTRATED (UserInterface/Mt2009MonsterModel.cpp; needs RENDER_TARGET).
#if defined(RENDER_TARGET)
#define ENABLE_MONSTER_CARD_MODEL
#endif
// MT2009_PLUS_ZODIAC_V1 (Autor: Digi Rasta, Swiatynia Zodiaku, nowy-system 0.35.0): GC 220 (boss effects),
// the 15 Zodiac SE_*/EFFECT_* effects, the mission chat types 13..15, chrmgr.IsDead/IsPC and the scripts'
// constants (UserInterface/Mt2009Zodiak.cpp). The image cooltime is MT2009_PLUS_MINIGAMES_V1's.
#define ENABLE_12ZI
// ------------------------------------------------------------------------------------------------------
// Files shared by GameCore.top
