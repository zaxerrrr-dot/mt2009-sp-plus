// MT2009_PLUS_BONUS67_V1: the 6th/7th bonuses of the wiki ("6. i 7. bonus") the engine lacked - the owner, 20 October
// 2026: "add them" (server-patches/bonusy67/README.md). Points 198-251 after POINT_HIT_PCT (common/length.h, the
// bonusy67 edit "points"); an item keeps them as any other bonus (the type is one byte: 252 of 256 used). None of
// them goes to the client as a point (the Yohara exe has POINT_MAX_NUM 198) - the item tooltip names them
// (root/localeinfo_point.py).
//   * HIT_BUFF_ENCHANT_* / HIT_BUFF_RESIST_* (198-209): a blow dealt (power) or taken (resistance) gives the element's
//     power / resistance for x seconds (b67_hitbuff_value, default 10; again after b67_hitbuff_cooldown, 15 s);
//   * *_PER_* (210-231): +x% of the character's whole total of that bonus (attack bonus against a race, element
//     power, resistance) - read where the bonus is used (Bonus67Total), never added to the point itself;
//   * *_BOSS_OR_MORE (232-235): normal hits / skills against a boss and from a boss (not Metin stones);
//   * FIRST..FIFTH_ATTRIBUTE_BONUS (236-240): the item's own 1st..5th normal bonus is worth x% more;
//   * the gloves' lines (241-251): fall resistance in combat (60 s cooldown), the lightning on the monsters around
//     (15 s cooldown), a 5 s shorter next cooldown of a champion skill, the glove's built-in Will line +x%.
// The engine's hooks are the edits of server-patches/bonusy67 - each declares the function it calls with the same
// signature as here (a mismatch does not link; BYTE is unsigned char, DWORD unsigned int).
#ifndef MT2009_PLUS_PLAYERBOT_BONUS67_H
#define MT2009_PLUS_PLAYERBOT_BONUS67_H

class CHARACTER;
class CItem;
typedef CHARACTER* LPCHARACTER;
typedef CItem* LPITEM;

// A bonus's total as the character uses it: the point, the hit buff of that point (an element power / resistance
// for a few seconds) and its "+x% of the total" line. Any other point: GetPoint.
int Bonus67Total(const CHARACTER* ch, unsigned char bPoint);
// battle.cpp CalcAttBonus: the race bonus total (iPointValue) against pkVictim with the attacker's *_PER_* lines.
int Bonus67AttBonus(LPCHARACTER pkAttacker, LPCHARACTER pkVictim, int iPointValue);
// CHARACTER::Damage (after the normal hit / skill bonuses): the boss lines; it starts the hit buffs, the gloves'
// fall resistance and lightning. iType is EDamageType.
int Bonus67Damage(LPCHARACTER pkVictim, LPCHARACTER pkAttacker, int iType, int iDam);
// CHARACTER::IsResistPush: the gloves' fall resistance is on.
bool Bonus67FallResist(const CHARACTER* ch);
// CHARACTER::UseSkill (after the cooldown is set): the gloves' 5 s shorter next cooldown of a champion skill - the
// new next usable time (and the client's cooldown ended then).
unsigned int Bonus67SkillCooldown(LPCHARACTER ch, unsigned int dwVnum, unsigned int dwNextUsable);
// CItem::ModifyPoints: an attribute slot's value as worn (FIRST..FIFTH_ATTRIBUTE_BONUS; the glove's Will is its base
// attribute since MT2009_PLUS_GLOVE_BASE_V1 - playerbot_yohara_gear.cpp Mt2009GloveBaseWill).
int Bonus67AttrValue(LPITEM item, int iSlot, unsigned char bType, int iValue);
// CItem::AddRareAttribute(2) / ChangeRareAttribute(2) on a glove: its 6th and 7th slots from the pool's glove column
// (MT2009_PLUS_GLOVE_BASE_V1: an addition fills the first free one, a change rolls the lines it has again). iMode 0 add
// (the panel's level odds), 1 add2 (aiPct), 2 change, 3 change2. -1: not a glove.
int Bonus67GloveRare(LPITEM item, int iMode, const int* aiPct);

#endif
