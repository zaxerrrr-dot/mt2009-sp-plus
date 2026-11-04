"""MT2009_PLUS_SEBAN_SNAPSHOT_RETENTION_V1: python3 -m unittest test_snapshot_retention

No database: the pure parts (settings, tiers, cutoffs, the bucket plan and
its DELETE statements) are checked directly, and a whole run against a small
in-memory stand-in for the snapshot tables that understands exactly the
statements snapshot_retention.py sends. Runs without PyMySQL too (a stub is
put in its place when the host has none)."""
import re
import sys
import types
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

try:
    import pymysql  # noqa: F401
except ImportError:
    stub = types.ModuleType("pymysql")
    stub.MySQLError = Exception
    stub.cursors = types.ModuleType("pymysql.cursors")
    stub.cursors.DictCursor = stub.cursors.SSCursor = object
    stub.connect = lambda **kw: (_ for _ in ()).throw(RuntimeError("no database in this test"))
    sys.modules["pymysql"] = stub
    sys.modules["pymysql.cursors"] = stub.cursors

import snapshot_retention as sr


class Settings(unittest.TestCase):
    def test_defaults_are_on(self):
        cfg = sr.settings_from_env({})
        self.assertEqual(cfg, {"full": 2, "hourly": 14, "history": 180, "news": 30, "gear": 300})

    def test_clamped_and_ordered(self):
        cfg = sr.settings_from_env({"SEBAN_KEEP_FULL_DAYS": "20", "SEBAN_KEEP_HOURLY_DAYS": "3",
                                    "SEBAN_KEEP_HISTORY_DAYS": "5", "SEBAN_KEEP_NEWS_DAYS": "x",
                                    "SEBAN_GEAR_PER_CHARACTER": "-4"})
        self.assertEqual(cfg["full"], 20)
        self.assertEqual(cfg["hourly"], 20)       # never shorter than full
        self.assertEqual(cfg["history"], 20)      # never shorter than hourly
        self.assertEqual(cfg["news"], 30)         # garbage -> default
        self.assertEqual(cfg["gear"], 0)          # clamped to the minimum
        self.assertEqual(sr.settings_from_env({"SEBAN_KEEP_HISTORY_DAYS": "0"})["history"], 0)
        self.assertEqual(sr.settings_from_env({"SEBAN_KEEP_FULL_DAYS": "999"})["full"], 30)

    def test_off_switch(self):
        self.assertEqual(sr.run(None, environ={"SEBAN_KEEP_FULL_DAYS": "0"}), {"status": "off"})

    def test_env_schema_and_example_know_the_keys(self):
        import os
        import env_schema
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(os.path.dirname(here), ".env.example"), encoding="utf-8") as handle:
            example = handle.read()
        for name, default in sr.DEFAULTS.items():
            key = "M2_" + name
            self.assertIn(key, env_schema.BY_KEY)
            self.assertEqual(env_schema.BY_KEY[key]["default"], str(default))
            self.assertEqual((env_schema.BY_KEY[key]["min"], env_schema.BY_KEY[key]["max"]), sr.LIMITS[name])
            self.assertIn(f"\n{key}={default}\n", example)


class Tiers(unittest.TestCase):
    cfg = {"full": 2, "hourly": 14, "history": 180, "news": 30, "gear": 300}

    def test_readers_needs(self):
        # /economy/item reads 14 days; items have no daily tier.
        self.assertEqual(sr.tiers("items", self.cfg), (2, 14, 14))
        self.assertEqual(sr.tiers("shop_items", self.cfg), (2, 14, 180))
        self.assertEqual(sr.tiers("positions", self.cfg), (2, 2, 30))
        self.assertEqual(sr.tiers("maps", self.cfg), (2, 14, 14))
        # 7-day trends at full detail.
        self.assertEqual(sr.tiers("small", self.cfg), (8, 14, 180))
        self.assertEqual(sr.tiers("small", dict(self.cfg, history=0)), (8, 14, 0))

    def test_cutoffs(self):
        now = datetime(2026, 11, 3, 13, 54, 7)
        self.assertEqual(sr.cutoffs(now, 2, 14, 14),
                         (datetime(2026, 11, 1, 13), datetime(2026, 10, 20), datetime(2026, 10, 20)))
        self.assertEqual(sr.cutoffs(now, 2, 2, 30),
                         (datetime(2026, 11, 1, 13), datetime(2026, 11, 1), datetime(2026, 10, 4)))
        self.assertIsNone(sr.cutoffs(now, 8, 14, 0)[2])


class BucketPlan(unittest.TestCase):
    def test_keeps_each_keys_last_row(self):
        t1, t2, t3 = (datetime(2026, 10, 20, 10, m) for m in (4, 9, 14))
        rows = [(t1, 1, 0), (t1, 2, 0), (t1, 3, 0),
                (t2, 1, 0), (t2, 2, 0),
                (t3, 1, 0)]
        plan = sr.plan_bucket(rows)
        # t1: keys 1 and 2 reappear later -> go; 3 is last seen at t1 -> stays.
        # t2: 1 reappears -> goes; 2's last row -> stays. t3: everything stays.
        self.assertEqual(plan, [(t1, "except", [(3, 0)]), (t2, "except", [(2, 0)])])

    def test_whole_snapshot(self):
        t1, t2 = datetime(2026, 10, 20, 10, 4), datetime(2026, 10, 20, 10, 9)
        self.assertEqual(sr.plan_bucket([(t1, 7), (t2, 7)]), [(t1, "all", [])])
        self.assertEqual(sr.plan_bucket([(t2, 7)]), [])
        self.assertEqual(sr.plan_bucket([]), [])

    def test_only_mode_when_most_rows_stay(self):
        t1, t2 = datetime(2026, 10, 20, 10, 4), datetime(2026, 10, 20, 10, 9)
        rows = [(t1, n) for n in range(10)] + [(t2, 0)]
        self.assertEqual(sr.plan_bucket(rows), [(t1, "only", [(0,)])])

    def test_statements(self):
        at = datetime(2026, 10, 20, 10, 4)
        (sql, params), = sr.delete_statements("web_seban_item_snapshot", ("vnum", "socket0"), at, "except", [(1, 0), (2, 5)])
        self.assertIn("`captured_at`=%s AND (`vnum`,`socket0`) NOT IN ((%s,%s),(%s,%s)) LIMIT", sql)
        self.assertEqual(params, [at, 1, 0, 2, 5])
        (sql, params), = sr.delete_statements("web_seban_bot_position_snapshot", ("pid",), at, "only", [(9,), (10,)])
        self.assertIn("`captured_at`=%s AND `pid` IN (%s,%s)", sql)
        self.assertEqual(params, [at, 9, 10])
        with patch.object(sr, "KEY_CHUNK", 2):
            self.assertEqual(len(sr.delete_statements("t", ("pid",), at, "only", [(1,), (2,), (3,)])), 2)


# ---------------------------------------------------------------- a whole run
class FakeCursor:
    """Understands the statements of snapshot_retention.py (and the few
    log_maintenance helpers it calls) over in-memory tables."""

    def __init__(self, db):
        self.db = db
        self.result = []
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def fetchone(self):
        return self.result[0] if self.result else None

    def fetchall(self):
        return list(self.result)

    def execute(self, sql, params=()):
        params = list(params or ())
        sql = " ".join(sql.split())
        self.db.log.append(sql)
        self.result, self.rowcount = [], 0
        if sql.startswith("SET ") or sql.startswith("CREATE TABLE") or sql.startswith("ALTER TABLE"):
            return
        if "GET_LOCK" in sql:
            self.result = [(0 if self.db.locked else 1,)]
            self.db.locked = True
            return
        if "RELEASE_LOCK" in sql:
            self.db.locked = False
            self.result = [(1,)]
            return
        if sql.startswith("SHOW GLOBAL STATUS"):
            status = self.db.status() if callable(self.db.status) else self.db.status
            self.result = list(status.items())
            return
        if sql == "SELECT NOW()":
            self.result = [(self.db.now,)]
            return
        if "FROM information_schema.tables" in sql:
            name = params[-1]
            self.result = [("InnoDB", len(self.db.tables[name]["rows"]))] if name in self.db.tables else []
            return
        if "FROM information_schema.statistics" in sql:
            _schema, table, column = params
            self.result = [(1,)] if column in self.db.tables.get(table, {}).get("indexed", ()) else []
            return
        if "web_seban_settings WHERE name=" in sql:
            value = self.db.settings.get(params[0])
            self.result = [(value,)] if value is not None else []
            return
        if sql.startswith("REPLACE INTO player.web_seban_settings"):
            self.db.settings[params[0]] = params[1]
            return
        match = re.match(r"SELECT MIN\(`(\w+)`\) FROM player\.`(\w+)`(?: WHERE (.*))?$", sql)
        if match:
            column, table, where = match.groups()
            values = [r[column] for r in self.db.tables[table]["rows"]]
            for part, value in zip((where or "").split(" AND ") if where else [], params):
                if ">=" in part:
                    values = [v for v in values if v >= value]
                elif "<" in part:
                    values = [v for v in values if v < value]
                else:
                    raise AssertionError(part)
            self.result = [(min(values, default=None),)]
            return
        match = re.match(r"SELECT `captured_at`,(.*) FROM player\.`(\w+)` WHERE `captured_at`>=%s AND `captured_at`<%s", sql)
        if match:
            columns = [c.strip("`") for c in match.group(1).split(",")]
            lo, hi = params
            self.result = [tuple([r["captured_at"]] + [r[c] for c in columns])
                           for r in self.db.tables[match.group(2)]["rows"] if lo <= r["captured_at"] < hi]
            return
        match = re.match(r"DELETE FROM player\.`(\w+)` WHERE `(\w+)` >= %s AND `(\w+)` < %s LIMIT (\d+)$", sql)
        if match:
            column = match.group(2)
            return self._delete(match.group(1), lambda r: params[0] <= r[column] < params[1], int(match.group(4)))
        match = re.match(r"DELETE FROM player\.`(\w+)` WHERE `captured_at`=%s(?: AND (\(?[`\w,]+\)?) (NOT IN|IN) \((.*)\))?(?: LIMIT (\d+))?$", sql)
        if match:
            table, cols, op, _marks, limit = match.groups()
            at = params[0]
            keyset = None
            if cols:
                columns = [c.strip("`()") for c in cols.split(",")]
                flat = params[1:]
                keyset = {tuple(flat[i:i + len(columns)]) for i in range(0, len(flat), len(columns))}

            def hit(r):
                if r["captured_at"] != at:
                    return False
                if keyset is None:
                    return True
                inside = tuple(r[c] for c in columns) in keyset
                return inside if op == "IN" else not inside
            return self._delete(table, hit, int(limit) if limit else None)
        match = re.match(r"SELECT pid FROM player\.`(\w+)` GROUP BY pid HAVING COUNT\(\*\) > %s", sql)
        if match:
            counts = {}
            for r in self.db.tables[match.group(1)]["rows"]:
                counts[r["pid"]] = counts.get(r["pid"], 0) + 1
            self.result = [(pid,) for pid, n in sorted(counts.items()) if n > params[0]]
            return
        match = re.match(r"SELECT `time` FROM player\.`(\w+)` WHERE pid=%s ORDER BY `time` DESC LIMIT 1 OFFSET %s", sql)
        if match:
            times = sorted((r["time"] for r in self.db.tables[match.group(1)]["rows"] if r["pid"] == params[0]), reverse=True)
            self.result = [(times[params[1]],)] if len(times) > params[1] else []
            return
        match = re.match(r"DELETE FROM player\.`(\w+)` WHERE pid=%s AND `time` < %s LIMIT (\d+)", sql)
        if match:
            return self._delete(match.group(1), lambda r: r["pid"] == params[0] and r["time"] < params[1], int(match.group(2)))
        raise AssertionError(f"unexpected statement: {sql}")

    def _delete(self, table, hit, limit):
        rows = self.db.tables[table]["rows"]
        gone = [r for r in rows if hit(r)][:limit]
        ids = {id(r) for r in gone}
        self.db.tables[table]["rows"] = [r for r in rows if id(r) not in ids]
        self.rowcount = len(gone)


class FakeConnection:
    def __init__(self, now):
        self.now = now
        self.tables, self.settings, self.log = {}, {}, []
        self.locked = False
        self.status = {"Threads_running": 2, "Innodb_history_list_length": 10}

    def cursor(self, *args):
        return FakeCursor(self)


def snapshots(start, end, every_minutes, keys, make):
    rows, at = [], start
    while at < end:
        rows += [make(at, key) for key in keys(at)]
        at += timedelta(minutes=every_minutes)
    return rows


# Every 20 minutes instead of 5: the same shape, a quarter of the rows for
# the in-memory stand-in to scan.
STEP = 20


class WholeRun(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 3, 13, 54)
        self.con = FakeConnection(self.now)
        start = self.now - timedelta(days=33)
        # Items: vnum 1 always there, vnum 2 sold out 20 days ago at 15:00.
        sold_out = datetime(2026, 10, 14, 15, 2)
        self.con.tables["web_seban_item_snapshot"] = {"indexed": ("captured_at",), "rows": snapshots(
            start, self.now, STEP, lambda at: [1] + ([2] if at < sold_out else []),
            lambda at, v: {"captured_at": at, "vnum": v, "socket0": 0, "amount": 1})}
        # Stall offers: vnum 7 offered only once, at 15:07 of 20 October (a
        # daily-tier day): "last seen" must survive the thinning.
        once = datetime(2026, 10, 20, 15, 14)
        self.once = once
        self.con.tables["web_seban_shop_item_snapshot"] = {"indexed": ("captured_at",), "rows": snapshots(
            start, self.now, STEP, lambda at: [5] + ([7] if at == once else []),
            lambda at, v: {"captured_at": at, "vnum": v, "socket0": 0})}
        self.con.tables["web_seban_bot_position_snapshot"] = {"indexed": ("captured_at", "pid"), "rows": snapshots(
            start, self.now, STEP, lambda at: [100, 101], lambda at, pid: {"captured_at": at, "pid": pid})}
        self.con.tables["web_seban_news_event"] = {"indexed": ("time",), "rows": [
            {"time": self.now - timedelta(days=d)} for d in range(0, 60)]}
        gear = []
        for n in range(500):
            gear.append({"pid": 1, "time": self.now - timedelta(minutes=n)})
        for n in range(10):
            gear.append({"pid": 2, "time": self.now - timedelta(days=n * 10)})
        self.con.tables["web_seban_gear_event"] = {"indexed": ("time", "pid"), "rows": gear}

    def run_once(self, now=None, **env):
        # The heavy hours always open unless a test says otherwise (13:54 is day).
        env.setdefault(sr.ENV_HEAVY_HOURS, "0-24")
        self.slept = []
        with patch.object(sr.time, "sleep", self.slept.append):
            return sr.run(self.con, now=now or self.now, environ=env, say=lambda m: None)

    def times(self, table, **match):
        return sorted({r["captured_at"] for r in self.con.tables[table]["rows"]
                       if all(r[k] == v for k, v in match.items())})

    def test_items(self):
        result = self.run_once()
        self.assertEqual(result["status"], "ok")
        times = self.times("web_seban_item_snapshot", vnum=1)
        full_cut = datetime(2026, 11, 1, 13)
        self.assertEqual(min(times).replace(minute=0), datetime(2026, 10, 20))
        # Full detail after the cut, one an hour (the hour's last) before it.
        older = [t for t in times if t < full_cut]
        self.assertEqual(len(older), len({t.replace(minute=0) for t in older}))
        self.assertTrue(all(t.minute + STEP >= 60 for t in older))
        recent = [t for t in times if t >= full_cut]
        self.assertEqual(len(recent), len(set(recent)))
        self.assertGreater(len(recent), 24 * 3 * 2 - 10)
        # vnum 2 is gone with the deleted days (older than 14 days).
        self.assertEqual(self.times("web_seban_item_snapshot", vnum=2), [])

    def test_shop_item_last_seen_survives(self):
        self.run_once()
        self.assertEqual(self.times("web_seban_shop_item_snapshot", vnum=7), [self.once])
        days = self.times("web_seban_shop_item_snapshot", vnum=5)
        daily = [t for t in days if t < datetime(2026, 10, 20)]
        self.assertEqual(len(daily), len({t.date() for t in daily}))
        self.assertTrue(all(t.hour == 23 for t in daily))

    def test_positions(self):
        self.run_once()
        times = self.times("web_seban_bot_position_snapshot", pid=100)
        self.assertEqual(times, self.times("web_seban_bot_position_snapshot", pid=101))
        self.assertGreaterEqual(min(times), datetime(2026, 10, 4))
        daily = [t for t in times if t < datetime(2026, 11, 1)]
        self.assertEqual(len(daily), len({t.date() for t in daily}))
        self.assertEqual(max(times), self.now - timedelta(minutes=STEP))

    def test_news_and_gear(self):
        self.run_once()
        news = self.con.tables["web_seban_news_event"]["rows"]
        self.assertTrue(news and all(r["time"] >= datetime(2026, 10, 4) for r in news))
        gear = self.con.tables["web_seban_gear_event"]["rows"]
        self.assertEqual(sum(1 for r in gear if r["pid"] == 1), 300)
        self.assertEqual(sum(1 for r in gear if r["pid"] == 2), 7)   # 0..60 days: the 60-day cap

    def test_second_run_resumes_from_watermarks(self):
        self.run_once()
        before = {name: len(t["rows"]) for name, t in self.con.tables.items()}
        self.con.log.clear()
        result = self.run_once()
        self.assertEqual(result["removed"], 0)
        self.assertEqual(before, {name: len(t["rows"]) for name, t in self.con.tables.items()})
        # Nothing re-read: no bucket SELECT below the watermarks.
        self.assertFalse([sql for sql in self.con.log if sql.startswith("SELECT `captured_at`,")])

    def test_lock_held_elsewhere(self):
        self.con.locked = True
        self.assertIsNone(self.run_once())

    def test_every_delete_is_bounded(self):
        self.run_once()
        for sql in self.con.log:
            if sql.startswith("DELETE"):
                self.assertTrue(" LIMIT " in sql or " IN (" in sql, sql)
                self.assertTrue("`captured_at`" in sql or "`time`" in sql, sql)


    # ---- MT2009_PLUS_SEBAN_SNAPSHOT_GENTLE_V1
    def test_every_delete_is_small(self):
        self.run_once()
        for sql in self.con.log:
            limit = re.search(r" LIMIT (\d+)$", sql)
            if sql.startswith("DELETE") and limit:
                self.assertLessEqual(int(limit.group(1)), sr.BATCH_MAX, sql)
            if sql.startswith("DELETE") and " IN (" in sql and "NOT IN" not in sql:
                self.assertLessEqual(sql.count("%s"), 1 + sr.KEY_CHUNK * 2, sql[:80])

    def test_deletes_walk_forward(self):
        with patch.object(sr, "BATCH", 50), patch.object(sr, "BATCH_MIN", 50), patch.object(sr, "BATCH_MAX", 50):
            self.run_once()
        starts = [sql for sql in self.con.log if sql.startswith("DELETE FROM player.`web_seban_news_event`")]
        self.assertTrue(all("`time` >= %s AND `time` < %s" in sql for sql in starts))

    def test_pauses_follow_the_statements(self):
        self.run_once()
        self.assertTrue(self.slept)
        self.assertTrue(all(pause >= sr.BATCH_SLEEP for pause in self.slept))

    def test_day_leaves_the_backlog_for_the_night(self):
        before = {name: len(t["rows"]) for name, t in self.con.tables.items()}
        result = self.run_once(**{sr.ENV_HEAVY_HOURS: "3-6"})
        self.assertFalse(result["heavy"])
        self.assertTrue(result["pending"])
        items = result["tables"]["web_seban_item_snapshot"]
        self.assertEqual(items["deleted"] + items["hourly"], 0)
        self.assertIn("delete", items["waiting"])
        self.assertEqual(before["web_seban_item_snapshot"], len(self.con.tables["web_seban_item_snapshot"]["rows"]))
        # The per-character cap (a GROUP BY over the whole table) waits too.
        self.assertIn("cap", result["tables"]["web_seban_gear_event"]["waiting"])
        self.assertFalse([sql for sql in self.con.log if "GROUP BY pid" in sql])
        # The night does it all.
        night = self.now.replace(hour=4)
        result = self.run_once(now=night, **{sr.ENV_HEAVY_HOURS: "3-6"})
        self.assertTrue(result["heavy"])
        self.assertFalse(result["pending"])
        self.assertGreater(result["tables"]["web_seban_item_snapshot"]["deleted"], 0)

    def test_day_does_the_small_tail(self):
        self.run_once()                                   # the backlog, done at "night"
        later = self.now + timedelta(hours=2)
        result = self.run_once(now=later, **{sr.ENV_HEAVY_HOURS: "3-6"})
        self.assertFalse(result["heavy"])
        self.assertFalse(result["tables"]["web_seban_item_snapshot"].get("waiting"))
        self.assertGreater(result["tables"]["web_seban_item_snapshot"]["hourly"], 0)

    def test_busy_database_is_waited_for(self):
        calls = {"n": 0}

        def status():
            calls["n"] += 1
            return {"Threads_running": 40 if calls["n"] <= 3 else 2, "Innodb_history_list_length": 10}
        self.con.status = status
        result = self.run_once()
        self.assertEqual(result["busy_waits"], 3)
        self.assertEqual(self.slept.count(sr.BUSY_PAUSE) >= 3, True)
        self.assertEqual(result["status"], "ok")

    def test_out_of_time_pauses_the_run(self):
        self.con.status = {"Threads_running": 2, "Innodb_history_list_length": 10 ** 9}
        clock = iter(range(0, 10 ** 6, 100))
        with patch.object(sr.time, "monotonic", lambda: next(clock)):
            result = self.run_once(**{sr.ENV_HEAVY_HOURS: "13-14"})
        self.assertEqual(result["status"], "paused")
        self.assertTrue(result["pending"])
        self.assertFalse([sql for sql in self.con.log if sql.startswith("DELETE")])


class ThrottleLogic(unittest.TestCase):
    def test_slow_statements_shrink_the_batch(self):
        t = sr.Throttle(pause=False)
        self.assertEqual(t.batch, sr.BATCH)
        t.adapt(2.0, sr.BATCH, sr.BATCH)
        self.assertLess(t.batch, sr.BATCH * sr.TARGET_SECONDS / 2.0 + 1)
        for _ in range(20):
            t.adapt(5.0, t.batch, t.batch)
        self.assertEqual(t.batch, sr.BATCH_MIN)

    def test_fast_full_statements_grow_it_up_to_the_max(self):
        t = sr.Throttle(pause=False)
        for _ in range(20):
            t.adapt(0.01, t.batch, t.batch)
        self.assertEqual(t.batch, sr.BATCH_MAX)

    def test_short_statements_say_nothing(self):
        t = sr.Throttle(pause=False)
        t.adapt(0.01, 3, t.batch)       # the last few rows: fast, but not full
        self.assertEqual(t.batch, sr.BATCH)

    def test_target_is_met_from_the_measure(self):
        t = sr.Throttle(pause=False)
        t.adapt(0.8, sr.BATCH, sr.BATCH)     # 0.8 ms a row: ~225 rows fit in 0.2 s
        self.assertLessEqual(t.batch * 0.8 / sr.BATCH, sr.TARGET_SECONDS)

    def test_rest_is_proportional(self):
        t = sr.Throttle(pause=False)
        self.assertAlmostEqual(t.rest(0.1), 0.1 * sr.SLEEP_FACTOR)
        self.assertEqual(t.rest(0.0), sr.BATCH_SLEEP)
        self.assertGreaterEqual(t.rest(2.0), max(sr.BUSY_PAUSE, 2.0 * sr.SLEEP_FACTOR))

    def test_execute_measures_and_sleeps(self):
        ticks = iter([10.0, 10.5])
        slept = []
        t = sr.Throttle(pause=True, clock=lambda: next(ticks), sleeper=slept.append)

        class Cur:
            rowcount = 1000

            def execute(self, sql, params=()):
                self.sql = sql

            def fetchall(self):
                return [("Threads_running", "1"), ("Innodb_history_list_length", "5")]
        with patch.object(sr.Throttle, "check_time", lambda self: None):
            self.assertEqual(t.execute(Cur(), "DELETE x", (), 1000), 1000)
        self.assertEqual(slept, [0.5 * sr.SLEEP_FACTOR])
        self.assertLess(t.batch, 1000)

    def test_busy_reasons(self):
        class Cur:
            def __init__(self, rows):
                self.rows = rows

            def execute(self, sql, params=()):
                pass

            def fetchall(self):
                return self.rows
        self.assertIsNone(sr.Throttle.busy(Cur([("Threads_running", "3"), ("Innodb_history_list_length", "10")])))
        self.assertIn("running", sr.Throttle.busy(Cur([("Threads_running", "30")])))
        self.assertIn("purge", sr.Throttle.busy(Cur([("Threads_running", "1"),
                                                      ("Innodb_history_list_length", str(sr.HISTORY_MAX + 1))])))


class HeavyHours(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(sr.heavy_hours({}), sr.DEFAULT_HEAVY_HOURS)
        self.assertEqual(sr.heavy_hours({sr.ENV_HEAVY_HOURS: "2-5"}), (2, 5))
        self.assertEqual(sr.heavy_hours({sr.ENV_HEAVY_HOURS: "0-24"}), (0, 24))
        self.assertEqual(sr.heavy_hours({sr.ENV_HEAVY_HOURS: "23-24"}), (23, 0))
        self.assertEqual(sr.heavy_hours({sr.ENV_HEAVY_HOURS: "nonsense"}), sr.DEFAULT_HEAVY_HOURS)
        self.assertEqual(sr.heavy_hours({sr.ENV_HEAVY_HOURS: "3-30"}), sr.DEFAULT_HEAVY_HOURS)

    def test_window(self):
        at = lambda h, m=0: datetime(2026, 11, 3, h, m)
        self.assertTrue(sr.in_window(at(3), (3, 6)))
        self.assertTrue(sr.in_window(at(5, 59), (3, 6)))
        self.assertFalse(sr.in_window(at(6), (3, 6)))
        self.assertTrue(sr.in_window(at(23, 30), (23, 5)))
        self.assertTrue(sr.in_window(at(1), (23, 5)))
        self.assertFalse(sr.in_window(at(12), (23, 5)))
        self.assertFalse(sr.in_window(at(12), (4, 4)))
        self.assertTrue(sr.in_window(at(12), (0, 24)))
        self.assertEqual(sr.window_seconds_left(at(5, 30), (3, 6)), 1800)
        self.assertEqual(sr.window_seconds_left(at(23), (23, 1)), 7200)
        self.assertEqual(sr.window_seconds_left(at(12), (3, 6)), 0)
        self.assertEqual(sr.seconds_to_window(at(2), (3, 6)), 3600)
        self.assertEqual(sr.seconds_to_window(at(7), (3, 6)), 20 * 3600)
        self.assertIsNone(sr.seconds_to_window(at(7), (4, 4)))

    def test_next_pause(self):
        at = lambda h: datetime(2026, 11, 3, h)
        self.assertEqual(sr.next_pause({"pending": False}, at(4), (3, 6)), sr.RUN_INTERVAL)
        self.assertEqual(sr.next_pause({"pending": True}, at(4), (3, 6)), sr.NIGHT_RERUN)
        self.assertEqual(sr.next_pause({"pending": True}, at(14), (3, 6)), sr.RUN_INTERVAL)
        self.assertEqual(sr.next_pause({"pending": True}, datetime(2026, 11, 3, 2, 50), (3, 6)), 660)
        self.assertEqual(sr.next_pause(None, at(4), (3, 6)), sr.RUN_INTERVAL)


if __name__ == "__main__":
    unittest.main()
