# -*- coding: utf-8 -*-
"""MT2009_PLUS_BONUS67_SKILL_V1: the 6th/7th bonuses of the wiki round 3 (the owner, 4 November 2026: "add ALL the
missing 6/7 bonuses exactly as on the wiki, without the Lycan") - the first two-byte points (256 up, after
server-patches/wideattr). One table for every generator:

  server-patches/bonusy67c/gen_edits.py      common/length.h (the points, in this order) and char.cpp (point change)
  tools/bonusy67/gen_bonusy67c_sql.py        apply.sh's ENUM names (this order) and bonusy67c_wiki.sql (the pool rows)
  tools/bonusy67/gen_bonusy67c_misc.py       the overlay's table (playerbot_bonus67c_table.h), the client's tooltip
                                             lines (root/localeinfo_point.py) and the panel's names (dbeditor/items.py)

A point: (number, POINT_* name, kind, skill vnum or 0, the pl-wiki's words (%d = the value), the panel's name (the wiki's
words, x = the value - MT2009_PLUS_BONUS67_WIKI_NAMES_V1; 257-259 are not on the pl-wiki and keep a short one),
unit, (lv1..lv5), {pool column: highest level}, weight).

Kinds (what playerbot_bonus67.cpp does with the value):
  RANK     "Niski ranking ..." - x the rank's per cent (Agresywny 1, Nieuczciwy 2, Zlosliwy 3, Okrutny 5)
  PER      +x% of the total of a race bonus (as ATTBONUS_PER_* 210-217)
  ABSORB   x% of the damage the skill dealt back as HP
  CD10     with 10% chance the skill's next cooldown x seconds shorter
  CD20     the same with 20%
  DUR      the skill's affect x seconds longer
  ATT      using the skill: Wartosc Ataku + b67_skill_att (50) for x seconds
  DEF      using the skill: Obrona + b67_skill_def (50) for x seconds
  CAST     using the skill: Szybkosc zaklecia + b67_skill_cast (20%) for x seconds
  STUN     x% chance the skill stuns what it hit
  KNOCK    x% chance the skill knocks back what it hit
  SKDMG    the skill's damage +x% (the body armour's line)

The skill numbers are ours (world.skill_proto); the official APPLY_* names (Owsap's item_attr_rare ENUM) name the
skills in Korean: 1 SAMYEON (Trzystronne Ciecie), 2 PALBANG (Wir Miecza), 4 GEOMKYUNG (Aura Miecza), 6 GIHYEOL (Wola
Zycia), 16 GIGONGCHAM (Duchowe Uderzenie), 17 GYOKSAN (Walniecie), 19 CHUNKEON (Silne Cialo), 20 GEOMPUNG (Uderzenie
Miecza), 21 NOEGEOM (Krag Mieczy), 31 AMSEOP (Zasadzka), 32 GUNGSIN (Szybki Atak), 33 CHARYUN (Wirujacy Sztylet), 34
EUNHYUNG (Krycie Sie), 35 SANGONG (Trujaca Chmura), 36 SEOMJEON (Wolno Dzialajaca Trucizna), 46 YEONSA (Powtarzalny
Strzal), 47 KWANKYEOK (Deszcz Strzal - our client names 47 "Iskrzace Uderzenie"), 49 GYEONGGONG (Bezszelestny Chod),
50 GIGUNG (Trujaca Strzala), 61 SWAERYUNG (Uderzenie Palcem), 62 YONGKWON (Smoczy Wir), 63 GWIGEOM (Czarowane Ostrze),
64 TERROR (Strach), 66 PABEOB (Rozproszenie Magii), 76 MARYUNG (Mroczne Uderzenie), 77 HWAYEOMPOK (Ogniste Uderzenie),
78 MUYEONG (Ognisty Duch), 79 MANASHIELD (Mroczna Ochrona), 80 TUSOK (Duchowy Cios), 81 MAHWAN (Mroczna Sfera), 91
BIPABU (Latajacy Talizman), 92 YONGBI (Strzelajacy Smok), 93 PAERYONG (Smoczy Skowyt), 94 HOSIN (Blogoslawienstwo),
96 GICHEON (Pomoc Smoka), 106 NOEJEON (Rzut Piorunem = the wiki's "blyskawiczny rzut"), 107 BYEURAK (Przywolanie
Blyskawicy), 108 CHAIN (Burzowy Szpon), 109 JEONGEOP (Leczenie), 111 JEUNGRYEOK (Zwiekszenie Ataku).

6, 21 and 36 (Wola Zycia, Krag Mieczy, Wolno Dzialajaca Trucizna - the warrior's and the dagger ninja's 6th skills of
the official game) are NOT in world.skill_proto nor in the client's skill window (playersettingmodule.py) - only their
books' names are in itemdesc. Their lines work by skill number the day the skills exist; until then their pool rows
roll nowhere (every column 0, as Burza Szponow's glove line). SKILL_ROWS_ON = False below keeps it so.
The Lycan's lines (Szpon Wilka, Rozdarcie, Wilczy Skok, Wilczy Tchu, Dusza Purpurowego/Indygo Wilka) are left out.
"""

WEAPON = {'weapon': 5}
BODY = {'body': 5}
NONE = {}

# the pool rows of skills this server does not have (6, 21, 36): False - every column 0
MISSING_SKILLS = (6, 21, 36)

POINTS = [
    # --- weapon (and helmet): not tied to a skill
    (256, 'POINT_ALIGNMENT_DAMAGE_BONUS', 'RANK', 0,
     u'Niski ranking powoduje zwiększenie zadawanych obrażeń', u'Niski ranking powoduje zwiększenie zadawanych obrażeń', u'',
     (1, 1, 1, 1, 1), {'weapon': 1, 'head': 1}, 18),
    (257, 'POINT_ATTBONUS_PER_HUMAN', 'PER', 0,
     u'Silny przeciwko pół-ludziom (+%d%% łącznej wartości)', u'Silny przeciw pół-ludziom (+% łącznej)', u'%',
     (3, 6, 9, 12, 15), WEAPON, 18),
    (258, 'POINT_ATTBONUS_PER_UNDEAD', 'PER', 0,
     u'Silny przeciwko nieumarłym (+%d%% łącznej wartości)', u'Silny przeciw nieumarłym (+% łącznej)', u'%',
     (3, 6, 9, 12, 15), WEAPON, 18),
    (259, 'POINT_ATTBONUS_PER_DESERT', 'PER', 0,
     u'Silny przeciwko potworom pustyni (+%d%% łącznej wartości)', u'Silny przeciw potworom pustyni (+% łącznej)', u'%',
     (4, 8, 12, 16, 20), WEAPON, 18),
    # --- weapon: "Absorbuje x% PZ przy uzyciu ..." (1-5%)
    (260, 'POINT_USE_SKILL_PALBANG_HP_ABSORB', 'ABSORB', 2,
     u'Absorbuje %d%% PŻ przy użyciu wiru miecza', u'Absorbuje x% PŻ przy użyciu wiru miecza', u'%', (1, 2, 3, 4, 5), WEAPON, 18),
    (261, 'POINT_USE_SKILL_AMSEOP_HP_ABSORB', 'ABSORB', 31,
     u'Absorbuje %d%% PŻ przy użyciu zasadzki', u'Absorbuje x% PŻ przy użyciu zasadzki', u'%', (1, 2, 3, 4, 5), WEAPON, 18),
    (262, 'POINT_USE_SKILL_YEONSA_HP_ABSORB', 'ABSORB', 46,
     u'Absorbuje %d%% PŻ przy użyciu powtarzalnego strzału', u'Absorbuje x% PŻ przy użyciu powtarzalnego strzału', u'%',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (263, 'POINT_USE_SKILL_TUSOK_HP_ABSORB', 'ABSORB', 80,
     u'Absorbuje %d%% PŻ przy użyciu duchowego ciosu', u'Absorbuje x% PŻ przy użyciu duchowego ciosu', u'%', (1, 2, 3, 4, 5), WEAPON, 18),
    (264, 'POINT_USE_SKILL_YONGBI_HP_ABSORB', 'ABSORB', 92,
     u'Absorbuje %d%% PŻ przy użyciu strzelającego smoka', u'Absorbuje x% PŻ przy użyciu strzelającego smoka', u'%',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (265, 'POINT_USE_SKILL_PAERYONG_HP_ABSORB', 'ABSORB', 93,
     u'Absorbuje %d%% PŻ przy użyciu smoczego skowytu', u'Absorbuje x% PŻ przy użyciu smoczego skowytu', u'%', (1, 2, 3, 4, 5), WEAPON, 18),
    (266, 'POINT_USE_SKILL_BYEURAK_HP_ABSORB', 'ABSORB', 107,
     u'Absorbujesz do %d%% PŻ przy użyciu przywołania błyskawicy', u'Absorbujesz do x% PŻ przy użyciu przywołania błyskawicy', u'%',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (267, 'POINT_USE_SKILL_CHAIN_HP_ABSORB', 'ABSORB', 108,
     u'Absorbuje %d%% PŻ przy użyciu burzowego szponu', u'Absorbuje x% PŻ przy użyciu burzowego szponu', u'%', (1, 2, 3, 4, 5), WEAPON, 18),
    # --- weapon: "Czas regeneracji ...: -x sek. z 10% szans" (1-5 s)
    (268, 'POINT_USE_SKILL_SAMYEON_NEXT_COOLTIME_DECREASE_10PER', 'CD10', 1,
     u'Czas regeneracji trzystronnego cięcia: -%d sek. z 10%% szans', u'Czas regeneracji trzystronnego cięcia: -x sek. z 10% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (269, 'POINT_USE_SKILL_GEOMPUNG_NEXT_COOLTIME_DECREASE_10PER', 'CD10', 20,
     u'Czas regeneracji uderzenia miecza: -%d sek. z 10%% szans', u'Czas regeneracji uderzenia miecza: -x sek. z 10% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (270, 'POINT_USE_SKILL_GUNGSIN_NEXT_COOLTIME_DECREASE_10PER', 'CD10', 32,
     u'Czas regeneracji szybkiego ataku: -%d sek. z 10%% szans', u'Czas regeneracji szybkiego ataku: -x sek. z 10% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (271, 'POINT_USE_SKILL_KWANKYEOK_NEXT_COOLTIME_DECREASE_10PER', 'CD10', 47,
     u'Czas regeneracji deszczu strzał: -%d sek. z 10%% szans', u'Czas regeneracji deszczu strzał: -x sek. z 10% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (272, 'POINT_USE_SKILL_YONGKWON_NEXT_COOLTIME_DECREASE_10PER', 'CD10', 62,
     u'Czas regeneracji smoczego wiru: -%d sek. z 10%% szans', u'Czas regeneracji smoczego wiru: -x sek. z 10% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (273, 'POINT_USE_SKILL_MARYUNG_NEXT_COOLTIME_DECREASE_10PER', 'CD10', 76,
     u'Czas regeneracji mrocznego uderzenia: -%d sek. z 10%% szans', u'Czas regeneracji mrocznego uderzenia: -x sek. z 10% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (274, 'POINT_USE_SKILL_BIPABU_NEXT_COOLTIME_DECREASE_10PER', 'CD10', 91,
     u'Czas regeneracji latającego talizmanu: -%d sek. z 10%% szans', u'Czas regeneracji latającego talizmanu: -x sek. z 10% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (275, 'POINT_USE_SKILL_NOEJEON_NEXT_COOLTIME_DECREASE_10PER', 'CD10', 106,
     u'Czas regeneracji błyskawicznego rzutu: -%d sek. z 10%% szans', u'Czas regeneracji błyskawicznego rzutu: -x sek. z 10% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    # --- weapon: the same with 20%
    (276, 'POINT_USE_SKILL_SAMYEON_NEXT_COOLTIME_DECREASE_20PER', 'CD20', 1,
     u'Czas regeneracji trzystronnego cięcia: -%d sek. z 20%% szans', u'Czas regeneracji trzystronnego cięcia: -x sek. z 20% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (277, 'POINT_USE_SKILL_GEOMPUNG_NEXT_COOLTIME_DECREASE_20PER', 'CD20', 20,
     u'Czas regeneracji uderzenia miecza: -%d sek. z 20%% szans', u'Czas regeneracji uderzenia miecza: -x sek. z 20% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (278, 'POINT_USE_SKILL_GUNGSIN_NEXT_COOLTIME_DECREASE_20PER', 'CD20', 32,
     u'Czas regeneracji szybkiego ataku: -%d sek. z 20%% szans', u'Czas regeneracji szybkiego ataku: -x sek. z 20% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (279, 'POINT_USE_SKILL_KWANKYEOK_NEXT_COOLTIME_DECREASE_20PER', 'CD20', 47,
     u'Czas regeneracji deszczu strzał: -%d sek. z 20%% szans', u'Czas regeneracji deszczu strzał: -x sek. z 20% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (280, 'POINT_USE_SKILL_YONGKWON_NEXT_COOLTIME_DECREASE_20PER', 'CD20', 62,
     u'Czas regeneracji smoczego wiru: -%d sek. z 20%% szans', u'Czas regeneracji smoczego wiru: -x sek. z 20% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (281, 'POINT_USE_SKILL_MARYUNG_NEXT_COOLTIME_DECREASE_20PER', 'CD20', 76,
     u'Czas regeneracji mrocznego uderzenia: -%d sek. z 20%% szans', u'Czas regeneracji mrocznego uderzenia: -x sek. z 20% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (282, 'POINT_USE_SKILL_BIPABU_NEXT_COOLTIME_DECREASE_20PER', 'CD20', 91,
     u'Czas regeneracji latającego talizmanu: -%d sek. z 20%% szans', u'Czas regeneracji latającego talizmanu: -x sek. z 20% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (283, 'POINT_USE_SKILL_NOEJEON_NEXT_COOLTIME_DECREASE_20PER', 'CD20', 106,
     u'Czas regeneracji błyskawicznego rzutu: -%d sek. z 20%% szans', u'Czas regeneracji błyskawicznego rzutu: -x sek. z 20% szans', u's',
     (1, 2, 3, 4, 5), WEAPON, 18),
    # --- weapon: "Czas trwania ... +x sek." (1-10 s)
    (284, 'POINT_SKILL_DURATION_INCREASE_GEOMKYUNG', 'DUR', 4,
     u'Czas trwania aury miecza +%d sek.', u'Czas trwania aury miecza +x sek.', u's', (2, 4, 6, 8, 10), WEAPON, 18),
    (285, 'POINT_SKILL_DURATION_INCREASE_EUNHYUNG', 'DUR', 34,
     u'Czas trwania krycia się +%d sek.', u'Czas trwania krycia się +x sek.', u's', (2, 4, 6, 8, 10), WEAPON, 18),
    (286, 'POINT_SKILL_DURATION_INCREASE_GYEONGGONG', 'DUR', 49,
     u'Czas trwania bezszelestnego chodu +%d sek.', u'Czas trwania bezszelestnego chodu +x sek.', u's',
     (2, 4, 6, 8, 10), WEAPON, 18),
    # --- weapon: "Na x sek. otrzymujesz bonus do ataku przy uzyciu ..." (1-10 s)
    (287, 'POINT_USE_SKILL_GIHYEOL_ATT_GRADE_BONUS', 'ATT', 6,
     u'Na %d sek. otrzymujesz bonus do ataku przy użyciu woli życia', u'Na x sek. otrzymujesz bonus do ataku przy użyciu woli życia', u's',
     (2, 4, 6, 8, 10), WEAPON, 18),
    (288, 'POINT_USE_SKILL_NOEGEOM_ATT_GRADE_BONUS', 'ATT', 21,
     u'Na %d sek. otrzymujesz bonus do ataku przy użyciu kręgu mieczy', u'Na x sek. otrzymujesz bonus do ataku przy użyciu kręgu mieczy', u's',
     (2, 4, 6, 8, 10), WEAPON, 18),
    (289, 'POINT_USE_SKILL_SANGONG_ATT_GRADE_BONUS', 'ATT', 35,
     u'Na %d sek. otrzymujesz bonus do ataku przy użyciu trującej chmury', u'Na x sek. otrzymujesz bonus do ataku przy użyciu trującej chmury', u's',
     (2, 4, 6, 8, 10), WEAPON, 18),
    (290, 'POINT_USE_SKILL_GIGUNG_ATT_GRADE_BONUS', 'ATT', 50,
     u'Na %d sek. otrzymujesz bonus do ataku przy użyciu zatrutej strzały', u'Na x sek. otrzymujesz bonus do ataku przy użyciu zatrutej strzały', u's',
     (2, 4, 6, 8, 10), WEAPON, 18),
    (291, 'POINT_USE_SKILL_TERROR_ATT_GRADE_BONUS', 'ATT', 64,
     u'Na %d sek. otrzymujesz bonus do ataku przy użyciu strachu', u'Na x sek. otrzymujesz bonus do ataku przy użyciu strachu', u's',
     (2, 4, 6, 8, 10), WEAPON, 18),
    (292, 'POINT_USE_SKILL_MUYEONG_ATT_GRADE_BONUS', 'ATT', 78,
     u'Na %d sek. otrzymujesz bonus do ataku przy użyciu ognistego ducha', u'Na x sek. otrzymujesz bonus do ataku przy użyciu ognistego ducha', u's',
     (2, 4, 6, 8, 10), WEAPON, 18),
    (293, 'POINT_USE_SKILL_GICHEON_ATT_GRADE_BONUS', 'ATT', 96,
     u'Na %d sek. zwiększa bonus do ataku przy użyciu pomocy smoka', u'Na x sek. zwiększa bonus do ataku przy użyciu pomocy smoka', u's',
     (2, 4, 6, 8, 10), WEAPON, 18),
    (294, 'POINT_USE_SKILL_JEONGEOP_ATT_GRADE_BONUS', 'ATT', 109,
     u'Na %d sek. otrzymujesz bonus do ataku przy użyciu leczenia', u'Na x sek. otrzymujesz bonus do ataku przy użyciu leczenia', u's',
     (2, 4, 6, 8, 10), WEAPON, 18),
    # --- weapon: "Na x sek. otrzymujesz bonus do obrony przy uzyciu ..." (1-10 s)
    (295, 'POINT_USE_SKILL_GWIGEOM_DEF_BONUS', 'DEF', 63,
     u'Na %d sek. otrzymujesz bonus do obrony przy użyciu czarowanego ostrza', u'Na x sek. otrzymujesz bonus do obrony przy użyciu czarowanego ostrza',
     u's', (2, 4, 6, 8, 10), WEAPON, 18),
    (296, 'POINT_USE_SKILL_HOSIN_DEF_BONUS', 'DEF', 94,
     u'Na %d sek. otrzymujesz bonus do obrony przy użyciu błogosławieństwa', u'Na x sek. otrzymujesz bonus do obrony przy użyciu błogosławieństwa',
     u's', (2, 4, 6, 8, 10), WEAPON, 18),
    (297, 'POINT_USE_SKILL_JEUNGRYEOK_DEF_BONUS', 'DEF', 111,
     u'Na %d sek. otrzymujesz bonus do obrony przy użyciu ataku+', u'Na x sek. otrzymujesz bonus do obrony przy użyciu ataku+', u's',
     (2, 4, 6, 8, 10), WEAPON, 18),
    # --- weapon: "Na x sek. zwieksza szybkosc zaklecia przy uzyciu ..." (1-10 s)
    (298, 'POINT_USE_SKILL_CHUNKEON_CASTING_SPEED', 'CAST', 19,
     u'Na %d sek. zwiększa szybkość zaklęcia przy użyciu silnego ciała', u'Na x sek. zwiększa szybkość zaklęcia przy użyciu silnego ciała', u's',
     (2, 4, 6, 8, 10), WEAPON, 18),
    (299, 'POINT_USE_SKILL_MANASHIELD_CASTING_SPEED', 'CAST', 79,
     u'Na %d sek. zwiększa szybkość zaklęcia przy użyciu mrocznej ochrony', u'Na x sek. zwiększa szybkość zaklęcia przy użyciu mrocznej ochrony',
     u's', (2, 4, 6, 8, 10), WEAPON, 18),
    # --- weapon: "... ma x% szans na ogluszenie przeciwnika" (1-5%)
    (300, 'POINT_USE_SKILL_SAMYEON_STUN', 'STUN', 1,
     u'Trzystronne cięcie ma %d%% szans na ogłuszenie przeciwnika', u'Trzystronne cięcie ma x% szans na ogłuszenie przeciwnika', u'%',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (301, 'POINT_USE_SKILL_GIGONGCHAM_STUN', 'STUN', 16,
     u'Duchowe uderzenie ma %d%% szans na ogłuszenie przeciwnika', u'Duchowe uderzenie ma x% szans na ogłuszenie przeciwnika', u'%',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (302, 'POINT_USE_SKILL_CHARYUN_STUN', 'STUN', 33,
     u'Wirujący sztylet ma %d%% szans na ogłuszenie przeciwnika', u'Wirujący sztylet ma x% szans na ogłuszenie przeciwnika', u'%',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (303, 'POINT_USE_SKILL_PABEOB_STUN', 'STUN', 66,
     u'Rozproszenie magii ma %d%% szans na ogłuszenie przeciwnika', u'Rozproszenie magii ma x% szans na ogłuszenie przeciwnika', u'%',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (304, 'POINT_USE_SKILL_MAHWAN_STUN', 'STUN', 81,
     u'Mroczna sfera ma %d%% szans na ogłuszenie przeciwnika', u'Mroczna sfera ma x% szans na ogłuszenie przeciwnika', u'%',
     (1, 2, 3, 4, 5), WEAPON, 18),
    # --- weapon: "... ma x% szans na oddanie przeciwnikowi" (1-5%, the knockback)
    (305, 'POINT_USE_SKILL_GYOKSAN_KNOCKBACK', 'KNOCK', 17,
     u'Walnięcie ma %d%% szans na oddanie przeciwnikowi', u'Walnięcie ma x% szans na oddanie przeciwnikowi', u'%', (1, 2, 3, 4, 5), WEAPON, 18),
    (306, 'POINT_USE_SKILL_SEOMJEON_KNOCKBACK', 'KNOCK', 36,
     u'Wolno działająca trucizna ma %d%% szans na oddanie przeciwnikowi', u'Wolno działająca trucizna ma x% szans na oddanie przeciwnikowi', u'%',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (307, 'POINT_USE_SKILL_KWANKYEOK_KNOCKBACK', 'KNOCK', 47,
     u'Deszcz strzał ma %d%% szans na oddanie przeciwnikowi', u'Deszcz strzał ma x% szans na oddanie przeciwnikowi', u'%', (1, 2, 3, 4, 5), WEAPON, 18),
    (308, 'POINT_USE_SKILL_SWAERYUNG_KNOCKBACK', 'KNOCK', 61,
     u'Uderzenie palcem ma %d%% szans na oddanie przeciwnikowi', u'Uderzenie palcem ma x% szans na oddanie przeciwnikowi', u'%',
     (1, 2, 3, 4, 5), WEAPON, 18),
    (309, 'POINT_USE_SKILL_HWAYEOMPOK_KNOCKBACK', 'KNOCK', 77,
     u'Ogniste uderzenie ma %d%% szans na oddanie przeciwnikowi', u'Ogniste uderzenie ma x% szans na oddanie przeciwnikowi', u'%',
     (1, 2, 3, 4, 5), WEAPON, 18),
    # --- body armour: "Obrazenia od ... +x%" (1-5%)
    (310, 'POINT_SKILL_DAMAGE_SAMYEON', 'SKDMG', 1,
     u'Obrażenia od trzystronnego cięcia +%d%%', u'Obrażenia od trzystronnego cięcia +x%', u'%', (1, 2, 3, 4, 5), BODY, 18),
    (311, 'POINT_SKILL_DAMAGE_GEOMPUNG', 'SKDMG', 20,
     u'Obrażenia od uderzenia miecza +%d%%', u'Obrażenia od uderzenia miecza +x%', u'%', (1, 2, 3, 4, 5), BODY, 18),
    (312, 'POINT_SKILL_DAMAGE_GUNGSIN', 'SKDMG', 32,
     u'Obrażenia od szybkiego ataku +%d%%', u'Obrażenia od szybkiego ataku +x%', u'%', (1, 2, 3, 4, 5), BODY, 18),
    (313, 'POINT_SKILL_DAMAGE_KWANKYEOK', 'SKDMG', 47,
     u'Obrażenia od deszczu strzał +%d%%', u'Obrażenia od deszczu strzał +x%', u'%', (1, 2, 3, 4, 5), BODY, 18),
    (314, 'POINT_SKILL_DAMAGE_YONGKWON', 'SKDMG', 62,
     u'Obrażenia od smoczego wiru +%d%%', u'Obrażenia od smoczego wiru +x%', u'%', (1, 2, 3, 4, 5), BODY, 18),
    (315, 'POINT_SKILL_DAMAGE_MARYUNG', 'SKDMG', 76,
     u'Obrażenia od mrocznego uderzenia +%d%%', u'Obrażenia od mrocznego uderzenia +x%', u'%', (1, 2, 3, 4, 5), BODY, 18),
    (316, 'POINT_SKILL_DAMAGE_BIPABU', 'SKDMG', 91,
     u'Obrażenia od latającego talizmanu +%d%%', u'Obrażenia od latającego talizmanu +x%', u'%', (1, 2, 3, 4, 5), BODY, 18),
    (317, 'POINT_SKILL_DAMAGE_YONGBI', 'SKDMG', 92,
     u'Obrażenia od strzelającego smoka +%d%%', u'Obrażenia od strzelającego smoka +x%', u'%', (1, 2, 3, 4, 5), BODY, 18),
    (318, 'POINT_SKILL_DAMAGE_NOEJEON', 'SKDMG', 106,
     u'Obrażenia od błyskawicznego rzutu +%d%%', u'Obrażenia od błyskawicznego rzutu +x%', u'%', (1, 2, 3, 4, 5), BODY, 18),
]
WIDE_END = 319

# A row for a point the engine had already: "Odpornosc na Upadek +x%" (the body armour - pl-wiki max 20%, en-wiki
# 5/10/15%) is POINT_IMMUNE_FALL (90), a flag till now; the value is a chance now (playerbot_bonus67.cpp).
EXTRA_ROWS = [
    ('POINT_IMMUNE_FALL', 18, (5, 10, 15, 20, 20), {'body': 4}),
]
FALL_TEXT = u'Odporność na Upadek +%d%%'


def check():
    assert [p[0] for p in POINTS] == list(range(256, WIDE_END)), 'the numbers follow from 256 in order'
    names = [p[1] for p in POINTS]
    assert len(set(names)) == len(names)
    for p in POINTS:
        assert len(p) == 10 and len(p[7]) == 5, p[1]
        assert p[2] in ('RANK', 'PER', 'ABSORB', 'CD10', 'CD20', 'DUR', 'ATT', 'DEF', 'CAST', 'STUN', 'KNOCK', 'SKDMG')
        assert (p[3] == 0) == (p[2] in ('RANK', 'PER')), p[1]


def pool_kinds(p):
    """The pool columns of a point (a skill this server lacks: none)."""
    return {} if p[3] in MISSING_SKILLS else p[8]


check()
