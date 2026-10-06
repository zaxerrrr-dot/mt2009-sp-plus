# -*- coding: utf-8 -*-
# MT2009_PLUS_AREZZO_COSTUME_SETS_V1 / _V2 - the Arezzo costume sets (owner, 6 October 2026: "Dodaj
# również wszystkie sety kostiumów z Arezzo, ale bez żadnych dodatkowych bonusów; mają działać
# dokładnie tak jak nasze, czyli bonus za set + bonusowanie 3 bonusów i miksowanie zaczarowaniami
# u handlarki").  The one source of truth for the server rows (gen_azcostume.py writes the SQL and
# costume_sets.txt lines), the client rows (patch_azcostume_client.py) and the asset list.
#
# Arezzo defines a set as the items one look shares (its item shop pages): a costume (m)/(k), a
# helmet / hairstyle (m)/(k), six weapon skins (sword, dagger, bow, two-handed, bell, fan - the
# seventh, a wolfman claw, is left out: no wolfman here), and a back piece Arezzo wears in its own
# "stole" slot (wings / a cape), here a sash skin ("nakladka na szarfe", see SKIN_* below).
#
# vnums: Arezzo's own costumes 41900-41963 clash with our wiki sets (Osmy Zestaw Halloweenowy,
# Zbroja Szczodrego, Toreador, Atlantyda, Wukong, Lampa Lorda, Straznik Piasku...), so a body
# moves by +1000 (42900-42963, a free block on the server, in the client's item_proto,
# gf_official_costumes.txt, item_list.txt and every msm ShapeIndex); its shape index (value3) is
# the new vnum.  Hairstyles 45900-45963 and weapon skins 40600-40995 are free and keep Arezzo's
# numbers (the hair index = the vnum, as at Arezzo).  The back pieces 85500-85521 move to
# 85200-85221: the client takes a sash part number with (vnum % 1000) >= 500 as "the glowing sash
# + 500" (InstanceBase.cpp SetAcce), so a skin must sit below x500.
#
# Arezzo's own extras are dropped (owner: "bez żadnych dodatkowych bonusów"): no built-in applies
# (Arezzo gives e.g. +2000 HP / +15% vs monsters / +50 attack to the Joker set, +5% / +5 to wings)
# and no 3-day limits.  Like our ItemShop costumes ("+" ones): 30 days from the first use
# (LIMIT_REAL_TIME_START_FIRST_USE 2592000), anti flags drop | PK drop | stack + the sex / class
# bits, specular 100, three costume bonuses through 70063 / 70064 and the costume bonus transfer,
# set bonus = ours (costume_sets.txt: a body and a hair of one set: +800 HP, +15 attack value).
#
# Each set: key, Polish set name (costume_sets.txt, no spaces there), the word for the items,
#   body (m, k) Arezzo vnums, hair (m, k) Arezzo vnums, weapon skins [(arezzo vnum, name)],
#   back piece Arezzo vnum or 0, and the item names.
# Left out: Arezzo's 41912-41919 / 45912-45919 ("Kostium", no icon, no item_list line - unused
# there), the blue Chinese costume 41920-41923 / 45920-45923 (its icons icon/costume/blue_chinese_*
# are in none of Arezzo's packs), the 30-day duplicates (41902/41903, 41906/41907, 41910/41911...),
# the wolfman claws (value3 8; no wolfman here) and the mounts 52900-52913 (no set bonus, and each
# needs a new monster with its model - a separate job).

BODY_SHIFT = 1000          # Arezzo body 419xx -> ours 429xx
SKIN_SHIFT = -300          # Arezzo back piece 855xx -> our sash skin 852xx

LIMIT_DAYS30 = (7, 2592000)  # LIMIT_REAL_TIME_START_FIRST_USE, 30 days (our "+" costumes)
ANTI_BASE = 128 | 16384 | 32768   # drop | PK drop | stack (49280), as our ItemShop costumes / hairs
ANTI_WEAPON_BASE = 128 | 32768    # drop | stack (32896), as our ItemShop weapon skins (32928 a sword)
MAGIC_PCT = 100                   # our ItemShop costumes roll their costume bonuses when made
ANTI_FEMALE, ANTI_MALE = 1, 2     # "(m)" items carry ANTI_FEMALE (male only), "(k)" ANTI_MALE
ANTI_WARRIOR, ANTI_ASSASSIN, ANTI_SURA, ANTI_SHAMAN = 4, 8, 16, 32
SPECULAR = 100

# weapon skin: value3 = weapon type, size and the classes that may NOT wear it (Arezzo's bits).
WEAPON_KINDS = {
    0: (u'Miecz', 2, ANTI_SHAMAN),                                # warrior, ninja, sura
    1: (u'Sztylet', 1, ANTI_WARRIOR | ANTI_SURA | ANTI_SHAMAN),   # ninja
    2: (u'Łuk', 2, ANTI_WARRIOR | ANTI_SURA | ANTI_SHAMAN),       # ninja
    3: (u'Ostrze', 3, ANTI_ASSASSIN | ANTI_SURA | ANTI_SHAMAN),   # warrior (two-handed)
    4: (u'Dzwon', 1, ANTI_WARRIOR | ANTI_ASSASSIN | ANTI_SURA),   # shaman
    5: (u'Wachlarz', 1, ANTI_WARRIOR | ANTI_ASSASSIN | ANTI_SURA),  # shaman
}

# (key, set name, item genitive / adjective, body (m,k), hair (m,k), hair word, first weapon vnum
#  (six in a row: sword, dagger, bow, two-handed, bell, fan) or 0, back piece or 0)
SETS = (
    ('mrok',      u'Zestaw_Mroku',               u'Mroku',             (41900, 41901), (45900, 45901), u'Hełm', 40900, 85500),
    ('chwala',    u'Zestaw_Chwaly',              u'Chwały',            (41904, 41905), (45904, 45905), u'Hełm', 40910, 85501),
    ('druid',     u'Zestaw_Druida',              u'Druida',            (41908, 41909), (45908, 45909), u'Hełm', 40920, 85502),
    ('zlocisty',  u'Zestaw_Zlocisty',            u'Złocisty',          (41924, 41925), (45924, 45925), u'Hełm', 0, 0),
    ('wiking',    u'Zestaw_Wikinga',             u'Wikinga',           (41926, 41927), (45926, 45927), u'Hełm', 40940, 85503),
    ('mroz',      u'Zestaw_Mroznego_Rycerza',    u'Mroź. Rycerza',     (41928, 41929), (45928, 45929), u'Hełm', 40950, 85504),
    ('ogien',     u'Zestaw_Ognistego_Rycerza',   u'Ognist. Rycerza',   (41930, 41931), (45930, 45931), u'Hełm', 40960, 85505),
    ('aniol',     u'Zestaw_Anielski',            u'Anielski',          (41932, 41933), (45932, 45933), u'Hełm', 40970, 85506),
    ('cien',      u'Zestaw_Cienia',              u'Cienia',            (41934, 41935), (45934, 45935), u'Hełm', 40980, 85507),
    ('ksiezyc',   u'Zestaw_Ksiezycowy',          u'Księżycowy',        (41936, 41937), (45936, 45937), u'Hełm', 40990, 85508),
    ('szmaragd',  u'Zestaw_Szmaragdowego_Wladcy', u'Szmaragd. Władcy', (41938, 41939), (45938, 45939), u'Hełm', 40800, 85509),
    ('lesny',     u'Zestaw_Lesnego_Ksiecia',     u'Leśnego Księcia',   (41940, 41941), (45940, 45941), u'Hełm', 40810, 85510),
    ('plaga',     u'Zestaw_Plagi',               u'Plagi',             (41942, 41943), (45942, 45943), u'Hełm', 40820, 85511),
    ('krollodu',  u'Zestaw_Krola_Lodu',          u'Króla Lodu',        (41944, 41945), (45944, 45945), u'Hełm', 40830, 85512),
    ('krwawa',    u'Zestaw_Krwawej_Zemsty',      u'Krwawej Zemsty',    (41946, 41947), (45946, 45947), u'Hełm', 40840, 85513),
    ('lato',      u'Zestaw_Letniej_Chwaly',      u'Letniej Chwały',    (41948, 41949), (45948, 45949), u'Hełm', 40850, 85514),
    ('wiatr',     u'Zestaw_Blekitnego_Wiatru',   u'Błk. Wiatru',       (41950, 41951), (45950, 45951), u'Hełm', 40860, 85515),
    ('arktyka',   u'Zestaw_Arktycznego_Krola',   u'Arkt. Króla',       (41952, 41953), (45952, 45953), u'Hełm', 40870, 85516),
    ('upior',     u'Zestaw_Upiornej_Nocy',       u'Upiornej Nocy',     (41954, 41955), (45954, 45955), u'Hełm', 40880, 85517),
    ('niebsmok',  u'Zestaw_Niebieskiego_Smoka',  u'Nieb. Smoka',       (41958, 41959), (45958, 45959), u'Hełm', 40700, 85519),
    ('zlsmok',    u'Zestaw_Zlotego_Smoka',       u'Złotego Smoka',     (41960, 41961), (45960, 45961), u'Hełm', 40710, 85520),
    ('joker',     u'Zestaw_Jokera',              u'Jokera',            (41962, 41963), (45962, 45963), u'Czapka', 40600, 85521),
)

# MT2009_PLUS_AREZZO_COSTUME_SETS_V2 (owner, 6 October 2026: "wywal zestawy: Krwawej zemsty i
# ognistego rycerza" - their costumes, weapons and sashes show no effect): two of the 22 sets of V1 are
# gone. Every other vnum stays; their rows are what REMOVED_SETS gives (gen_azcostume_server.py writes
# the clean-up: item_proto, both ItemShops, the players' items, the sash skin on a sash).
REMOVED_SETS = ()
# MT2009_PLUS_AREZZO_COSTUME_SETS_V3 (owner, 6 October 2026: "dodaj również w takim razie te dwa sety
# kostiumów co usunęliśmy ... a jak teraz będą działać to git"): the effects were missing because of the
# effect textures' sub-folders (build_azcostume.py file_refs, V3), not because of the sets - both are
# back in SETS with their V1 vnums and ItemShop indexes. A world that ran V2 got them deleted; the
# apply.sh block gives the in-game ItemShop their lines back once (ishop_once arezzo_costume_sets_v3),
# the item rows and web offers come back by themselves (INSERT IGNORE / NOT EXISTS at every start).
RESTORED_V3 = ('ogien', 'krwawa')
# The V1 order of the sets: the in-game ItemShop's indexes (10600+ / 20600+ / 30600+ / 30800+) were given
# in it, and a line keeps its index (a removed set leaves a gap; test_dbeditor_itemshop's BOOT_ONCE).
SETS_V1_ORDER = ('mrok', 'chwala', 'druid', 'zlocisty', 'wiking', 'mroz', 'ogien', 'aniol', 'cien', 'ksiezyc',
                 'szmaragd', 'lesny', 'plaga', 'krollodu', 'krwawa', 'lato', 'wiatr', 'arktyka', 'upior',
                 'niebsmok', 'zlsmok', 'joker')


def removed_vnums():
    """Our vnums of every item of REMOVED_SETS (bodies moved by BODY_SHIFT, sash skins by SKIN_SHIFT)."""
    out = []
    for key, name, word, bodies, hairs, hair_word, first_weapon, back in REMOVED_SETS:
        out += [v + BODY_SHIFT for v in bodies] + list(hairs)
        out += [first_weapon + i for i in range(6)] if first_weapon else []
        out += [back + SKIN_SHIFT] if back else []
    return sorted(out)


# Arezzo's item_list gives two weapon skins no line and the Blekitny Wiatr fan the bell's files;
# the files are in Arezzo's packs under the usual names (icon, model).
WEAPON_FIX = {
    40864: (u'icon/item/ch2022_2_bell.tga', u'd:/ymir work/item/weapon/plechito/christmas2022_2/ch2022_2_bell.gr2'),
    40865: (u'icon/item/ch2022_2_fan.tga', u'd:/ymir work/item/weapon/plechito/christmas2022_2/ch2022_2_fan.gr2'),
    40994: (u'icon/item/hfm_bell.tga', u'd:/ymir work/item/weapon/plechito/halfmoon_set/hfm_bell.gr2'),
}
