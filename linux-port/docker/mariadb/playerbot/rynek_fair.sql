-- MT2009_PLUS_BOT_FAIR_PRICE_V1: the "fair price" market (the owner, 10 November 2026; docs/RYNEK_UCZCIWA_CENA.md).
-- Every start (apply.sh), idempotent: CREATE TABLE IF NOT EXISTS only - nothing the game or the panel wrote is changed.
--
-- Who writes what:
--   * the game's writer core (playerbot_fair_price.h - one shop-channel core, the lada's tier writer): every kind's row in
--     playerbot_market_fair every m2_bot_fair_step_min minutes (the reference, the ratio, the fair price, the bounds,
--     the market's numbers, the spread of the offers) and its hourly point in playerbot_market_fair_hist; every other
--     core reads playerbot_market_fair every 5 minutes;
--   * the Seban panel ("Gospodarka -> Rynek - uczciwa cena", rynek.py): playerbot_market_fair_pin - a pinned fair price
--     a unit and / or the kind's own bounds (percent of the reference), which the writer reads every step; the global
--     switches are event flags (player.quest rows of pid 0, m2_bot_fair_* and m2_bot_fairprice_off).
-- The game makes the same tables itself when they are missing (EnsurePlayerBotFairTables).
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS player.playerbot_market_fair (
  vnum INT UNSIGNED NOT NULL PRIMARY KEY,
  ref_unit INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'the reference a unit (inflation applied)',
  ref_src CHAR(1) NOT NULL DEFAULT 'S' COMMENT 'O owner, S sheet, P merchant/wallet prior, M real sales',
  ratio_pm INT UNSIGNED NOT NULL DEFAULT 1000 COMMENT 'fair / reference, per mille',
  fair_unit INT UNSIGNED NOT NULL DEFAULT 0,
  min_pm INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'the bounds of the ratio, per mille',
  max_pm INT UNSIGNED NOT NULL DEFAULT 0,
  pin_unit INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'the panel''s pinned fair price, 0 none',
  stock BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'units on every stand',
  offer_lines INT UNSIGNED NOT NULL DEFAULT 0,
  sellers INT UNSIGNED NOT NULL DEFAULT 0,
  sold_w INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'units sold in the window (window_h)',
  events_w INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'sales in the window',
  sold_6h INT UNSIGNED NOT NULL DEFAULT 0,
  sold_hi_6h INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'of them at or above the fair price',
  window_h SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  cover_h INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'stock / units sold an hour (999999: nothing sold)',
  sale_mean INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'trimmed mean of the accepted sales a unit',
  p_min INT UNSIGNED NOT NULL DEFAULT 0,
  p25 INT UNSIGNED NOT NULL DEFAULT 0,
  p50 INT UNSIGNED NOT NULL DEFAULT 0,
  p75 INT UNSIGNED NOT NULL DEFAULT 0,
  p_max INT UNSIGNED NOT NULL DEFAULT 0,
  conf_pm SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'confidence, per mille',
  x_pm SMALLINT NOT NULL DEFAULT 0 COMMENT 'imbalance -1000 (up) .. 1000 (down)',
  move_bp SMALLINT NOT NULL DEFAULT 0 COMMENT 'the move an hour, basis points',
  port SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'the writer core',
  updated INT UNSIGNED NOT NULL DEFAULT 0,
  KEY updated (updated)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS player.playerbot_market_fair_hist (
  vnum INT UNSIGNED NOT NULL,
  hour INT UNSIGNED NOT NULL COMMENT 'unix time / 3600',
  ref_unit INT UNSIGNED NOT NULL DEFAULT 0,
  fair_unit INT UNSIGNED NOT NULL DEFAULT 0,
  stock BIGINT UNSIGNED NOT NULL DEFAULT 0,
  sold INT UNSIGNED NOT NULL DEFAULT 0,
  events INT UNSIGNED NOT NULL DEFAULT 0,
  sold_hi INT UNSIGNED NOT NULL DEFAULT 0,
  sale_mean INT UNSIGNED NOT NULL DEFAULT 0,
  p50 INT UNSIGNED NOT NULL DEFAULT 0,
  sellers INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (vnum, hour),
  KEY hour (hour)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS player.playerbot_market_fair_pin (
  vnum INT UNSIGNED NOT NULL PRIMARY KEY,
  pin_unit INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'a pinned fair price a unit, 0 none',
  min_pct SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'the kind''s own lower bound, % of the reference, 0 global',
  max_pct SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'the kind''s own upper bound, % of the reference, 0 global',
  note VARCHAR(80) NOT NULL DEFAULT '',
  updated_at DATETIME NULL
) ENGINE=InnoDB;
