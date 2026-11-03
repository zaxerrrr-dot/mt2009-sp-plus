-- MT2009_PLUS_FISH_PUZZLE_V1: Event Rybacki - Puzzle (the owner, 3 November 2026; server-patches/fishpuzzle, the
-- engine part linux-port/overlays/playerbot/src/game/src/fish_puzzle.cpp). Every start (apply.sh), idempotent.
--
-- player.fish_puzzle: one row a player who has played - the 6 x 4 board (pieces: two characters a piece, its shape
--   '1'-'7' and its top-left cell 'a' + 0..23), the piece in hand (pending 0 none, 1-7), the attempts of the board
--   being laid (uses: boxes opened) and the boards finished (completed). The engine reads and writes it by pid only.
--   MT2009_PLUS_FISH_PUZZLE_V2: the package's player.sql (player.fish_slots blob, fish_use_count) is not taken - this
--   table keeps the same board without a TPlayerTable / db core change; 'pending' is cleared at every client hello.
-- The items (the official vnums - GF 26.1.11 item_list / Owsap's pl item_proto; all five free in our
-- world.item_proto on 3 November 2026). INSERT IGNORE - a row the operator changed is kept:
--   25106 Pudlo wedkarskich puzzli, 25107 Luks. pudlo wedk. puzzli - ITEM_QUEST, stacks of 200; used from the
--         inventory they open the puzzle window (the box is opened there, one piece a box); MT2009_PLUS_FISH_PUZZLE_V2:
--         the antiflags of the owner's package "Mini Game Fish Event (17.3)" (item_proto.txt: ANTI_DROP | ANTI_GIVE |
--         ANTI_MYSHOP = 73856) - V1's 82304 (DROP | SELL | PKDROP | MYSHOP) is changed below where it is still V1's
--   83001 / 83002 / 83003 Zl. Skrzynia na Ryby (M) / (S) / (D) - ITEM_GIFTBOX, one a slot, opened 1 / 2 / 3 times
--         (ShipDefense_ChestKeep), the contents special_item_group.fishpuzzle.txt (game/Dockerfile); tradeable.
-- Client: client-patches/client-2.0.30/tools/fishpuzzle (the same records, item_list lines, itemdesc, GF icons).
SET NAMES utf8mb4;
CREATE TABLE IF NOT EXISTS player.fish_puzzle (
	pid INT UNSIGNED NOT NULL,
	pieces VARCHAR(64) CHARACTER SET ascii NOT NULL DEFAULT '',
	pending TINYINT UNSIGNED NOT NULL DEFAULT 0,
	uses INT NOT NULL DEFAULT 0,
	completed INT UNSIGNED NOT NULL DEFAULT 0,
	updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (pid)
) ENGINE=InnoDB;
INSERT IGNORE INTO world.item_proto (`vnum`,`name`,`locale_name`,`type`,`subtype`,`stack`,`weight`,`size`,`antiflag`,`flag`,`wearflag`,`immuneflag`,`gold`,`shop_buy_price`,`refined_vnum`,`refine_set`,`magic_pct`,`specular`,`socket_pct`,`addon_type`,`limittype0`,`limitvalue0`,`limittype1`,`limitvalue1`,`applytype0`,`applyvalue0`,`applytype1`,`applyvalue1`,`applytype2`,`applyvalue2`,`value0`,`value1`,`value2`,`value3`,`value4`,`value5`,`socket0`,`socket1`,`socket2`,`socket3`,`socket4`,`socket5`) VALUES
(25106,'Fish box',_cp1250 X'507564B36F2077EA646B6172736B6963682070757A7A6C69',18,0,200,0,1,73856,4,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(25107,'Fish box(s)',_cp1250 X'4C756B732E20707564B36F2077EA646B2E2070757A7A6C69',18,0,200,0,1,73856,4,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(83001,'Gold fish chest (M)',_cp1250 X'5AB32E20536B727A796E6961206E61205279627920284D29',23,0,1,0,1,32768,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(83002,'Gold fish chest (S)',_cp1250 X'5AB32E20536B727A796E6961206E61205279627920288C29',23,0,1,0,1,32768,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(83003,'Gold fish chest (D)',_cp1250 X'5AB32E20536B727A796E6961206E61205279627920284429',23,0,1,0,1,32768,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1);
-- MT2009_PLUS_FISH_PUZZLE_V2: a V1 row (antiflag 82304) takes the package's antiflags; a row the operator changed is kept.
UPDATE world.item_proto SET antiflag = 73856 WHERE vnum IN (25106, 25107) AND antiflag = 82304;
-- MT2009_PLUS_FISH_PUZZLE_V3 (the owner's table of the chests, 3 November 2026; special_item_group.fishpuzzle.txt): the
-- chest items our world.item_proto lacked or named wrong. Client: tools/fishpuzzle/patch_fishpuzzle_client.py (COPIES).
--   72309 Podrecznik Kowala (the gift one; Owsap's / GF's vnum, not in our proto) - a copy of 70039's row (USE_TUNING,
--         +15% refine chance, the same antiflags), only the vnum differs; INSERT IGNORE keeps a row already there.
--   72310 Zwoj Egzorcyzmu - the row is 71001's twin but its Polish name was "NoNAme".
--   72027 Dlon Przebicia - the piercing hand (apply 41, +10% for 10 minutes) was named "Dlon Krytyka".
-- A row the operator renamed is kept (the WHERE asks for the old name).
CREATE TEMPORARY TABLE world.mt2009_fishpuzzle_item AS SELECT * FROM world.item_proto WHERE vnum = 70039;
UPDATE world.mt2009_fishpuzzle_item SET vnum = 72309;
INSERT IGNORE INTO world.item_proto SELECT * FROM world.mt2009_fishpuzzle_item;
DROP TEMPORARY TABLE world.mt2009_fishpuzzle_item;
UPDATE world.item_proto SET locale_name = _cp1250 X'5A77F36A2045677A6F7263797A6D75' WHERE vnum = 72310 AND locale_name = 'NoNAme';
UPDATE world.item_proto SET locale_name = _cp1250 X'44B36FF12050727A656269636961'
	WHERE vnum = 72027 AND value1 = 41 AND locale_name = _cp1250 X'44B36FF1204B727974796B61';
