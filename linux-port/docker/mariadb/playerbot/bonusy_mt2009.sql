-- MT2009_PLUS_GLOBAL_BONUS_V1: back from M2_BONUS_MODE=global to mt2009 (apply.sh: world.item_attr_mt2009 is not
-- empty, i.e. the global set is in item_attr). The 14 rows
-- bonusy_global.sql changed or added are replaced by the copy it took of them (world.item_attr_mt2009): a row that
-- did not exist then (the experience and double-item chances) is gone again. Items keep every bonus they rolled in
-- global mode (player.item is never touched) - a line the pool no longer has is only not rolled again.
START TRANSACTION;
DELETE FROM world.item_attr WHERE apply IN ('POINT_MAX_HP', 'POINT_MAX_SP',
    'POINT_HP_REGEN', 'POINT_SP_REGEN', 'POINT_MAX_STAMINA', 'POINT_ST_REGEN', 'POINT_SKILL_DURATION',
    'POINT_REFLECT_ARROW', 'POINT_MALL_EXPBONUS', 'POINT_RESIST_FIRE', 'POINT_RESIST_ELEC', 'POINT_RESIST_WIND',
    'POINT_EXP_DOUBLE_BONUS', 'POINT_ITEM_DROP_BONUS')
   AND (SELECT COUNT(*) FROM world.item_attr_mt2009) > 0;
INSERT INTO world.item_attr SELECT * FROM world.item_attr_mt2009;
DELETE FROM world.item_attr_mt2009;
COMMIT;
