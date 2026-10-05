"""MT2009_PLUS_DB_EDITOR_REAPPLY_V1: the editor's history against the data.

The history (player.web_dbeditor_history, common_items.py) says what the
operator changed; the tables say what the game runs. The two part ways
when the database is put back without the panel - "Reset całego świata"
(m2-world-reset imports the shipped dumps again) or a backup of the player
database restored by hand: the history stays, the values are the image's
again, and an undo refuses ("Pole zmieniono później jeszcze raz...").

  * replay_sql(request_id): the net effect of the whole history
    (common_items.net_changes(include_applied=True)) as plain-ASCII SQL -
    every value a number or a hex literal. The panel writes it into the
    spool with a "Reset całego świata" that keeps the editor's changes, and
    m2-world-reset runs it after the migrator, before the cores boot.
  * drift(): each net field / whole row of the history classified by what
    the database holds now - "sync" (the newest value), "restore" (the value
    from before the first edit: the data was reset under the history) or
    "conflict" (neither: listed, never touched).
  * restore(): the "restore" ones written back as one save (one batch,
    note RESTORE_NOTE), so the history and the data agree again.
  * label resolvers: a history label kept as "Zwi?kszenie Ataku" (a backup
    dumped as latin1 turns every Polish letter outside latin1 into "?") is
    shown - and on restore() stored - from the current name instead.

The page /db/historia/przywroc lists all of it; the hub shows a notice while
there is something to restore.
"""
import json
import re
import time

from flask import flash, redirect, render_template, request, url_for

from dbeditor import common_items as common

MARKER = "MT2009_PLUS_DB_EDITOR_REAPPLY_V1"
RESTORE_NOTE = "Przywrócenie po resecie świata"
_NAME = re.compile(r"^\w+\.\w+$")
_COL = re.compile(r"^\w+$")
_INT = re.compile(r"^-?\d+$")
# The hub asks on every visit; a few hundred keys are read once a minute at most.
_CACHE = {"at": 0.0, "result": None}
CACHE_SECONDS = 60


# ---- labels ------------------------------------------------------------------------

def _skill_label(row_key):
    try:
        from dbeditor import skills
        name = skills.SKILL_NAMES_PL.get(int(row_key))
    except (ImportError, ValueError, AttributeError):
        name = None
    if name:
        return name
    found = common.ctx()["rows"]("SELECT CAST(`szName` AS BINARY) AS `szName` FROM world.skill_proto "
                                 "WHERE `dwVnum`=%s", (row_key,))
    return common.text_of(found[0]["szName"]) if found else None


def _name_label(table, key_col, name_col):
    def resolve(row_key):
        found = common.ctx()["rows"](f"SELECT CAST(`{name_col}` AS BINARY) AS `{name_col}` FROM {table} "
                                     f"WHERE `{key_col}`=%s", (str(row_key).split(":")[0],))
        return common.text_of(found[0][name_col]).strip() if found else None
    return resolve


def register_label_resolvers():
    items = _name_label("world.item_proto", "vnum", "locale_name")
    common.LABEL_RESOLVERS.setdefault("world.skill_proto", _skill_label)
    common.LABEL_RESOLVERS.setdefault("world.item_proto", items)
    common.LABEL_RESOLVERS.setdefault("world.item_extra_apply", items)  # row_key vnum:slot
    # world.shop_item: row_key shop:item:count - the item is the second part
    common.LABEL_RESOLVERS.setdefault(
        "world.shop_item", lambda key: items(str(key).split(":")[1]) if ":" in str(key) else None)
    common.LABEL_RESOLVERS.setdefault("world.mob_proto", _name_label("world.mob_proto", "vnum", "locale_name"))


def repair_labels():
    """Store the resolved label for every history row whose label is broken
    ("?" in place of Polish letters). Returns the number of rows fixed."""
    common.ensure_table()
    found = common.ctx()["rows"](f"SELECT DISTINCT tbl, row_key, label FROM {common.HISTORY_TABLE} "
                                 "WHERE label LIKE '%%?%%'")
    fixed = 0
    for row in found:
        label = common.display_label(row)
        if label and label != row["label"]:
            common.ctx()["rows"](f"UPDATE {common.HISTORY_TABLE} SET label=%s WHERE tbl=%s AND row_key=%s AND label=%s",
                                 (label[:100], row["tbl"], row["row_key"], row["label"]))
            fixed += 1
    return fixed


# ---- the world reset's replay ---------------------------------------------------------

def _hex(text, encoding):
    data = str(text).encode(encoding, "replace")
    return "X'%s'" % data.hex() if data else "''"


def _literal(spec, value):
    if value is None:
        return "NULL"
    kind = spec.get("kind")
    if kind == "int":
        text = str(value).strip()
        if not _INT.match(text):
            raise ValueError(value)
        return text
    return _hex(value, "cp1250" if kind == "cp1250" else "utf-8")


def _key_literal(row_key):
    text = str(row_key)
    return text if _INT.match(text) else _hex(text, "utf-8")


def replay_statements(changes=None):
    """([SQL statement], [skipped history description]) setting every net
    change of the history again. ASCII only: names and formulas as hex."""
    changes = common.net_changes(include_applied=True) if changes is None else changes
    statements, skipped = [], []
    for row in changes:
        table, col, row_key = row["tbl"], row["col"], row["row_key"]
        meta = common.TABLES.get(table)
        what = f"{table} {row_key} {col}"
        if not meta or not _NAME.match(table):
            skipped.append(what + " (tabela nieznana panelowi)")
            continue
        try:
            if col == common.ROW_COL:
                if not meta.get("row_cols"):
                    skipped.append(what + " (tabela bez całych wierszy)")
                    continue
                keys = common.key_values(table, row_key)
                where = " AND ".join(f"`{c}`={int(keys[c])}" for c in common.key_cols(table))
                statements.append(f"DELETE FROM {table} WHERE {where};")
                if row["new_value"] is not None:
                    values = json.loads(row["new_value"])
                    cols = meta["row_cols"]
                    statements.append(f"INSERT INTO {table} ({', '.join('`%s`' % c for c in cols)}) VALUES "
                                      f"({', '.join(str(int(values.get(c) or 0)) for c in cols)});")
                continue
            spec = meta["cols"].get(col)
            key = meta["key"]
            if spec is None or not _COL.match(col) or isinstance(key, (tuple, list)):
                skipped.append(what + " (pole nieedytowalne)")
                continue
            statements.append(f"UPDATE {table} SET `{col}`={_literal(spec, row['new_value'])} "
                              f"WHERE `{key}`={_key_literal(row_key)};")
        except (ValueError, TypeError, KeyError) as exc:
            skipped.append(f"{what} ({exc})")
    return statements, skipped


def replay_sql(request_id, changes=None):
    statements, skipped = replay_statements(changes)
    lines = [f"-- id={request_id}",
             f"-- {MARKER}: the Seban panel's database editor changes, set again after the world reset",
             f"-- {len(statements)} statements; skipped: {len(skipped)}",
             "SET SESSION sql_mode='';"]
    lines += ["-- skipped: " + s.encode("ascii", "replace").decode("ascii").replace("\n", " ") for s in skipped]
    lines += statements
    return "\n".join(lines) + "\n"


# ---- drift -----------------------------------------------------------------------------

def _current_values(table, key, cols):
    try:
        return common.read_row(table, key, cols)
    except Exception:
        return None


def drift(changes=None):
    """{"restore": [...], "conflict": [...], "sync": n, "skipped": [...]}; each
    entry a net history row plus "current" (text) and "reason"."""
    changes = common.net_changes(include_applied=True) if changes is None else changes
    result = {"restore": [], "conflict": [], "sync": 0, "skipped": []}
    by_key = {}
    for row in changes:
        by_key.setdefault((row["tbl"], row["row_key"]), []).append(row)
    for (table, row_key), group in by_key.items():
        meta = common.TABLES.get(table)
        if not meta:
            result["skipped"].extend(group)
            continue
        fields = [r for r in group if r["col"] != common.ROW_COL and r["col"] in meta["cols"]]
        current = _current_values(table, row_key, [r["col"] for r in fields]) if fields else None
        for row in group:
            entry = dict(row, label=common.display_label(row))
            if row["col"] == common.ROW_COL:
                if not meta.get("row_cols"):
                    result["skipped"].append(entry)
                    continue
                whole = common.read_whole_row(table, row_key)
                now = common.row_json(table, whole) if whole is not None else None
                entry["current"] = now
                if now == row["new_value"]:
                    result["sync"] += 1
                elif now == row["old_value"]:
                    result["restore"].append(entry)
                else:
                    entry["reason"] = "wiersz jest teraz inny"
                    result["conflict"].append(entry)
                continue
            spec = meta["cols"].get(row["col"])
            if spec is None:
                result["skipped"].append(entry)
                continue
            if current is None:
                entry["current"], entry["reason"] = None, "wiersza nie ma w bazie"
                result["conflict"].append(entry)
                continue
            value = current[row["col"]]
            entry["current"] = common.text_of(value)
            if common._same(spec, value, row["new_value"]):
                result["sync"] += 1
            elif common._same(spec, value, row["old_value"]):
                result["restore"].append(entry)
            else:
                entry["reason"] = "w bazie jest inna wartość"
                result["conflict"].append(entry)
    return result


def drift_count(max_age=CACHE_SECONDS):
    now = time.time()
    if _CACHE["result"] is None or now - _CACHE["at"] > max_age:
        _CACHE["result"] = len(drift()["restore"])
        _CACHE["at"] = now
    return _CACHE["result"]


def restore(note=RESTORE_NOTE):
    """Write back every "restore" entry of drift() as one batch. Returns
    (batch or None, restored count, [error texts], conflict count)."""
    found = drift()
    _CACHE["result"] = None
    entries = found["restore"]
    if not entries:
        return None, 0, [], len(found["conflict"])
    batch = common.uuid.uuid4().hex[:16]
    labels = {(e["tbl"], str(e["row_key"])): e["label"] for e in entries}
    fields, rows = {}, {}
    for e in entries:
        if e["col"] == common.ROW_COL:
            ops = rows.setdefault(e["tbl"], {"inserts": [], "deletes": []})
            if e["old_value"] is not None:  # the row the history replaced is back: remove it
                ops["deletes"].append(common.key_values(e["tbl"], e["row_key"]))
            if e["new_value"] is not None:
                ops["inserts"].append(json.loads(e["new_value"]))
            continue
        spec = common.TABLES[e["tbl"]]["cols"][e["col"]]
        value = e["new_value"]
        if spec["kind"] == "int":
            value = int(value) if value not in (None, "") else 0
        fields.setdefault(e["tbl"], {}).setdefault(e["row_key"], {})[e["col"]] = value if value is not None else ""
    restored, errors = 0, []
    for table, keyed in fields.items():
        try:
            _b, changed = common.save_rows(table, list(keyed.items()), note=note, batch=batch,
                                           label_of=lambda k, t=table: labels.get((t, str(k)), ""))
            restored += len(changed)
        except Exception as exc:  # one table refusing must not stop the others
            errors.append(f"{common.table_title(table)}: {exc}")
    for table, ops in rows.items():
        try:
            _b, done = common.write_rows(table, inserts=ops["inserts"], deletes=ops["deletes"], note=note,
                                         batch=batch, label_of=lambda k, t=table: labels.get((t, str(k)), ""))
            restored += len(done)
        except Exception as exc:
            errors.append(f"{common.table_title(table)}: {exc}")
    _CACHE["result"] = None
    return (batch if restored else None), restored, errors, len(found["conflict"])


# ---- pages --------------------------------------------------------------------------------

def hub_notice():
    try:
        count = drift_count()
    except Exception:
        return None
    if not count:
        return None
    return {"text": f"Wykryto {count} zmian z historii, których nie ma w bazie (np. po resecie świata).",
            "url": url_for("dbeditor.reapply_page"), "link": "Przywróć zmiany z historii"}


def install(bp, ctx):
    import dbeditor

    common.init(ctx)
    register_label_resolvers()
    common.install_history(bp, ctx)
    login_required = ctx["login_required"]
    if hub_notice not in dbeditor.HUB_NOTICES:
        dbeditor.HUB_NOTICES.insert(0, hub_notice)

    @bp.route("/historia/przywroc")
    @login_required
    def reapply_page():
        try:
            found, error = drift(), None
        except Exception as exc:
            found, error = {"restore": [], "conflict": [], "sync": 0, "skipped": []}, str(exc)
        return render_template("dbeditor/reapply.html", found=found, error=error, dbe_csrf=common.csrf_token(),
                               note=RESTORE_NOTE, **common.template_helpers())

    @bp.post("/historia/przywroc")
    @login_required
    def reapply_post():
        if not common.check_csrf():
            return redirect(url_for("dbeditor.reapply_page"))
        try:
            fixed = repair_labels()
        except Exception:
            fixed = 0
        try:
            batch, restored, errors, conflicts = restore()
        except Exception as exc:
            flash(f"Nie udało się przywrócić zmian: {exc}", "error")
            return redirect(url_for("dbeditor.reapply_page"))
        if restored:
            flash(f"Przywrócono {restored} zmian(y) z historii (zapis #{batch[:8]}). Gra wczyta je po „Zastosuj” "
                  "(restart rdzeni); potem gracze pobierają aktualne pliki klienta.", "success")
        elif not errors:
            flash("Nic do przywrócenia – baza zgadza się z historią.", "success")
        for error in errors:
            flash("Nie przywrócono: " + error, "error")
        if conflicts:
            flash(f"{conflicts} pól ma w bazie inną wartość niż w historii – zostały bez zmian (lista niżej).", "warning")
        if fixed:
            flash(f"Poprawiono {fixed} nazw w historii (znaki „?” zamiast polskich liter).", "success")
        return redirect(url_for("dbeditor.reapply_page"))
