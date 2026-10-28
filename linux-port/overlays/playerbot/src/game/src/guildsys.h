#ifndef __INC_METIN2_GUILDSYS_H__
#define __INC_METIN2_GUILDSYS_H__

// MT2009_PLUS_GUILDSYS_V1 - the guild system update (server-patches/guildsys/README.md), on the Guild Systems
// package compiled by Nazox (GitHub "Guild-Systems": GUILD_NEW_LEVEL_40, GUILD_SKILLBOOK and the join date of
// GUILD_DONATE_ATTENDANCE; the other modules of the package are not ported - the README says why), made for the
// guild White Dragon lair (Balathor, claude/y-balathor):
//
//  - guild levels 1-40 (common/length.h GUILD_MAX_LEVEL, constants.cpp guild_exp_table, db GuildManager.cpp
//    c_aiScoreByLevel); the member limit still grows only to level 20 (48 + 4 per level, as before);
//  - the three guild skills of Balathor on the free places 158-160 of the guild skill array (GF's vnums:
//    158 Burza, 159 Wola, 160 Nieugietosc Balathora; skill_proto rows in guildsys.sql), learned only from their
//    books 50344-50346 (the guild leader reads one: +1 level, at most 10), never with guild skill points;
//  - Ksiega Zapomnienia Gildii (50347): the leader gets back every point spent on the skills 151-157;
//  - the guild's creation time (player.guild.create_time) and every member's join time
//    (player.guild_member.join_time) - INVISIBLE columns of guildsys.sql, filled by the database itself;
//  - guild skills work in the Balathor lair (map 420 and its instances) without a war; elsewhere as before (the
//    guild war arena while at war).
//
// Everything a Balathor port needs from the guild is here - the quest functions (questlua_guild.cpp list:
// guild.get_level, guild.create_time, guild.age, guild.member_join_time, guild.member_age, guild.get_bank,
// guild.check_requirements) and the C++ ones below.

class CHARACTER;
class CItem;
class CGuild;

enum EGuildSys
{
	GUILDSYS_MAX_MEMBER_LEVEL = 40,		// the member limit grows with the level up to this one (4 a level; 204 at 40)

	GUILDSYS_SKILL_STORM = 158,			// Burza Balathora - stun and slow
	GUILDSYS_SKILL_WILL = 159,			// Wola Balathora - stun, chains (root) and Balathor's freeze
	GUILDSYS_SKILL_FIRMNESS = 160,		// Nieugietosc Balathora - knock-back and knock-down
	GUILDSYS_SKILL_MAX_LEVEL = 10,

	GUILDSYS_BOOK_STORM = 50344,
	GUILDSYS_BOOK_WILL = 50345,
	GUILDSYS_BOOK_FIRMNESS = 50346,
	GUILDSYS_BOOK_FORGET = 50347,

	GUILDSYS_BALATHOR_MAP = 420,		// metin2_map_guild_whitedragon_boss (mods-incoming/balathor/README.md)

	// GuildSysIsImmune's own flag for Balathor's freeze (its polymorph into an ice crystal) - the engine's
	// IMMUNE_* flags end at 1 << 7.
	GUILDSYS_IMMUNE_FREEZE = 1 << 20,
};

// the guild White Dragon lair: map 420 or one of its private copies (index / 10000 == 420)
bool GuildSysIsBalathorMap(long lMapIndex);
// a guild skill may be used here without a guild war (CGuild::UseSkill's arena check)
bool GuildSysSkillMapAllowed(long lMapIndex);
// 158-160: raised only by their books (CGuild::SkillLevelUp refuses a skill point)
bool GuildSysBookOnlySkill(unsigned int dwVnum);
// CGuild::UseSkill after the SP and the cool-down checks: true = handled here (Balathor's skills anywhere they
// are allowed, every guild skill in the lair), false = the engine's own switch
bool GuildSysUseSkill(CGuild* pGuild, CHARACTER* ch, unsigned int dwVnum, int iNeededSP);
// the books 50344-50347 (char_item.cpp USE_SPECIAL); true = used up one
bool GuildSysUseItem(CHARACTER* ch, CItem* item);
// CHARACTER::IsImmune / IsResistPush: a Balathor skill's affect on the character (chance = 10 % a skill level)
bool GuildSysIsImmune(CHARACTER* ch, unsigned int dwImmuneFlag);
bool GuildSysResistPush(CHARACTER* ch);

// unix times (0 = before guildsys.sql: an old guild / member); the guild's from its row (cached), the member's from
// guild_member (asked each time: a member who left and came back has a new one). A row not there yet (the db core
// writes the member's a moment after the join) counts as "now".
unsigned int GuildSysCreateTime(CGuild* pGuild);
unsigned int GuildSysMemberJoinTime(CGuild* pGuild, unsigned int dwPID);

// Balathor's registration (wiki): 0 OK, 1 no guild, 2 guild level < iMinLevel, 3 guild younger than
// iMinGuildHours, 4 the character in the guild shorter than iMinMemberHours, 5 the treasury (what may be spent)
// < llMinBank
int GuildSysCheckRequirements(CHARACTER* ch, int iMinLevel, int iMinGuildHours, int iMinMemberHours, long long llMinBank);

#endif
