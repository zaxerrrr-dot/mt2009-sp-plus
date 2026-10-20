"""MT2009_PLUS_DB_LOG_RETENTION_V1: the panel's own summaries of the log
database, and the job that removes old rows from it.

Why both live here
------------------
The advanced panel used to count its "since the server started" figures
(successful refines, the refine-rate ranking, Reaper chests opened, stall
sales, Yang from offline shops, fish caught, the +9 history behind the daily
summary's highlights and the Golden Hammer) straight from the raw log
tables, log.log above all. Deleting old rows would have changed every one of
them. So before anything is deleted, those rows are folded into small
summary tables in the player schema that only ever grow:

    player.web_seban_log_daily    one row per day, metric and character
    player.web_seban_log_refine9  every +9 refine (item id, owner, time, name)
    player.web_seban_gear_event   the equipment history of /player/<id>,
                                  the last GEAR_KEEP_DAYS days

Each source table has a watermark (player.web_seban_settings, name
"logstat_wm:<table>"): the rows below it are already counted. A cycle
counts [watermark, now - 2 minutes) and moves the watermark in the same
transaction, so a crash counts nothing twice. The first cycle counts the
whole history once (the seed).

The prune job deletes rows older than M2_DB_LOG_RETENTION_DAYS full days
(0 = keep everything, the default of an install that existed before this
setting) once a day at PRUNE_HOUR, and never past a watermark: what is
deleted has been counted.

log.log is MyISAM and has no index on `time`. A DELETE ... WHERE time < X
LIMIT n on it reads the table from the start every batch (quadratic on a
100M-row table), so log.log is pruned one of two ways:

* it has an index on `time` (a new install gets one here while the table is
  small, a rotated table has one): batched DELETE through that index;
* it has none and is big: the first prune *rotates* it - an empty copy with
  the index takes its name in one atomic RENAME, the rows of the kept days
  are copied back in batches from the old table, and the old table is
  dropped, which gives its disk space back at once (no OPTIMIZE). The game
  keeps writing into the new table throughout.

Runs in the seban-collector container (collector.py calls run_cycle()), the
stack's periodic job. Pure pymysql, no Flask: app.py imports the read side.

By hand, inside the collector container:
    python log_maintenance.py status
    python log_maintenance.py cycle
    python log_maintenance.py prune --dry-run [--days N]
    python log_maintenance.py prune [--days N]
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta

import pymysql
import pymysql.cursors

RETENTION_ENV = "DB_LOG_RETENTION_DAYS"
PRUNE_HOUR = int(os.environ.get("SEBAN_LOG_PRUNE_HOUR", "5"))
BATCH = 5000
BATCH_SLEEP = float(os.environ.get("SEBAN_LOG_PRUNE_SLEEP", "0.2"))
GEAR_KEEP_DAYS = 60
# log.log gets its `time` index by a plain ALTER while it is this small (a
# new install: seconds). A bigger table is only ever rotated, by the prune.
LOG_INDEX_ALTER_MAX_ROWS = 500_000
# A cycle reads log.log by its `how` index when there is no `time` index:
# every row of those kinds, whatever the window. Hourly then, not every 5 min.
CYCLE_INTERVAL_INDEXED = 300
CYCLE_INTERVAL_UNINDEXED = 3600
LOCK_NAME = "mt2009_log_maintenance"

REAPER_CHEST_VNUM = 50082
MINING_ORE_VNUMS = (50601, 50619)

# The equipment history kinds of /player/<id> (app.py GEAR_HISTORY_HOWS;
# test_log_maintenance.py keeps the two lists equal).
GEAR_HOWS = (
    "REFINE SUCCESS", "REFINE FAIL", "REMOVE (REFINE FAIL)", "REFINE FISH_ROD SUCCESS",
    "REFINE FISH_ROD FAIL", "PLAYERBOT_EQUIP", "PLAYERBOT_GIFT_OUT", "PLAYERBOT_GIFT_IN",
    "PLAYERBOT_STALL_SOLD", "SHOP_BUY", "PLAYERBOT_SHOP_SELL", "PLAYERBOT_BONUS",
    "PLAYERBOT_BONUS_ADD", "PLAYERBOT_BONUS_CHANGE", "PLAYERBOT_BONUS_MARBLE",
    "PLAYERBOT_NPC_BUY", "PLAYERBOT_DUST_MARBLE", "SAFEBOX PUT", "SAFEBOX GET",
    "MOONLIGHT_GET", "EXCHANGE_TAKE", "EXCHANGE_GIVE",
)

# Metrics of web_seban_log_daily. "n" is a count, or a sum where named.
METRICS = {
    "stone": "Metiny zniszczone (STONE_KILL)",
    "boss": "Bossowie zabici (BOSS_KILL)",
    "refine_ok": "Udane ulepszenia (REFINE SUCCESS)",
    "refine_burn": "Spalone przy ulepszaniu (REMOVE (REFINE FAIL))",
    "refine7": "Udane ulepszenia na +7/+8/+9",
    "refine9": "Udane ulepszenia na +9",
    "stall_sold": "Sprzedaże na straganach botów (PLAYERBOT_STALL_SOLD)",
    "pvp_kill": "Zabójstwa graczy (DEAD_BY_PC, zabójca)",
    "reaper_chest": "Otwarte Szkatułki Umarłego Rozpruwacza",
    "fish": "Złowione ryby (suma fish_log.count)",
    "mining": "Wydobyta ruda (suma money_log.gold, cały świat)",
    "shop_yang": "Yang ze sprzedaży w sklepach offline (po podatku)",
}

# The source tables a cycle reads, each with its own watermark.
SOURCES = ("log", "fish_log", "money_log", "ikarusshop_log")

# Growing log tables the prune empties of old rows: (table, time column).
# Not here on purpose: levellog (one row per character and level, the daily
# summary's level history), itemshop* and voucher/command logs (purchases
# and GM actions an owner may need to look up), playerbot_listing (the live
# state of the bots' shop counters), playerbot_session (open sessions),
# change_name, okay_event and every other table that is state, not a feed.
PRUNE_TABLES = (
    ("log", "time"),
    ("item_meta_log", "time"),
    ("money_log", "time"),
    ("fish_log", "time"),
    ("ikarusshop_log", "time"),
    ("refinelog", "time"),
    ("loginlog", "time"),
    ("request_info_log", "time"),
    ("gold_session_log", "time"),
    ("quest_reward_log", "time"),
    ("quest_state_log", "time"),
    ("playerbot_equip", "time"),
    ("chat_log", "when"),
    ("exchange_log", "time"),
    ("cube", "time"),
    ("acce", "time"),
    ("hack_log", "time"),
    ("speed_hack", "time"),
)
# The prune never deletes past these watermarks (table -> source).
PRUNE_NEEDS = {"log": "log", "fish_log": "fish_log", "money_log": "money_log",
               "ikarusshop_log": "ikarusshop_log"}


def _say(message):
    print(f"[log-maintenance] {message}", flush=True)


def connect():
    con = pymysql.connect(
        host=os.environ.get("DB_HOST", "mariadb"), port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
        charset="utf8mb4", autocommit=True)
    with con.cursor() as cur:
        # This is the background job: no panel statement limit here.
        cur.execute("SET SESSION max_statement_time=0")
    return con


def retention_days(value=None):
    """M2_DB_LOG_RETENTION_DAYS: 0 keeps everything, 1-365 days."""
    raw = os.environ.get(RETENTION_ENV, "0") if value is None else value
    try:
        days = int(str(raw).strip() or "0")
    except ValueError:
        return 0
    return days if 0 < days <= 365 else 0


def ensure_tables(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_settings (
      name VARCHAR(64) NOT NULL PRIMARY KEY, value VARCHAR(255) NOT NULL,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP) ENGINE=InnoDB""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_log_daily (
      day DATE NOT NULL, metric VARCHAR(24) NOT NULL, pid INT UNSIGNED NOT NULL DEFAULT 0,
      n BIGINT NOT NULL DEFAULT 0,
      PRIMARY KEY (day, metric, pid), KEY metric_pid (metric, pid, day)) ENGINE=InnoDB""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_log_refine9 (
      item_id BIGINT UNSIGNED NOT NULL, pid INT UNSIGNED NOT NULL, time DATETIME NOT NULL,
      hint VARBINARY(500) NOT NULL DEFAULT '',
      PRIMARY KEY (item_id, pid, time), KEY time_idx (time), KEY pid_idx (pid)) ENGINE=InnoDB""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_gear_event (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      pid INT UNSIGNED NOT NULL, time DATETIME NOT NULL, how VARBINARY(50) NOT NULL,
      hint VARBINARY(500) DEFAULT NULL, vnum INT UNSIGNED NOT NULL DEFAULT 0,
      what BIGINT UNSIGNED NOT NULL DEFAULT 0,
      KEY pid_time (pid, time), KEY time_idx (time)) ENGINE=InnoDB""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_log_prune (
      id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      started_at DATETIME NOT NULL, finished_at DATETIME DEFAULT NULL,
      retention_days INT NOT NULL, cutoff DATETIME NOT NULL, dry_run TINYINT NOT NULL DEFAULT 0,
      status VARCHAR(16) NOT NULL, deleted BIGINT NOT NULL DEFAULT 0, detail TEXT) ENGINE=InnoDB""")


# ---------------------------------------------------------------- helpers
def get_setting(cur, name):
    cur.execute("SELECT value FROM player.web_seban_settings WHERE name=%s", (name,))
    row = cur.fetchone()
    return row[0] if row else None


def set_setting(cur, name, value):
    cur.execute("REPLACE INTO player.web_seban_settings (name,value) VALUES (%s,%s)", (name, str(value)[:255]))


def watermark(cur, source):
    value = get_setting(cur, f"logstat_wm:{source}")
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def table_exists(cur, schema, table):
    cur.execute("SELECT engine, table_rows FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
                (schema, table))
    return cur.fetchone()


def column_exists(cur, schema, table, column):
    cur.execute("SELECT 1 FROM information_schema.columns WHERE table_schema=%s AND table_name=%s AND column_name=%s",
                (schema, table, column))
    return cur.fetchone() is not None


def time_indexed(cur, schema, table, column="time"):
    """True when an index of the table starts with `column`."""
    cur.execute("""SELECT 1 FROM information_schema.statistics
      WHERE table_schema=%s AND table_name=%s AND column_name=%s AND seq_in_index=1 LIMIT 1""",
                (schema, table, column))
    return cur.fetchone() is not None


def single_int_pk(cur, schema, table):
    cur.execute("""SELECT GROUP_CONCAT(column_name) FROM information_schema.statistics
      WHERE table_schema=%s AND table_name=%s AND index_name='PRIMARY'""", (schema, table))
    row = cur.fetchone()
    columns = (row[0] or "").split(",") if row and row[0] else []
    return columns[0] if len(columns) == 1 else None


def db_now(cur):
    cur.execute("SELECT NOW()")
    return cur.fetchone()[0]


def _ts(value):
    return value.strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------- the counts
def _add_daily(cur, counts):
    """counts: {(day, metric, pid): n} added onto what is there."""
    if not counts:
        return
    items = [(day, metric, int(pid or 0), int(n)) for (day, metric, pid), n in counts.items() if n]
    for start in range(0, len(items), 1000):
        cur.executemany("""INSERT INTO player.web_seban_log_daily (day,metric,pid,n) VALUES (%s,%s,%s,%s)
          ON DUPLICATE KEY UPDATE n=n+VALUES(n)""", items[start:start + 1000])


def _bump(counts, day, metric, pid, n):
    key = (day, metric, int(pid or 0))
    counts[key] = counts.get(key, 0) + int(n or 0)


def _fold_log(cur, lo, hi):
    """log.log [lo, hi) into the summaries. Returns the number of rows read."""
    counts, read = {}, 0
    cur.execute("""SELECT DATE(time), how, who, hint LIKE '%%+9', (hint LIKE '%%+7' OR hint LIKE '%%+8' OR hint LIKE '%%+9'), COUNT(*)
      FROM log.log WHERE how IN ('STONE_KILL','BOSS_KILL','REFINE SUCCESS','REMOVE (REFINE FAIL)','PLAYERBOT_STALL_SOLD')
        AND time >= %s AND time < %s GROUP BY 1,2,3,4,5""", (lo, hi))
    names = {b"STONE_KILL": "stone", b"BOSS_KILL": "boss", b"REFINE SUCCESS": "refine_ok",
             b"REMOVE (REFINE FAIL)": "refine_burn", b"PLAYERBOT_STALL_SOLD": "stall_sold"}
    for day, how, who, is9, is7, n in cur.fetchall():
        how = how if isinstance(how, bytes) else str(how).encode()
        metric = names.get(how)
        if not metric or day is None:
            continue
        read += int(n)
        _bump(counts, day, metric, who, n)
        if metric == "refine_ok":
            if is7:
                _bump(counts, day, "refine7", who, n)
            if is9:
                _bump(counts, day, "refine9", who, n)
    # The killer is the last word of the hint; resolved to a character now.
    cur.execute("""SELECT DATE(l.time), p.id, COUNT(*) FROM log.log l
      JOIN player.player p ON p.name=SUBSTRING_INDEX(CONVERT(l.hint USING latin1),' ',-1)
      WHERE l.how='DEAD_BY_PC' AND l.time >= %s AND l.time < %s GROUP BY 1,2""", (lo, hi))
    for day, pid, n in cur.fetchall():
        if day is not None:
            _bump(counts, day, "pvp_kill", pid, n)
    # One chest opening writes USE_ITEM and CHEST_OPEN in the same second.
    cur.execute("""SELECT DATE(time), who, COUNT(DISTINCT CONCAT(who, ':', UNIX_TIMESTAMP(time))) FROM log.log
      WHERE what=%s AND how IN ('USE_ITEM','CHEST_OPEN') AND time >= %s AND time < %s GROUP BY 1,2""",
                (REAPER_CHEST_VNUM, lo, hi))
    for day, who, n in cur.fetchall():
        if day is not None:
            _bump(counts, day, "reaper_chest", who, n)
    _add_daily(cur, counts)
    cur.execute("""INSERT IGNORE INTO player.web_seban_log_refine9 (item_id,pid,time,hint)
      SELECT COALESCE(what,0), COALESCE(who,0), time, COALESCE(hint,'') FROM log.log
      WHERE how='REFINE SUCCESS' AND hint LIKE '%%+9' AND time >= %s AND time < %s""", (lo, hi))
    gear_lo = max(lo, hi - timedelta(days=GEAR_KEEP_DAYS))
    if gear_lo < hi:
        marks = ",".join(["%s"] * len(GEAR_HOWS))
        cur.execute(f"""INSERT INTO player.web_seban_gear_event (pid,time,how,hint,vnum,what)
          SELECT who, time, how, hint, COALESCE(vnum,0), COALESCE(what,0) FROM log.log
          WHERE how IN ({marks}) AND who IS NOT NULL AND time >= %s AND time < %s""",
                    list(GEAR_HOWS) + [gear_lo, hi])
    return read


def _fold_fish(cur, lo, hi):
    cur.execute("""SELECT DATE(time), player_id, SUM(count) FROM log.fish_log
      WHERE time >= %s AND time < %s GROUP BY 1,2""", (lo, hi))
    counts = {}
    for day, pid, n in cur.fetchall():
        if day is not None:
            _bump(counts, day, "fish", pid, n)
    _add_daily(cur, counts)
    return sum(counts.values())


def _fold_money(cur, lo, hi):
    cur.execute("""SELECT DATE(time), SUM(gold) FROM log.money_log
      WHERE type='DROP' AND vnum BETWEEN %s AND %s AND time >= %s AND time < %s GROUP BY 1""",
                (MINING_ORE_VNUMS[0], MINING_ORE_VNUMS[1], lo, hi))
    counts = {}
    for day, n in cur.fetchall():
        if day is not None:
            _bump(counts, day, "mining", 0, n)
    _add_daily(cur, counts)
    return sum(counts.values())


def _fold_ikarus(cur, lo, hi):
    cur.execute("""SELECT DATE(time), shop_owner,
        SUM(GREATEST(0,yang-IF(extra LIKE 'TAX: %%',CAST(SUBSTRING_INDEX(extra,' ',-1) AS UNSIGNED),0)))
      FROM log.ikarusshop_log WHERE what='BUY_ITEM' AND time >= %s AND time < %s GROUP BY 1,2""", (lo, hi))
    counts = {}
    for day, pid, n in cur.fetchall():
        if day is not None:
            _bump(counts, day, "shop_yang", pid, n)
    _add_daily(cur, counts)
    return len(counts)


FOLDERS = {"log": _fold_log, "fish_log": _fold_fish, "money_log": _fold_money, "ikarusshop_log": _fold_ikarus}


def fold_source(con, source, hi):
    """Count [watermark, hi) of one source and move its watermark, atomically
    (the summaries are InnoDB). Returns (lo, hi) or None when the table is
    missing or already counted."""
    with con.cursor() as cur:
        if not table_exists(cur, "log", source):
            return None
        lo = watermark(cur, source) or datetime(1970, 1, 1)
    if lo >= hi:
        return None
    con.begin()
    try:
        with con.cursor() as cur:
            FOLDERS[source](cur, lo, hi)
            set_setting(cur, f"logstat_wm:{source}", _ts(hi))
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.autocommit(True)
    return lo, hi


def fold_all(con, hi=None):
    with con.cursor() as cur:
        ensure_tables(cur)
        hi = hi or (db_now(cur) - timedelta(minutes=2)).replace(microsecond=0)
    done = {}
    for source in SOURCES:
        started = time.monotonic()
        span = fold_source(con, source, hi)
        if span:
            done[source] = round(time.monotonic() - started, 2)
            if span[0].year == 1970:
                _say(f"{source}: the whole history counted once (seed), {done[source]} s")
    return hi, done


def ensure_small_log_index(con):
    """A new install's log.log gets its `time` index while it is small."""
    with con.cursor() as cur:
        found = table_exists(cur, "log", "log")
        if not found or time_indexed(cur, "log", "log"):
            return False
        cur.execute("SELECT COUNT(*) FROM log.log")  # MyISAM: exact and instant
        count = int(cur.fetchone()[0])
        if count > LOG_INDEX_ALTER_MAX_ROWS:
            return False
        cur.execute("SET SESSION lock_wait_timeout=5")
        try:
            cur.execute("ALTER TABLE log.log ADD INDEX time_idx (`time`)")
            _say(f"log.log: index on time added ({count} rows)")
            return True
        except pymysql.MySQLError as exc:
            _say(f"log.log: index on time not added now: {exc}")
            return False
        finally:
            cur.execute("SET SESSION lock_wait_timeout=DEFAULT")


# ---------------------------------------------------------------- the prune
def cutoff_for(now, days):
    """Keep `days` full days before today: midnight of today - days."""
    return datetime.combine(now.date(), datetime.min.time()) - timedelta(days=days)


def _record(cur, started, days, cutoff, dry_run, status, deleted, detail):
    cur.execute("""INSERT INTO player.web_seban_log_prune
      (started_at,finished_at,retention_days,cutoff,dry_run,status,deleted,detail)
      VALUES (%s,NOW(),%s,%s,%s,%s,%s,%s)""",
                (started, days, cutoff, 1 if dry_run else 0, status, deleted, json.dumps(detail, default=str)))
    set_setting(cur, "log_prune_last", json.dumps({
        "at": _ts(datetime.now()), "days": days, "cutoff": _ts(cutoff), "dry_run": bool(dry_run),
        "status": status, "deleted": deleted}, default=str))


def _delete_indexed(cur, table, column, cutoff, say):
    total = 0
    while True:
        cur.execute(f"DELETE FROM log.`{table}` WHERE `{column}` < %s LIMIT {BATCH}", (cutoff,))
        total += cur.rowcount
        if cur.rowcount < BATCH:
            return total
        time.sleep(BATCH_SLEEP)


def _delete_front(cur, table, column, cutoff, pk):
    """No index on the time column. Old rows are at the front of the table
    (an InnoDB clustered index or an auto-increment key keeps the order of
    writing), so each batch first counts the old rows among the first BATCH
    rows and deletes exactly that many - the DELETE then stops near the
    front instead of reading the whole table for a LIMIT it cannot fill."""
    order = f" ORDER BY `{pk}`" if pk else ""
    total = 0
    while True:
        # SELECT *: a covering secondary index (refinelog's (pid, time))
        # would otherwise be read instead, in its own order, not the table's.
        cur.execute(f"SELECT COUNT(*) FROM (SELECT * FROM log.`{table}`{order} LIMIT {BATCH}) s WHERE s.`{column}` < %s",
                    (cutoff,))
        found = int(cur.fetchone()[0])
        if not found:
            return total
        cur.execute(f"DELETE FROM log.`{table}` WHERE `{column}` < %s{order} LIMIT {found}", (cutoff,))
        total += cur.rowcount
        if found < BATCH or cur.rowcount == 0:
            return total
        time.sleep(BATCH_SLEEP)


def _log_columns(cur):
    cur.execute("""SELECT column_name FROM information_schema.columns
      WHERE table_schema='log' AND table_name='log' ORDER BY ordinal_position""")
    return [row[0] for row in cur.fetchall()]


def _copy_rows(con, source_sql, params, columns, skip_present=False):
    """Stream rows of log.log_prune_old into log.log in batches."""
    reader = pymysql.connect(
        host=os.environ.get("DB_HOST", "mariadb"), port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"], charset="utf8mb4",
        autocommit=True, cursorclass=pymysql.cursors.SSCursor)
    names = ",".join(f"`{c}`" for c in columns)
    insert = f"INSERT INTO log.log ({names}) VALUES ({','.join(['%s'] * len(columns))})"
    present = " AND ".join(f"`{c}` <=> %s" for c in columns)
    copied = 0
    try:
        with reader.cursor() as rcur:
            rcur.execute("SET SESSION max_statement_time=0")
            rcur.execute(source_sql, params)
            with con.cursor() as wcur:
                batch = []
                for row in rcur:
                    if skip_present:
                        wcur.execute(f"SELECT 1 FROM log.log WHERE {present} LIMIT 1", row)
                        if wcur.fetchone():
                            continue
                    batch.append(row)
                    if len(batch) >= BATCH:
                        wcur.executemany(insert, batch)
                        copied += len(batch)
                        batch = []
                        time.sleep(0.02)
                if batch:
                    wcur.executemany(insert, batch)
                    copied += len(batch)
    finally:
        reader.close()
    return copied


def _rotate_log(con, cutoff, say):
    """See the module docstring. Resumable: the state is kept in
    web_seban_settings 'log_rotate_state' until the old table is dropped."""
    with con.cursor() as cur:
        state = json.loads(get_setting(cur, "log_rotate_state") or "{}")
        old_exists = table_exists(cur, "log", "log_prune_old")
        if old_exists and state.get("swap_at"):
            swap_at = datetime.strptime(state["swap_at"], "%Y-%m-%d %H:%M:%S")
            cutoff = datetime.strptime(state["cutoff"], "%Y-%m-%d %H:%M:%S")
            say(f"log.log: resuming the copy of an interrupted rotation (swap {state['swap_at']})")
            # The rows copied before the stop are all older than the swap:
            # take them out and copy again; rows at/after the swap may be the
            # game's own, so those are copied only when not there yet.
            cur.execute("SET SESSION max_statement_time=0")
            _delete_indexed(cur, "log", "time", swap_at, say)
            resume = True
        elif old_exists:
            raise RuntimeError("log.log_prune_old exists without a rotation state - check it by hand")
        else:
            cur.execute("DROP TABLE IF EXISTS log.log_prune_new")
            cur.execute("CREATE TABLE log.log_prune_new LIKE log.log")
            cur.execute("ALTER TABLE log.log_prune_new ADD INDEX time_idx (`time`)")
            cur.execute("SET SESSION lock_wait_timeout=10")
            try:
                # Atomic: the game's next INSERT INTO log lands in the new table.
                cur.execute("RENAME TABLE log.log TO log.log_prune_old, log.log_prune_new TO log.log")
            finally:
                cur.execute("SET SESSION lock_wait_timeout=DEFAULT")
            swap_at = db_now(cur).replace(microsecond=0)
            set_setting(cur, "log_rotate_state", json.dumps({"swap_at": _ts(swap_at), "cutoff": _ts(cutoff)}))
            say(f"log.log: rotated at {_ts(swap_at)}; copying the rows since {_ts(cutoff)} back")
            resume = False
        columns = _log_columns(cur)
    names = ",".join(f"`{c}`" for c in columns)
    copied = _copy_rows(con, f"SELECT {names} FROM log.log_prune_old WHERE `time` >= %s AND `time` < %s",
                        (cutoff, swap_at), columns)
    copied += _copy_rows(con, f"SELECT {names} FROM log.log_prune_old WHERE `time` >= %s",
                         (swap_at,), columns, skip_present=resume)
    with con.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM log.log_prune_old")
        old_rows = int(cur.fetchone()[0])
        cur.execute("DROP TABLE log.log_prune_old")
        cur.execute("DELETE FROM player.web_seban_settings WHERE name='log_rotate_state'")
    say(f"log.log: {copied} rows kept, {old_rows - copied} removed; the old table dropped (disk space returned)")
    return max(0, old_rows - copied)


def _prune_log_log(con, cutoff, dry_run, say):
    with con.cursor() as cur:
        info = table_exists(cur, "log", "log")
        if not info:
            return 0, "missing"
        if table_exists(cur, "log", "log_prune_old"):
            if dry_run:
                return 0, "an interrupted rotation waits to be resumed"
            return _rotate_log(con, cutoff, say), "rotation resumed"
        if not dry_run and not time_indexed(cur, "log", "log"):
            ensure_small_log_index(con)
        if time_indexed(cur, "log", "log"):
            if dry_run:
                cur.execute("SELECT COUNT(*) FROM log.log WHERE `time` < %s", (cutoff,))
                return int(cur.fetchone()[0]), "indexed delete (dry run)"
            return _delete_indexed(cur, "log", "time", cutoff, say), "indexed delete"
        if dry_run:
            cur.execute("SELECT COUNT(*) FROM log.log WHERE `time` < %s", (cutoff,))
            return int(cur.fetchone()[0]), "rotation (dry run)"
    return _rotate_log(con, cutoff, say), "rotation"


def prune(con, days=None, dry_run=False, now=None, say=_say):
    """Delete rows older than `days` full days. Returns the result dict."""
    days = retention_days() if days is None else int(days)
    with con.cursor() as cur:
        ensure_tables(cur)
        cur.execute("SET SESSION max_statement_time=0")
        started = db_now(cur)
    now = now or started
    if days <= 0:
        return {"status": "off", "deleted": 0, "tables": {}}
    cutoff = cutoff_for(now, days)
    with con.cursor() as cur:
        cur.execute("SELECT GET_LOCK(%s, 0)", (LOCK_NAME + "_prune",))
        if cur.fetchone()[0] != 1:
            return {"status": "busy", "deleted": 0, "tables": {}}
    detail, deleted, status = {"tables": {}, "skipped": {}}, 0, "ok"
    try:
        # Everything about to go is counted first.
        fold_all(con)
        with con.cursor() as cur:
            marks = {source: watermark(cur, source) for source in SOURCES}
        for table, column in PRUNE_TABLES:
            with con.cursor() as cur:
                info = table_exists(cur, "log", table)
                if not info or not column_exists(cur, "log", table, column):
                    continue
                needed = PRUNE_NEEDS.get(table)
                if needed and (marks.get(needed) is None or marks[needed] < cutoff):
                    detail["skipped"][table] = "not counted up to the cutoff yet"
                    status = "partial"
                    continue
            started_table = time.monotonic()
            try:
                if table == "log":
                    count, how = _prune_log_log(con, cutoff, dry_run, say)
                else:
                    with con.cursor() as cur:
                        engine, rows_estimate = info[0], int(info[1] or 0)
                        if dry_run:
                            cur.execute(f"SELECT COUNT(*) FROM log.`{table}` WHERE `{column}` < %s", (cutoff,))
                            count, how = int(cur.fetchone()[0]), "dry run"
                        elif time_indexed(cur, "log", table, column):
                            count, how = _delete_indexed(cur, table, column, cutoff, say), "indexed delete"
                        elif engine == "InnoDB" or rows_estimate <= 1_000_000:
                            pk = single_int_pk(cur, "log", table)
                            count, how = _delete_front(cur, table, column, cutoff, pk), "front delete"
                        else:
                            detail["skipped"][table] = "big table without a time index"
                            status = "partial"
                            continue
            except pymysql.MySQLError as exc:
                detail["skipped"][table] = f"error {exc.args[0] if exc.args else ''}: {exc}"
                status = "partial"
                say(f"{table}: {exc}")
                continue
            detail["tables"][table] = {"deleted": count, "how": how,
                                       "seconds": round(time.monotonic() - started_table, 1)}
            deleted += count
            if count:
                say(f"{table}: {'would delete' if dry_run else 'deleted'} {count} rows older than {_ts(cutoff)} ({how})")
        if not dry_run:
            with con.cursor() as cur:
                cur.execute("DELETE FROM player.web_seban_gear_event WHERE time < %s LIMIT 100000",
                            (started - timedelta(days=GEAR_KEEP_DAYS),))
    except Exception as exc:
        status = "error"
        detail["error"] = str(exc)
        say(f"prune stopped: {exc}")
    finally:
        with con.cursor() as cur:
            _record(cur, started, days, cutoff, dry_run, status, deleted, detail)
            cur.execute("SELECT RELEASE_LOCK(%s)", (LOCK_NAME + "_prune",))
    return {"status": status, "deleted": deleted, "cutoff": cutoff, **detail}


# ---------------------------------------------------------------- the cycle
def run_cycle(con, now=None, say=_say):
    """Called by collector.py every round. Counts new rows (every 5 min, or
    hourly while log.log has no time index), adds the index to a small
    log.log, and prunes once a day at PRUNE_HOUR when retention is on."""
    now = now or datetime.now()
    with con.cursor() as cur:
        ensure_tables(cur)
        cur.execute("SET SESSION max_statement_time=0")
        cur.execute("SELECT GET_LOCK(%s, 0)", (LOCK_NAME,))
        if cur.fetchone()[0] != 1:
            return None
    result = {}
    try:
        ensure_small_log_index(con)
        with con.cursor() as cur:
            indexed = bool(table_exists(cur, "log", "log")) and time_indexed(cur, "log", "log")
            last = float(get_setting(cur, "logstat_cycle_at") or 0)
        interval = CYCLE_INTERVAL_INDEXED if indexed else CYCLE_INTERVAL_UNINDEXED
        if time.time() - last >= interval - 5:
            _hi, done = fold_all(con)
            with con.cursor() as cur:
                set_setting(cur, "logstat_cycle_at", time.time())
            result["folded"] = done
        days = retention_days()
        with con.cursor() as cur:
            last_prune = get_setting(cur, "log_prune_day") or ""
        if days and now.hour == PRUNE_HOUR and last_prune != now.date().isoformat():
            with con.cursor() as cur:
                set_setting(cur, "log_prune_day", now.date().isoformat())
            result["prune"] = prune(con, days, say=say)
    finally:
        with con.cursor() as cur:
            cur.execute("SELECT RELEASE_LOCK(%s)", (LOCK_NAME,))
    return result


# ---------------------------------------------------------------- reading
def status(con):
    """What the panel's "Logi bazy danych" page shows."""
    with con.cursor(pymysql.cursors.DictCursor) as cur:
        ensure_tables(cur)
        cur.execute("""SELECT table_name AS name, engine, table_rows AS row_estimate,
            ROUND((data_length+index_length)/1048576) AS size_mb, ROUND(data_free/1048576) AS free_mb
          FROM information_schema.tables WHERE table_schema='log' ORDER BY data_length+index_length DESC""")
        tables = cur.fetchall()
        cur.execute("SELECT * FROM player.web_seban_log_prune ORDER BY id DESC LIMIT 10")
        runs = cur.fetchall()
        cur.execute("SELECT name, value FROM player.web_seban_settings WHERE name LIKE 'logstat_wm:%%' OR name IN ('log_rotate_state','logstat_cycle_at')")
        settings = {row["name"]: row["value"] for row in cur.fetchall()}
    with con.cursor() as cur:
        indexed = bool(table_exists(cur, "log", "log")) and time_indexed(cur, "log", "log")
    for run in runs:
        try:
            run["detail"] = json.loads(run.get("detail") or "{}")
        except ValueError:
            run["detail"] = {}
    return {"tables": tables, "runs": runs, "indexed": indexed,
            "watermarks": {source: settings.get(f"logstat_wm:{source}") for source in SOURCES},
            "rotation_pending": bool(settings.get("log_rotate_state")),
            "cycle_at": settings.get("logstat_cycle_at")}


def totals(con):
    """All-time totals of every metric: the check that a prune changed nothing."""
    with con.cursor() as cur:
        cur.execute("SELECT metric, SUM(n) FROM player.web_seban_log_daily GROUP BY metric ORDER BY metric")
        result = {metric: int(n) for metric, n in cur.fetchall()}
        cur.execute("SELECT COUNT(*) FROM player.web_seban_log_refine9")
        result["refine9_items"] = int(cur.fetchone()[0])
    return result


def main(argv):
    import argparse
    parser = argparse.ArgumentParser(description="Summaries and retention of the log database")
    parser.add_argument("command", choices=("status", "cycle", "prune", "totals"))
    parser.add_argument("--days", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    con = connect()
    try:
        if args.command == "status":
            print(json.dumps(status(con), default=str, indent=1))
        elif args.command == "totals":
            fold_all(con)
            print(json.dumps(totals(con), indent=1))
        elif args.command == "cycle":
            with con.cursor() as cur:
                set_setting(cur, "logstat_cycle_at", 0)
            print(json.dumps(run_cycle(con, now=datetime(2000, 1, 1)), default=str, indent=1))
        else:
            print(json.dumps(prune(con, args.days, dry_run=args.dry_run), default=str, indent=1))
    finally:
        con.close()


if __name__ == "__main__":
    main(sys.argv[1:])
