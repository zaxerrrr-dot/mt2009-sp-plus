"""MT2009_PLUS_ENV_EDITOR_V1: python3 -m unittest test_env_editor

The panel's half of "Ustawienia serwera (.env)" through Flask's test client,
on a temporary update spool: read-only without a watcher, CSRF, the checks
made before anything is queued (invalid, read-only, risky without the typed
confirmation), the request it leaves for the updater and the status JSON.
Nothing here writes .env - the panel never can."""
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import app as panel

panel.app.config["TESTING"] = True


class EnvEditorRoutes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.spool = Path(self.tmp.name)
        self.patches = [patch.object(panel, "UPDATE_SPOOL", self.spool),
                        patch.object(panel, "settings", return_value={"setup_complete": "1", "auth_enabled": "0"}),
                        patch.object(panel, "db", side_effect=AssertionError("the .env editor must not touch the DB"))]
        for p in self.patches:
            p.start()
        self.client = panel.app.test_client()
        self.client.get("/advanced/server-env")
        with self.client.session_transaction() as sess:
            self.csrf = sess["seban_update_csrf"]

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def ready(self, values=None):
        (self.spool / "watcher").touch()
        (self.spool / "watcher.features").write_text("features=env-editor-v1\nscript=1\nupdates=0\n")
        current = {"features": ["env-editor-v1"], "time": int(time.time()),
                   "values": values or {"PLAYERBOT_AUTOSPAWN_COUNT": "350", "M2_AREZZO": "0", "M2_TZ": "UTC"},
                   "secrets": {"M2_DB_PASSWORD": "set", "M2_ADMINPAGE_PASSWORD": "set", "M2_PANEL_PASSWORD": "unset"},
                   "present": ["PLAYERBOT_AUTOSPAWN_COUNT", "M2_AREZZO", "M2_TZ"], "overridden": ["M2_TZ"]}
        (self.spool / "env.current").write_text(json.dumps(current))

    def save(self, changes, confirm="", csrf=None):
        return self.client.post("/advanced/server-env", data={"env_csrf": self.csrf if csrf is None else csrf,
                                                               "changes": json.dumps(changes), "confirm": confirm})

    def test_read_only_without_watcher(self):
        page = self.client.get("/advanced/server-env")
        self.assertEqual(page.status_code, 200)
        html = page.get_data(as_text=True)
        self.assertIn("Aktualizator nie działa", html)
        self.assertIn("docker compose --profile update up -d --build updater", html)
        self.assertIn("sh linux-port/tools/update.sh updater", html)
        self.assertIn("start-server.ps1 -UpdaterOnly", html)
        self.assertIn('id="env-recheck"', html)
        self.assertIn("PLAYERBOT_AUTOSPAWN_COUNT", html)
        response = self.save({"M2_AREZZO": "1"})
        self.assertEqual(response.status_code, 409)
        self.assertFalse((self.spool / "env.request").exists())

    def test_old_watcher_is_named(self):
        (self.spool / "watcher").touch()
        html = self.client.get("/advanced/server-env").get_data(as_text=True)
        self.assertIn("starszej wersji", html)

    def test_page_shows_every_field_and_no_secret(self):
        self.ready()
        html = self.client.get("/advanced/server-env").get_data(as_text=True)
        import env_schema
        hidden = {section["id"] for section in env_schema.SECTIONS if section.get("hidden")}
        for entry in env_schema.SCHEMA:
            if entry["section"] in hidden:
                self.assertNotIn('id="env-%s"' % entry["key"], html)   # Gra w przeglądarce: off the page
            else:
                self.assertIn('id="env-%s"' % entry["key"], html)
        self.assertNotIn("Aktualizator nie działa", html)
        self.assertIn("nadpisane w override", html)
        self.assertIn("● ustawione", html)
        self.assertIn("Ustawienia serwera (.env)", html)

    def test_csrf_is_required(self):
        self.ready()
        self.assertEqual(self.save({"M2_AREZZO": "1"}, csrf="nope").status_code, 403)
        self.assertFalse((self.spool / "env.request").exists())

    def test_invalid_readonly_and_risky_are_refused(self):
        self.ready()
        bad = self.save({"PLAYERBOT_AUTOSPAWN_COUNT": "99999", "M2_AREZZO": "1"})
        self.assertEqual(bad.status_code, 400)
        self.assertIn("PLAYERBOT_AUTOSPAWN_COUNT", bad.get_json()["errors"])
        self.assertEqual(self.save({"M2_DB_PASSWORD": "abcdef"}).status_code, 400)
        self.assertEqual(self.save({"M2_UPDATE_STACK_DIR": "/"}).status_code, 400)
        risky = self.save({"M2_SEBAN_PANEL_PORT": "7795"})
        self.assertEqual(risky.status_code, 400)
        self.assertIn("ZMIENIAM", risky.get_json()["message"])
        self.assertEqual(self.save({"M2_AREZZO": "0"}).status_code, 400)  # nothing changes
        self.assertFalse((self.spool / "env.request").exists())

    def test_valid_change_is_queued_for_the_updater(self):
        self.ready()
        response = self.save({"PLAYERBOT_AUTOSPAWN_COUNT": "900", "M2_AREZZO": "1", "M2_SEBAN_PANEL_PORT": "7795",
                              "M2_SEBAN_SESSION_SECRET": "newSessionKey_1"}, confirm="zmieniam")
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        request = json.loads((self.spool / "env.request").read_text())
        self.assertRegex(request["id"], r"^env-[0-9a-f]+$")
        self.assertEqual(request["changes"], {"PLAYERBOT_AUTOSPAWN_COUNT": "900", "M2_AREZZO": "1",
                                              "M2_SEBAN_PANEL_PORT": "7795", "M2_SEBAN_SESSION_SECRET": "newSessionKey_1"})
        status = json.loads((self.spool / "env.status").read_text())
        self.assertEqual(status["state"], "queued")
        self.assertNotIn("newSessionKey_1", (self.spool / "env.status").read_text())
        self.assertIn("game", status["services"])
        # A second save waits for the first one.
        self.assertEqual(self.save({"M2_SEONHAE": "1"}).status_code, 409)
        data = self.client.get("/advanced/server-env/status").get_json()
        self.assertTrue(data["ready"])
        self.assertEqual(data["status"]["state"], "queued")
        self.assertTrue(data["status"]["busy"])
        self.assertNotIn("M2_DB_PASSWORD", data["values"])

    def test_status_after_the_updater_answered(self):
        self.ready()
        (self.spool / "env.status").write_text(json.dumps({"id": "env-1", "state": "ok", "time": int(time.time()),
                                                            "message": "Zapisano", "results": {}}))
        data = self.client.get("/advanced/server-env/status").get_json()
        self.assertFalse(data["status"]["busy"])
        self.assertEqual(self.save({"M2_SEONHAE": "1"}).status_code, 200)

    def test_nav_links_the_page(self):
        html = self.client.get("/advanced/server-env").get_data(as_text=True)
        self.assertIn("/advanced/server-env", html)


if __name__ == "__main__":
    unittest.main()


class FakeWorld:
    """player.quest flags and web_admin_queue, enough for the live switches."""
    def __init__(self, flags=None, answer="done"):
        self.flags = dict(flags or {})
        self.queue = {}
        self.answer = answer

    def connect(self):
        world = self

        class Cursor:
            lastrowid = 0
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def execute(self, sql, params=()):
                self.rows = []
                if sql.startswith("SELECT szName"):
                    self.rows = [{"szName": k, "lValue": v} for k, v in world.flags.items() if k in params]
                elif sql.startswith("REPLACE INTO player.quest"):
                    world.flags[params[0]] = int(params[1])
                elif sql.startswith("INSERT INTO player.web_admin_queue"):
                    qid = len(world.queue) + 1
                    world.queue[qid] = {"cmd": params[0], "arg1": params[1], "status": "pending"}
                    self.lastrowid = qid
                elif sql.startswith("SELECT id, status"):
                    for qid in params:
                        if world.answer and world.queue[qid]["status"] == "pending":
                            world.queue[qid]["status"] = world.answer
                    self.rows = [{"id": q, "status": world.queue[q]["status"]} for q in params]
                elif sql.startswith("UPDATE player.web_admin_queue"):
                    for qid in params:
                        if world.queue[qid]["status"] == "pending":
                            world.queue[qid]["status"] = "cancelled"
            def fetchall(self): return self.rows

        class Connection:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def cursor(self): return Cursor()
        return Connection()


class LiveSwitches(EnvEditorRoutes):
    """MT2009_PLUS_ENV_LIVE_V1: without the updater, Arezzo / Seon-Hae /
    alchemy / sashes are switched in the game; .env waits in env.pending."""
    def setUp(self):
        super().setUp()
        self.world = FakeWorld({"mt2009_arezzo_closed": 1, "m2_seonhae_on": 0, "m2_seonhae_wait_min": 30,
                                "m2_alchemy_off": 0, "m2_sash_off": 0})
        self.db_patch = patch.object(panel, "db", side_effect=self.world.connect)
        self.db_patch.start()
        self.sleep = patch("env_editor.time.sleep")
        self.sleep.start()

    def tearDown(self):
        self.sleep.stop()
        self.db_patch.stop()
        super().tearDown()

    def test_read_only_without_watcher(self):
        html = self.client.get("/advanced/server-env").get_data(as_text=True)
        self.assertIn("działa od razu", html)
        self.assertIn('class="envf envf-live', html)

    def test_live_switch_without_updater(self):
        response = self.save({"M2_AREZZO": "1", "M2_SASHES": "0"})
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        body = response.get_json()
        self.assertTrue(body["ok"] and body["live"])
        self.assertEqual(self.world.flags["mt2009_arezzo_closed"], 0)
        self.assertEqual(self.world.flags["m2_sash_off"], 1)
        self.assertEqual(self.world.flags["m2_alchemy_off"], 0)
        cmds = sorted((q["cmd"], q["arg1"]) for q in self.world.queue.values())
        self.assertEqual(cmds, [("AREZZO", "1"), ("RARE", "1,0")])
        self.assertIn("od razu", body["status"]["message"])
        pending = json.loads((self.spool / "env.pending").read_text())["values"]
        self.assertEqual(pending, {"M2_AREZZO": "1", "M2_SASHES": "0"})
        self.assertFalse((self.spool / "env.request").exists())
        self.assertEqual(json.loads((self.spool / "env.status").read_text())["source"], "live")

    def test_seonhae_keeps_its_wait(self):
        self.assertEqual(self.save({"M2_SEONHAE": "1"}).status_code, 200)
        self.assertEqual([q["arg1"] for q in self.world.queue.values()], ["1,30"])

    def test_teleport_map_switch(self):
        # MT2009_PLUS_TELEPORT_MAP_V1: no row reads as off; on writes the flag and a TPMAP row.
        self.assertEqual(panel.env_editor.live_values_from_flags({})["M2_TELEPORT_MAP"], "0")
        self.assertEqual(self.save({"M2_TELEPORT_MAP": "1"}).status_code, 200)
        self.assertEqual(self.world.flags["m2_teleport_map_on"], 1)
        self.assertEqual([(q["cmd"], q["arg1"]) for q in self.world.queue.values()], [("TPMAP", "1")])

    def test_game_down_is_said_and_row_cancelled(self):
        self.world.answer = None
        with patch("env_editor.LIVE_WAIT", 0.0):
            body = self.save({"M2_AREZZO": "1"}).get_json()
        self.assertTrue(body["ok"])
        self.assertIn("najbliższym starcie", body["status"]["message"])
        self.assertEqual([q["status"] for q in self.world.queue.values()], ["cancelled"])

    def test_other_keys_still_need_the_updater(self):
        response = self.save({"M2_AREZZO": "1", "PLAYERBOT_AUTOSPAWN_COUNT": "500"})
        self.assertEqual(response.status_code, 409)
        self.assertIn("PLAYERBOT_AUTOSPAWN_COUNT", response.get_json()["message"])
        self.assertEqual(self.world.queue, {})
        self.assertFalse((self.spool / "env.pending").exists())

    def test_same_as_live_value_is_nothing(self):
        response = self.save({"M2_ALCHEMY": "1"})
        self.assertEqual(response.status_code, 400)

    def test_with_updater_the_request_is_queued_as_before(self):
        self.ready()
        response = self.save({"M2_AREZZO": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue((self.spool / "env.request").exists())
        self.assertEqual(self.world.queue, {})

    # inherited tests that assume no database
    test_valid_change_is_queued_for_the_updater = None
    test_invalid_readonly_and_risky_are_refused = None
    test_status_after_the_updater_answered = None
    test_page_shows_every_field_and_no_secret = None
    test_old_watcher_is_named = None
    test_csrf_is_required = None
    test_nav_links_the_page = None
