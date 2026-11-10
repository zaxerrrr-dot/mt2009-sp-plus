-- MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V1: Kolekcjoner Najemnikow - the mercenaries' unlock (the owner, 8 November 2026,
-- /opt/metin2/cache/yohara/najemnicy-plan.md, "Odblokowanie: Kolekcjoner Najemnikow" and "Stale bonusy za zadania
-- Kolekcjonera"). A port of the Arezzo "Collections System" (collections_categories / collections_items) to our
-- 6 tasks. Every start (apply.sh), idempotent: CREATE TABLE IF NOT EXISTS, ADD COLUMN IF NOT EXISTS and INSERT IGNORE
-- of the six tasks - a row already there (changed by hand or by the panel) is never overwritten.
--
-- Who writes what:
--   * this file: the definitions (categories, items, rewards) once;
--   * the game (playerbot_kolekcjoner_najemnikow.cpp, "/kolekcja_najemnikow" behind the client's window): a character's
--     hand-ins (progress), the completed tasks (complete) and, at every completion, player.najemnicy_unlock.tasks
--     (GREATEST, the najemnicy tables) with the quest flag najemnicy.tasks.
-- The game makes the same tables (and the seed) itself when they are missing.
SET NAMES utf8mb4;

-- One task ("collection"). percent = the SUCCESS chance of one hand-in (Arezzo read it as the failure chance).
CREATE TABLE IF NOT EXISTS player.najemnicy_kolekcjoner_categories (
  collection_index TINYINT UNSIGNED NOT NULL COMMENT '1..6, the window order',
  name VARCHAR(48) NOT NULL DEFAULT '' COMMENT 'ASCII key / log name; the client and the game show their Polish name',
  percent TINYINT UNSIGNED NOT NULL DEFAULT 95 COMMENT 'success chance of a hand-in, 1..100',
  PRIMARY KEY (collection_index)
) ENGINE=InnoDB;

-- The items a task wants. item_count = how many in all; pack = how many one hand-in takes (and counts on success);
-- unopened = 1: only a chest never opened (socket 0 = 0 - the openings used, ShipDefense_ChestKeep).
CREATE TABLE IF NOT EXISTS player.najemnicy_kolekcjoner_items (
  collection_index TINYINT UNSIGNED NOT NULL,
  item_index TINYINT UNSIGNED NOT NULL COMMENT '0.., the order in the window',
  item_vnum INT UNSIGNED NOT NULL,
  item_count INT UNSIGNED NOT NULL DEFAULT 1,
  pack INT UNSIGNED NOT NULL DEFAULT 1,
  unopened TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (collection_index, item_index)
) ENGINE=InnoDB;

-- The permanent bonus of a completed task: one row a point (the game's names, playerbot_kolekcjoner_najemnikow.cpp
-- s_aKnPoints: MAX_HP, ATT_GRADE_BONUS, MAGIC_ATT_GRADE_BONUS, ATTBONUS_MONSTER / BOSS / STONE, RESIST_FIRE ...).
CREATE TABLE IF NOT EXISTS player.najemnicy_kolekcjoner_rewards (
  collection_index TINYINT UNSIGNED NOT NULL,
  point_name VARCHAR(32) NOT NULL,
  value INT NOT NULL DEFAULT 0,
  PRIMARY KEY (collection_index, point_name)
) ENGINE=InnoDB;

-- A character's hand-ins: count = what counted (successes x pack), tries = hand-ins made (success or not).
CREATE TABLE IF NOT EXISTS player.najemnicy_kolekcjoner_progress (
  pid INT UNSIGNED NOT NULL,
  collection_index TINYINT UNSIGNED NOT NULL,
  item_index TINYINT UNSIGNED NOT NULL,
  count INT UNSIGNED NOT NULL DEFAULT 0,
  tries INT UNSIGNED NOT NULL DEFAULT 0,
  updated_at DATETIME NULL,
  PRIMARY KEY (pid, collection_index, item_index)
) ENGINE=InnoDB;

-- A character's completed tasks: nr = the order it was completed in (1..6: the n-th task -> the mercenary tier n).
-- The row IS the permanent bonus: the game adds the task's rewards to the character's points at every recompute
-- (CHARACTER::ComputePoints) - no affect, no expiry, nothing the player can remove.
CREATE TABLE IF NOT EXISTS player.najemnicy_kolekcjoner_complete (
  pid INT UNSIGNED NOT NULL,
  collection_index TINYINT UNSIGNED NOT NULL,
  nr TINYINT UNSIGNED NOT NULL DEFAULT 0,
  completed_at DATETIME NULL,
  PRIMARY KEY (pid, collection_index)
) ENGINE=InnoDB;

-- Later columns go here (ADD COLUMN IF NOT EXISTS), never into the CREATEs above only.
ALTER TABLE player.najemnicy_kolekcjoner_items ADD COLUMN IF NOT EXISTS unopened TINYINT UNSIGNED NOT NULL DEFAULT 0 AFTER pack;
ALTER TABLE player.najemnicy_kolekcjoner_progress ADD COLUMN IF NOT EXISTS tries INT UNSIGNED NOT NULL DEFAULT 0 AFTER count;

-- The owner's six tasks (8 November 2026), any order, each once, 95%.
INSERT IGNORE INTO player.najemnicy_kolekcjoner_categories (collection_index, name, percent) VALUES
  (1, 'Skrzynie bossow', 95),
  (2, 'Kamienie Duszy', 95),
  (3, 'Cor Draconis', 95),
  (4, 'Odlamki Energii', 95),
  (5, 'Perly i malze', 95),
  (6, 'Bossowie lochow', 95);

INSERT IGNORE INTO player.najemnicy_kolekcjoner_items (collection_index, item_index, item_vnum, item_count, pack, unopened) VALUES
  -- 1 Skrzynie bossow: Szkat. Dziewieciu Ogonow, Zoltego Tygrysa, Ognistego Krola - 5 each, one at a time
  (1, 0, 50077, 5, 1, 0),
  (1, 1, 50078, 5, 1, 0),
  (1, 2, 50079, 5, 1, 0),
  -- 2 Kamienie Duszy: Obrony+4, Przyspieszenia+4, Potwora+4 - 3 each, one at a time
  (2, 0, 28442, 3, 1, 0),
  (2, 1, 28443, 3, 1, 0),
  (2, 2, 28437, 3, 1, 0),
  -- 3 Cor Draconis (Rough): 100, packs of 10
  (3, 0, 50255, 100, 10, 0),
  -- 4 Odlamki Energii: 1000, packs of 100
  (4, 0, 51001, 1000, 100, 0),
  -- 5 Biala / Niebieska / Krwawa Perla 10 each one at a time, Malz 50 in packs of 10
  (5, 0, 27992, 10, 1, 0),
  (5, 1, 27993, 10, 1, 0),
  (5, 2, 27994, 10, 1, 0),
  (5, 3, 27987, 50, 10, 0),
  -- 6 Szkat. Umarlego Rozpruwacza 5, Zlota Skrzynia Zodiaku 5, Skrzynia Nemere 10 - only never opened: the first two
  -- go when opened (one opening), so any in the bag is unopened; the Nemere chest opens 3 times and keeps the openings
  -- used in socket 0 (ShipDefense_ChestKeep), so it is taken only with socket 0 = 0 (3/3 left)
  (6, 0, 50082, 5, 1, 0),
  (6, 1, 33033, 5, 1, 0),
  (6, 2, 50271, 10, 1, 1);

INSERT IGNORE INTO player.najemnicy_kolekcjoner_rewards (collection_index, point_name, value) VALUES
  (1, 'ATTBONUS_BOSS', 10),
  (2, 'ATTBONUS_STONE', 10),
  (3, 'ATTBONUS_MONSTER', 10),
  (4, 'RESIST_FIRE', 10),
  (4, 'RESIST_ICE', 10),
  (4, 'RESIST_ELEC', 10),
  (4, 'RESIST_WIND', 10),
  (4, 'RESIST_EARTH', 10),
  (4, 'RESIST_DARK', 10),
  (5, 'MAX_HP', 5000),
  (6, 'ATT_GRADE_BONUS', 100),
  (6, 'MAGIC_ATT_GRADE_BONUS', 100);

-- MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V2 (the owner, 10 November 2026): the tasks are edited in the Seban panel
-- ("Wydarzenia -> Najemnicy -> Kolekcjoner", kolekcjoner_config.py). The window shows the task's title and description
-- ('' = the client's built-in ones), min_level = the level a hand-in needs (0 = none), sort_order = the window's
-- order; an item's sort_order is its place in the window (item_index stays the progress rows' key). The tiers: the
-- n-th completed task -> so many mercenaries from that level (playerbot_najemnicy.h counts the slots from this table).
-- The panel writes the event flag m2_kolekcjoner_najemnikow_ver at every change; the game reads it again within 30 s.
ALTER TABLE player.najemnicy_kolekcjoner_categories ADD COLUMN IF NOT EXISTS title VARCHAR(64) NOT NULL DEFAULT '' AFTER percent;
ALTER TABLE player.najemnicy_kolekcjoner_categories ADD COLUMN IF NOT EXISTS description VARCHAR(200) NOT NULL DEFAULT '' AFTER title;
ALTER TABLE player.najemnicy_kolekcjoner_categories ADD COLUMN IF NOT EXISTS min_level SMALLINT UNSIGNED NOT NULL DEFAULT 0 AFTER description;
ALTER TABLE player.najemnicy_kolekcjoner_categories ADD COLUMN IF NOT EXISTS sort_order SMALLINT NOT NULL DEFAULT 0 AFTER min_level;
ALTER TABLE player.najemnicy_kolekcjoner_items ADD COLUMN IF NOT EXISTS sort_order SMALLINT NOT NULL DEFAULT 0 AFTER unopened;

CREATE TABLE IF NOT EXISTS player.najemnicy_kolekcjoner_tiers (
  nr TINYINT UNSIGNED NOT NULL COMMENT 'the n-th completed collector task (1..16)',
  slots TINYINT UNSIGNED NOT NULL DEFAULT 2 COMMENT 'mercenaries allowed with it (1..7)',
  level SMALLINT UNSIGNED NOT NULL DEFAULT 80 COMMENT 'from this character level',
  PRIMARY KEY (nr)
) ENGINE=InnoDB;

-- The owner's table (8 November 2026), only into an empty table (the panel's rows are never overwritten).
INSERT IGNORE INTO player.najemnicy_kolekcjoner_tiers (nr, slots, level)
  SELECT * FROM (SELECT 1 AS nr, 2 AS slots, 80 AS level UNION ALL SELECT 2, 3, 85 UNION ALL SELECT 3, 4, 90
    UNION ALL SELECT 4, 5, 95 UNION ALL SELECT 5, 6, 100 UNION ALL SELECT 6, 7, 105) seed
  WHERE NOT EXISTS (SELECT 1 FROM player.najemnicy_kolekcjoner_tiers);

-- The six tasks' titles and descriptions - only where the panel left them empty (all sort_order 0 = by index).
UPDATE player.najemnicy_kolekcjoner_categories SET title='Skrzynie bossów' WHERE collection_index=1 AND title='';
UPDATE player.najemnicy_kolekcjoner_categories SET title='Kamienie Duszy' WHERE collection_index=2 AND title='';
UPDATE player.najemnicy_kolekcjoner_categories SET title='Cor Draconis' WHERE collection_index=3 AND title='';
UPDATE player.najemnicy_kolekcjoner_categories SET title='Odłamki Energii' WHERE collection_index=4 AND title='';
UPDATE player.najemnicy_kolekcjoner_categories SET title='Perły i małże' WHERE collection_index=5 AND title='';
UPDATE player.najemnicy_kolekcjoner_categories SET title='Bossowie lochów' WHERE collection_index=6 AND title='';
UPDATE player.najemnicy_kolekcjoner_categories SET description='Szkatułki bossów, oddawane po jednej.' WHERE collection_index=1 AND description='';
UPDATE player.najemnicy_kolekcjoner_categories SET description='Kamienie Duszy +4, oddawane po jednym.' WHERE collection_index=2 AND description='';
UPDATE player.najemnicy_kolekcjoner_categories SET description='Cor Draconis z misji Alchemika, paczki po 10.' WHERE collection_index=3 AND description='';
UPDATE player.najemnicy_kolekcjoner_categories SET description='Odłamki Energii, oddawane w paczkach po 100.' WHERE collection_index=4 AND description='';
UPDATE player.najemnicy_kolekcjoner_categories SET description='Perły po jednej, małże w paczkach po 10.' WHERE collection_index=5 AND description='';
UPDATE player.najemnicy_kolekcjoner_categories SET description='Skrzynie bossów lochów, tylko nieotwierane.' WHERE collection_index=6 AND description='';
