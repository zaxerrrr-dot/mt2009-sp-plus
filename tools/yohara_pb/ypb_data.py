# -*- coding: utf-8 -*-
"""MT2009_PLUS_YOHARA_PB_V1: the shared tables of the awakened bosses (Przebudzeni bossowie) - Razador (PB) and Nemere
(PB) - the owner, 14 October 2026 (cache/yohara/decyzje.md, "14.10 ok. 8:10": "Przebudzeni bossowie: Razador (PB) i
Nemere (PB) - dodac wg wiki (zrodlo materialow Mrocznego Smoka)").

  369 metin2_map_boss_awaken_flame  Twierdza Czerwonego Smoka (PB) (3x3)  dungeon, quest razador_pb
  370 metin2_map_boss_awaken_snow   Strażnica Nemere (PB) (4x3)           dungeon, quest nemere_pb

Both maps are copies of our Razador / Nemere terrain (351 metin2_map_n_flame_dungeon_01, 352 metin2_map_n_snow_
dungeon_01) at the official base positions: the client's map folder carries only setting.txt and mapproperty.txt
("ParentMapName", the exe's copied map - GameLib/MapBase.cpp), as the GF 26.1.11 client has them. Map indexes and
bases: Owsap v6.2.6 (= the official ones; free in every map of ours, of every worktree and of the client, 14 October
2026). The normal Razador / Nemere dungeons (351/352, quests razador_dungeon / nemere_dungeon) stay as they are.

Sources: the pl-wiki ("Razador (PB)", "Nemere (PB)", "Twierdza Czerwonego Smoka (PB)", "Strażnica Nemere (PB)",
"Statua Przebudzenia", "Statua Iluzji", "Płaskowyż Iluzji", "Książka Przebudzenia", "Codzienna misja: Świat Iluzji",
the chests and the materials - cache of 14 October: the scratchpad's pb/wiki), Owsap v6.2.6 (db/mob_proto.txt and
item_proto.txt - the official vnums and numbers; quest/source/dungeon/boss_awaken/awaken_flame_dungeon.quest and
awaken_snow_dungeon.quest - the stages, positions and odds; data/dungeon/awaken_*_dungeon - the rooms' spawns), the
Polish names of Owsap's Polish client (pack/locale/locale/pl/mob_proto, itemdesc.txt = the official translation), the
GF 26.1.11 client (attr.atr of the parent maps, the races, the icons).
"""

# -- elements (setRaceFlag bits 11-16, MT2009_PLUS_ELEMENTS_V1) -----------------------------------------------------
ELEC, FIRE, ICE, WIND, EARTH, DARK = 2048, 4096, 8192, 16384, 32768, 65536
ELEMENT_BITS = ELEC | FIRE | ICE | WIND | EARTH | DARK
ELEMENT_NAME = {ELEC: 'blyskawica', FIRE: 'ogien', ICE: 'lod', WIND: 'wiatr', EARTH: 'ziemia', DARK: 'mrok'}

# -- the monsters, bosses, Metins: vnum -> (Polish name (Owsap's PL client = the official), element (the pl-wiki
#    "Zywiol": every monster of the fortress fire, of the watchtower ice; Owsap's AttFire / AttIce 90 agree; the
#    Metins none - the wiki gives a Metin none), place) ---------------------------------------------------------------
MOBS = {
    # Twierdza Czerwonego Smoka (PB) - ogien
    4300: ('PB: Ognisty Duch Żaru', FIRE, 'flame'),         # wiki "Ognisty Duch Żaru (PB)", lvl 110
    4301: ('PB: Ognisty Tygrys Żaru', FIRE, 'flame'),       # 112
    4302: ('PB: Płomień Żaru', FIRE, 'flame'),              # 112-113
    4303: ('PB: Og. Wojownik Żaru', FIRE, 'flame'),         # 113
    4304: ('PB: Ognisty Król Żaru', FIRE, 'flame'),         # 116
    4305: ('PB: Ognisty Troll Żaru', FIRE, 'flame'),        # 116
    4306: ('PB: Ognista Broda Żaru', FIRE, 'flame'),        # 118
    4307: ('PB: Og. Generał Żaru', FIRE, 'flame'),          # 118 - Razador (PB) summons them (max. 3)
    4308: ('PB: Ognisty Książę Żaru', FIRE, 'flame'),       # 120
    4309: ('PB: Ignator', FIRE, 'flame'),                   # 120, the 4th zone's target
    4411: ('PB: Razador', FIRE, 'flame'),                   # 130, the boss
    8134: ('PB: Metin Purgatorium', 0, 'flame'),            # the 6th zone's target
    # Strażnica Nemere (PB) - lod
    4320: ('PB: Kryształ Mrozu', ICE, 'snow'),              # 110
    4321: ('PB: Mroźny Robak', ICE, 'snow'),                # 110
    4322: ('PB: Mroźny Człowiek', ICE, 'snow'),             # 113
    4323: ('PB: Mroźny Yeti', ICE, 'snow'),                 # 113
    4324: ('PB: Mroźny Golem', ICE, 'snow'),                # 116
    4325: ('PB: Mroźny Troll', ICE, 'snow'),                # 116
    4326: ('PB: Mroźna Broda', ICE, 'snow'),                # 118
    4327: ('PB: Mroźny Generał', ICE, 'snow'),              # 118 - Nemere (PB) summons them (max. 3)
    4328: ('PB: Mroźny Książę', ICE, 'snow'),               # 120 (the wiki leaves the element out; Owsap AttIce 90)
    4329: ('PB: Szel', ICE, 'snow'),                        # 120, the 4th / 7th floor's boss
    4412: ('PB: Nemere', ICE, 'snow'),                      # 130, the boss
    8135: ('PB: Metin Chłodu', 0, 'snow'),                  # the 6th floor - only a Shaman damages it
    20538: ('PB: Kolumna Smoka Płn.', 0, 'snow'),           # the 9th floor - only a Shaman or a Ninja damages it
}
# the stones whose damage only some classes may deal (the pl-wiki; server-patches/przebudzeni)
JOB_ONLY = {8135: 'SHAMAN', 20538: 'SHAMAN,ASSASSIN'}

# -- NPCs (our NPC numbers - gen_ymaps_sql.npc_row; Owsap's folder) ---------------------------------------------------
NPCS = {
    20470: 'Statua Iluzji',                 # Yongan / Joan / Pyungmoo (the wiki's cells): Codzienna misja Swiat Iluzji
    20471: 'Statua Przebudzenia',           # on Plaskowyz Iluzji (MT2009_PLUS_YOHARA_ILUZJA_V1): the four dungeons
    20531: 'PB: Gardziel Am-heha',          # the fortress' task giver
    20532: 'PB: Nagrobek Taramora',         # the fortress' boss room (scenery, as Owsap's npc.txt)
    20533: 'PB: Stela Isfet',               # the 2nd and the 5th zone
    20534: 'PB: Zamek Losu',                # the six zones' locks
    20535: 'PB: Smocza Brama',              # the six zones' gates (Owsap: a DOOR - our gates are NPCs, 20388)
    20536: 'PB: Lodowy Lew',                # the watchtower: the start, and the 10th floor's way (after the pillar)
    20537: 'PB: Arktyczna Kostka',          # the 5th floor's five cubes
}

# -- the maps -----------------------------------------------------------------------------------------------------
MAPS = [
    dict(index=369, folder='metin2_map_boss_awaken_flame', parent='metin2_map_n_flame_dungeon_01',
         name='Twierdza Czerwonego Smoka (PB)', size=(3, 3), base=(153600, 1971200), town=(342, 584)),
    dict(index=370, folder='metin2_map_boss_awaken_snow', parent='metin2_map_n_snow_dungeon_01',
         name='Strażnica Nemere (PB)', size=(4, 3), base=(230400, 1971200), town=(171, 270)),
]

# -- the entrance: Statua Iluzji (the pl-wiki's cells in the three first villages) - the daily mission and the way to
#    Plaskowyz Iluzji, where Statua Przebudzenia stands (MT2009_PLUS_YOHARA_ILUZJA_V1, tools/yohara_iluzja; the
#    second cells below are where she stood beside the village statue before). map index, folder, Statua Iluzji x, y,
#    the old Statua Przebudzenia x, y (local cells; measured walkable on our server_attr, gen_ypb.py) ------------------
STATUES = [
    (1, 'metin2_map_a1', 'Yongan', (540, 500), (544, 500)),
    (21, 'metin2_map_b1', 'Joan', (688, 748), (692, 748)),
    (41, 'metin2_map_c1', 'Pyungmoo', (342, 800), (346, 800)),
]

# -- the dungeons' quest numbers (Owsap's awaken_*_dungeon.quest = the official ones) ---------------------------------
TICKET = 31146                       # Książka Przebudzenia - one a person, for every entry
MIN_LEVEL = 110
TIME_LIMIT = 60 * 60
