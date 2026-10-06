#!/usr/bin/env python3
"""MT2009_PLUS_ENV_EDITOR_V1: the updater's half of the .env editor.

The advanced panel never writes .env and never touches Docker. It leaves a
request in the update spool (the volume it already shares with the updater)
and reads back what this writes:

    env.request        {"id", "time", "changes": {"KEY": "value", ...}}  (panel)
    env.status         state queued|running|ok|failed|rejected, message,
                       per-key results, services recreated              (here)
    env.current        the current values; secrets only as set / unset   (here)
    env.log            the last apply's docker compose output            (here)

botcount.request (count=N) and spawn-plan.request (window=, late_joiners=,
late_hours=) - the panel's older special-purpose requests, which the host
watcher seban-updater-watch.sh used to answer - go through the same apply and
keep answering in botcount.status / spawn-plan.status.

Run by linux-port/tools/update.sh in its watch loop (the `updater' compose
service, the only container with the Docker socket) and by the host watcher
seban-updater-watch.sh:

    python3 env_apply.py --root /opt/metin2 --spool /opt/m2update poll
    python3 env_apply.py --root /opt/metin2 --spool /opt/m2update snapshot

Every request is validated again against env_schema.py (the panel's own
copy of the rules is not trusted), .env is backed up (the last
KEEP_BACKUPS copies, .env-backups/ beside it), only the named lines are
rewritten - comments, order and every other line stay byte for byte - and
exactly the services the schema names are recreated with
`docker compose up -d --force-recreate`. When compose fails the backup is put
back and compose is run once more, so the server returns to what it ran.
"""
import argparse
import datetime
import fcntl
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time

KEEP_BACKUPS = 10
COMPOSE_TIMEOUT = 25 * 60
FEATURE = "env-editor-v1"
SECRET_SET, SECRET_UNSET = "__SET__", "__UNSET__"
LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*?)(\r?)$")


class Apply:
    def __init__(self, root, spool, docker=None):
        self.root = os.path.abspath(root)
        self.spool = spool
        self.compose_dir = os.path.join(self.root, "linux-port", "docker")
        self.env_file = os.path.join(self.compose_dir, ".env")
        self.backup_dir = os.path.join(self.compose_dir, ".env-backups")
        self.docker = (docker or os.environ.get("M2_ENV_APPLY_DOCKER") or "docker").split()
        self.schema = self._load_schema()

    # ---------------------------------------------------------------- basics
    def _load_schema(self):
        path = os.path.join(self.compose_dir, "seban-panel", "env_schema.py")
        spec = importlib.util.spec_from_file_location("m2_env_schema", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _spool(self, name):
        return os.path.join(self.spool, name)

    def _write(self, name, text):
        os.makedirs(self.spool, exist_ok=True)
        temporary = self._spool(name + ".new")
        old = os.umask(0o007)
        try:
            with open(temporary, "w", encoding="utf-8") as handle:
                handle.write(text)
        finally:
            os.umask(old)
        os.replace(temporary, self._spool(name))

    def _write_json(self, name, data):
        self._write(name, json.dumps(data, ensure_ascii=False, indent=1) + "\n")

    def _heartbeat(self):
        try:
            with open(self._spool("watcher"), "a"):
                os.utime(self._spool("watcher"), None)
        except OSError:
            pass

    def log(self, text):
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self._spool("env.log"), "a", encoding="utf-8") as handle:
                handle.write("%s %s\n" % (stamp, text))
        except OSError:
            pass
        print("%s [env] %s" % (stamp, text), flush=True)

    # ------------------------------------------------------------------ .env
    def read_lines(self):
        with open(self.env_file, "r", encoding="utf-8", newline="") as handle:
            return handle.read().splitlines(keepends=True)

    @staticmethod
    def _value(raw):
        value = raw.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        return value

    def read_env(self):
        """KEY -> value; the last line wins, as for docker compose."""
        values = {}
        for line in self.read_lines():
            match = LINE.match(line.rstrip("\n"))
            if match:
                values[match.group(1)] = self._value(match.group(2))
        return values

    def write_env(self, changes, note):
        """Rewrite only the lines of the changed keys; append the missing ones."""
        lines = self.read_lines()
        seen = set()
        out = []
        for line in lines:
            ending = "\n" if line.endswith("\n") else ""
            body = line[:-1] if ending else line
            match = LINE.match(body)
            if match and match.group(1) in changes:
                key = match.group(1)
                seen.add(key)
                out.append("%s=%s%s%s" % (key, changes[key], match.group(3), ending))
            else:
                out.append(line)
        missing = [key for key in changes if key not in seen]
        if missing:
            crlf = "\r\n" if any(line.endswith("\r\n") for line in lines) else "\n"
            if out and not out[-1].endswith("\n"):
                out[-1] += crlf
            out.append(crlf + "# %s%s" % (note, crlf))
            for key in missing:
                out.append("%s=%s%s" % (key, changes[key], crlf))
        mode = os.stat(self.env_file).st_mode & 0o777
        temporary = self.env_file + ".env-editor.new"
        with open(temporary, "w", encoding="utf-8", newline="") as handle:
            handle.write("".join(out))
        os.chmod(temporary, mode)
        try:
            stat = os.stat(self.env_file)
            os.chown(temporary, stat.st_uid, stat.st_gid)
        except OSError:
            pass
        os.replace(temporary, self.env_file)

    def backup(self, request_id):
        os.makedirs(self.backup_dir, exist_ok=True)
        os.chmod(self.backup_dir, 0o700)
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        safe = re.sub(r"[^A-Za-z0-9_-]", "", request_id)[-24:]
        target = os.path.join(self.backup_dir, ".env.%s-%s" % (stamp, safe))
        shutil.copy2(self.env_file, target)
        os.chmod(target, 0o600)
        kept = sorted(name for name in os.listdir(self.backup_dir) if name.startswith(".env."))
        for name in kept[:-KEEP_BACKUPS]:
            try:
                os.remove(os.path.join(self.backup_dir, name))
            except OSError:
                pass
        return target

    # -------------------------------------------------------------- snapshot
    def overridden_keys(self):
        """Keys docker-compose.override.yml sets itself (best effort): there a
        change in .env reaches nothing, and the page says so."""
        path = os.path.join(self.compose_dir, "docker-compose.override.yml")
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            return []
        found = []
        for entry in self.schema.SCHEMA:
            key = entry["key"]
            if re.search(r"^\s+-?\s*%s\s*[:=]" % re.escape(key), text, re.M) and not re.search(r"\$\{%s[:}-]" % re.escape(key), text):
                found.append(key)
        return found

    def snapshot(self):
        values, secrets, present = {}, {}, []
        try:
            current = self.read_env()
            error = None
        except OSError as exc:
            current, error = {}, "Nie można odczytać .env: %s" % exc.strerror
        for entry in self.schema.SCHEMA:
            key = entry["key"]
            if key in current:
                present.append(key)
            if entry.get("secret"):
                secrets[key] = "set" if current.get(key) else "unset"
            elif key in current:
                values[key] = current[key]
        unknown = sorted(key for key in current if key not in self.schema.BY_KEY)
        data = {"features": [FEATURE], "schema_version": self.schema.SCHEMA_VERSION, "time": int(time.time()),
                "values": values, "secrets": secrets, "present": present, "unknown_keys": unknown,
                "overridden": self.overridden_keys(), "error": error,
                "backups": len([n for n in os.listdir(self.backup_dir) if n.startswith(".env.")]) if os.path.isdir(self.backup_dir) else 0}
        self._write_json("env.current", data)
        return data

    # ---------------------------------------------------------------- compose
    def compose(self, services, label):
        """docker compose up -d --force-recreate <services>; True when it worked."""
        command = self.docker + ["compose", "up", "-d", "--force-recreate"] + list(services)
        self.log("%s: %s" % (label, " ".join(command[len(self.docker):])))
        try:
            process = subprocess.Popen(command, cwd=self.compose_dir, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, errors="replace")
        except OSError as exc:
            self.log("docker compose nie wystartował: %s" % exc)
            return False
        started = time.time()
        import threading

        def pump():
            for line in process.stdout:
                self.log("   " + line.rstrip())
        reader = threading.Thread(target=pump, daemon=True)
        reader.start()
        beat = 0.0
        while process.poll() is None:
            if time.time() - beat > 5:
                beat = time.time()
                self._heartbeat()
            if time.time() - started > COMPOSE_TIMEOUT:
                process.kill()
                self.log("docker compose przekroczył %d min - przerwano" % (COMPOSE_TIMEOUT // 60))
                break
            time.sleep(0.25)
        reader.join(timeout=5)
        code = process.wait()
        process.stdout.close()
        return code == 0

    def sync_channel_ports(self):
        """update.sh's own channel/port rule (`sh update.sh ports')."""
        script = os.path.join(self.root, "linux-port", "tools", "update.sh")
        if not os.path.isfile(script):
            return
        env = dict(os.environ, M2_UPDATE_STACK_DIR=self.root)
        result = subprocess.run(["sh", script, "ports"], env=env, capture_output=True, text=True, errors="replace")
        for line in (result.stdout + result.stderr).splitlines():
            self.log("   " + line)

    # ------------------------------------------------------------------ apply
    def apply(self, request_id, changes, source="panel"):
        """Validate, write, recreate. Returns the status dict (also written)."""
        schema = self.schema
        status = {"id": request_id, "state": "running", "time": int(time.time()), "source": source,
                  "message": "Sprawdzanie zmian.", "results": {}, "services": [], "changed": []}
        self._write_json("env.status", status)
        try:
            with open(self._spool("env.log"), "w", encoding="utf-8"):
                pass
        except OSError:
            pass
        if not isinstance(changes, dict) or not changes:
            return self._finish(status, "rejected", "Puste albo nieprawidłowe zlecenie – nic nie zmieniono.")
        bad = False
        for key, value in changes.items():
            reason = schema.validate(key, value) if isinstance(key, str) else "nieprawidłowa nazwa"
            secret = bool(schema.BY_KEY.get(key, {}).get("secret"))
            status["results"][str(key)] = {"ok": reason is None, "message": reason or "", "secret": secret}
            bad = bad or reason is not None
        if bad:
            self.log("odrzucono: " + ", ".join("%s (%s)" % (k, r["message"]) for k, r in status["results"].items() if not r["ok"]))
            return self._finish(status, "rejected", "Odrzucono zlecenie: co najmniej jedna wartość jest nieprawidłowa. Nic nie zmieniono.")
        if not os.path.isfile(self.env_file):
            return self._finish(status, "failed", "Nie odnaleziono pliku .env aktywnej instalacji (%s)." % self.env_file)
        before = self.read_env()
        changed = {k: v for k, v in changes.items() if before.get(k) != v}
        for key, result in status["results"].items():
            result["changed"] = key in changed
            if not result["secret"]:
                result["old"] = before.get(key)
                result["new"] = changes[key]
        if not changed:
            return self._finish(status, "ok", "Wszystkie wartości były już takie same – nic nie zmieniono.")
        if "M2_PLAYERBOT_CH2" in changed:
            changed["M2_PLAYERBOT_CH2_SET_AT"] = str(int(time.time()))
        backup = self.backup(request_id)
        status["backup"] = os.path.basename(backup)
        note = "MT2009_PLUS_ENV_EDITOR_V1: dopisane z panelu zaawansowanego %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.write_env(changed, note)
        self.log("zapisano .env (%d): %s" % (len(changed), ", ".join(
            k + ("=<ukryte>" if schema.BY_KEY.get(k, {}).get("secret") else "=" + v) for k, v in changed.items())))
        if any(key in changed for key in schema.CHANNEL_KEYS):
            self.sync_channel_ports()
            after = self.read_env()
            for key, value in after.items():
                if before.get(key) != value and key not in changed:
                    changed[key] = value
                    self.log("dopasowano %s=%s" % (key, value))
        status["changed"] = sorted(changed)
        services = schema.services_for(changed)
        skipped = [s for s in services if s == "updater"]
        services = [s for s in services if s != "updater"]
        if "seban-panel" in services:
            services = [s for s in services if s != "seban-panel"] + ["seban-panel"]
        status["services"] = services
        build_only = sorted(k for k in changed if schema.BY_KEY.get(k, {}).get("build"))
        extra = []
        if build_only:
            extra.append("Ustawienia budowania (%s) zadziałają przy następnej przebudowie obrazu gry (aktualizacji)." % ", ".join(build_only))
        if skipped:
            extra.append("Aktualizator przyjmie nowe ustawienia po swoim ponownym uruchomieniu.")
        if not services:
            self.snapshot()
            return self._finish(status, "ok", " ".join(["Zapisano w .env. Żadna usługa nie wymagała ponownego uruchomienia."] + extra))
        labels = ", ".join(schema.SERVICE_LABELS.get(s, s) for s in services)
        status["message"] = "Zapisano .env. Odtwarzanie usług: %s…" % labels
        self._write_json("env.status", status)
        self.snapshot()
        if self.compose(services, "odtwarzanie"):
            self.snapshot()
            return self._finish(status, "ok", " ".join(["Zapisano i uruchomiono ponownie: %s." % labels] + extra))
        self.log("docker compose nie powiódł się - przywracam poprzedni .env")
        shutil.copy2(backup, self.env_file)
        restored = self.compose(services, "przywracanie")
        self.snapshot()
        return self._finish(status, "failed",
                            "Nie udało się uruchomić usług z nowymi wartościami – przywrócono poprzedni .env%s. Szczegóły w logu poniżej."
                            % ("" if restored else " (ponowne uruchomienie także nie powiodło się – sprawdź serwer)"))

    def _finish(self, status, state, message):
        status["state"] = state
        status["message"] = message
        status["time"] = int(time.time())
        try:
            with open(self._spool("env.log"), encoding="utf-8", errors="replace") as handle:
                status["log"] = handle.read().splitlines()[-40:]
        except OSError:
            status["log"] = []
        self._write_json("env.status", status)
        self.log("%s: %s" % (state, message))
        return status

    # ------------------------------------------------------------ the requests
    def _take(self, name):
        """Read and claim a request: renamed away first, so it never runs twice."""
        path = self._spool(name)
        if not os.path.isfile(path):
            return None
        claimed = path + ".taken"
        try:
            os.replace(path, claimed)
            with open(claimed, encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            return None
        finally:
            try:
                os.replace(claimed, path + ".done")
            except OSError:
                pass
        return text

    @staticmethod
    def _kv(text):
        values = {}
        for line in text.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values.setdefault(key.strip(), value.strip())
        return values

    def _seen(self, kind, request_id):
        marker = self._spool(kind + ".last-id")
        try:
            with open(marker, encoding="utf-8") as handle:
                if handle.read().strip() == request_id:
                    return True
        except OSError:
            pass
        self._write(kind + ".last-id", request_id + "\n")
        return False

    def poll(self):
        handled = False
        text = self._take("env.request")
        if text is not None:
            handled = True
            try:
                request = json.loads(text)
                request_id = str(request.get("id") or "")[:80]
                changes = request.get("changes")
            except (ValueError, AttributeError):
                request_id, changes = "", None
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", request_id):
                self._finish({"id": request_id, "results": {}, "services": [], "changed": []}, "rejected",
                             "Nieprawidłowe zlecenie (brak identyfikatora).")
            elif not self._seen("env", request_id):
                changes = {str(k): v if isinstance(v, str) else str(v) for k, v in changes.items()} if isinstance(changes, dict) else None
                self.apply(request_id, changes, "panel")
        text = self._take("botcount.request")
        if text is not None:
            handled = True
            values = self._kv(text)
            request_id = values.get("id", "")
            if request_id and not self._seen("botcount", request_id):
                count = values.get("count", "")
                result = self.apply(re.sub(r"[^A-Za-z0-9_-]", "", request_id)[:80] or "botcount",
                                    {"PLAYERBOT_AUTOSPAWN_COUNT": count}, "botcount")
                ok = result["state"] == "ok"
                self._write("botcount.status", "state=%s\ntime=%d\ncount=%s\nmessage=%s\n" % (
                    "ok" if ok else "failed", time.time(), count if ok else self.read_env().get("PLAYERBOT_AUTOSPAWN_COUNT", count),
                    result["message"].replace("\n", " ")))
        text = self._take("spawn-plan.request")
        if text is not None:
            handled = True
            values = self._kv(text)
            request_id = values.get("id", "")
            if request_id and not self._seen("spawn-plan", request_id):
                changes = {"PLAYERBOT_SPAWN_WINDOW_MINUTES": values.get("window", ""),
                           "PLAYERBOT_LATE_JOINERS": values.get("late_joiners", ""),
                           "PLAYERBOT_LATE_JOIN_HOURS": values.get("late_hours", "")}
                result = self.apply(re.sub(r"[^A-Za-z0-9_-]", "", request_id)[:80] or "spawnplan", changes, "spawn-plan")
                ok = result["state"] == "ok"
                current = self.read_env()
                self._write("spawn-plan.status", "state=%s\ntime=%d\nwindow=%s\nlate_joiners=%s\nlate_hours=%s\nmessage=%s\n" % (
                    "ok" if ok else "failed", time.time(), current.get("PLAYERBOT_SPAWN_WINDOW_MINUTES", "1"),
                    current.get("PLAYERBOT_LATE_JOINERS", "0"), current.get("PLAYERBOT_LATE_JOIN_HOURS", "24"),
                    result["message"].replace("\n", " ")))
        return handled


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=os.environ.get("M2_UPDATE_STACK_DIR") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    parser.add_argument("--spool", default=os.environ.get("M2_UPDATE_SPOOL", "/opt/m2update"))
    parser.add_argument("action", choices=("poll", "snapshot", "pending"))
    args = parser.parse_args(argv)
    if args.action == "pending":
        # Cheap check for the watch loop: exit 0 when a request is waiting.
        return 0 if any(os.path.isfile(os.path.join(args.spool, n)) for n in ("env.request", "botcount.request", "spawn-plan.request")) else 1
    os.makedirs(args.spool, exist_ok=True)
    with open(os.path.join(args.spool, "env.lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        worker = Apply(args.root, args.spool)
        if args.action == "snapshot":
            worker.snapshot()
        else:
            worker.poll()
    return 0


if __name__ == "__main__":
    sys.exit(main())
