#ifndef __INC_METIN2_PLAYERBOT_SMALL_FIXES_H__
#define __INC_METIN2_PLAYERBOT_SMALL_FIXES_H__

// MT2009_PLUS_BOT_SMALL_FIXES_V1 - the lower-priority points of the second bot analysis (the owner, 6 November 2026,
// cache/yohara/drugie-podejscie-2026-11-06-brief.md, all approved): the switches and the numbers of five small fixes,
// read here once so every file that carries one of them asks the same place.
//
//   horse   MT2009_PLUS_BOT_HORSE_AFFORD_V1 (playerbot_horse30.h): the paid trainings 1-19 at the Stajenny cost a bot
//           PLAYERBOT_HORSE_AFFORD_YANG_PCT of konie.koszt()'s yang (was a fixed 50), and the Materialy Rzemieslnicze
//           (30378) its bag lacks for the training are paid in yang at PLAYERBOT_HORSE_AFFORD_MATERIAL_YANG a piece
//           (0: never) - "Konie stoja na 10": can_advance=234 can_pay_training=11 short_goods=159 (95.168), 270 without
//           the yang and 177 without the materials (supporters). Medals stay the bag's (PLAYERBOT_HORSE_AFFORD_MEDAL_YANG,
//           0 = never paid in yang).
//   books   MT2009_PLUS_BOT_BOOK_GATE_V1 (playerbot_offline_market.h): a bot a gate holds for its skills looks for its
//           books before every other pick of the market pass, and the books of the skills nearest the gate's level
//           first ("2 umiej. na 24+" - the bots have 0 while 8 505 books stand on the counters, 95.168).
//   pets    MT2009_PLUS_BOT_PET_FEED_V1 (playerbot_newpet_bots.h): a keeper feeds its growth pet's life under
//           PLAYERBOT_NEWPET_FEED_PCT (was 30), and with no Odzywka in the bag gives it a spare weak egg - the window's own
//           feed (growth_pet::FeedLifeWithItem, +3-5% an egg); the census counts the hungry and the foodless.
//   talisman MT2009_PLUS_BOT_TALISMAN_CHEAP_V1 (playerbot_talismans.h): a talisman worker whose body armour stands at
//           PLAYERBOT_TALISMAN_CHEAP_ARMOUR_PLUS or more and whose talisman is under PLAYERBOT_TALISMAN_CHEAP_MAX_PLUS
//           gets the step's spare Talisman +0 and Ornament from the Blacksmith for PLAYERBOT_TALISMAN_CHEAP_SPARE_YANG /
//           PLAYERBOT_TALISMAN_CHEAP_ORNAMENT_YANG when its bag lacks them (vps3: 441 Talizmanow Wiatru +0, census
//           steps=0 on most cores of the test world).
//   belts   MT2009_PLUS_BOT_BELT_MATS_V1 (playerbot_mats_flow.h, playerbot_belts.h): a belt maker's metal and pearl at the
//           Dozorca for Materialy Rzemieslnicze (PLAYERBOT_BELT_SWAP_METAL_RATE / PLAYERBOT_BELT_SWAP_PEARL_RATE a piece),
//           what one attempt at its target recipe lacks - Miedz/Srebro stood at 0 on every market and the miners at 0
//           (vps3, crafts=0 on four servers); and the pouch's potion line is one throttled line with the census' count.
//
// Switches (event flags, looked at once a second): m2_bot_small_fixes_off 1 - all of it; m2_bot_horse_afford_off,
// m2_bot_book_gate_off, m2_bot_pet_feed_off, m2_bot_talisman_cheap_off, m2_bot_belt_mats_off - one part.
// The numbers: env, read once (a BOT_SMALLFIX config line at the first ask).
// Included once from playerbot_manager.cpp after playerbot_config.h, in the anonymous namespace.

namespace
{
	enum EPlayerBotSmallFix
	{
		SMALLFIX_HORSE = 0,
		SMALLFIX_BOOKS,
		SMALLFIX_PETS,
		SMALLFIX_TALISMAN,
		SMALLFIX_BELTS,
		SMALLFIX_COUNT
	};

	struct TPlayerBotSmallFixCfg
	{
		bool read;
		int horseYangPct, horseMaterialYang, horseMedalYang;
		int petFeedPct;
		int talismanArmourPlus, talismanMaxPlus, talismanSpareYang, talismanOrnamentYang;
		int beltMetalRate, beltPearlRate, beltVisitMax;
		TPlayerBotSmallFixCfg() : read(false), horseYangPct(25), horseMaterialYang(50000), horseMedalYang(0), petFeedPct(50),
				talismanArmourPlus(7), talismanMaxPlus(20), talismanSpareYang(250000), talismanOrnamentYang(100000),
				beltMetalRate(3), beltPearlRate(30), beltVisitMax(20) {}
	};
	TPlayerBotSmallFixCfg s_kPlayerBotSmallFixCfg;

	int ReadPlayerBotSmallFixEnv(const char* name, int def, int lo, int hi)
	{
		const char* v = getenv(name);
		if (!v || !*v)
			return def;
		char* end = NULL;
		const long n = strtol(v, &end, 10);
		if (end == v)
			return def;
		return (int)std::max<long>(lo, std::min<long>(hi, n));
	}

	const TPlayerBotSmallFixCfg& GetPlayerBotSmallFixCfg()
	{
		TPlayerBotSmallFixCfg& c = s_kPlayerBotSmallFixCfg;
		if (!c.read)
		{
			c.read = true;
			c.horseYangPct = ReadPlayerBotSmallFixEnv("PLAYERBOT_HORSE_AFFORD_YANG_PCT", 25, 0, 100);
			c.horseMaterialYang = ReadPlayerBotSmallFixEnv("PLAYERBOT_HORSE_AFFORD_MATERIAL_YANG", 50000, 0, 10000000);
			c.horseMedalYang = ReadPlayerBotSmallFixEnv("PLAYERBOT_HORSE_AFFORD_MEDAL_YANG", 0, 0, 100000000);
			c.petFeedPct = ReadPlayerBotSmallFixEnv("PLAYERBOT_NEWPET_FEED_PCT", 50, 1, 95);
			c.talismanArmourPlus = ReadPlayerBotSmallFixEnv("PLAYERBOT_TALISMAN_CHEAP_ARMOUR_PLUS", 7, 0, 15);
			c.talismanMaxPlus = ReadPlayerBotSmallFixEnv("PLAYERBOT_TALISMAN_CHEAP_MAX_PLUS", 20, 0, 200);
			c.talismanSpareYang = ReadPlayerBotSmallFixEnv("PLAYERBOT_TALISMAN_CHEAP_SPARE_YANG", 250000, 0, 100000000);
			c.talismanOrnamentYang = ReadPlayerBotSmallFixEnv("PLAYERBOT_TALISMAN_CHEAP_ORNAMENT_YANG", 100000, 0, 100000000);
			c.beltMetalRate = ReadPlayerBotSmallFixEnv("PLAYERBOT_BELT_SWAP_METAL_RATE", 3, 1, 1000);
			c.beltPearlRate = ReadPlayerBotSmallFixEnv("PLAYERBOT_BELT_SWAP_PEARL_RATE", 30, 1, 5000);
			c.beltVisitMax = ReadPlayerBotSmallFixEnv("PLAYERBOT_BELT_SWAP_VISIT_MAX", 20, 1, 200);
			sys_log(0, "BOT_SMALLFIX: config horse_yang_pct=%d horse_material_yang=%d horse_medal_yang=%d pet_feed_pct=%d "
					"talisman_armour_plus=%d talisman_max_plus=%d talisman_spare_yang=%d talisman_ornament_yang=%d "
					"belt_metal_rate=%d belt_pearl_rate=%d belt_visit_max=%d",
					c.horseYangPct, c.horseMaterialYang, c.horseMedalYang, c.petFeedPct, c.talismanArmourPlus,
					c.talismanMaxPlus, c.talismanSpareYang, c.talismanOrnamentYang, c.beltMetalRate, c.beltPearlRate,
					c.beltVisitMax);
		}
		return c;
	}

	// The event flags, once a second.
	bool IsPlayerBotSmallFixOn(int part)
	{
		static DWORD s_dwAt = 0;
		static bool s_abOff[SMALLFIX_COUNT] = { false, false, false, false, false };
		const DWORD now = get_dword_time();
		if (s_dwAt == 0 || now - s_dwAt >= 1000)
		{
			s_dwAt = now ? now : 1;
			quest::CQuestManager& q = quest::CQuestManager::instance();
			const bool all = q.GetEventFlag("m2_bot_small_fixes_off") != 0;
			s_abOff[SMALLFIX_HORSE] = all || q.GetEventFlag("m2_bot_horse_afford_off") != 0;
			s_abOff[SMALLFIX_BOOKS] = all || q.GetEventFlag("m2_bot_book_gate_off") != 0;
			s_abOff[SMALLFIX_PETS] = all || q.GetEventFlag("m2_bot_pet_feed_off") != 0;
			s_abOff[SMALLFIX_TALISMAN] = all || q.GetEventFlag("m2_bot_talisman_cheap_off") != 0;
			s_abOff[SMALLFIX_BELTS] = all || q.GetEventFlag("m2_bot_belt_mats_off") != 0;
		}
		return part >= 0 && part < SMALLFIX_COUNT && !s_abOff[part];
	}
}

#endif
