#ifndef __INC_METIN2_PLAYERBOT_F_CENSUS_H__
#define __INC_METIN2_PLAYERBOT_F_CENSUS_H__

// MT2009_PLUS_BOT_F_CENSUS_V1 - the counters of the owner's bot list of 3 November 2026 (section F of
// poprawki-3.0.7-lista-wlasciciela-2026-11-03.md, and poprawki-3.0.8 point 3), said with the market's census
// (ReportPlayerBotMarket, playerbot_market.h) - cumulative since the core started:
//
//   loot_room_sold        drops given room by a junk sale where the bot stood (MT2009_PLUS_BOT_LOOT_YOHARA_V1)
//   plain_low_refused     plain gear under 30 and +6 a counter refused, plain_low_scrap the junk rule sold,
//   plain_low_lines       counter lines of it found for the take-off (MT2009_PLUS_BOT_PLAIN_LOW_GEAR_V1)
//   helm_shield_ranked    helmets and shields past their family's best two, helm_shield_aged held too long,
//   family_capped         other gear past its family's best two in a bag under pressure (MT2009_PLUS_BOT_HELM_SHIELD_HOLD_V1)
//   family_glut           listings marked down for their family's glut (MT2009_PLUS_BOT_FAMILY_GLUT_V1)
//   low_plus_capped       +0..+5 prices cut to plain + 50% (MT2009_PLUS_BOT_LOW_PLUS_BONUS_PRICE_V1)
//   slow_markdown         reprices past the forty percent (MT2009_PLUS_BOT_LINE_CLOCK_V1), clocks_known /
//   clocks_new            line clocks read back from ikashop_item_meta / started there
//   low_gear_spared       ordinary stones kept off outgrown low gear (MT2009_PLUS_BOT_LOW_GEAR_STONES_V1)
//   sale_refine_far       sale refines refused far under the bot's level (MT2009_PLUS_BOT_SALE_REFINE_NEAR_LEVEL_V1)
//   ds_clearly_better     dragon stone passes with a stone two grades over the worn one (MT2009_PLUS_BOT_DS_CLEARLY_BETTER_V1)
//   shield41              worn shields under 41 given way to an owned level-41 one (MT2009_PLUS_BOT_SHIELD41_V1)
//   scroll_pack           looks that wanted a scroll pack for a worn piece (MT2009_PLUS_BOT_SCROLL_PACK_V1)
//   small_developed       small pieces / the 41 helmet aimed past +4 (MT2009_PLUS_BOT_JEWEL_DEVELOP_V1)
//   m1_square             high bots' strolls on the first village's square (MT2009_PLUS_BOT_M1_SQUARE_STROLL_V1)
//   pdg_solo / pdg_far    a person's party bots' own targets in a dungeon / the instance's nearest
//                         (MT2009_PLUS_BOT_PDG_SOLO_V1)
//
// Included once, after playerbot_party_dungeon.h (the last of the counters' files).

namespace
{
	void LogPlayerBotSectionFCensus()
	{
#if defined(PLAYERBOT_ENGINE_MT2009) && defined(ENABLE_IKASHOP_RENEWAL)
		const unsigned int slowMarkdown = s_uBotOfflineSlowMarkdown;
		const unsigned int clocksKnown = s_uBotOfflineLineClockKnown, clocksNew = s_uBotOfflineLineClockNew;
#else
		const unsigned int slowMarkdown = 0, clocksKnown = 0, clocksNew = 0;
#endif
		sys_log(0, "PLAYERBOT_F: census loot_room_sold=%u plain_low_refused=%u plain_low_scrap=%u plain_low_lines=%u "
				"helm_shield_ranked=%u helm_shield_aged=%u family_capped=%u family_glut=%u low_plus_capped=%u "
				"slow_markdown=%u clocks_known=%u clocks_new=%u low_gear_spared=%u sale_refine_far=%u ds_clearly_better=%u "
				"shield41=%u scroll_pack=%u small_developed=%u m1_square=%u pdg_solo=%u pdg_far=%u valuable_kept=%u",
				s_uPlayerBotLootRoomSold, s_uPlayerBotPlainLowGearRefused, s_uPlayerBotPlainLowGearScrap,
				s_uPlayerBotPlainLowGearTakenOff, s_uPlayerBotHelmShieldRanked, s_uPlayerBotHelmShieldAged,
				s_uPlayerBotGoodsFamilyCapped, s_uPlayerBotFamilyGlutPriced, s_uPlayerBotLowPlusBonusCapped,
				slowMarkdown, clocksKnown, clocksNew,
				s_uPlayerBotLowGearStonesSpared, s_uPlayerBotSaleRefineFar, s_uPlayerBotDsClearlyBetter,
				s_uPlayerBotShield41Steps, s_uPlayerBotScrollPackWanted, s_uPlayerBotSmallPiecesDeveloped,
				s_uPlayerBotM1SquareStrolls, s_uPlayerBotPdgSoloPicks, s_uPlayerBotPdgSoloFar, s_uPlayerBotGoodsValuableKept);
	}
}

#endif
