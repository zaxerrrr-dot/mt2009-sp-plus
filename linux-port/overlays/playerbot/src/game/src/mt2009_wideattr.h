#ifndef MT2009_WIDEATTR_H
#define MT2009_WIDEATTR_H
// MT2009_PLUS_WIDE_ATTR_V1 (overlay): the type of a bonus / point number in the functions the engine's patched files
// declare and this overlay defines (Bonus67Total, Bonus67AttrValue, BonusModeAttrValue, ChampionAffectBonus). With
// server-patches/wideattr (common/length.h defines MT2009_PLUS_WIDE_ATTR) an item's bonus type, an item_proto apply
// and an affect's point are two bytes (WORD, up to POINT_MAX_NUM 512); without it they are the engine's old BYTE - the
// overlay builds and links either way.
#include "../../common/length.h" // MT2009_PLUS_WIDE_ATTR is defined there (with the patch) - stdafx.h does not include it
#ifdef MT2009_PLUS_WIDE_ATTR
typedef WORD TMt2009PointNum;
#else
typedef BYTE TMt2009PointNum;
#endif
#endif
