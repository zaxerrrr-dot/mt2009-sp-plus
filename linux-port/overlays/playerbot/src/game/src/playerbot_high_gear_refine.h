#ifndef __INC_METIN2_PLAYERBOT_HIGH_GEAR_REFINE_H__
#define __INC_METIN2_PLAYERBOT_HIGH_GEAR_REFINE_H__

// MT2009_PLUS_BOT_HIGH_GEAR_SCROLLS_V1 - how a bot raises a piece of level PLAYERBOT_HIGH_GEAR_MIN_LEVEL and over (the
// Yohara gear: the level-100 helmets, the jade jewellery, the Rekawice Mocy, the Talizman Woli, the 105-120 weapons and
// armours), as pure policy. The owner, 3 November 2026 (the night's bot trainer brief): gear of level 100 and over is
// raised only under scrolls and stones that never destroy the item -
//   * up to +4: the Blacksmith's Zwoj Wojny (UP_TO_3TH_LEVEL_SCROLL, value0 2: 100% under +4; crafting_proto rows 1 / 4,
//     a Blessing Scroll + Magiczna Ruda Miedzi 70035 + 400 000 Yang at Kowal 20016);
//   * +4 -> +6: the Zwoj Blogoslawienstwa (NORMAL_REFINE_SCROLL, value1 0 - a failure hands the piece back a level down);
//   * +6 -> +7: the Zwoj Boga Smokow (value1 10) when the bot has one, or the Podrecznik Kowala (value1 15) for +6 -> +9;
//   * neither, but a big Yang reserve for the materials and a big stock of Blessing Scrolls: the Blessing Scroll above +6.
// A step of the refine table at 100% needs no scroll (nothing can burn); every other step of such a piece without the
// policy's scroll waits - the plain anvil burned 74 Yohara pieces on 3 November (PLAYERBOT_CHI: refine BURNED, mostly
// Talizmany Woli at the 70% step) and never may again.
//
// The scroll is known by what DoRefineWithScroll reads off it (char_item.cpp): value0 the kind, value1 the percent it
// adds. The Magic Stone / Kamien Rytualny (NO_REDUCTION_WHEN_FAIL_SCROLL, value0 1) keep the level on a failure - a
// Blessing Scroll's tier at +4..+5, the Manual's at +6 and over when it adds 15. The Gwarancja (REFINE_BONUS_SCROLL,
// value0 3) burns what it fails and is never taken.
//
// No engine types. The engine side: playerbot_economy.h (FindPlayerBotHighGearScrollCell, the blacksmith pass and the
// planner), playerbot_yohara_chi.h (Mistrz Chi's anvil: jade, gloves, the Talizman Woli) and playerbot_shop_aids.h
// (Zwoj Wojny at Kowal, Magiczna Ruda Miedzi from ItemShop V3).

namespace playerbot_high_gear
{
	const int MIN_LEVEL = 100;
	// "Big Yang reserve and a big stock of Blessing Scrolls" (the owner's words): the bot may go on over +6 under
	// Blessing Scrolls with this much Yang and this many scrolls (25040 / 25041 / 76016) in the bag.
	const long long RICH_GOLD = 150000000LL;
	const int RICH_BLESSINGS = 10;
	// The plus each scroll ladder starts at.
	const int WAR_BELOW = 4;		// Zwoj Wojny: steps from +0..+3
	const int BLESSING_FROM = 4;	// Blessing: +4 -> +6
	const int DRAGON_FROM = 6;		// Boga Smokow / Podrecznik: from +6
	const int DRAGON_STEP_TO = 7;	// Boga Smokow: the +6 -> +7 step
	const int MANUAL_STEP_TO = 9;	// Podrecznik Kowala: up to +9

	enum EScrollKind
	{
		KIND_NONE = 0,
		KIND_WAR,			// value0 2
		KIND_BLESSING,		// value0 0, value1 0
		KIND_DRAGON,		// value0 0, value1 1..14 (10: Zwoj Boga Smokow)
		KIND_MANUAL,		// value0 0, value1 15+ (Podrecznik Kowala)
		KIND_KEEP,			// value0 1, value1 0 (Magiczny Kamien: keeps the level)
		KIND_KEEP_PLUS,		// value0 1, value1 15+ (Kamien Rytualny)
		KIND_COUNT
	};

	inline EScrollKind ClassifyScroll(long value0, long value1)
	{
		switch (value0)
		{
			case 2:
				return KIND_WAR;
			case 1:
				return value1 >= 15 ? KIND_KEEP_PLUS : KIND_KEEP;
			case 0:
				if (value1 <= 0)
					return KIND_BLESSING;
				return value1 >= 15 ? KIND_MANUAL : KIND_DRAGON;
			default:
				return KIND_NONE;	// 3: the Gwarancja burns what it fails
		}
	}

	inline const char* KindName(int kind)
	{
		static const char* const names[KIND_COUNT] = { "none", "war", "blessing", "dragon", "manual", "keep", "keep_plus" };
		return kind >= 0 && kind < KIND_COUNT ? names[kind] : "?";
	}

	inline bool IsRich(long long gold, int blessings)
	{
		return gold >= RICH_GOLD && blessings >= RICH_BLESSINGS;
	}

	// The rank of a scroll for the step from plus (0: not this step's scroll under the policy). rich: IsRich.
	inline int RankScroll(int plus, EScrollKind kind, bool rich)
	{
		if (kind == KIND_NONE)
			return 0;
		if (plus < WAR_BELOW)
		{
			if (kind == KIND_WAR)
				return 1000;
			// No Zwoj Wojny: a rich bot may take its Blessing Scroll on the cheap step; the rest wait for the Blacksmith.
			if (rich && (kind == KIND_BLESSING || kind == KIND_KEEP))
				return kind == KIND_KEEP ? 290 : 300;
			return 0;
		}
		if (plus < DRAGON_FROM)
		{
			if (kind == KIND_BLESSING)
				return 900;
			if (kind == KIND_KEEP)
				return 850;
			return 0;
		}
		// From +6: the Boga Smokow for the +6 -> +7 step, the Podrecznik (and the Kamien Rytualny) up to +9.
		if (plus < DRAGON_STEP_TO && kind == KIND_DRAGON)
			return 1000;
		if (plus < MANUAL_STEP_TO && (kind == KIND_MANUAL || kind == KIND_KEEP_PLUS))
			return kind == KIND_KEEP_PLUS ? 980 : 960;
		if (!rich)
			return 0;
		switch (kind)
		{
			case KIND_DRAGON: return 600;
			case KIND_BLESSING: return 500;
			case KIND_KEEP: return 450;
			case KIND_MANUAL: return 400;	// past +9 (the serpent ladder)
			case KIND_KEEP_PLUS: return 400;
			default: return 0;
		}
	}

	// Whether a step needs a scroll at all: one at the table's 100% (or more) cannot burn.
	inline bool StepNeedsScroll(int stepProb)
	{
		return stepProb < 100;
	}

	// The scroll kind the policy wants for the step from plus, for the shopping and the Blacksmith (what a bot without
	// any allowed scroll should get): War under +4, Blessing at +4..+5, Boga Smokow at +6, Podrecznik from +7.
	inline EScrollKind WantedKind(int plus)
	{
		if (plus < WAR_BELOW)
			return KIND_WAR;
		if (plus < DRAGON_FROM)
			return KIND_BLESSING;
		if (plus < DRAGON_STEP_TO)
			return KIND_DRAGON;
		return KIND_MANUAL;
	}
}

#endif
