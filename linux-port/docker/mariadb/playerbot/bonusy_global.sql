-- MT2009_PLUS_GLOBAL_BONUS_V1: the item bonus table of M2_BONUS_MODE=global (Tieru's 2.2.31 "Bonusy jak na
-- serwerze globalnym", item_attr_global_2231, mapped by name onto our world.item_attr). apply.sh runs it when the
-- world switches from mt2009 to global - while world.item_attr_mt2009 is empty (it holds the mt2009 rows exactly
-- while the global set is in item_attr, so the state lives in the world database itself) - never twice in a row: an
-- operator's own edit of these rows made while global is on stays. First the 14 rows as they are (the mt2009 set)
-- go to world.item_attr_mt2009 - bonusy_mt2009.sql puts exactly them back. Items keep every bonus they have in both modes
-- (only the random pool changes; player.item is never touched).
--   Max HP to 2000 (prob 35, 500/500/1000/1500/2000), Max SP to 80 on bracelet and boots (max level 4) and 200 on the
--   necklace (10/20/30/80/200), HP and SP regeneration to 30% (4/8/12/20/30); no longer rolled on weapon, armour,
--   bracelet, boots, necklace, helmet, shield, earrings: stamina, stamina regeneration, skill duration, arrow
--   reflection, flat experience (the costume columns and the talisman keep theirs); fire, lightning and wind
--   resistance on armour, bracelet and helmet 2/4/6/10/15 (the talisman column stays: the core gives a talisman its
--   own 5-25%, server-patches/bonusyglobal); chance of an experience bonus on boots, necklace and shield and of
--   double items on bracelet and earrings, 2/4/6/8/20.
-- (empty when this runs: made again, so it has item_attr's columns of today)
DROP TABLE IF EXISTS world.item_attr_mt2009;
CREATE TABLE world.item_attr_mt2009 LIKE world.item_attr;
START TRANSACTION;
INSERT INTO world.item_attr_mt2009 SELECT * FROM world.item_attr WHERE apply IN ('POINT_MAX_HP', 'POINT_MAX_SP',
    'POINT_HP_REGEN', 'POINT_SP_REGEN', 'POINT_MAX_STAMINA', 'POINT_ST_REGEN', 'POINT_SKILL_DURATION',
    'POINT_REFLECT_ARROW', 'POINT_MALL_EXPBONUS', 'POINT_RESIST_FIRE', 'POINT_RESIST_ELEC', 'POINT_RESIST_WIND',
    'POINT_EXP_DOUBLE_BONUS', 'POINT_ITEM_DROP_BONUS');
UPDATE world.item_attr SET prob = 35, lv1 = 500, lv2 = 500, lv3 = 1000, lv4 = 1500, lv5 = 2000 WHERE apply = 'POINT_MAX_HP';
UPDATE world.item_attr SET lv1 = 10, lv2 = 20, lv3 = 30, lv4 = 80, lv5 = 200, wrist = 4, foots = 4, neck = 5
 WHERE apply = 'POINT_MAX_SP';
UPDATE world.item_attr SET lv1 = 4, lv2 = 8, lv3 = 12, lv4 = 20, lv5 = 30 WHERE apply IN ('POINT_HP_REGEN', 'POINT_SP_REGEN');
UPDATE world.item_attr SET weapon = 0, body = 0, wrist = 0, foots = 0, neck = 0, head = 0, shield = 0, ear = 0
 WHERE apply IN ('POINT_MAX_STAMINA', 'POINT_ST_REGEN', 'POINT_SKILL_DURATION', 'POINT_REFLECT_ARROW', 'POINT_MALL_EXPBONUS');
UPDATE world.item_attr SET prob = 18, lv1 = 2, lv2 = 4, lv3 = 6, lv4 = 10, lv5 = 15, weapon = 0, body = 5, wrist = 5,
       foots = 0, neck = 0, head = 5, shield = 0, ear = 0
 WHERE apply IN ('POINT_RESIST_FIRE', 'POINT_RESIST_ELEC', 'POINT_RESIST_WIND');
INSERT INTO world.item_attr (apply, prob, lv1, lv2, lv3, lv4, lv5, weapon, body, wrist, foots, neck, head, shield, ear)
SELECT n.a, n.p, n.l1, n.l2, n.l3, n.l4, n.l5, n.w, n.b, n.wr, n.f, n.ne, n.h, n.s, n.e FROM (
    SELECT 'POINT_RESIST_FIRE' AS a, 18 AS p, 2 AS l1, 4 AS l2, 6 AS l3, 10 AS l4, 15 AS l5, 0 AS w, 5 AS b, 5 AS wr, 0 AS f, 0 AS ne, 5 AS h, 0 AS s, 0 AS e
    UNION ALL SELECT 'POINT_RESIST_ELEC', 18, 2, 4, 6, 10, 15, 0, 5, 5, 0, 0, 5, 0, 0
    UNION ALL SELECT 'POINT_RESIST_WIND', 18, 2, 4, 6, 10, 15, 0, 5, 5, 0, 0, 5, 0, 0
    UNION ALL SELECT 'POINT_EXP_DOUBLE_BONUS', 10, 2, 4, 6, 8, 20, 0, 0, 0, 5, 5, 0, 5, 0
    UNION ALL SELECT 'POINT_ITEM_DROP_BONUS', 7, 2, 4, 6, 8, 20, 0, 0, 5, 0, 0, 0, 0, 5) AS n
 WHERE NOT EXISTS (SELECT 1 FROM world.item_attr AS x WHERE x.apply = n.a);
COMMIT;
