"""What the database editor changed, read from the database, and the client
files built from it.

query(sql, params) -> list of dict rows is all this needs (the panel's
rows()). Every table here is optional: a missing one means "nothing".

The editor's history (MT2009_PLUS_DB_EDITOR_V1) is player.web_dbeditor_history,
one row per saved change. This module reads it by column NAMES and accepts
the usual spellings, so the editor parts only have to keep to:
  id          auto-increment                         (required)
  created_at  when (DATETIME / TIMESTAMP)            (or changed_at, ts, time)
  table_name  'item_proto' / 'skill_proto' / 'drop' / 'chest' ... (or kind,
              tbl, target, section)
  vnum        the item's / skill's vnum              (or row_key, record_key)
  field       the column changed, or a comma list    (or fields, column_name)
  changes     JSON {column: {"old":..,"new":..}} or {column: new} - an
              alternative to `field`                 (or diff, after, data)
  summary     text for the "Zastosuj" page           (or description, note)
An item edit without field information changes clientfiles.SAFE_FIELDS.

Optional texts the client shows and the database has no column for:
  player.web_dbeditor_itemdesc (vnum, description, summary)
  player.web_dbeditor_skilldesc (vnum, name1, name2, name3, description)
"""
import json

from . import clientfiles

HISTORY = 'player.web_dbeditor_history'
ITEMDESC = 'player.web_dbeditor_itemdesc'
SKILLDESC = 'player.web_dbeditor_skilldesc'
ITEM_TABLES = ('player.item_proto', 'world.item_proto')
SKILL_TABLES = ('world.skill_proto', 'player.skill_proto')

TIME_COLS = ('created_at', 'changed_at', 'updated_at', 'ts', 'time', 'date', 'when')
KIND_COLS = ('table_name', 'tbl', 'table', 'kind', 'target', 'section', 'part', 'module',
             'entity', 'object_type', 'category', 'type')
KEY_COLS = ('vnum', 'row_key', 'record_key', 'record_id', 'key_id', 'item_vnum', 'skill_vnum',
            'object_id', 'target_id', 'entity_id', 'row_id', 'pk', 'key')
FIELD_COLS = ('field', 'field_name', 'column_name', 'column', 'fields', 'columns', 'changed_fields')
JSON_COLS = ('changes', 'diff', 'after', 'new_values', 'new', 'data', 'details', 'payload')
TEXT_COLS = ('summary', 'description', 'note', 'message', 'text', 'label')
USER_COLS = ('username', 'user', 'author', 'login', 'operator')


def _first(row, cols):
    lower = dict((k.lower(), k) for k in row)
    for c in cols:
        if c in lower and row[lower[c]] not in (None, ''):
            return row[lower[c]]
    return None


def _text(v):
    if isinstance(v, (bytes, bytearray)):
        return bytes(v).decode('utf-8', 'replace')
    return '' if v is None else str(v)


def classify(kind):
    k = _text(kind).lower()
    if 'skill' in k:
        return 'skill'
    if 'chest' in k or 'special_item_group' in k or 'szkat' in k:
        return 'chest'
    if 'drop' in k or 'mob_item' in k:
        return 'drop'
    if 'item' in k or 'przedmiot' in k:
        return 'item'
    return k or 'inne'


def _fields(row):
    raw = _first(row, FIELD_COLS)
    if raw is not None:
        text = _text(raw).strip()
        if text.startswith('['):
            try:
                return [_text(x) for x in json.loads(text)]
            except ValueError:
                pass
        return [p.strip() for p in text.replace(';', ',').split(',') if p.strip()]
    raw = _first(row, JSON_COLS)
    if raw is None:
        return None
    try:
        data = json.loads(_text(raw)) if not isinstance(raw, (dict, list)) else raw
    except ValueError:
        return None
    if isinstance(data, dict):
        if isinstance(data.get('fields'), list):
            return [_text(x) for x in data['fields']]
        inner = data.get('changes') or data.get('after') or data.get('new')
        if isinstance(inner, dict):
            data = inner
        return [_text(k) for k in data]
    if isinstance(data, list):
        out = []
        for x in data:
            if isinstance(x, dict):
                name = x.get('field') or x.get('column') or x.get('name')
                if name:
                    out.append(_text(name))
            else:
                out.append(_text(x))
        return out
    return None


def normalize(row):
    key = _first(row, KEY_COLS)
    key_text = _text(key).strip()
    return {
        'id': row.get('id'),
        'time': _first(row, TIME_COLS),
        'kind': classify(_first(row, KIND_COLS)),
        'key': int(key_text) if key_text.lstrip('-').isdigit() else (key_text or None),
        'fields': _fields(row),
        'summary': _text(_first(row, TEXT_COLS)),
        'user': _text(_first(row, USER_COLS)),
    }


def table_exists(query, qualified):
    schema, table = qualified.split('.', 1)
    try:
        return bool(query('SELECT 1 FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s',
                          (schema, table)))
    except Exception:
        return False


def history(query, after_id=None, limit=None):
    """Normalized history rows, oldest first; only id > after_id when
    given. [] when the table does not exist."""
    if not table_exists(query, HISTORY):
        return []
    sql = 'SELECT * FROM %s' % HISTORY
    params = ()
    if after_id is not None:
        sql += ' WHERE id > %s'
        params = (int(after_id),)
    sql += ' ORDER BY id'
    if limit:
        sql += ' LIMIT %d' % int(limit)
    try:
        return [normalize(r) for r in query(sql, params)]
    except Exception:
        return []


def edited_targets(rows):
    """{vnum: set(fields)} of items and {vnum} of skills, from all history
    rows."""
    items, skills = {}, set()
    for r in rows:
        if not isinstance(r['key'], int):
            continue
        if r['kind'] == 'item':
            fields = set(f for f in (r['fields'] or []) if f in clientfiles.ITEM_FIELDS)
            if not fields:
                fields = set(clientfiles.SAFE_FIELDS)
            items.setdefault(r['key'], set()).update(fields)
        elif r['kind'] == 'skill':
            skills.add(r['key'])
    return items, skills


def _rows_by(query, tables, key, vnums):
    if not vnums:
        return {}
    marks = ','.join(['%s'] * len(vnums))
    for table in tables:
        if not table_exists(query, table):
            continue
        out = {}
        for r in query('SELECT * FROM %s WHERE %s IN (%s)' % (table, key, marks), tuple(sorted(vnums))):
            out[int(r[key])] = r
        return out
    return {}


def _optional(query, table):
    if not table_exists(query, table):
        return []
    try:
        return query('SELECT * FROM %s' % table, ())
    except Exception:
        return []


def client_files(query, base, items=None, skills=None, notes=None):
    """{entry name: bytes} of the client files the edits change (equal ones
    included; overlay.build drops them), plus a summary. items/skills
    default to everything the history ever touched."""
    notes = [] if notes is None else notes
    if items is None or skills is None:
        h_items, h_skills = edited_targets(history(query))
        items = h_items if items is None else items
        skills = h_skills if skills is None else skills
    files = {}
    summary = {'items': [], 'skills': [], 'itemdesc': [], 'skilldesc': [], 'notes': notes}
    item_rows = _rows_by(query, ITEM_TABLES, 'vnum', set(items))
    blob, changed = clientfiles.patch_item_proto(base.file('gamedata/item_proto'), items, item_rows, notes)
    files['gamedata/item_proto'] = blob
    summary['items'] = changed

    skill_rows = _rows_by(query, SKILL_TABLES, 'dwVnum', set(skills))
    for v in sorted(set(skills) - set(skill_rows)):
        notes.append('Umiejętność %d: nie ma jej w bazie - klient bez zmian.' % v)
    blob, changed = clientfiles.patch_skilltable(base.file('gamedata/skilltable.txt'), skill_rows, notes)
    files['gamedata/skilltable.txt'] = blob
    summary['skills'] = changed

    # itemdesc.txt: vnum, name, description, summary. The name column only
    # follows a renamed item; descriptions come from the optional table.
    desc = {}
    for vnum, fields in items.items():
        row = item_rows.get(vnum)
        if row is not None and 'locale_name' in fields:
            desc.setdefault(vnum, {})[1] = row.get('locale_name', '')
    for r in _optional(query, ITEMDESC):
        try:
            vnum = int(r.get('vnum'))
        except (TypeError, ValueError):
            continue
        upd = desc.setdefault(vnum, {})
        if vnum in item_rows:
            upd[1] = item_rows[vnum].get('locale_name', '')
        if r.get('description') is not None:
            upd[2] = r.get('description')
        if r.get('summary') is not None:
            upd[3] = r.get('summary')
    base_desc = base.file('locale/pl/itemdesc.txt')
    known = set()
    for line in base_desc.decode(clientfiles.TEXT_ENCODING, 'replace').splitlines():
        head = line.split('\t', 1)[0].strip()
        if head.isdigit():
            known.add(int(head))
    # a rename alone never adds a line the release did not have
    desc = dict((v, u) for v, u in desc.items() if v in known or 2 in u or 3 in u)
    blob, changed = clientfiles.patch_tab_text(base_desc, desc, 3)
    files['locale/pl/itemdesc.txt'] = blob
    summary['itemdesc'] = changed

    # skilldesc.txt: vnum, job, name1..3, description - existing lines only.
    sdesc = {}
    for r in _optional(query, SKILLDESC):
        try:
            vnum = int(r.get('vnum'))
        except (TypeError, ValueError):
            continue
        upd = {}
        for col, key in ((2, 'name1'), (3, 'name2'), (4, 'name3'), (5, 'description')):
            if r.get(key) not in (None, ''):
                upd[col] = r.get(key)
        if upd:
            sdesc[vnum] = upd
    base_sdesc = base.file('locale/pl/skilldesc.txt')
    known = set()
    for line in base_sdesc.decode(clientfiles.TEXT_ENCODING, 'replace').splitlines():
        head = line.split('\t', 1)[0].strip()
        if head.isdigit():
            known.add(int(head))
    for v in sorted(set(sdesc) - known):
        notes.append('Opis umiejętności %d: klient nie ma tej umiejętności - pominięty.' % v)
    sdesc = dict((v, u) for v, u in sdesc.items() if v in known)
    blob, changed = clientfiles.patch_tab_text(base_sdesc, sdesc, 6)
    files['locale/pl/skilldesc.txt'] = blob
    summary['skilldesc'] = changed
    return files, summary


def build_from_db(query, out_dir, base=None, items=None, skills=None):
    """The whole build: history -> client files -> overlay in out_dir.
    Returns the manifest."""
    from . import overlay
    base = base or overlay.latest_base()
    notes = []
    files, summary = client_files(query, base, items, skills, notes)
    return overlay.build(base, files, out_dir, summary)
