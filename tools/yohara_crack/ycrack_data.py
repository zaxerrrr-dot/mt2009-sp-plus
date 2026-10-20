# -*- coding: utf-8 -*-
"""MT2009_PLUS_YOHARA_CRACK_V1: Statua Szczeliny Czasu on Płaskowyż Iluzji and the first Time Rift dungeon - Zaklęty
Las (SZC) / Erebu (SZC), Jotun Thrym (SZC) - the owner, 14 October 2026 ("Statua Szczeliny Czasu na Płaskowyżu
Iluzji, na razie tylko jeden loch: Zaklęty Las; pozostałe trzy później").

  404 metin2_map_boss_crack_dawnmist  Zaklęty Las (SZC) (3x4)   dungeon, quest jotun_szc (Jotun Thrym (SZC))
  397 metin2_map_labyrinth            Płaskowyż Iluzji           + Statua Szczeliny Czasu (20472) at the wiki's 103,90

Index: Owsap's 367 is Obrona Statku here; 404 is free in every map of ours, of every worktree and of Owsap's list
(372-403 are Owsap's / ours, 14 October 2026). Base: the official one (GF 26.1.11 atlasinfo = Owsap v6.2.6 Setting.txt):
332800 1817600 - right of Płaskowyż Iluzji (307200 1792000, 1x1), overlapping no map of our client's atlasinfo. The
terrain is GF's metin2_map_dawnmist_dungeon_01 - the same as Zaklęty Las (PB) (371); the server_attr is 371's, the
client's folder a COPIED map whose ParentMapName is our metin2_map_boss_awaken_dawnmist (client-2.0.30/tools/ycrack).

Sources: the pl-wiki ("Statua Szczeliny Czasu", "Zaklęty Las (SZC)", "Erebu (SZC)", "Zegarek Kieszonkowy", "Handlarka
Iluzji", the six SZC missions, the SZC monsters and items; cache/yohara/wiki/crack), the tr-wiki where the pl-wiki is
silent ("ZÇ: Jotun Thrym": 10-27 million Yang), Owsap v6.2.6 (db/mob_proto.txt, item_proto.txt, data/dungeon/
crack_dawnmist_dungeon, quest boss_crack/crack_dawnmist_dungeon(_access).quest, group.txt 6401-6408).
"""

# -- elements (setRaceFlag bits 11-16, MT2009_PLUS_ELEMENTS_V1) ------------------------------------------------------
WIND = 16384
ELEMENT_BITS = 2048 | 4096 | 8192 | 16384 | 32768 | 65536

# -- monsters, bosses, Metins: vnum -> (Polish name, element (pl-wiki "Element Wiatru" = Owsap's AttWind 90; the
#    Metins none)) - names as the PB ones ("PB: ..." -> "SZC: ..."), at most 24 bytes ---------------------------------
MOBS = {
    4260: ('SZC: Wojownik En-Tai', WIND),          # 107 - 1st mission (50 of them)
    4261: ('SZC: Bojownik En-Tai', WIND),          # 109
    4262: ('SZC: Druid En-Tai', WIND),             # 111 - Apteczka (SZC)
    4263: ('SZC: Uzdrowiciel En-Tai', WIND),       # 112 - Władca En-Tai (SZC) summons them
    4264: ('SZC: Niszczyciel En-Tai', WIND),       # 113 - Rosa En-Tai (SZC)
    4265: ('SZC: Władca En-Tai', WIND),            # 128 - Szlachetne Drewno, Drzewny Szmaragd (SZC)
    4267: ('SZC: Wojownik En-Tai', WIND),          # 119 - Niszczyciel En-Tai (SZC-125) summons them
    4268: ('SZC: Bojownik En-Tai', WIND),          # 120
    4269: ('SZC: Druid En-Tai', WIND),             # 120
    4270: ('SZC: Uzdrowiciel En-Tai', WIND),       # 121 - Bagjanamu (SZC) summons them
    4271: ('SZC: Niszczyciel En-Tai', WIND),       # 125 - Jotun Thrym (SZC) summons them (pl-wiki)
    4272: ('SZC: Bagjanamu', WIND),                # 130 - Erebu's first boss
    4403: ('SZC: Jotun Thrym', WIND),              # 135, the boss
    8126: ('SZC: Metin Drz. Stworzeń', 0),         # 2nd reconnaissance (5 of them)
    8127: ('SZC: Metin Lasu', 0),
}
# the pl-wiki where Owsap's row differs: Jotun Thrym (SZC) "Przywołuje Niszczycieli En-Tai (SZC-125)" (Owsap: the 113
# one); the tr-wiki's yang of Jotun Thrym (SZC) ("10.000.000-27.000.000 Yang düşer"). MT2009_PLUS_MOBY_ARKUSZ_V1: the
# experience of 4267 / 4270 is Owsap's again (41 001 / 61 350) - the owner's sheet of 20 October 2026 has it so (the
# pl-wiki's 41 101 / 49 080 were the outliers)
OVERRIDE = {
    4403: dict(SummonVnum='4271', MinGold='10000000', MaxGold='27000000'),
}

# -- NPCs (our NPC numbers - gen_ymaps_sql.npc_row); Statua Szczeliny Czasu 20472 is yohara_iluzja.sql's row --------
NPCS = {
    20519: ('TR: Guard. of the Forest', 'SZC: Strażnik Lasu'),
    20520: ('TR: Scout of the Forest', 'SZC: Zwiadowca Lasu'),
    20521: ('TR: Outrider of the For.', 'SZC: Badacz Lasu'),
    20522: ('TR: Forest Guard. Leader', 'SZC: Przywódca St. Lasu'),
}
STATUE = 20472
MERCHANT_SHOP = 9551                    # Handlarka Iluzji (yohara_iluzja.sql)
WATCH = 31147                           # Zegarek Kieszonkowy - the pl-wiki's shop rows: 1, 10, 100 (25 000 Yang each)
WATCH_ROWS = [(WATCH, 1), (WATCH, 10), (WATCH, 100)]

# -- the map ----------------------------------------------------------------------------------------------------------
MAP = dict(index=404, folder='metin2_map_boss_crack_dawnmist', src='metin2_map_dawnmist_dungeon_01',
           pb_folder='metin2_map_boss_awaken_dawnmist', name='Zaklęty Las (SZC)', size=(3, 4),
           base=(332800, 1817600), town=(478, 970), owsap='metin2_map_boss_crack_dawnmist')
PLATEAU = dict(index=397, folder='metin2_map_labyrinth', base=(307200, 1792000))
STATUE_CELL = (103, 90, 2)              # pl-wiki "Statua Szczeliny Czasu": Płaskowyż Iluzji 103,90 (Owsap's npc.txt: dir 2)
LANDING = (106, 96)                     # the way back from the dungeon: beside the statue (checked walkable)
MIN_LEVEL = 110
TIME_LIMIT = 60 * 60
