-- MT2009_PLUS_ARROWS_GLOBAL_V1: the ammunition as on the global server (the owner, 5 November 2026: "wgraj na serwer
-- strzaly i wartosci bonusow jak na globalu, nie ograniczaj ataku w moby jak dotychczas"; the pl-wiki's category
-- Przedmioty/Amunicja). apply.sh runs it every start after gf_wartosci.sql / refine_global.sql. Idempotent.
--
--   8000-8005  the six arrows: level, attack (value3) and magic attack (value1) of the wiki, no bonus line, value2 /
--              value4 / value5 0 (the engine no longer reads them: a stack fades by the distance alone, a quiver
--              never - MT2009_PLUS_ARROWS_GLOBAL_V2, server-patches/strzaly). The
--              Wooden Arrow's price as the wiki's 100 for 20 Yang (COUNT_PER_1GOLD, 5 a Yang; ours was 1 a Yang).
--   8011/8012  Kolczan for 1 day (100 000 Yang) and for 7 days (550 000 Yang) at the General Store (shop 3, 9003),
--              the wiki's two quivers. Copies of the ItemShop's 14-day Kolczan 8010 (apply.sh, MT2009_PLUS_QUIVER_V1:
--              Ninja only, unlimited arrows - a timed arrow is a quiver to the engine and the bots - 25 / 4, no
--              trade / drop / stall / safebox; level 1 - V2, was 35). The time runs from the purchase (LIMIT_REAL_TIME).
--   30395      Balathor's Hwacha arrow takes the wiki's name, Plonaca Strzala (it was Ognista Strzala - the same
--              name as the Archer's skill and the arrow 8006).
-- The client's rows: client-patches/client-2.0.30/tools/strzaly (item_proto, item_list, itemdesc, itemname).
SET NAMES utf8mb4;

UPDATE world.item_proto SET
    limittype0 = 1, limitvalue0 = ELT(vnum - 7999, 0, 10, 30, 40, 45, 50),
    value1 = ELT(vnum - 7999, 1, 2, 3, 4, 5, 4),
    value3 = ELT(vnum - 7999, 3, 10, 15, 17, 20, 25),
    value2 = 0, value4 = 0, value5 = 0,
    applytype0 = 0, applyvalue0 = 0, applytype1 = 0, applyvalue1 = 0, applytype2 = 0, applyvalue2 = 0
WHERE vnum BETWEEN 8000 AND 8005 AND type = 1 AND subtype = 6;
UPDATE world.item_proto SET gold = 5, shop_buy_price = 5 WHERE vnum = 8000 AND gold = 1 AND (flag & 8) <> 0;

DROP TEMPORARY TABLE IF EXISTS world.arrows_global_quiver;
CREATE TEMPORARY TABLE world.arrows_global_quiver AS SELECT * FROM world.item_proto WHERE vnum = 8010 LIMIT 1;
UPDATE world.arrows_global_quiver SET vnum = 8011;
INSERT IGNORE INTO world.item_proto SELECT * FROM world.arrows_global_quiver;
UPDATE world.arrows_global_quiver SET vnum = 8012;
INSERT IGNORE INTO world.item_proto SELECT * FROM world.arrows_global_quiver;
DROP TEMPORARY TABLE IF EXISTS world.arrows_global_quiver;
UPDATE world.item_proto q JOIN world.item_proto k ON k.vnum = 8010 SET
    q.name = 'Quiver', q.locale_name = k.locale_name, q.type = 1, q.subtype = 6, q.stack = 1, q.size = 1,
    q.antiflag = k.antiflag, q.flag = 0, q.wearflag = 512, q.refined_vnum = 0, q.refine_set = 0,
    q.limittype0 = 7, q.limitvalue0 = IF(q.vnum = 8011, 86400, 604800),
    q.limittype1 = k.limittype1, q.limitvalue1 = k.limitvalue1,
    q.applytype0 = 0, q.applyvalue0 = 0, q.applytype1 = 0, q.applyvalue1 = 0, q.applytype2 = 0, q.applyvalue2 = 0,
    q.value0 = 0, q.value1 = 4, q.value2 = 0, q.value3 = 25, q.value4 = 0, q.value5 = 0
WHERE q.vnum IN (8011, 8012);
-- the price: once, so an operator's own price stays
UPDATE world.item_proto SET gold = IF(vnum = 8011, 100000, 550000), shop_buy_price = IF(vnum = 8011, 100000, 550000)
WHERE vnum IN (8011, 8012) AND gold = 0;
INSERT IGNORE INTO world.shop_item (shop_vnum, item_vnum, count)
SELECT 3, v.vnum, 1 FROM (SELECT 8011 AS vnum UNION ALL SELECT 8012) v
WHERE EXISTS (SELECT 1 FROM world.shop WHERE vnum = 3) AND EXISTS (SELECT 1 FROM world.item_proto p WHERE p.vnum = v.vnum);

UPDATE world.item_proto SET locale_name = _cp1250 X'50B36F6EB96361205374727A61B361', name = 'Flaming Arrow'
WHERE vnum = 30395 AND locale_name = _cp1250 X'4F676E69737461205374727A61B361';
