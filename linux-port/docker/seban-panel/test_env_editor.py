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
        self.assertIn("Tryb tylko do odczytu", html)
        self.assertIn("docker compose --profile update up -d updater", html)
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
        for entry in env_schema.SCHEMA:
            self.assertIn('id="env-%s"' % entry["key"], html)
        self.assertNotIn("Tryb tylko do odczytu", html)
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
