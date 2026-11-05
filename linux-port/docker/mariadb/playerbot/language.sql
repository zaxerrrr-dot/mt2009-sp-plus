-- MT2009_PLUS_LANGUAGE_V1: the language each player reads (server-patches/language/README.md). Every start (apply.sh),
-- idempotent: ADD COLUMN IF NOT EXISTS. The game core reads it when a character enters a core and writes it on
-- "/lang <code>" (mt2009_language.cpp); the db core never names it, so a core without the patch is unaffected.
-- player_deleted gets the same column in the same place - a deleted character is copied there with INSERT ... SELECT *.
-- The panels may show it (the player's language, e.g. for the ItemShop's or the panel's default).
SET NAMES utf8mb4;

ALTER TABLE player.player
  ADD COLUMN IF NOT EXISTS `language` varchar(4) NOT NULL DEFAULT 'pl' COMMENT 'MT2009_PLUS_LANGUAGE_V1';

ALTER TABLE player.player_deleted
  ADD COLUMN IF NOT EXISTS `language` varchar(4) NOT NULL DEFAULT 'pl' COMMENT 'MT2009_PLUS_LANGUAGE_V1';
