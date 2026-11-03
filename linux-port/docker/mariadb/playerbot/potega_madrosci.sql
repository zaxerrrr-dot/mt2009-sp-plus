-- MT2009_PLUS_POTEGA_MADROSCI_V1: "Potega madrosci" - Uriel's experience bonus by level range (the owner, 3 November
-- 2026; the pl-wiki's server pages). The quest potega_madrosci.quest reads these tables on every talk, the cores
-- (playerbot_potega.h, the bots) every minute; the advanced panel's page "Potega madrosci" (seban-panel
-- potega_madrosci.py) edits them - a change is live at the next talk, no restart. Whether the event runs is the event
-- flag potega_madrosci (the events planner's kind "potega"), not a column here.
-- Every start (apply.sh), idempotent: CREATE TABLE IF NOT EXISTS; the wiki's table is seeded ONCE, together with the
-- settings row - a range the owner deleted does not come back. potega_madrosci.py::DDL carries the same statements.
SET NAMES utf8mb4;

-- The ranges. champion 0: the character's level; 1: its Champion level (a Champion - Champion level 1 or more - is
-- judged by these rows only). The first enabled row (by champion, lvl_from, lvl_to) that holds the level gives pct.
CREATE TABLE IF NOT EXISTS player.potega_madrosci_tier (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  enabled TINYINT(1) NOT NULL DEFAULT 1,
  champion TINYINT(1) NOT NULL DEFAULT 0,
  lvl_from SMALLINT UNSIGNED NOT NULL,
  lvl_to SMALLINT UNSIGNED NOT NULL,
  pct SMALLINT UNSIGNED NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY champion_from (champion, lvl_from)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- The pl-wiki's table, only when the settings row does not exist yet (the first start).
INSERT INTO player.potega_madrosci_tier (champion, lvl_from, lvl_to, pct)
  SELECT * FROM (SELECT 0 AS c, 41 AS f, 80 AS t, 25 AS p UNION ALL SELECT 0, 81, 100, 50 UNION ALL SELECT 0, 101, 120, 100
                 UNION ALL SELECT 1, 1, 10, 125 UNION ALL SELECT 1, 11, 30, 100) AS wiki
  WHERE NOT EXISTS (SELECT 1 FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'player' AND TABLE_NAME = 'potega_madrosci_config');

-- The one settings row: how long the bonus lasts (minutes, the wiki's 4 hours), whether bots take it and what share of
-- the bots near an Uriel bother (per cent).
CREATE TABLE IF NOT EXISTS player.potega_madrosci_config (
  id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  minutes INT UNSIGNED NOT NULL DEFAULT 240,
  bots TINYINT(1) NOT NULL DEFAULT 1,
  bot_share TINYINT UNSIGNED NOT NULL DEFAULT 60,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
INSERT IGNORE INTO player.potega_madrosci_config (id, minutes, bots, bot_share) VALUES (1, 240, 1, 60);
