// MT2009_PLUS_SKILL_HACK_V1: the skills of the other specialisation (server-patches/skillhack/README.md).
// The owner (3 November 2026): "a warrior body may use the skills of warrior mental too - Aura Miecza and Duchowe
// Uderzenie on one character, a dragon shaman may have Leczenie. The client opens a second skill tab and the skills
// grow as usual 1-17, M1-M10, G1-P. Switched on in .env, off by default. The bots do not use it."
//
// The decisions (4 November 2026, PLAN-SKILL-HACK.md section 11):
//   - the player picks the main path as before (level 5); the other path is simply additional, shown on the skill
//     window's second tab under that path's own name (no special name);
//   - one pool of skill points, exactly as now (the other path's skills take the same POINT_SKILL);
//   - no PvP limits, no power cut, every grade up to P;
//   - the other path's 9th skill is available too (Ninja 177/178, Sura 179/180, Szaman 181/182; the Warrior's 176
//     is one skill for both);
//   - switched off: the other path's skills sleep (their levels stay, they cannot be used, learnt or forgotten, the
//     client hides them) and the quick slots holding them are cleared;
//   - the boost (Dopalacz 236-243) and Seon-Hae's book exchange stay with the main path; Soul Stones (G1 -> P) and
//     Mikstura Talentu work for the other path's skills like for the own (quests training_grandmaster_skill,
//     mikstura_talentu read the event flag);
//   - from level 5 (a chosen path); a GM switches it live: the event flag m2_skill_hack (/e m2_skill_hack 0|1, the
//     panel's .env page; mariadb/playerbot/apply.sh writes it from M2_SKILL_HACK at a start).
// Players only: the bots, their companions and Buffi never (a PC with a player's own connection).
// In the code and the logs "SKILL2" - "SKILL_HACK:" in the hack log stays the cheat detection of input_main.cpp.
#ifndef MT2009_PLAYERBOT_SKILLHACK_H
#define MT2009_PLAYERBOT_SKILLHACK_H

class CHARACTER;

namespace skill2
{
	// The world switch: the event flag m2_skill_hack (non-zero = on).
	bool Enabled();
	// A player's own character with a chosen path of the four classes (not a bot, a companion or Buffi).
	bool Applies(const CHARACTER* ch);
	// The skill belongs to the character's OTHER path (its 1-6 or its 9th skill) - whatever the switch.
	bool IsForeign(const CHARACTER* ch, unsigned int dwVnum);
	// The client's state: "SKILL2 1|0" (game.py -> skillhack.py), quick slots of the other path cleared when off.
	void SendState(CHARACTER* ch, bool bResendLevels);
}

// The hooks (server-patches/skillhack/edits.json), -1 = "not mine, the engine's own rule":
int Skill2Learnable(const CHARACTER* ch, unsigned int dwVnum);        // IsLearnableSkill
int Skill2CanUse(const CHARACTER* ch, unsigned int dwVnum);           // CanUseSkill
int Skill2NinthMotion(const CHARACTER* ch, unsigned int dwMotion);    // IsUsableSkillMotion: the other 9th skill
bool Skill2MotionGroup(const CHARACTER* ch, unsigned int dwJobGroup); // IsUsableSkillMotion: the other path's group
void Skill2OnLogin(CHARACTER* ch);                                    // input_login.cpp
void Skill2FlagChanged(int iValue, int iPrev);                        // CQuestManager::SetEventFlag

#endif
