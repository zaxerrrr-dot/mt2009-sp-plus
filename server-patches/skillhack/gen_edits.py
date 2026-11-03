#!/usr/bin/env python3
"""gen_edits.py - writes edits.json of server-patches/skillhack (MT2009_PLUS_SKILL_HACK_V1, the skills of the other
specialisation - README.md) from the code below; the developer's tool (the apply scripts read edits.json only). Every
hook calls a free function of linux-port/overlays/playerbot/src/game/src/playerbot_skillhack.cpp (declared at the
hook, as the other patches do). Applied AFTER skill9, riposty and buffi: the hooks go in front of theirs.
    python3 gen_edits.py [<game/src dir to check the anchors against>]"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_SKILL_HACK_V1'
E = []


def edit(file, tag, old, new):
    marker = '%s (%s)' % (M, tag)
    assert marker in new, marker
    E.append({'file': file, 'marker': marker, 'old': old, 'new': new})


CS = 'char_skill.cpp'

# ---- IsLearnableSkill: the other path's skills (and its 9th) learnable while the switch is on - and NOT while it is off
# (the class-only rule let the other path's books through before). In front of Buffi's / the ripostes' / skill9's hooks.
edit(CS, 'learnable',
     'bool CHARACTER::IsLearnableSkill(DWORD dwSkillVnum) const\n{\n',
     'bool CHARACTER::IsLearnableSkill(DWORD dwSkillVnum) const\n{\n'
     '\t// MT2009_PLUS_SKILL_HACK_V1 (learnable): the other specialisation\'s skills - only while the switch m2_skill_hack is\n'
     '\t// on, for a player (not a bot), its 9th skill too (playerbot_skillhack.cpp).\n'
     '\t{\n'
     '\t\tint Skill2Learnable(const CHARACTER*, unsigned int);\n'
     '\t\tconst int r = Skill2Learnable(this, dwSkillVnum);\n'
     '\t\tif (r >= 0)\n'
     '\t\t\treturn r != 0;\n'
     '\t}\n')

# ---- CanUseSkill: use, /skillup and the attack packet's skill type - in front of skill9's hook (the other 9th skill).
edit(CS, 'can use',
     'bool CHARACTER::CanUseSkill(DWORD dwSkillVnum) const\n{\n\tif (0 == dwSkillVnum) return false;\n',
     'bool CHARACTER::CanUseSkill(DWORD dwSkillVnum) const\n{\n\tif (0 == dwSkillVnum) return false;\n'
     '\n'
     '\t// MT2009_PLUS_SKILL_HACK_V1 (can use): the other specialisation\'s skills while the switch is on (playerbot_skillhack.cpp).\n'
     '\t{\n'
     '\t\tint Skill2CanUse(const CHARACTER*, unsigned int);\n'
     '\t\tconst int r = Skill2CanUse(this, dwSkillVnum);\n'
     '\t\tif (r >= 0)\n'
     '\t\t\treturn r != 0;\n'
     '\t}\n')

# ---- IsUsableSkillMotion: the anti-cheat of the move packet (input_main.cpp "SKILL_HACK:", a disconnect) - the other
# path's motions of a learnt skill pass while the switch is on; its 9th skill's motion (9 / 24) in front of skill9's.
edit(CS, 'motion',
     'bool CHARACTER::IsUsableSkillMotion(DWORD dwMotionIndex) const\n{\n',
     'bool CHARACTER::IsUsableSkillMotion(DWORD dwMotionIndex) const\n{\n'
     '\t// MT2009_PLUS_SKILL_HACK_V1 (motion): the other specialisation\'s learnt skills move without the cheat kick while the\n'
     '\t// switch is on - its 9th skill\'s motion here, its other skills\' job group in the loop below (playerbot_skillhack.cpp).\n'
     '\tint Skill2NinthMotion(const CHARACTER*, unsigned int);\n'
     '\tbool Skill2MotionGroup(const CHARACTER*, unsigned int);\n'
     '\t{\n'
     '\t\tconst int r = Skill2NinthMotion(this, dwMotionIndex);\n'
     '\t\tif (r >= 0)\n'
     '\t\t\treturn r != 0;\n'
     '\t}\n')

edit(CS, 'motion group',
     '\t\t\tif (0 == eachJobGroup || eachJobGroup == selfJobGroup)\n',
     '\t\t\t// MT2009_PLUS_SKILL_HACK_V1 (motion group): the other specialisation\'s group too (the level check stays).\n'
     '\t\t\tif (0 == eachJobGroup || eachJobGroup == selfJobGroup || Skill2MotionGroup(this, eachJobGroup))\n')

# ---- login: the client's state ("SKILL2 1|0", the levels again for its new slots; quick slots cleared when off)
edit('input_login.cpp', 'login',
     '\t{ void BuffiOnLogin(LPCHARACTER); BuffiOnLogin(ch); }\n',
     '\t{ void BuffiOnLogin(LPCHARACTER); BuffiOnLogin(ch); }\n'
     '\t// MT2009_PLUS_SKILL_HACK_V1 (login): the other specialisation\'s tab on or off in the client (playerbot_skillhack.cpp).\n'
     '\t{ void Skill2OnLogin(CHARACTER*); Skill2OnLogin(ch); }\n')

# ---- the live switch: /e m2_skill_hack, the panel (web_admin.quest SKILL2) - every player online told at once
QM = 'questmanager.cpp'
edit(QM, 'decl',
     '#include "questmanager.h"\n',
     '#include "questmanager.h"\n'
     '// MT2009_PLUS_SKILL_HACK_V1 (decl): playerbot_skillhack.cpp, a global function (declared at file scope - an extern\n'
     '// inside CQuestManager::SetEventFlag would name quest::Skill2FlagChanged).\n'
     'void Skill2FlagChanged(int iValue, int iPrev);\n')

edit(QM, 'flag',
     '\t\tm_mapEventFlag[name] = value;\n',
     '\t\tm_mapEventFlag[name] = value;\n'
     '\n'
     '\t\t// MT2009_PLUS_SKILL_HACK_V1 (flag): the other specialisation\'s skills switched live - the players online told.\n'
     '\t\tif (name == "m2_skill_hack")\n'
     '\t\t\t::Skill2FlagChanged(value, prev_value);\n')


def check(src):
    texts = {}
    for e in E:
        p = os.path.join(src, e['file'])
        if p not in texts:
            texts[p] = open(p, 'rb').read().decode('latin-1')
        t = texts[p]
        if e['marker'] in t:
            print('present', e['marker'])
            continue
        n = t.count(e['old'].replace('\n', '\r\n')) or t.count(e['old'])
        assert n == 1, (e['file'], e['marker'], n)
    print('anchors ok:', len(E))


if __name__ == '__main__':
    json.dump(E, open(os.path.join(HERE, 'edits.json'), 'w'), indent=2)
    print('edits.json: %d edit(s)' % len(E))
    if len(sys.argv) > 1:
        check(sys.argv[1])
