# -*- coding: utf-8 -*-
"""MT2009_PLUS_GROWTH_PET_V1 - System Zwierzat Domowych: the one data source of the feature.

The SQL generator (tools/pety/gen_pety_sql.py -> linux-port/docker/mariadb/playerbot/pety.sql), the server tables
(the overlay growth_pet_data.h is generated from here too: gen_pety_sql.py --header) and the client pack builder
(client-patches/client-2.0.30/tools/pety) read this file. Every number comes from the wiki (pl first, tr/en/de where
pl has nothing): https://pl-wiki.metin2.gameforge.com/index.php/System_Zwierz%C4%85t_Domowych and
https://tr-wiki.metin2.gameforge.com/index.php/Pet_Sistemi - see server-patches/pety/README.md for the choices made
where the wiki is silent.
"""

# --------------------------------------------------------------------------------------------------------------------
# Species: (index, egg, seal, pl pet name, pl egg name, mobs (young, heroic, champion), hatch life days, enchant life
# days, skill slots (min, max), max type, the pl short name used by the old system's eggs)
SPECIES = [
    # idx egg    seal   pet name                 egg name                    young  hero   champ  hatch     enchant   slots  maxtype
    (1, 55401, 55701, u"Mały Małpiszon",       u"Jajo Małpiszona",          34041, 34042, 34216, (1, 14),  (1, 21),  (1, 2), 6),
    (2, 55402, 55702, u"Mały Pająk",           u"Jajo Pająka",              34045, 34046, 34217, (1, 14),  (1, 19),  (1, 2), 6),
    (3, 55403, 55703, u"Mały Razador",         u"Jajo Razadora",            34049, 34050, 34218, (1, 14),  (1, 19),  (1, 3), 8),
    (4, 55404, 55704, u"Mała Nemere",          u"Jajo Nemere",              34053, 34054, 34219, (1, 14),  (1, 19),  (1, 3), 8),
    (5, 55405, 55705, u"Niebieski Mały Smok",  u"Niebieskie Jajo Smoka",    34036, 34037, 34220, (1, 14),  (1, 19),  (1, 3), 8),
    (6, 55406, 55706, u"Mała Meley",           u"Czerwone Jajo Smoka",      34064, 34065, 34221, (15, 45), (15, 48), (3, 3), 8),
    (7, 55407, 55707, u"Mini Azrael",          u"Jajo Mini Azraela",        34073, 34074, 34222, (1, 14),  (1, 20),  (1, 2), 6),
    (8, 55408, 55708, u"Gruby Mini Kat",       u"Jajo Grubego Mini Kata",   34075, 34076, 34223, (1, 14),  (1, 18),  (1, 3), 8),
    (9, 55409, 55709, u"Mały Baashido",        u"Jajo Baashido",            34080, 34081, 34224, (7, 28),  (7, 28),  (1, 3), 8),
    (10, 55410, 55710, u"Nessie",              u"Jajo Nessie",              34082, 34083, 34225, (15, 45), (15, 48), (3, 3), 8),
    (11, 55411, 55711, u"Wyląg Exedyara",      u"Jajo Exedyara",            34047, 34048, 34226, (15, 45), (15, 45), (3, 3), 8),
    (12, 55412, 55712, u"Gniewny Mini Alastor", u"Białe Jajo Smoka",        34077, 34078, 34227, (15, 45), (15, 49), (3, 3), 8),
    (13, 55413, 55713, u"Mini-Dowódca",        u"Jajo Strażnika",           34165, 34166, 34228, (15, 45), (15, 49), (3, 3), 8),
    (14, 55414, 55714, u"Mały Aamon",          u"Jajo Aamona",              34229, 34230, 34231, (15, 45), (15, 49), (3, 3), 8),
]

HATCH_PRICE = 100000
RENAME_PRICE = 100000
SKILL_UPGRADE_PRICE = 2000000
EGG_LIFE_SECONDS = 7 * 24 * 3600
BAG_LIFE_SECONDS = 30 * 24 * 3600

# --------------------------------------------------------------------------------------------------------------------
# Skills: id -> (pl name, icon, kind, cooldown s, point, per-skill-level value at pet level 105 (skill level 1..20,
# no specialty; unit below), pl item name of the book, book vnum, pl description)
# Units of the value (what the server keeps and sends in wSkillFormula2):
#   '%10'  tenths of a per cent (12 % = 120)          'm10' tenths of a metre (6 m = 60)
#   'hp'   hit points                                    'dmg' the feather's minimum damage (max 1400)
#   's10'  tenths of a second (Niesmiertelnosc's duration)
# Uzdrowienie (18): the value (tenths of a per cent) is the chance to remove the bad effects (one roll a trigger).
PASSIVE, AUTO = 1, 2

RESIST = [1, 1, 2, 2, 3, 4, 4, 5, 5, 6, 6, 7, 8, 8, 9, 9, 10, 10, 11, 12]


def pct10(seq):
    return [v * 10 for v in seq]


def linear(v20):
    """A curve the wiki has only the skill level 20 value of: v20 * k / 20, at least 1 (tenths kept)."""
    return [max(10, (v20 * 10 * k + 10) // 20) for k in range(1, 21)]


SKILLS = {
    1: (u"Odporność (wojownik)", "jijoong", PASSIVE, 0, "RESIST_WARRIOR", pct10(RESIST), '%10',
        u"Odporność (wojownik)", 55010, u"Zwiększa odporność na ataki Wojownika."),
    2: (u"Odporność (sura)", "jijoong", PASSIVE, 0, "RESIST_SURA", pct10(RESIST), '%10',
        u"Odporność (sura)", 55011, u"Zwiększa odporność na ataki Sury."),
    3: (u"Odporność (ninja)", "jijoong", PASSIVE, 0, "RESIST_ASSASSIN", pct10(RESIST), '%10',
        u"Odporność (ninja)", 55012, u"Zwiększa odporność na ataki Ninja."),
    4: (u"Odporność (szaman)", "jijoong", PASSIVE, 0, "RESIST_SHAMAN", pct10(RESIST), '%10',
        u"Odporność (szaman)", 55013, u"Zwiększa odporność na ataki Szamana."),
    5: (u"Odporność (likan)", "jijoong", PASSIVE, 0, "RESIST_WOLFMAN", pct10(RESIST), '%10',
        u"Odporność (likan)", 55014, u"Zwiększa odporność na ataki Likana."),
    6: (u"Berserk", "pacheon", PASSIVE, 0, "MELEE_MAGIC_ATT_BONUS_PER",
        pct10([1, 1, 1, 2, 2, 3, 3, 3, 4, 4, 5, 5, 5, 6, 6, 6, 7, 7, 8, 8]), '%10',
        u"Księga Berserka", 55015, u"Zwiększa magiczny i krótkodystansowy atak."),
    7: (u"Antymagia", "cheonryeong", PASSIVE, 0, "ANTI_RESIST_MAGIC",
        pct10([1, 1, 2, 2, 3, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10]), '%10',
        u"Księga Antymagii", 55016, u"Zmniejsza obronę magiczną przeciwnika."),
    8: (u"Przyspieszenie", "banya", PASSIVE, 0, "CASTING_SPEED",
        pct10([7, 8, 8, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 14, 15, 15, 16, 17, 17, 18]), '%10',
        u"Księga Przyspieszenia", 55017, u"Zwiększa szybkość zaklęcia."),
    9: (u"Przebicie", "choehoenbimu", PASSIVE, 0, "PENETRATE_PCT",
        pct10([1, 1, 2, 2, 3, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10]), '%10',
        u"Księga Przebicia", 55018, u"Zwiększa szanse na przeszywający cios."),
    10: (u"Odnowa", "heal", AUTO, 480, "", [17, 70, 159, 282, 441, 636, 865, 1130, 1431, 1766, 2137, 2544, 2985, 3462,
                                             3975, 4522, 5105, 5724, 6377, 7066], 'hp',
         u"Księga Odnowy", 55019, u"Regeneruje PŻ, jeśli zdrowie postaci spadnie poniżej 20%."),
    11: (u"Wampir", "stealhp", PASSIVE, 0, "STEAL_HP",
         pct10([1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6]), '%10',
         u"Księga Wampira", 55020, u"Zwiększa szansę na kradzież PŻ."),
    12: (u"Duch", "stealmp", PASSIVE, 0, "STEAL_SP",
         pct10([1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6, 7]), '%10',
         u"Księga Ducha", 55021, u"Zwiększa szansę na kradzież PE."),
    13: (u"Przeszkoda", "block", PASSIVE, 0, "BLOCK",
         pct10([1, 1, 2, 3, 3, 4, 4, 5, 5, 6, 7, 7, 8, 8, 9, 9, 10, 11, 11, 12]), '%10',
         u"Księga Przeszkody", 55022, u"Zwiększa szansę na blok ciosów."),
    14: (u"Zwierciadło", "reflect_melee", PASSIVE, 0, "REFLECT_MELEE",
         pct10([1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6]), '%10',
         u"Księga Zwierciadła", 55023, u"Zwiększa wartość odbitych ciosów."),
    15: (u"Drop Yang", "gold_drop", PASSIVE, 0, "GOLD_DOUBLE_BONUS",
         [5, 10, 16, 21, 26, 31, 37, 42, 47, 53, 58, 63, 69, 74, 79, 84, 90, 95, 100, 106], '%10',
         u"Księga Dropu Yang", 55024, u"Zwiększa szansę na drop Yang."),
    16: (u"Zasięg", "bow_distance", PASSIVE, 0, "BOW_DISTANCE",
         pct10([1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6]), 'm10',
         u"Księga Zasięgu", 55025, u"Zwiększa zasięg ataku z łuku."),
    # the value is the duration in tenths of a second; the chance is ACTIVATE[17]
    17: (u"Nieśmiertelność", "invincibility", AUTO, 600, "",
         [2, 4, 5, 6, 8, 9, 10, 11, 13, 14, 15, 17, 18, 19, 21, 22, 23, 25, 26, 27], 's10',
         u"Księga Nieśmiertelności", 55026, u"Daje tymczasową nieśmiertelność."),
    18: (u"Uzdrowienie", "removal", AUTO, 480, "",
         pct10([2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 33, 35, 37, 39, 41]), '%10',
         u"Księga Uzdrowienia", 55027, u"Usuwa negatywne efekty (otrucie, krwawienie i spowolnienie)."),
    19: (u"Browarnik", "potion", PASSIVE, 0, "POTION_BONUS", linear(10), '%10',
         u"Księga Browarnika", 55034, u"Zwiększa efektywność mikstur regeneracyjnych."),
    20: (u"Łowca Potworów", "mob_bonus", PASSIVE, 0, "ATTBONUS_MONSTER", linear(8), '%10',
         u"Księga Łowcy Potworów", 55035, u"Zwiększa siłę przeciwko potworom."),
    21: (u"Spostrzegawczość", "exp", PASSIVE, 0, "MALL_EXPBONUS", linear(6), '%10',
         u"Księga Spostrzegawczości", 55036, u"Zwiększa ilość zdobywanych PD."),
    22: (u"Absorpcja Życia", "hp_recover", PASSIVE, 0, "KILL_HP_RECOVERY", linear(6), '%10',
         u"Księga Absorpcji Życia", 55037, u"Przywraca PŻ po zabiciu potwora."),
    23: (u"Lekkie jak Piórko", "feather", AUTO, 180, "", [max(10, 175 * k // 20) for k in range(1, 21)], 'dmg',
         u"Księga Lekkie jak Piórko", 55038, u"Aktywuje na krótki czas „Bezszelestny chód”."),
}

# Odnowa (10): the pl species table gives 7000 PŻ at level 20 to a pet without the specialty (de: 7066) - pl wins:
# the de curve scaled to 7000.
SKILLS[10] = SKILLS[10][:5] + ([max(1, v * 7000 // 7066) for v in SKILLS[10][5]],) + SKILLS[10][6:]

# Activation chance (%) by skill level of the auto skills (de; the feather's 57 % at 20 like Odnowa - the wiki gives
# only 57 %).
ACTIVATE = {
    10: [2, 5, 8, 11, 14, 17, 20, 23, 25, 28, 31, 34, 37, 40, 43, 46, 49, 51, 54, 57],
    17: [2, 5, 7, 10, 13, 15, 18, 21, 23, 26, 28, 31, 34, 36, 39, 42, 44, 47, 49, 52],
    23: [2, 5, 8, 11, 14, 17, 20, 23, 25, 28, 31, 34, 37, 40, 43, 46, 49, 51, 54, 57],
}
# Duration in tenths of a second of the feather's dash ("Bezszelestny chod"; not on the wiki: 5 s). Niesmiertelnosc's
# duration is its value.
DURATION = {
    23: [50] * 20,
}
# The trigger of the auto skills (pl): Odnowa below 20 % HP; Niesmiertelnosc below 10 % HP (not on the wiki - the
# official client's habit, Anka2); Uzdrowienie while poisoned / bleeding / slowed; the feather while fighting.
FEATHER_MAX_DAMAGE = 1400

# Specialty: species -> skill -> value at skill level 20, pet level 105, per type 1..8 (pl species pages; Aamon tr/en).
# A species / skill missing here has the base curve's level 20 value. Types 7/8 of the species that cannot reach them
# repeat type 6.
SPECIALTY = {
    1: {15: [108, 108, 112, 112, 116, 116, 116, 116], 2: [130, 130, 130, 130, 140, 140, 140, 140],
        1: [130, 130, 130, 130, 140, 140, 140, 140], 16: [60, 60, 70, 70, 80, 80, 80, 80],
        10: [7066, 7066, 7133, 7133, 7200, 7200, 7200, 7200]},
    2: {5: [130, 130, 130, 130, 140, 140, 140, 140], 16: [60, 60, 70, 70, 80, 80, 80, 80],
        14: [60, 60, 70, 70, 80, 80, 80, 80], 17: [27, 27, 28, 28, 29, 29, 29, 29],
        10: [7066, 7066, 7133, 7133, 7200, 7200, 7200, 7200]},
    3: {6: [110, 110, 110, 110, 130, 130, 130, 130], 3: [130, 130, 130, 130, 140, 140, 140, 140],
        9: [110, 110, 120, 120, 130, 130, 130, 130], 16: [70, 70, 70, 70, 80, 80, 80, 80],
        10: [7133, 7133, 7200, 7200, 7333, 7333, 7333, 7333]},
    4: {7: [110, 110, 120, 120, 140, 140, 140, 140], 4: [130, 130, 130, 130, 140, 140, 140, 140],
        16: [70, 70, 70, 70, 80, 80, 80, 80], 23: [355, 355, 535, 535, 675, 675, 775, 775],
        10: [7133, 7133, 7200, 7200, 7333, 7333, 7333, 7333], 18: [470, 470, 570, 570, 670, 670, 670, 670]},
    6: {19: [110, 110, 120, 120, 140, 140, 140, 140], 20: [90, 90, 110, 110, 120, 120, 120, 120],
        13: [120, 120, 140, 140, 150, 150, 150, 150], 8: [190, 190, 200, 200, 220, 220, 220, 220],
        17: [28, 28, 29, 29, 30, 30, 30, 30], 10: [7133, 7133, 7200, 7200, 7333, 7333, 7333, 7333],
        18: [470, 470, 570, 570, 670, 670, 670, 670]},
    8: {7: [100, 100, 100, 110, 110, 110, 140, 140], 6: [80, 80, 80, 110, 110, 110, 160, 160],
        9: [110, 110, 120, 120, 130, 130, 130, 130], 16: [70, 70, 70, 70, 80, 80, 80, 80],
        10: [7133, 7133, 7200, 7200, 7200, 7200, 7200, 7200]},
    9: {6: [110, 110, 110, 110, 130, 130, 130, 130], 15: [108, 108, 112, 112, 116, 116, 116, 116],
        12: [70, 70, 80, 80, 100, 100, 100, 100], 5: [130, 130, 130, 130, 140, 140, 140, 140],
        11: [60, 60, 70, 70, 80, 80, 80, 80], 23: [375, 375, 575, 575, 575, 775, 775, 775]},
    12: {7: [110, 110, 120, 120, 140, 140, 140, 140], 6: [110, 110, 130, 130, 160, 160, 160, 160],
         20: [90, 90, 110, 110, 110, 110, 110, 120], 9: [110, 110, 120, 120, 130, 130, 130, 130],
         13: [120, 120, 130, 140, 140, 140, 150, 150], 16: [70, 70, 70, 70, 80, 80, 80, 80]},
    13: {7: [110, 110, 120, 120, 140, 140, 140, 140], 6: [110, 110, 130, 130, 160, 160, 160, 160],
         20: [90, 90, 110, 110, 110, 110, 120, 120], 9: [110, 110, 120, 120, 130, 130, 130, 130],
         13: [120, 120, 130, 140, 140, 140, 150, 150], 16: [70, 70, 70, 70, 80, 80, 80, 80]},
    14: {9: [110, 110, 120, 120, 130, 130, 130, 130], 13: [120, 120, 130, 140, 140, 140, 150, 150],
         20: [90, 90, 110, 110, 110, 110, 110, 120], 11: [60, 60, 70, 70, 80, 80, 80, 80],
         17: [28, 28, 29, 29, 30, 30, 30, 30]},
}
SPECIALTY[5] = SPECIALTY[3]     # Niebieski Maly Smok = Maly Razador (pl)
SPECIALTY[7] = SPECIALTY[2]     # Mini Azrael = Maly Pajak (pl)
SPECIALTY[10] = SPECIALTY[6]    # Nessie = Mala Meley (pl)
SPECIALTY[11] = SPECIALTY[9]    # Wylag Exedyara = Maly Baashido (pl)

# The pet levels at which a level-20 skill's value grows by one unit of its table (tr "Beceri ... seviyede artar"):
# below the first level the value is one less per level left in the list. None = it grows continuously (80 % at 81,
# 100 % at 105 - the wiki gives no numbers for these). Per species overrides below.
GROWTH_LEVELS = {
    1: [84, 94, 104], 2: [84, 94, 104], 3: [84, 94, 104], 4: [84, 94, 104], 5: [84, 94, 104],
    6: [96], 7: [92, 104], 8: [89, 103], 9: [92, 104], 10: None, 11: [105], 12: [82, 101], 13: [83, 93, 103],
    14: [105], 15: None, 16: [90], 17: None, 18: None, 19: [92, 104], 20: [96], 21: [105], 22: [105], 23: None,
}
GROWTH_LEVELS_SPECIES = {
    2: {14: [90]}, 7: {14: [90]},
    4: {7: [83, 96]},
    6: {8: [84, 99], 19: [83, 96], 13: [83, 93, 103], 20: [86, 101], 16: [105]},
    9: {6: [89, 104], 16: [105], 11: [90]},
    8: {6: [89, 104], 7: [88, 100], 11: [90]},
    12: {6: [89, 104], 9: [92, 104], 13: [83, 93, 103], 7: [92], 20: [86, 101]},
    13: {6: [89, 104], 13: [83, 93, 103], 20: [86, 101]},
    14: {9: [92, 104], 13: [83, 93, 103], 20: [86, 101], 16: [105], 11: [90]},
}
GROWTH_LEVELS_SPECIES[10] = GROWTH_LEVELS_SPECIES[6]
GROWTH_LEVELS_SPECIES[11] = GROWTH_LEVELS_SPECIES[9]

# The potential skills an egg gives a champion pet (tr egg pages), by the egg's species.
POTENTIAL = {
    1: [16, 15, 1, 2, 10], 2: [16, 14, 5, 17, 10], 3: [16, 6, 3, 9, 10], 5: [16, 6, 3, 9, 10],
    4: [16, 7, 4, 23, 10, 18], 6: [20, 13, 19, 8, 10, 17, 18], 10: [20, 13, 19, 8, 10, 17, 18],
    9: [6, 11, 12, 5, 15, 23], 11: [6, 11, 12, 5, 15, 23], 8: [6, 9, 7, 16, 10], 7: [16, 14, 5, 17, 10],
    12: [6, 13, 9, 20, 7, 16], 13: [6, 13, 9, 20, 7, 16], 14: [11, 13, 9, 20, 17],
}
# Potential skill level by the pet's champion level (tr/de): 1-14 -> 1, 15-19 -> 3, 20-24 -> 4, 25-29 -> 5, 30 -> 6;
# with the second slot open and empty at most 2.
POTENTIAL_LEVEL = [(30, 6), (25, 5), (20, 4), (15, 3), (1, 1)]

# --------------------------------------------------------------------------------------------------------------------
# Owner bonuses (0.001 % units). Start values 0.1-2.0 % (pl/tr). Per type: (every X levels, min, max) for HP, DEF, SP.
START_STAT = (100, 2000)
TYPE_GAIN = {
    1: ((6, 100, 500), (8, 100, 200), (6, 100, 500)),
    2: ((5, 200, 300), (7, 200, 300), (4, 200, 300)),
    3: ((6, 100, 700), (8, 100, 300), (6, 100, 700)),
    4: ((5, 300, 400), (7, 300, 400), (4, 300, 400)),
    5: ((6, 100, 900), (8, 100, 400), (6, 100, 900)),
    6: ((5, 500, 600), (7, 400, 500), (4, 400, 500)),
    7: ((6, 100, 1000), (8, 100, 600), (6, 100, 1100)),
    8: ((5, 500, 700), (7, 500, 600), (4, 500, 600)),
}
# Champion stats (Wola SungMa (ODP), Przebicie bloku, Precyzja): start 0.1-0.5 %, per type every X champion levels.
CHAMPION_START_STAT = (100, 500)
CHAMPION_TYPE_GAIN = {
    1: ((5, 100, 500), (5, 100, 500), (4, 100, 500)),
    2: ((4, 200, 300), (4, 200, 300), (3, 200, 300)),
    3: ((5, 100, 700), (5, 100, 700), (4, 100, 700)),
    4: ((4, 300, 400), (4, 300, 400), (3, 300, 400)),
    5: ((5, 100, 900), (5, 100, 900), (4, 100, 900)),
    6: ((4, 500, 600), (4, 500, 600), (3, 400, 500)),
    7: ((5, 100, 1000), (5, 100, 1000), (4, 100, 1100)),
    8: ((4, 500, 700), (4, 500, 700), (3, 500, 600)),
}
AGE_BONUS_MAX_DAYS = 800      # +0.001 % a day of age to every gain, up to 0.8 %
STAT_FIRST_LEVEL = 5          # the gains start at pet level 5

# --------------------------------------------------------------------------------------------------------------------
# EXP (wiki appendix: tr/en values; pl level 105 is "-"). Level -> (mob exp 90 %, item exp 10 %).
EXP = [
    (135, 15), (360, 40), (675, 75), (1125, 125), (1935, 215), (3240, 360), (4950, 550), (7650, 850), (10800, 1200),
    (14850, 1350), (19350, 2150), (26100, 2900), (34200, 3800), (45000, 5000), (58000, 6500), (76050, 8450),
    (98550, 10950), (127350, 14150), (164250, 18250), (212400, 23600), (274500, 30500), (317250, 35250),
    (365850, 40650), (421650, 46850), (484650, 53850), (556650, 61850), (638100, 70900), (730800, 81200),
    (835650, 92850), (954900, 106100), (1089450, 121500), (1242450, 138050), (1413226, 157250), (1611000, 179000),
    (1833000, 203650), (2084400, 231600), (2337300, 255300), (2572650, 285850), (2818800, 313200),
    (3076350, 341850), (3420000, 380000), (3723300, 413700), (4045500, 449500), (4388850, 487650),
    (4752000, 528000), (5134500, 570500), (5544000, 616000), (5971500, 663500), (6426000, 714000),
    (6903000, 767000), (7591500, 843500), (8532000, 948000), (8991000, 999000), (9639000, 1071000),
    (10318500, 1146500), (11061000, 1229000), (11790000, 1310000), (12582000, 1398000), (13410000, 1490000),
    (14751000, 1639000), (16227000, 1803000), (17851500, 1983500), (19638000, 2182000), (21600000, 2400000),
    (23760000, 2640000), (26136000, 2904000), (28750500, 3194500), (31626000, 3514000), (34789500, 3865500),
    (38268000, 4252000), (42093000, 4677000), (46305000, 5145000), (50940000, 5660000), (54450000, 6050000),
    (61650000, 6850000), (67815000, 7535000), (74565000, 8285000), (106645500, 11849500), (117292500, 13032500),
    (129051000, 14339000), (141921000, 15769000), (156136500, 17348500), (171756000, 19084000),
    (188896500, 20988500), (207792000, 23088000), (228618000, 25402000), (251433000, 27937000),
    (276588000, 30732000), (304258500, 33806500), (334408500, 37156500), (468549900, 52061100),
    (515404890, 57267210), (566945379, 62993931), (623639916, 69293324), (686003908, 76222656),
    (754604299, 83844922), (830064729, 92229414), (913071202, 101452355), (922500000, 102500000),
    (967500000, 107500000), (994500000, 110500000), (1012500000, 112500000), (1026000000, 114000000),
    (1039500000, 115500000), (1057500000, 117500000),
]
assert len(EXP) == 105
# Champion levels 1..30: (champion exp, item exp).
CHAMPION_EXP = [
    (173360, 37186500), (520082, 52059100), (1040165, 57264210), (1733612, 62993931), (2600421, 69293324),
    (3640596, 76222656), (4854136, 83844922), (6241041, 92229414), (7801314, 101452355), (9534954, 102500000),
    (11441962, 107500000), (13522340, 110500000), (15776087, 112500000), (18203206, 114000000),
    (20803696, 115500000), (23577558, 116500000), (26524794, 117500000), (29645403, 118500000),
    (32939388, 119500000), (36406748, 120000000), (40047484, 120500000), (43861598, 121000000),
    (47849089, 121500000), (52009960, 122000000), (56344210, 122500000), (60851840, 123000000),
    (65532852, 123500000), (70387245, 124000000), (75415022, 124500000), (80616182, 124500000),
]
assert len(CHAMPION_EXP) == 30

# --------------------------------------------------------------------------------------------------------------------
# Evolution (pl): stage -> name; the materials of each step (vnum, count) come from sources.md mapping in
# EVOLUTION below (filled by gen_pety_sql.py checks against item_proto).
STAGES = {1: u"Młody", 2: u"Dziki", 3: u"Dzielny", 4: u"Bohaterski", 5: u"Przebudzony", 6: u"Mocny"}
EVOLUTION = {
    # to stage: (needed level or champion level, needed age days, [(vnum, count, pl name)]). No age is needed any more
    # (the owner, Yohara list 3.0.14 item 8: the wiki's 30 days are old information) - the field stays, always 0.
    2: (40, 0, [(55003, 10, u"Księga Młodego Zwierza"), (30017, 10, u"Ozdobna Spinka Do Włosów"),
                (30088, 5, u"Kawałek Lodu +"), (30074, 5, u"Czarny Uniform +"), (30073, 10, u"Biała Wstęga +"),
                (30058, 10, u"Worek Z Pajęczymi Jajami"), (30041, 10, u"Shuriken")]),
    3: (80, 0, [(55004, 10, u"Księga Dzikiego Zwierza"), (27994, 2, u"Krwawa Perła"), (30031, 10, u"Ornament"),
                (30035, 10, u"Krem Do Twarzy"), (30089, 10, u"Futro Yeti +"), (30011, 10, u"Kłąb"),
                (30080, 5, u"Księga Klątw +")]),
    4: (81, 0, [(55005, 10, u"Księga Dzielnego Zwierza"), (30083, 10, u"Nieznane Lekarstwo +"),
                 (30077, 10, u"Ząb Orka +"), (30086, 10, u"Pamiątka Po Demonie +"), (27992, 2, u"Biała Perła"),
                 (27993, 2, u"Niebieska Perła"), (30550, 5, u"Niebieski Rzemyk")]),
    5: (105, 0, [(55006, 10, u"Bohat. Księga Zwierza"), (31139, 2, u"Skrzynia Berana-Setaou (PB)"),
                  (31141, 2, u"Skrzynia Razadora (PB)"), (31140, 2, u"Skrzynia Jotuna Thryma (PB)"),
                  (31142, 2, u"Skrzynia Nemere (PB)"), (31143, 5, u"Skrzynia Przebudzenia"),
                  (30602, 5, u"Niebieski Barwnik"), (30617, 10, u"Agat"), (55001, 20, u"Odżywka")]),
    6: (14, 0, [(55007, 10, u"Przeb. Księga Zwierza"), (30616, 10, u"Dwutlenek Tytanu"),
                 (31253, 5, u"Skrzynia Mistrza Gnolli"), (31254, 5, u"Skrzynia Mistrza Ahtrina"),
                 (70429, 5, u"Skarb Węży"), (31255, 5, u"Skrzynia Zdobiona Złotem"),
                 (70411, 3, u"B. Smocza Skrz. (lekka)"), (70412, 3, u"B. Smocza Skrz. (ciężka)"),
                 (55001, 40, u"Odżywka")]),
}
