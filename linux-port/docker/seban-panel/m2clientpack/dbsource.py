"""The client files built from the database editor's edits.

What was edited comes from the editor's own history
(dbeditor/common_items.py: net_changes(include_applied=True) - every
(table, vnum, column) whose value differs from before the first edit);
targets() turns those rows into {item vnum: {columns}} and {skill vnums}.
The values are read from the database at build time.

query(sql, params) -> list of dict rows is the panel's rows().
"""
from . import clientfiles

ITEM_TABLE = 'world.item_proto'
SKILL_TABLE = 'world.skill_proto'
# the history's "tbl" for the two tables (common_items keeps the full name)
ITEM_TABLES = ('world.item_proto', 'player.item_proto')
SKILL_TABLES = ('world.skill_proto', 'player.skill_proto')


def targets(changes):
    """({vnum: set(columns)}, {skill vnums}) of history rows (tbl, row_key,
    col). Columns the client record does not have (addon_type, socket3..5)
    are dropped; an item left with none is not a client change."""
    items, skills = {}, set()
    for row in changes:
        try:
            key = int(row['row_key'])
        except (KeyError, TypeError, ValueError):
            continue
        if row.get('tbl') in ITEM_TABLES:
            if row.get('col') in clientfiles.ITEM_FIELDS:
                items.setdefault(key, set()).add(row['col'])
        elif row.get('tbl') in SKILL_TABLES:
            skills.add(key)
    return items, skills


def _item_rows(query, vnums):
    out = {}
    vnums = sorted(vnums)
    for start in range(0, len(vnums), 500):
        part = vnums[start:start + 500]
        marks = ','.join(['%s'] * len(part))
        # names as their bytes: the game's cp1250, whatever the column's charset
        # (own aliases - a repeated column name comes back as ".name")
        for r in query('SELECT *, CAST(`name` AS BINARY) AS `name_bytes`, CAST(`locale_name` AS BINARY) AS '
                       '`locale_name_bytes` FROM %s WHERE vnum IN (%s)' % (ITEM_TABLE, marks), tuple(part)):
            r = dict(r)
            for col in ('name', 'locale_name'):
                if r.get(col + '_bytes') is not None:
                    r[col] = r.pop(col + '_bytes')
            out[int(r['vnum'])] = r
    return out


def _skill_rows(query, vnums):
    if not vnums:
        return {}
    marks = ','.join(['%s'] * len(vnums))
    return dict((int(r['dwVnum']), r) for r in
                query('SELECT * FROM %s WHERE dwVnum IN (%s)' % (SKILL_TABLE, marks), tuple(sorted(vnums))))


def client_files(query, base, items, skills, notes=None):
    """({entry name: bytes}, summary) of the client files the edits change
    (equal ones included; overlay.build drops them)."""
    notes = [] if notes is None else notes
    files = {}
    summary = {'items': [], 'skills': [], 'itemdesc': [], 'notes': notes}
    item_rows = _item_rows(query, set(items))
    blob, changed = clientfiles.patch_item_proto(base.file('gamedata/item_proto'), items, item_rows, notes)
    files['gamedata/item_proto'] = blob
    summary['items'] = changed

    skill_rows = _skill_rows(query, set(skills))
    for v in sorted(set(skills) - set(skill_rows)):
        notes.append('Umiejętność %d: nie ma jej w bazie - klient bez zmian.' % v)
    blob, changed = clientfiles.patch_skilltable(base.file('gamedata/skilltable.txt'), skill_rows, notes)
    files['gamedata/skilltable.txt'] = blob
    summary['skills'] = changed

    # itemdesc.txt (vnum, name, description, summary): the name column
    # follows a renamed item that has a line there.
    base_desc = base.file('locale/pl/itemdesc.txt')
    known = set()
    for line in base_desc.decode(clientfiles.TEXT_ENCODING, 'replace').splitlines():
        head = line.split('\t', 1)[0].strip()
        if head.isdigit():
            known.add(int(head))
    renamed = dict((v, {1: item_rows[v].get('locale_name', '')}) for v, cols in items.items()
                   if v in item_rows and v in known and 'locale_name' in cols)
    blob, changed = clientfiles.patch_tab_text(base_desc, renamed, 3)
    files['locale/pl/itemdesc.txt'] = blob
    summary['itemdesc'] = changed
    return files, summary


def build_from_db(query, out_dir, changes, base=None):
    """The whole build: history rows -> client files -> overlay in out_dir.
    Returns the manifest."""
    from . import overlay
    base = base or overlay.latest_base()
    items, skills = targets(changes)
    notes = []
    files, summary = client_files(query, base, items, skills, notes)
    return overlay.build(base, files, out_dir, summary)
