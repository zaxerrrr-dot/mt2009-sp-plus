"""MT2009_PLUS_DB_EDITOR_V1: "Zastosuj" - the editor's pending changes and
one button that restarts the game cores (ctx["queue_restart"]: the same
queued restart as the chests' "Zastosuj teraz" and "Gra i serwer") - and
the client files as a zip to download.

Pending changes come from the editor's parts themselves:
  * items and skills: common_items.pending_changes() (the history rows not
    yet applied, net per field); common_items.mark_applied() once the
    restart is queued;
  * drop files and chests: dropfiles.pending_changes(<spool>) - the files
    the game does not run yet.

Client files (m2clientpack.dbdata): nothing is downloaded automatically - a
player's client may list several servers (localhost, COOP 1, COOP 2). The
operator clicks "Pobierz aktualne pliki klienta" and gets a zip with
pack/dbdata.index + pack/dbdata.data (the release's dbdata pack with every
item/skill field the editor ever changed, common_items.net_changes(
include_applied=True)) and CZYTAJ_MNIE.txt; he unpacks it into his client or
sends it to a friend who plays on this server. "Pobierz oryginalne pliki"
gives the release's own dbdata pack back.
"""
import json
import os
import time
from pathlib import Path

from flask import Response, flash, redirect, render_template, request, url_for

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
    import m2clientpack.dbdata as dbdata

    common_items.init(ctx)
    login_required = ctx["login_required"]
    rows = ctx["rows"]
    spool = Path(os.environ.get("DBEDITOR_SPOOL_ROOT") or ctx.get("spool") or "/opt/m2spool")
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

    def build_zip(original=False):
        """(file name, zip bytes, summary) of the client files."""
        server = request.host.split(":")[0]
        if original:
            base = dbdata.latest_base()
            index, data = base.original()
            name, blob = dbdata.make_zip(base, index, data, server, [], original=True)
            return name, blob, {}
        started = time.time()
        try:
            base, index, data, changed, summary = dbsource.build_dbdata(
                query, common_items.net_changes(include_applied=True))
        except Exception as exc:
            _write_json(build_log, {"ok": False, "time": int(started), "error": "%s: %s" % (type(exc).__name__, exc)})
            raise
        summary["changed_files"] = changed
        _write_json(build_log, {"ok": True, "time": int(started), "when": time.strftime("%d.%m.%Y %H:%M"),
                                "seconds": round(time.time() - started, 1), "client": base.version, "summary": summary})
        name, blob = dbdata.make_zip(base, index, data, server, changed)
        return name, blob, summary

    def base_version():
        try:
            return dbdata.latest_base().version
        except Exception:
            return None

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
            build=_read_json(build_log, {}), csrf=common_items.csrf_token(), client_version=base_version(),
            restart=restart_state(), column_label=common_items.column_label,
            format_value=common_items.format_value)

    @bp.route("/apply", methods=["POST"])
    @login_required
    def apply_post():
        if not common_items.check_csrf():
            return redirect(url_for("dbeditor.apply_page"))
        if request.form.get("confirmation", "").strip().upper() != "RESTART":
            flash("Restartu nie zlecono: aby potwierdzić restart rdzeni, wpisz RESTART.", "error")
            return redirect(url_for("dbeditor.apply_page"))
        queue = ctx.get("queue_restart")
        if queue is None:
            flash("Ten panel nie ma funkcji restartu gry.", "error")
            return redirect(url_for("dbeditor.apply_page"))
        items, files = pending()
        try:
            queue()
        except FileExistsError:
            flash("Poprzedni restart jeszcze trwa - poczekaj na jego koniec i kliknij Zastosuj ponownie.", "error")
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
                                 "changes": len(items) + len(files), "history_rows": marked})
        flash("Restart rdzeni zlecony - gra wczyta zmiany (%d pól, %d plików) po starcie; gracze online zostaną "
              "rozłączeni na ok. minutę. Nowe nazwy i bonusy w kliencie: pobierz aktualne pliki klienta (zip) niżej."
              % (len(items), len(files)), "success")
        return redirect(url_for("dbeditor.apply_page"))

    @bp.route("/clientdata.zip")
    @login_required
    def clientdata_zip():
        original = request.args.get("oryginal") == "1"
        try:
            name, blob, _summary = build_zip(original)
        except Exception as exc:
            flash("Nie udało się zbudować plików klienta: %s" % exc, "error")
            return redirect(url_for("dbeditor.apply_page"))
        return Response(blob, mimetype="application/zip", headers={
            "Content-Disposition": 'attachment; filename="%s"' % name, "Cache-Control": "no-store"})

    add_section("dbeditor.apply_page", "✅", "Zastosuj",
                "Oczekujące zmiany, restart gry i pliki klienta (zip) dla graczy.")
