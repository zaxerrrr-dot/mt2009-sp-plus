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
and a 5 s lock wait, or the table is skipped this round). Deletes go in
batches of BATCH rows (or one snapshot of one bucket) with BATCH_SLEEP
between them, so the game never waits on a long lock; the first run on a big
table therefore takes a while (tens of minutes) and runs in its own thread
of the collector, never delaying the snapshots. A named lock (GET_LOCK) keeps
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

By hand, inside the collector container:
    python snapshot_retention.py plan      the cutoffs and what is beyond them
    python snapshot_retention.py run       one run now (waits for nothing)
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta

import log_maintenance

LOCK_NAME = "mt2009_snapshot_retention"
BATCH = 20000
BATCH_SLEEP = float(os.environ.get("SEBAN_SNAPSHOT_PRUNE_SLEEP", "0.1"))
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


def delete_statements(table, columns, at, mode, keys):
    """The DELETE statements (sql, params) carrying out one plan_bucket()
    entry. Every one is bound to captured_at = at (the primary key's prefix)
    and so touches one snapshot at most."""
    base = f"DELETE FROM player.`{table}` WHERE `captured_at`=%s"
    if mode == "all":
        return [(f"{base} LIMIT {BATCH}", [at])]
    if mode == "except":
        return [(f"{base} AND {_tuple_sql(columns)} NOT IN ({_tuple_marks(columns, len(keys))}) LIMIT {BATCH}",
                 [at] + _flat(keys))]
    statements = []
    for start in range(0, len(keys), KEY_CHUNK):
        chunk = keys[start:start + KEY_CHUNK]
        statements.append((f"{base} AND {_tuple_sql(columns)} IN ({_tuple_marks(columns, len(chunk))})",
                           [at] + _flat(chunk)))
    return statements


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


def delete_older(cur, table, column, cutoff, sleep=None):
    """DELETE ... WHERE column < cutoff, BATCH rows a statement."""
    sleep = BATCH_SLEEP if sleep is None else sleep
    total = 0
    while True:
        cur.execute(f"DELETE FROM player.`{table}` WHERE `{column}` < %s LIMIT {BATCH}", (cutoff,))
        total += cur.rowcount
        if cur.rowcount < BATCH:
            return total
        time.sleep(sleep)


def _execute_all(cur, sql, params, sleep):
    """A plan statement; one with a LIMIT is repeated until it comes back short."""
    total = 0
    while True:
        cur.execute(sql, params)
        total += cur.rowcount
        if "LIMIT" not in sql or cur.rowcount < BATCH:
            break
        time.sleep(sleep)
    if sleep:
        time.sleep(sleep / 2)
    return total


def thin_bucket(cur, table, columns, start, end, sleep=None):
    """Keep each key's last row of [start, end). Returns rows deleted."""
    sleep = BATCH_SLEEP if sleep is None else sleep
    names = ",".join(f"`{c}`" for c in columns)
    cur.execute(f"SELECT `captured_at`,{names} FROM player.`{table}` WHERE `captured_at`>=%s AND `captured_at`<%s",
                (start, end))
    deleted = 0
    for at, mode, keys in plan_bucket(cur.fetchall()):
        for sql, params in delete_statements(table, columns, at, mode, keys):
            deleted += _execute_all(cur, sql, params, sleep)
    return deleted


def _get_watermark(cur, name):
    value = log_maintenance.get_setting(cur, SETTING_PREFIX + name)
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S") if value else None
    except ValueError:
        return None


def thin_range(cur, table, columns, grain, upto, sleep=None):
    """Thin every whole `grain` ("hour"/"day") bucket below `upto`, from the
    watermark (or the oldest row) on; moves the watermark bucket by bucket so
    a stopped run resumes where it was. Returns (rows deleted, buckets)."""
    step = timedelta(hours=1) if grain == "hour" else timedelta(days=1)
    floor = floor_hour if grain == "hour" else floor_day
    mark = f"{table}:{grain}"
    start = _get_watermark(cur, mark)
    cur.execute(f"SELECT MIN(`captured_at`) FROM player.`{table}`")
    oldest = cur.fetchone()[0]
    if oldest is None:
        return 0, 0
    start = max(start or floor(oldest), floor(oldest))
    deleted = buckets = 0
    # A day is only thinned below hourly_cut, which the hourly pass of the
    # same run has already reached: a day's read is at most 24 rows a key.
    while start + step <= upto:
        deleted += thin_bucket(cur, table, columns, start, start + step, sleep)
        start += step
        buckets += 1
        log_maintenance.set_setting(cur, SETTING_PREFIX + mark, log_maintenance._ts(start))
    return deleted, buckets


def prune_snapshot_table(cur, table, columns, kind, cfg, now, say=_say, sleep=None):
    info = table_info(cur, table)
    if not info:
        return None
    if not ensure_time_index(cur, table, "captured_at", say):
        return {"skipped": "no time index"}
    full_days, hourly_days, daily_days = tiers(kind, cfg)
    full_cut, hourly_cut, delete_cut = cutoffs(now, full_days, hourly_days, daily_days)
    result = {"engine": info[0], "deleted": 0, "hourly": 0, "daily": 0}
    if delete_cut is not None:
        result["deleted"] = delete_older(cur, table, "captured_at", delete_cut, sleep)
    result["hourly"], _ = thin_range(cur, table, columns, "hour", full_cut, sleep)
    if daily_days != hourly_days:
        result["daily"], _ = thin_range(cur, table, columns, "day", hourly_cut, sleep)
    removed = result["deleted"] + result["hourly"] + result["daily"]
    if removed:
        say(f"{table}: removed {removed} rows ({result['deleted']} older than "
            f"{log_maintenance._ts(delete_cut) if delete_cut else '-'}, {result['hourly']} thinned to one an hour "
            f"below {log_maintenance._ts(full_cut)}, {result['daily']} to one a day below "
            f"{log_maintenance._ts(hourly_cut)}; {info[0]})")
    return result


def prune_news(cur, cfg, now, say=_say, sleep=None):
    if not cfg["news"] or not table_info(cur, "web_seban_news_event"):
        return None
    if not ensure_time_index(cur, "web_seban_news_event", "time", say):
        return {"skipped": "no time index"}
    cutoff = floor_day(now - timedelta(days=cfg["news"]))
    deleted = delete_older(cur, "web_seban_news_event", "time", cutoff, sleep)
    if deleted:
        say(f"web_seban_news_event: removed {deleted} rows older than {log_maintenance._ts(cutoff)}")
    return {"deleted": deleted}


def prune_gear(cur, cfg, now, say=_say, sleep=None):
    """The equipment history: nothing older than GEAR_KEEP_DAYS, and per
    character only its newest cfg["gear"] rows (the page shows 60)."""
    sleep = BATCH_SLEEP if sleep is None else sleep
    table = "web_seban_gear_event"
    if not table_info(cur, table):
        return None
    if not ensure_time_index(cur, table, "time", say):
        return {"skipped": "no time index"}
    cutoff = now - timedelta(days=log_maintenance.GEAR_KEEP_DAYS)
    old = delete_older(cur, table, "time", cutoff, sleep)
    capped = 0
    cap = cfg["gear"]
    if cap and log_maintenance.time_indexed(cur, "player", table, "pid"):
        cur.execute(f"SELECT pid FROM player.`{table}` GROUP BY pid HAVING COUNT(*) > %s", (cap,))
        for (pid,) in cur.fetchall():
            cur.execute(f"SELECT `time` FROM player.`{table}` WHERE pid=%s ORDER BY `time` DESC LIMIT 1 OFFSET %s",
                        (pid, cap - 1))
            row = cur.fetchone()
            if not row:
                continue
            while True:
                cur.execute(f"DELETE FROM player.`{table}` WHERE pid=%s AND `time` < %s LIMIT {BATCH}", (pid, row[0]))
                capped += cur.rowcount
                if cur.rowcount < BATCH:
                    break
                time.sleep(sleep)
            time.sleep(sleep / 10)
    if old or capped:
        say(f"{table}: removed {old} rows older than {log_maintenance.GEAR_KEEP_DAYS} days and {capped} "
            f"beyond the newest {cap} of a character")
    return {"deleted": old, "capped": capped}


def run(con, now=None, environ=None, say=_say, sleep=None):
    """One whole run. Returns the result dict, or None when another run holds
    the lock. The cutoffs are computed from the database's clock."""
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
            log_maintenance.ensure_tables(cur)
            now = now or log_maintenance.db_now(cur)
            for table, columns, kind in SNAPSHOT_TABLES:
                try:
                    found = prune_snapshot_table(cur, table, columns, kind, cfg, now, say, sleep)
                except Exception as exc:  # one table's trouble never stops the others
                    result["status"] = "partial"
                    found = {"error": str(exc)}
                    say(f"{table}: {exc}")
                if found is not None:
                    result["tables"][table] = found
            for name, job in (("web_seban_news_event", prune_news), ("web_seban_gear_event", prune_gear)):
                try:
                    found = job(cur, cfg, now, say, sleep)
                except Exception as exc:
                    result["status"] = "partial"
                    found = {"error": str(exc)}
                    say(f"{name}: {exc}")
                if found is not None:
                    result["tables"][name] = found
            removed = sum(sum(v for k, v in (t or {}).items() if isinstance(v, int)) for t in result["tables"].values())
            result["removed"] = removed
            result["seconds"] = round(time.monotonic() - started, 1)
            log_maintenance.set_setting(cur, SETTING_PREFIX + "last", json.dumps(
                {"at": log_maintenance._ts(now), "status": result["status"], "removed": removed,
                 "seconds": result["seconds"]}))
            if removed:
                say(f"run done: {removed} rows removed in {result['seconds']} s")
    finally:
        with con.cursor() as cur:
            cur.execute("SELECT RELEASE_LOCK(%s)", (LOCK_NAME,))
    return result


def loop():
    """collector.py's background thread: a run FIRST_RUN_DELAY s after the
    start (the collector's first round has created the tables by then), then
    every RUN_INTERVAL s. A run's own length never shifts the snapshots."""
    time.sleep(FIRST_RUN_DELAY)
    while True:
        try:
            con = log_maintenance.connect()
            try:
                run(con)
            finally:
                con.close()
        except Exception as exc:
            _say(f"run failed: {exc}")
        time.sleep(RUN_INTERVAL)


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
    args = parser.parse_args(argv)
    con = log_maintenance.connect()
    try:
        result = plan(con) if args.command == "plan" else run(con)
        print(json.dumps(result, default=str, indent=1))
    finally:
        con.close()


if __name__ == "__main__":
    main(sys.argv[1:])
