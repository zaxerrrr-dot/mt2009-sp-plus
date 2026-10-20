"""MT2009_PLUS_PANEL_DB_GUARD_V1 + MT2009_PLUS_DB_LOG_RETENTION_V1:
python3 -m unittest test_panel_db_guard

Needs the panel's Python packages (Flask, PyMySQL): run it in the panel's
image. The unit part uses no database. The integration part runs only with
SEBAN_IT_DB_HOST set - a throwaway MariaDB loaded with a copy of a world
(DB_USER/DB_PASSWORD as for the panel) - and checks against real tables:

    docker run --rm --network <net> -e SEBAN_IT_DB_HOST=<db> -e DB_HOST=<db> \\
      -e DB_USER=metin2 -e DB_PASSWORD=... -v $PWD:/w -w /w <panel image> \\
      python -m unittest test_panel_db_guard
"""
import os
import unittest
from datetime import datetime
from unittest.mock import patch

os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")

import pymysql

import app as panel
import log_maintenance

panel.app.config["TESTING"] = True
NO_AUTH = {"setup_complete": "1", "auth_enabled": "0"}


def timeout_error():
    return pymysql.err.OperationalError(1969, "Query execution was interrupted (max_statement_time exceeded)")


class StatementLimit(unittest.TestCase):
    def test_selects_get_the_limit(self):
        with patch.object(panel, "DB_STATEMENT_TIMEOUT", 2.0):
            with panel.app.test_request_context("/"):
                self.assertEqual(panel.limited_sql("SELECT 1"), "SET STATEMENT max_statement_time=2 FOR SELECT 1")
                self.assertEqual(panel.limited_sql("  select 1"), "SET STATEMENT max_statement_time=2 FOR   select 1")
                self.assertTrue(panel.limited_sql("WITH a AS (SELECT 1) SELECT * FROM a").startswith("SET STATEMENT"))
                self.assertTrue(panel.limited_sql("(SELECT 1) UNION (SELECT 2)").startswith("SET STATEMENT"))

    def test_writes_are_never_cut(self):
        with panel.app.test_request_context("/"):
            for sql in ("INSERT INTO t SELECT 1", "UPDATE t SET a=1", "DELETE FROM t", "REPLACE INTO t VALUES (1)",
                        "CREATE TABLE t (a INT)", "SET SESSION x=1"):
                self.assertEqual(panel.limited_sql(sql), sql)

    def test_background_and_zero(self):
        with patch.object(panel, "DB_STATEMENT_TIMEOUT", 2.0), patch.object(panel, "DB_BACKGROUND_TIMEOUT", 300.0):
            with panel.app.test_request_context("/"):
                with panel.background_queries():
                    self.assertIn("max_statement_time=300 ", panel.limited_sql("SELECT 1"))
                with panel.background_queries(0):
                    self.assertEqual(panel.limited_sql("SELECT 1"), "SELECT 1")
                self.assertIn("max_statement_time=2 ", panel.limited_sql("SELECT 1"))
            # A thread outside any request (the deferred dashboard refresh).
            self.assertIn("max_statement_time=300 ", panel.limited_sql("SELECT 1"))


class BlockGuard(unittest.TestCase):
    def setUp(self):
        panel._db_block_stats.clear()

    def test_fallback_and_metric(self):
        def failing(*_args):
            raise timeout_error()
        with panel.app.test_request_context("/players"):
            self.assertEqual(panel.db_block("t.block", "fallback", failing, 1), "fallback")
            self.assertEqual(panel.db_block("t.block", lambda: [1], failing), [1])
        found = panel.db_block_failures()
        self.assertEqual(found[0]["block"], "t.block")
        self.assertEqual(found[0]["errno"], 1969)
        self.assertEqual(found[0]["count"], 2)

    def test_connection_lost_is_guarded_too(self):
        def lost():
            raise pymysql.err.OperationalError(2013, "Lost connection to server during query")
        self.assertIsNone(panel.db_block("t.lost", None, lost))
        def interface():
            raise pymysql.err.InterfaceError(0, "")
        self.assertEqual(panel.db_block("t.iface", 0, interface), 0)

    def test_crashed_table_still_reaches_its_page(self):
        def crashed():
            raise pymysql.err.OperationalError(1194, "Table './log/log' is marked as crashed")
        with self.assertRaises(pymysql.err.OperationalError):
            panel.db_block("t.crashed", None, crashed)

    def test_success_passes_through(self):
        self.assertEqual(panel.db_block("t.ok", None, lambda a, b=0: a + b, 1, b=2), 3)


class PagesSurviveTimeouts(unittest.TestCase):
    def setUp(self):
        self.client = panel.app.test_client()

    def test_players_without_plus9_marks(self):
        roster = [{"id": 7, "name": "Bot", "level": 10, "job": 0, "map_index": 1, "gold": 0, "playtime": 0,
                   "last_play": None, "empire": 1, "is_sidekick": 0}]

        failed = []

        def fake_rows(sql, params=()):
            if "FROM player.player p" in sql and "LIMIT 250" in sql:
                return roster
            if "FROM player.item i" in sql:  # the +9 marks' batch
                failed.append(sql)
                raise timeout_error()
            return []
        panel._db_block_stats.clear()
        with patch.object(panel, "settings", return_value=NO_AUTH), \
             patch.object(panel, "rows", side_effect=fake_rows), \
             patch.object(panel, "full_plus9_badges_enabled", return_value=True), \
             patch.object(panel, "live_statuses", return_value={}), \
             patch.object(panel, "legend_tiers", return_value={}), \
             patch.object(panel, "plus9_vnums", return_value=frozenset({19})):
            panel._plus9_ids_cache.clear()
            response = self.client.get("/players")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Bot", response.get_data(as_text=True))
        self.assertTrue(failed)
        self.assertEqual(panel.db_block_failures()[0]["block"], "players.full_plus9")
        self.assertEqual(panel.db_block_failures()[0]["route"], "/players")

    def test_a_timeout_elsewhere_is_a_503_page_not_a_bare_500(self):
        with patch.object(panel, "settings", return_value=NO_AUTH), \
             patch.object(panel, "rows", side_effect=timeout_error()), \
             patch.object(panel, "live_statuses", return_value={}):
            response = self.client.get("/players")
        self.assertEqual(response.status_code, 503)
        self.assertIn("chwilowo", response.get_data(as_text=True))


class Plus9Marks(unittest.TestCase):
    def test_full_set_only(self):
        equipped = [{"owner_id": 1, "pos": pos, "vnum": 19} for pos in (0, 1, 2, 3, 4, 5, 6, 10)]
        equipped += [{"owner_id": 2, "pos": pos, "vnum": 19} for pos in (0, 1, 2, 3, 4, 5, 6)]
        equipped += [{"owner_id": 2, "pos": 10, "vnum": 18}]
        calls = []

        def fake_rows(sql, params=()):
            calls.append(sql)
            self.assertNotIn("item_proto", sql)
            return [row for row in equipped if row["owner_id"] in params]
        panel._plus9_ids_cache.clear()
        with patch.object(panel, "rows", side_effect=fake_rows), \
             patch.object(panel, "full_plus9_badges_enabled", return_value=True), \
             patch.object(panel, "plus9_vnums", return_value=frozenset({19})):
            self.assertEqual(panel.full_plus9_equipment_ids(range(1, 251)), {1})
            self.assertEqual(len(calls), 3)  # batches of 100
            panel.full_plus9_equipment_ids(range(1, 251))
            self.assertEqual(len(calls), 3)  # the second answer is the cached one


class SharedLists(unittest.TestCase):
    def test_gear_kinds_match(self):
        self.assertEqual(set(log_maintenance.GEAR_HOWS), set(panel.GEAR_HISTORY_HOWS))

    def test_retention_values(self):
        self.assertEqual(log_maintenance.retention_days("0"), 0)
        self.assertEqual(log_maintenance.retention_days("14"), 14)
        self.assertEqual(log_maintenance.retention_days("7 "), 7)
        self.assertEqual(log_maintenance.retention_days("366"), 0)
        self.assertEqual(log_maintenance.retention_days("-3"), 0)
        self.assertEqual(log_maintenance.retention_days("x"), 0)
        self.assertEqual(log_maintenance.retention_days(""), 0)

    def test_cutoff_keeps_whole_days(self):
        self.assertEqual(log_maintenance.cutoff_for(datetime(2026, 10, 20, 5, 0), 14), datetime(2026, 10, 6))
        self.assertEqual(log_maintenance.cutoff_for(datetime(2026, 10, 20, 23, 59), 7), datetime(2026, 10, 13))


@unittest.skipUnless(os.environ.get("SEBAN_IT_DB_HOST"), "SEBAN_IT_DB_HOST not set (throwaway database)")
class AgainstACopyOfAWorld(unittest.TestCase):
    def setUp(self):
        self.client = panel.app.test_client()
        panel._logstat_cache["at"] = 0.0

    def test_the_limit_really_stops_a_select(self):
        with patch.object(panel, "DB_STATEMENT_TIMEOUT", 1.0), panel.app.test_request_context("/"):
            started = datetime.now()
            self.assertEqual(panel.db_block("it.sleep", "stopped", panel.rows, "SELECT SLEEP(5) AS s"), "stopped")
            self.assertLess((datetime.now() - started).total_seconds(), 4)

    def _pid_with_history(self):
        found = panel.one("SELECT pid FROM player.web_seban_gear_event GROUP BY pid ORDER BY COUNT(*) DESC LIMIT 1")
        if found:
            return int(found["pid"])
        return int(panel.one("SELECT id FROM player.player ORDER BY level DESC LIMIT 1")["id"])

    def test_profile_survives_a_gear_history_timeout(self):
        pid = self._pid_with_history()
        with patch.object(panel, "settings", return_value=NO_AUTH), \
             patch.object(panel, "_gear_history_rows", side_effect=timeout_error()):
            response = self.client.get(f"/player/{pid}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Historia chwilowo niedostępna", response.get_data(as_text=True))

    def test_profile_and_list_render(self):
        pid = self._pid_with_history()
        with patch.object(panel, "settings", return_value=NO_AUTH):
            self.assertEqual(self.client.get(f"/player/{pid}").status_code, 200)
            self.assertEqual(self.client.get("/players").status_code, 200)
            self.assertEqual(self.client.get("/diagnostics/db-logs").status_code, 200)

    def test_plus9_marks_match_the_old_join(self):
        roster = [int(r["id"]) for r in panel.rows("SELECT id FROM player.player ORDER BY level DESC, exp DESC LIMIT 250")]
        marks = ",".join(["%s"] * len(roster))
        old = panel.rows(f"""SELECT i.owner_id,i.pos,COALESCE(p.locale_name,CONCAT('VNUM ',i.vnum)) AS item_name
          FROM player.item i LEFT JOIN player.item_proto p ON p.vnum=i.vnum
          WHERE i.owner_id IN ({marks}) AND i.window='EQUIPMENT' AND i.pos IN (0,1,2,3,4,5,6,10)""", roster)
        slots = {}
        for item in old:
            if panel.re.search(r"\+9\s*$", panel.game_text(item.get("item_name") or "")):
                slots.setdefault(int(item["owner_id"]), set()).add(int(item["pos"]))
        expected = {pid for pid, positions in slots.items() if positions == set(panel.PLUS9_EQUIPMENT_SLOTS)}
        panel._plus9_ids_cache.clear()
        with patch.object(panel, "full_plus9_badges_enabled", return_value=True):
            self.assertEqual(panel.full_plus9_equipment_ids(roster), expected)


if __name__ == "__main__":
    unittest.main()
