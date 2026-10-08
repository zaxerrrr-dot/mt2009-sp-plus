"""MT2009_PLUS_ENV_EDITOR_V1: "Ustawienia serwera (.env)" - the panel's half.

The panel shows every variable of env_schema.py with the values the updater
published (env.current, secrets only as set / unset) and queues changes as
env.request in the update spool. It never writes .env and holds no Docker
socket: the updater (update.sh watch -> linux-port/tools/env_apply.py)
validates the request again, writes .env, recreates the services and
answers in env.status, which the page polls.
"""
import hmac
import json
import os
import time
import uuid

from flask import abort, jsonify, render_template, request, session

import env_schema

FEATURE = "env-editor-v1"
WATCHER_MAX_AGE = 90
# A request nobody has picked up for this long is not "in progress" any more.
QUEUED_STALE_SECONDS = 15 * 60
RUNNING_STALE_SECONDS = 40 * 60
DANGER_WORD = "ZMIENIAM"
HIDDEN_SECTIONS = {section["id"] for section in env_schema.SECTIONS if section.get("hidden")}
BUSY_STATES = ("queued", "running")


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _read_kv(path):
    values = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if "=" in line:
                    key, value = line.rstrip("\n").split("=", 1)
                    values[key.strip()] = value.strip()
    except OSError:
        pass
    return values


def editor_state(spool):
    """Is a watcher that understands env.request alive, and what did it say."""
    try:
        age = max(0, int(time.time() - os.stat(os.path.join(spool, "watcher")).st_mtime))
    except OSError:
        age = None
    features = _read_kv(os.path.join(spool, "watcher.features"))
    current = _read_json(os.path.join(spool, "env.current"))
    supports = FEATURE in features.get("features", "").split(",") or FEATURE in current.get("features", [])
    alive = age is not None and age < WATCHER_MAX_AGE
    ready = bool(alive and supports and current)
    if ready:
        reason = ""
    elif not alive:
        reason = "watcher"
    elif not supports or not current:
        reason = "old-watcher"
    else:
        reason = "watcher"
    return {"ready": ready, "alive": alive, "supports": supports, "reason": reason, "watcher_age": age,
            "current": current, "status": read_status(spool)}


def read_status(spool):
    status = _read_json(os.path.join(spool, "env.status"))
    state = status.get("state", "")
    try:
        age = int(time.time()) - int(status.get("time") or 0)
    except (TypeError, ValueError):
        age = 0
    limit = QUEUED_STALE_SECONDS if state == "queued" else RUNNING_STALE_SECONDS
    status["busy"] = state in BUSY_STATES and age < limit
    status["stale"] = state in BUSY_STATES and age >= limit
    return status


def validate_changes(changes, current, confirm_word):
    """(clean changes, {key: reason}) - the panel's check; the updater repeats it."""
    errors, clean = {}, {}
    if not isinstance(changes, dict) or not changes:
        return {}, {"_": "Brak zmian do zapisania."}
    if len(changes) > len(env_schema.SCHEMA):
        return {}, {"_": "Za dużo zmian naraz."}
    dangerous = False
    for key, value in changes.items():
        if not isinstance(key, str) or not isinstance(value, (str, int, float)):
            errors[str(key)] = "nieprawidłowa wartość"
            continue
        value = str(value)
        reason = env_schema.validate(key, value)
        if reason:
            errors[key] = reason
            continue
        entry = env_schema.BY_KEY[key]
        if entry["section"] in HIDDEN_SECTIONS:
            errors[key] = "to ustawienie nie jest zmieniane z panelu"
            continue
        if not entry.get("secret") and current.get("values", {}).get(key) == value:
            continue
        clean[key] = value
        dangerous = dangerous or bool(entry.get("dangerous"))
    if not errors and not clean:
        errors["_"] = "Wszystkie wartości są już takie same."
    if not errors and dangerous and (confirm_word or "").strip().upper() != DANGER_WORD:
        errors["_"] = "Zmiany obejmują ustawienia oznaczone jako ryzykowne – wpisz %s, aby potwierdzić." % DANGER_WORD
    return clean, errors


def queue_request(spool, changes):
    request_id = "env-" + uuid.uuid4().hex[:20]
    os.makedirs(spool, exist_ok=True)
    payload = {"id": request_id, "time": int(time.time()), "changes": changes}
    temporary = os.path.join(spool, request_id + ".env.new")
    try:
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False)
        os.chmod(temporary, 0o660)
        os.replace(temporary, os.path.join(spool, "env.request"))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    services = env_schema.services_for(changes)
    status = {"id": request_id, "state": "queued", "time": int(time.time()), "source": "panel",
              "message": "Zlecenie zapisane – czeka na aktualizator (zwykle kilka sekund).",
              "services": [s for s in services if s != "updater"], "changed": sorted(changes),
              "results": {k: {"ok": True, "message": "", "secret": bool(env_schema.BY_KEY[k].get("secret"))} for k in changes}}
    temporary = os.path.join(spool, "env.status.panel.new")
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(status, handle, ensure_ascii=False)
    os.replace(temporary, os.path.join(spool, "env.status"))
    return request_id


# ---------------------------------------------------------------- live switches
# MT2009_PLUS_ENV_LIVE_V1: env_schema.LIVE_KEYS are switched in the running
# game the way the classic panel does it (/arezzo, /seonhae, /rare): the event
# flag in player.quest (what the cores read at a start) and a web_admin_queue
# row for web_admin.quest, which sets the flag in the running cores. .env is
# not touched here - the panel has no access to it - the wanted values go to
# env.pending in the spool and the updater writes them into .env, with no
# restart, whenever it runs (env_apply.py apply_pending).
LIVE_WAIT = 6.0
LIVE_FINAL = ("done", "failed", "bad_args", "cancelled", "player_offline")
_FLAGS = ("mt2009_arezzo_closed", "m2_seonhae_on", "m2_seonhae_wait_min", "m2_alchemy_off", "m2_sash_off",
          "m2_teleport_map_on")


def _flag_rows(cur):
    cur.execute("SELECT szName, lValue FROM player.quest WHERE dwPID = 0 AND szName IN (%s)"
                % ",".join(["%s"] * len(_FLAGS)), _FLAGS)
    flags = {}
    for row in cur.fetchall():
        name, value = (row["szName"], row["lValue"]) if isinstance(row, dict) else (row[0], row[1])
        try:
            flags[name] = int(value)
        except (TypeError, ValueError):
            pass
    return flags


def live_values_from_flags(flags):
    out = {}
    if "mt2009_arezzo_closed" in flags:
        out["M2_AREZZO"] = "0" if flags["mt2009_arezzo_closed"] == 1 else "1"
    if "m2_seonhae_on" in flags:
        out["M2_SEONHAE"] = "1" if flags["m2_seonhae_on"] == 1 else "0"
    if "m2_alchemy_off" in flags:
        out["M2_ALCHEMY"] = "0" if flags["m2_alchemy_off"] == 1 else "1"
    if "m2_sash_off" in flags:
        out["M2_SASHES"] = "0" if flags["m2_sash_off"] == 1 else "1"
    # MT2009_PLUS_TELEPORT_MAP_V1 (Autor: Mur4s): no row = off.
    out["M2_TELEPORT_MAP"] = "1" if flags.get("m2_teleport_map_on") == 1 else "0"
    return out


def read_live(db_connect):
    """{KEY: '0'/'1'} of the live switches as the world has them now; None without a database."""
    if db_connect is None:
        return None
    try:
        with db_connect() as con, con.cursor() as cur:
            return live_values_from_flags(_flag_rows(cur))
    except Exception:
        return None


def read_pending(spool):
    data = _read_json(os.path.join(spool, "env.pending"))
    values = data.get("values")
    return values if isinstance(values, dict) else {}


def write_pending(spool, changes):
    """Merge the live-applied values into env.pending (the updater writes them into .env)."""
    values = read_pending(spool)
    values.update(changes)
    os.makedirs(spool, exist_ok=True)
    temporary = os.path.join(spool, "env.pending.panel.new")
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump({"time": int(time.time()), "values": values}, handle, ensure_ascii=False)
    os.chmod(temporary, 0o660)
    os.replace(temporary, os.path.join(spool, "env.pending"))


def apply_live(db_connect, changes, wait=LIVE_WAIT, sleep=time.sleep):
    """Write the flags and queue the in-game switch. Returns {command: status}."""
    with db_connect() as con, con.cursor() as cur:
        flags = _flag_rows(cur)
        now = live_values_from_flags(flags)
        queued = {}

        def flag(name, value):
            cur.execute("REPLACE INTO player.quest (dwPID, szName, szState, lValue) VALUES (0, %s, '', %s)", (name, int(value)))

        def queue(cmd, arg1):
            cur.execute("INSERT INTO player.web_admin_queue (player_name, cmd, arg1, arg2) VALUES ('', %s, %s, '')", (cmd, arg1))
            queued[cmd] = cur.lastrowid

        if "M2_AREZZO" in changes:
            on = 1 if changes["M2_AREZZO"] == "1" else 0
            flag("mt2009_arezzo_closed", 1 - on)
            queue("AREZZO", str(on))
        if "M2_SEONHAE" in changes:
            on = 1 if changes["M2_SEONHAE"] == "1" else 0
            wait_min = max(0, min(10080, flags.get("m2_seonhae_wait_min", 0)))
            flag("m2_seonhae_on", on)
            queue("SEONHAE", "%d,%d" % (on, wait_min))
        if "M2_TELEPORT_MAP" in changes:
            on = 1 if changes["M2_TELEPORT_MAP"] == "1" else 0
            flag("m2_teleport_map_on", on)
            queue("TPMAP", str(on))
        if "M2_ALCHEMY" in changes or "M2_SASHES" in changes:
            alchemy = 1 if changes.get("M2_ALCHEMY", now.get("M2_ALCHEMY", "1")) == "1" else 0
            sashes = 1 if changes.get("M2_SASHES", now.get("M2_SASHES", "1")) == "1" else 0
            flag("m2_alchemy_off", 1 - alchemy)
            flag("m2_sash_off", 1 - sashes)
            queue("RARE", "%d,%d" % (alchemy, sashes))
    result = {cmd: "timeout" for cmd in queued}
    ids = [qid for qid in queued.values() if qid]
    deadline = time.time() + wait
    while ids and time.time() < deadline:
        sleep(0.6)
        with db_connect() as con, con.cursor() as cur:
            cur.execute("SELECT id, status FROM player.web_admin_queue WHERE id IN (%s)" % ",".join(["%s"] * len(ids)), ids)
            got = {}
            for row in cur.fetchall():
                rid, st = (row["id"], row["status"]) if isinstance(row, dict) else (row[0], row[1])
                got[int(rid)] = st
        for cmd, qid in queued.items():
            if got.get(qid) in LIVE_FINAL:
                result[cmd] = got[qid]
        if all(v != "timeout" for v in result.values()):
            break
    left = [queued[c] for c, v in result.items() if v == "timeout" and queued.get(c)]
    if left:
        # Nobody in the game took it (no channel up): the flag is in the
        # database already and the cores read it at their next start.
        try:
            with db_connect() as con, con.cursor() as cur:
                cur.execute("UPDATE player.web_admin_queue SET status='cancelled' WHERE status='pending' AND id IN (%s)"
                            % ",".join(["%s"] * len(left)), left)
        except Exception:
            pass
    return result


def install(app, login_required, csrf_token, spool_getter, db_connect=None):
    def spool():
        return str(spool_getter())

    def live_state(state):
        """The live switches the page may change without the updater."""
        values = read_live(db_connect)
        return {"keys": sorted(env_schema.LIVE_KEYS), "values": values or {},
                "available": values is not None, "pending": read_pending(spool())}

    def save_live(state, live, changes, confirm):
        current = dict(state["current"])
        merged = dict(current.get("values", {}))
        merged.update(live["values"])
        current["values"] = merged
        clean, errors = validate_changes(changes, current, confirm)
        if errors:
            message = errors.pop("_", "") or "Popraw zaznaczone wartości."
            return jsonify({"ok": False, "message": message, "errors": errors}), 400
        other = sorted(k for k in clean if k not in env_schema.LIVE_KEYS)
        if other:
            return jsonify({"ok": False, "message": "Aktualizator nie działa, więc od razu można zmienić tylko przełączniki oznaczone „działa od razu” "
                            "(Arezzo, Seon-Hae, alchemia, szarfy). Tych ustawień nie da się teraz zapisać: %s." % ", ".join(other)}), 409
        try:
            outcome = apply_live(db_connect, clean)
        except Exception:
            app.logger.exception("env editor: live switch failed")
            return jsonify({"ok": False, "message": "Nie udało się połączyć z bazą danych – nic nie zmieniono."}), 500
        pending_saved = True
        try:
            write_pending(spool(), clean)
        except OSError:
            pending_saved = False
        in_game = all(v == "done" for v in outcome.values())
        message = ("Przełączono od razu w działającej grze (bez restartu)." if in_game else
                   "Zapisano w bazie świata. Żaden kanał gry nie potwierdził zmiany w ciągu kilku sekund (serwer gry wyłączony albo dopiero startuje) – zadziała przy jego najbliższym starcie.")
        message += (" Linia w .env zostanie dopisana automatycznie, gdy aktualizator będzie uruchomiony (bez restartu usług)." if pending_saved else
                    " Uwaga: nie udało się zapamiętać zmiany dla aktualizatora – ustaw ją też ręcznie w .env.")
        old = merged
        status = {"id": "live-" + uuid.uuid4().hex[:12], "state": "ok", "time": int(time.time()), "source": "live",
                  "message": message, "services": [], "changed": sorted(clean), "live": outcome,
                  "results": {k: {"ok": True, "message": "", "secret": False, "changed": True, "old": old.get(k), "new": v}
                              for k, v in clean.items()}}
        try:
            temporary = os.path.join(spool(), "env.status.panel.new")
            with open(temporary, "w", encoding="utf-8") as handle:
                json.dump(status, handle, ensure_ascii=False)
            os.replace(temporary, os.path.join(spool(), "env.status"))
        except OSError:
            pass
        app.logger.warning("env editor: live %s (%s)", ", ".join("%s=%s" % kv for kv in sorted(clean.items())), outcome)
        status["busy"] = False
        return jsonify({"ok": True, "live": True, "id": status["id"], "status": status, "live_values": read_live(db_connect) or {}})

    @app.route("/advanced/server-env")
    @login_required
    def server_env():
        state = editor_state(spool())
        current = state["current"]
        live = live_state(state) if not state["ready"] else {"keys": sorted(env_schema.LIVE_KEYS), "values": {}, "available": False, "pending": {}}
        sections = []
        for section in env_schema.SECTIONS:
            if section.get("hidden"):
                continue
            fields = [entry for entry in env_schema.SCHEMA if entry["section"] == section["id"]]
            sections.append(dict(section, fields=fields))
        return render_template("server_env.html", state=state, sections=sections, current=current,
                               values=current.get("values", {}), secrets=current.get("secrets", {}),
                               present=set(current.get("present", [])), overridden=set(current.get("overridden", [])),
                               schema_json=env_schema.public_schema(), service_labels=env_schema.SERVICE_LABELS,
                               env_csrf=csrf_token(), danger_word=DANGER_WORD, live=live, field_count=len(env_schema.SCHEMA),
                               snapshot_when=time.strftime("%d.%m.%Y %H:%M", time.localtime(int(current.get("time") or 0))))

    @app.get("/advanced/server-env/status")
    @login_required
    def server_env_status():
        state = editor_state(spool())
        current = state["current"]
        return jsonify({"ready": state["ready"], "reason": state["reason"], "alive": state["alive"], "status": state["status"],
                        "values": current.get("values", {}), "secrets": current.get("secrets", {}),
                        "present": current.get("present", []), "overridden": current.get("overridden", []),
                        "snapshot_time": current.get("time")})

    @app.post("/advanced/server-env")
    @login_required
    def server_env_save():
        supplied = request.form.get("env_csrf", "")
        expected = session.get("seban_update_csrf", "")
        if not expected or not hmac.compare_digest(supplied, expected):
            abort(403)
        state = editor_state(spool())
        if not state["ready"]:
            live = live_state(state)
            if live["available"]:
                try:
                    changes = json.loads(request.form.get("changes", "") or "{}")
                except ValueError:
                    changes = None
                return save_live(state, live, changes, request.form.get("confirm", ""))
            return jsonify({"ok": False, "message": "Aktualizator nie jest uruchomiony albo nie obsługuje edytora .env – zmiany nie mogą zostać zapisane."}), 409
        if state["status"].get("busy"):
            return jsonify({"ok": False, "message": "Poprzednia zmiana jeszcze trwa. Poczekaj na jej zakończenie."}), 409
        if os.path.exists(os.path.join(spool(), "env.request")):
            return jsonify({"ok": False, "message": "Poprzednie zlecenie czeka na aktualizator."}), 409
        try:
            changes = json.loads(request.form.get("changes", "") or "{}")
        except ValueError:
            changes = None
        clean, errors = validate_changes(changes, state["current"], request.form.get("confirm", ""))
        if errors:
            message = errors.pop("_", "") or "Popraw zaznaczone wartości."
            return jsonify({"ok": False, "message": message, "errors": errors}), 400
        try:
            request_id = queue_request(spool(), clean)
        except OSError:
            return jsonify({"ok": False, "message": "Nie udało się zapisać zlecenia do kolejki aktualizatora."}), 500
        app.logger.warning("env editor: queued %s (%s)", request_id, ", ".join(sorted(clean)))
        return jsonify({"ok": True, "id": request_id, "status": read_status(spool())})

    return server_env
