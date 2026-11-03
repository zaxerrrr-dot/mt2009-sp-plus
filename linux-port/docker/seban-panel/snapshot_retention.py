"""MT2009_PLUS_SEBAN_SNAPSHOT_RETENTION_V1: how long the advanced panel keeps
its own monitoring history, and the job that thins and removes the rest.

Why
---
collector.py writes a snapshot every 5 minutes (SEBAN_COLLECTOR_INTERVAL) -
the amount of every item in the world (~4 700 rows), every bot's position
(~1 000), every item on offer in the stalls (~1 600), the map and metric
counters - and nothing ever removed any of it. After one month on the Yohara
test server (3 November 2026): web_seban_item_snapshot 35.6M rows / 2.0 GB,
web_seban_bot_position_snapshot 17M / 1.5 GB, web_seban_shop_item_snapshot
16.7M / 1.2 GB, web_seban_gear_event 5M / 0.9 GB - most of the player
database, and the panel's GROUP BY queries over them got slower each day.

What the pages read (app.py, item_grants.py), and so what is kept
-----------------------------------------------------------------
web_seban_item_snapshot           /economy: the newest snapshot; /economy/item:
                                  one item over 14 days.
                                  -> full KEEP_FULL_DAYS, one an hour up to
                                     KEEP_HOURLY_DAYS, then deleted.
web_seban_shop_item_snapshot      /economy/shops: the newest snapshot, 24 h
                                  baseline, an item's last offer ever ("was it
                                  ever on the market", last seen), the skill
                                  book variants ever offered.
                                  -> full, hourly, then one a day up to
                                     KEEP_HISTORY_DAYS (an item's last row of
                                     each day survives, so "last seen" stays
                                     right to the day).
web_seban_bot_position_snapshot   dashboard "stuck" check (the last position
                                  5-120 min ago); /player: an offline bot's last
                                  channel; item_grants: who is online now.
                                  -> full, then each bot's last position of a
                                     day up to POSITIONS_HISTORY_DAYS.
web_seban_map_snapshot            /maps: 24 h chart.  -> full, hourly, deleted.
web_seban_metric_snapshot         /economy 7-day Yang trend, level brackets 7
                                  days, the daily summary's start/end of a day.
web_seban_shop_snapshot           /economy/shops 7-day trend, the newest one.
                                  -> both: full for at least SMALL_FULL_DAYS (8,
                                     they are small), hourly, then daily.
web_seban_news_event              ticker 12 h, /world-feed 14 days, live chat's
                                  newest announcements. -> KEEP_NEWS_DAYS.
web_seban_gear_event              /player/<id> "historia ekwipunku": a
                                  character's newest 60 rows. -> the newest
                                  GEAR_PER_CHARACTER rows of each character,
                                  and nothing older than
                                  log_maintenance.GEAR_KEEP_DAYS.
Not touched: web_seban_system_snapshot (288 small rows a day; its oldest row
is "day 1" of the daily summary's day numbering), web_seban_log_daily and
web_seban_log_refine9 (the "since the server started" summaries, they must
only ever grow), web_seban_daily_summary, event runs, notifications.

Thinning keeps, for every key (item, bot, map, metric...) of a bucket (an
hour, a day), its *last* row in that bucket - not the bucket's first
snapshot - so an item offered only at 15:00 of a day still shows as seen
that day, and a day's last metric value is still the one before midnight.

How it deletes
--------------
Every time column here leads the primary key or has its own index (checked
each run; a missing one is added online with ALGORITHM=INPLACE, LOCK=NONE
and a 5 s lock wait, or the table is skipped this round). It runs in its own
thread of the collector, never delaying the snapshots.

MT2009_PLUS_SEBAN_SNAPSHOT_GENTLE_V1 (3 November 2026): the first version
deleted 20 000 rows a statement with 0.1 s between them. On the Yohara test
server (a 128 MB InnoDB buffer pool, 6 GB of tables) one such DELETE of
web_seban_item_snapshot took ~16 s - EXPLAIN: a range on the PRIMARY key,
so not a bad plan, just 20 000 rows of random reads and two index trees to
update - and the db core's answer to a login (InputDB::login_success) came
16 s late behind it; players hung on the login and character screens. So:

* Throttle: a statement deletes `batch` rows (start BATCH, between
  BATCH_MIN and BATCH_MAX), and the batch follows the measured time - shrunk
  when a statement takes longer than TARGET_SECONDS, grown when it takes
  less than half - and after every statement the job sleeps SLEEP_FACTOR
  times what the statement took (at least BATCH_SLEEP). The database gets
  the larger share of every second.
* Busy: before each statement SHOW GLOBAL STATUS: with more than
  BUSY_THREADS statements running at once, or more than HISTORY_MAX undo
  records waiting for purge (a big delete's own after-effect), it waits
  BUSY_PAUSE s and looks again.
* Night: the backlog - a table whose oldest row lies more than BACKLOG_SLACK
  beyond its cutoff, or whose thinning watermark is that far behind - is
  only worked on inside the heavy hours (M2_SEBAN_SNAPSHOT_HEAVY_HOURS,
  "3-6" = 03:00-06:00 database time). In the day a run only does the
  hourly tail, at most DAY_BUDGET seconds of it; the equipment history's
  per-character cap (a GROUP BY over the whole table) is night-only too.
  At night a run goes on until the window closes, the next one starts
  NIGHT_RERUN s later while backlog remains.
* Deletes walk forward: "column >= last position AND column < cutoff LIMIT
  n", the position moved after every batch, so a statement never re-reads
  the rows the previous ones deleted (until purge removes them they are
  still in the index); READ COMMITTED and a 5 s lock wait for the session. A named lock (GET_LOCK) keeps
two runs - the thread and a manual one - from overlapping. Thinning keeps a
watermark per table and grain in web_seban_settings ("snapret:<table>:hour"
/ ":day"), so a run only looks at the buckets that became old since.

InnoDB does not give disk space back after a DELETE: the files stop growing
and the freed pages are reused. To shrink them once after the first cleanup,
by hand at a quiet hour: OPTIMIZE TABLE player.web_seban_item_snapshot (and
the other three big ones) - it rebuilds the table online but needs free disk
space of the table's new size.

Settings (.env, the panel's "Ustawienia serwera" -> Baza danych):
    M2_SEBAN_KEEP_FULL_DAYS       2    (0 = this whole job off, keep everything)
    M2_SEBAN_KEEP_HOURLY_DAYS     14
    M2_SEBAN_KEEP_HISTORY_DAYS    180  (0 = the daily rows are never deleted)
    M2_SEBAN_KEEP_NEWS_DAYS       30   (0 = keep all)
    M2_SEBAN_GEAR_PER_CHARACTER   300  (0 = no per-character limit)
    M2_SEBAN_SNAPSHOT_HEAVY_HOURS 3-6  (the backlog's hours, database time;
                                        "0-24" always, "0-0" only by hand)

By hand, inside the collector container:
    python snapshot_retention.py plan      the cutoffs and what is beyond them
    python snapshot_retention.py run       one run now, as the thread would do it
    python snapshot_retention.py run --heavy   the backlog too, whatever the hour
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta

import log_maintenance

LOCK_NAME = "mt2009_snapshot_retention"
# MT2009_PLUS_SEBAN_SNAPSHOT_GENTLE_V1: the throttle (see "How it deletes").
BATCH = 1000
BATCH_MIN = 100
BATCH_MAX = 2000
TARGET_SECONDS = 0.2
SLEEP_FACTOR = 3.0
BATCH_SLEEP = float(os.environ.get("SEBAN_SNAPSHOT_PRUNE_SLEEP", "0.05"))
BUSY_THREADS = int(os.environ.get("SEBAN_SNAPSHOT_BUSY_THREADS", "8"))
HISTORY_MAX = int(os.environ.get("SEBAN_SNAPSHOT_HISTORY_MAX", "300000"))
BUSY_PAUSE = 5.0
SLOW_SECONDS = 1.0
ENV_HEAVY_HOURS = "SEBAN_SNAPSHOT_HEAVY_HOURS"
DEFAULT_HEAVY_HOURS = (3, 6)
DAY_BUDGET = int(os.environ.get("SEBAN_SNAPSHOT_DAY_BUDGET", "240"))
BACKLOG_SLACK = timedelta(days=1)
NIGHT_RERUN = 120
# Explicit key lists in one DELETE are cut into chunks of this many.
KEY_CHUNK = 1000
RUN_INTERVAL = 3600
FIRST_RUN_DELAY = 90
# The small tables read over 7 days at full detail (economy and shop trends).
SMALL_FULL_DAYS = 8
# An offline bot's last channel needs one position; a month of daily ones.
POSITIONS_HISTORY_DAYS = 30
SETTING_PREFIX = "snapret:"

ENV_FULL = "SEBAN_KEEP_FULL_DAYS"
ENV_HOURLY = "SEBAN_KEEP_HOURLY_DAYS"
ENV_HISTORY = "SEBAN_KEEP_HISTORY_DAYS"
ENV_NEWS = "SEBAN_KEEP_NEWS_DAYS"
ENV_GEAR = "SEBAN_GEAR_PER_CHARACTER"
DEFAULTS = {ENV_FULL: 2, ENV_HOURLY: 14, ENV_HISTORY: 180, ENV_NEWS: 30, ENV_GEAR: 300}
LIMITS = {ENV_FULL: (0, 30), ENV_HOURLY: (1, 90), ENV_HISTORY: (0, 3650), ENV_NEWS: (0, 3650), ENV_GEAR: (0, 100000)}

# (table, key columns besides captured_at, kind): kind picks the tiers below.
SNAPSHOT_TABLES = (
    ("web_seban_item_snapshot", ("vnum", "socket0"), "items"),
    ("web_seban_shop_item_snapshot", ("vnum", "socket0"), "shop_items"),
    ("web_seban_bot_position_snapshot", ("pid",), "positions"),
    ("web_seban_map_snapshot", ("channel", "map_index"), "maps"),
    ("web_seban_metric_snapshot", ("metric",), "small"),
    ("web_seban_shop_snapshot", ("map_index",), "small"),
)


def _say(message):
    print(f"[snapshot-retention] {message}", flush=True)


def _int_env(name, environ=None):
    environ = os.environ if environ is None else environ
    raw = str(environ.get(name, "")).strip()
    try:
        value = int(raw) if raw else DEFAULTS[name]
    except ValueError:
        value = DEFAULTS[name]
    low, high = LIMITS[name]
    return min(high, max(low, value))


def settings_from_env(environ=None):
    """The five keep settings, clamped and made consistent (each tier at
    least as long as the one before it)."""
    full = _int_env(ENV_FULL, environ)
    hourly = max(_int_env(ENV_HOURLY, environ), full)
    history = _int_env(ENV_HISTORY, environ)
    if history:
        history = max(history, hourly)
    return {"full": full, "hourly": hourly, "history": history,
            "news": _int_env(ENV_NEWS, environ), "gear": _int_env(ENV_GEAR, environ)}


def tiers(kind, cfg):
    """(full_days, hourly_days, daily_days) of a table kind: rows newer than
    full_days stay as written, then one per key an hour up to hourly_days,
    then one per key a day up to daily_days (== hourly_days: no daily tier;
    0: the daily rows are kept forever)."""
    full, hourly, history = cfg["full"], cfg["hourly"], cfg["history"]
    if kind == "items":
        return full, hourly, hourly
    if kind == "shop_items":
        return full, hourly, history
    if kind == "positions":
        daily = min(history, POSITIONS_HISTORY_DAYS) if history else POSITIONS_HISTORY_DAYS
        return full, full, max(daily, full)
    if kind == "maps":
        return full, hourly, hourly
    # small: metric_snapshot, shop_snapshot
    small_full = max(full, SMALL_FULL_DAYS)
    small_hourly = max(hourly, small_full)
    return small_full, small_hourly, (max(history, small_hourly) if history else 0)


def floor_hour(value):
    return value.replace(minute=0, second=0, microsecond=0)


def floor_day(value):
    return datetime.combine(value.date(), datetime.min.time())


def cutoffs(now, full_days, hourly_days, daily_days):
    """(full_cut, hourly_cut, delete_cut): hourly thinning runs below
    full_cut, daily thinning below hourly_cut, everything below delete_cut
    goes (None: nothing is deleted outright)."""
    full_cut = floor_hour(now - timedelta(days=full_days))
    hourly_cut = floor_day(now - timedelta(days=hourly_days))
    if hourly_cut > full_cut:
        hourly_cut = floor_day(full_cut)
    if daily_days == 0:
        delete_cut = None
    else:
        delete_cut = floor_day(now - timedelta(days=daily_days))
        delete_cut = min(delete_cut, hourly_cut)
    return full_cut, hourly_cut, delete_cut


def plan_bucket(rows):
    """rows: [(captured_at, *key)] of one bucket. Returns
    [(captured_at, mode, keys)] with mode "all" (every row of that snapshot
    goes), "except" (all but `keys`) or "only" (just `keys`). A key's last
    row in the bucket always stays."""
    last, by_time = {}, {}
    for row in rows:
        at, key = row[0], tuple(row[1:])
        by_time.setdefault(at, []).append(key)
        if key not in last or at > last[key]:
            last[key] = at
    plan = []
    for at in sorted(by_time):
        keys = by_time[at]
        keep = [key for key in keys if last[key] == at]
        if len(keep) == len(keys):
            continue
        if not keep:
            plan.append((at, "all", []))
        else:
            drop = [key for key in keys if last[key] != at]
            if len(keep) <= len(drop) and len(keep) <= KEY_CHUNK:
                plan.append((at, "except", keep))
            else:
                plan.append((at, "only", drop))
    return plan


def _tuple_sql(columns):
    if len(columns) == 1:
        return f"`{columns[0]}`"
    return "(" + ",".join(f"`{c}`" for c in columns) + ")"


def _tuple_marks(columns, count):
    one = "%s" if len(columns) == 1 else "(" + ",".join(["%s"] * len(columns)) + ")"
    return ",".join([one] * count)


def _flat(keys):
    return [value for key in keys for value in key]


def delete_statements(table, columns, at, mode, keys, limit=None):
    """The DELETE statements (sql, params) carrying out one plan_bucket()
    entry. Every one is bound to captured_at = at (the primary key's prefix)
    and so touches one snapshot at most. `limit`: the LIMIT of "all" and
    "except", the key list size of "only" (default BATCH / KEY_CHUNK)."""
    limit = BATCH if limit is None else limit
    base = f"DELETE FROM player.`{table}` WHERE `captured_at`=%s"
    if mode == "all":
        return [(f"{base} LIMIT {limit}", [at])]
    if mode == "except":
        return [(f"{base} AND {_tuple_sql(columns)} NOT IN ({_tuple_marks(columns, len(keys))}) LIMIT {limit}",
                 [at] + _flat(keys))]
    statements = []
    chunk_size = max(1, min(KEY_CHUNK, limit))
    for start in range(0, len(keys), chunk_size):
        chunk = keys[start:start + chunk_size]
        statements.append((f"{base} AND {_tuple_sql(columns)} IN ({_tuple_marks(columns, len(chunk))})",
                           [at] + _flat(chunk)))
    return statements


# ---------------------------------------------------------------- MT2009_PLUS_SEBAN_SNAPSHOT_GENTLE_V1
def heavy_hours(environ=None):
    """(from, to) of M2_SEBAN_SNAPSHOT_HEAVY_HOURS ("3-6"): the hours in
    which the backlog may be worked on; from == to: never (the backlog then
    only goes by hand, "run --heavy"); "0-24": always."""
    environ = os.environ if environ is None else environ
    raw = str(environ.get(ENV_HEAVY_HOURS, "")).strip()
    try:
        low, high = (int(part) for part in raw.split("-", 1))
        if not (0 <= low <= 24 and 0 <= high <= 24):
            raise ValueError(raw)
    except ValueError:
        return DEFAULT_HEAVY_HOURS
    if (low, high) == (0, 24):
        return 0, 24
    return low % 24, high % 24


def in_window(now, hours):
    low, high = hours
    if (low, high) == (0, 24):
        return True
    if low == high:
        return False
    if low < high:
        return low <= now.hour < high
    return now.hour >= low or now.hour < high   # over midnight, e.g. 23-5


def window_seconds_left(now, hours):
    """Seconds from `now` to the end of the window it is in (0 outside)."""
    if not in_window(now, hours):
        return 0
    if hours == (0, 24):
        return 24 * 3600
    end = now.replace(hour=hours[1] % 24, minute=0, second=0, microsecond=0)
    if end <= now:
        end += timedelta(days=1)
    return (end - now).total_seconds()


def seconds_to_window(now, hours):
    """Seconds from `now` to the next start of the window (0 inside)."""
    if in_window(now, hours):
        return 0
    if hours[0] == hours[1]:
        return None
    start = now.replace(hour=hours[0], minute=0, second=0, microsecond=0)
    if start <= now:
        start += timedelta(days=1)
    return (start - now).total_seconds()


class OutOfTime(Exception):
    """The run's time is up (the day budget, or the night window closed)."""


class Throttle:
    """The pace of every statement of a run (see "How it deletes")."""

    def __init__(self, deadline=None, pause=True, clock=None, sleeper=None):
        self.batch = BATCH
        self.deadline = deadline          # a clock() value, None = no limit
        self.pause = pause                # False: no sleeping (by hand, tests)
        self.clock = clock or time.monotonic
        self.sleeper = sleeper or (lambda seconds: time.sleep(seconds))
        self.statements = 0
        self.busy_waits = 0
        self.slowest = 0.0

    def adapt(self, seconds, rows, limit):
        """The next batch from the time the last one took. Only a statement
        that filled its limit says anything about the batch size."""
        self.slowest = max(self.slowest, seconds)
        if seconds > TARGET_SECONDS:
            self.batch = max(BATCH_MIN, int(self.batch * TARGET_SECONDS / seconds * 0.9))
        elif seconds < TARGET_SECONDS / 2 and rows >= limit:
            self.batch = min(BATCH_MAX, int(self.batch * 1.5) + 1)
        return self.batch

    def rest(self, seconds):
        """How long to leave the database alone after a statement."""
        rest = max(BATCH_SLEEP, seconds * SLEEP_FACTOR)
        if seconds > SLOW_SECONDS:
            rest = max(rest, BUSY_PAUSE, seconds * 2 * SLEEP_FACTOR)
        return rest

    def check_time(self):
        if self.deadline is not None and self.clock() >= self.deadline:
            raise OutOfTime()

    @staticmethod
    def busy(cur):
        """None when the database is quiet enough, else why it is not."""
        cur.execute("SHOW GLOBAL STATUS WHERE Variable_name IN ('Threads_running','Innodb_history_list_length')")
        status = {str(name).lower(): value for name, value in cur.fetchall()}
        try:
            running = int(status.get("threads_running", 0))
            history = int(status.get("innodb_history_list_length", 0))
        except (TypeError, ValueError):
            return None
        # This job's own statement is one of the running ones.
        if running - 1 > BUSY_THREADS:
            return f"{running} statements running"
        if HISTORY_MAX and history > HISTORY_MAX:
            return f"{history} undo records waiting for purge"
        return None

    def wait_quiet(self, cur):
        while True:
            self.check_time()
            if not self.pause or not self.busy(cur):
                return
            self.busy_waits += 1
            self.sleeper(BUSY_PAUSE)

    def execute(self, cur, sql, params=(), limit=None):
        """One statement at the throttle's pace. Returns cur.rowcount."""
        self.wait_quiet(cur)
        started = self.clock()
        cur.execute(sql, params)
        rows = cur.rowcount
        seconds = self.clock() - started
        self.statements += 1
        if limit:
            self.adapt(seconds, rows, limit)
        if self.pause:
            self.sleeper(self.rest(seconds))
        return rows


# ---------------------------------------------------------------- the database side
def table_info(cur, table):
    cur.execute("SELECT engine, table_rows FROM information_schema.tables WHERE table_schema='player' AND table_name=%s",
                (table,))
    return cur.fetchone()


def ensure_time_index(cur, table, column, say):
    """True when an index starts with `column`; adds one online when not."""
    if log_maintenance.time_indexed(cur, "player", table, column):
        return True
    cur.execute("SET SESSION lock_wait_timeout=5")
    try:
        cur.execute(f"ALTER TABLE player.`{table}` ADD INDEX IF NOT EXISTS snapret_time (`{column}`), "
                    f"ALGORITHM=INPLACE, LOCK=NONE")
        say(f"{table}: index on {column} added")
        return True
    except Exception as exc:  # pymysql.MySQLError (lock wait, old server): skipped this round
        say(f"{table}: no index on {column} and none added now ({exc}); skipped")
        return False
    finally:
        cur.execute("SET SESSION lock_wait_timeout=DEFAULT")


def oldest(cur, table, column, below=None, since=None):
    """MIN(column) (below `below`, from `since` on): one index seek."""
    where, params = [], []
    if since is not None:
        where.append(f"`{column}` >= %s")
        params.append(since)
    if below is not None:
        where.append(f"`{column}` < %s")
        params.append(below)
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    cur.execute(f"SELECT MIN(`{column}`) FROM player.`{table}`{clause}", params)
    row = cur.fetchone()
    return row[0] if row else None


def delete_older(cur, table, column, cutoff, throttle):
    """DELETE ... WHERE column < cutoff, throttle.batch rows a statement,
    walking forward from the oldest row (see "How it deletes")."""
    total = 0
    position = oldest(cur, table, column, below=cutoff)
    while position is not None:
        limit = throttle.batch
        rows = throttle.execute(
            cur, f"DELETE FROM player.`{table}` WHERE `{column}` >= %s AND `{column}` < %s LIMIT {limit}",
            (position, cutoff), limit)
        total += rows
        if rows < limit:
            break
        position = oldest(cur, table, column, below=cutoff, since=position)
    return total


def thin_bucket(cur, table, columns, start, end, throttle):
    """Keep each key's last row of [start, end). Returns rows deleted."""
    names = ",".join(f"`{c}`" for c in columns)
    throttle.wait_quiet(cur)
    cur.execute(f"SELECT `captured_at`,{names} FROM player.`{table}` WHERE `captured_at`>=%s AND `captured_at`<%s",
                (start, end))
    deleted = 0
    for at, mode, keys in plan_bucket(cur.fetchall()):
        if mode == "only":
            done = 0
            while done < len(keys):
                size = max(1, min(KEY_CHUNK, throttle.batch))
                (sql, params), = delete_statements(table, columns, at, "only", keys[done:done + size], size)
                deleted += throttle.execute(cur, sql, params, size)
                done += size
            continue
        while True:   # "all" / "except": repeated until a statement comes back short
            limit = throttle.batch
            (sql, params), = delete_statements(table, columns, at, mode, keys, limit)
            rows = throttle.execute(cur, sql, params, limit)
            deleted += rows
            if rows < limit:
                break
    return deleted


def _get_watermark(cur, name):
    value = log_maintenance.get_setting(cur, SETTING_PREFIX + name)
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S") if value else None
    except ValueError:
        return None


def thin_start(cur, table, grain):
    """Where the thinning of `grain` goes on from: the watermark, or the
    oldest row's bucket (None: an empty table)."""
    floor = floor_hour if grain == "hour" else floor_day
    first = oldest(cur, table, "captured_at")
    if first is None:
        return None
    start = _get_watermark(cur, f"{table}:{grain}")
    return max(start or floor(first), floor(first))


def thin_range(cur, table, columns, grain, upto, throttle):
    """Thin every whole `grain` ("hour"/"day") bucket below `upto`, from the
    watermark (or the oldest row) on; moves the watermark bucket by bucket so
    a stopped run resumes where it was. Returns (rows deleted, buckets)."""
    step = timedelta(hours=1) if grain == "hour" else timedelta(days=1)
    mark = f"{table}:{grain}"
    start = thin_start(cur, table, grain)
    if start is None:
        return 0, 0
    deleted = buckets = 0
    # A day is only thinned below hourly_cut, which the hourly pass of the
    # same run has already reached: a day's read is at most 24 rows a key.
    while start + step <= upto:
        deleted += thin_bucket(cur, table, columns, start, start + step, throttle)
        start += step
        buckets += 1
        log_maintenance.set_setting(cur, SETTING_PREFIX + mark, log_maintenance._ts(start))
    return deleted, buckets


def is_backlog(position, cutoff):
    """More than BACKLOG_SLACK of work below `cutoff` from `position` on."""
    return position is not None and cutoff is not None and position < cutoff - BACKLOG_SLACK


def prune_snapshot_table(cur, table, columns, kind, cfg, now, say=_say, throttle=None, heavy=True):
    """heavy False (the day): each step only when it is the small tail - a
    backlog is left for the night and reported in result["waiting"]."""
    throttle = throttle or Throttle(pause=False)
    info = table_info(cur, table)
    if not info:
        return None
    if not ensure_time_index(cur, table, "captured_at", say):
        return {"skipped": "no time index"}
    full_days, hourly_days, daily_days = tiers(kind, cfg)
    full_cut, hourly_cut, delete_cut = cutoffs(now, full_days, hourly_days, daily_days)
    result = {"engine": info[0], "deleted": 0, "hourly": 0, "daily": 0}
    waiting = []
    if delete_cut is not None:
        if heavy or not is_backlog(oldest(cur, table, "captured_at", below=delete_cut), delete_cut):
            result["deleted"] = delete_older(cur, table, "captured_at", delete_cut, throttle)
        else:
            waiting.append("delete")
    if heavy or not is_backlog(thin_start(cur, table, "hour"), full_cut):
        result["hourly"], _ = thin_range(cur, table, columns, "hour", full_cut, throttle)
    else:
        waiting.append("hour")
    if daily_days != hourly_days:
        if heavy or not is_backlog(thin_start(cur, table, "day"), hourly_cut):
            result["daily"], _ = thin_range(cur, table, columns, "day", hourly_cut, throttle)
        else:
            waiting.append("day")
    if waiting:
        result["waiting"] = waiting
    removed = result["deleted"] + result["hourly"] + result["daily"]
    if removed:
        say(f"{table}: removed {removed} rows ({result['deleted']} older than "
            f"{log_maintenance._ts(delete_cut) if delete_cut else '-'}, {result['hourly']} thinned to one an hour "
            f"below {log_maintenance._ts(full_cut)}, {result['daily']} to one a day below "
            f"{log_maintenance._ts(hourly_cut)}; {info[0]})")
    return result


def prune_news(cur, cfg, now, say=_say, throttle=None, heavy=True):
    throttle = throttle or Throttle(pause=False)
    if not cfg["news"] or not table_info(cur, "web_seban_news_event"):
        return None
    if not ensure_time_index(cur, "web_seban_news_event", "time", say):
        return {"skipped": "no time index"}
    cutoff = floor_day(now - timedelta(days=cfg["news"]))
    if not heavy and is_backlog(oldest(cur, "web_seban_news_event", "time", below=cutoff), cutoff):
        return {"deleted": 0, "waiting": ["delete"]}
    deleted = delete_older(cur, "web_seban_news_event", "time", cutoff, throttle)
    if deleted:
        say(f"web_seban_news_event: removed {deleted} rows older than {log_maintenance._ts(cutoff)}")
    return {"deleted": deleted}


def prune_gear(cur, cfg, now, say=_say, throttle=None, heavy=True):
    """The equipment history: nothing older than GEAR_KEEP_DAYS, and per
    character only its newest cfg["gear"] rows (the page shows 60). The cap
    counts the rows of every character (a scan of the whole pid index):
    night only."""
    throttle = throttle or Throttle(pause=False)
    table = "web_seban_gear_event"
    if not table_info(cur, table):
        return None
    if not ensure_time_index(cur, table, "time", say):
        return {"skipped": "no time index"}
    cutoff = now - timedelta(days=log_maintenance.GEAR_KEEP_DAYS)
    waiting = []
    old = 0
    if heavy or not is_backlog(oldest(cur, table, "time", below=cutoff), cutoff):
        old = delete_older(cur, table, "time", cutoff, throttle)
    else:
        waiting.append("delete")
    capped = 0
    cap = cfg["gear"]
    if cap and not heavy:
        waiting.append("cap")
    elif cap and log_maintenance.time_indexed(cur, "player", table, "pid"):
        throttle.wait_quiet(cur)
        cur.execute(f"SELECT pid FROM player.`{table}` GROUP BY pid HAVING COUNT(*) > %s", (cap,))
        for (pid,) in cur.fetchall():
            throttle.wait_quiet(cur)
            cur.execute(f"SELECT `time` FROM player.`{table}` WHERE pid=%s ORDER BY `time` DESC LIMIT 1 OFFSET %s",
                        (pid, cap - 1))
            row = cur.fetchone()
            if not row:
                continue
            while True:
                limit = throttle.batch
                rows = throttle.execute(cur, f"DELETE FROM player.`{table}` WHERE pid=%s AND `time` < %s LIMIT {limit}",
                                        (pid, row[0]), limit)
                capped += rows
                if rows < limit:
                    break
    if old or capped:
        say(f"{table}: removed {old} rows older than {log_maintenance.GEAR_KEEP_DAYS} days and {capped} "
            f"beyond the newest {cap} of a character")
    result = {"deleted": old, "capped": capped}
    if waiting:
        result["waiting"] = waiting
    return result


def run(con, now=None, environ=None, say=_say, sleep=None, heavy=None):
    """One whole run. Returns the result dict, or None when another run holds
    the lock. The cutoffs are computed from the database's clock.
    heavy: None = by the heavy hours, True = the backlog too (by hand).
    sleep: 0 = no pauses at all (by hand; the tests)."""
    cfg = settings_from_env(environ)
    if not cfg["full"]:
        return {"status": "off"}
    with con.cursor() as cur:
        cur.execute("SET SESSION max_statement_time=0")
        cur.execute("SELECT GET_LOCK(%s, 0)", (LOCK_NAME,))
        if cur.fetchone()[0] != 1:
            return None
    started = time.monotonic()
    result = {"status": "ok", "tables": {}}
    try:
        with con.cursor() as cur:
            # A row lock held by the game is waited for 5 s at most (the
            # statement fails, the next run tries again), and no gap locks.
            cur.execute("SET SESSION innodb_lock_wait_timeout=5")
            cur.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
            log_maintenance.ensure_tables(cur)
            now = now or log_maintenance.db_now(cur)
            hours = heavy_hours(environ)
            night = in_window(now, hours)
            if heavy is None:
                heavy = night
                budget = window_seconds_left(now, hours) if night else DAY_BUDGET
            else:
                budget = None   # by hand: until done (Ctrl+C stops it; the watermarks keep the place)
            throttle = Throttle(deadline=started + budget if budget else None, pause=sleep != 0)
            result["heavy"] = bool(heavy)
            for table, columns, kind in SNAPSHOT_TABLES:
                try:
                    found = prune_snapshot_table(cur, table, columns, kind, cfg, now, say, throttle, heavy)
                except OutOfTime:
                    result["status"] = "paused"
                    break
                except Exception as exc:  # one table's trouble never stops the others
                    result["status"] = "partial"
                    found = {"error": str(exc)}
                    say(f"{table}: {exc}")
                if found is not None:
                    result["tables"][table] = found
            for name, job in (("web_seban_news_event", prune_news), ("web_seban_gear_event", prune_gear)):
                if result["status"] == "paused":
                    break
                try:
                    found = job(cur, cfg, now, say, throttle, heavy)
                except OutOfTime:
                    result["status"] = "paused"
                    break
                except Exception as exc:
                    result["status"] = "partial"
                    found = {"error": str(exc)}
                    say(f"{name}: {exc}")
                if found is not None:
                    result["tables"][name] = found
            removed = sum(sum(v for k, v in (t or {}).items() if isinstance(v, int)) for t in result["tables"].values())
            result["removed"] = removed
            result["seconds"] = round(time.monotonic() - started, 1)
            result["pending"] = result["status"] == "paused" or any(
                "waiting" in (t or {}) for t in result["tables"].values())
            result["statements"] = throttle.statements
            result["busy_waits"] = throttle.busy_waits
            log_maintenance.set_setting(cur, SETTING_PREFIX + "last", json.dumps(
                {"at": log_maintenance._ts(now), "status": result["status"], "removed": removed,
                 "seconds": result["seconds"], "heavy": result["heavy"], "pending": result["pending"],
                 "batch": throttle.batch, "slowest": round(throttle.slowest, 3), "busy_waits": throttle.busy_waits}))
            if removed or result["status"] == "paused":
                say(f"run {result['status']}: {removed} rows removed in {result['seconds']} s "
                    f"({throttle.statements} statements, batch now {throttle.batch}, slowest "
                    f"{throttle.slowest:.2f} s, {throttle.busy_waits} waits for a busy database"
                    f"{', backlog left for the night' if result['pending'] and not heavy else ''})")
    finally:
        with con.cursor() as cur:
            cur.execute("SELECT RELEASE_LOCK(%s)", (LOCK_NAME,))
    return result


def next_pause(result, now, hours):
    """Seconds until the next run: NIGHT_RERUN inside the heavy hours while
    backlog remains, else RUN_INTERVAL - but a backlog waiting for the night
    starts when the window opens, not up to an hour later."""
    if result and result.get("pending"):
        if in_window(now, hours):
            return NIGHT_RERUN
        until = seconds_to_window(now, hours)
        if until is not None:
            return max(NIGHT_RERUN, min(RUN_INTERVAL, until + 60))
    return RUN_INTERVAL


def loop():
    """collector.py's background thread: a run FIRST_RUN_DELAY s after the
    start (the collector's first round has created the tables by then), then
    every next_pause() s. A run's own length never shifts the snapshots."""
    time.sleep(FIRST_RUN_DELAY)
    while True:
        pause = RUN_INTERVAL
        try:
            con = log_maintenance.connect()
            try:
                result = run(con)
                with con.cursor() as cur:
                    pause = next_pause(result, log_maintenance.db_now(cur), heavy_hours())
            finally:
                con.close()
        except Exception as exc:
            _say(f"run failed: {exc}")
        time.sleep(pause)


def plan(con, environ=None):
    """What a run would do: the cutoffs per table and the rows beyond the
    outright delete cutoff (read only)."""
    cfg = settings_from_env(environ)
    out = {"settings": cfg, "tables": {}}
    with con.cursor() as cur:
        now = log_maintenance.db_now(cur)
        for table, _columns, kind in SNAPSHOT_TABLES:
            if not table_info(cur, table):
                continue
            full_cut, hourly_cut, delete_cut = cutoffs(now, *tiers(kind, cfg))
            entry = {"full_from": full_cut, "hourly_from": hourly_cut, "delete_below": delete_cut}
            if delete_cut is not None:
                cur.execute(f"SELECT COUNT(*) FROM player.`{table}` WHERE captured_at < %s", (delete_cut,))
                entry["rows_to_delete"] = int(cur.fetchone()[0])
            out["tables"][table] = entry
    return out


def main(argv):
    import argparse
    parser = argparse.ArgumentParser(description="Retention of the advanced panel's snapshot tables")
    parser.add_argument("command", choices=("plan", "run"))
    parser.add_argument("--heavy", action="store_true",
                        help="work on the backlog now, outside the heavy hours (still throttled)")
    args = parser.parse_args(argv)
    con = log_maintenance.connect()
    try:
        result = plan(con) if args.command == "plan" else run(con, heavy=True if args.heavy else None)
        print(json.dumps(result, default=str, indent=1))
    finally:
        con.close()


if __name__ == "__main__":
    main(sys.argv[1:])
