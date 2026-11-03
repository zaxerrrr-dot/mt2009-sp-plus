"""MT2009_PLUS_SERVER_CONFIG_V1: python3 -m unittest test_server_config

"Konfiguracja serwera": the shipped server_profiles.txt is valid for the panel
(every .env value passes env_schema, every event row is one the planner
knows), the parser refuses what a profile must never carry (passwords,
ports and addresses, unknown lines), the plan says exactly what changes,
the calendar is added without duplicates, and the page applies a profile
only through the existing paths: CSRF and the typed confirmation, live
switches through env_editor.apply_live + env.pending, the rest as one
env.request for the updater, rates through queue_rate_restart, rows through
write_events, and a history entry. Also the chest drop's 7th column
(MT2009_PLUS_CHEST_DROP_TARGET_V1) through read_events / write_events and the
monsters' percent switches of the .env editor."""
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import app as panel
import env_editor
import env_schema
import server_config

panel.app.config["TESTING"] = True


class ShippedProfiles(unittest.TestCase):
    def test_file_is_valid(self):
        data = server_config.load()
        server_config.check_event_kinds(data["profiles"], panel.EVENT_KINDS, panel.EVENT_KEYED_KINDS)
        ids = [p["id"] for p in data["profiles"]]
        self.assertEqual(ids, ["mt2009", "clean_easy", "clean_hard", "sapphire"])
        for profile in data["profiles"]:
            for key, value in profile["env"].items():
                self.assertIsNone(env_schema.validate(key, value), (profile["id"], key, value))
                self.assertFalse(env_schema.BY_KEY[key].get("dangerous"))
        for group in data["groups"]:
            for key in group["keys"]:
                self.assertIn(key, env_schema.BY_KEY)
            for link in group["links"]:
                self.assertIn(link["endpoint"], panel.app.view_functions)

    def test_sapphire_calendar(self):
        # MT2009_PLUS_SERVER_CONFIG_V1 (the owner, 3 November 2026): the original Sapphire week (pl-wiki "Eventy")
        # exactly - four slots a day, the fishing puzzle event (Wednesday 0-12, Saturday 12-16) left out, every item
        # a 7% drop from every Metin and boss.
        sapphire = next(p for p in server_config.load()["profiles"] if p["id"] == "sapphire")
        rows = sapphire["events"]
        slots = ("00:00", "12:00", "16:00", "20:00", "24:00")
        week = {
            1: (71094, 100300, 25040, 71187),       # Rada Pustelnika, Zielona Smocza Fasola, Zwoj Blog., Nugget (ziel.)
            2: (72724, 51501, 72351, 76014),        # Eliksir Slonca (S), Cor Draconis, Male Blogoslawienstwo, Zaczarowanie (n)
            3: (None, 70024, 71094, "superstone"),  # fishing, Kula Blogoslawienstwa, Rada Pustelnika, Super Kamienie
            4: (72728, 72351, 51501, 76013),        # Eliksir Ksiezyca (S), Male Blog., Cor Draconis, Wzmocnienie (n)
            5: (100300, 76014, "superstone", 51501),
            6: (25040, None, 53235, 50011),         # Zwoj Blog., fishing, Robin (1d), Szkatulka Blasku Ksiezyca
            7: (71001, 76013, 71001, 71012),        # Zwoj Egzorcyzmu, Wzmocnienie (n), Zwoj Egzorcyzmu, Ksiazka Lidera
        }
        want = []
        for day, items in sorted(week.items()):
            for slot, what in enumerate(items):
                if what is None:
                    continue
                row = {"days": [day], "start": slots[slot], "end": slots[slot + 1], "on": True}
                if what == "superstone":
                    row.update(kind="superstone", value=1, map=0)
                else:
                    row.update(kind="chestdrop", value=70, map=what, target=1)
                want.append(row)
        self.assertEqual(rows, want)
        self.assertEqual(len(rows), 26)
        self.assertNotIn(990071, [r["map"] for r in rows])  # no item of its own invented
        self.assertLessEqual(len(rows), server_config.EVENT_ROWS_MAX)
        self.assertEqual(sapphire["env"]["M2_MONSTER_ATTACK"], "80")
        self.assertEqual(sapphire["rates"], {"exp": 100, "drop": 150, "yang": 100})


class Parser(unittest.TestCase):
    def bad(self, body):
        with self.assertRaises(server_config.ProfileError):
            server_config.parse("[profile x]\ntitle = X\n" + body + "\n")

    def test_refuses_what_a_profile_must_not_carry(self):
        self.bad("env M2_DB_PASSWORD = abc")          # a secret
        self.bad("env M2_PUBLIC_ADDRESS = 1.2.3.4")   # an address: risky, never a profile's
        self.bad("env M2_AUTH_PORT = 11000")          # a port
        self.bad("env M2_DIFFICULTY = brutal")        # not a value the schema knows
        self.bad("env M2_NOT_A_KEY = 1")
        self.bad("rate yang = 5000")
        self.bad("event chestdrop 8 00:00 12:00 70 51501")
        self.bad("event chestdrop 1 24:00 12:00 70 51501")
        self.bad("event chestdrop 1 00:00 12:00 70 51501 5")
        self.bad("env M2_DIFFICULTY = easy\nrm -rf /")
        with self.assertRaises(server_config.ProfileError):
            server_config.parse("[profile empty]\ntitle = Nic\n")
        with self.assertRaises(server_config.ProfileError):
            server_config.parse("[profile a]\nrate exp = 100\n[profile a]\nrate exp = 100\n")

    def test_event_kinds_checked_against_the_planner(self):
        data = server_config.parse("[profile a]\nevent nosuch * 00:00 01:00 0\n")
        with self.assertRaises(server_config.ProfileError):
            server_config.check_event_kinds(data["profiles"], panel.EVENT_KINDS, panel.EVENT_KEYED_KINDS)
        data = server_config.parse("[profile a]\nevent flower * 00:00 01:00 0 5\n")
        with self.assertRaises(server_config.ProfileError):
            server_config.check_event_kinds(data["profiles"], panel.EVENT_KINDS, panel.EVENT_KEYED_KINDS)

    def test_plan_and_merge(self):
        profile = server_config.parse("[profile a]\nenv M2_DIFFICULTY = hard\nenv M2_MONSTER_HP = 100\n"
                                      "rate drop = 150\nevent chestdrop 1 00:00 12:00 70 51501 1\n")["profiles"][0]
        existing = [{"kind": "chestdrop", "days": [1], "start": "00:00", "end": "12:00", "value": 70, "map": 51501,
                     "on": False, "target": 1}]
        result = server_config.plan(profile, {"M2_DIFFICULTY": "easy", "M2_MONSTER_HP": "default"},
                                    {"exp": 100, "drop": 100, "yang": 100}, existing)
        # default and 100 are the same health: only the difficulty changes.
        self.assertEqual([c["key"] for c in result["env"]], ["M2_DIFFICULTY"])
        self.assertEqual(result["rates"], [{"name": "drop", "old": 100, "new": 150}])
        self.assertEqual(result["events"], 0)  # the same row, switched off, is not added again
        rows, added = server_config.merge_events([], profile["events"] * 2)
        self.assertEqual(added, 1)

    def test_monster_percent(self):
        self.assertEqual(env_schema.monster_percent("default"), 100)
        self.assertEqual(env_schema.monster_percent("easy"), 80)
        self.assertEqual(env_schema.monster_percent("5"), 10)
        self.assertEqual(env_schema.monster_percent("80%"), 80)
        self.assertIsNone(env_schema.monster_percent("hard"))
        self.assertEqual(env_editor.live_values_from_flags({"m2_mob_attack": 80})["M2_MONSTER_ATTACK"], "80")
        self.assertEqual(env_editor.live_values_from_flags({})["M2_MONSTER_HP"], "default")


class FakeCursor:
    def __init__(self, log):
        self.log, self.lastrowid = log, 0

    def execute(self, sql, args=None):
        self.log.append((sql, args))
        self.lastrowid += 1

    def fetchall(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConnection:
    def __init__(self, log):
        self.log = log

    def cursor(self):
        return FakeCursor(self.log)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Routes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.spool = Path(self.tmp.name)
        self.events_file = self.spool / "playerbot_events.tsv"
        self.rates_called, self.sql = [], []
        self.patches = [patch.object(panel, "UPDATE_SPOOL", self.spool),
                        patch.object(panel, "EVENTS_FILE", self.events_file),
                        patch.object(panel, "RATES_SPOOL", self.spool),
                        patch.object(panel, "settings", return_value={"setup_complete": "1", "auth_enabled": "0"}),
                        patch.object(panel, "db", side_effect=lambda: FakeConnection(self.sql)),
                        patch.object(panel, "read_rates", return_value={"exp": 100, "drop": 100, "yang": 100}),
                        patch.object(panel, "queue_rate_restart", side_effect=self.rates_called.append),
                        patch.object(panel, "restart_in_flight", return_value=False)]
        for p in self.patches:
            p.start()
        self.client = panel.app.test_client()
        self.client.get("/advanced/server-config")
        with self.client.session_transaction() as sess:
            self.csrf = sess["seban_update_csrf"]

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def ready(self, values=None):
        (self.spool / "watcher").touch()
        (self.spool / "watcher.features").write_text("features=env-editor-v1\n")
        (self.spool / "env.current").write_text(json.dumps({
            "features": ["env-editor-v1"], "time": int(time.time()), "schema_version": env_schema.SCHEMA_VERSION,
            "values": values or {"M2_BONUS_MODE": "mt2009", "M2_DIFFICULTY": "easy", "M2_MONSTER_HP": "default",
                                 "M2_MONSTER_ATTACK": "default", "M2_STARTER_CHEST": "1", "M2_MLODZI_BOHATEROWIE": "1"},
            "secrets": {}, "present": [], "overridden": []}))

    def apply(self, profile, parts=("env", "rates", "events"), confirm="ZASTOSUJ", csrf=None):
        form = {"config_csrf": self.csrf if csrf is None else csrf, "profile": profile, "confirm": confirm}
        for part in parts:
            form["part_" + part] = "1"
        return self.client.post("/advanced/server-config/apply", data=form)

    def test_page_lists_profiles_and_groups(self):
        html = self.client.get("/advanced/server-config").get_data(as_text=True)
        for text in ("SAPPHIRE", "CLEAN GLOBAL EASY", "CLEAN GLOBAL HARD", "Świat i trudność", "Siła ataku potworów",
                     "Wybierz konfigurację świata"):
            self.assertIn(text, html)

    def test_csrf_and_confirmation(self):
        self.ready()
        self.apply("sapphire", csrf="nope")
        self.apply("sapphire", confirm="tak")
        self.assertFalse((self.spool / "env.request").exists())
        self.assertEqual(self.rates_called, [])
        self.assertFalse(self.events_file.exists())

    def test_apply_sapphire_through_the_existing_paths(self):
        self.ready()
        with patch.object(env_editor, "apply_live", return_value={"MOB_HP": "done", "MOB_ATTACK": "done"}) as live:
            self.apply("sapphire")
        live.assert_called_once()
        self.assertEqual(live.call_args[0][1], {"M2_MONSTER_HP": "80", "M2_MONSTER_ATTACK": "80"})
        pending = json.loads((self.spool / "env.pending").read_text())["values"]
        self.assertEqual(pending, {"M2_MONSTER_HP": "80", "M2_MONSTER_ATTACK": "80"})
        request = json.loads((self.spool / "env.request").read_text())
        self.assertEqual(request["changes"], {"M2_BONUS_MODE": "global"})
        self.assertEqual(self.rates_called, [{"exp": 100, "drop": 150, "yang": 100}])
        rows, _nows = panel.read_events()
        self.assertEqual(len(rows), 26)
        text = self.events_file.read_text()
        self.assertIn("chestdrop\t4\t00:00\t12:00\t70\t72728\t1\n", text)
        self.assertIn("chestdrop\t6\t20:00\t24:00\t70\t50011\t1\n", text)
        self.assertIn("chestdrop\t2\t16:00\t20:00\t70\t72351\t1\n", text)
        history = json.loads((self.spool / server_config.HISTORY_FILE).read_text())
        self.assertEqual(history[-1]["profile"], "sapphire")
        self.assertEqual(json.loads((self.spool / server_config.STATE_FILE).read_text())["applied"], "sapphire")
        # Again: the calendar is not added twice.
        self.rates_called.clear()
        (self.spool / "env.request").unlink()
        with patch.object(env_editor, "apply_live", return_value={}):
            self.apply("sapphire", parts=("events",))
        self.assertEqual(len(panel.read_events()[0]), 26)

    def test_without_updater_only_live_parts(self):
        # No watcher: a profile with a queued .env change is refused whole.
        with patch.object(env_editor, "apply_live", return_value={}) as live:
            self.apply("clean_hard")
        live.assert_not_called()
        self.assertFalse((self.spool / "env.request").exists())
        self.assertEqual(self.rates_called, [])
        # Rates and the calendar alone need no updater.
        self.apply("sapphire", parts=("rates", "events"))
        self.assertEqual(self.rates_called, [{"exp": 100, "drop": 150, "yang": 100}])
        self.assertEqual(len(panel.read_events()[0]), 26)

    def test_dismiss_hides_the_reminder(self):
        self.assertIn("Wybierz konfigurację świata", self.client.get("/advanced/server-config").get_data(as_text=True))
        self.client.post("/advanced/server-config/dismiss", data={"config_csrf": self.csrf})
        self.assertNotIn("Wybierz konfigurację świata", self.client.get("/advanced/server-config").get_data(as_text=True))


class ChestDropTarget(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "playerbot_events.tsv"
            path.write_text("chestdrop\t1\t00:00\t12:00\t70\t51501\t1\nchestdrop\t2\t00:00\t12:00\t70\t50011\n"
                            "chestdrop\t3\t00:00\t12:00\t70\t50011\t7\nzuo\t5\t21:00\t22:00\t8\t0\n")
            with patch.object(panel, "EVENTS_FILE", path), patch.object(panel, "RATES_SPOOL", Path(tmp)):
                rows, nows = panel.read_events()
                self.assertEqual([r.get("target") for r in rows], [1, 0, 0, None])
                panel.write_events(rows, nows, {"bots": 50})
                text = path.read_text()
        self.assertIn("chestdrop\t1\t00:00\t12:00\t70\t51501\t1\n", text)
        self.assertIn("chestdrop\t2\t00:00\t12:00\t70\t50011\n", text)
        self.assertIn("zuo\t5\t21:00\t22:00\t8\t0\n", text)


if __name__ == "__main__":
    unittest.main()
