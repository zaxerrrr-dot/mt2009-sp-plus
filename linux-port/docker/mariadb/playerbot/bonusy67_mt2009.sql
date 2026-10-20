-- MT2009_PLUS_RARE_WIKI_V1: back from M2_BONUS_MODE=global to mt2009 (apply.sh: world.item_attr_rare_mt2009 is not
-- empty, i.e. the wiki pool of bonusy67_global.sql is in item_attr_rare). The 6th/7th bonus pool becomes the copy
-- taken of it then (the mt2009 pool, the owner's table of 1 October unless edited since). Items keep every bonus they
-- got in global mode (player.item is never touched) - a line the pool no longer has is only not rolled again.
START TRANSACTION;
DELETE FROM world.item_attr_rare WHERE (SELECT COUNT(*) FROM world.item_attr_rare_mt2009) > 0;
INSERT INTO world.item_attr_rare SELECT * FROM world.item_attr_rare_mt2009;
DELETE FROM world.item_attr_rare_mt2009;
COMMIT;
