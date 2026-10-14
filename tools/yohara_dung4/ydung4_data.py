# -*- coding: utf-8 -*-
"""MT2009_PLUS_YOHARA_DUNG4_V1: the shared tables of the two dungeons of the fourth batch of Yohara places (the owner,
14 October 2026, cache/yohara/decyzje.md: "Jaskinie Gnolli 1/2/3 i Wieza Sung Mahi - dodac"; plan
cache/yohara/plan-mapy-yohary.md):

  382 metin2_map_maze_dungeon1  Jaskinie Gnolli (pierwszy poziom) (3x3)  open map, the official maze of GOTO portals
  383 metin2_map_maze_dungeon2  Jaskinie Gnolli (drugi poziom) (3x3)     open map
  384 metin2_map_maze_dungeon3  Jaskinie Gnolli (trzeci poziom) (3x3)    open map
  386 metin2_map_smhdungeon_01  Wieza Sung Mahi - the entrance hall (1x1) open map (portal, merchant)
  387 metin2_map_smhdungeon_02  Wieza Sung Mahi (2x2)                    dungeon (50 floors, quest wieza_sung_mahi)

Map indexes: Owsap v6.2.6's (= the official ones, the plan's table). The tower's terrain sits at another base than the
GF client's (947200 614400 is our Komnata Wiedzy, plechito_chamber_of_wisdom - the client finds a map by its base):
998400 614400, free in every map of ours, of every worktree and of the GF 26.1.11 client (checked 14 October 2026);
the client's setting.txt and atlasinfo get the same base (client-patches/client-2.0.30/tools/ydung4).

Sources of the numbers: Owsap db/mob_proto.txt (the official vnums, levels, HP...), the Polish names of Owsap's
Polish client (pack/locale/locale/pl/mob_proto = the official translation; the wiki's where they differ and fit in
24 characters), GF 26.1.11 shared/common/map/metin2_map_maze_dungeon*_point.txt (every NPC and maze portal of the
caves), the pl-wiki pages (cache of 14 October: scratchpad dung4/wiki, the TR wiki where the Polish one is silent).
"""

# -- elements (setRaceFlag bits 11-16, MT2009_PLUS_ELEMENTS_V1) -----------------------------------------------------
ELEC, FIRE, ICE, WIND, EARTH, DARK = 2048, 4096, 8192, 16384, 32768, 65536
ELEMENT_BITS = ELEC | FIRE | ICE | WIND | EARTH | DARK
ELEMENT_NAME = {ELEC: 'blyskawica', FIRE: 'ogien', ICE: 'lod', WIND: 'wiatr', EARTH: 'ziemia', DARK: 'mrok'}

# -- the monsters, bosses, Metins: vnum -> (Polish name, element bits (the pl-wiki "Zywiol"; Owsap's Att* columns
#    agree), place) ----------------------------------------------------------------------------------------------
MOBS = {
    # Jaskinie Gnolli (pierwszy poziom) - ziemia
    6800: ('Gnoll Wojownik', EARTH, 'gnolle1'),            # wiki "Gnoll Wojownik (lvl-119)"
    6801: ('Gnoll Zwiadowca', EARTH, 'gnolle1'),
    6802: ('Czarodziej Gnoll', EARTH, 'gnolle1'),
    6803: ('Gnoll Marszałek', EARTH, 'gnolle1'),
    6804: ('Mistrz Gnolli', EARTH, 'gnolle1'),              # boss, every hour (TR wiki)
    6805: ('Gnoll Kapitan', EARTH, 'gnolle1'),              # boss, every hour
    # Jaskinie Gnolli (drugi poziom) - the gnolls ziemia, the Ahtrins mrok
    6806: ('Gnoll Żołnierz', EARTH, 'gnolle2'),
    6807: ('Gnoll Szpieg', EARTH, 'gnolle2'),
    6808: ('Gnoll Mag', EARTH, 'gnolle2'),                  # wiki "Gnoll Mag (lvl-120)"
    6809: ('Komendant Gnoll', EARTH, 'gnolle2'),
    6810: ('Ahtrin Wojownik', DARK, 'gnolle2'),             # levels 2 and 3
    6811: ('Ahtrin Zwiadowca', DARK, 'gnolle2'),
    6812: ('Ahtrin Czarodziej', DARK, 'gnolle2'),
    6813: ('Ahtrin Komendant', DARK, 'gnolle2'),            # wiki "Ahtrin Komendant (lvl-124)"
    6814: ('Ahtrin Kapitan', DARK, 'gnolle2'),              # boss lvl 126, every 2 hours
    6815: ('Ahtrin Kapitan', DARK, 'gnolle2'),              # boss lvl 127, every 2 hours
    # Jaskinie Gnolli (trzeci poziom) - mrok, Mistrz Ahtrin ziemia
    6816: ('Ahtrin Szpieg', DARK, 'gnolle3'),
    6817: ('Ahtrin Wiedźmin', DARK, 'gnolle3'),
    6818: ('Ahtrin Komendant', DARK, 'gnolle3'),            # wiki "Ahtrin Komendant (lvl-127)"
    6819: ('Mistrz Ahtrin', EARTH, 'gnolle3'),              # wiki "Ahtrin Wielki Mistrz (ziemia)", every 3 hours
    6820: ('Ahtrin Wielki Mistrz', DARK, 'gnolle3'),        # wiki "Ahtrin Wielki Mistrz (mrok)", every 3 hours
}
# Wieza Sung Mahi: six sets of seven (the wiki's 30 monsters and 12 bosses), one an element - wolf, bruiser, berserker,
# warlock, butcher, the boss Wozbit (7555...) and the king Wielki Mistrz (7556...); Owsap's Att* columns give the order
TOWER_ELEMENTS = [(7550, FIRE, 'ogien'), (7557, ICE, 'lod'), (7564, ELEC, 'blyskawice'), (7571, WIND, 'wiatr'),
                  (7578, EARTH, 'ziemia'), (7585, DARK, 'mrok')]
TOWER_SET = ['Wilk Piekielnej Wieży', 'Zbir Piekielnej Wieży', 'Berserk Piekielnej Wieży', 'Wiedźmin Piek. Wieży',
             'Rzeźnik Piekielnej Wieży', 'Wóżbit Piekielnej Wieży', 'Wielki Mistrz P. Wieży']
for _first, _el, _n in TOWER_ELEMENTS:
    for _i, _name in enumerate(TOWER_SET):
        MOBS[_first + _i] = (_name, _el, 'wieza')
MOBS.update({
    # the kings of the tenth floors (all the elements: one of them a run), Owsap's 7609-7614 (fire, ice, lightning,
    # wind, earth, dark - their Att* columns)
    7609: ('Czarnoksiężnik P. Wieży', FIRE, 'wieza'),
    7610: ('Książę Piekielnej Wieży', ICE, 'wieza'),
    7611: ('Książę Piekielnej Wieży', ELEC, 'wieza'),
    7612: ('Książę Śmierci P. Wieży', WIND, 'wieza'),
    7613: ('Książę Śmierci P. Wieży', EARTH, 'wieza'),
    7614: ('Czarnoksiężnik P. Wieży', DARK, 'wieza'),
    # the chess board's pieces (Owsap "(체스)" = chess): one an element
    7615: ('Wilk Piekielnej Wieży', FIRE, 'wieza'),
    7616: ('Zbir Piekielnej Wieży', ICE, 'wieza'),
    7617: ('Rzeźnik Piekielnej Wieży', ELEC, 'wieza'),
    7618: ('Rzeźnik Piekielnej Wieży', WIND, 'wieza'),
    7619: ('Berserk Piekielnej Wieży', EARTH, 'wieza'),
    7620: ('Wiedźmin Piek. Wieży', DARK, 'wieza'),
    # the 2nd room's tasks
    7592: ('Niszczyciel P. Wieży', 0, 'wieza'),              # "Unikaj wszystkich atakow" - the wiki: no element
    7593: ('Niszczyciel P. Wieży', 0, 'wieza'),
    7594: ('Demon. Kamień P. Wieży', 0, 'wieza'),            # "Pokonaj ... demoniczne kamienie" (the archers' stone)
    7595: ('Łucznik P. Wieży', 0, 'wieza'),                  # Owsap's PL "Lucznika P. Wiezy" (a typo)
    7600: ('Kamień Duchowy P. Wieży', 0, 'wieza'),           # "Zniszcz prawidlowy kamien metin"
})

# AI flags of ours (the quest drives these pieces): the chess board's pieces stand on their squares and wait to be
# attacked (Owsap: AGGR,BERSERK - they would all charge at once); the Demon Stone's archers stand on the walls and
# wake when their stone is hit (the wiki) - the quest swaps them for aggressive ones then (group 9268)
AI_OVERRIDE = dict([(v, 'NOMOVE') for v in range(7615, 7621)] + [(7595, 'NOMOVE')])

# -- NPCs (our NPC numbers, Owsap's folder; Owsap's NPC rows lack a column - gen_ymaps_sql.npc_row) ---------------
NPCS = {
    20837: 'Wyjście',                       # Jaskinie Gnolli 1 (205,109) - back to Dongan (quest)
    20838: 'Odcinek 2',                     # Jaskinie Gnolli 1 (600,560) - to the second level (quest)
    20839: 'Odcinek 3',                     # Jaskinie Gnolli 2 (600,560) - to the third level (quest)
    20840: 'Dongan',                        # Jaskinie Gnolli 3 (600,560) - back to Dongan (quest)
    4019: 'Wejście Piekielnej Wieży',       # Seoganland (76,1459, GF's point) - the tower's hall (quest)
    4020: 'Piek. Wieża Sunga Mahi',         # the hall (122,119) - the floors; in the tower: the next room
    4021: 'Pieczęć Piekielnej Wieży',       # the tower, task "Znajdz kamien by usunac pieczec"
    9014: 'Handlarka',                      # the hall (137,142) - the wiki's "Handlarka (Wieza Sung Mahi)"
}
# Owsap's folder of an NPC whose row we write
NPC_FOLDER = {}
# Halabardnik (20836, Dongan 990,973) is a row of the first batch (yohara_maps.sql); his dialog here (jaskinie_gnolli)

# -- portals: vnum -> (type, name (the official one: "<place> x y"), Polish name). WARP (3) = global coordinates /100,
#    GOTO (9) = this map's own coordinates (char.cpp FuncCheckWarp). Owsap's Polish client's names. ---------------------
WARP, GOTO = 3, 9
PORTALS = {
    # the hall -> Seoganland (Owsap "Exit 11622 5809": 102,1457 on Seoganland, next to the hall's portal)
    10126: (WARP, 'Exit 11622 5809', 'Wyjście 11622 5809'),
}
# the caves' maze: the official GOTO portals of the three levels - level 1 10901-10924, level 2 10931-10954, level 3
# 10961-10984 (GF's points), their names = the destination on the same map (Owsap's mob_proto, = the official)
MAZE_PORTALS = list(range(10901, 10925)) + list(range(10931, 10955)) + list(range(10961, 10985))

# The races the client draws for the vnums that are new to its npclist (client 2.0.61 has every GF row)
NPCLIST_ADD = {}

# -- the maps -----------------------------------------------------------------------------------------------------
MAPS = [
    dict(index=382, folder='metin2_map_maze_dungeon1', name='Jaskinie Gnolli (pierwszy poziom)', size=(3, 3),
         base=(768000, 1203200), kind='map', pack='gnolle1_map', goto='gnolle'),
    dict(index=383, folder='metin2_map_maze_dungeon2', name='Jaskinie Gnolli (drugi poziom)', size=(3, 3),
         base=(844800, 1203200), kind='map', pack='gnolle2_map', goto=None),
    dict(index=384, folder='metin2_map_maze_dungeon3', name='Jaskinie Gnolli (trzeci poziom)', size=(3, 3),
         base=(921600, 1203200), kind='map', pack='gnolle3_map', goto=None),
    dict(index=386, folder='metin2_map_smhdungeon_01', name='Wieża Sung Mahi', size=(1, 1),
         base=(921600, 614400), kind='map', pack='wieza_hall_map', goto='wieza'),
    dict(index=387, folder='metin2_map_smhdungeon_02', name='Wieża Sung Mahi', size=(2, 2),
         base=(998400, 614400), gf_base=(947200, 614400), kind='dungeon', pack='wieza_map', goto=None),
]
