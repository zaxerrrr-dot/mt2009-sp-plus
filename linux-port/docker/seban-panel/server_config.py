"""MT2009_PLUS_SERVER_CONFIG_V1: "Konfiguracja serwera" - whole configurations at once.

The owner (3 November 2026) brought a first-run "server configurator" made
elsewhere: a wizard with three profiles (SAPPHIRE, CLEAN GLOBAL EASY / HARD)
that wrote .env from a web form in its own container. Its ideas are kept, its
way is not (KONFIGURATOR-ANALIZA.md): a profile here is data
(server_profiles.txt) and is applied only through the paths the panel already
trusts -

* .env settings: env_schema.validate, then the live switches
  (env_schema.LIVE_KEYS - Arezzo, Seon-Hae, alchemy, sashes, the monsters'
  health and damage...) at once in the running game through env_editor.apply_live
  with their .env lines left to the updater in env.pending (no restart), and
  everything else as one env.request for the updater, which validates it
  again, writes .env and recreates exactly the services concerned;
* rates: the "Gra i serwer -> Raty" path (queue_rate_restart: the flags and
  one restart of the cores);
* events: rows added to the events planner's file through its own
  read_events / write_events - nothing there is removed.

Every apply is written to a history in the update spool (who changed what,
from what to what). The page's "Ustawienia" part shows groups of .env
settings (also data, the [group] blocks) and saves them through the .env
editor's own endpoint, so CSRF, validation, the typed confirmation of risky
settings and the live / updater split are the editor's.

The parser and the planner are pure and unit-tested (test_server_config.py);
install() takes the panel's functions it needs as arguments, so this module
imports nothing of app.py.
"""
import hmac
import json
import os
import re
import time
import uuid

from flask import flash, redirect, render_template, request, session, url_for

import env_editor
import env_schema

PROFILES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server_profiles.txt")
HISTORY_FILE = "server-config.history.json"
STATE_FILE = "server-config.json"
HISTORY_MAX = 100
CONFIRM_WORD = "ZASTOSUJ"
RATE_NAMES = ("exp", "drop", "yang")
EVENT_ROWS_MAX = 64  # the planner's own limit (events.html)
_ID = re.compile(r"[a-z0-9_]{1,32}")
_HHMM = re.compile(r"([01]\d|2[0-4]):([0-5]\d)")
PARTS = ("env", "rates", "events")


class ProfileError(ValueError):
    pass


def _env_allowed(key, value):
    """None when a profile or a group may carry this .env key, else why not."""
    entry = env_schema.BY_KEY.get(key)
    if entry is None:
        return "nieznana zmienna %s" % key
    if entry.get("secret") or entry.get("readonly"):
        return "%s: hasła i ustawień tylko do odczytu nie ustawia profil" % key
    if any(section["id"] == entry["section"] and section.get("hidden") for section in env_schema.SECTIONS):
        return "%s: ukryta sekcja" % key
    if value is not None:
        if entry.get("dangerous"):
            return "%s: ryzykowne ustawienie (porty, adresy) nie należy do profilu" % key
        reason = env_schema.validate(key, value)
        if reason:
            return "%s: %s" % (key, reason)
    return None


def _event(fields, line_no):
    """event KIND DAYS FROM TO VALUE [MAP [TARGET]] -> a planner row (kind unchecked here)."""
    if not 5 <= len(fields) <= 7:
        raise ProfileError("linia %d: event KIND DNI OD DO WARTOŚĆ [MAPA [CEL]]" % line_no)
    kind, days, start, end = fields[0], fields[1], fields[2], fields[3]
    if not re.fullmatch(r"[a-z]{2,16}", kind):
        raise ProfileError("linia %d: nieprawidłowy rodzaj eventu" % line_no)
    if days == "*":
        day_list = list(range(1, 8))
    elif re.fullmatch(r"[1-7](,[1-7])*", days):
        day_list = sorted(set(int(day) for day in days.split(",")))
    else:
        raise ProfileError("linia %d: dni to * albo 1..7 po przecinku" % line_no)
    for text in (start, end):
        match = _HHMM.fullmatch(text)
        if not match or (match.group(1) == "24" and match.group(2) != "00"):
            raise ProfileError("linia %d: godzina %s (HH:MM)" % (line_no, text))
    if start == "24:00":
        raise ProfileError("linia %d: start nie może być 24:00" % line_no)
    numbers = []
    for text in fields[4:]:
        if not re.fullmatch(r"\d{1,9}", text):
            raise ProfileError("linia %d: wartość, mapa i cel to liczby" % line_no)
        numbers.append(int(text))
    value = numbers[0]
    row = {"kind": kind, "days": day_list, "start": start, "end": end, "value": value,
           "map": numbers[1] if len(numbers) > 1 else 0, "on": True}
    if len(numbers) > 2:
        if numbers[2] not in (0, 1, 2):
            raise ProfileError("linia %d: cel dropu 0, 1 albo 2" % line_no)
        row["target"] = numbers[2]
    return row


def parse(text):
    """{'profiles': [...], 'groups': [...]} from server_profiles.txt; ProfileError on any bad line."""
    profiles, groups, current = [], [], None
    seen = set()
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        header = re.fullmatch(r"\[(profile|group) ([a-z0-9_]{1,32})\]", line)
        if header:
            kind, ident = header.groups()
            if (kind, ident) in seen:
                raise ProfileError("linia %d: %s %s drugi raz" % (line_no, kind, ident))
            seen.add((kind, ident))
            if kind == "profile":
                current = {"type": "profile", "id": ident, "title": ident, "desc": "", "env": {}, "rates": {}, "events": []}
                profiles.append(current)
            else:
                current = {"type": "group", "id": ident, "title": ident, "desc": "", "keys": [], "links": []}
                groups.append(current)
            continue
        if current is None:
            raise ProfileError("linia %d: najpierw [profile ...] albo [group ...]" % line_no)
        match = re.fullmatch(r"(title|desc)\s*=\s*(.+)", line)
        if match:
            current[match.group(1)] = match.group(2).strip()
            continue
        if current["type"] == "profile":
            match = re.fullmatch(r"env\s+([A-Z][A-Z0-9_]*)\s*=\s*(\S*)", line)
            if match:
                key, value = match.groups()
                reason = _env_allowed(key, value)
                if reason:
                    raise ProfileError("linia %d: %s" % (line_no, reason))
                current["env"][key] = value
                continue
            match = re.fullmatch(r"rate\s+(exp|drop|yang)\s*=\s*(\d{1,5})", line)
            if match:
                name, value = match.group(1), int(match.group(2))
                if not 1 <= value <= (1000 if name == "yang" else 10000):
                    raise ProfileError("linia %d: rate %s poza zakresem" % (line_no, name))
                current["rates"][name] = value
                continue
            if line.startswith("event ") or line.startswith("event\t"):
                current["events"].append(_event(line.split()[1:], line_no))
                continue
        else:
            match = re.fullmatch(r"keys\s*=\s*([A-Z0-9_ ]+)", line)
            if match:
                for key in match.group(1).split():
                    reason = _env_allowed(key, None)
                    if reason:
                        raise ProfileError("linia %d: %s" % (line_no, reason))
                    current["keys"].append(key)
                continue
            match = re.fullmatch(r"link\s*=\s*([a-z_.]{1,40})\s*\|\s*(.+)", line)
            if match:
                current["links"].append({"endpoint": match.group(1), "text": match.group(2).strip()})
                continue
        raise ProfileError("linia %d: nie rozumiem: %s" % (line_no, line[:60]))
    for profile in profiles:
        if not (profile["env"] or profile["rates"] or profile["events"]):
            raise ProfileError("profil %s niczego nie ustawia" % profile["id"])
    return {"profiles": profiles, "groups": groups}


def load(path=PROFILES_FILE):
    with open(path, encoding="utf-8") as handle:
        return parse(handle.read())


def check_event_kinds(profiles, kinds, keyed_kinds=("tanaka", "zuo", "chestdrop")):
    """Kinds the planner knows, and a map column only where it has one."""
    for profile in profiles:
        for row in profile["events"]:
            if row["kind"] not in kinds:
                raise ProfileError("profil %s: nieznany event %s" % (profile["id"], row["kind"]))
            if row["kind"] not in keyed_kinds and row.get("map"):
                raise ProfileError("profil %s: event %s nie ma kolumny mapy" % (profile["id"], row["kind"]))
            if "target" in row and row["kind"] != "chestdrop":
                raise ProfileError("profil %s: cel dropu ma tylko chestdrop" % profile["id"])
            if row["kind"] == "chestdrop" and not 1 <= row["value"] <= 1000:
                raise ProfileError("profil %s: szansa chestdrop 1-1000 promili" % profile["id"])


def _row_key(row):
    return (row["kind"], tuple(row["days"]), row["start"], row["end"], int(row.get("value", 0)),
            int(row.get("map", 0)), int(row.get("target", 0) or 0))


def merge_events(existing, wanted):
    """(rows, added): the planner's rows with the profile's appended, an
    identical row (switched on or off) never twice."""
    have = {_row_key(row) for row in existing}
    rows, added = list(existing), 0
    for row in wanted:
        if _row_key(row) in have:
            continue
        have.add(_row_key(row))
        rows.append(dict(row))
        added += 1
    return rows, added


def _shown(key, value):
    entry = env_schema.BY_KEY.get(key, {})
    for option, label in entry.get("options", []):
        if option == value:
            return label
    return value if value not in (None, "") else "(puste)"


def plan(profile, env_values, rates, event_rows):
    """What applying the profile would change, part by part (pure)."""
    env_changes = []
    for key, value in profile["env"].items():
        old = env_values.get(key)
        if old is None:
            old = env_schema.BY_KEY[key].get("default", "")
        same = old == value
        if key in ("M2_MONSTER_HP", "M2_MONSTER_ATTACK"):
            same = env_schema.monster_percent(old) == env_schema.monster_percent(value)
        if not same:
            env_changes.append({"key": key, "label": env_schema.BY_KEY[key]["label"], "old": _shown(key, old),
                                "new": _shown(key, value), "value": value, "live": key in env_schema.LIVE_KEYS})
    rate_changes = [{"name": name, "old": rates.get(name), "new": value}
                    for name, value in profile["rates"].items() if rates.get(name) != value]
    _rows, added = merge_events(event_rows, profile["events"])
    return {"env": env_changes, "rates": rate_changes, "events": added,
            "events_total": len(event_rows) + added, "events_fit": len(event_rows) + added <= EVENT_ROWS_MAX}


def read_history(spool):
    try:
        with open(os.path.join(spool, HISTORY_FILE), encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def append_history(spool, entry):
    history = (read_history(spool) + [entry])[-HISTORY_MAX:]
    os.makedirs(spool, exist_ok=True)
    temporary = os.path.join(spool, HISTORY_FILE + ".new")
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(history, handle, ensure_ascii=False)
    os.replace(temporary, os.path.join(spool, HISTORY_FILE))


def read_state(spool):
    return env_editor._read_json(os.path.join(spool, STATE_FILE))


def write_state(spool, state):
    os.makedirs(spool, exist_ok=True)
    temporary = os.path.join(spool, STATE_FILE + ".new")
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False)
    os.replace(temporary, os.path.join(spool, STATE_FILE))


def first_run(state, env_values):
    """The page's banner: no profile applied or dismissed yet. The installer's
    choice (M2_SERVER_PROFILE) is named when there is one."""
    if state.get("applied") or state.get("dismissed"):
        return None
    return {"installer_profile": env_values.get("M2_SERVER_PROFILE") or ""}


def install(app, login_required, csrf_token, spool_getter, *, db_connect, read_rates, queue_rate_restart,
            restart_in_flight, read_events, write_events, event_kinds, keyed_kinds):
    """Registers the page. The callables are the panel's own (app.py)."""

    def spool():
        return str(spool_getter())

    def catalogue():
        data = load()
        check_event_kinds(data["profiles"], event_kinds, keyed_kinds)
        return data

    def current_values(editor):
        values = dict(editor["current"].get("values", {}))
        if not editor["ready"]:
            live = env_editor.read_live(db_connect)
            if live:
                values.update(live)
        return values

    def safe_rates():
        try:
            return read_rates()
        except Exception:
            return {}

    @app.context_processor
    def _server_config_banner():
        # The dashboard's reminder; cheap - two small files of the spool.
        try:
            state = read_state(spool())
            values = env_editor.editor_state(spool())["current"].get("values", {})
            return {"server_config_first_run": first_run(state, values)}
        except Exception:
            return {"server_config_first_run": None}

    @app.route("/advanced/server-config")
    @login_required
    def server_config():
        try:
            data = catalogue()
            error = ""
        except (OSError, ProfileError) as exc:
            data, error = {"profiles": [], "groups": []}, str(exc)
        editor = env_editor.editor_state(spool())
        values = current_values(editor)
        rates = safe_rates()
        try:
            event_rows, _nows = read_events()
        except Exception:
            event_rows = []
        plans = {profile["id"]: plan(profile, values, rates, event_rows) for profile in data["profiles"]}
        state = read_state(spool())
        groups = []
        for group in data["groups"]:
            fields = [dict(env_schema.BY_KEY[key], current=values.get(key, env_schema.BY_KEY[key].get("default", "")))
                      for key in group["keys"]]
            groups.append(dict(group, fields=fields))
        live = {"available": not editor["ready"] and env_editor.read_live(db_connect) is not None,
                "keys": sorted(env_schema.LIVE_KEYS)}
        return render_template("server_config.html", profiles=data["profiles"], plans=plans, groups=groups,
                               error=error, editor=editor, live=live, rates=rates, state=state,
                               first_run=first_run(state, values), history=list(reversed(read_history(spool())))[:20],
                               config_csrf=csrf_token(), confirm_word=CONFIRM_WORD, event_rows_max=EVENT_ROWS_MAX,
                               danger_word=env_editor.DANGER_WORD,
                               env_save_url=url_for("server_env_save"), env_status_url=url_for("server_env_status"))

    def check_csrf():
        supplied = request.form.get("config_csrf", "")
        expected = session.get("seban_update_csrf", "")
        return bool(expected) and hmac.compare_digest(supplied, expected)

    @app.post("/advanced/server-config/dismiss")
    @login_required
    def server_config_dismiss():
        if not check_csrf():
            flash("Sesja wygasła – odśwież stronę.", "error")
            return redirect(url_for("server_config"))
        state = read_state(spool())
        state["dismissed"] = int(time.time())
        write_state(spool(), state)
        return redirect(url_for("server_config"))

    @app.post("/advanced/server-config/apply")
    @login_required
    def server_config_apply():
        if not check_csrf():
            flash("Sesja wygasła – odśwież stronę i spróbuj jeszcze raz.", "error")
            return redirect(url_for("server_config"))
        try:
            data = catalogue()
        except (OSError, ProfileError) as exc:
            flash("Plik konfiguracji jest uszkodzony: %s" % exc, "error")
            return redirect(url_for("server_config"))
        profile = next((p for p in data["profiles"] if p["id"] == request.form.get("profile")), None)
        if profile is None:
            flash("Nie ma takiej konfiguracji.", "error")
            return redirect(url_for("server_config"))
        parts = [part for part in PARTS if request.form.get("part_" + part) == "1"]
        if not parts:
            flash("Zaznacz, co zastosować: ustawienia, raty albo kalendarz eventów.", "error")
            return redirect(url_for("server_config"))
        if (request.form.get("confirm") or "").strip().upper() != CONFIRM_WORD:
            flash("Wpisz %s, aby potwierdzić zastosowanie konfiguracji „%s”." % (CONFIRM_WORD, profile["title"]), "error")
            return redirect(url_for("server_config"))

        editor = env_editor.editor_state(spool())
        values = current_values(editor)
        rates = safe_rates()
        try:
            event_rows, nows = read_events()
        except Exception:
            event_rows, nows = [], {}
        todo = plan(profile, values, rates, event_rows)

        # Everything is checked before anything is written: a profile is
        # applied whole (the parts ticked) or not at all.
        env_changes = {c["key"]: c["value"] for c in todo["env"]} if "env" in parts else {}
        live_changes = {k: v for k, v in env_changes.items() if k in env_schema.LIVE_KEYS}
        queued_changes = {k: v for k, v in env_changes.items() if k not in env_schema.LIVE_KEYS}
        rate_values = None
        if "rates" in parts and todo["rates"]:
            rate_values = {name: int(rates.get(name) or 100) for name in RATE_NAMES}
            rate_values.update(profile["rates"])
        add_events = "events" in parts and todo["events"] > 0
        problems = []
        if queued_changes:
            if not editor["ready"]:
                problems.append("aktualizator nie działa, więc ustawień %s nie da się teraz zapisać do .env "
                                "(uruchom aktualizator albo odznacz „ustawienia”)" % ", ".join(sorted(queued_changes)))
            elif editor["status"].get("busy") or os.path.exists(os.path.join(spool(), "env.request")):
                problems.append("poprzednia zmiana .env jeszcze trwa – poczekaj na jej zakończenie")
        if live_changes and not editor["ready"] and env_editor.read_live(db_connect) is None:
            problems.append("brak połączenia z bazą świata – przełączników nie da się zmienić")
        if rate_values and restart_in_flight():
            problems.append("restart serwera jeszcze trwa – raty zastosujesz po jego zakończeniu")
        if add_events and not todo["events_fit"]:
            problems.append("w Planerze eventów zmieści się najwyżej %d wierszy (byłoby %d) – usuń część starych"
                            % (EVENT_ROWS_MAX, todo["events_total"]))
        if problems:
            flash("Nic nie zmieniono: " + "; ".join(problems) + ".", "error")
            return redirect(url_for("server_config"))
        if not (env_changes or rate_values or add_events):
            flash("Konfiguracja „%s” jest już zastosowana – nic do zmiany." % profile["title"])
            return redirect(url_for("server_config"))

        done, notes = [], []
        if live_changes:
            try:
                outcome = env_editor.apply_live(db_connect, live_changes)
                env_editor.write_pending(spool(), live_changes)
                in_game = all(v == "done" for v in outcome.values())
                done.append("przełączniki %s %s" % (", ".join(sorted(live_changes)),
                                                    "zmienione od razu w grze" if in_game else "zapisane (zadziałają przy najbliższym starcie gry)"))
            except Exception:
                app.logger.exception("server config: live switches failed")
                flash("Nie udało się połączyć z bazą świata – przełączników nie zmieniono.", "error")
                return redirect(url_for("server_config"))
        if queued_changes:
            try:
                request_id = env_editor.queue_request(spool(), queued_changes)
                done.append("zlecenie .env %s (%s) – aktualizator zapisze je i uruchomi ponownie potrzebne usługi"
                            % (request_id, ", ".join(sorted(queued_changes))))
                notes.append("serwer gry zostanie uruchomiony ponownie przez aktualizator")
            except OSError:
                flash("Nie udało się zapisać zlecenia do kolejki aktualizatora.", "error")
                return redirect(url_for("server_config"))
        if rate_values:
            try:
                queue_rate_restart(rate_values)
                done.append("raty %s" % ", ".join("%s %d%%" % (n, rate_values[n]) for n in RATE_NAMES))
                notes.append("raty działają po restarcie rdzeni, który został zlecony")
            except OSError:
                flash("Nie udało się zapisać zlecenia rat.", "error")
                return redirect(url_for("server_config"))
        if add_events:
            rows, added = merge_events(event_rows, profile["events"])
            try:
                write_events(rows, nows)
                done.append("%d wierszy w Planerze eventów" % added)
            except OSError:
                flash("Nie udało się zapisać Planera eventów.", "error")
                return redirect(url_for("server_config"))

        entry = {"id": "cfg-" + uuid.uuid4().hex[:12], "time": int(time.time()), "profile": profile["id"],
                 "title": profile["title"], "parts": parts,
                 "env": [{"key": c["key"], "old": c["old"], "new": c["new"]} for c in todo["env"] if c["key"] in env_changes],
                 "rates": todo["rates"] if rate_values else [], "events_added": todo["events"] if add_events else 0}
        try:
            append_history(spool(), entry)
            state = read_state(spool())
            state.update({"applied": profile["id"], "applied_title": profile["title"], "applied_time": entry["time"]})
            write_state(spool(), state)
        except OSError:
            notes.append("historii zmian nie udało się zapisać")
        app.logger.warning("server config: %s applied (%s)", profile["id"], "; ".join(done))
        flash("Zastosowano „%s”: %s.%s" % (profile["title"], "; ".join(done),
                                          (" Uwaga: " + "; ".join(notes) + ".") if notes else ""))
        return redirect(url_for("server_config"))

    return server_config
