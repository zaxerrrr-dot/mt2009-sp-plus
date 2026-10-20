# -*- coding: utf-8 -*-
"""MT2009_PLUS_MOBY_ARKUSZ_V1: the decisions of tools/ymoby_arkusz (the owner's sheet of 20 October 2026,
Metin2_Moby_statystyki_EXP_i_drop.xlsx - metin2alerts' mob pages, read 16 October 2026) - which differences of our
Yohara monsters are brought to the sheet and which stay ours (cache/yohara/porownanie-moby.md has the whole list).
"""

# -- statistics: (vnum, column, our old value, the sheet's) - the source rows (shipdefense.sql by hand, the Yohara
#    generators' OVERRIDE) hold the new value already; yohara_moby_arkusz.sql moves a world that still has the old one
#    (a guarded UPDATE: a value the operator set himself is kept) --------------------------------------------------
FIXES = [
    # Obrona Statku: the levels were lowered into 90-110 by a guess (our highest monster was 110) - the official ones
    (3953, 'level', 103, 105),
    (3956, 'level', 108, 110),
    (3957, 'level', 105, 110),
    (3958, 'level', 105, 110),
    (3959, 'level', 105, 110),
    (3960, 'level', 110, 120),
    (3961, 'level', 110, 120),
    (3962, 'level', 110, 120),
    (3963, 'level', 110, 120),
    (3964, 'level', 110, 120),
    (20432, 'level', 105, 120),
    # SZC (Szczelina) and Zaklety Las: the pl-wiki's experience was over Owsap's; the sheet = Owsap
    (4267, 'exp', 41101, 41001),
    (4270, 'exp', 49080, 61350),
    (6402, 'exp', 27356, 28934),
    # Alastor (Glebie Polnocnego Wiatru): Owsap's HP over the sheet's
    (6790, 'max_hp', 67751800, 22587258),
    (6790, 'regen_cycle', 15, 30),
    (6791, 'max_hp', 48751800, 22587258),
]

# -- statistics the sheet has otherwise and we keep (the reason; the report lists them for the owner) -------------
KEEP = {
    'elements': 'the owner, 14 October 2026: the elements of Yohara as the pl-wiki (Duch Kamienia 3990 Wiatr, Alastor '
                '6790 Lod / 6791 Blyskawica, no element on a Metin, Wieza Sung Mahi 7592-7595 none)',
    'tower_ai': 'Wieza Sung Mahi 7595, 7615-7620: NOMOVE on purpose - the quest wakes them (tools/yohara_dung4)',
    'meley_exp': 'Schronienie Meley 6110-6117: the pl-wiki Basis-EXP (sheet and Owsap: 0) - for the owner',
    'mast_regen': 'Drewno na Naprawe 20437: regen 1 HP / 255 s on purpose (the engine has no NORECOVERY flag)',
    'metin_exp': 'Metin Shiho / Swiadomosc 8066 / 8067: exp 0 (sheet 1) - no difference worth a change',
}

# -- drops ---------------------------------------------------------------------------------------------------------
# The sheet's item (an official vnum) -> ours: the same vnum when our item has the same name (a translation of it in
# SAME), else tools/yohara_chestdrops SUBST (our number of the same item), else an item of ours with exactly that name;
# chestdrops SKIP (a system we lack) and EXCLUDE stay out.
SAME = {28146, 30050, 30090, 30167, 30220, 30221, 30222, 30223, 30224, 30225, 30226, 30227, 30228, 31139, 31140, 31141,
        31142, 31250, 39002, 39004, 39081, 50614, 50901, 55001, 55009, 55401, 55402, 55409, 70005, 70048, 70104,
        72006, 76015, 76029, 100300}
# the sheet's vnum -> ours where our Yohara tables already use another item for it
MAP = {
    70043: 72006,       # Rekawica Zlodzieja: the Yohara monsters drop the 3 h one here (tools/yohara_items)
}
EXCLUDE = {
    50124: 'Sprochniala Skrzynia - out of every drop (the owner, 15 October 2026)',
    # the dungeons' task items: their quests give and take them
    31096: 'quest item', 31097: 'quest item', 31099: 'quest item', 31100: 'quest item',
    31162: 'quest item (SZC)', 31163: 'quest item (SZC)', 31165: 'quest item (SZC)', 31166: 'quest item (SZC)',
    31180: 'quest item (PB)', 31182: 'quest item (PB)', 31183: 'quest item (PB)', 31185: 'quest item (PB)',
    31186: 'quest item (PB)', 30168: 'quest item', 31256: 'the labyrinth chest of its quest',
    31143: 'Skrzynia Przebudzenia - the awakened bosses\' quest gives it', 76019: 'event pass',
}
# monsters whose drop the sheet lists but which stay without one here (the reason)
NO_DROP_MOBS = {
    3965: 'Skarb Hydry - its drop is the ship defence quest\'s chest group (game/shipdefense)',
}
# the Time Rift (SZC, map 404) drops nothing but Jotun Thrym's yang (pl-wiki, server-patches/szczelina): every
# vnum of yohara_crack.sql
NO_DROP_SQL = 'yohara_crack.sql'

# -- the chance of an added row (the file's value v; one kill draws v / 4 % before the level difference and the drop
#    bonuses - as the other Yohara drop files). The same item on our Yohara monsters of the same kind (normal /
#    boss / Metin) -> the median of those rows; else on any of our Yohara monsters -> that median, at most CAP of
#    the kind; else the kind's default by the item ----------------------------------------------------------------
CAP = {'normal': 2.0, 'boss': 40.0, 'stone': 40.0}
DEFAULT = {
    #            normal  boss   stone
    'potion':   (1.0,   40.0,  40.0),      # 27001-27125
    'gear+0-5': (0.5,   10.0,  10.0),      # weapons / armour by their +N
    'gear+6':   (0.2,    5.0,   5.0),
    'gear+7':   (0.1,    2.0,   2.0),
    'gear+8':   (0.05,   1.0,   1.0),
    'material': (0.5,   10.0,  10.0),      # ITEM_MATERIAL, herbs
    'other':    (0.2,    4.0,   4.0),
}
