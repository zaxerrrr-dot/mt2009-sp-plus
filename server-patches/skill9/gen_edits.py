#!/usr/bin/env python3
"""gen_edits.py - writes edits.json of server-patches/skill9 (MT2009_PLUS_SKILL9_V1, the 9th skills of Yohara) from
the code below; the developer's tool (the apply scripts read edits.json only). Every hook calls a free function of
linux-port/overlays/playerbot/src/game/src/playerbot_skill9.cpp (declared at the hook, as the other patches do).
    python3 gen_edits.py [<game/src dir to check the anchors against>]"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_SKILL9_V1'
E = []


def edit(file, tag, old, new):
    marker = '%s (%s)' % (M, tag)
    assert marker in new, marker
    E.append({'file': file, 'marker': marker, 'old': old, 'new': new})


# ---- common/skill_length.h: the vnums (Owsap's names; 183 SKILL_ILIPUNGU is the Lycan's, here for the range only)
edit('../../common/skill_length.h', 'vnums',
     '\tGUILD_SKILL_COUNT = GUILD_SKILL_END - GUILD_SKILL_START + 1,\n',
     '\tGUILD_SKILL_COUNT = GUILD_SKILL_END - GUILD_SKILL_START + 1,\n'
     '\n'
     '\t// MT2009_PLUS_SKILL9_V1 (vnums): the 9th skills of Yohara (server-patches/skill9, playerbot_skill9.cpp).\n'
     '\tSKILL_FINISH = 176,\t\t// Trzesienie (Wojownik)\n'
     '\tSKILL_ILGWANGPYO = 177,\t// Swiatlo Gwiazd (Ninja, sztylety)\n'
     '\tSKILL_PUNGLOEPO = 178,\t// Strzal Wichury (Ninja, luk)\n'
     '\tSKILL_GEOMAGGWI = 179,\t// Piekielny Cios (Sura, bron)\n'
     '\tSKILL_MABEOBAGGWI = 180,\t// Fala Smierci (Sura, czarna magia)\n'
     '\tSKILL_METEO = 181,\t\t// Meteor (Szaman, smok)\n'
     '\tSKILL_CHEONUN = 182,\t\t// Tarcza Eteru (Szaman, leczenie)\n'
     '\tSKILL_ILIPUNGU = 183,\t\t// Burza Szponow (Likan - no Lycan here)\n')

CS = 'char_skill.cpp'
# ---- IsLearnableSkill: a 9th skill only for its own class and specialisation (skill group)
edit(CS, 'learnable',
     'bool CHARACTER::IsLearnableSkill(DWORD dwSkillVnum) const\n{\n',
     'bool CHARACTER::IsLearnableSkill(DWORD dwSkillVnum) const\n{\n'
     '\t// MT2009_PLUS_SKILL9_V1 (learnable): a 9th skill belongs to one class AND specialisation (playerbot_skill9.cpp).\n'
     '\t{\n'
     '\t\tint Skill9Learnable(const CHARACTER*, unsigned int);\n'
     '\t\tconst int r = Skill9Learnable(this, dwSkillVnum);\n'
     '\t\tif (r >= 0)\n'
     '\t\t\treturn r != 0;\n'
     '\t}\n')

# ---- LearnSkillByBook: a Champion only, with 2 000 (below M1) / 5 000 Champion experience a read
edit(CS, 'book check',
     '\tif (!IsLearnableSkill(dwSkillVnum))\n\t{\n\t\tChatPacket(CHAT_TYPE_INFO, LC_TEXT("You cannot train this skill."));\n'
     '\t\treturn false;\n\t}\n\n\tDWORD need_exp = 0;',
     '\tif (!IsLearnableSkill(dwSkillVnum))\n\t{\n\t\tChatPacket(CHAT_TYPE_INFO, LC_TEXT("You cannot train this skill."));\n'
     '\t\treturn false;\n\t}\n\n'
     '\t// MT2009_PLUS_SKILL9_V1 (book check): a 9th skill\'s book - Champion level 1+ and its Champion experience.\n'
     '\t{\n'
     '\t\tint Skill9BookCheck(CHARACTER*, unsigned int);\n'
     '\t\tif (!Skill9BookCheck(this, dwSkillVnum))\n'
     '\t\t\treturn false;\n'
     '\t}\n\n'
     '\tDWORD need_exp = 0;')

# ---- LearnSkillByBook: a 9th skill is read from level 0 (no skill points), not from M1 only
edit(CS, 'book grade',
     '\tif (pkSk->dwType != 0)\n\t{\n\t\tif (GetSkillMasterType(dwSkillVnum) != SKILL_MASTER)\n\t\t{\n'
     '\t\t\tif (GetSkillMasterType(dwSkillVnum) > SKILL_MASTER)\n'
     '\t\t\t\tChatPacket(CHAT_TYPE_INFO, LC_TEXT("You cannot train this skill with a Book."));',
     '\t// MT2009_PLUS_SKILL9_V1 (book grade): the books of a 9th skill teach it from 0 to M1 as well (a level a read).\n'
     '\tif (pkSk->dwType != 0 && !(dwSkillVnum >= SKILL_FINISH && dwSkillVnum <= SKILL_CHEONUN && GetSkillMasterType(dwSkillVnum) == SKILL_NORMAL))\n'
     '\t{\n\t\tif (GetSkillMasterType(dwSkillVnum) != SKILL_MASTER)\n\t\t{\n'
     '\t\t\tif (GetSkillMasterType(dwSkillVnum) > SKILL_MASTER)\n'
     '\t\t\t\tChatPacket(CHAT_TYPE_INFO, LC_TEXT("You cannot train this skill with a Book."));')

edit(CS, 'book index',
     '\t\tint idx = MIN(9, GetSkillLevel(dwSkillVnum) - 20);\n',
     '\t\t// MT2009_PLUS_SKILL9_V1 (book index): a 9th skill is read below M1 too - the log\'s index stays in its table.\n'
     '\t\tint idx = MINMAX(0, GetSkillLevel(dwSkillVnum) - 20, 9);\n')

edit(CS, 'book pay',
     '\t\tPointChange(POINT_EXP, -need_exp);\n',
     '\t\tPointChange(POINT_EXP, -need_exp);\n'
     '\t\t// MT2009_PLUS_SKILL9_V1 (book pay): a 9th skill\'s read costs 2 000 / 5 000 Champion experience (won or not).\n'
     '\t\t{ void Skill9BookPay(CHARACTER*, unsigned int); Skill9BookPay(this, dwSkillVnum); }\n')

# ---- SkillLevelDown: no skill point back from a 9th skill (none went into it)
edit(CS, 'level down',
     '\tif (!IsLearnableSkill(dwVnum))\n\t\treturn false;\n\n\tif (GetSkillMasterType(pkSk->dwVnum) != SKILL_NORMAL)\n\t\treturn false;\n',
     '\tif (!IsLearnableSkill(dwVnum))\n\t\treturn false;\n\n'
     '\t// MT2009_PLUS_SKILL9_V1 (level down): a 9th skill is books only - nothing to give back as a skill point.\n'
     '\tif (dwVnum >= SKILL_FINISH && dwVnum <= SKILL_CHEONUN)\n\t\treturn false;\n\n'
     '\tif (GetSkillMasterType(pkSk->dwVnum) != SKILL_NORMAL)\n\t\treturn false;\n')

# ---- SkillLevelUp: by book below M1; no 17-19 stop and no roll for M - a level a read, 20 = M1
edit(CS, 'level up book',
     '\telse if (bMethod == SKILL_UP_BY_BOOK)\n\t{\n\t\tif (pkSk->dwType != 0)\n'
     '\t\t\tif (GetSkillMasterType(pkSk->dwVnum) != SKILL_MASTER)\n\t\t\t\treturn;\n\t}',
     '\telse if (bMethod == SKILL_UP_BY_BOOK)\n\t{\n'
     '\t\t// MT2009_PLUS_SKILL9_V1 (level up book): a 9th skill goes up by its books from 0 too.\n'
     '\t\tif (pkSk->dwType != 0 && !(pkSk->dwVnum >= SKILL_FINISH && pkSk->dwVnum <= SKILL_CHEONUN))\n'
     '\t\t\tif (GetSkillMasterType(pkSk->dwVnum) != SKILL_MASTER)\n\t\t\t\treturn;\n\t}')

edit(CS, 'level up stop',
     '\t\tpkSk->dwType != 5 && // horse skill\n\t\tGetSkillLevel(pkSk->dwVnum) >= 17 && GetSkillLevel(pkSk->dwVnum) < 20)',
     '\t\tpkSk->dwType != 5 && // horse skill\n'
     '\t\t!(pkSk->dwVnum >= SKILL_FINISH && pkSk->dwVnum <= SKILL_CHEONUN) && // MT2009_PLUS_SKILL9_V1 (level up stop)\n'
     '\t\tGetSkillLevel(pkSk->dwVnum) >= 17 && GetSkillLevel(pkSk->dwVnum) < 20)')

edit(CS, 'level up roll',
     '\t\t\tcase SKILL_NORMAL:\n\n\t\t\t\tif (GetSkillLevel(pkSk->dwVnum) >= 17)\n',
     '\t\t\tcase SKILL_NORMAL:\n\n'
     '\t\t\t\t// MT2009_PLUS_SKILL9_V1 (level up roll): a 9th skill jumps to M at 17-19 by the classic roll (de wiki:\n'
     '\t\t\t\t// "beim 17. bis 20. Punkt springt sie auf Meister"), never on this server\'s reset-scroll counters.\n'
     '\t\t\t\tif (pkSk->dwVnum >= SKILL_FINISH && pkSk->dwVnum <= SKILL_CHEONUN)\n'
     '\t\t\t\t{\n'
     '\t\t\t\t\tif (GetSkillLevel(pkSk->dwVnum) >= 17 && number(1, 21 - MIN(20, GetSkillLevel(pkSk->dwVnum))) == 1)\n'
     '\t\t\t\t\t\tSetSkillLevel(pkSk->dwVnum, 20);\n'
     '\t\t\t\t}\n'
     '\t\t\t\telse if (GetSkillLevel(pkSk->dwVnum) >= 17)\n')

# ---- ResetSkill: the 9th skill survives a skill reset (its levels are books, not skill points)
edit(CS, 'reset',
     '\tmemset(m_pSkillLevels, 0, sizeof(TPlayerSkill) * SKILL_MAX_NUM);\n',
     '\t// MT2009_PLUS_SKILL9_V1 (reset): the 9th skills are kept like the support skills (books, not skill points).\n'
     '\tfor (DWORD dwNinth = SKILL_FINISH; dwNinth <= SKILL_CHEONUN; ++dwNinth)\n'
     '\t\tvec.emplace_back(dwNinth, m_pSkillLevels[dwNinth]);\n\n'
     '\tmemset(m_pSkillLevels, 0, sizeof(TPlayerSkill) * SKILL_MAX_NUM);\n')

# ---- UseSkill: Meteor strikes its target when cast (Owsap's UseSkill: ComputeSkill at once)
edit(CS, 'meteor',
     '\tif (bShamanPartyBuff)\n\t\tComputeSkillParty(dwVnum, this);\n',
     '\t// MT2009_PLUS_SKILL9_V1 (meteor): Meteor falls on its target as it is cast (Owsap); its shot does nothing more.\n'
     '\tif (dwVnum == SKILL_METEO && pkVictim && pkVictim != this)\n'
     '\t\tComputeSkill(dwVnum, pkVictim);\n\n'
     '\tif (bShamanPartyBuff)\n\t\tComputeSkillParty(dwVnum, this);\n')

# ---- IsUsableSkillMotion: the 9th skill's motions (9 / 24 and their grades) - else SKILL_HACK and a kick
edit(CS, 'motion',
     'bool CHARACTER::IsUsableSkillMotion(DWORD dwMotionIndex) const\n{\n',
     'bool CHARACTER::IsUsableSkillMotion(DWORD dwMotionIndex) const\n{\n'
     '\t// MT2009_PLUS_SKILL9_V1 (motion): motions 9 and 24 (+25 a grade) are the 9th skills\' (playerbot_skill9.cpp).\n'
     '\t{\n'
     '\t\tint Skill9UsableMotion(const CHARACTER*, unsigned int);\n'
     '\t\tconst int r = Skill9UsableMotion(this, dwMotionIndex);\n'
     '\t\tif (r >= 0)\n'
     '\t\t\treturn r != 0;\n'
     '\t}\n')

# ---- CanUseSkill: the 9th skill of the class and specialisation
edit(CS, 'can use',
     'bool CHARACTER::CanUseSkill(DWORD dwSkillVnum) const\n{\n\tif (0 == dwSkillVnum) return false;\n',
     'bool CHARACTER::CanUseSkill(DWORD dwSkillVnum) const\n{\n\tif (0 == dwSkillVnum) return false;\n\n'
     '\t// MT2009_PLUS_SKILL9_V1 (can use): the 9th skill of the class and specialisation (playerbot_skill9.cpp).\n'
     '\t{\n'
     '\t\tint Skill9CanUse(const CHARACTER*, unsigned int);\n'
     '\t\tconst int r = Skill9CanUse(this, dwSkillVnum);\n'
     '\t\tif (r >= 0)\n'
     '\t\t\treturn r != 0;\n'
     '\t}\n')

CB = 'char_battle.cpp'
edit(CB, 'reach',
     '\tcase SKILL_HORSE_WILDATTACK:\n\t\treturn 400;\n\tdefault:\n\t\treturn ATTACK_MELEE_MAX_DISTANCE;',
     '\tcase SKILL_HORSE_WILDATTACK:\n\t\treturn 400;\n'
     '\t// MT2009_PLUS_SKILL9_V1 (reach): Trzesienie strikes up to 550 ahead (playerbot_skill9.cpp).\n'
     '\tcase SKILL_FINISH:\n'
     '\t\t{ unsigned int Skill9MeleeReach(unsigned int); return Skill9MeleeReach(skill_vnum); }\n'
     '\tdefault:\n\t\treturn ATTACK_MELEE_MAX_DISTANCE;')

edit(CB, 'shoot arrow',
     '\t\tcase SKILL_POISON_ARROW:\n\t\t{\n',
     '\t\tcase SKILL_POISON_ARROW:\n'
     '\t\tcase SKILL_PUNGLOEPO: // MT2009_PLUS_SKILL9_V1 (shoot arrow): Strzal Wichury - an arrow like Trujaca Strzala\n'
     '\t\t{\n')

edit(CB, 'shoot magic',
     '\t\tcase SKILL_DARK_STRIKE:\n\t\tcase SKILL_SPIRIT_ORB:\n\t\tcase SKILL_FLYING_TALISMAN:\n',
     '\t\tcase SKILL_ILGWANGPYO:   // MT2009_PLUS_SKILL9_V1 (shoot magic): Swiatlo Gwiazd\n'
     '\t\tcase SKILL_MABEOBAGGWI:  // and Fala Smierci strike where they land\n'
     '\t\tcase SKILL_DARK_STRIKE:\n\t\tcase SKILL_SPIRIT_ORB:\n\t\tcase SKILL_FLYING_TALISMAN:\n')

edit(CB, 'shoot meteor',
     '\t\tcase SKILL_SHOOTING_DRAGON:\n\t\t{\n\t\t\tm_me->OnMove(true);\n\t\t\tupdateAttackLog = false;\n',
     '\t\tcase SKILL_METEO: // MT2009_PLUS_SKILL9_V1 (shoot meteor): its blow came with the cast (UseSkill)\n'
     '\t\tcase SKILL_SHOOTING_DRAGON:\n\t\t{\n\t\t\tm_me->OnMove(true);\n\t\t\tupdateAttackLog = false;\n')

edit(CB, 'protect',
     "\t// MT2009_PLUS_SUNGMA_V1 (damage): a person's blow at a monster",
     '\t// MT2009_PLUS_SKILL9_V1 (protect): Tarcza Eteru\'s protection blocks every blow while it lasts (Owsap).\n'
     '\t{\n'
     '\t\tint Skill9Blocked(CHARACTER*, CHARACTER*);\n'
     '\t\tif (Skill9Blocked(this, pAttacker))\n'
     '\t\t{\n'
     '\t\t\tSendDamagePacket(pAttacker, 0, DAMAGE_BLOCK);\n'
     '\t\t\treturn false;\n'
     '\t\t}\n'
     '\t}\n\n'
     "\t// MT2009_PLUS_SUNGMA_V1 (damage): a person's blow at a monster")

edit('constants.cpp', 'shoot',
     '\t\tcase SKILL_LIGHTNING_CLAW:\n\t\tcase SKILL_HORSE_WILDATTACK_RANGE:\n\t\t\treturn true;\n\t\tdefault:\n\t\t\treturn false;',
     '\t\tcase SKILL_LIGHTNING_CLAW:\n\t\tcase SKILL_HORSE_WILDATTACK_RANGE:\n'
     '\t\t// MT2009_PLUS_SKILL9_V1 (shoot): the 9th skills that fly to their target\n'
     '\t\tcase SKILL_ILGWANGPYO:\n\t\tcase SKILL_PUNGLOEPO:\n\t\tcase SKILL_MABEOBAGGWI:\n\t\tcase SKILL_METEO:\n'
     '\t\t\treturn true;\n\t\tdefault:\n\t\t\treturn false;')

edit('battle.cpp', 'distance',
     '\tcase SKILL_HORSE_WILDATTACK_RANGE:\n\t\treturn true;\n\t}\n\treturn false;\n}',
     '\tcase SKILL_HORSE_WILDATTACK_RANGE:\n'
     '\t// MT2009_PLUS_SKILL9_V1 (distance): the 9th skills that fly to their target\n'
     '\tcase SKILL_ILGWANGPYO:\n\tcase SKILL_PUNGLOEPO:\n\tcase SKILL_MABEOBAGGWI:\n\tcase SKILL_METEO:\n'
     '\t\treturn true;\n\t}\n\treturn false;\n}')

CA = 'char_affect.cpp'
edit(CA, 'affect',
     '\tif (pkAff->dwType == SKILL_FLAME_SPIRIT)\n\t{\n\t\tif (bAdd)\n\t\t\tStartMuyeongEvent();',
     '\t// MT2009_PLUS_SKILL9_V1 (affect): Tarcza Eteru starts its 12-second rolls (playerbot_skill9.cpp).\n'
     '\t{ void Skill9ComputeAffect(CHARACTER*, const CAffect*, bool); Skill9ComputeAffect(this, pkAff, bAdd); }\n\n'
     '\tif (pkAff->dwType == SKILL_FLAME_SPIRIT)\n\t{\n\t\tif (bAdd)\n\t\t\tStartMuyeongEvent();')

edit(CA, 'remove',
     '\tRemoveAffect(SKILL_DRAGON_HELP);\n#ifdef ENABLE_WOLFMAN_CHARACTER\n\tRemoveAffect(SKILL_JEOKRANG);',
     '\tRemoveAffect(SKILL_DRAGON_HELP);\n'
     '\t{ void Skill9RemoveAffects(CHARACTER*); Skill9RemoveAffects(this); } // MT2009_PLUS_SKILL9_V1 (remove): Tarcza Eteru\n'
     '#ifdef ENABLE_WOLFMAN_CHARACTER\n\tRemoveAffect(SKILL_JEOKRANG);')

edit(CA, 'good',
     '\t\tcase (SKILL_DRAGON_HELP):\n#ifdef ENABLE_WOLFMAN_CHARACTER\n',
     '\t\tcase (SKILL_DRAGON_HELP):\n'
     '\t\tcase (SKILL_CHEONUN): // MT2009_PLUS_SKILL9_V1 (good): Tarcza Eteru is a good affect (dispel, duel)\n'
     '#ifdef ENABLE_WOLFMAN_CHARACTER\n')


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
