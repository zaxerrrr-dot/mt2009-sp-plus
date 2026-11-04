-- MT2009_PLUS_TITLES_V1: Tytuly (the owner's package "Official Title System Renewal", rebuilt; server-patches/tytuly,
-- the engine part linux-port/overlays/playerbot/src/game/src/playerbot_titles.cpp). Every start (apply.sh), idempotent.
--
-- player.player_title: one row an owned title - pid, title_index (playerbot_titles.cpp TITLES), end_time (unix time, 0 =
--   for good), equipped (1 = the worn one, at most one row of a pid). Read at login, written at a change. The package's
--   table plus `equipped` (it kept the worn title in a quest flag); its latin5 charset is not needed (numbers only).
-- The certificates (the package's vnums 57000-57002, free in our world.item_proto on 4 November 2026; 57003-57008 free
--   too): ITEM_QUEST like the fish puzzle boxes (the engine's use hook takes them before the item's type), one a slot.
--   MT2009_PLUS_TITLES_V2 (the owner, 4 November 2026: "Tytuly jak na wiki ... trzeba kupic certyfikaty w ItemShopie"):
--   one certificate a title whose wiki source we do not have, named as pl-wiki names them ("Tytul Czciciel Slonca"),
--   the wiki's flags (pl-wiki: no NPC sale, no trade, no shop, no drop, no stacking; storeroom yes): no drop, no sale,
--   no give, no PK drop, no stacking, no private shop = 123264; value0 = the title, value1 = its time in seconds (0 =
--   the title's default, the wiki's time - playerbot_titles.cpp TITLES). The icons are GF's three (red / blue / green):
--   57000 Tytul Heroiczny        -> 1002 (30 days, another one adds 30)   red
--   57001 Tytul Szczesciarz      -> 1000 (for good)                       blue
--   57002 Tytul Czciciel Slonca  -> 1005 (365 days)                       green
--   57003 Tytul PLUS             -> 1001 (30 days)                        red
--   57004 Tytul Legendarny       -> 1003 (30 days)                        red
--   57005 Tytul Mistyczny        -> 1004 (30 days)                        red
--   57006 Tytul Gwiazda Polarna  -> 1006 (365 days)                       green
--   57007 Tytul Czempion Nyx     -> 1007 (for good)                       blue
--   57008 Tytul Ostatni Ocalaly  -> 1 (3 hours)                           blue
--   INSERT IGNORE - a row the operator changed is kept; V1's three rows (other names, the package's antiflags 123008)
--   are set to these once (the mark 'tytuly:certs_v2' in player.playerbot_migrations).
--   The ItemShop's lines 40-48 (apply.sh, ishop_once tytuly_certs_40, after this file).
-- player.player_title.granted_at (V2): the time a title the server gave by itself (TitleSystemGrantPid - the weekly
--   ranking, Okey, the Treasure Hunt) was written for a character not on that core; every core reads the rows newer
--   than its last look once a minute (the index), 0 for every other write.
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
ALTER TABLE player.player_title ADD COLUMN IF NOT EXISTS granted_at INT UNSIGNED NOT NULL DEFAULT 0;
ALTER TABLE player.player_title ADD INDEX IF NOT EXISTS granted_at (granted_at);
-- MT2009_PLUS_TITLES_V2: V1's three certificates once
CREATE TABLE IF NOT EXISTS player.playerbot_migrations (name VARCHAR(64) NOT NULL PRIMARY KEY, done_at DATETIME NOT NULL) ENGINE=InnoDB;
SET @tytuly_v2 = (SELECT COUNT(*) FROM player.playerbot_migrations WHERE name = 'tytuly:certs_v2');
UPDATE world.item_proto SET name='Title: Heroic', locale_name=_cp1250 X'54797475B3204865726F69637A6E79', antiflag=123264, value0=1002, value1=0 WHERE vnum=57000 AND @tytuly_v2 = 0;
UPDATE world.item_proto SET name='Title: Lucky', locale_name=_cp1250 X'54797475B320537A637AEA9C636961727A', antiflag=123264, value0=1000, value1=0 WHERE vnum=57001 AND @tytuly_v2 = 0;
UPDATE world.item_proto SET name='Title: Sun Worshipper', locale_name=_cp1250 X'54797475B320437A63696369656C2053B36FF16361', antiflag=123264, value0=1005, value1=0 WHERE vnum=57002 AND @tytuly_v2 = 0;
INSERT IGNORE INTO world.item_proto (`vnum`,`name`,`locale_name`,`type`,`subtype`,`stack`,`weight`,`size`,`antiflag`,`flag`,`wearflag`,`immuneflag`,`gold`,`shop_buy_price`,`refined_vnum`,`refine_set`,`magic_pct`,`specular`,`socket_pct`,`addon_type`,`limittype0`,`limitvalue0`,`limittype1`,`limitvalue1`,`applytype0`,`applyvalue0`,`applytype1`,`applyvalue1`,`applytype2`,`applyvalue2`,`value0`,`value1`,`value2`,`value3`,`value4`,`value5`,`socket0`,`socket1`,`socket2`,`socket3`,`socket4`,`socket5`) VALUES
(57000,'Title: Heroic',_cp1250 X'54797475B3204865726F69637A6E79',18,0,1,0,1,123264,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1002,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(57001,'Title: Lucky',_cp1250 X'54797475B320537A637AEA9C636961727A',18,0,1,0,1,123264,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1000,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(57002,'Title: Sun Worshipper',_cp1250 X'54797475B320437A63696369656C2053B36FF16361',18,0,1,0,1,123264,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1005,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(57003,'Title: PLUS',_cp1250 X'54797475B320504C5553',18,0,1,0,1,123264,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1001,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(57004,'Title: Legendary',_cp1250 X'54797475B3204C6567656E6461726E79',18,0,1,0,1,123264,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1003,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(57005,'Title: Mythic',_cp1250 X'54797475B3204D69737479637A6E79',18,0,1,0,1,123264,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1004,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(57006,'Title: North Star',_cp1250 X'54797475B320477769617A646120506F6C61726E61',18,0,1,0,1,123264,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1006,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(57007,'Title: Nyx Champion',_cp1250 X'54797475B320437A656D70696F6E204E7978',18,0,1,0,1,123264,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1007,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(57008,'Title: Last Survivor',_cp1250 X'54797475B3204F737461746E69204F63616C61B379',18,0,1,0,1,123264,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,-1,-1,-1,-1,-1,-1);
INSERT IGNORE INTO player.playerbot_migrations (name, done_at) VALUES ('tytuly:certs_v2', NOW());
