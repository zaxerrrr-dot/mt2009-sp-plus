"""MT2009_PLUS_UPDATER_AUTOSTART_V1: python3 -m unittest test_update_autostart (in linux-port/tools)

update.sh's `updater' mode and the background start after an older
update.sh's unpack, on a temporary server folder with a fake `docker' that
records its arguments and the environment compose would read."""
import os
import shutil
import subprocess
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "update.sh")

FAKE_DOCKER = """#!/bin/sh
if [ "$1" = inspect ]; then
    case "$3" in
        *Config.Env*) cat "$FAKE_ENV" 2>/dev/null ;;
        *Mounts*) cat "$FAKE_MOUNTS" 2>/dev/null ;;
        *) cat "$FAKE_RUNNING" 2>/dev/null ;;
    esac
    exit 0
fi
printf '%s|stack=%s|watch=%s\\n' "$*" "$M2_UPDATE_STACK_DIR" "$M2_UPDATE_WATCH_UPDATES" >> "$FAKE_DOCKER_LOG"
exit 0
"""


class UpdaterAutostart(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="upd-auto-")
        self.root = os.path.join(self.tmp, "Serwer")
        self.compose = os.path.join(self.root, "linux-port", "docker")
        os.makedirs(os.path.join(self.root, "linux-port", "tools"))
        os.makedirs(self.compose)
        shutil.copy(SCRIPT, os.path.join(self.root, "linux-port", "tools", "update.sh"))
        open(os.path.join(self.root, "VERSION"), "w").write("9.9.9\n")
        open(os.path.join(self.compose, "docker-compose.yml"), "w").write("services: {}\n")
        open(os.path.join(self.compose, "ENGINE"), "w").write("mt2009\n")
        self.env = os.path.join(self.compose, ".env")
        self.write_env("M2_UPDATE_APPLY=0\r\nM2_UPDATE_STACK_DIR=/opt/metin2\r\nM2_UPDATE_WATCH_UPDATES=1\r\n")
        bindir = os.path.join(self.tmp, "bin")
        os.makedirs(bindir)
        with open(os.path.join(bindir, "docker"), "w") as handle:
            handle.write(FAKE_DOCKER)
        os.chmod(os.path.join(bindir, "docker"), 0o755)
        self.log = os.path.join(self.tmp, "docker.log")
        self.running = os.path.join(self.tmp, "running")
        self.fake_env = os.path.join(self.tmp, "container.env")
        self.fake_mounts = os.path.join(self.tmp, "container.mounts")
        self.environ = dict(os.environ, PATH=bindir + os.pathsep + os.environ["PATH"], FAKE_DOCKER_LOG=self.log,
                            FAKE_RUNNING=self.running, FAKE_ENV=self.fake_env, FAKE_MOUNTS=self.fake_mounts,
                            M2_UPDATE_SPOOL=os.path.join(self.tmp, "spool"))
        for key in ("M2_UPDATE_STACK_DIR", "M2_UPDATE_WATCHING", "M2_UPDATE_WATCH_UPDATES", "M2_UPDATE_PARENT_REFRESHES"):
            self.environ.pop(key, None)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_env(self, text):
        with open(self.env, "w", newline="") as handle:
            handle.write(text)

    def run_script(self, *args):
        return subprocess.run(["sh", os.path.join(self.root, "linux-port", "tools", "update.sh")] + list(args),
                              env=self.environ, capture_output=True, text=True, timeout=60)

    def calls(self):
        try:
            return [c for c in open(self.log).read().splitlines() if "updater" in c]
        except OSError:
            return []

    def test_syntax(self):
        for shell in ("sh", "bash"):
            self.assertEqual(subprocess.run([shell, "-n", SCRIPT]).returncode, 0)
        self.assertEqual(subprocess.run(["bash", "-n", os.path.join(HERE, "vps-install.sh")]).returncode, 0)

    def test_starts_settings_only_by_default(self):
        result = self.run_script("updater")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = self.calls()
        self.assertEqual(len(calls), 1, calls)
        self.assertIn("compose --profile update up -d --build --no-deps updater", calls[0])
        self.assertIn("|stack=%s|" % self.root, calls[0])
        self.assertTrue(calls[0].endswith("|watch=0"), calls[0])
        # the example's /opt/metin2 is replaced by the real folder, CRLF kept on the other lines
        text = open(self.env, newline="").read()
        self.assertIn("M2_UPDATE_STACK_DIR=%s\n" % self.root, text)
        self.assertIn("M2_UPDATE_APPLY=0\r\n", text)

    def test_apply_switch_allows_updates(self):
        self.write_env("M2_UPDATE_APPLY=1\n")
        self.run_script("updater")
        self.assertTrue(self.calls()[0].endswith("|watch=1"))
        self.assertIn("M2_UPDATE_STACK_DIR=%s\n" % self.root, open(self.env).read())

    def test_autostart_off(self):
        self.write_env("M2_UPDATE_AUTOSTART=0\r\n")
        self.run_script("updater")
        self.assertEqual(self.calls(), [])

    # MT2009_PLUS_UPDATER_REFRESH_V1: `updater' (an install, by hand) and an
    # update recreate a running updater; its WATCH_UPDATES stays.
    def test_running_updater_is_recreated(self):
        open(self.running, "w").write("true\n")
        open(self.fake_env, "w").write("M2_UPDATE_STACK_DIR=%s\nM2_UPDATE_WATCH_UPDATES=1\n" % self.root)
        open(self.fake_mounts, "w").write("%s|%s\n/opt/m2update|/var/lib/docker/volumes/x\n" % (self.root, self.root))
        result = self.run_script("updater")
        calls = self.calls()
        self.assertEqual(len(calls), 1, result.stdout + result.stderr)
        self.assertIn("up -d --build --no-deps --force-recreate updater", calls[0])
        self.assertTrue(calls[0].endswith("|watch=1"), calls[0])

    def test_updater_of_another_folder_is_replaced(self):
        open(self.running, "w").write("true\n")
        open(self.fake_env, "w").write("M2_UPDATE_STACK_DIR=/home/old/MT2009-PLUS-Serwer-2.12.0\nM2_UPDATE_WATCH_UPDATES=0\n")
        result = self.run_script("updater")
        calls = self.calls()
        self.assertEqual(len(calls), 2, calls)
        self.assertTrue(calls[0].startswith("rm -f metin2-updater"), calls[0])
        self.assertIn("up -d --build --no-deps updater|stack=%s|" % self.root, calls[1])
        self.assertIn("serves another folder", result.stdout)

    def test_mount_of_another_folder_is_replaced(self):
        open(self.running, "w").write("true\n")
        open(self.fake_env, "w").write("M2_UPDATE_STACK_DIR=%s\n" % self.root)
        open(self.fake_mounts, "w").write("%s|/srv/elsewhere\n" % self.root)
        self.run_script("updater")
        self.assertTrue(self.calls()[0].startswith("rm -f metin2-updater"), self.calls())

    def test_parent_that_refreshes_skips_the_background_start(self):
        pending = os.path.join(self.root, ".update-build-pending")
        open(pending, "w").close()
        open(os.path.join(self.compose, ".env.example"), "w").write("")
        self.environ["M2_UPDATE_STACK_DIR"] = self.root
        self.environ["M2_UPDATE_PARENT_REFRESHES"] = "1"
        result = self.run_script("env")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        os.remove(pending)
        time.sleep(25)
        self.assertEqual(self.calls(), [])

    def test_after_an_older_scripts_unpack(self):
        # The old update.sh runs the new one with `env' right after the unpack,
        # BUILD_PENDING present; the updater starts once the build removed it.
        pending = os.path.join(self.root, ".update-build-pending")
        open(pending, "w").close()
        open(os.path.join(self.compose, ".env.example"), "w").write("")
        self.environ["M2_UPDATE_STACK_DIR"] = self.root
        result = self.run_script("env")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.calls(), [])
        os.remove(pending)
        deadline = time.time() + 40
        while time.time() < deadline and not self.calls():
            time.sleep(0.5)
        self.assertEqual(len(self.calls()), 1)
        self.assertIn("up -d --build --no-deps updater", self.calls()[0])


if __name__ == "__main__":
    unittest.main()
