"""MT2009_PLUS_DB_EDITOR_V1: what the item and skill editors share - the
change history (with undo) and the "pending" state.

The game reads world.item_proto and world.skill_proto once, while the cores
boot (PROTO_FROM_DB; player.item_proto is only a view of world.item_proto),
so an edit made here changes the database at once but the game only after a
restart. Every saved field is one row of player.web_dbeditor_history:

    id, changed_at, who, tbl ('world.item_proto' / 'world.skill_proto'),
    row_key (the vnum), label (the item's / skill's name at that time),
    col, old_value, new_value (as text), batch (one save = one batch),
    note, reverted_in (the batch that undid this row), applied_at.

applied_at stays NULL until the game has been restarted with the change.
The part that restarts the game ("Zastosuj", clientdata.py) reads what is
waiting with pending_changes() / pending_count() and, once the restart has
been queued, calls mark_applied(). Nothing else here restarts anything.

Every other module of the package can use these three without knowing the
table:

    from dbeditor import common_items
    common_items.pending_count()     # -> int, 0 when nothing waits
    common_items.pending_changes()   # -> [{tbl,row_key,label,col,old_value,new_value,changed_at}]
    common_items.mark_applied()      # -> number of history rows marked
"""
import uuid

from flask import flash, redirect, render_template, request, session, url_for

HISTORY_TABLE = "player.web_dbeditor_history"
_CTX = {}
_STATE = {"table_ready": False, "history_installed": False}

# The tables this editor may write, filled by items.py and skills.py:
# "world.item_proto" -> {"key": "vnum", "cols": {col: spec}, "title": ...}.
# spec = {"kind": "int", "min": .., "max": ..} | {"kind": "cp1250", "max": n}
#      | {"kind": "ascii", "max": n}; "label" is what the history shows.
TABLES = {}


def init(ctx):
    _CTX.update(ctx)


def register_table(name, key, cols, title, edit_endpoint=None, formatter=None):
    TABLES[name] = {"key": key, "cols": cols, "title": title, "edit_endpoint": edit_endpoint, "formatter": formatter}


def column_label(table, col):
    meta = TABLES.get(table)
    return (meta["cols"].get(col, {}).get("label") if meta else None) or col


def format_value(table, col, value):
    """A history value as the operator reads it (a bonus by its name...)."""
    meta = TABLES.get(table)
    if value is None:
        return "—"
    if meta and meta.get("formatter"):
        try:
            shown = meta["formatter"](col, value)
            if shown is not None:
                return shown
        except (TypeError, ValueError):
            pass
    return value if value != "" else "(puste)"


def ctx():
    return _CTX


def ensure_table():
    if _STATE["table_ready"]:
        return
    _CTX["rows"](f"""CREATE TABLE IF NOT EXISTS {HISTORY_TABLE} (
        id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
        changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        who VARCHAR(64) NOT NULL DEFAULT '',
        tbl VARCHAR(64) NOT NULL,
        row_key VARCHAR(32) NOT NULL,
        label VARCHAR(100) NOT NULL DEFAULT '',
        col VARCHAR(64) NOT NULL,
        old_value TEXT NULL,
        new_value TEXT NULL,
        batch VARCHAR(32) NOT NULL,
        note VARCHAR(255) NOT NULL DEFAULT '',
        reverted_in VARCHAR(32) NULL,
        applied_at DATETIME NULL,
        KEY idx_batch (batch),
        KEY idx_row (tbl, row_key),
        KEY idx_applied (applied_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
    _STATE["table_ready"] = True


# ---- form helpers -----------------------------------------------------------

def csrf_token():
    """The panel's one form token (app.py update_csrf_token keeps the same key)."""
    token = session.get("seban_update_csrf")
    if not token:
        token = uuid.uuid4().hex
        session["seban_update_csrf"] = token
    return token


def check_csrf():
    if request.form.get("dbe_csrf", "") != session.get("seban_update_csrf", "") or not request.form.get("dbe_csrf"):
        flash("Sesja formularza wygasła – odśwież stronę i spróbuj jeszcze raz.", "error")
        return False
    return True


def who():
    return f"panel ({request.remote_addr or '?'})"[:64]


def text_of(value):
    """A value as the history keeps it: text, NULL for None."""
    if value is None:
        return None
    if isinstance(value, bytes):
        return _CTX.get("game_text", lambda v: v.decode("cp1250", "replace"))(value)
    return str(value)


# ---- values -------------------------------------------------------------------

def validate(spec, raw, label):
    """(value, error) for one submitted field, by the column's spec."""
    kind = spec["kind"]
    if kind == "int":
        text = str(raw if raw is not None else "").strip().replace(" ", "")
        if text in ("", "-", "+"):
            return None, f"{label}: podaj liczbę."
        try:
            value = int(text)
        except ValueError:
            return None, f"{label}: „{text}” nie jest liczbą całkowitą."
        if not spec["min"] <= value <= spec["max"]:
            return None, f"{label}: dozwolone {spec['min']}…{spec['max']}, podano {value}."
        return value, None
    text = str(raw if raw is not None else "")
    if kind == "cp1250":
        text = text.strip()
        if any(ord(ch) < 32 for ch in text):
            return None, f"{label}: niedozwolone znaki sterujące."
        try:
            encoded = text.encode("cp1250")
        except UnicodeEncodeError:
            return None, f"{label}: znak spoza polskiego alfabetu gry (cp1250)."
        if len(encoded) > spec["max"]:
            return None, f"{label}: najwyżej {spec['max']} znaków (podano {len(encoded)})."
        if spec.get("required") and not text:
            return None, f"{label}: nie może być puste."
        return text, None
    # ascii (skill formulas)
    text = text.strip()
    if any(ord(ch) < 32 or ord(ch) > 126 for ch in text):
        return None, f"{label}: tylko znaki ASCII (cyfry, litery łacińskie, + - * / ( ) , .)."
    if len(text) > spec["max"]:
        return None, f"{label}: najwyżej {spec['max']} znaków (podano {len(text)})."
    return text, None


def _same(spec, a, b):
    if spec["kind"] == "int":
        try:
            return int(a) == int(b)
        except (TypeError, ValueError):
            return False
    return text_of(a or "") == text_of(b or "")


def _select_expr(col, spec):
    # Names are read as their bytes and decoded as cp1250 - right for the
    # cp1250 column of this world and for a latin1 column holding cp1250 bytes
    # (an older dump) alike.
    return f"CAST(`{col}` AS BINARY) AS `{col}`" if spec["kind"] == "cp1250" else f"`{col}`"


def _set_expr(col, spec, value):
    if spec["kind"] == "cp1250":
        # Written as the bytes the game reads (the way apply.sh writes
        # _cp1250 X'..'): UNHEX gives a binary string, stored unconverted.
        return f"`{col}`=UNHEX(%s)", value.encode("cp1250").hex()
    return f"`{col}`=%s", value


def read_row(table, key, cols, cur=None):
    meta = TABLES[table]
    specs = meta["cols"]
    sql = (f"SELECT {', '.join(_select_expr(c, specs[c]) for c in cols)} FROM {table} "
           f"WHERE `{meta['key']}`=%s")
    if cur is None:
        found = _CTX["rows"](sql, (key,))
        return found[0] if found else None
    cur.execute(sql + " FOR UPDATE", (key,))
    return cur.fetchone()


def save_rows(table, updates, note="", label_of=None, batch=None):
    """Write [(key, {col: value})] to one table in one transaction and record
    every changed field. Values must already be validated. Returns
    (batch, [(key, col, old, new)]) - only fields that really changed."""
    ensure_table()
    meta = TABLES[table]
    specs = meta["cols"]
    batch = batch or uuid.uuid4().hex[:16]
    author = who()
    changed = []
    con = _CTX["db"]()
    try:
        con.begin()
        with con.cursor() as cur:
            for key, values in updates:
                cols = [c for c in values if c in specs]
                if not cols:
                    continue
                current = read_row(table, key, cols, cur)
                if current is None:
                    raise LookupError(f"{meta['title']} {key} nie istnieje.")
                diff = [(c, current[c], values[c]) for c in cols if not _same(specs[c], current[c], values[c])]
                if not diff:
                    continue
                parts, params = [], []
                for col, _old, new in diff:
                    expr, param = _set_expr(col, specs[col], new)
                    parts.append(expr)
                    params.append(param)
                cur.execute(f"UPDATE {table} SET {', '.join(parts)} WHERE `{meta['key']}`=%s", params + [key])
                label = (label_of(key) if label_of else "") or ""
                for col, old, new in diff:
                    cur.execute(f"INSERT INTO {HISTORY_TABLE} (who,tbl,row_key,label,col,old_value,new_value,batch,note) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                (author, table, str(key), label[:100], col, text_of(old), text_of(new), batch, note[:255]))
                    changed.append((key, col, old, new))
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    return batch, changed


# ---- history, undo ------------------------------------------------------------

def history_batches(limit=100, table=None, key=None):
    ensure_table()
    where, params = [], []
    if table:
        where.append("tbl=%s")
        params.append(table)
    if key is not None:
        where.append("row_key=%s")
        params.append(str(key))
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    batches = _CTX["rows"](f"""SELECT batch, MIN(id) AS first_id, MIN(changed_at) AS changed_at, MIN(who) AS who,
            MIN(note) AS note, MIN(tbl) AS tbl, COUNT(*) AS fields, COUNT(DISTINCT row_key) AS row_count,
            MAX(reverted_in) AS reverted_in, SUM(applied_at IS NULL) AS unapplied
        FROM {HISTORY_TABLE} {clause} GROUP BY batch ORDER BY first_id DESC LIMIT {int(limit)}""", params)
    if not batches:
        return []
    marks = ",".join(["%s"] * len(batches))
    details = _CTX["rows"](f"""SELECT id,batch,tbl,row_key,label,col,old_value,new_value,reverted_in,applied_at
        FROM {HISTORY_TABLE} WHERE batch IN ({marks}) ORDER BY id""", [b["batch"] for b in batches])
    by_batch = {}
    for row in details:
        by_batch.setdefault(row["batch"], []).append(row)
    for batch in batches:
        batch["rows"] = by_batch.get(batch["batch"], [])
        batch["reverted"] = all(r["reverted_in"] for r in batch["rows"])
    return batches


def revert(batch=None, history_id=None, force=False):
    """Undo one save (batch) or one field (history_id). A field that was
    changed again since is a conflict: nothing is written unless force.
    Returns (new_batch or None, message, ok)."""
    ensure_table()
    if history_id is not None:
        targets = _CTX["rows"](f"SELECT * FROM {HISTORY_TABLE} WHERE id=%s AND reverted_in IS NULL", (int(history_id),))
    else:
        targets = _CTX["rows"](f"SELECT * FROM {HISTORY_TABLE} WHERE batch=%s AND reverted_in IS NULL ORDER BY id DESC", (batch,))
    if not targets:
        return None, "Ta zmiana została już cofnięta albo nie istnieje.", False
    conflicts, updates = [], {}
    for row in targets:
        meta = TABLES.get(row["tbl"])
        if not meta or row["col"] not in meta["cols"]:
            return None, f"Tabela {row['tbl']}.{row['col']} nie jest edytowalna w tym panelu.", False
        spec = meta["cols"][row["col"]]
        current = read_row(row["tbl"], row["row_key"], [row["col"]])
        if current is None:
            return None, f"{meta['title']} {row['row_key']} już nie istnieje.", False
        if not _same(spec, current[row["col"]], row["new_value"]):
            conflicts.append(f"{row['label'] or row['row_key']} · {row['col']}: teraz „{text_of(current[row['col']])}”, "
                             f"a zapis ustawił „{row['new_value']}”")
        old = row["old_value"]
        value = int(old) if spec["kind"] == "int" and old not in (None, "") else (old or "")
        # The oldest value wins when one batch touched a field twice.
        updates.setdefault((row["tbl"], row["row_key"]), {})[row["col"]] = value
    if conflicts and not force:
        return None, ("Pole zmieniono później jeszcze raz, więc cofnięcie nadpisałoby nowszą zmianę: "
                      + "; ".join(conflicts[:5]) + ". Cofnij najpierw nowszą zmianę albo zaznacz „cofnij mimo to”."), False
    labels = {(r["tbl"], r["row_key"]): r["label"] for r in targets}
    note = f"Cofnięcie zmiany #{targets[0]['batch'][:8]}" if history_id is None else f"Cofnięcie pola (wpis #{history_id})"
    new_batch = uuid.uuid4().hex[:16]
    for table in {t for t, _k in updates}:
        save_rows(table, [(k, v) for (t, k), v in updates.items() if t == table], note=note,
                  label_of=lambda k, t=table: labels.get((t, str(k)), ""), batch=new_batch)
    ids = [r["id"] for r in targets]
    marks = ",".join(["%s"] * len(ids))
    _CTX["rows"](f"UPDATE {HISTORY_TABLE} SET reverted_in=%s WHERE id IN ({marks})", [new_batch] + ids)
    return new_batch, f"Cofnięto {len(targets)} zmian(y). Zmiany czekają na zastosowanie (restart gry).", True


# ---- pending ------------------------------------------------------------------

def net_changes(include_applied=False):
    """For each (table, key, column) of the history, the oldest old_value
    against the newest new_value; only the fields where they differ. Without
    include_applied only the rows not yet applied (pending_changes); with it
    the whole history - what the client data (clientdata.py) must carry
    against the released client."""
    try:
        ensure_table()
        where = "" if include_applied else "WHERE applied_at IS NULL "
        found = _CTX["rows"](f"""SELECT id,tbl,row_key,label,col,old_value,new_value,changed_at
            FROM {HISTORY_TABLE} {where}ORDER BY id""")
    except Exception:  # no database: nothing to report, never break a page
        return []
    net = {}
    for row in found:
        key = (row["tbl"], row["row_key"], row["col"])
        if key not in net:
            net[key] = dict(row)
        else:
            net[key].update(new_value=row["new_value"], changed_at=row["changed_at"], label=row["label"] or net[key]["label"])
    return [row for row in net.values() if (row["old_value"] or "") != (row["new_value"] or "")]


def pending_changes():
    """Every field whose value now differs from what the game booted with:
    for each (table, key, column) among the history rows not yet applied,
    the oldest old_value against the newest new_value - a change undone
    before a restart is therefore not pending."""
    return net_changes(include_applied=False)


def pending_count():
    return len(pending_changes())


def mark_applied():
    """Called by "Zastosuj" once the restart that loads the changes is queued."""
    ensure_table()
    con = _CTX["db"]()
    try:
        with con.cursor() as cur:
            cur.execute(f"UPDATE {HISTORY_TABLE} SET applied_at=NOW() WHERE applied_at IS NULL")
            return cur.rowcount
    finally:
        con.close()


def template_helpers():
    """What templates/dbeditor/_items_history_list.html needs."""
    return {"column_label": column_label, "format_value": format_value, "tables": TABLES}


def pending_context():
    """What the pages' banner (templates/dbeditor/_items_pending.html) needs."""
    changes = pending_changes()
    return {"pending_total": len(changes),
            "pending_items": len({c["row_key"] for c in changes if c["tbl"] == "world.item_proto"}),
            "pending_skills": len({c["row_key"] for c in changes if c["tbl"] == "world.skill_proto"})}


# ---- the history page -----------------------------------------------------------

def install_history(bp, ctx_):
    if _STATE["history_installed"]:
        return
    _STATE["history_installed"] = True
    login_required = ctx_["login_required"]

    @bp.route("/historia")
    @login_required
    def proto_history():
        table = request.args.get("tbl") or None
        if table not in TABLES:
            table = None
        key = request.args.get("key") or None
        try:
            batches = history_batches(200, table, key)
            error = None
        except Exception as exc:  # pymysql errors: show, do not 500
            batches, error = [], str(exc)
        try:
            pending = pending_context()
        except Exception:
            pending = {"pending_total": 0}
        return render_template("dbeditor/items_history.html", batches=batches, error=error, table=table, key=key,
                               dbe_csrf=csrf_token(), **template_helpers(), **pending)

    @bp.post("/historia/cofnij")
    @login_required
    def proto_history_revert():
        back = request.form.get("back") or url_for("dbeditor.proto_history")
        if not back.startswith("/"):
            back = url_for("dbeditor.proto_history")
        if not check_csrf():
            return redirect(back)
        force = request.form.get("force") == "1"
        try:
            if request.form.get("id"):
                _batch, message, ok = revert(history_id=int(request.form["id"]), force=force)
            else:
                _batch, message, ok = revert(batch=request.form.get("batch", ""), force=force)
        except (ValueError, LookupError) as exc:
            message, ok = str(exc), False
        flash(message, "success" if ok else "error")
        return redirect(back)
