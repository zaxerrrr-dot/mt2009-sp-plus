"""MT2009_PLUS_ENV_EDITOR_V1: python3 -m unittest test_env_apply (in linux-port/tools)

env_apply.py on a temporary server folder: a copy of .env.example with
comments, CRLF-free and CRLF variants, a fake `docker' that records what it
was asked to do. Checks that only the listed lines change (comments, order and
every other byte stay), missing keys are appended, invalid and read-only
values are refused without touching the file, secrets never appear in what
the panel can read, a failed compose puts the backup back, and the older
botcount / spawn-plan requests still work."""
import json
import os
import shutil
import stat
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import env_apply  # noqa: E402

EXAMPLE = os.path.join(REPO, "linux-port", "docker", ".env.example")
SCHEMA = os.path.join(REPO, "linux-port", "docker", "seban-panel", "env_schema.py")

FAKE_DOCKER = """#!/bin/sh
printf '%s\\n' "$*" >> "$FAKE_DOCKER_LOG"
[ -f "$FAKE_DOCKER_FAIL" ] && { echo "Error: port is already allocated"; exit 1; }
echo "Container recreated"
exit 0
"""


class EnvApplyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="env-apply-")
        self.root = os.path.join(self.tmp, "server")
        docker = os.path.join(self.root, "linux-port", "docker")
        os.makedirs(os.path.join(docker, "seban-panel"))
        os.makedirs(os.path.join(self.root, "linux-port", "tools"))
        shutil.copy(SCHEMA, os.path.join(docker, "seban-panel", "env_schema.py"))
        with open(EXAMPLE, encoding="utf-8") as handle:
            text = handle.read()
        text = text.replace("M2_DB_PASSWORD=\n", "M2_DB_PASSWORD=s3cretDBvalue\n")
        text = text.replace("M2_ADMINPAGE_PASSWORD=\n", "M2_ADMINPAGE_PASSWORD=adminSECRETvalue\n")
        # An .env written before M2_SEONHAE existed: the key is appended.
        text = text.replace("M2_SEONHAE=0\n", "")
        self.env = os.path.join(docker, ".env")
        with open(self.env, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.chmod(self.env, 0o600)
        self.original = text
        self.spool = os.path.join(self.tmp, "spool")
        os.makedirs(self.spool)
        fake = os.path.join(self.tmp, "docker")
        with open(fake, "w") as handle:
            handle.write(FAKE_DOCKER)
        os.chmod(fake, 0o755)
        self.log = os.path.join(self.tmp, "docker.log")
        self.fail_flag = os.path.join(self.tmp, "fail")
        os.environ.update(M2_ENV_APPLY_DOCKER=fake, FAKE_DOCKER_LOG=self.log, FAKE_DOCKER_FAIL=self.fail_flag)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def worker(self):
        return env_apply.Apply(self.root, self.spool)

    def read(self):
        with open(self.env, encoding="utf-8", newline="") as handle:
            return handle.read()

    def docker_calls(self):
        try:
            return open(self.log).read().splitlines()
        except OSError:
            return []

    def request(self, name, payload):
        path = os.path.join(self.spool, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(payload if isinstance(payload, str) else json.dumps(payload))

    def status(self, name="env.status"):
        with open(os.path.join(self.spool, name), encoding="utf-8") as handle:
            return json.load(handle) if name.endswith("status") and name.startswith("env") else handle.read()

    def test_only_listed_lines_change(self):
        self.request("env.request", {"id": "env-1", "changes": {"PLAYERBOT_AUTOSPAWN_COUNT": "800", "M2_AREZZO": "1", "M2_SEONHAE": "1"}})
        self.worker().poll()
        st = self.status()
        self.assertEqual(st["state"], "ok", st)
        after = self.read()
        before_lines, after_lines = self.original.splitlines(), after.splitlines()
        changed = [(a, b) for a, b in zip(before_lines, after_lines) if a != b]
        self.assertEqual(changed, [("PLAYERBOT_AUTOSPAWN_COUNT=350", "PLAYERBOT_AUTOSPAWN_COUNT=800"), ("M2_AREZZO=0", "M2_AREZZO=1")])
        self.assertTrue(after.startswith(self.original.replace("PLAYERBOT_AUTOSPAWN_COUNT=350", "PLAYERBOT_AUTOSPAWN_COUNT=800").replace("M2_AREZZO=0", "M2_AREZZO=1")))
        self.assertTrue(after.rstrip().endswith("M2_SEONHAE=1"))
        self.assertEqual(stat.S_IMODE(os.stat(self.env).st_mode), 0o600)
        self.assertEqual(st["services"], ["game", "playerbot-migrate"])
        self.assertEqual(self.docker_calls(), ["compose up -d --no-deps --force-recreate game playerbot-migrate"])
        backups = os.listdir(os.path.join(os.path.dirname(self.env), ".env-backups"))
        self.assertEqual(len(backups), 1)
        self.assertFalse(os.path.exists(os.path.join(self.spool, "env.request")))
        current = json.load(open(os.path.join(self.spool, "env.current")))
        self.assertEqual(current["values"]["PLAYERBOT_AUTOSPAWN_COUNT"], "800")
        self.assertIn("env-editor-v1", current["features"])

    def test_same_request_never_runs_twice(self):
        self.request("env.request", {"id": "env-2", "changes": {"M2_LOG_KEEP_DAYS": "9"}})
        self.worker().poll()
        self.request("env.request", {"id": "env-2", "changes": {"M2_LOG_KEEP_DAYS": "11"}})
        self.worker().poll()
        self.assertIn("M2_LOG_KEEP_DAYS=9\n", self.read())
        self.assertEqual(len(self.docker_calls()), 1)

    def test_invalid_and_readonly_are_refused(self):
        for i, changes in enumerate(({"PLAYERBOT_AUTOSPAWN_COUNT": "99999"}, {"M2_DB_PASSWORD": "newpassword"},
                        {"M2_UPDATE_STACK_DIR": "/"}, {"M2_BRAND": "x\nM2_TEST_SERVER=1"},
                        {"M2_TZ": "${M2_DB_PASSWORD}"}, {"NOT_A_KEY": "1"},
                        {"M2_AREZZO": "1", "M2_HOST_BIND_ADDRESS": "everywhere"})):
            self.request("env.request", {"id": "env-bad-%d" % i, "changes": changes})
            self.worker().poll()
            st = self.status()
            self.assertEqual(st["state"], "rejected", (changes, st))
            self.assertEqual(self.read(), self.original, changes)
        self.assertEqual(self.docker_calls(), [])
        self.assertFalse(os.path.isdir(os.path.join(os.path.dirname(self.env), ".env-backups")))

    def test_secrets_never_leak(self):
        self.request("env.request", {"id": "env-3", "changes": {"M2_ADMINPAGE_PASSWORD": "brandNEWsecret"}})
        self.worker().poll()
        self.assertIn("M2_ADMINPAGE_PASSWORD=brandNEWsecret\n", self.read())
        st = self.status()
        self.assertEqual(st["state"], "ok", st)
        self.assertEqual(st["services"], ["game", "seban-collector", "seban-item-grants", "seban-panel"])
        for name in ("env.status", "env.current", "env.log"):
            text = open(os.path.join(self.spool, name), encoding="utf-8").read()
            for secret in ("brandNEWsecret", "adminSECRETvalue", "s3cretDBvalue"):
                self.assertNotIn(secret, text, name)
        current = json.load(open(os.path.join(self.spool, "env.current")))
        self.assertEqual(current["secrets"]["M2_ADMINPAGE_PASSWORD"], "set")
        self.assertEqual(current["secrets"]["M2_PANEL_PASSWORD"], "unset")
        self.assertNotIn("M2_DB_PASSWORD", current["values"])

    def test_failed_compose_restores_env(self):
        open(self.fail_flag, "w").close()
        self.request("env.request", {"id": "env-4", "changes": {"M2_SEBAN_PANEL_PORT": "7795"}})
        self.worker().poll()
        st = self.status()
        self.assertEqual(st["state"], "failed", st)
        self.assertEqual(self.read(), self.original)
        self.assertEqual(len(self.docker_calls()), 2)
        self.assertTrue(any("port is already allocated" in line for line in st["log"]))

    def test_unchanged_values_do_nothing(self):
        self.request("env.request", {"id": "env-5", "changes": {"M2_DIFFICULTY": "easy"}})
        self.worker().poll()
        self.assertEqual(self.status()["state"], "ok")
        self.assertEqual(self.read(), self.original)
        self.assertEqual(self.docker_calls(), [])

    def test_build_only_and_no_service_keys(self):
        self.request("env.request", {"id": "env-6", "changes": {"M2_MAKE_JOBS": "4", "M2_CLIENT_MIN_FREE_MB": "8000"}})
        self.worker().poll()
        st = self.status()
        self.assertEqual(st["state"], "ok", st)
        self.assertIn("M2_MAKE_JOBS=4\n", self.read())
        self.assertEqual(self.docker_calls(), [])
        self.assertIn("przebudowie", st["message"])

    def test_crlf_env_keeps_its_line_endings(self):
        with open(self.env, "w", encoding="utf-8", newline="") as handle:
            handle.write(self.original.replace("\n", "\r\n"))
        self.request("env.request", {"id": "env-7", "changes": {"M2_AREZZO": "1", "M2_SEONHAE": "1"}})
        self.worker().poll()
        text = self.read()
        self.assertIn("M2_AREZZO=1\r\n", text)
        self.assertIn("M2_SEONHAE=1\r\n", text)
        self.assertNotIn("\n", text.replace("\r\n", ""))

    def test_botcount_and_spawn_plan_requests(self):
        self.request("botcount.request", "id=seban-botcount-1\ncount=1200\ntime=1\n")
        self.worker().poll()
        self.assertIn("PLAYERBOT_AUTOSPAWN_COUNT=1200\n", self.read())
        self.assertIn("count=1200", open(os.path.join(self.spool, "botcount.status")).read())
        self.assertIn("state=ok", open(os.path.join(self.spool, "botcount.status")).read())
        self.request("spawn-plan.request", "id=seban-spawn-plan-1\nwindow=15\nlate_joiners=500\nlate_hours=24\n")
        self.worker().poll()
        text = self.read()
        self.assertIn("PLAYERBOT_SPAWN_WINDOW_MINUTES=15\n", text)
        self.assertIn("PLAYERBOT_LATE_JOINERS=500\n", text)
        self.assertIn("window=15", open(os.path.join(self.spool, "spawn-plan.status")).read())
        self.request("botcount.request", "id=seban-botcount-2\ncount=99999\n")
        self.worker().poll()
        self.assertIn("state=failed", open(os.path.join(self.spool, "botcount.status")).read())
        self.assertIn("PLAYERBOT_AUTOSPAWN_COUNT=1200\n", self.read())

    def test_backups_are_capped(self):
        for i in range(env_apply.KEEP_BACKUPS + 3):
            self.request("env.request", {"id": "env-cap-%d" % i, "changes": {"M2_LOG_KEEP_DAYS": str(10 + i)}})
            self.worker().poll()
        names = os.listdir(os.path.join(os.path.dirname(self.env), ".env-backups"))
        self.assertEqual(len(names), env_apply.KEEP_BACKUPS)

    def test_second_channel_widens_the_ports(self):
        # update.sh's own rule (`sh update.sh ports'), run on the temporary folder.
        tools = os.path.join(self.root, "linux-port", "tools")
        shutil.copy(os.path.join(HERE, "update.sh"), tools)
        open(os.path.join(self.root, "VERSION"), "w").write("9.9.9\n")
        docker = os.path.dirname(self.env)
        open(os.path.join(docker, "ENGINE"), "w").write("mt2009\n")
        open(os.path.join(docker, "docker-compose.yml"), "w").write("services: {}\n")
        self.request("env.request", {"id": "env-ch2", "changes": {"M2_PLAYERBOT_CH2": "1"}})
        self.worker().poll()
        st = self.status()
        self.assertEqual(st["state"], "ok", st)
        text = self.read()
        self.assertIn("M2_PLAYERBOT_CH2=1\n", text)
        self.assertIn("M2_GAME_PORT_RANGE=13000-13012\n", text)
        self.assertIn("M2_GAME_CONTAINER_PORT_RANGE=13000-13012\n", text)
        self.assertNotIn("M2_PLAYERBOT_CH2_SET_AT=0\n", text)
        self.assertIn("M2_GAME_PORT_RANGE", st["changed"])
        self.assertEqual(st["services"], ["game", "panel"])

    def test_overridden_keys_are_reported(self):
        with open(os.path.join(os.path.dirname(self.env), "docker-compose.override.yml"), "w") as handle:
            handle.write("services:\n  game:\n    environment:\n      PLAYERBOT_AUTOSPAWN_COUNT: \"2000\"\n")
        current = self.worker().snapshot()
        self.assertEqual(current["overridden"], ["PLAYERBOT_AUTOSPAWN_COUNT"])


if __name__ == "__main__":
    unittest.main()


class PendingLiveSwitches(EnvApplyTest):
    """MT2009_PLUS_ENV_LIVE_V1: env.pending (switches the panel turned in the
    game while no updater ran) reaches .env without restarting anything."""

    def test_pending_written_without_compose_crlf(self):
        with open(self.env, "w", encoding="utf-8", newline="") as handle:
            handle.write(self.original.replace("\n", "\r\n"))
        self.request("env.pending", {"time": 1, "values": {"M2_AREZZO": "1", "M2_SEONHAE": "1", "M2_SASHES": "0"}})
        self.assertEqual(env_apply.main(["--root", self.root, "--spool", self.spool, "pending"]), 0)
        env_apply.main(["--root", self.root, "--spool", self.spool, "snapshot"])
        text = self.read()
        self.assertIn("M2_AREZZO=1\r\n", text)
        self.assertIn("M2_SEONHAE=1\r\n", text)
        self.assertIn("M2_SASHES=0\r\n", text)
        self.assertNotIn("\n", text.replace("\r\n", ""))
        self.assertEqual(self.docker_calls(), [])
        self.assertFalse(os.path.exists(os.path.join(self.spool, "env.pending")))
        current = json.load(open(os.path.join(self.spool, "env.current"), encoding="utf-8"))
        self.assertEqual(current["values"]["M2_AREZZO"], "1")

    def test_pending_only_takes_live_keys(self):
        self.request("env.pending", {"values": {"M2_AREZZO": "1", "PLAYERBOT_AUTOSPAWN_COUNT": "9", "M2_SASHES": "x"}})
        self.worker().poll()
        values = self.worker().read_env()
        self.assertEqual(values["M2_AREZZO"], "1")
        self.assertNotEqual(values.get("PLAYERBOT_AUTOSPAWN_COUNT"), "9")
        self.assertNotEqual(values.get("M2_SASHES"), "x")
        self.assertEqual(self.docker_calls(), [])
