-- MT2009_PLUS_SM_GRANTS_V1: real Smocze Monety (account.account.cash, "SM") paid to accounts at an interval (the owner,
-- 28 October 2026). The panel (seban-panel sm_grants.py, "Ustawienia -> Smocze Monety - nadawanie") edits the tiers and
-- the switch; the worker in the seban-item-grants container pays the due periods every few minutes. Every start
-- (apply.sh), idempotent: CREATE TABLE IF NOT EXISTS and one INSERT IGNORE of the settings row. No tier is seeded: a
-- seeded row would come back after the owner deleted it. sm_grants.py::DDL carries the same statements, so a panel
-- started before this file ran still finds its tables.
SET NAMES utf8mb4;

-- The one settings row: the global switch (off until the owner turns it on) and how many accounts one run may pay.
CREATE TABLE IF NOT EXISTS account.sm_grant_config (
  id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  enabled TINYINT(1) NOT NULL DEFAULT 0,
  per_run_limit INT UNSIGNED NOT NULL DEFAULT 500,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
INSERT IGNORE INTO account.sm_grant_config (id, enabled, per_run_limit) VALUES (1, 0, 500);

-- The tiers ("pakiety"). target: player accounts or bot accounts (login playerbot_*), never both. An account
-- qualifies when one of its characters has level >= min_level and Champion level (player.conqueror_level) >=
-- min_champion_level (0 = not required); active_days > 0 also asks for a login within that many days. Per interval
-- (day / week / month) an account gets only its BEST qualifying tier: the highest Champion requirement, then the
-- highest level requirement, then the larger amount.
CREATE TABLE IF NOT EXISTS account.sm_grant_tier (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target ENUM('player','bot') NOT NULL,
  enabled TINYINT(1) NOT NULL DEFAULT 1,
  name VARCHAR(64) NOT NULL,
  min_level SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  min_champion_level SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  amount INT UNSIGNED NOT NULL,
  period ENUM('day','week','month') NOT NULL DEFAULT 'day',
  active_days SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY target_enabled (target, enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Every payment. period_key is the Europe/Warsaw period: 2026-10-28 (day), 2026-W44 (ISO week), 2026-10 (month).
-- The unique key is what makes a period paid once: the worker inserts the row and adds the SM in the same
-- transaction, and a second insert for the same account, interval and period is ignored, after a restart too.
CREATE TABLE IF NOT EXISTS account.sm_grant_log (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  account_id INT UNSIGNED NOT NULL,
  target ENUM('player','bot') NOT NULL,
  tier_id INT UNSIGNED NOT NULL,
  tier_name VARCHAR(64) NOT NULL DEFAULT '',
  amount INT UNSIGNED NOT NULL,
  period ENUM('day','week','month') NOT NULL,
  period_key VARCHAR(10) NOT NULL,
  granted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY one_per_period (account_id, period, period_key),
  KEY period_key (period, period_key),
  KEY granted_at (granted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- MT2009_PLUS_SM_GRANTS_BOT_SEED_V1 (the owner, 7 November 2026: the bots' weekly packages are the default of a new
-- install, the paying switched on): ONCE - the marker row in account.sm_grant_seed - and only when the install has no
-- bot tier yet, the eight bot tiers of the test world (28 October) go in and the switch goes on. A tier changed or
-- deleted later never comes back (the marker stays); an install with its own bot tiers keeps them and its switch.
-- The players' tiers stay empty (the server owner's to set).
CREATE TABLE IF NOT EXISTS account.sm_grant_seed (
  name VARCHAR(32) NOT NULL PRIMARY KEY,
  applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
SET @mt2009_sm_seed := (SELECT COUNT(*) FROM account.sm_grant_seed WHERE name = 'bot_tiers_v1') = 0
    AND (SELECT COUNT(*) FROM account.sm_grant_tier WHERE target = 'bot') = 0;
INSERT INTO account.sm_grant_tier (target, enabled, name, min_level, min_champion_level, amount, period, active_days)
SELECT t.* FROM (
  SELECT 'bot' AS target, 1 AS enabled, 'Boty do 30 lvl' AS name, 1 AS min_level, 0 AS min_champion_level, 500 AS amount, 'week' AS period, 0 AS active_days
  UNION ALL SELECT 'bot', 1, 'Boty 31-55 lvl', 31, 0, 800, 'week', 0
  UNION ALL SELECT 'bot', 1, 'Boty 56-75 lvl', 56, 0, 1300, 'week', 0
  UNION ALL SELECT 'bot', 1, 'Boty 76-90 lvl', 76, 0, 2000, 'week', 0
  UNION ALL SELECT 'bot', 1, 'Boty 91-110 lvl', 91, 0, 3000, 'week', 0
  UNION ALL SELECT 'bot', 1, 'Boty 111-120 lvl', 111, 0, 4000, 'week', 0
  UNION ALL SELECT 'bot', 1, 'Boty czempion 10+', 1, 10, 7500, 'week', 0
  UNION ALL SELECT 'bot', 1, 'Boty czempion 20+', 1, 20, 9000, 'week', 0
) AS t WHERE @mt2009_sm_seed;
UPDATE account.sm_grant_config SET enabled = 1 WHERE id = 1 AND @mt2009_sm_seed;
INSERT IGNORE INTO account.sm_grant_seed (name) VALUES ('bot_tiers_v1');
