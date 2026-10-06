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


def install(app, login_required, csrf_token, spool_getter):
    def spool():
        return str(spool_getter())

    @app.route("/advanced/server-env")
    @login_required
    def server_env():
        state = editor_state(spool())
        current = state["current"]
        sections = []
        for section in env_schema.SECTIONS:
            fields = [entry for entry in env_schema.SCHEMA if entry["section"] == section["id"]]
            sections.append(dict(section, fields=fields))
        return render_template("server_env.html", state=state, sections=sections, current=current,
                               values=current.get("values", {}), secrets=current.get("secrets", {}),
                               present=set(current.get("present", [])), overridden=set(current.get("overridden", [])),
                               schema_json=env_schema.public_schema(), service_labels=env_schema.SERVICE_LABELS,
                               env_csrf=csrf_token(), danger_word=DANGER_WORD, field_count=len(env_schema.SCHEMA),
                               snapshot_when=time.strftime("%d.%m.%Y %H:%M", time.localtime(int(current.get("time") or 0))))

    @app.get("/advanced/server-env/status")
    @login_required
    def server_env_status():
        state = editor_state(spool())
        current = state["current"]
        return jsonify({"ready": state["ready"], "reason": state["reason"], "status": state["status"],
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
