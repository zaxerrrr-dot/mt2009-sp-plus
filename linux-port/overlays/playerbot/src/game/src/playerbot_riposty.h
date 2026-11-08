// MT2009_PLUS_RIPOSTY_V1: Riposty i Dopalacze - the passive 7th and 8th skills of every character (pl-wiki
// "Umiejetnosci - Riposty i Dopalacze"; server-patches/riposty/README.md). GF's vnums (Owsap's SKILL_ANTI_* / SKILL_HELP_*,
// skill_proto riposty_skill.sql, type 6 - their points are the class skills' points):
//   Riposta  221 Wir Miecza  222 Zasadzka  223 Uderzenie Palcem  224 Strzelajacy Smok  225 Duchowe Uderzenie
//            226 Ognista Strzala  227 Mroczne Uderzenie  228 Przywolanie Blyskawicy  (229 Wilczy Dech - no Lycan)
//            - fewer damage taken from that skill; ONE riposte a character, chosen with Podrecznik: Riposta (50515).
//   Dopalacz 236-243, the same skills in the same order - more damage done with it; the class and specialisation's
//            own (Body: Wir Miecza, Mental: Duchowe Uderzenie, Dagger: Zasadzka, Archer: Ognista Strzala, Sura WP:
//            Uderzenie Palcem, BM: Mroczne Uderzenie, Smok: Strzelajacy Smok, Healer: Przywolanie Blyskawicy),
//            learnt with Podrecznik: Dopalacz (50514) once a riposte is P.
// Both from level 5 with a specialisation chosen; 1 -> M1 with the class skill points (sure; at 17-20 the classic roll for
// M) or their books (50516-50523 / 50560-50567, 35% a read, not sure), M1 -> G1 their books, G1 -> P Kamien Duchowy+
// (50525, quest riposty). The wiki's values: riposte 1.2% / M1 12% / G1 19.7% / P 30% (24*k), boost 0.8 / 8 / 13.1 /
// 20% (16*k), k = the skill power of the level (GF's table, below) / 100. Zwoj Zmiany Treningu (71000) removes both
// and gives their skill points back; a skill reset keeps them (only their points stay spent).
#ifndef MT2009_PLAYERBOT_RIPOSTY_H
#define MT2009_PLAYERBOT_RIPOSTY_H

class CHARACTER;

namespace riposty
{
	const unsigned int RIPOSTE_FIRST = 221, RIPOSTE_LAST = 228;
	const unsigned int BOOST_FIRST = 236, BOOST_LAST = 243;
	const unsigned int ITEM_MANUAL_BOOST = 50514, ITEM_MANUAL_RIPOSTE = 50515, ITEM_RESET = 71000;
	const unsigned int ITEM_SOUL_STONE_PLUS = 50525;	// Kamien Duchowy+ (G1 -> P)

	bool IsRiposte(unsigned int dwVnum);
	bool IsBoost(unsigned int dwVnum);
	bool IsPassive(unsigned int dwVnum);
	// The boost of a class and its specialisation (skill group 1/2); 0 none.
	unsigned int BoostFor(unsigned char bJob, unsigned char bGroup);
	// The riposte / boost a character knows (level > 0); 0 none.
	unsigned int RiposteOf(const CHARACTER* ch);
	unsigned int BoostOf(const CHARACTER* ch);
	// Per cent (riposte: damage taken less, boost: damage done more) at a skill level 0-40 - the wiki's values.
	double Percent(unsigned int dwVnum, int iLevel);
	// pc.learn_passive_skill: 0 learnt (level 1), 1 no specialisation, 2 level below 5, 3 one known already,
	// 4 a boost wants a riposte at P, 5 not a passive skill or not this class's boost.
	int Learn(CHARACTER* ch, unsigned int dwVnum);
	// Zwoj Zmiany Treningu: every riposte and boost to 0, their skill points back; how many were known.
	int ResetAll(CHARACTER* ch);
	// MT2009_PLUS_RIPOSTY_V2: "Riposta: Wir Miecza" / "Dopalacz: Wir Miecza" (ASCII, for the bots' chat); NULL other.
	const char* Name(unsigned int dwVnum);
	// MT2009_PLUS_RIPOSTY_V2 (bots): the riposte a bot chooses - against the path met most among the other kingdoms'
	// characters online (a weighted draw), by its pid when nobody is online.
	unsigned int BotChoice(const CHARACTER* ch);
}

#endif
