-- MT2009_PLUS_ELEMENT_STONES_V1: one Kamien Ochrony Zywiolow (39120, 7 days from now) for every Yohara bot - a ONE-OFF,
-- run by hand WITH THE GAME STOPPED (the cores keep the bots' items in memory and would write over the rows).
-- Not run by apply.sh or any update. The bots' own pass (playerbot_element_stones.h) does the same in the game - it
-- puts the stone on and gives a new one when it ends; this only spares the first wait.
--
-- Who: the members of common.playerbot_yohara_cohort with purpose 'yohara' or 'yohara800' (the Sung Ma maps' bots)
-- that hold no element stone (39119 / 39120) anywhere yet - a second run gives nothing to anybody.
-- Where: the first unique slot (EQUIPMENT pos 7) when it is empty, else the second (pos 8), else the first free cell
-- of the bag's four pages (INVENTORY 0-179; an item of size 2/3 covers the cells under it). A bot with both slots taken
-- and a full bag gets nothing (listed at the end); in the game its pass puts the bag's stone on in place of the least
-- useful unique.
-- Needs: world.item_proto 39120 (kamienie_zywiolow.sql - apply.sh has run once with this update); without it nothing
-- is inserted.
--
-- Run (vps1, the test stack; the game stopped first):
--   docker exec -i mt2009plustest-db sh -c 'MYSQL_PWD="$MARIADB_ROOT_PASSWORD" mariadb -uroot' \
--       < tools/kamienie_zywiolow/grant_yohara_bots.sql
-- Undo (game stopped): DELETE FROM player.item WHERE vnum = 39120 AND owner_id IN
--   (SELECT pid FROM common.playerbot_yohara_cohort WHERE purpose IN ('yohara', 'yohara800'));
SET NAMES latin1;
START TRANSACTION;

DROP TEMPORARY TABLE IF EXISTS player.mt2009_elemstone_todo;
CREATE TEMPORARY TABLE player.mt2009_elemstone_todo (pid INT UNSIGNED NOT NULL PRIMARY KEY) ENGINE=MEMORY;
INSERT INTO player.mt2009_elemstone_todo (pid)
SELECT DISTINCT c.pid FROM common.playerbot_yohara_cohort c
  JOIN player.player p ON p.id = c.pid
 WHERE c.purpose IN ('yohara', 'yohara800')
   AND EXISTS (SELECT 1 FROM world.item_proto ip WHERE ip.vnum = 39120)
   AND NOT EXISTS (SELECT 1 FROM player.item i WHERE i.owner_id = c.pid AND i.vnum IN (39119, 39120));
SELECT COUNT(*) AS bots_without_a_stone FROM player.mt2009_elemstone_todo;

-- 1. the first unique slot
INSERT INTO player.item (owner_id, window, pos, count, vnum, socket0)
SELECT t.pid, 'EQUIPMENT', 7, 1, 39120, UNIX_TIMESTAMP() + 604800 FROM player.mt2009_elemstone_todo t
 WHERE NOT EXISTS (SELECT 1 FROM player.item i WHERE i.owner_id = t.pid AND i.window = 'EQUIPMENT' AND i.pos = 7);
DELETE t FROM player.mt2009_elemstone_todo t JOIN player.item i ON i.owner_id = t.pid AND i.vnum = 39120;

-- 2. the second unique slot
INSERT INTO player.item (owner_id, window, pos, count, vnum, socket0)
SELECT t.pid, 'EQUIPMENT', 8, 1, 39120, UNIX_TIMESTAMP() + 604800 FROM player.mt2009_elemstone_todo t
 WHERE NOT EXISTS (SELECT 1 FROM player.item i WHERE i.owner_id = t.pid AND i.window = 'EQUIPMENT' AND i.pos = 8);
DELETE t FROM player.mt2009_elemstone_todo t JOIN player.item i ON i.owner_id = t.pid AND i.vnum = 39120;

-- 3. the first free cell of the bag (the cohort tool's free-cell rule)
INSERT INTO player.item (owner_id, window, pos, count, vnum, socket0)
WITH RECURSIVE n(pos) AS (SELECT 0 UNION ALL SELECT pos + 1 FROM n WHERE pos < 179)
SELECT t.pid, 'INVENTORY', MIN(n.pos), 1, 39120, UNIX_TIMESTAMP() + 604800
  FROM player.mt2009_elemstone_todo t JOIN n
 WHERE NOT EXISTS (SELECT 1 FROM player.item i JOIN player.item_proto ip ON ip.vnum = i.vnum
                    WHERE i.owner_id = t.pid AND i.window = 'INVENTORY' AND n.pos >= i.pos
                      AND n.pos < i.pos + 5 * GREATEST(ip.size, 1) AND (n.pos - i.pos) % 5 = 0)
 GROUP BY t.pid;
DELETE t FROM player.mt2009_elemstone_todo t JOIN player.item i ON i.owner_id = t.pid AND i.vnum = 39120;

-- what is left: both unique slots taken and a full bag
SELECT t.pid AS no_room_for_a_stone, p.name FROM player.mt2009_elemstone_todo t JOIN player.player p ON p.id = t.pid;
DROP TEMPORARY TABLE player.mt2009_elemstone_todo;
COMMIT;

SELECT c.purpose,
       COUNT(DISTINCT c.pid) AS members,
       COUNT(DISTINCT CASE WHEN i.window = 'EQUIPMENT' THEN c.pid END) AS stone_worn,
       COUNT(DISTINCT CASE WHEN i.window = 'INVENTORY' THEN c.pid END) AS stone_in_bag
  FROM common.playerbot_yohara_cohort c
  LEFT JOIN player.item i ON i.owner_id = c.pid AND i.vnum = 39120
 WHERE c.purpose IN ('yohara', 'yohara800')
 GROUP BY c.purpose;
