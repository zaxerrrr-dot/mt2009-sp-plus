"""MT2009_PLUS_DB_EDITOR_V1: "Zastosuj" - the editor's pending changes, one
button that restarts the game cores (ctx["queue_restart"]: the same queued
restart as the chests' "Zastosuj teraz" and "Gra i serwer") and builds the
client data, and the public download of that client data for the players'
launchers.

Pending changes come from the editor's parts themselves:
  * items and skills: common_items.pending_changes() (the history rows not
    yet applied, net per field); common_items.mark_applied() once the
    restart is queued;
  * drop files and chests: dropfiles.pending_changes(<spool>) - the files
    the game does not run yet (it clears its own flags when the game reports
    them applied).

Client data (m2clientpack): every item/skill field the editor ever changed
(common_items.net_changes(include_applied=True)) patched into the released
client's gamedata/locale files, built as an overlay in
<spool>/dbeditor/clientdata/ and served WITHOUT login (they are the same item
names and numbers every player sees in the game) at
  /db/clientdata/manifest.json
  /db/clientdata/<stamp>/<pack>.index|.tail
The launcher (Sync-M2DbEditorClientData) compares the manifest's stamp with
what it laid on the client last time.

COOP (design, not built yet): a friend's client needs the HOST's overlay.
The host would publish these files on a port of their own - a read-only
static server over <spool>/dbeditor/clientdata, not the whole panel with its
login page - forward it like the game ports (UPnP + firewall rule,
Metin2Launcher.Coop.psm1) and put the port in the invite ("cd", a field old
readers skip). The friend's "Dołączam" would then run
Sync-M2DbEditorClientData -BaseUrl http://<host>:<cd>/db/clientdata after
writing coop.cfg; the state remembers the server, so GRAJ on his own world
syncs back to his own panel. Without "cd" the friend keeps his own data.
"""
import json
import os
import re
import time
from pathlib import Path

from flask import abort, flash, redirect, render_template, request, send_file, url_for

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


def install(bp, ctx):
    from dbeditor import add_section, common_items, dropfiles
    import m2clientpack.dbsource as dbsource

    common_items.init(ctx)
    login_required = ctx["login_required"]
    rows = ctx["rows"]
    spool = Path(os.environ.get("DBEDITOR_SPOOL_ROOT") or ctx.get("spool") or "/opt/m2spool")
    client_dir = spool / "dbeditor" / "clientdata"
    last_apply = spool / "dbeditor" / "last-apply.json"
    build_log = spool / "dbeditor" / "clientdata-build.json"

    def query(sql, params=()):
        # looked up per call like items.py does, so tests can swap the database
        return common_items.ctx().get("rows", rows)(sql, params)

    def pending():
        items = common_items.pending_changes()
        try:
            files = dropfiles.pending_changes(spool)
        except Exception:  # never break the page over a spool folder
            files = []
        return items, files

    def manifest():
        return _read_json(client_dir / "manifest.json", None)

    def build_client_data():
        started = time.time()
        try:
            result = dbsource.build_from_db(query, str(client_dir), common_items.net_changes(include_applied=True))
        except Exception as exc:
            _write_json(build_log, {"ok": False, "time": int(started), "error": "%s: %s" % (type(exc).__name__, exc)})
            raise
        _write_json(build_log, {"ok": True, "time": int(started), "seconds": round(time.time() - started, 1),
                                "stamp": result["stamp"]})
        return result

    def restart_state():
        try:
            return ctx["restart_progress"]() if ctx.get("restart_progress") else {}
        except Exception:
            return {}

    @bp.route("/apply", methods=["GET"])
    @login_required
    def apply_page():
        items, files = pending()
        return render_template(
            "dbeditor/clientdata.html", items=items, files=files, last=_read_json(last_apply, {}),
            manifest=manifest(), build=_read_json(build_log, {}), csrf=common_items.csrf_token(),
            restart=restart_state(), column_label=common_items.column_label,
            format_value=common_items.format_value,
            client_url=request.host_url.rstrip("/") + url_for("dbeditor.clientdata_manifest"))

    @bp.route("/apply", methods=["POST"])
    @login_required
    def apply_post():
        if not common_items.check_csrf():
            return redirect(url_for("dbeditor.apply_page"))
        action = request.form.get("action", "apply")
        if action not in ("apply", "client"):
            abort(400)
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
        queue = ctx.get("queue_restart")
        if queue is None:
            flash("Ten panel nie ma funkcji restartu gry.", "error")
            return redirect(url_for("dbeditor.apply_page"))
        items, files = pending()
        try:
            queue()
        except FileExistsError:
            flash("Poprzedni restart jeszcze trwa - poczekaj na jego koniec i kliknij Zastosuj ponownie. "
                  "Dane klienta są już zbudowane.", "error")
            return redirect(url_for("dbeditor.apply_page"))
        except (OSError, RuntimeError) as exc:
            flash("Nie udało się zlecić restartu: %s" % exc, "error")
            return redirect(url_for("dbeditor.apply_page"))
        try:
            marked = common_items.mark_applied()
        except Exception as exc:
            marked = 0
            flash("Restart zlecony, ale nie oznaczono zmian jako zastosowanych: %s" % exc, "warning")
        _write_json(last_apply, {"time": int(time.time()), "when": time.strftime("%d.%m.%Y %H:%M"),
                                 "changes": len(items) + len(files), "history_rows": marked, "stamp": built["stamp"]})
        flash("Restart rdzeni zlecony - gra wczyta zmiany (%d pól, %d plików) po starcie; gracze online zostaną "
              "rozłączeni na ok. minutę. Dane klienta: %s." % (len(items), len(files), packs), "success")
        return redirect(url_for("dbeditor.apply_page"))

    # Public: the launchers download these before starting the client.
    @bp.route("/clientdata/manifest.json")
    def clientdata_manifest():
        path = client_dir / "manifest.json"
        if not path.is_file():
            return {"schema": 1, "stamp": "oryginal", "packs": [], "client": None}
        response = send_file(path, mimetype="application/json", max_age=0)
        response.headers["Cache-Control"] = "no-store"
        return response

    @bp.route("/clientdata/<stamp>/<name>")
    def clientdata_file(stamp, name):
        if not FILE_RE.match("%s/%s" % (stamp, name)):
            abort(404)
        path = client_dir / stamp / name
        if not path.is_file():
            abort(404)
        return send_file(path, mimetype="application/octet-stream", max_age=3600)

    add_section("dbeditor.apply_page", "✅", "Zastosuj",
                "Oczekujące zmiany, restart gry i dane klienta dla graczy.")
