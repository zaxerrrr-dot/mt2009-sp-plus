-- MT2009_PLUS_BOT_SM_MARKET_RULE_V1: Smocze Monety botow na rynku (the owner, 8 November 2026: "Jesli boty maja za duzo
-- SM - nie wystawiaja ich na rynek. Na rynek moga trafic tylko w dwoch przypadkach: (1) SM zostaly wydropione z
-- Metina/bossa/battle passa/z gry; (2) bot bardzo potrzebuje Yang - w tej kategorii moze wystawic maksymalnie 1000 SM
-- lacznie dziennie, wszystkie boty razem"). playerbot_sm_market_rule.h. Every start (apply.sh), idempotent: CREATE TABLE
-- IF NOT EXISTS only - nothing the cores wrote is changed. The cores make the same tables themselves at their first look.
--
--   playerbot_sm_origin       - one row a bot that holds (or held) Kupon SM of its ACCOUNT's Smocze Monety: acct_coins,
--                               the coupons' coins in its bag that came from the account (the panel's "Daj wszystkim
--                               botom SM" coupons, the need sale's own coupons); need_coins, the coins of the server's
--                               daily need pool the bot holds and has not listed yet; need_day / need_today, its own
--                               share of the pool today. Every coupon a bot holds over acct_coins is from the game.
--   playerbot_sm_origin_grant - the panel's coupon grants (player.web_seban_grants rows, done) already credited to
--                               acct_coins: one credit a grant row, whatever core reads it first.
--   playerbot_sm_market_pool  - the need pool of a day (CURDATE() - the database's clock, Europe/Warsaw): the coins
--                               reserved (used, at most the event flag m2_bot_sm_need_daily, default 1000), the coins of
--                               coupon lines the bots put up by origin, the conversions. Every core, every channel.
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS player.playerbot_sm_origin (
  pid INT UNSIGNED NOT NULL PRIMARY KEY,
  acct_coins BIGINT NOT NULL DEFAULT 0 COMMENT 'coupon coins in the bag that came from the account',
  need_coins BIGINT NOT NULL DEFAULT 0 COMMENT 'need pool coins reserved, not listed yet',
  need_day DATE NULL DEFAULT NULL,
  need_today BIGINT NOT NULL DEFAULT 0 COMMENT 'need pool coins this bot reserved on need_day',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS player.playerbot_sm_origin_grant (
  grant_id BIGINT UNSIGNED NOT NULL PRIMARY KEY COMMENT 'player.web_seban_grants.id (0: the baseline marker)',
  pid INT UNSIGNED NOT NULL DEFAULT 0,
  coins BIGINT NOT NULL DEFAULT 0,
  credited TINYINT(1) NOT NULL DEFAULT 0,
  seen_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY credited (credited)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS player.playerbot_sm_market_pool (
  day DATE NOT NULL PRIMARY KEY,
  used BIGINT NOT NULL DEFAULT 0 COMMENT 'need pool coins reserved this day',
  listed_game BIGINT NOT NULL DEFAULT 0 COMMENT 'coins of game coupons the bots listed',
  listed_need BIGINT NOT NULL DEFAULT 0 COMMENT 'coins of account coupons listed from the need pool',
  conversions INT NOT NULL DEFAULT 0 COMMENT 'need reservations (account cash to coupons, or account coupons freed)',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;
