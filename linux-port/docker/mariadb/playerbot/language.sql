-- MT2009_PLUS_LANGUAGE_V1: the language each player reads (server-patches/language/README.md). Every start (apply.sh),
-- idempotent: ADD COLUMN IF NOT EXISTS. The game core reads it when a character enters a core and writes it on
-- "/lang <code>" (mt2009_language.cpp); the db core never names it, so a core without the patch is unaffected.
-- player_deleted gets the same column in the same place - a deleted character is copied there with INSERT ... SELECT *.
-- The panels may show it (the player's language, e.g. for the ItemShop's or the panel's default).
--
-- MT2009_PLUS_LANGUAGE_DEFAULT_V1 (the owner, 5 November 2026: a default language for the whole server): NULL = the
-- player never chose a language and reads the server's default (M2_DEFAULT_LANGUAGE in .env); a code = his own choice,
-- kept whatever the default becomes. The first version had NOT NULL DEFAULT 'pl', so a stored 'pl' cannot tell "never
-- chose" from "chose Polish": once, while the column is still NOT NULL, it becomes nullable and every 'pl' becomes
-- NULL. A client whose user did choose a language sends it again at the next entry into the game ("/lang <code>").
SET NAMES utf8mb4;

SET @m2lang_old_player := (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'player'
  AND TABLE_NAME = 'player' AND COLUMN_NAME = 'language' AND IS_NULLABLE = 'NO');
SET @m2lang_old_deleted := (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'player'
  AND TABLE_NAME = 'player_deleted' AND COLUMN_NAME = 'language' AND IS_NULLABLE = 'NO');

ALTER TABLE player.player
  ADD COLUMN IF NOT EXISTS `language` varchar(4) NULL DEFAULT NULL COMMENT 'MT2009_PLUS_LANGUAGE_V1';

ALTER TABLE player.player_deleted
  ADD COLUMN IF NOT EXISTS `language` varchar(4) NULL DEFAULT NULL COMMENT 'MT2009_PLUS_LANGUAGE_V1';

-- The one-time conversion of a column the first version made (only while it is still NOT NULL).
EXECUTE IMMEDIATE IF(@m2lang_old_player > 0,
  'ALTER TABLE player.player MODIFY COLUMN `language` varchar(4) NULL DEFAULT NULL COMMENT ''MT2009_PLUS_LANGUAGE_V1''',
  'DO 0');
EXECUTE IMMEDIATE IF(@m2lang_old_player > 0,
  'UPDATE player.player SET `language` = NULL WHERE `language` = ''pl'' OR `language` = ''''',
  'DO 0');
EXECUTE IMMEDIATE IF(@m2lang_old_deleted > 0,
  'ALTER TABLE player.player_deleted MODIFY COLUMN `language` varchar(4) NULL DEFAULT NULL COMMENT ''MT2009_PLUS_LANGUAGE_V1''',
  'DO 0');
EXECUTE IMMEDIATE IF(@m2lang_old_deleted > 0,
  'UPDATE player.player_deleted SET `language` = NULL WHERE `language` = ''pl'' OR `language` = ''''',
  'DO 0');
