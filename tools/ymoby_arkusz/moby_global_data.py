# -*- coding: utf-8 -*-
"""MT2009_PLUS_MOBY_GLOBAL_V1: the decisions of tools/ymoby_arkusz/gen_moby_global.py - the monsters before Yohara
"as on the global server" (the owner, 20 October 2026: HP, damage, EXP, levels, resistances, the effects' chances and
the other stats of the sheet for every monster we have; their drops as the sheet lists them; the race flags of the
Zodiac's red thieves and the Tu-Gui). Cache report: /opt/metin2/cache/yohara/porownanie-moby.md.
"""

# the columns brought to the sheet (numbers; the sheet's value replaces ours)
NUM = ['level', 'max_hp', 'exp', 'damage_min', 'damage_max', 'def', 'st', 'dx', 'ht', 'iq', 'attack_speed',
       'move_speed', 'regen_cycle', 'regen_percent', 'enchant_curse', 'enchant_slow', 'enchant_poison', 'enchant_stun',
       'enchant_critical', 'enchant_penetrate', 'resist_sword', 'resist_twohand', 'resist_dagger', 'resist_bell',
       'resist_fan', 'resist_bow', 'resist_fire', 'resist_elect', 'resist_magic', 'resist_wind', 'resist_poison']
# the flags brought to the sheet (only these bits of the SET columns; the others - NOMOVE, ATTMOB, the elements of
# setRaceFlag bits 11-16, FALL/REFLECT - stay ours)
AI = ['AGGR', 'BERSERK', 'STONESKIN', 'GODSPEED', 'DEATHBLOW', 'REVIVE', 'COWARD']
IMMUNE = ['STUN', 'SLOW', 'CURSE', 'POISON', 'TERROR']
# a race flag is only ADDED, to a monster that has none of these (2676-2679 HUMAN, 7008-7010 ORC)
RACE = ['ANIMAL', 'UNDEAD', 'DEVIL', 'HUMAN', 'ORC', 'MILGYO', 'INSECT', 'DESERT']
# MT2009_PLUS_MOBY_RANK_V1: the rank as the sheet's too (the owner, 20 October 2026 - first left out, our boss
# systems count rank >= 4): every row of moby_global.json's "ranks" (2307 boss -> king, Tartar / Piekielne Bastardy /
# Ereb / Motloch Azraela 2591-2596 boss -> Poziom 4 = S_KNIGHT) becomes a guarded UPDATE like the other columns
RANK = True

# the sheet's name and ours differ only in the translation (the same monster)
SAME_NAME = {2301, 2302, 2311, 2312, 3790}

# drops: what the sheet lists and we leave out - besides chestdrops SKIP, ymoby_data.EXCLUDE, a quest's own items
# (any vnum a quest of ours gives, counts or takes) and the materials no recipe, shop, chest or drop of our world uses
EXCLUDE = dict((v, 'Seon-Hae event shard') for v in range(39070, 39078))
# MT2009_PLUS_NO_TRZECH_WLADCOW_V1 (the owner, 10 November 2026: "Tarcza Trzech Wladcow do wywalenia calkowicie z dropu ze
# wszystkiego"): the shield 13160-13169 in no drop; the game Dockerfile's last drop step cuts it from every file too
EXCLUDE.update((v, 'Tarcza Trzech Wladcow - out of every drop (owner 10.11)') for v in range(13160, 13170))

# MT2009_PLUS_MOBY_GLOBAL_OCHAO_BASE_V1: monsters our apply.sh makes (not in mob_proto.mt2009plus.sql) - the values a
# fresh world gets from apply.sh (world.ochao_mob), not the test world's: that one held the panel's database-editor
# import (6301 max_hp 12950), so the guards never fired on a fresh world (found when the editor's changes were undone,
# 20 Oct). extract() takes them as "made", and the build corrects a json extracted before.
SCRIPT_BASE = {
    6301: dict(max_hp=18500, damage_min=190, damage_max=232),
    6302: dict(max_hp=23000, damage_min=192, damage_max=236),
    6303: dict(max_hp=22000, damage_min=194, damage_max=238),
    6304: dict(max_hp=52000, damage_min=176, damage_max=262),
    6305: dict(max_hp=95000, damage_min=178, damage_max=266),
}
