"""MT2009_PLUS_DB_EDITOR_V1: "Zastosuj" - the editor's pending changes, one
button that restarts the game cores (the same queued restart as the chests'
"Zastosuj teraz" and "Gra i serwer") and builds the client data, and the
public download of that client data for the players' launchers.

Pending changes:
  * rows of player.web_dbeditor_history newer than the last apply (see
    m2clientpack/dbsource.py for the columns read);
  * flag files in /opt/m2spool/dbeditor/pending/ - one per change that is
    not in the database (drop files, chests): any file name, its first line
    is the text shown. Cleared by the apply.
  Both are optional: no table and no folder = nothing pending.

Client data (m2clientpack): the edited items and skills patched into the
released client's gamedata/locale files, built as an overlay in
/opt/m2spool/dbeditor/clientdata/ and served WITHOUT login (they are the
same item names and numbers every player sees in the game) at
  /db/clientdata/manifest.json
  /db/clientdata/<stamp>/<pack>.index|.tail
The launcher (Sync-M2DbEditorClientData) compares the manifest's stamp with
what it laid on the client last time.

COOP (design, not built yet): a friend's client needs the HOST's overlay.
The host would publish these files on a port of their own - a read-only
static server over /opt/m2spool/dbeditor/clientdata, not the whole panel
with its login page - forward it like the game ports (UPnP + firewall rule,
Metin2Launcher.Coop.psm1) and put the port in the invite ("cd", a field old
readers skip). The friend's "Dołączam" would then run
Sync-M2DbEditorClientData -BaseUrl http://<host>:<cd>/db/clientdata after
writing coop.cfg; the state remembers the server, so GRAJ on his own world
syncs back to his own panel. Without "cd" the friend keeps his own data.
"""
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path

from flask import abort, flash, redirect, render_template, request, send_file, session, url_for

SPOOL = Path(os.environ.get("DBEDITOR_SPOOL", "/opt/m2spool/dbeditor"))
PENDING_DIR = SPOOL / "pending"
CLIENT_DIR = SPOOL / "clientdata"
LAST_APPLY = SPOOL / "last-apply.json"
BUILD_LOG = SPOOL / "clientdata-build.json"
FILE_RE = re.compile(r"^[0-9a-f]{16}/(gamedata|locale)\.(index|tail)$")


def _read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    os.replace(tmp, path)


def pending_flags():
    out = []
    try:
        names = sorted(p for p in PENDING_DIR.iterdir() if p.is_file() and not p.name.startswith("."))
    except OSError:
        return out
    for p in names:
        try:
            text = p.read_text(encoding="utf-8", errors="replace").strip().splitlines()
        except OSError:
            continue
        out.append({"name": p.name, "text": (text[0] if text else p.stem)[:300],
                    "time": time.strftime("%d.%m.%Y %H:%M", time.localtime(p.stat().st_mtime))})
    return out


def mark_pending(name, text):
    """For the editor's parts that change files, not tables: a pending
    entry until the next apply."""
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)[:80] or "zmiana"
    (PENDING_DIR / safe).write_text(text + "\n", encoding="utf-8")


def _clear_flags(names):
    for name in names:
        try:
            (PENDING_DIR / name).unlink()
        except OSError:
            pass


def _panel():
    """app.py's module (gunicorn imports it as "app"), for its restart
    helpers; looked up at request time, so this module never imports it."""
    for name in ("app", "__main__"):
        module = sys.modules.get(name)
        if module is not None and hasattr(module, "queue_rate_restart"):
            return module
    return None


def install(bp, ctx):
    from dbeditor import add_section
    import m2clientpack.dbsource as dbsource

    login_required = ctx["login_required"]
    rows = ctx["rows"]

    def query(sql, params=()):
        return rows(sql, params)

    def csrf():
        token = session.get("seban_update_csrf")
        if not token:
            token = uuid.uuid4().hex
            session["seban_update_csrf"] = token
        return token

    def manifest():
        return _read_json(CLIENT_DIR / "manifest.json", None)

    def build_client_data():
        started = time.time()
        try:
            result = dbsource.build_from_db(query, str(CLIENT_DIR))
        except Exception as exc:  # the restart must not hang on this
            _write_json(BUILD_LOG, {"ok": False, "time": int(started), "error": "%s: %s" % (type(exc).__name__, exc)})
            raise
        _write_json(BUILD_LOG, {"ok": True, "time": int(started), "seconds": round(time.time() - started, 1),
                                "stamp": result["stamp"]})
        return result

    def restart_cores():
        panel = _panel()
        queue = ctx.get("queue_restart")
        if queue is None and panel is None:
            raise RuntimeError("Ten panel nie ma funkcji restartu gry.")
        if panel is not None and getattr(panel, "restart_in_flight", lambda: False)():
            raise FileExistsError("restart w toku")
        if queue is not None:
            queue()
        else:
            panel.queue_rate_restart(panel.read_rates())

    def restart_state():
        panel = _panel()
        try:
            return panel.restart_progress() if panel is not None else {}
        except Exception:
            return {}

    @bp.route("/apply", methods=["GET"])
    @login_required
    def apply_page():
        last = _read_json(LAST_APPLY, {})
        history = dbsource.history(query, after_id=last.get("history_id"), limit=500)
        return render_template(
            "dbeditor/clientdata.html", history=history, flags=pending_flags(), last=last,
            manifest=manifest(), build=_read_json(BUILD_LOG, {}), csrf=csrf(), restart=restart_state(),
            history_table=dbsource.table_exists(query, dbsource.HISTORY),
            client_url=request.host_url.rstrip("/") + url_for("dbeditor.clientdata_manifest"))

    @bp.route("/apply", methods=["POST"])
    @login_required
    def apply_post():
        if request.form.get("csrf", "") != session.get("seban_update_csrf", "") or not request.form.get("csrf"):
            flash("Sesja wygasła - odśwież stronę i spróbuj jeszcze raz.", "error")
            return redirect(url_for("dbeditor.apply_page"))
        action = request.form.get("action", "apply")
        if action not in ("apply", "client"):
            abort(400)
        last = _read_json(LAST_APPLY, {})
        history = dbsource.history(query, after_id=last.get("history_id"))
        flags = pending_flags()
        try:
            built = build_client_data()
        except Exception as exc:
            flash("Nie udało się zbudować danych klienta: %s. Serwera nie restartowano." % exc, "error")
            return redirect(url_for("dbeditor.apply_page"))
        packs = ", ".join(p["name"] for p in built["packs"]) or "bez zmian względem klienta"
        if action == "client":
            flash("Dane klienta zbudowane (%s, znacznik %s). Launchery graczy pobiorą je przy następnym GRAJ."
                  % (packs, built["stamp"]), "success")
            return redirect(url_for("dbeditor.apply_page"))
        if request.form.get("confirmation", "").strip().upper() != "RESTART":
            flash("Dane klienta zbudowane, ale restartu nie zlecono: aby potwierdzić restart rdzeni, wpisz RESTART.", "error")
            return redirect(url_for("dbeditor.apply_page"))
        try:
            restart_cores()
        except FileExistsError:
            flash("Poprzedni restart jeszcze trwa - poczekaj na jego koniec i kliknij Zastosuj ponownie. "
                  "Dane klienta są już zbudowane.", "error")
            return redirect(url_for("dbeditor.apply_page"))
        except (OSError, RuntimeError) as exc:
            flash("Nie udało się zlecić restartu: %s" % exc, "error")
            return redirect(url_for("dbeditor.apply_page"))
        history_id = max([h["id"] for h in history if isinstance(h.get("id"), int)] + [last.get("history_id") or 0])
        _write_json(LAST_APPLY, {"time": int(time.time()), "when": time.strftime("%d.%m.%Y %H:%M"), "history_id": history_id or None,
                                 "changes": len(history) + len(flags), "stamp": built["stamp"]})
        _clear_flags([f["name"] for f in flags])
        flash("Restart rdzeni zlecony - gra wczyta zmiany (%d) po starcie; gracze online zostaną rozłączeni na ok. "
              "minutę. Dane klienta: %s." % (len(history) + len(flags), packs), "success")
        return redirect(url_for("dbeditor.apply_page"))

    # Public: the launchers download these before starting the client.
    @bp.route("/clientdata/manifest.json")
    def clientdata_manifest():
        path = CLIENT_DIR / "manifest.json"
        if not path.is_file():
            return {"schema": 1, "stamp": "oryginal", "packs": [], "client": None}
        response = send_file(path, mimetype="application/json", max_age=0)
        response.headers["Cache-Control"] = "no-store"
        return response

    @bp.route("/clientdata/<stamp>/<name>")
    def clientdata_file(stamp, name):
        rel = "%s/%s" % (stamp, name)
        if not FILE_RE.match(rel):
            abort(404)
        path = CLIENT_DIR / stamp / name
        if not path.is_file():
            abort(404)
        return send_file(path, mimetype="application/octet-stream", max_age=3600)

    ctx["dbeditor_mark_pending"] = mark_pending
    add_section("dbeditor.apply_page", "✅", "Zastosuj",
                "Oczekujące zmiany, restart gry i dane klienta dla graczy.")
