# -*- coding: utf-8 -*-
# MT2009_PLUS_WORLDBOSS_V1 - Boss Swiata (World Boss): the data gen_worldboss.py turns into the server's files.
# Source: the pl-wiki "Boss Świata" and the pages it links (copies in /opt/metin2/cache/yohara/wiki/worldboss/,
# 21 October 2026), where it says nothing the it-/ro-wiki of the same event (copies there as other_*.raw), and
# the GF 26.1.11 client for the numbers (npclist 4420-4479 - the "w_*" models of the bosses, twice the size of the
# base ones; event_reward_list.txt "world_boss" 38015 / 50033 / 83016).

# ------------------------------------------------------------------------------------------------ elements, races
ATT = {'mrok': 65536, 'lod': 8192, 'ziemia': 32768, 'blyskawica': 2048, 'ogien': 4096, 'wiatr': 16384}
ELEMENT_BITS = 129024           # setRaceFlag bits 11-16 (ATT_ELEC .. ATT_DARK) - zywioly_moby.sql's mask
RACE = {'Nieumarli': 'UNDEAD', 'Diably': 'DEVIL', 'Zwierzeta': 'ANIMAL', 'Orki': 'ORC', '': ''}
# the SET names of world.mob_proto.setRaceFlag: bit 11 (lightning) is 'SAVAGE', bit 14 (wind) 'ATT_TEMPLE'
ELEMENT_NAME = {'mrok': 'ATT_DARK', 'lod': 'ATT_ICE', 'ziemia': 'ATT_EARTH', 'blyskawica': 'SAVAGE',
                'ogien': 'ATT_FIRE', 'wiatr': 'ATT_TEMPLE'}

# ------------------------------------------------------------------------------------------------ the monsters
# The bosses: (vnum, Polish name, base vnum (the server's folder and AI, the model's motions), GF model (client
# npclist - our client has the rows already), wiki race, wiki element, minions). Every boss: level 120, rank 5
# (KING), Basis-EXP 0, no yang, no drop ("Bossowie i potwory nie dropią niczego" - it/ro-wiki), no regeneration
# ("Nie regeneruje swoich Punktów Życia"), immune to stun, slow and fear (and poison, curse - the it-wiki: "immuni a
# tutti gli status"). Their strength: Bagjanamu's (6408, our only level-120 boss of these six) figures; the health
# the game sets at the spawn (worldboss_config.hp_full x the growth - "na początku bossowie są słabi").
# Minions: (vnum, Polish name, wiki level, wiki rank (Stopień), base vnum: the model folder's own monster).
BOSSES = [
    dict(key='azrael', vnum=4449, name='Azrael (BŚ)', base=2598, model='w_zombie_bigboss2', race='Nieumarli',
         element='mrok', minions=[
             (4440, 'Piekielny Strzelec (BŚ)', 117, 2, 2509),
             (4441, 'Piekielny Włócznik (BŚ)', 118, 2, 2510),
             (4442, 'Piekielny Kapłan (BŚ)', 118, 3, 2511),
             (4443, 'Piekielny Major (BŚ)', 119, 3, 2512),
             (4444, 'Piekielny Generał (BŚ)', 120, 4, 2514)]),
    dict(key='bagjanamu', vnum=4429, name='Bagjanamu (BŚ)', base=6408, model='w_trent_boss2', race='Diably',
         element='lod', minions=[
             (4420, 'Wojownik En-Tai (BŚ)', 117, 1, 6401),
             (4421, 'Bojownik En-Tai (BŚ)', 118, 2, 6402),
             (4422, 'Druid En-Tai (BŚ)', 118, 2, 6403),
             (4423, 'Uzdrowiciel En-Tai (BŚ)', 119, 3, 6404),
             (4424, 'Niszczyciel En-Tai (BŚ)', 120, 4, 6406)]),
    dict(key='ogr', vnum=4479, name='Ogr Maximus (BŚ)', base=3891, model='w_ogre_boss2', race='Zwierzeta',
         element='ziemia', minions=[
             (4470, 'Katogr (BŚ)', 117, 2, 3801),
             (4471, 'Ogr Łucznik (BŚ)', 118, 2, 3802),
             (4472, 'Ogr Bojowy (BŚ)', 118, 3, 3803),
             (4473, 'Ogr Mag (BŚ)', 119, 3, 3804),
             (4474, 'Generał Ogg (BŚ)', 120, 4, 3805)]),
    dict(key='polifem', vnum=4439, name='Polifem (BŚ)', base=3191, model='w_cyclops_boss2', race='Orki',
         element='blyskawica', minions=[
             (4430, 'Gnoll Łucznik (BŚ)', 117, 2, 3002),
             (4431, 'Cyklop Żołnierz (BŚ)', 118, 2, 3102),
             (4432, 'Cyklop Mag (BŚ)', 118, 2, 3103),
             (4433, 'Cyklop Kat (BŚ)', 119, 3, 3104),
             (4434, 'Generał Outis (BŚ)', 120, 4, 3105)]),
    dict(key='idall', vnum=4469, name='Smoczy Strażnik Idall (BŚ)', base=6116, model='w_reddragon_human_boss',
         race='', element='ogien', minions=[
             (4460, 'Ognisty Duch Żaru (BŚ)', 117, 2, 2202),
             (4461, 'Ognisty Tygrys Żaru (BŚ)', 118, 2, 2203),
             (4462, 'Płomień Żaru (BŚ)', 118, 3, 2204),
             (4463, 'Ognisty Wojownik Żaru (BŚ)', 119, 3, 2205),
             (4464, 'Magmowy Kryształ (BŚ)', 120, 4, 6114)]),
    dict(key='tygrys', vnum=4459, name='Zjawa Żółtego Tygrysa (BŚ)', base=1304, model='w_yellow_tigerman', race='',
         element='wiatr', minions=[
             (4450, 'Drzewny Żabi Żołnierz (BŚ)', 117, 2, 1301),
             (4451, 'Drzewny Żabi Przyw. (BŚ)', 118, 2, 1302),
             (4452, 'Straszydło (BŚ)', 118, 3, 1303),
             (4453, 'Zła Zjawa Żółtego Tygrysa (BŚ)', 119, 3, 1306),
             (4454, 'Ropuszy Generał (BŚ)', 120, 4, 1305)]),
]
# The name a 24-byte column can hold (mob_proto locale_name is VARCHAR(24) in cp1250): the wiki's long names cut
# where the client's own short names are cut ("Drzewny Żabi Przyw.").
SHORT = {4453: 'Zła Zjawa Ż. Tygr. (BŚ)', 4469: 'Sm. Strażnik Idall (BŚ)', 4459: 'Zjawa Żółt. Tygrysa (BŚ)',
         4463: 'Ognisty Wojownik Ż. (BŚ)', 4450: 'Drzewny Żabi Żoł. (BŚ)', 4451: 'Drzewny Żabi Przyw. (BŚ)',
         4461: 'Ognisty Tygrys Żaru (BŚ)', 4460: 'Ognisty Duch Żaru (BŚ)', 4423: 'Uzdrowiciel En-Tai (BŚ)',
         4424: 'Niszczyciel En-Tai (BŚ)', 4444: 'Piekielny Generał (BŚ)', 4441: 'Piekielny Włócznik (BŚ)',
         4440: 'Piekielny Strzelec (BŚ)'}
# The stat template of a minion by its wiki rank: the Bagjanamu's men of Zaklety Las (level 100-108), the closest
# level our world has for every rank; their damage, health and defence grow 2 % a level up to the wiki's level.
# A man whose wiki race is not his boss's: Gnoll Łucznik (BŚ) - "Rasa = Zwierzęta" (Polifem's men are orcs).
MINION_RACE = {4430: 'Zwierzeta'}
MINION_TEMPLATE = {1: 6402, 2: 6404, 3: 6406, 4: 6406}
MINION_RANK4_HP = 1.5           # a rank-4 general: half again a rank-3's health
STAT_TEMPLATE_BOSS = 6408       # Bagjanamu: damage, defence, st/dx/ht/iq, damage multiplier of every boss
BOSS_LEVEL = 120
BOSS_HP_PROTO = 8000000         # the full strength in mob_proto (the game scales it, worldboss_config)
BOSS_AI = 'AGGR,BERSERK,STONESKIN,DEATHBLOW'      # no REVIVE (a world boss falls once)
BOSS_IMMUNE = 'STUN,SLOW,FALL,CURSE,POISON,TERROR'
MINION_IMMUNE = 'STUN,SLOW,CURSE,TERROR'           # the wiki: "Omdlewa / Spowalnia = Tak" for some - kept simple

# ------------------------------------------------------------------------------------------------ the maps
# "Boss Świata może pojawić się na następujących mapach: Dolina Seungryong, Pustynia Yongbi, Doyyumhwan oraz Góra
# Sohan." The spots: the middle of each map's own boss and big-monster groups (boss.txt of the map - open ground
# the server's regen already uses), in the map's local cells (x 100 = units). The area's name for the notice
# ("komunikat serwerowy z informacją o terroryzowanym przez bossa obszarze") is the map and its part.
MAPS = [
    (64, 'Dolina Seungryong', [(770, 757), (418, 270), (1242, 810)]),
    (63, 'Pustynia Yongbi', [(869, 658), (1309, 1073), (824, 266), (356, 722), (825, 1064)]),
    (62, 'Doyyumhwan', [(998, 463), (426, 911), (1266, 1082), (1357, 336)]),
    (61, 'Góra Sohan', [(789, 184), (194, 1156), (1349, 1210), (903, 755)]),
]
MAP_CELLS = 1536                # 6 x 6 sectors of 256 cells (each of the four maps)

# ------------------------------------------------------------------------------------------------ the rewards
KAMYKI = 95926
SKRZYNKA_TAJEMNIC = 38015       # GF's number (event_reward_list "world_boss"); new here
ZAGADKOWA = 50033               # Zagadkowa Szkatułka - ours already (special_item_group 50033)
KUPON_50 = 80017                # Kupon SM (50) - ours
KUPON_20 = 80031                # Kupon SM (20) - new (Kupon TM (20): no Tiger Coins here, Dragon Coins instead)
KUPON_10 = 80032                # Kupon SM (10) - new
# tier: (number, first rank, last rank (0 = no end), rank points, drop buff %, items)
TIERS = [
    (1, 1, 10, 10, 100, [(KAMYKI, 100), (SKRZYNKA_TAJEMNIC, 1), (ZAGADKOWA, 1), (KUPON_50, 1)]),
    (2, 11, 25, 5, 50, [(KAMYKI, 50), (ZAGADKOWA, 1), (KUPON_20, 1)]),
    (3, 26, 100, 2, 25, [(KAMYKI, 50), (ZAGADKOWA, 1), (KUPON_10, 1)]),
    (4, 101, 0, 1, 0, [(KAMYKI, 25)]),
]
DROP_BUFF_SECONDS = 2 * 60 * 60     # "buff +100% szans na wydropienie przedmiotów na 2 godziny"
# "Pokonaj Bossa Świata": Wartość Ataku +20% na 3 godziny (once a day, ro-wiki "Misiunea poate fi repetată zilnic")
MISSION_ATTACK_PCT = 20
MISSION_SECONDS = 3 * 60 * 60

# The season (8 weeks): the top 25 characters and the top 3 guilds of every kingdom. (vnum, count, days): days > 0
# is the wiki's "(60d)" - set on an item with a real-time limit (others keep their own time).
AMULET_NAZARA, MANU, BONSAI, KAMIEN_RYTUALNY, MAGICZNY_KAMIEN = 71202, 71225, 53243, 25046, 25042
BIALY_SFINKS, CZARNY_TULU, MARA_SENNA, REKAWICE = 71250, 71227, 71172, 72004
SEASON_CHAR = [
    (1, 1, [(AMULET_NAZARA, 1, 60), (MANU, 1, 60), (BONSAI, 1, 60), (KAMIEN_RYTUALNY, 1, 0), (MAGICZNY_KAMIEN, 3, 0)]),
    (2, 5, [(BIALY_SFINKS, 1, 60), (BONSAI, 1, 60), (MAGICZNY_KAMIEN, 1, 0)]),
    (6, 10, [(CZARNY_TULU, 1, 60), (BONSAI, 1, 60)]),
    (11, 25, [(MARA_SENNA, 1, 60), (BONSAI, 1, 60)]),
]
SEASON_GUILD = [
    (1, 1, [(REKAWICE, 1, 60)]),
    (2, 2, [(REKAWICE, 1, 30)]),
    (3, 3, [(REKAWICE, 1, 15)]),
]
SEASON_WEEKS = 8

# Skrzynka Tajemnic: "Zawiera losowy rzadki przedmiot." - one of the wiki's list, equal shares. Barwnik złoty
# metalik is not in our world (left out).
MYSTERY = [
    (50271, 'Skrzynia Nemere'), (54701, 'Skrzynia Bagjanamu'), (50270, 'Skrzynia Razadora'),
    (50266, 'Skrzynia Jotuna Thryma'), (54700, 'Skrzynia Berana-Setaou'), (54705, 'Skrzynia Hydry'),
    (54706, 'Skrzynia Królowej Meley'), (54707, 'Skrzynia Sm. Strażników'), (18900, 'Kamień Czerw. Płomienia'),
    (27992, 'Biała Perła'), (27994, 'Krwawa Perła'), (27993, 'Niebieska Perła'), (30616, 'Dwutlenek Tytanu'),
    (30617, 'Agat'), (30618, 'Kamień Księżycowy'),
]
ITEMS_NEW = [
    dict(vnum=SKRZYNKA_TAJEMNIC, src=ZAGADKOWA, name='Skrzynka Tajemnic',
         desc='Zawiera losowy rzadki przedmiot. Nagroda za pokonanie Bossa Świata.', icon='icon/item/38015.tga',
         gf_icon='icon/item/38015.tga'),
    dict(vnum=KUPON_20, src=KUPON_50, name='Kupon SM (20)', value0=20,
         desc='Kupon o wartości 20 Smoczych Monet. Kliknij prawym przyciskiem myszy, aby dodać je do konta.',
         icon='icon/item/80017.tga'),
    dict(vnum=KUPON_10, src=KUPON_50, name='Kupon SM (10)', value0=10,
         desc='Kupon o wartości 10 Smoczych Monet. Kliknij prawym przyciskiem myszy, aby dodać je do konta.',
         icon='icon/item/80017.tga'),
]
