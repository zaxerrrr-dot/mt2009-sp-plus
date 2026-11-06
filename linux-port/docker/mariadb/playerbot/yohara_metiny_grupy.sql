-- MT2009_PLUS_YOHARA_STONE_GROUPS_V1 (6 November 2026, the second bot analysis, item 2): the Time Rift / Plaskowyz
-- Metins call the groups their place has. A stone calls a random group of attack_speed..move_speed (char_state.cpp
-- __StateIdle_Stone); these four kept Owsap's numbers, which our generators renumbered (tools/yohara_crack: Owsap's
-- 6401-6407 as 6178-6184; tools/yohara_iluzja: 6411-6417 as 6171-6177 - 6408-6412 are Atlantyda's groups here):
--   8126 SZC: Metin Drz. Stworzen  6401-6404 -> 6178-6181 (none existed: NOT_EXIST_GROUP_VNUM on 404)
--   8127 SZC: Metin Lasu           6420-6423 -> 6178-6181 (Owsap's 6420-6423 = 6401-6404, the same monsters)
--   8136 PB: Metin Drz. Stworzen   6411-6414 -> 6171-6174 (6411/6412 called Atlantyda's Stwor z Glebin and
--                                                           Nieumarly Rybi Wojownik onto map 371; 6413/6414 none)
--   8137 PB: Metin Lasu            6430-6433 -> 6171-6174 (Owsap's 6430-6433 = 6411-6414)
-- MT2009_PLUS_YOHARA_STONE_GROUPS_V3 (6 November 2026, "sprawdz jak jest na globalu"): Metin Jin (8065, maps 377/385)
-- kept the global 6176-6178, which here are Plaskowyz Iluzji's PB En-Tai (6176/6177) and Szczelina Czasu's SZC Wojownik
-- En-Tai (6178) - so it called those onto 377/385. Global: the earth Myr (Kovix, Proletariusz, Golem, Bojownik):
--   8065 Metin Jin                 6176-6178 -> 6221-6223 (game/yohara_metiny/group.yohara_metiny.txt)
-- Guarded: only a row that still has Owsap's numbers (one the operator set is kept). Idempotent. After every Yohara
-- mob file (apply.sh). The groups of the other Yohara Metins and eggs: game/yohara_metiny/group.yohara_metiny.txt.
SET NAMES utf8mb4;
UPDATE world.mob_proto SET attack_speed = 6178, move_speed = 6181 WHERE vnum = 8126 AND attack_speed = 6401 AND move_speed = 6404;
UPDATE world.mob_proto SET attack_speed = 6178, move_speed = 6181 WHERE vnum = 8127 AND attack_speed = 6420 AND move_speed = 6423;
UPDATE world.mob_proto SET attack_speed = 6171, move_speed = 6174 WHERE vnum = 8136 AND attack_speed = 6411 AND move_speed = 6414;
UPDATE world.mob_proto SET attack_speed = 6171, move_speed = 6174 WHERE vnum = 8137 AND attack_speed = 6430 AND move_speed = 6433;
UPDATE world.mob_proto SET attack_speed = 6221, move_speed = 6223 WHERE vnum = 8065 AND attack_speed = 6176 AND move_speed = 6178;
