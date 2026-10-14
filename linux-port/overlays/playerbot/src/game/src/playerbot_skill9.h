// MT2009_PLUS_SKILL9_V1: the 9th skills of Yohara (server-patches/skill9/README.md) - one per class and
// specialisation, skill_proto 176-182 (yskill9.sql), learnt only from their books 50569-50575 by a Champion:
//   176 Trzesienie      Wojownik (both)    melee, a line of blows forward
//   177 Swiatlo Gwiazd  Ninja (sztylety)   shot (stars), splash around the target
//   178 Strzal Wichury  Ninja (luk)        arrow shot, splash
//   179 Piekielny Cios  Sura (bron)        melee
//   180 Fala Smierci    Sura (cz. magia)   magic shot, splash
//   181 Meteor          Szaman (smok)      at the target at once (Owsap: computed on use), splash, fire
//   182 Tarcza Eteru    Szaman (leczenie)  party buff: every 12 s a chance of a few seconds' protection
// (Burza Szponow 183 is the Lycan's - we have no Lycan.) Books: Champion level 1+, 2 000 Champion experience a
// read below M1 and 5 000 from M1 to G1 (the books' item_proto value1/value2 of the GF client, the en/tr/de wikis;
// the pl wiki's older text says 20 000), from 0 a level per successful read (no skill points; at 17-19 the classic
// roll for M), M1 -> G1 as every skill's books, G1 -> P
// with Soul Stones (the quest training_grandmaster_skill offers the 9th skill too, game/quest/skill9.lua).
// New file outside the engine's own; the engine's hooks are server-patches/skill9 (edits.json) and call the
// free functions below (declared again at each hook, as the other patches do).
#ifndef MT2009_PLAYERBOT_SKILL9_H
#define MT2009_PLAYERBOT_SKILL9_H

class CHARACTER;
class CAffect;

namespace skill9
{
	// The protection of Tarcza Eteru (Owsap's AFFECT_CHEONUN_INVINCIBILITY): blocks every blow while it lasts.
	const unsigned int AFFECT_CHEONUN_INVINCIBILITY = 608;
	// What a read of a 9th skill's book costs in Champion experience: below M1 / from M1 (the books' value1 and
	// value2 in the GF item_proto, 2000 / 5000; the en and tr wikis say the same).
	const unsigned int BOOK_CHAMPION_EXP_NORMAL = 2000;
	const unsigned int BOOK_CHAMPION_EXP_MASTER = 5000;
	unsigned int BookCost(unsigned int bSkillLevel);
	// Tarcza Eteru rolls its chance every 12 seconds (the wiki: "Chroni co 12 sekund").
	const int CHEONUN_PERIOD_SEC = 12;

	bool IsNinth(unsigned int dwVnum);
	// The 9th skill of a class and its specialisation (skill group 1/2); 0 none.
	unsigned int SkillFor(unsigned char bJob, unsigned char bGroup);
	// Its motion in the skill motions' table (skilldesc's motion column): 9 = the first group's slot 9,
	// 24 = the second group's (the grades add 25 each).
	unsigned int MotionBase(unsigned int dwVnum);
	// Seconds of protection for a chance of Tarcza Eteru (4*k against 0.4*k+18*k, the skill's two polys).
	int CheonunProtectSeconds(int iChance);
}

// The hooks (server-patches/skill9/edits.json):
int Skill9Learnable(const CHARACTER* ch, unsigned int dwVnum);      // IsLearnableSkill: -1 not a 9th skill
int Skill9BookCheck(CHARACTER* ch, unsigned int dwVnum);            // LearnSkillByBook: 0 refuse (told why)
void Skill9BookPay(CHARACTER* ch, unsigned int dwVnum);             // LearnSkillByBook: the read's price
int Skill9CanUse(const CHARACTER* ch, unsigned int dwVnum);         // CanUseSkill: -1 not a 9th skill
int Skill9UsableMotion(const CHARACTER* ch, unsigned int dwMotion); // IsUsableSkillMotion: -1 not its motion
void Skill9ComputeAffect(CHARACTER* ch, const CAffect* pkAff, bool bAdd);
void Skill9RemoveAffects(CHARACTER* ch);                            // RemoveSkillAffect
int Skill9Blocked(CHARACTER* victim, CHARACTER* attacker);          // Damage: 1 the blow is blocked
unsigned int Skill9MeleeReach(unsigned int dwVnum);                 // GetMeleeSkillDistanceAttack: 0 default

#endif
