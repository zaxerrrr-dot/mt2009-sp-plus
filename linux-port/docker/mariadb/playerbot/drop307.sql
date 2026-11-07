-- MT2009_PLUS_DROP307_V1 - the owner's list of 3 November 2026 (Yohara 3.x, section C "Przedmioty / drop"), the world's
-- part: item_proto flags, Kowal's recipes for the tradeable smith materials, the yang of Zaklety Las. Run by apply.sh
-- (last step before the copy check, after every file that writes these rows). Idempotent: bit operations, conditions
-- on the package's values, INSERT IGNORE. PROTO_FROM_DB - the cores read it at boot. The client's item_proto carries
-- the same flags (client-patches/client-2.0.30/tools/yitems307/patch_yitems307_client.py).
--
-- Bits: flag 4 = ITEM_FLAG_STACKABLE, 256 = ITEM_FLAG_IRREMOVABLE (CHARACTER::CanUnequipNow refuses it);
-- antiflag 256 = ANTI_SELL, 8192 = ANTI_GIVE (trade), 32768 = ANTI_STACK, 65536 = ANTI_MYSHOP, 131072 = ANTI_SAFEBOX
-- (the storekeeper's safebox and Kolekcjoner, playerbot_collector.cpp).

-- 1. Pierscien Doswiadczenia 39002 (the level-90 maps' Metins and bosses, the Yohara bosses): it stacks (STACKABLE,
--    no ANTI_STACK - the stack is 200; one piece of a stack is put on, CHARACTER::EquipItem's unique auto-split), it
--    trades, sells and goes on a stall, and a worn one comes off (no IRREMOVABLE - its timer stops while it is off,
--    as the ItemShop's 72001-72050). Pierscien Doswiadczenia 70005 and Rekawica Zlodzieja 70043 (the Metins' and the
--    bosses' rings / gloves; stack 10): the same trade bits and IRREMOVABLE off. Rekawica Zlodzieja 72005: IRREMOVABLE
--    off. Peleryna Mestwa 39006 (the 90 maps' capes): stacks and trades as 70038 (antiflag 0). Pierscien
--    Doswiadczenia 72003 (the Yohara chests' ring, 83051-83053 / 83067, and the Biologist's boxes; the ItemShop sells
--    none): stacks and trades as 39002.
UPDATE world.item_proto SET flag = (flag | 4) & ~256, antiflag = antiflag & ~(32768 | 256 | 8192 | 65536)
 WHERE vnum IN (39002, 72003);
-- MT2009_PLUS_IRREMOVABLE_KEEP_V1 (the owner, 3 November 2026): 70005 / 70043 / 72005 say "cannot be taken off" and stay so -
-- a worn one is destroyed through the question (server-patches/irrem); trade stays allowed.
UPDATE world.item_proto SET flag = flag | 256, antiflag = antiflag & ~(256 | 8192 | 65536)
 WHERE vnum IN (70005, 70043);
UPDATE world.item_proto SET flag = flag | 256 WHERE vnum = 72005;
UPDATE world.item_proto SET antiflag = antiflag & ~(32768 | 256 | 8192 | 65536) WHERE vnum = 39006;

-- 2. Ksiegi Riposty 50516-50523 (Riposta: Wir Miecza .. Przyw. Blysk.): stacks of 200, as every skill book.
UPDATE world.item_proto SET flag = flag | 4, stack = 200 WHERE vnum BETWEEN 50516 AND 50523 AND type = 17;

-- 3. Lodowa Runa Aury 49990: into the storekeeper's safebox and Kolekcjoner (no ANTI_SAFEBOX).
UPDATE world.item_proto SET antiflag = antiflag & ~131072 WHERE vnum = 49990;

-- 4. Kamien Kowala 39015 / Magiczny Metal 39016 - the tradeable twins of the ItemShop's 71025 / 71026 (their client
--    description already says "Przedmiot ten jest zdatny do handlu"): the bosses' and boss chests' Magiczny Metal and
--    the fishing's Kamien Kowala / Magiczny Metal are these now (the game image, MT2009_PLUS_DROP307_V1). They trade,
--    sell, go on a stall and stack (200); the ItemShop's 71025 / 71026 stay bound.
UPDATE world.item_proto SET flag = flag | 4, stack = 200, antiflag = antiflag & ~(32768 | 256 | 8192 | 65536)
 WHERE vnum IN (39015, 39016);
--    Kowal 20016's crafting window (CRAFTING_BLACKSMITH, crafting_data.lua: rows 1-6 + these 7-10, the game image)
--    takes them as the bound ones: Podrecznik Kowala 25043 / 70039 and Zwoj Boga Smokow 25045 / 71032.
INSERT IGNORE INTO world.crafting_proto (vnum, item_vnum, count, price, chance, recipe, req_progress, req_level, recipe_vnum, comment) VALUES
 (7, 25043, 1, 200000, 100, '25040,1,39015,1', 0, 0, 0, 'MT2009_PLUS_DROP307_V1 Kamien Kowala (handlowy)'),
 (8, 70039, 1, 200000, 100, '25041,1,39015,1', 0, 0, 0, 'MT2009_PLUS_DROP307_V1 Kamien Kowala (handlowy)'),
 (9, 25045, 1, 100000, 100, '25040,1,39016,1', 0, 0, 0, 'MT2009_PLUS_DROP307_V1 Magiczny Metal (handlowy)'),
 (10, 71032, 1, 100000, 100, '25041,1,39016,1', 0, 0, 0, 'MT2009_PLUS_DROP307_V1 Magiczny Metal (handlowy)');

-- 5. Zaklety Las (353): no yang at all - the package (and the clean upstream mob_proto) has gold 0 for every
--    monster of the forest. The monsters get the level-95..105 maps' curve by rank (Przyladek .. Gromiste Gory: rank 0
--    ~190, 1 ~380, 2 ~570, 3 ~770 + a little a level, max = 1.5 x min; x5 in RewardGold); the bosses and the Metin the
--    2.x line's curve (MT2009_PLUS_DROP90_V1: a boss 150 000 + 5 000 a level over 103 .. 220 000 + 7 500, a king
--    300 000 + 10 000 a level over 105 .. 450 000 + 15 000; Metin Lasu 22 000-38 000) - the same values, so whichever
--    of the two steps runs first, the other changes nothing. Only over the package's zero.
UPDATE world.mob_proto SET
       gold_min = ELT(FIELD(vnum, 6401, 6402, 6403, 6404, 6406), 825, 1670, 1690, 2560, 3470),
       gold_max = ELT(FIELD(vnum, 6401, 6402, 6403, 6404, 6406), 1240, 2505, 2535, 3840, 5205)
 WHERE vnum IN (6401, 6402, 6403, 6404, 6406) AND gold_max = 0;
-- MT2009_PLUS_ZAKLETY_YANG_15_V1 (the owner, 7 November 2026: "w Zakletym Lesie musi leciec okolo 1,5x razy wiecej
--    yang niz w Grocie Wygnancow v2" - per kill, his choice): the five monsters of the forest (only here and in Erebu's
--    summons - no other map, group or quest spawns them) x4.34, the rank curve kept (max = 1.5 x min). Expected yang
--    of a kill (the rank's drop percent x the mean of gold_min/max; the rates, the x5 and the level fade the same on
--    both maps): Grota V2 (73, its regen's group_group mix of 2401-2404 / 2411-2414) 268.9, the forest (Owsap's 346
--    group lines, 6311-6317) 93.0 -> 403.4 = 1.50x. The Metins, Wladca En-Tai, Bagjanamu, Jotun Thrym and the Silni
--    En-Tai (Metin Lasu's, 0 yang) unchanged. Over the original values only, so a value the database editor set stays
--    (a fresh row gets the new values from the step above).
UPDATE world.mob_proto SET
       gold_min = ELT(FIELD(vnum, 6401, 6402, 6403, 6404, 6406), 825, 1670, 1690, 2560, 3470),
       gold_max = ELT(FIELD(vnum, 6401, 6402, 6403, 6404, 6406), 1240, 2505, 2535, 3840, 5205)
 WHERE (vnum, gold_min, gold_max) IN ((6401, 190, 285), (6402, 385, 578), (6403, 390, 585), (6404, 590, 885),
                                      (6406, 800, 1200));
UPDATE world.mob_proto
   SET gold_min = IF(`rank` >= 5, 300000 + (GREATEST(level, 105) - 105) * 10000, 150000 + (GREATEST(level, 103) - 103) * 5000),
       gold_max = IF(`rank` >= 5, 450000 + (GREATEST(level, 105) - 105) * 15000, 220000 + (GREATEST(level, 103) - 103) * 7500)
 WHERE vnum IN (6405, 6407, 6408) AND `rank` >= 4 AND gold_max < 100000;
UPDATE world.mob_proto SET gold_min = 22000, gold_max = 38000 WHERE vnum = 8061 AND gold_max < 10000;
