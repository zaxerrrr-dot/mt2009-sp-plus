-- MT2009_PLUS_NAJEMNICY_V1: "Najemnicy" - a player's hired party (the owner, 8 November 2026,
-- /opt/metin2/cache/yohara/najemnicy-plan.md). Every start (apply.sh), idempotent: CREATE TABLE IF NOT EXISTS /
-- ADD COLUMN IF NOT EXISTS only - nothing the game or the panel wrote is changed.
--
-- Who writes what:
--   * the game (playerbot_najemnicy.h, "/najemnicy" behind the Najemnicy quest): a new mercenary's identity (an account
--     playerbot_njNNNN with password '!' and status BLOCK + player + player_index + a najemnicy row), the vault's
--     deposits and the fee a minute, setup_done at its first entry, retired / retired_at, and - 20 minutes after a
--     retirement, offline - the deletion of the retired character, its account and items; the GM's unlock;
--   * the Seban panel ("Wydarzenia -> Najemnicy", najemnicy.py): a character's Kolekcjoner Najemnikow tasks count
--     (najemnicy_unlock.tasks 0..6 - stage 1's unlock until the collector exists; slots = tasks x level), the switches (player.quest
--     rows with dwPID 0: m2_najemnicy_off, m2_najemnicy_free_unlock, m2_najemnicy_price_h).
-- The game makes the same tables itself when they are missing (EnsureNajemnicyTables).
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS player.najemnicy (
  merc_pid INT UNSIGNED NOT NULL COMMENT 'the mercenary character (player.player.id)',
  owner_pid INT UNSIGNED NOT NULL COMMENT 'the player who hired it, for good',
  slot TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '1..7: 80 -> 2 slots, 85 -> 3 ... 105 -> 7',
  account_id INT UNSIGNED NOT NULL DEFAULT 0,
  login VARCHAR(16) NOT NULL DEFAULT '' COMMENT 'playerbot_njNNNN',
  seq INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'the login number',
  job TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'player.job (race 0..7: class + sex)',
  skill_group TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT 'the path: 1 or 2',
  sex TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0 male, 1 female',
  name VARCHAR(24) NOT NULL DEFAULT '',
  setup_done TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '1 after its first entry (its bag emptied)',
  created_at DATETIME NULL,
  retired TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '1: let go, deleted 20 min later',
  retired_at DATETIME NULL,
  PRIMARY KEY (merc_pid),
  KEY owner_live (owner_pid, retired),
  KEY seq (seq)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS player.najemnicy_vault (
  owner_pid INT UNSIGNED NOT NULL,
  balance BIGINT NOT NULL DEFAULT 0 COMMENT 'yang left for the fee',
  total_paid BIGINT NOT NULL DEFAULT 0 COMMENT 'yang the fee took, ever',
  total_deposit BIGINT NOT NULL DEFAULT 0 COMMENT 'yang paid in, ever',
  updated_at DATETIME NULL,
  PRIMARY KEY (owner_pid)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS player.najemnicy_unlock (
  owner_pid INT UNSIGNED NOT NULL,
  unlocked TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT 'tasks > 0 (kept for reading)',
  tasks TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'the Kolekcjoner Najemnikow tasks done, 0..6 (GM / panel; the quest flag najemnicy.tasks too)',
  unlocked_at DATETIME NULL,
  source VARCHAR(32) NOT NULL DEFAULT '' COMMENT 'gm:<name>, panel, (later) the mission',
  PRIMARY KEY (owner_pid)
) ENGINE=InnoDB;

-- Later columns of the first version's tables go here (ADD COLUMN IF NOT EXISTS), never into the CREATEs above only.
ALTER TABLE player.najemnicy ADD COLUMN IF NOT EXISTS setup_done TINYINT UNSIGNED NOT NULL DEFAULT 0 AFTER name;
ALTER TABLE player.najemnicy ADD COLUMN IF NOT EXISTS retired_at DATETIME NULL AFTER retired;
ALTER TABLE player.najemnicy_vault ADD COLUMN IF NOT EXISTS total_deposit BIGINT NOT NULL DEFAULT 0 AFTER total_paid;
ALTER TABLE player.najemnicy_unlock ADD COLUMN IF NOT EXISTS tasks TINYINT UNSIGNED NOT NULL DEFAULT 0 AFTER unlocked;
ALTER TABLE player.najemnicy_unlock ADD COLUMN IF NOT EXISTS source VARCHAR(32) NOT NULL DEFAULT '' AFTER unlocked_at;
