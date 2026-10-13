# -*- coding: utf-8 -*-
"""MT2009_PLUS_YOHARA_MAPS3_V1: the shared tables of the third batch of Yohara places (the owner, 14 October 2026,
cache/yohara/decyzje.md "Kolejna partia (14.10)"; plan cache/yohara/plan-mapy-yohary.md):

  394 metin2_map_whitedragoncave_02   Zejscie Polnocnego Wiatru (3x3)   open map, the maze of the official portals
  395 metin2_map_whitedragoncave_boss Glebie Polnocnego Wiatru (2x2)    dungeon (Alastor, slaby / silny)
  390 metin2_map_snake_temple_01      1. poziom Swiatyni Wezy (3x3)     open map
  391 metin2_map_snake_temple_02      Swiatynia Wezy (3x3)              dungeon (7 levels)
  396 metin2_map_anglar_dungeon_01    Tajemnicza Instancja (6x6)        open map (Tajemniczy Bilet)
  378-381 metin2_map_elemental_01..04 Krolestwo Zywiolow (5x5 x3, 1x2)  open maps (from the port, level 90)

The map indexes are Owsap v6.2.6's (= the official ones, plan's table). Krolestwo Zywiolow is FOUR maps in every
source we have (GF 26.1.11 client, Owsap): elemental_01 (Turnioblysk, Szczytoblysk, Lodogory), _02 (Ognioturnia,
Ognioszczyt, Wyspowiatr), _03 (Turniomrok, Szczytomrok, Ziemiopust) - the wiki's nine "maps" are their parts, the
portals between them - and _04 Plaskowyz Sil Natury. metin2_map_elemental_04_rework is Ameria's own copy of _04
(the same terrain files, another base, a snow textureset): not official, not used.

Sources of the numbers: Owsap db/mob_proto.txt (the official vnums, levels, HP...), the Polish names of Owsap's
Polish client (pack/locale/locale/pl/mob_proto = the official translation), GF 26.1.11 shared/common/map
(map_mob_list.txt - where each monster lives, metin2_map_*_point.txt - every NPC and portal), the pl-wiki pages.
"""

# -- elements (setRaceFlag bits 11-16, MT2009_PLUS_ELEMENTS_V1) -----------------------------------------------------
ELEC, FIRE, ICE, WIND, EARTH, DARK = 2048, 4096, 8192, 16384, 32768, 65536
ELEMENT_BITS = ELEC | FIRE | ICE | WIND | EARTH | DARK
ELEMENT_NAME = {ELEC: 'blyskawica', FIRE: 'ogien', ICE: 'lod', WIND: 'wiatr', EARTH: 'ziemia', DARK: 'mrok'}

# -- the monsters, bosses, Metins: vnum -> (Polish name (Owsap PL client = official), element bits (the pl-wiki
#    "Zywiol"; Owsap's Att* columns agree unless said; Metins none - the wiki gives a Metin none, as
#    tools/yohara_maps), place) -----------------------------------------------------
MOBS = {
    # Zejscie / Glebie Polnocnego Wiatru: "(lod, blyskawice)" - Owsap Elec 50 + Ice 25
    6792: ('Żołnierz Schron. Płn. W.', ICE | ELEC, 'zejscie'),
    6793: ('Zadziora Schron. Płn. W.', ICE | ELEC, 'zejscie'),
    6794: ('Wojownik Schron. Płn. W.', ICE | ELEC, 'zejscie'),
    6795: ('Czarownik Sch. Płn. W.', ICE | ELEC, 'zejscie'),
    6796: ('Generał Schron. Płn. W.', ICE | ELEC, 'zejscie'),
    6797: ('Wódz Wojenny Schronienia', ICE | ELEC, 'zejscie'),
    6790: ('Alastor', ICE, 'glebie'),           # Alastor (slaby): wiki Element Lodu, champion exp 256
    6791: ('Alastor', ELEC, 'glebie'),          # Alastor (silny): wiki Element Blyskawicy (Owsap Ice 60), exp 548
    3971: ('Kryształ Płn. Wiatru', 0, 'glebie'),   # the crystal before the egg chamber (TR wiki)
    8635: ('Białe Jajo Smoka (słaby)', 0, 'glebie'),
    8636: ('Białe Jajo Smoka (silny)', 0, 'glebie'),
    # 1. poziom Swiatyni Wezy (the Kappas; Owsap Wind 45/65)
    6744: ('Kappa Żołnierz', WIND, 'swiatynia1'),     # wiki "Kappa Zolnierz (lvl-124)"
    6745: ('Kappa Robotnik', WIND, 'swiatynia1'),
    6746: ('Kappa Żołnierz', WIND, 'swiatynia1'),     # wiki "Kappa Zolnierz (lvl-123)"
    6747: ('Kappa Czarodziej', WIND, 'swiatynia1'),
    6748: ('Kappa Łowca', WIND, 'swiatynia1'),
    6749: ('Potężny Kappa', WIND, 'swiatynia1'),
    8076: ('Metin Wężowy Przestrzeni', 0, 'swiatynia1'),
    # Swiatynia Wezy (dungeon)
    6750: ('Skorpion Wężowy', EARTH, 'swiatynia'),
    6751: ('Robotnik Wężowy', ICE, 'swiatynia'),
    6752: ('Kappa Wężowy', WIND, 'swiatynia'),
    6753: ('Żołnierz Wężowy', WIND, 'swiatynia'),
    6754: ('Wężowa Ascetka', EARTH, 'swiatynia'),
    6755: ('Potężny Wojownik Wężowy', ICE, 'swiatynia'),     # the reincarnation (lod)
    6756: ('Królowa Węży Nethis', EARTH, 'swiatynia'),
    6765: ('Potężny Wojownik Wężowy', EARTH, 'swiatynia'),   # level 4 (ziemia)
    6850: ('Skorpion Wężowy', DARK, 'swiatynia'),
    6851: ('Robotnik Wężowy', FIRE, 'swiatynia'),
    6852: ('Kappa Wężowy', ICE, 'swiatynia'),
    6853: ('Żołnierz Wężowy', ICE, 'swiatynia'),
    6854: ('Rzeźnik Wężowy', WIND, 'swiatynia'),
    8630: ('Metin Wężowy Ognia', 0, 'swiatynia'),
    8631: ('Metin Wężowy Lodu', 0, 'swiatynia'),
    8632: ('Metin Wężowy Wiatru', 0, 'swiatynia'),
    8633: ('Metin Wężowy Ziemi', 0, 'swiatynia'),
    8634: ('Metin Wężowy Czasu', 0, 'swiatynia'),
    # Tajemnicza Instancja (Owsap Dark 40-65 / Ice 40-65)
    6860: ('Mistrz Miecza Jin', DARK, 'instancja'),
    6861: ('Mistrz Włóczni Ki', DARK, 'instancja'),
    6862: ('Mistrz Włóczni Mao', DARK, 'instancja'),
    6863: ('Łucznik Gong', DARK, 'instancja'),
    6864: ('Mistrz Miecza Kao', DARK, 'instancja'),
    6865: ('Mistrz Miecza Jin', ICE, 'instancja'),
    6866: ('Mistrz Włóczni Ki', ICE, 'instancja'),
    6867: ('Mistrz Włóczni Mao', ICE, 'instancja'),
    6868: ('Łucznik Gong', ICE, 'instancja'),
    6869: ('Mistrz Miecza Kao', ICE, 'instancja'),
    6870: ('Tajemniczy Mnich', ICE, 'instancja'),
    6871: ('Tajemniczy Mnich', DARK, 'instancja'),
    # Krolestwo Zywiolow
    3980: ('Żywiołak Ognia', FIRE, 'zywioly'),
    3981: ('Żywiołak Lodu', ICE, 'zywioly'),
    3982: ('Żywiołak Błyskawicy', ELEC, 'zywioly'),
    3983: ('Żywiołak Wiatru', WIND, 'zywioly'),
    3984: ('Żywiołak Ziemi', EARTH, 'zywioly'),
    3985: ('Żywiołak Mroku', DARK, 'zywioly'),
    3986: ('Duch Żaru', FIRE, 'zywioly'),
    3987: ('Duch Mrozu', ICE, 'zywioly'),
    3988: ('Duch Elektro', ELEC, 'zywioly'),
    3989: ('Duch Powietrza', WIND, 'zywioly'),
    3990: ('Duch Kamienia', EARTH, 'zywioly'),     # wiki: Wiatr (an obvious copy slip - every other spirit is its
                                                   # area's element); Owsap Earth 55 kept
    3991: ('Duch Półmroku', DARK, 'zywioly'),
    3992: ('Władca Płomieni', FIRE, 'zywioly'),
    3993: ('Władca Lodowca', ICE, 'zywioly'),
    3994: ('Władca Grzmotu', ELEC, 'zywioly'),
    3995: ('Władca Wichury', WIND, 'zywioly'),
    3996: ('Władca Ziemi', EARTH, 'zywioly'),
    3997: ('Władca Nocy', DARK, 'zywioly'),
    4000: ('Metin Ognia', 0, 'zywioly'),
    4001: ('Metin Lodu', 0, 'zywioly'),
    4002: ('Metin Błyskawicy', 0, 'zywioly'),
    4003: ('Metin Wiatru', 0, 'zywioly'),
    4004: ('Metin Ziemi', 0, 'zywioly'),
    4005: ('Metin Nocy', 0, 'zywioly'),
    4006: ('Stróż Żywiołów', 0, 'zywioly'),
}

# -- NPCs (our NPC numbers, Owsap's folder; Owsap's NPC rows lack a column - gen_ymaps_sql.npc_row) ---------------
NPCS = {
    20815: 'Upiorny Strażnik',          # Zejscie 383,614 - Glebie (slaby / silny)
    20813: 'Pustelnik Płn. Wiatru',     # Zejscie 67,71
    20848: 'Stare Kości',               # Zejscie 413,200
    4030: 'Białe Jajo Smoka',           # Glebie: the leader touches it - Alastor wakes (TR wiki)
    20807: 'Statua Węży',               # 1. poziom Swiatyni Wezy 404,364 - the temple
    20829: 'Kowal Świątyni Węży',       # the temple, level 6
    20842: 'Uwięziony Kowal',           # the temple, level 6
    4022: 'Portal Świątyni Węży',       # the temple, level 1: "Rozpocznij walke"
    4024: 'Głowa Węża',                 # the temple, level 7: ice / fire / wind / earth (quest by vnum)
    4025: 'Głowa Węża',
    4026: 'Głowa Węża',
    4027: 'Głowa Węża',
    6757: 'Kolumna Węży',               # the temple, level 5
    3998: 'Królestwo Żywiołów',         # Port Nowego Kontynentu 229,585 (Owsap's place) - the elemental realm
    3999: 'Wyjście',                    # elemental_01 144,417 / elemental_04 126,321 - back to the port
    10138: 'Wyjście',                   # 1. poziom Swiatyni Wezy 671,665 - back to Przelecz Yilad (quest)
    10204: 'Wyjście',                   # Tajemnicza Instancja 39,119 - back to Namgan (quest)
}
# Owsap's folder of an NPC whose row we write (npclist race of the client is by vnum; the folder is the server's)
NPC_FOLDER = {}
# Straznik Wezy (20804, Przelecz Yilad 637,494) and Tajemniczy Oltarz (20850, Namgan 960,242) are rows of the second
# batch (yohara_maps2.sql, MT2009_PLUS_YOHARA_MAPS2_V1); their dialogs here (quest yohara_mapy3)

# -- portals: vnum -> (type, name (the official one: "<place> x y"), Polish name). WARP (3) = global coordinates /100,
#    GOTO (9) = this map's own coordinates (char.cpp FuncCheckWarp). Owsap's Polish client's names. ---------------------
WARP, GOTO = 3, 9
PORTALS = {
    # Schronienie (393, maps2) <-> Zejscie (394): GF metin2_map_whitedragoncave_01_point.txt 10202 at 1358,1467
    10202: (WARP, 'ZejsciePlnW 11590 12181', 'ZejściePłnW. 11590 12181'),
    10203: (WARP, 'SchronPlnW 11323 13499', 'SchronPłnW. 11323 13499'),
    # Zejscie's maze (the official GOTO portals; "70 149" = back to the start)
    10205: (GOTO, '. 70 149', '. 70 149'), 10206: (GOTO, '. 295 157', '. 295 157'),
    10207: (GOTO, '. 190 84', '. 190 84'), 10208: (GOTO, '. 70 149', '. 70 149'),
    10209: (GOTO, '. 650 184', '. 650 184'), 10210: (GOTO, '. 476 53', '. 476 53'),
    10211: (GOTO, '. 70 149', '. 70 149'), 10212: (GOTO, '. 80 330', '. 80 330'),
    10213: (GOTO, '. 351 385', '. 351 385'), 10214: (GOTO, '. 81 451', '. 81 451'),
    10215: (GOTO, '. 70 149', '. 70 149'), 10216: (GOTO, '. 707 445', '. 707 445'),
    10217: (GOTO, '. 351 445', '. 351 445'), 10218: (GOTO, '. 70 149', '. 70 149'),
    10219: (GOTO, '. 215 557', '. 215 557'), 10220: (GOTO, '. 698 325', '. 698 325'),
    10221: (GOTO, '. 70 149', '. 70 149'), 10224: (GOTO, '. 646 65', '. 646 65'),
    10225: (GOTO, '. 70 149', '. 70 149'),
    10222: (WARP, 'TajnaKomnata 11913 12692', 'TajnaKomnata 11913 12692'),
    10223: (WARP, 'Wroc 11553 12697', 'Wróć 11553 12697'),
    # Glebie: the two halls (GOTO in the instance)
    3972: (GOTO, 'GlebiePlnW 415 136', 'GłębiePłnW. 415 136'),
    3973: (GOTO, 'GlebiePlnW 94 139', 'GłębiePłnW. 94 139'),
    # Krolestwo Zywiolow (Owsap's 10109-10124; our 10109 is Przelecz, so Turnioblysk is 10125 here)
    10125: (WARP, 'Turnioblysk 451 9492', 'Turniobłysk 451 9492'),
    10110: (WARP, 'Szczytoblysk 830 9454', 'Szczytobłysk 830 9454'),
    10111: (WARP, 'Ognioturnia 1430 9616', 'Ognioturnia 1430 9616'),
    10112: (WARP, 'Lodogory 690 10169', 'Lodogóry 690 10169'),
    10113: (WARP, 'Szczytoblysk 1023 9623', 'Szczytobłysk 1023 9623'),
    10114: (WARP, 'Lodogory 303 10113', 'Lodogóry 303 10113'),
    10115: (WARP, 'Ognioszczyt 2117 9447', 'Ognioszczyt 2117 9447'),
    10116: (WARP, 'Ognioturnia 1720 9499', 'Ognioturnia 1720 9499'),
    10117: (WARP, 'Wyspowiatr 1973 10159', 'Wyspowiatr 1973 10159'),
    10118: (WARP, 'Ognioszczyt 2337 9633', 'Ognioszczyt 2337 9633'),
    10119: (WARP, 'Turniomrok 2710 9616', 'Turniomrok 2710 9616'),
    10120: (WARP, 'Wyspowiatr 1582 10111', 'Wyspowiatr 1582 10111'),
    10121: (WARP, 'Szczytomrok 3393 9454', 'Szczytomrok 3393 9454'),
    10122: (WARP, 'Turniomrok 3012 9500', 'Turniomrok 3012 9500'),
    10123: (WARP, 'Ziemiopust 3069 10174', 'Ziemiopust 3069 10174'),
    10124: (WARP, 'Szczytomrok 3685 9551', 'Szczytomrok 3685 9551'),
}
PORTAL_RENUMBER = {10109: 10125}     # Owsap's npc.txt vnum -> ours

# The races the client draws for the vnums that are new to its npclist (client 2.0.61 has every GF row but these)
NPCLIST_ADD = {10125: 'warp'}

# -- the maps -----------------------------------------------------------------------------------------------------
MAPS = [
    dict(index=394, folder='metin2_map_whitedragoncave_02', name='Zejście Północnego Wiatru', size=(3, 3),
         base=(1152000, 1203200), kind='map', pack='zejscie_map', goto='zejscie'),
    dict(index=395, folder='metin2_map_whitedragoncave_boss', name='Głębie Północnego Wiatru', size=(2, 2),
         base=(1228800, 1203200), kind='dungeon', pack='glebie_map', goto=None),
    dict(index=390, folder='metin2_map_snake_temple_01', name='1. poziom Świątyni Węży', size=(3, 3),
         base=(0, 1638400), kind='map', pack='swiatynia1_map', goto='swiatynia'),
    dict(index=391, folder='metin2_map_snake_temple_02', name='Świątynia Węży', size=(3, 3),
         base=(76800, 1638400), kind='dungeon', pack='swiatynia_map', goto=None),
    dict(index=396, folder='metin2_map_anglar_dungeon_01', name='Tajemnicza Instancja', size=(6, 6),
         base=(153600, 1049600), kind='map', pack='instancja_map', goto='instancja'),
    dict(index=378, folder='metin2_map_elemental_01', name='Królestwo Żywiołów', size=(5, 5),
         base=(0, 921600), kind='map', pack='zywioly1_map', goto='zywioly'),
    dict(index=379, folder='metin2_map_elemental_02', name='Królestwo Żywiołów', size=(5, 5),
         base=(128000, 921600), kind='map', pack='zywioly2_map', goto=None),
    dict(index=380, folder='metin2_map_elemental_03', name='Królestwo Żywiołów', size=(5, 5),
         base=(256000, 921600), kind='map', pack='zywioly3_map', goto=None),
    dict(index=381, folder='metin2_map_elemental_04', name='Płaskowyż Sił Natury', size=(1, 2),
         base=(384000, 921600), kind='map', pack='zywioly4_map', goto=None),
]
