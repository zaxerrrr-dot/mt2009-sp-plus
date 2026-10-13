-- MT2009_PLUS_CHAMPION_V1 / MT2009_PLUS_SUNGMA_V1: Poziom Czempiona and the Sung Ma stats (server-patches/czempion/README.md,
-- plan cache/yohara/plan-champion-sungma.md). Every start (apply.sh), idempotent: ADD COLUMN IF NOT EXISTS, INSERT IGNORE.
-- The engine reads and writes the eight columns through TPlayerTable (db ClientManagerPlayer.cpp): the db core of a
-- release with the patch needs them, an older core never names them. player_deleted gets the same columns in the
-- same order - a deleted character is copied there with INSERT ... SELECT *.
-- The monsters' champion experience is a game data file (share/locale/<locale>/sungma_mob_exp.txt), not a
-- mob_proto column: no TMobTable or boot packet change.
SET NAMES utf8mb4;

ALTER TABLE player.player
  ADD COLUMN IF NOT EXISTS `conqueror_level` tinyint(3) unsigned NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_CHAMPION_V1',
  ADD COLUMN IF NOT EXISTS `conqueror_level_step` tinyint(3) unsigned NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_CHAMPION_V1',
  ADD COLUMN IF NOT EXISTS `conqueror_exp` int(10) unsigned NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_CHAMPION_V1',
  ADD COLUMN IF NOT EXISTS `conqueror_point` smallint(6) NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_CHAMPION_V1',
  ADD COLUMN IF NOT EXISTS `sungma_str` smallint(6) NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_SUNGMA_V1',
  ADD COLUMN IF NOT EXISTS `sungma_hp` smallint(6) NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_SUNGMA_V1',
  ADD COLUMN IF NOT EXISTS `sungma_move` smallint(6) NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_SUNGMA_V1',
  ADD COLUMN IF NOT EXISTS `sungma_immune` smallint(6) NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_SUNGMA_V1';

ALTER TABLE player.player_deleted
  ADD COLUMN IF NOT EXISTS `conqueror_level` tinyint(3) unsigned NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_CHAMPION_V1',
  ADD COLUMN IF NOT EXISTS `conqueror_level_step` tinyint(3) unsigned NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_CHAMPION_V1',
  ADD COLUMN IF NOT EXISTS `conqueror_exp` int(10) unsigned NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_CHAMPION_V1',
  ADD COLUMN IF NOT EXISTS `conqueror_point` smallint(6) NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_CHAMPION_V1',
  ADD COLUMN IF NOT EXISTS `sungma_str` smallint(6) NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_SUNGMA_V1',
  ADD COLUMN IF NOT EXISTS `sungma_hp` smallint(6) NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_SUNGMA_V1',
  ADD COLUMN IF NOT EXISTS `sungma_move` smallint(6) NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_SUNGMA_V1',
  ADD COLUMN IF NOT EXISTS `sungma_immune` smallint(6) NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_SUNGMA_V1';

-- ---- Nowa Wola 72068-72071 (champion_reset.quest): gives back the points of one Sung Ma stat. The official vnums
-- (GF 26.1.11 item_list.txt, icon/item/72068-72071.tga); free in our world (13 October 2026). Columns as our stat
-- reset scrolls 71103-71106: ITEM_QUEST, stack 200, the same anti flags and quest-use flag.
INSERT IGNORE INTO world.item_proto (`vnum`,`name`,`locale_name`,`type`,`subtype`,`stack`,`weight`,`size`,`antiflag`,`flag`,`wearflag`,`immuneflag`,`gold`,`shop_buy_price`,`refined_vnum`,`refine_set`,`magic_pct`,`specular`,`socket_pct`,`addon_type`,`limittype0`,`limitvalue0`,`limittype1`,`limitvalue1`,`applytype0`,`applyvalue0`,`applytype1`,`applyvalue1`,`applytype2`,`applyvalue2`,`value0`,`value1`,`value2`,`value3`,`value4`,`value5`,`socket0`,`socket1`,`socket2`,`socket3`,`socket4`,`socket5`) VALUES
(72068,'New Will (STR)','Nowa Wola (Siła Sung Ma)',18,0,200,0,1,106880,8192,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(72069,'New Will (VIT)','Nowa Wola (Witalność Sung Ma)',18,0,200,0,1,106880,8192,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(72070,'New Will (RES)','Nowa Wola (Odporność Sung Ma)',18,0,200,0,1,106880,8192,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(72071,'New Will (INT)','Nowa Wola (Inteligencja Sung Ma)',18,0,200,0,1,106880,8192,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1);
