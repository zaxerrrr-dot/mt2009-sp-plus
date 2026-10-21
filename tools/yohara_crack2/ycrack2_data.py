# -*- coding: utf-8 -*-
"""MT2009_PLUS_YOHARA_CRACK2_V1: the three remaining Time Rift dungeons (Szczeliny Czasu) - the owner, 21 October 2026
(cache/yohara/decyzje.md, "Właściciel 21.10 - robimy": "Szczeliny Czasu - 3 brakujące lochy"; "Jeśli czegoś nie wiesz -
wszystko zgodnie z wiki"). The first one, Zaklęty Las (SZC) (404), is tools/yohara_crack (MT2009_PLUS_YOHARA_CRACK_V1).

  405 metin2_map_boss_crack_skipia  Grota Wygnańców 2 (SZC) + Świątynia Smoka (SZC) (6x6)  quest beran_szc
  406 metin2_map_boss_crack_flame   Twierdza Czerwonego Smoka (SZC) (3x3)                  quest razador_szc
  407 metin2_map_boss_crack_snow    Strażnica Nemere (SZC) (4x3)                           quest nemere_szc

Each is the second version of its awakened (PB) dungeon - the same terrain, rooms, stages and positions (Owsap v6.2.6:
crack_*_dungeon.quest = awaken_*_dungeon.quest with the "TR:" vnums and the base 153600 lower), the "TR:" monsters
(more experience, no drop - the pl-wiki), Zegarek Kieszonkowy as the ticket, Statua Szczeliny Czasu (Płaskowyż Iluzji)
as the entrance. Indexes: the official 364-366 are ours already (Wukong, Scorpion, Easter dungeons) - 405-407, free in
every map of ours, of every worktree and of Owsap's list (21 October 2026). Bases: the official ones (GF 26.1.11
setting.txt = Owsap's Setting.txt = atlasinfo), right below the PB maps.

Sources: the pl-wiki ("Statua Szczeliny Czasu", "Grota Wygnańców 2 (SZC)", "Świątynia Smoka (SZC)", "Twierdza
Czerwonego Smoka (SZC)", "Strażnica Nemere (SZC)", "Beran-Setaou (SZC)", "Razador (SZC)", "Nemere (SZC)", "Generał
Yonghan (SZC)", "Kapitan Yonghan (SZC-110)", "Kręty Klucz (SZC)", "Duch Sura (SZC)"; cache/yohara/wiki/crack), the
tr-wiki where the pl-wiki is silent ("ZÇ: Beran-Setaou": 20 000 000 Yang; "ZÇ: General Yonghan (110)": the key;
"Zaman Çatlağı Nemere Gözlemevi": the floors), the owner's sheet of 20 October 2026 (Metin2_Moby_statystyki_EXP_i_drop:
level, HP, EXP, damage, defence of every SZC monster - equal to Owsap's rows, checked), Owsap v6.2.6 (db/mob_proto.txt,
item_proto.txt, group.txt / group_group.txt "crack_*", data/dungeon/crack_*_dungeon, quest/source/dungeon/boss_crack).
"""

ELEC, FIRE, ICE, WIND, EARTH, DARK = 2048, 4096, 8192, 16384, 32768, 65536
ELEMENT_BITS = ELEC | FIRE | ICE | WIND | EARTH | DARK
ELEMENT_NAME = {ELEC: 'blyskawica', FIRE: 'ogien', ICE: 'lod', WIND: 'wiatr', EARTH: 'ziemia', DARK: 'mrok'}
OWSAP_ATT = {ELEC: 'AttElec', FIRE: 'AttFire', ICE: 'AttIce'}

# -- monsters, bosses, Metins: vnum -> (Polish name (the owner's sheet = the official "SZC: ..."), element (the
#    pl-wiki "Żywioł": the grotto lightning, the fortress fire, the watchtower ice; Owsap's Att* 90 agree; the Metins and
#    the pillar none), place) - the PB vnum is this one + 80 (monsters), + 10 (bosses, Metins), + 20 (NPCs, pillar) ------
MOBS = {
    # Grota Wygnańców 2 (SZC) / Świątynia Smoka (SZC) - błyskawica
    4200: ('SZC: Wojownik Setaou', ELEC, 'skipia'),        # 108 - Beran-Setaou / the Captains summon them
    4201: ('SZC: Łowca Setaou', ELEC, 'skipia'),           # 110
    4202: ('SZC: Mistyk Setaou', ELEC, 'skipia'),          # 110
    4203: ('SZC: Żołnierz Setaou', ELEC, 'skipia'),        # 114
    4204: ('SZC: Łucznik Setaou', ELEC, 'skipia'),         # 116
    4205: ('SZC: Magistrat Setaou', ELEC, 'skipia'),       # 118
    4206: ('SZC: Komendant Setaou', ELEC, 'skipia'),       # 120 - Generał Yonghan (SZC) summons them
    4207: ('SZC: Kapitan Yonghan', ELEC, 'skipia'),        # 116 (SZC-116) - a General (4209) appears where he falls
    4208: ('SZC: Kapitan Yonghan', ELEC, 'skipia'),        # 110 (SZC-110) - a General (4210) appears where he falls
    4209: ('SZC: Generał Yonghan', ELEC, 'skipia'),        # 115 (800 000 HP) - no key
    4210: ('SZC: Generał Yonghan', ELEC, 'skipia'),        # 115 (500 000 HP) - Kręty Klucz (SZC)
    4400: ('SZC: Beran-Setaou', ELEC, 'skipia'),           # 122, the boss
    8120: ('SZC: Metin Góry', 0, 'skipia'),                # the temple's four stones: Beran (SZC) takes no blow
    8121: ('SZC: Metin Zemsty', 0, 'skipia'),              #   while one of them stands
    8122: ('SZC: Metin Samotności', 0, 'skipia'),
    8123: ('SZC: Metin Pychy', 0, 'skipia'),
    # Twierdza Czerwonego Smoka (SZC) - ogień
    4220: ('SZC: Ognisty Duch Żaru', FIRE, 'flame'),       # 110
    4221: ('SZC: Ognisty Tygrys Żaru', FIRE, 'flame'),     # 112
    4222: ('SZC: Płomień Żaru', FIRE, 'flame'),            # 113
    4223: ('SZC: Og. Wojownik Żaru', FIRE, 'flame'),       # 113
    4224: ('SZC: Ognisty Król Żaru', FIRE, 'flame'),       # 116
    4225: ('SZC: Ognisty Troll Żaru', FIRE, 'flame'),      # 116
    4226: ('SZC: Ognista Broda Żaru', FIRE, 'flame'),      # 118
    4227: ('SZC: Og. Generał Żaru', FIRE, 'flame'),        # 118 - Razador (SZC) summons them (max. 3)
    4228: ('SZC: Ognisty Książę Żaru', FIRE, 'flame'),     # 120
    4229: ('SZC: Ignator', FIRE, 'flame'),                 # 120, the 4th zone's target
    4401: ('SZC: Razador', FIRE, 'flame'),                 # 130, the boss
    8124: ('SZC: Metin Purgatorium', 0, 'flame'),          # the 6th zone's target
    # Strażnica Nemere (SZC) - lód
    4240: ('SZC: Kryształ Mrozu', ICE, 'snow'),            # 110
    4241: ('SZC: Mroźny Robak', ICE, 'snow'),              # 110
    4242: ('SZC: Mroźny Człowiek', ICE, 'snow'),           # 113
    4243: ('SZC: Mroźny Yeti', ICE, 'snow'),               # 113
    4244: ('SZC: Mroźny Golem', ICE, 'snow'),              # 116
    4245: ('SZC: Mroźny Troll', ICE, 'snow'),              # 116
    4246: ('SZC: Mroźna Broda', ICE, 'snow'),              # 118
    4247: ('SZC: Mroźny Generał', ICE, 'snow'),            # 118 - Nemere (SZC) summons them
    4248: ('SZC: Mroźny Książę', ICE, 'snow'),             # 120
    4249: ('SZC: Szel', ICE, 'snow'),                      # 120, the 4th / 7th floor's boss
    4402: ('SZC: Nemere', ICE, 'snow'),                    # 130, the boss
    8125: ('SZC: Metin Chłodu', 0, 'snow'),                # the 6th floor - only a Shaman damages it
    20518: ('SZC: Kolumna Smoka Płn.', 0, 'snow'),         # the 9th floor - only a Shaman or a Ninja damages it
}
# the stones whose damage only some classes may deal (the pl-/tr-wiki; server-patches/szczelina, as przebudzeni's PB ones)
JOB_ONLY = {8125: 'SHAMAN', 20518: 'SHAMAN,ASSASSIN'}
# the pl-/tr-wiki over Owsap's row: Beran-Setaou (SZC) "Öldüğünde 20.000.000 Yang düşer" (tr-wiki "ZÇ: Beran-Setaou");
# Razador / Nemere (SZC): no word of yang on any wiki - none (the engine drops nothing else on 405-407)
OVERRIDE = {
    4400: dict(MinGold='20000000', MaxGold='20000000'),
}

# -- NPCs (our NPC numbers - gen_ymaps_sql.npc_row; Owsap's folder) ---------------------------------------------------
NPCS = {
    20510: ('TR: Ghost of a Sura', 'SZC: Duch Sura'),
    20511: ('TR: Am-heh Gorge', 'SZC: Gardziel Am-heha'),
    20512: ('TR: Taramor Gravestone', 'SZC: Nagrobek Taramora'),
    20513: ('TR: Isfet Stele', 'SZC: Stela Isfet'),
    20514: ('TR: Destiny Lock', 'SZC: Zamek Losu'),
    20515: ('TR: Dragon Gate', 'SZC: Smocza Brama'),           # Owsap: a DOOR - our gates are NPCs (as the PB one)
    20516: ('TR: Ice Lion', 'SZC: Lodowy Lew'),
    20517: ('TR: Arctic Cube', 'SZC: Arktyczna Kostka'),
}

# -- the PB vnums of the PB quests and spawn files -> the SZC ones (Owsap's crack quests = its awaken ones with these) -
PB_TO_SZC = {}
for _pb in list(range(4280, 4291)) + list(range(4300, 4310)) + list(range(4320, 4330)):
    PB_TO_SZC[_pb] = _pb - 80                          # monsters (Beran's troop groups 4288-4290 -> 4208-4210 too)
PB_TO_SZC.update({4410: 4400, 4411: 4401, 4412: 4402})  # the bosses
PB_TO_SZC.update(dict((_pb, _pb - 10) for _pb in range(8130, 8136)))     # the Metins
PB_TO_SZC.update(dict((_pb, _pb - 20) for _pb in range(20530, 20539)))   # the NPCs and the pillar
PB_TO_SZC.update({4292: 4212})                          # Beran-Setaou's group (Owsap: crack_skipia_boss)
PB_TO_SZC.update({31180: 31160, 31187: 31167, 31188: 31168, 31189: 31169, 31190: 31170, 31191: 31171})  # items
PB_TO_SZC.update({31146: 31147})                        # the ticket: Książka Przebudzenia -> Zegarek Kieszonkowy

# -- the items: the quests' ones (Owsap's vnums; the PB twin's row with "(SZC)") -------------------------------------
ITEMS = {31160: 31180, 31167: 31187, 31168: 31188, 31169: 31189, 31170: 31190, 31171: 31191}   # SZC -> PB twin
ITEM_TEXT = {
    31160: 'Ten magiczny klucz aktywuje portal do Świątyni Smoka (SZC). Zostawia go Generał Yonghan (SZC), który '
           'pojawia się po Kapitanie Yonghanie (SZC-110). Duch Sura (SZC) chce trzech od każdego.',
}

# -- the maps -----------------------------------------------------------------------------------------------------
# pb_dir: the PB twin's generated folder (its server_attr = the same terrain, GF's; its Setting.txt = this one but the
# BasePosition); gf_parent: the terrain's GF folder (the walk grid); own_attr: GF's own sector of the crack folder
MAPS = [
    dict(index=405, folder='metin2_map_boss_crack_skipia', name='Grota Wygnańców 2 (SZC)', size=(6, 6),
         base=(0, 1817600), town=(877, 722), pb_index=398, pb_folder='metin2_map_boss_awaken_skipia',
         pb_dir='yohara_iluzja', gf_parent='metin2_map_skipia_dungeon_02', own_attr='metin2_map_boss_crack_skipia',
         owsap='crack_skipia_dungeon', sub='beran_szc', quest='beran_szc', pb_quest='beran_pb', boss=4400,
         element=ELEC, attr_head='1800000018000000'),
    dict(index=406, folder='metin2_map_boss_crack_flame', name='Twierdza Czerwonego Smoka (SZC)', size=(3, 3),
         base=(153600, 1817600), town=(342, 584), pb_index=369, pb_folder='metin2_map_boss_awaken_flame',
         pb_dir='yohara_pb', gf_parent='metin2_map_n_flame_dungeon_01', own_attr=None,
         owsap='crack_flame_dungeon', sub='razador_szc', quest='razador_szc', pb_quest='razador_pb', boss=4401,
         element=FIRE, attr_head='0c0000000c000000'),
    dict(index=407, folder='metin2_map_boss_crack_snow', name='Strażnica Nemere (SZC)', size=(4, 3),
         base=(230400, 1817600), town=(171, 270), pb_index=370, pb_folder='metin2_map_boss_awaken_snow',
         pb_dir='yohara_pb', gf_parent='metin2_map_n_snow_dungeon_01', own_attr=None,
         owsap='crack_snow_dungeon', sub='nemere_szc', quest='nemere_szc', pb_quest='nemere_pb', boss=4402,
         element=ICE, attr_head='100000000c000000'),
]
BASE_SHIFT = 1971200 - 1817600          # the PB maps' base y minus the SZC ones' (Owsap: 19712 -> 18176 in its quests)
TICKET = 31147                          # Zegarek Kieszonkowy (tools/yohara_crack)
MIN_LEVEL = 110
TIME_LIMIT = 60 * 60
