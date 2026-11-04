-- MT2009_PLUS_TITLES_V1: Tytuly (the owner's package "Official Title System Renewal", rebuilt; server-patches/tytuly,
-- the engine part linux-port/overlays/playerbot/src/game/src/playerbot_titles.cpp). Every start (apply.sh), idempotent.
--
-- player.player_title: one row an owned title - pid, title_index (playerbot_titles.cpp TITLES), end_time (unix time, 0 =
--   for good), equipped (1 = the worn one, at most one row of a pid). Read at login, written at a change. The package's
--   table plus `equipped` (it kept the worn title in a quest flag); its latin5 charset is not needed (numbers only).
-- The certificates (the package's vnums 57000-57002, free in our world.item_proto on 4 November 2026): ITEM_QUEST like
--   the fish puzzle boxes (the engine's use hook takes them before the item's type), one a slot, the package's
--   antiflags (no drop, no give, no PK drop, no stacking, no private shop = 123008); value0 = the title, value1 = its time
--   in seconds (0 = the title's default). INSERT IGNORE - a row the operator changed is kept:
--   57000 Czerwony Certyfikat Tytulu  -> 1002 Heroiczny (30 days, another one adds 30)
--   57001 Niebieski Certyfikat Tytulu -> 1000 Szczesciarz (for good)
--   57002 Zielony Certyfikat Tytulu   -> 1005 Czciciel Slonca (for good)
-- Client: client-patches/client-2.0.30/tools/tytuly (the same records, item_list lines, itemdesc, icons).
SET NAMES utf8mb4;
CREATE TABLE IF NOT EXISTS player.player_title (
	pid INT UNSIGNED NOT NULL,
	title_index INT UNSIGNED NOT NULL,
	end_time INT UNSIGNED NOT NULL DEFAULT 0,
	equipped TINYINT UNSIGNED NOT NULL DEFAULT 0,
	PRIMARY KEY (pid, title_index)
) ENGINE=InnoDB;
ALTER TABLE player.player_title ADD COLUMN IF NOT EXISTS equipped TINYINT UNSIGNED NOT NULL DEFAULT 0;
INSERT IGNORE INTO world.item_proto (`vnum`,`name`,`locale_name`,`type`,`subtype`,`stack`,`weight`,`size`,`antiflag`,`flag`,`wearflag`,`immuneflag`,`gold`,`shop_buy_price`,`refined_vnum`,`refine_set`,`magic_pct`,`specular`,`socket_pct`,`addon_type`,`limittype0`,`limitvalue0`,`limittype1`,`limitvalue1`,`applytype0`,`applyvalue0`,`applytype1`,`applyvalue1`,`applytype2`,`applyvalue2`,`value0`,`value1`,`value2`,`value3`,`value4`,`value5`,`socket0`,`socket1`,`socket2`,`socket3`,`socket4`,`socket5`) VALUES
(57000,'Red title certificate',_cp1250 X'437A6572776F6E7920436572747966696B61742054797475B375',18,0,1,0,1,123008,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1002,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(57001,'Blue title certificate',_cp1250 X'4E6965626965736B6920436572747966696B61742054797475B375',18,0,1,0,1,123008,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1000,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(57002,'Green title certificate',_cp1250 X'5A69656C6F6E7920436572747966696B61742054797475B375',18,0,1,0,1,123008,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1005,0,0,0,0,0,-1,-1,-1,-1,-1,-1);
