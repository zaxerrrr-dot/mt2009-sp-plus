-- MT2009_PLUS_HORSE40_V3 (the owner, 30 October 2026, poprawki-3.0.6 item 1): no horse bags ("juki konne") on Yohara.
-- Once per world (marker horse_bags_gone_v1 in player.playerbot_migrations), run by apply.sh before the db and game
-- cores start (playerbot-migrate is their service_completed_successfully dependency - no core holds a cached item):
-- every item kept in a horse bag (INVENTORY cells 180-224, the fifth bag page after the four pages of 5 x 9) moves
--   1. to the first free place of the owner's four bag pages (cells 0-179, a page 5 x 9, an item of size 2-3 standing
--      in one column of one page - CHARACTER::IsEmptyItemGrid's rule, the size from world.item_proto);
--   2. when the bag has no room, to the account's storeroom (window SAFEBOX, owner = the account): the pages a bot's
--      storeroom has (4, MT2009_PLUS_BOT_SAFEBOX_PAGES_V1) or a person's own size (1-2; no row or anything else = 1 -
--      CInputDB::SafeboxLoad; the premium page is not counted, it may run out), the same 5 x 9 grid;
--   3. when that is full too, to the ItemShop storage (player.item_award, mall 1: the owner takes it in the game) with
--      its sockets and bonuses.
-- In one transaction with the marker: a failure rolls everything back and apply.sh runs it again at the next start.
-- Every move is logged in player.horse_bag_migration_log (item, owner, where to). The flags of the gone system go too:
-- the special flag horse_inventory_slot, the bots' playerbot.saddlebag_next_row and the stock horse_inventory_init
-- state. The engine opens no bag cell any more (server-patches/konie, CanUseHorseInventory). Items of a character
-- that no longer exists (no player row) stay where they are - nobody can log in to them.

CREATE TABLE IF NOT EXISTS player.horse_bag_migration_log (
	id INT UNSIGNED NOT NULL AUTO_INCREMENT,
	item_id INT UNSIGNED NOT NULL,
	owner_id INT UNSIGNED NOT NULL,
	account_id INT UNSIGNED NOT NULL,
	vnum INT UNSIGNED NOT NULL,
	count INT UNSIGNED NOT NULL,
	from_pos SMALLINT UNSIGNED NOT NULL,
	dest ENUM('INVENTORY', 'SAFEBOX', 'ITEM_AWARD') NOT NULL,
	dest_pos INT UNSIGNED NOT NULL DEFAULT 0,
	moved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	KEY owner_id (owner_id)
) ENGINE = InnoDB;

-- the work tables: ordinary InnoDB tables (a query names the taken cells up to three times, which a temporary table
-- cannot be; point lookups on the primary key), made again here when a run broke off and dropped at the end
DROP PROCEDURE IF EXISTS player.mt2009_horse_bags_gone;
DROP TABLE IF EXISTS player.mt2009_hb_items, player.mt2009_hb_occ, player.mt2009_hb_n;
CREATE TABLE player.mt2009_hb_n (n INT NOT NULL PRIMARY KEY) ENGINE = InnoDB;
CREATE TABLE player.mt2009_hb_items (
	id INT UNSIGNED NOT NULL PRIMARY KEY,
	owner_id INT UNSIGNED NOT NULL,
	account_id INT UNSIGNED NOT NULL,
	pos INT NOT NULL,
	size INT NOT NULL,
	pages INT NOT NULL
) ENGINE = InnoDB;
CREATE TABLE player.mt2009_hb_occ (
	kind TINYINT NOT NULL,
	owner INT UNSIGNED NOT NULL,
	cell INT NOT NULL,
	PRIMARY KEY (kind, owner, cell)
) ENGINE = InnoDB;

DELIMITER //
CREATE PROCEDURE player.mt2009_horse_bags_gone()
BEGIN
	DECLARE v_done INT DEFAULT 0;
	DECLARE v_id INT UNSIGNED;
	DECLARE v_owner INT UNSIGNED;
	DECLARE v_acc INT UNSIGNED;
	DECLARE v_pos INT;
	DECLARE v_size INT;
	DECLARE v_pages INT;
	DECLARE v_cell INT;
	DECLARE cur CURSOR FOR SELECT id, owner_id, account_id, pos, size, pages FROM player.mt2009_hb_items ORDER BY owner_id, pos;
	DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;
	DECLARE EXIT HANDLER FOR SQLEXCEPTION
	BEGIN
		ROLLBACK;
		RESIGNAL;
	END;

	IF (SELECT COUNT(*) FROM player.playerbot_migrations WHERE name = 'horse_bags_gone_v1') = 0 THEN
		START TRANSACTION;

		-- the cell numbers of four pages
		INSERT INTO player.mt2009_hb_n (n)
			WITH RECURSIVE s (n) AS (SELECT 0 UNION ALL SELECT n + 1 FROM s WHERE n < 179) SELECT n FROM s;

		-- the items in the horse bags, their size and their storeroom's pages
		INSERT INTO player.mt2009_hb_items (id, owner_id, account_id, pos, size, pages)
			SELECT i.id, i.owner_id, p.account_id, i.pos, LEAST(3, GREATEST(1, COALESCE(ip.size, 1))),
				CASE WHEN BINARY a.login LIKE BINARY 'playerbot\_%' THEN 4
					WHEN sb.size IN (1, 2) THEN sb.size ELSE 1 END
			FROM player.item i
			JOIN player.player p ON p.id = i.owner_id
			LEFT JOIN account.account a ON a.id = p.account_id
			LEFT JOIN player.safebox sb ON sb.account_id = p.account_id
			LEFT JOIN world.item_proto ip ON ip.vnum = i.vnum
			WHERE i.window = 'INVENTORY' AND i.pos BETWEEN 180 AND 224;

		-- the taken cells: kind 0 the owner's four bag pages, kind 1 the account's storeroom
		INSERT IGNORE INTO player.mt2009_hb_occ (kind, owner, cell)
			SELECT 0, i.owner_id, i.pos + 5 * k.k
			FROM player.item i
			JOIN (SELECT 0 AS k UNION ALL SELECT 1 UNION ALL SELECT 2) k
			LEFT JOIN world.item_proto ip ON ip.vnum = i.vnum
			WHERE i.window = 'INVENTORY' AND i.pos < 180 AND k.k < LEAST(3, GREATEST(1, COALESCE(ip.size, 1)))
				AND i.owner_id IN (SELECT owner_id FROM player.mt2009_hb_items);
		INSERT IGNORE INTO player.mt2009_hb_occ (kind, owner, cell)
			SELECT 1, i.owner_id, i.pos + 5 * k.k
			FROM player.item i
			JOIN (SELECT 0 AS k UNION ALL SELECT 1 UNION ALL SELECT 2) k
			LEFT JOIN world.item_proto ip ON ip.vnum = i.vnum
			WHERE i.window = 'SAFEBOX' AND k.k < LEAST(3, GREATEST(1, COALESCE(ip.size, 1)))
				AND i.owner_id IN (SELECT account_id FROM player.mt2009_hb_items);

		OPEN cur;
		moving: LOOP
			FETCH cur INTO v_id, v_owner, v_acc, v_pos, v_size, v_pages;
			IF v_done THEN
				LEAVE moving;
			END IF;

			-- 1. the bag: a cell whose column on its page has room for the item
			SET v_cell = NULL;
			SELECT MIN(c.n) INTO v_cell FROM player.mt2009_hb_n c
				WHERE (c.n MOD 45) DIV 5 + v_size <= 9
					AND NOT EXISTS (SELECT 1 FROM player.mt2009_hb_occ o WHERE o.kind = 0 AND o.owner = v_owner AND o.cell = c.n)
					AND (v_size < 2 OR NOT EXISTS (SELECT 1 FROM player.mt2009_hb_occ o
						WHERE o.kind = 0 AND o.owner = v_owner AND o.cell = c.n + 5))
					AND (v_size < 3 OR NOT EXISTS (SELECT 1 FROM player.mt2009_hb_occ o
						WHERE o.kind = 0 AND o.owner = v_owner AND o.cell = c.n + 10));
			IF v_cell IS NOT NULL THEN
				UPDATE player.item SET pos = v_cell WHERE id = v_id;
				INSERT IGNORE INTO player.mt2009_hb_occ (kind, owner, cell)
					SELECT 0, v_owner, v_cell + 5 * k.k FROM (SELECT 0 AS k UNION ALL SELECT 1 UNION ALL SELECT 2) k
					WHERE k.k < v_size;
				INSERT INTO player.horse_bag_migration_log (item_id, owner_id, account_id, vnum, count, from_pos, dest, dest_pos)
					SELECT id, v_owner, v_acc, vnum, count, v_pos, 'INVENTORY', v_cell FROM player.item WHERE id = v_id;
			ELSE
				-- 2. the storeroom
				SELECT MIN(c.n) INTO v_cell FROM player.mt2009_hb_n c
					WHERE c.n < 45 * v_pages AND (c.n MOD 45) DIV 5 + v_size <= 9
						AND NOT EXISTS (SELECT 1 FROM player.mt2009_hb_occ o WHERE o.kind = 1 AND o.owner = v_acc AND o.cell = c.n)
						AND (v_size < 2 OR NOT EXISTS (SELECT 1 FROM player.mt2009_hb_occ o
							WHERE o.kind = 1 AND o.owner = v_acc AND o.cell = c.n + 5))
						AND (v_size < 3 OR NOT EXISTS (SELECT 1 FROM player.mt2009_hb_occ o
							WHERE o.kind = 1 AND o.owner = v_acc AND o.cell = c.n + 10));
				IF v_cell IS NOT NULL THEN
					UPDATE player.item SET window = 'SAFEBOX', owner_id = v_acc, pos = v_cell WHERE id = v_id;
					INSERT IGNORE INTO player.mt2009_hb_occ (kind, owner, cell)
						SELECT 1, v_acc, v_cell + 5 * k.k FROM (SELECT 0 AS k UNION ALL SELECT 1 UNION ALL SELECT 2) k
						WHERE k.k < v_size;
					INSERT INTO player.horse_bag_migration_log (item_id, owner_id, account_id, vnum, count, from_pos, dest, dest_pos)
						SELECT id, v_owner, v_acc, vnum, count, v_pos, 'SAFEBOX', v_cell FROM player.item WHERE id = v_id;
				ELSE
					-- 3. the ItemShop storage
					INSERT INTO player.item_award (pid, login, vnum, count, why, socket0, socket1, socket2,
							attrtype0, attrvalue0, attrtype1, attrvalue1, attrtype2, attrvalue2, attrtype3, attrvalue3,
							attrtype4, attrvalue4, attrtype5, attrvalue5, attrtype6, attrvalue6, mall)
						SELECT v_owner, COALESCE(a.login, ''), i.vnum, i.count, 'juki konne (MT2009_PLUS_HORSE40_V3)',
							i.socket0, i.socket1, i.socket2, i.attrtype0, i.attrvalue0, i.attrtype1, i.attrvalue1,
							i.attrtype2, i.attrvalue2, i.attrtype3, i.attrvalue3, i.attrtype4, i.attrvalue4,
							i.attrtype5, i.attrvalue5, i.attrtype6, i.attrvalue6, 1
						FROM player.item i LEFT JOIN account.account a ON a.id = v_acc
						WHERE i.id = v_id;
					INSERT INTO player.horse_bag_migration_log (item_id, owner_id, account_id, vnum, count, from_pos, dest, dest_pos)
						SELECT id, v_owner, v_acc, vnum, count, v_pos, 'ITEM_AWARD', LAST_INSERT_ID() FROM player.item WHERE id = v_id;
					DELETE FROM player.item WHERE id = v_id;
				END IF;
			END IF;
		END LOOP;
		CLOSE cur;

		-- the gone system's flags
		DELETE FROM player.player_special_flag WHERE flag = 'horse_inventory_slot';
		DELETE FROM player.quest WHERE szName = 'playerbot' AND szState = 'saddlebag_next_row';
		DELETE FROM player.quest WHERE szName IN ('horse_inventory', 'horse_inventory_init');

		INSERT INTO player.playerbot_migrations (name, done_at) VALUES ('horse_bags_gone_v1', NOW());
		COMMIT;
	END IF;
END //
DELIMITER ;

CALL player.mt2009_horse_bags_gone();
DROP PROCEDURE IF EXISTS player.mt2009_horse_bags_gone;
DROP TABLE IF EXISTS player.mt2009_hb_items, player.mt2009_hb_occ, player.mt2009_hb_n;

SELECT CONCAT('horse bags: ', dest, ' ', COUNT(*)) FROM player.horse_bag_migration_log GROUP BY dest;
