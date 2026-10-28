-- MT2009_PLUS_GAYA_CURRENCY_V1: Gaya as a currency of the character, as on the global servers (the owner, 28 October
-- 2026; server-patches/gaya2/README.md). Every start (apply.sh), idempotent: ADD COLUMN IF NOT EXISTS. The engine reads
-- and writes the column through TPlayerTable (db ClientManagerPlayer.cpp, after the champion columns): the db core of a
-- release with the patch needs it, an older core never names it. player_deleted gets the same column at the same
-- place - a deleted character is copied there with INSERT ... SELECT *.
-- The Gaya items (95927) of before are changed into it by the game core itself (once, logged: char log "GAYA", item
-- log "GAYA_CURRENCY" / "GAYA_PICKUP"): the bag and the extra inventory at the login, the warehouse and the ItemShop
-- storage when they are opened - nothing to run by hand.
SET NAMES utf8mb4;

ALTER TABLE player.player
  ADD COLUMN IF NOT EXISTS `gaya` int(10) unsigned NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_GAYA_CURRENCY_V1';

ALTER TABLE player.player_deleted
  ADD COLUMN IF NOT EXISTS `gaya` int(10) unsigned NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_GAYA_CURRENCY_V1';
