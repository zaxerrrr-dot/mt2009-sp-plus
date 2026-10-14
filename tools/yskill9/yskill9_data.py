# -*- coding: utf-8 -*-
"""yskill9_data.py - the 9th skills' skill_proto rows (MT2009_PLUS_SKILL9_V1), one source for the server's
yskill9.sql (gen_yskill9_sql.py) and the client's gamedata/skilltable.txt
(client-patches/client-2.0.30/tools/yskill9/patch_yskill9_client.py). See gen_yskill9_sql.py for what differs from
Owsap's rows."""

COLS = ('dwVnum', 'szName', 'bType', 'bLevelStep', 'bMaxLevel', 'bLevelLimit', 'szPointOn', 'szPointPoly',
        'szSPCostPoly', 'szDurationPoly', 'szDurationSPCostPoly', 'szCooldownPoly', 'szMasterBonusPoly',
        'szAttackGradePoly', 'setFlag', 'setAffectFlag', 'szPointOn2', 'szPointPoly2', 'szDurationPoly2',
        'setAffectFlag2', 'szPointOn3', 'szPointPoly3', 'szDurationPoly3', 'setAffectFlag3',
        'szGrandMasterAddSPCostPoly', 'prerequisiteSkillVnum', 'prerequisiteSkillLevel', 'eSkillType', 'iMaxHit',
        'szSplashAroundDamageAdjustPoly', 'dwTargetRange', 'dwSplashRange')

HIT = '0.4*k+(32*k/2)'   # Bonus Precyzji (inert here)
SP = '200+200*k'
CD = '35+20*k'


def row(vnum, name, job, point, poly, flags, kind, maxhit, target, splash, point2=('NONE', HIT, '20*k'),
        point_on='HP', dur='', master=None):
    return (vnum, name, job, 1, 1, 0, point_on, poly, SP, dur, '', CD if vnum != 182 else '386+(80*k)',
            master if master is not None else poly, '', flags, 'NONE', point2[0], point2[1], point2[2], 'NONE',
            'NONE', '', '', 'NONE', SP, 0, 0, kind, maxhit, '1', target, splash)


ROWS = [
    # Trzesienie - Wojownik (both specialisations): melee, four blows in a line ahead (finish*.msa)
    row(176, 'FINISH', 1, 'HP', '-(3*atk+(0.9*atk+number(1,1000)+str*5+dex*3+lv)*k)',
        'ATTACK,USE_MELEE_DAMAGE,DISABLE_BY_POINT_UP', 'MELEE', 8, 0, 200),
    # Swiatlo Gwiazd - Ninja (sztylety): thrown stars, splash at the target
    row(177, 'ILGWANGPYO', 2, 'HP', '-(atk+(1.7*atk+number(1,1000)+dex*6+lv*5)*k)',
        'ATTACK,USE_MELEE_DAMAGE,SPLASH,DISABLE_BY_POINT_UP', 'MELEE', 8, 2000, 200),
    # Strzal Wichury - Ninja (luk): an arrow, splash
    row(178, 'PUNGLOEPO', 2, 'HP', '-(1.9*atk+(2.6*atk+number(1,1000))*k)',
        'ATTACK,SPLASH,USE_ARROW_DAMAGE,DISABLE_BY_POINT_UP', 'RANGE', 8, 2500, 200),
    # Piekielny Cios - Sura (bron): melee
    row(179, 'GEOMAGGWI', 3, 'HP', '-(1.9*atk+(2.6*atk+number(1,1000))*k)',
        'ATTACK,USE_MELEE_DAMAGE,DISABLE_BY_POINT_UP', 'MELEE', 4, 0, 0),
    # Fala Smierci - Sura (czarna magia): magic shot, splash
    row(180, 'MABEOBAGGWI', 3, 'HP', '-(120+6*lv+(5*con+5*dex+30*iq+number(1,1)+9*mwep)*ar*k)',
        'ATTACK,COMPUTE_MAGIC_DAMAGE,SPLASH,DISABLE_BY_POINT_UP', 'MAGIC', 5, 2000, 200),
    # Meteor - Szaman (smok): on the target at once, splash, burning (chance 20*k %)
    row(181, 'METEO', 4, 'HP', '-(120+6*lv+(5*con+5*dex+30*iq+number(1,1)+9*mwep)*ar*k)',
        'ATTACK,SPLASH,ATTACK_FIRE_CONT,DISABLE_BY_POINT_UP', 'MAGIC', 5, 2000, 500),
    # Tarcza Eteru - Szaman (leczenie): party buff 50+8k s; its amount is the chance of protection every 12 s
    # (the protection's seconds 4*k: playerbot_skill9.cpp CheonunProtectSeconds)
    row(182, 'CHEONUN', 4, 'NONE', '0.4*k+(18*k)', 'DISABLE_BY_POINT_UP,PARTY', 'NORMAL', 1, 2000, 0,
        point2=('NONE', '4*k', ''), point_on='NONE', dur='50+(8*k)'),
]
