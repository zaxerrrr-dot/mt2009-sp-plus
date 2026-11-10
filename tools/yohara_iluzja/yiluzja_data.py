# -*- coding: utf-8 -*-
"""MT2009_PLUS_YOHARA_ILUZJA_V1: the shared tables of Płaskowyż Iluzji and the two remaining awakened bosses - the
owner, 14 October 2026 (cache/yohara/decyzje.md, last lines: "dodać Płaskowyż Iluzji jako hub lochów PB (Statua
Przebudzenia, Handlarka Iluzji, Statua Kowala Zbroi, Statua Fabryki Broni, Teleporter); dodać Beran PB i Jotun PB").

  397 metin2_map_labyrinth           Płaskowyż Iluzji (1x1)           the hub: no monsters, level 110+
  398 metin2_map_boss_awaken_skipia  Grota Wygnańców 2 (PB) (6x6)     dungeon, quest beran_pb   (Beran-Setaou (PB))
  371 metin2_map_boss_awaken_dawnmist Zaklęty Las (PB) (3x4)          dungeon, quest jotun_pb   (Jotun Thrym (PB))

Bases: the official ones (GF 26.1.11 atlasinfo = Owsap v6.2.6). Indexes: Owsap's 371 for the forest (free here); the
plateau's official 363 and the grotto's 368 are ours already (Komnata Wiedzy, Port Nowego Kontynentu) - 397 / 398,
free in every map of ours, of every worktree and of Owsap's list (14 October 2026). The plateau is the GF folder; both
dungeons are FULL map folders in the client (the terrain of GF's metin2_map_skipia_dungeon_02 / dawnmist_dungeon_01
under the awakened name): exe 2.0.25 reads a copied map's attr.atr from the parent, and the grotto's own 000000/attr.atr
opens Beran's temple, which the normal Grota Wygnańców 2 keeps closed; the forest's parent is in no client of ours.

Sources: the pl-wiki ("Płaskowyż Iluzji", "Statua Przebudzenia", "Statua Iluzji", "Handlarka Iluzji", "Grota Wygnańców
2 (PB)", "Świątynia Smoka (PB)", "Zaklęty Las (PB)", "Erebu (PB)", "Beran-Setaou (PB)", "Jotun Thrym (PB)", the chests,
"Wytwarzanie Zbroi", "Wytwarzanie Broni", the plans; cache/yohara/wiki/iluzja), the de-wiki for what the pl-wiki leaves
out (the plans' sources, "EW: ..."), Owsap v6.2.6 (db/mob_proto.txt, item_proto.txt, cube.txt npc 20470/20473/20474,
quest/source/dungeon/boss_awaken/awaken_skipia_dungeon.quest, awaken_dawnmist_dungeon.quest and _access.quest,
labyrinth_dungeon.quest, data/dungeon/awaken_*), the Polish names of Owsap's Polish client.
"""

# -- elements (setRaceFlag bits 11-16, MT2009_PLUS_ELEMENTS_V1) -----------------------------------------------------
ELEC, FIRE, ICE, WIND, EARTH, DARK = 2048, 4096, 8192, 16384, 32768, 65536
ELEMENT_BITS = ELEC | FIRE | ICE | WIND | EARTH | DARK
ELEMENT_NAME = {ELEC: 'blyskawica', FIRE: 'ogien', ICE: 'lod', WIND: 'wiatr', EARTH: 'ziemia', DARK: 'mrok'}

# -- monsters, bosses, Metins: vnum -> (Polish name (Owsap's PL client), element (pl-wiki "Żywioł" = Owsap's AttElec /
#    AttWind 90; the Metins none), place) -------------------------------------------------------------------------------
MOBS = {
    # Grota Wygnańców 2 (PB) / Świątynia Smoka (PB) - błyskawica
    4280: ('PB: Wojownik Setaou', ELEC, 'skipia'),          # 108
    4281: ('PB: Łowca Setaou', ELEC, 'skipia'),             # 110
    4282: ('PB: Mistyk Setaou', ELEC, 'skipia'),            # 110
    4283: ('PB: Żołnierz Setaou', ELEC, 'skipia'),          # 114
    4284: ('PB: Łucznik Setaou', ELEC, 'skipia'),           # 116
    4285: ('PB: Magistrat Setaou', ELEC, 'skipia'),         # 118
    4286: ('PB: Komendant Setaou', ELEC, 'skipia'),         # 120 - Generał Yonghan (PB) summons them
    4287: ('PB: Kapitan Yonghan', ELEC, 'skipia'),          # 116 (PB-116)
    4288: ('PB: Kapitan Yonghan', ELEC, 'skipia'),          # 110 (PB-110)
    4289: ('PB: Generał Yonghan', ELEC, 'skipia'),          # 115 - Kręty Klucz (PB)
    4290: ('PB: Generał Yonghan', ELEC, 'skipia'),          # 115 - Kręty Klucz (PB)
    4410: ('PB: Beran-Setaou', ELEC, 'skipia'),             # 122, the boss
    8130: ('PB: Metin Góry', 0, 'skipia'),                  # the temple's four stones: Beran (PB) takes no blow
    8131: ('PB: Metin Zemsty', 0, 'skipia'),                #   while one of them stands (server-patches/iluzja);
                                                            #   Owsap's "PB : Metin Zemsty" without the stray space
    8132: ('PB: Metin Samotności', 0, 'skipia'),
    8133: ('PB: Metin Pychy', 0, 'skipia'),
    # Zaklęty Las (PB) / Erebu (PB) - wiatr
    4340: ('PB: Wojownik En-Tai', WIND, 'dawnmist'),        # 107 (PB-107) - 1st investigation
    4341: ('PB: Bojownik En-Tai', WIND, 'dawnmist'),        # 109
    4342: ('PB: Druid En-Tai', WIND, 'dawnmist'),           # 111 - Apteczka (PB)
    4343: ('PB: Uzdrowiciel En-Tai', WIND, 'dawnmist'),     # 112
    4344: ('PB: Niszczyciel En-Tai', WIND, 'dawnmist'),     # 113 - Rosa En-Tai (PB)
    4345: ('PB: Władca En-Tai', WIND, 'dawnmist'),          # 128 - Szlachetne Drzewo, Drzewny Szmaragd (PB)
    4347: ('PB: Wojownik En-Tai', WIND, 'dawnmist'),        # 119 - Niszczyciel En-Tai (PB-125) summons them
    4348: ('PB: Bojownik En-Tai', WIND, 'dawnmist'),        # 120
    4349: ('PB: Druid En-Tai', WIND, 'dawnmist'),           # 120
    4350: ('PB: Uzdrowiciel En-Tai', WIND, 'dawnmist'),     # 121 - Bagjanamu (PB) summons them
    4351: ('PB: Niszczyciel En-Tai', WIND, 'dawnmist'),     # 125 - Jotun Thrym (PB) summons them
    4352: ('PB: Bagjanamu', WIND, 'dawnmist'),              # 130 - Erebu's first boss
    4413: ('PB: Jotun Thrym', WIND, 'dawnmist'),            # 135, the boss
    8136: ('PB: Metin Drz. Stworzeń', 0, 'dawnmist'),      # 4th investigation
    8137: ('PB: Metin Lasu', 0, 'dawnmist'),
}

# -- MT2009_PLUS_YOHARA_RASY_V1: the races (setRaceFlag bits 0-10 - the "Silny przeciwko ..." bonuses, battle.cpp
#    CalcAttBonus) where they differ from Owsap's row. The owner, 10 November 2026: "Silny przeciwko diabłom" works on
#    every monster and boss of Zaklęty Las, its PB and its SZC - all of them are devils (the pl-wiki "Rasa = Diabły" of
#    every En-Tai / Bagjanamu / Uzdrowiciel Ochao), only Jotun Thrym was not (Owsap: ORC). Jotun Thrym (PB):
#    the pl-wiki "Jotun Thrym (PB)" gives no race ("Rasa =") - the orc goes, the devil comes.
#    The row (INSERT IGNORE) carries it and the elements' file sets bits 0-10 of these vnums every start (a world
#    made earlier, either bonus mode - M2_BONUS_MODE touches only bits 11-16). The Metins keep none (the wiki gives a
#    Metin no race).
RACE_BITS = 2047
RACE = {
    4413: 'DEVIL',                             # PB: Jotun Thrym - was ORC
}

# -- NPCs (our NPC numbers - gen_ymaps_sql.npc_row) ------------------------------------------------------------------
# Handlarka Iluzji is Owsap's 9013 - ours is Pomocnik Zdarzeń: 20469 (free), GF's "goods" look (client npclist)
NPCS = {
    20469: ('Illusions Merchant', 'Handlarka Iluzji'),
    20472: ('Time Rift Statue', 'Statua Szczeliny Czasu'),   # its plateau line and dungeon: tools/yohara_crack
    20473: ('Weaponsmith Statue', 'Statua Fabryki Broni'),
    20474: ('Armoursmith Statue', 'Statua Kowala Zbroi'),
    20530: ('RX: Ghost of a Sura', 'PB: Duch Sura'),
    20539: ('RX: Guard. of the Forest', 'PB: Strażnik Lasu'),
    20540: ('RX: Scout of the Forest', 'PB: Zwiadowca Lasu'),
    20541: ('RX: Outrider of the For.', 'PB: Badacz Lasu'),          # Owsap "Badacza" - the wiki's "Badacz Lasu (PB)"
    20542: ('RX: Forest Guard. Leader', 'PB: Przywódca St. Lasu'),
}
NPCLIST_ADD = {20469: 'goods'}          # the client's npclist (GF 9013's race)
MERCHANT = 20469
MERCHANT_SHOP = 9551                    # world.shop (9550 is Mistrz's)
# the pl-wiki "Handlarka Iluzji" rows we have (item, count): Czerwona / Niebieska Mikstura (XXL) by 20 and 200,
# Transformuj / Zaczaruj Kostium; Zegarek Kieszonkowy: tools/yohara_crack (yohara_crack.sql); left out: Sfera Losu
# Zwierzaka, Kołczan, Pergamin Więzi / Przerwania (not ours)
MERCHANT_ITEMS = [(27007, 20), (27007, 200), (27008, 20), (27008, 200), (70063, 1), (70064, 1)]

# -- the maps -----------------------------------------------------------------------------------------------------
MAPS = [
    dict(index=397, folder='metin2_map_labyrinth', src='metin2_map_labyrinth', name='Płaskowyż Iluzji',
         size=(1, 1), base=(307200, 1792000), town=(125, 125), owsap='metin2_map_labyrinth'),
    dict(index=398, folder='metin2_map_boss_awaken_skipia', src='metin2_map_skipia_dungeon_02',
         own_attr='metin2_map_boss_awaken_skipia', name='Grota Wygnańców 2 (PB)', size=(6, 6), base=(0, 1971200),
         town=(877, 722), owsap='metin2_map_boss_awaken_skipia'),
    dict(index=371, folder='metin2_map_boss_awaken_dawnmist', src='metin2_map_dawnmist_dungeon_01',
         name='Zaklęty Las (PB)', size=(3, 4), base=(332800, 1971200), town=(478, 970),
         owsap='metin2_map_boss_awaken_dawnmist'),
]

# -- the plateau's NPCs (pl-wiki cells = Owsap's npc.txt; Statua Szczeliny Czasu 103,90 is appended by the Dockerfile's
#    Szczelina Czasu step - tools/yohara_crack) -------------------------------------------------------------------------
PLATEAU_NPCS = [(20471, 153, 89, 8), (20473, 141, 181, 7), (20474, 113, 179, 3), (9012, 127, 190, 5),
                (MERCHANT, 128, 98, 1)]

# -- the villages: Statua Iluzji (20470, PB's cells) takes the player to the plateau; Statua Przebudzenia (20471) is
#    no longer there (it stands on the plateau) ------------------------------------------------------------------------
TICKET = 31146                       # Książka Przebudzenia - one a person, for every entry
MIN_LEVEL = 110
TIME_LIMIT = 60 * 60
