# -*- coding: utf-8 -*-
"""MT2009_PLUS_YOHARA_ZAKLETY_V1: Zaklęty Las (Enchanted Forest) and Erebu - the open forest of Jotun Thrym past the
Temple of Ochao (the owner, 14 October 2026: "usuń Zaczarowany Las z Arezzo, dodaj oficjalny Zaklęty Las").

  353 metin2_map_dawnmist_dungeon_01  Zaklęty Las (3x4)  an open map from level 95 (pl-wiki "Zaklęty Las"), the seven
                                      missions of the forest's guards (quest zaklety_las) and Erebu - a private copy of
                                      the same map's boss corner for a party with Kamień Driad (quest erebu: Bagjanamu,
                                      a minute later Jotun Thrym)

The way in (pl-wiki "Świątynia Ochao", "Strażnik En-Tai"): Straznik En-Tai (6400) falls in the Temple of Ochao (209),
his Portal (20415) stands a minute - its first choice is Zaklęty Las now (quest temple_of_the_ochao). Not a Yohara or
Sung Ma map (no Sung Ma on the wiki's page); it lives on the Yohara core (bin/m2-render-config) beside the PB / SZC
forests, so no bot goes there.

Index 353: Owsap's for this map (dawnmist_dungeon.quest ENTRY_MAP_INDEX), free in every map of ours, of every
worktree and branch (14 October 2026). Base: the official one (GF 26.1.11 atlasinfo = Owsap's Setting.txt): 768000
1408000, 3x4 - overlapping no map of our client's atlasinfo (checked by the generator and the client builder). The
terrain is GF's metin2_map_dawnmist_dungeon_01 - the same as Zaklęty Las (PB) (371) and (SZC) (404); the server_attr
is 371's (GF's attr.atr cell for cell, checked), the client's folder a COPIED map whose ParentMapName is our
metin2_map_boss_awaken_dawnmist (client-2.0.30/tools/yzaklety).

Sources: the pl-wiki ("Zaklęty Las", "Erebu", "Jotun Thrym", "Bagjanamu", "Władca En-Tai", the En-Tai monsters and
"Silny" ones, "Uzdrowiciel Ochao", "Metin Drzewnych Stworzeń", "Metin Lasu", the seven missions, "Kamień Driad",
"Skrzynia Jotuna Thryma", "Skrzynia Bagjanamu", the forest's NPCs), the tr-wiki where the pl-wiki is silent ("Jotun
Thrym": 10-27 million Yang), Owsap v6.2.6 (db/mob_proto.txt, item_proto.txt, map/metin2_map_dawnmist_dungeon_01,
group.txt 6311-6318 / 6330-6333, dawnmist_dungeon(_access).quest, data/monster/trent_*), Ameria's spawns compared
(theirs: aggregated groups and Metins every 10 s - Owsap's kept).
"""

# -- elements (setRaceFlag bits 11-16, MT2009_PLUS_ELEMENTS_V1) ------------------------------------------------------
ICE, WIND, EARTH = 8192, 16384, 32768
ELEMENT_BITS = 2048 | 4096 | 8192 | 16384 | 32768 | 65536

# -- monsters, bosses, Metins: vnum -> (Polish name (pl-wiki), element (pl-wiki "Żywioł")) - the official vnums,
#    every one free in our world; at most 24 bytes in cp1250 --------------------------------------------------------
MOBS = {
    6401: ('Wojownik En-Tai', WIND),            # 100 - "Pierwszy rekonesans" (50 of them)
    6402: ('Bojownik En-Tai', WIND),            # 102
    6403: ('Druid En-Tai', WIND),               # 104 - "Znajdź apteczkę" (Apteczka)
    6404: ('Uzdrowiciel En-Tai', WIND),         # 105 - Władca En-Tai / Bagjanamu summon them
    6406: ('Niszczyciel En-Tai', WIND),         # 108 - "Zdobądź Rosy En-Tai" (Rosa En-Tai)
    6407: ('Władca En-Tai', ICE),               # 112 BOSS - "Zabij władcę En-Tai" (Szlachetne Drewno, Drzewny Szmaragd)
    6408: ('Bagjanamu', ICE),                   # 120 BOSS - Erebu's first boss
    6409: ('Uzdrowiciel Ochao', WIND),          # 110 - Jotun Thrym summons them (Erebu)
    6410: ('Silny Wojownik En-Tai', WIND),      # 117 - Metin Lasu calls them
    6411: ('Silny Bojownik En-Tai', WIND),      # 118
    6412: ('Silny Druid En-Tai', WIND),         # 118
    6413: ('Silny Uzdrowiciel En-Tai', WIND),   # 119
    6414: ('Silny Niszczyciel En-Tai', WIND),   # 120 - summons Silni Wojownicy En-Tai (Owsap)
    6192: ('Jotun Thrym', EARTH),               # 123 - Erebu's boss
    8059: ('Metin Drzewnych Stworzeń', 0),      # 100 - "Drugi rekonesans" (5 of them)
    8061: ('Metin Lasu', 0),                    # 120
}
# the pl-wiki over Owsap: Jotun Thrym summons Uzdrowiciele Ochao ("Erebu": "przywołuje 4 respy Uzdrowicieli Ochao";
# Owsap: Niszczyciel En-Tai) and drops 10-27 million Yang (tr-wiki "Jotun Thrym"). MT2009_PLUS_MOBY_ARKUSZ_V1: Bojownik
# En-Tai's experience is Owsap's again (28 934, the owner's sheet of 20 October 2026; the pl-wiki's 27 356 is gone)
OVERRIDE = {
    6192: dict(SummonVnum='6409', MinGold='10000000', MaxGold='27000000'),
}

# -- NPCs: our numbers where the official ones are taken (20409-20411 are Królewski Łucznik in Orc Valley here) -
#    the official races (GF npclist 20409-20412: redguild_guard_M / _M_2 / _M_3, jinno_patrol_spear) ---------------
NPCS = {
    20160: ('Guardian of the Forest', 'Strażnik Lasu', 'redguild_guard_M'),       # official 20409
    20161: ('Scout of the Forest', 'Zwiadowca Lasu', 'redguild_guard_M'),          # official 20410 (_M_2)
    20162: ('Outrider of the Forest', 'Badacz Lasu', 'redguild_guard_M'),          # official 20411 (_M_3)
    20412: ('Forest Guardian Leader', 'Przywódca Straż. Lasu', 'jinno_patrol_spear'),
}
NPC_RACE = {20160: 'redguild_guard_M', 20161: 'redguild_guard_M_2', 20162: 'redguild_guard_M_3'}   # client npclist
GUARD, SCOUT, OUTRIDER, LEADER = 20160, 20161, 20162, 20412
TEMPLE_GUARD = 20426                    # Strażnik Świątyni on Zbocze Gautama (302) - temple_of_the_ochao.quest
TELEPORTER = 9012

# -- the map ----------------------------------------------------------------------------------------------------------
MAP = dict(index=353, folder='metin2_map_dawnmist_dungeon_01', src='metin2_map_dawnmist_dungeon_01',
           pb_folder='metin2_map_boss_awaken_dawnmist', name='Zaklęty Las', size=(3, 4), base=(768000, 1408000),
           town=(478, 970), owsap='metin2_map_dawnmist_dungeon_01')
# npc.txt: the wiki's cells (Strażnik Lasu 495,963, Zwiadowca 680,400, Badacz 125,495, Przywódca 615,108, Teleporter
# 477,984); the directions Owsap's / Ameria's
NPC_CELLS = [(GUARD, 495, 963, 5), (SCOUT, 680, 400, 5), (OUTRIDER, 125, 495, 5), (LEADER, 615, 108, 5),
             (TELEPORTER, 477, 984, 4)]
# Erebu: the boss corner (Owsap: DUNGEON_ENTRY_POS 7780,15020 = local 100,940; the boss 69,941; the open map's
# corner x < 200, y > 800 is the instance's only - a player standing there on the open map is put at the entry)
EREBU_ENTRY = (100, 940)
EREBU_BOSS = (69, 941)
EREBU_CORNER = (200, 800)
# the way out of Erebu and the landing of the temple's portal: the open map's Town.txt cell; beside Przywódca
LEADER_SIDE = (611, 107)

# -- the spawns: Owsap's files (Owsap's group numbers kept - free here), Władca En-Tai's group 6318 at the wiki's
#    boss point. Metin Lasu (8061) calls groups 6330-6333 (its row's attack/move speed): Owsap's numbers, the
#    wiki's members (the "Silny" En-Tai) -------------------------------------------------------------------------------
GROUPS_OWSAP = list(range(6311, 6319))
GROUPS_STRONG = {
    6330: ('Silni_En-Tai_1', [6410, 6410, 6410]),
    6331: ('Silni_En-Tai_2', [6411, 6410, 6410]),
    6332: ('Silni_En-Tai_3', [6412, 6411, 6411]),
    6333: ('Silni_En-Tai_4', [6414, 6413, 6412]),
}
# Metin Drzewnych Stworzeń (8059): Owsap's 6311-6314 (the En-Tai of the forest)

# -- items: the official vnums, free in our world (14 October 2026) --------------------------------------------------
DRYAD, TIMBER, DEW, SPIRIT, EMERALD, AIDKIT = 30613, 31096, 31097, 31098, 31099, 31100
CHEST_JOTUN, CHEST_BAGJANAMU = 50266, 54701
QUEST_ITEMS = [TIMBER, DEW, SPIRIT, EMERALD, AIDKIT]
ITEMS = [DRYAD] + QUEST_ITEMS + [CHEST_JOTUN, CHEST_BAGJANAMU]

MIN_LEVEL = 95
EREBU_PARTY_MIN = 5                     # pl-wiki "Erebu": "W grupie musi znajdować się co najmniej 5 osób"
EREBU_COOLDOWN = 2 * 60 * 60            # "co 2 godziny od jego zakończenia"
EREBU_LIMIT = 30 * 60                   # Owsap's timers: 15 + 10 + 4 + 1 minutes
