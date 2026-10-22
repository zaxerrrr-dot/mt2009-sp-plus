-- MT2009_PLUS_BOT_YOHARA_HANDOVER_V1: przekazanie bota miedzy rdzeniami jednego kanalu
-- (playerbot_yohara_bots.h). Wiersz na bota w drodze albo w pobycie na innym rdzeniu:
--   state 1 - prosba (rdzen, ktory hostuje target_map, przejmuje ja po ready_at),
--   state 2 - pobyt (rdzen-gospodarz odswieza updated_at co minute; po 3 minutach bez odswiezenia
--             wiersz nie trzyma juz bota - wraca przez swoj rdzen domowy).
-- purpose: zaklety / loot / home (szc tylko na linii Yohara). Rdzenie tworza tabele same (CREATE IF NOT EXISTS); tu - zeby
-- byla od startu i zeby kazdy start zaczynal od pustej (apply.sh, przed szybkim startem).
CREATE TABLE IF NOT EXISTS common.playerbot_core_handover (
    pid INT UNSIGNED NOT NULL PRIMARY KEY,
    channel TINYINT UNSIGNED NOT NULL,
    target_map INT NOT NULL,
    x INT NOT NULL,
    y INT NOT NULL,
    from_map INT NOT NULL DEFAULT 0,
    purpose VARCHAR(16) NOT NULL DEFAULT '',
    state TINYINT UNSIGNED NOT NULL DEFAULT 1,
    reason VARCHAR(48) NOT NULL DEFAULT '',
    ready_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY channel_state (channel, state)
) ENGINE=InnoDB;
DELETE FROM common.playerbot_core_handover;
