-- MT2009_PLUS_COMMUNITY_V1: the Community window (server-patches/community/README.md, playerbot_community.cpp; the
-- package "Community System (Messenger Renewal)", Autor: Best Studio - its 03. Server/mysql file, with our second
-- column). Every start (apply.sh), idempotent: ADD COLUMN IF NOT EXISTS.
--   status_message   the status message a player shows his friends (at most 50 bytes, CP1250 as the game's latin1)
--   community_flags  bits 0-2 the state he chose (0 online, 1 AFK, 4 appear offline), 8 hide his level, 16 hide his
--                    location from his friends
-- The game core reads them at each login (one query per login with the friend list's) and writes them when the
-- player changes them; the db core never names them. player_deleted gets the same columns in the same order - a
-- deleted character is copied there with INSERT ... SELECT * (ClientManagerPlayer.cpp) - so the two tables get them
-- in one statement each, after every column the earlier steps added (no AFTER).
SET NAMES utf8mb4;

ALTER TABLE player.player
  ADD COLUMN IF NOT EXISTS `status_message` varchar(50) NOT NULL DEFAULT '' COMMENT 'MT2009_PLUS_COMMUNITY_V1',
  ADD COLUMN IF NOT EXISTS `community_flags` tinyint(3) unsigned NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_COMMUNITY_V1';

ALTER TABLE player.player_deleted
  ADD COLUMN IF NOT EXISTS `status_message` varchar(50) NOT NULL DEFAULT '' COMMENT 'MT2009_PLUS_COMMUNITY_V1',
  ADD COLUMN IF NOT EXISTS `community_flags` tinyint(3) unsigned NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_COMMUNITY_V1';
