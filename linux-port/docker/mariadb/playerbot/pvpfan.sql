-- MT2009_PLUS_PVPFAN_V1: "PVP Fan" - bot wars for fun (the owner, 7 November 2026: "boty, ktorych jedynym zadaniem
-- jest walczyc ze soba ... np. 50 Wojownikow Cialo vs 50 Szamanow Smok"). Every start (apply.sh), idempotent: CREATE
-- TABLE IF NOT EXISTS / ADD COLUMN IF NOT EXISTS only - nothing the panel or the game wrote is changed.
--
-- Who writes what:
--   * the Seban panel ("Wydarzenia -> PVP Fan", pvpfan.py): the categories, their teams and slots, the equipment
--     sets and their items, the characters (account playerbot_pfNNNN + player + player_index + pvpfan_char rows,
--     made while nobody plays them) and the commands of its Start / Gotowi / Stop buttons;
--   * the game core that hosts the category's arena map on its channel (playerbot_pvpfan.h): the category's state,
--     the wars and their teams' results, the commands it took; "/pvpfan tu" writes the arena point and
--     pvpfan_gm_pos (the panel's "position of the GM" hint).
-- The game reads the configuration once per "/pvpfan start" (never on a timer), polls pvpfan_command every 3 s.
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS player.pvpfan_category (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(32) NOT NULL COMMENT 'the name in /pvpfan start <code>: a-z 0-9 _ -',
  name VARCHAR(64) NOT NULL DEFAULT '',
  enabled TINYINT(1) NOT NULL DEFAULT 1,
  map_index INT NOT NULL DEFAULT 0 COMMENT 'the arena map (0 = not set yet)',
  x INT NOT NULL DEFAULT 0 COMMENT 'the arena centre, global units',
  y INT NOT NULL DEFAULT 0,
  radius INT NOT NULL DEFAULT 1500 COMMENT 'how far each team starts from the centre',
  arena_radius INT NOT NULL DEFAULT 5000 COMMENT 'a bot further than this from the centre walks back',
  channel TINYINT UNSIGNED NOT NULL DEFAULT 1,
  countdown_sec TINYINT UNSIGNED NOT NULL DEFAULT 5,
  max_minutes SMALLINT UNSIGNED NOT NULL DEFAULT 15 COMMENT 'after this the team with more standing wins',
  exit_sec SMALLINT UNSIGNED NOT NULL DEFAULT 20 COMMENT 'after the result, the bots log off',
  allow_players TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1: people may hit the bots and be hit',
  potions TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1: the bots drink their potions in the fight',
  state VARCHAR(16) NOT NULL DEFAULT 'idle' COMMENT 'idle starting waiting countdown fighting finished stopping',
  state_note VARCHAR(255) NOT NULL DEFAULT '',
  state_at DATETIME NULL,
  core VARCHAR(32) NOT NULL DEFAULT '' COMMENT 'the core that runs the war now',
  online SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  alive_text VARCHAR(255) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS player.pvpfan_team (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  category_id INT UNSIGNED NOT NULL,
  idx TINYINT UNSIGNED NOT NULL DEFAULT 1,
  name VARCHAR(32) NOT NULL DEFAULT '',
  empire TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'the characters kingdom, 0 = 1/3/2 by the team number',
  x INT NOT NULL DEFAULT 0 COMMENT 'own start point (global), 0 = round the arena centre',
  y INT NOT NULL DEFAULT 0,
  name_prefix VARCHAR(12) NOT NULL DEFAULT '' COMMENT 'the characters names, empty = by the class',
  PRIMARY KEY (id),
  KEY category (category_id, idx)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS player.pvpfan_slot (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  category_id INT UNSIGNED NOT NULL,
  team_id INT UNSIGNED NOT NULL,
  job TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0 Wojownik 1 Ninja 2 Sura 3 Szaman',
  skill_group TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '1 or 2 (Cialo/Mental, Skrytobojca/Lucznik, Bron/Magia, Smok/Leczenie)',
  sex ENUM('male','female') NOT NULL DEFAULT 'male',
  count SMALLINT UNSIGNED NOT NULL DEFAULT 10,
  level TINYINT UNSIGNED NOT NULL DEFAULT 120,
  skill_level TINYINT UNSIGNED NOT NULL DEFAULT 40 COMMENT '20 M1, 30 G1, 40 P',
  st SMALLINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0 = the class preset',
  ht SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  dx SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  iq SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  set_id INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'equipment set, 0 = the preset of the class and path',
  sort SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  KEY team (team_id, sort),
  KEY category (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS player.pvpfan_set (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(64) NOT NULL DEFAULT '',
  job TINYINT UNSIGNED NOT NULL DEFAULT 255 COMMENT '255 = any class',
  skill_group TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0 = any path',
  preset_key VARCHAR(16) NOT NULL DEFAULT '' COMMENT 'w1 w2 n1 n2 s1 s2 sh1 sh2 - the class preset',
  red_vnum INT UNSIGNED NOT NULL DEFAULT 27003,
  red_count SMALLINT UNSIGNED NOT NULL DEFAULT 400,
  blue_vnum INT UNSIGNED NOT NULL DEFAULT 27006,
  blue_count SMALLINT UNSIGNED NOT NULL DEFAULT 400,
  note VARCHAR(255) NOT NULL DEFAULT '',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY preset (preset_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS player.pvpfan_set_item (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  set_id INT UNSIGNED NOT NULL,
  slot VARCHAR(16) NOT NULL COMMENT 'body head foots wrist weapon neck ear shield ring1 ring2 arrow belt costume_body costume_hair costume_weapon sash mount pendant glove ds1..ds6',
  vnum INT UNSIGNED NOT NULL DEFAULT 0,
  count SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  socket0 INT NOT NULL DEFAULT 0 COMMENT '0 = as the item comes, else the stone vnum (or the raw socket value)',
  socket1 INT NOT NULL DEFAULT 0,
  socket2 INT NOT NULL DEFAULT 0,
  attrtype0 SMALLINT UNSIGNED NOT NULL DEFAULT 0, attrvalue0 SMALLINT NOT NULL DEFAULT 0,
  attrtype1 SMALLINT UNSIGNED NOT NULL DEFAULT 0, attrvalue1 SMALLINT NOT NULL DEFAULT 0,
  attrtype2 SMALLINT UNSIGNED NOT NULL DEFAULT 0, attrvalue2 SMALLINT NOT NULL DEFAULT 0,
  attrtype3 SMALLINT UNSIGNED NOT NULL DEFAULT 0, attrvalue3 SMALLINT NOT NULL DEFAULT 0,
  attrtype4 SMALLINT UNSIGNED NOT NULL DEFAULT 0, attrvalue4 SMALLINT NOT NULL DEFAULT 0,
  attrtype5 SMALLINT UNSIGNED NOT NULL DEFAULT 0, attrvalue5 SMALLINT NOT NULL DEFAULT 0,
  attrtype6 SMALLINT UNSIGNED NOT NULL DEFAULT 0, attrvalue6 SMALLINT NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY set_slot (set_id, slot)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS player.pvpfan_char (
  pid INT UNSIGNED NOT NULL,
  account_id INT UNSIGNED NOT NULL,
  category_id INT UNSIGNED NOT NULL,
  team_id INT UNSIGNED NOT NULL,
  slot_id INT UNSIGNED NOT NULL,
  seq INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'the login number: playerbot_pf%04u',
  name VARCHAR(24) NOT NULL DEFAULT '',
  job TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'the race (player.job) it was made with',
  retired TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1: no longer fights, deleted by the panel once offline 15 min',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (pid),
  UNIQUE KEY seq (seq),
  KEY category (category_id, retired),
  KEY slot (slot_id, retired)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS player.pvpfan_war (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  category_id INT UNSIGNED NOT NULL,
  category_name VARCHAR(64) NOT NULL DEFAULT '',
  started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fight_at DATETIME NULL,
  ended_at DATETIME NULL,
  state VARCHAR(16) NOT NULL DEFAULT 'fighting' COMMENT 'fighting won draw stopped',
  winner_team_id INT UNSIGNED NOT NULL DEFAULT 0,
  winner_name VARCHAR(64) NOT NULL DEFAULT '',
  duration_sec INT UNSIGNED NOT NULL DEFAULT 0,
  fighters INT UNSIGNED NOT NULL DEFAULT 0,
  started_by VARCHAR(48) NOT NULL DEFAULT '',
  summary VARCHAR(512) NOT NULL DEFAULT '',
  PRIMARY KEY (id),
  KEY category (category_id, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS player.pvpfan_war_team (
  war_id INT UNSIGNED NOT NULL,
  team_id INT UNSIGNED NOT NULL,
  idx TINYINT UNSIGNED NOT NULL DEFAULT 0,
  name VARCHAR(32) NOT NULL DEFAULT '',
  fighters SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  survivors SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  kills INT UNSIGNED NOT NULL DEFAULT 0,
  deaths INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (war_id, team_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS player.pvpfan_command (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  category_id INT UNSIGNED NOT NULL,
  cmd VARCHAR(16) NOT NULL COMMENT 'start ready stop',
  source VARCHAR(48) NOT NULL DEFAULT '' COMMENT 'gm:<name> or panel:<user>',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  done TINYINT(1) NOT NULL DEFAULT 0,
  taken_by VARCHAR(32) NOT NULL DEFAULT '',
  taken_at DATETIME NULL,
  result VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY (id),
  KEY pending (done, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS player.pvpfan_gm_pos (
  gm_name VARCHAR(24) NOT NULL,
  map_index INT NOT NULL DEFAULT 0,
  x INT NOT NULL DEFAULT 0,
  y INT NOT NULL DEFAULT 0,
  at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (gm_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Later columns of the first version's tables go here (ADD COLUMN IF NOT EXISTS), never into the CREATEs above only.
ALTER TABLE player.pvpfan_category ADD COLUMN IF NOT EXISTS potions TINYINT(1) NOT NULL DEFAULT 1 AFTER allow_players;
-- MT2009_PLUS_PVPFAN_TACTICS_V1 (the owner, 8 November 2026: "a real war, not two blobs"): squads, roles, kiting and
-- retreats (playerbot_pvpfan.h, "tactics"). Read at each /pvpfan start; a core ahead of this migration fights with
-- these defaults. The event flag m2_pvpfan_tactics_off turns them off for every category.
ALTER TABLE player.pvpfan_category
  ADD COLUMN IF NOT EXISTS tactics TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1: squads, roles, kiting, retreats; 0: the first version''s fight' AFTER potions,
  ADD COLUMN IF NOT EXISTS squad_size TINYINT UNSIGNED NOT NULL DEFAULT 5 COMMENT 'bots per squad, 2..12' AFTER tactics,
  ADD COLUMN IF NOT EXISTS kite_distance SMALLINT UNSIGNED NOT NULL DEFAULT 400 COMMENT 'a ranged/support bot steps away from a melee foe this near (150..900, 0 = never)' AFTER squad_size,
  ADD COLUMN IF NOT EXISTS retreat_hp TINYINT UNSIGNED NOT NULL DEFAULT 35 COMMENT 'HP % under which a bot retreats to mend (5..80, 0 = never)' AFTER kite_distance;
-- MT2009_PLUS_PVPFAN_WARSTYLE_V1 (the owner, 10 November 2026: the squads stuttered - "it must fight like a guild
-- war"): the default fight is the guild war's for every category; the squads are experimental, only with tactics = 2
-- (0 and 1, the old default, both mean the guild war's fight, so no row needs changing). Idempotent at every start.
ALTER TABLE player.pvpfan_category
  MODIFY COLUMN tactics TINYINT(1) NOT NULL DEFAULT 0 COMMENT '2: experimental squads, roles, kiting, retreats; 0/1: the guild war''s fight (default)';

-- A command nobody took within an hour (no core hosts the map on that channel, the core was down) is closed, so the
-- panel's queue shows what is really waiting.
UPDATE player.pvpfan_command SET done = 1, result = 'Nikt nie odebral polecenia (brak rdzenia z mapa areny na tym kanale?)'
 WHERE done = 0 AND created_at < NOW() - INTERVAL 1 HOUR;

-- MT2009_PLUS_PVPFAN_NO_GEAR_OUT_V1 (the owner, 7 November 2026: "nie ma byc nawet najmniejszej szansy, ze ich ekwipunek
-- trafi na rynek serwera"): every start, before the game is up, an arena bot keeps nothing - its items (worn, bag,
-- storages, safebox, shop windows) and its Yang go; a war makes the set anew. The game also clears it at the war's end.
DELETE FROM player.item WHERE owner_id IN (SELECT pid FROM player.pvpfan_char);
UPDATE player.player SET gold = 0 WHERE gold <> 0 AND id IN (SELECT pid FROM player.pvpfan_char);
