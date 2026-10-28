-- MT2009_PLUS_SMH_RANKING_V1: Wieza Sung Mahi's floor ranking (the owner, 28 October 2026; quest wieza_sung_mahi,
-- MT2009_PLUS_SMH_TOWER_V3). Idempotent: CREATE TABLE IF NOT EXISTS only - a second run changes nothing.
--
-- player.wieza_smh_rank: a player's best time on a floor in a season (season = year * 12 + month, Polish time).
--   The quest writes it when the floor's last boss falls: INSERT ... ON DUPLICATE KEY UPDATE keeps the lower time
--   (achieved_at - when that time was set - breaks a tie: the earlier one ranks higher, then the lower pid).
--   The tower window shows the player's place on each floor (one SELECT per window).
-- player.wieza_smh_season: the seasons already paid out. When a season is over, the first hall login (any core,
--   under GET_LOCK('wieza_smh_settle')) gives the first place of every floor Skrzynia Triumfu (50249; floors 10, 20 ...
--   50: 5 x floor/10, the others 1 + floor/10 - the original package's count) into the ItemShop storage
--   (player.item_award, mall = 1, why smh_rank_<season>_<floor> - never twice), then marks the season here.
-- The quest only ever puts numbers into its queries (no player text).
CREATE TABLE IF NOT EXISTS player.wieza_smh_rank (
	season INT UNSIGNED NOT NULL,
	floor TINYINT UNSIGNED NOT NULL,
	pid INT UNSIGNED NOT NULL,
	best_time INT UNSIGNED NOT NULL,
	achieved_at INT UNSIGNED NOT NULL DEFAULT 0,
	PRIMARY KEY (season, floor, pid),
	KEY rank_idx (season, floor, best_time, achieved_at),
	KEY pid_idx (pid, season)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS player.wieza_smh_season (
	season INT UNSIGNED NOT NULL,
	winners INT UNSIGNED NOT NULL DEFAULT 0,
	paid_at DATETIME NOT NULL,
	PRIMARY KEY (season)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
