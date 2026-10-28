#!/usr/bin/env python3
"""gen_edits.py - writes edits.json of server-patches/guildsys (MT2009_PLUS_GUILDSYS_V1, the guild system update:
guild levels to 40, Balathor's guild skills 158-160 and their books, the guild's and the members' dates for the
Balathor port) from the code below; the developer's tool (the apply scripts read edits.json only). The logic is
linux-port/overlays/playerbot/src/game/src/guildsys.cpp (declared at each hook, as the other patches do).
    python3 gen_edits.py [<game/src dir to check the anchors against>]"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_GUILDSYS_V1'
E = []


def edit(file, tag, old, new):
    marker = '%s (%s)' % (M, tag)
    assert marker in new, marker
    E.append({'file': file, 'marker': marker, 'old': old, 'new': new})


# ---- common/length.h: the guild's last level (GUILD_NEW_LEVEL_40)
edit('../../common/length.h', 'max level',
     '\tGUILD_MAX_LEVEL = 20,\n',
     '\t// MT2009_PLUS_GUILDSYS_V1 (max level): guilds level to 40 (server-patches/guildsys; Guild Systems by Nazox,\n'
     '\t// GUILD_NEW_LEVEL_40) - guild_exp_table (constants.cpp) and the db core\'s c_aiScoreByLevel have 41 rows.\n'
     '\tGUILD_MAX_LEVEL = 40,\n')

# ---- game constants.cpp: the experience a level needs, 20 -> 21 ... 39 -> 40; index 40 stays the engine's
# "at the last level" bound (CGuild::GuildPointChange empties the experience when it is reached)
rows = ''.join('\t%dUL,\t// %d -> %d\n' % (10500000 + (lv - 20) * 500000, lv, lv + 1) for lv in range(20, 40))
edit('constants.cpp', 'exp table',
     '\t10000000UL,\n\t42000000UL\n};',
     '\t10000000UL,\n'
     '\t// MT2009_PLUS_GUILDSYS_V1 (exp table): levels 21-40 (GUILD_MAX_LEVEL 40; the client\'s exe table is the same,\n'
     '\t// client-patches/exe UserInterface/Locale.cpp). 10.5 M at 20 -> 21, +0.5 M a level, 20 M at 39 -> 40.\n'
     + rows +
     '\t42000000UL\t// 40: the last level\n};')

# ---- db GuildManager.cpp: a guild level's war ladder score to 40 (the 21 rows had zeros after 20)
score = ''.join('\t%d,\t// %d\n' % (60000 + (lv - 21) * 5000, lv) for lv in range(21, 41))
edit('../../db/src/GuildManager.cpp', 'ladder',
     '\t50000,\n\t55000,\n};',
     '\t50000,\n\t55000,\n'
     '\t// MT2009_PLUS_GUILDSYS_V1 (ladder): levels 21-40 (GUILD_MAX_LEVEL 40), +5000 a level.\n'
     + score + '};')

# ---- guild.h: guildsys.cpp's access to the skill array, the points and the online members
edit('guild.h', 'friend',
     'class CGuild\n{\n\tpublic:\n',
     'class CGuild\n{\n'
     '\t// MT2009_PLUS_GUILDSYS_V1 (friend): Balathor\'s skill books and the forget book change the skills without a\n'
     '\t// skill point (guildsys.cpp GuildSysAccess).\n'
     '\tfriend struct GuildSysAccess;\n\n'
     '\tpublic:\n')

G = 'guild.cpp'
# ---- the member limit grows only to level 20 (as before the 40 levels: 48 + 4 a level = 124)
edit(G, 'members',
     '\treturn 48 + 4 * (m_data.level-1) + m_iMemberCountBonus;',
     '\t// MT2009_PLUS_GUILDSYS_V1 (members): levels 21-40 add no member places (guildsys.h GUILDSYS_MAX_MEMBER_LEVEL).\n'
     '\treturn 48 + 4 * (MIN((int)m_data.level, 20) - 1) + m_iMemberCountBonus;')

# ---- UseSkill: the Balathor lair is a place for guild skills too
edit(G, 'arena',
     '\tif (ch && !CWarMapManager::instance().IsWarMap(ch->GetMapIndex()))\n',
     '\t// MT2009_PLUS_GUILDSYS_V1 (arena): guild skills work in the Balathor lair (map 420 and its copies) as well.\n'
     '\tbool GuildSysSkillMapAllowed(long lMapIndex);\n'
     '\tif (ch && !CWarMapManager::instance().IsWarMap(ch->GetMapIndex()) && !GuildSysSkillMapAllowed(ch->GetMapIndex()))\n')

# ---- UseSkill: Balathor's skills and every skill in the lair (after the SP / cool-down checks)
edit(G, 'use',
     '\tswitch (dwVnum)\n\t{\n\t\tcase GUILD_SKILL_TELEPORT:',
     '\t// MT2009_PLUS_GUILDSYS_V1 (use): Balathor\'s guild skills (158-160: immunities) and every guild skill in the\n'
     '\t// Balathor lair (no war needed there; the members on the caster\'s map) - guildsys.cpp. The rest as before.\n'
     '\t{\n'
     '\t\tbool GuildSysUseSkill(CGuild*, CHARACTER*, unsigned int, int);\n'
     '\t\tif (GuildSysUseSkill(this, ch, dwVnum, iNeededSP))\n'
     '\t\t\treturn;\n'
     '\t}\n\n'
     '\tswitch (dwVnum)\n\t{\n\t\tcase GUILD_SKILL_TELEPORT:')

# ---- SkillLevelUp: 158-160 only from their books
edit(G, 'points',
     '\tif (m_data.abySkill[dwRealVnum] >= pkSk->bMaxLevel)\n\t\treturn;\n\n\tif (m_data.skill_point <= 0)\n\t\treturn;',
     '\tif (m_data.abySkill[dwRealVnum] >= pkSk->bMaxLevel)\n\t\treturn;\n\n'
     '\t// MT2009_PLUS_GUILDSYS_V1 (points): Balathor\'s guild skills (158-160) rise only by their books (guildsys.cpp).\n'
     '\t{\n'
     '\t\tbool GuildSysBookOnlySkill(unsigned int);\n'
     '\t\tif (GuildSysBookOnlySkill(dwVnum))\n'
     '\t\t\treturn;\n'
     '\t}\n\n'
     '\tif (m_data.skill_point <= 0)\n\t\treturn;')

# ---- char_item.cpp USE_SPECIAL: the books 50344-50347
NPCLOC = '\t\t\t\t\t\t\t// MT2009_PLUS_NPC_LOCATION_HELPER_V1 (use): Lokalizator NPC (79667)'
edit('char_item.cpp', 'books',
     NPCLOC,
     '\t\t\t\t\t\t\t// MT2009_PLUS_GUILDSYS_V1 (books): Ksiega Burzy / Woli / Nieugietosci Balathora (50344-50346, +1 level\n'
     '\t\t\t\t\t\t\t// of the guild skill 158-160) and Ksiega Zapomnienia Gildii (50347, the points of 151-157 back) - the\n'
     '\t\t\t\t\t\t\t// guild leader\'s (guildsys.cpp).\n'
     '\t\t\t\t\t\t\tcase 50344:\n'
     '\t\t\t\t\t\t\tcase 50345:\n'
     '\t\t\t\t\t\t\tcase 50346:\n'
     '\t\t\t\t\t\t\tcase 50347:\n'
     '\t\t\t\t\t\t\t\t{\n'
     '\t\t\t\t\t\t\t\t\tbool GuildSysUseItem(CHARACTER*, CItem*);\n'
     '\t\t\t\t\t\t\t\t\tif (!GuildSysUseItem(this, item))\n'
     '\t\t\t\t\t\t\t\t\t\treturn false;\n'
     '\t\t\t\t\t\t\t\t}\n'
     '\t\t\t\t\t\t\t\tbreak;\n'
     + NPCLOC)

# ---- char_resist.cpp IsImmune: Burza (stun, slow), Wola (stun, root), Nieugietosc (fall)
edit('char_resist.cpp', 'immune',
     'bool CHARACTER::IsImmune(DWORD dwImmuneFlag, LPCHARACTER pkAttacker)\n{\n',
     'bool CHARACTER::IsImmune(DWORD dwImmuneFlag, LPCHARACTER pkAttacker)\n{\n'
     '\t// MT2009_PLUS_GUILDSYS_V1 (immune): Balathor\'s guild skills\' affects - 10 % a skill level (guildsys.cpp).\n'
     '\t{\n'
     '\t\tbool GuildSysIsImmune(CHARACTER*, unsigned int);\n'
     '\t\tif (GuildSysIsImmune(this, dwImmuneFlag))\n'
     '\t\t\treturn true;\n'
     '\t}\n')

# ---- char_battle.cpp IsResistPush: Nieugietosc Balathora (the skills' crush and the archer's knock-back)
edit('char_battle.cpp', 'push',
     'bool CHARACTER::IsResistPush()\n{\n',
     'bool CHARACTER::IsResistPush()\n{\n'
     '\t// MT2009_PLUS_GUILDSYS_V1 (push): Nieugietosc Balathora, 10 % a skill level (guildsys.cpp).\n'
     '\t{\n'
     '\t\tbool GuildSysResistPush(CHARACTER*);\n'
     '\t\tif (GuildSysResistPush(this))\n'
     '\t\t\treturn true;\n'
     '\t}\n')

# ---- questlua_guild.cpp: the quest functions (guildsys.cpp)
Q = 'questlua_guild.cpp'
FUNCS = [('get_level', 'guildsys_get_level'), ('create_time', 'guildsys_create_time'), ('age', 'guildsys_age'),
         ('member_join_time', 'guildsys_member_join_time'), ('member_age', 'guildsys_member_age'),
         ('get_bank', 'guildsys_get_bank'), ('check_requirements', 'guildsys_check_requirements')]
edit(Q, 'declare',
     '\tvoid RegisterGuildFunctionTable()\n\t{\n',
     '\t// MT2009_PLUS_GUILDSYS_V1 (declare): the guild\'s level, dates, treasury and the Balathor registration check\n'
     '\t// (guildsys.cpp; server-patches/guildsys/README.md).\n'
     + ''.join('\tint %s(lua_State* L);\n' % c for n, c in FUNCS) +
     '\n\tvoid RegisterGuildFunctionTable()\n\t{\n')
LIST_OLD = '\t\t\t{ "get_rank",\t\t\t\tguild_get_rank\t\t\t\t},\n'
edit(Q, 'list',
     LIST_OLD,
     LIST_OLD +
     '\t\t\t// MT2009_PLUS_GUILDSYS_V1 (list): guild.get_level(), guild.create_time(), guild.age(),\n'
     '\t\t\t// guild.member_join_time([pid]), guild.member_age([pid]), guild.get_bank(),\n'
     '\t\t\t// guild.check_requirements(min_level, min_guild_hours, min_member_hours, min_bank).\n'
     + ''.join('\t\t\t{ "%s",%s%s\t},\n' % (n, '\t' * max(1, (28 - len(n) - 4) // 4 + 1), c) for n, c in FUNCS))


def main():
    out = os.path.join(HERE, 'edits.json')
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(E, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('%d edit(s) -> %s' % (len(E), out))
    if len(sys.argv) > 1:
        bad = 0
        texts = {}
        for e in E:
            p = os.path.join(sys.argv[1], e['file'])
            if p not in texts:
                texts[p] = open(p, 'rb').read().decode('latin-1').replace('\r\n', '\n')
            t = texts[p]
            if e['marker'] in t:
                print('  already there: %s' % e['marker'])
            elif t.count(e['old']) != 1:
                bad += 1
                print('  ANCHOR x%d: %s %s' % (t.count(e['old']), e['file'], e['marker']))
        print('anchors: %s' % ('OK' if not bad else '%d bad' % bad))
        sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
