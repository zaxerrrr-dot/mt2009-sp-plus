# -*- coding: utf-8 -*-
# MT2009_PLUS_AREZZO_COSTUME_SETS_V1 - the Arezzo costume sets in the client's data: the same 235
# items linux-port/docker/mariadb/playerbot/arezzo_costumes.sql adds to world.item_proto (both
# made from azcostume_items.json - keep them equal; gen_azcostume_server.py writes the server).
#
#   python3 patch_azcostume_client.py <data dir> [<out dir>]
#
# <data dir> holds plain copies of the client files under their pack paths:
#   gamedata/gf_official_costumes.txt   gamedata pack - bodies, hairs, weapon skins (ITEM_COSTUME rows;
#                                       the client's legacy item_proto has no 4xxxx cosmetics, the exe's
#                                       CItemManager::LoadItemTable reads this 24-column table)
#   gamedata/costume_attr_items.txt     gamedata pack - the 21 sash skins (ITEM_USE rows, same layout;
#                                       the applicable flag makes the bag send "use on item")
#   gamedata/item_list.txt              gamedata pack - icon (ARMOR / ETC), weapon model (WEAPON),
#                                       the skin's wing / cape model (WING - SetAcce shows it)
#   gamedata/item_scale.txt             gamedata pack - the skins' size on the back, 100% for every
#                                       class (a sash without a scale row is drawn at scale 0)
#   gamedata/<race>.msm                 gamedata pack - ShapeData / HairData groups (warrior, assassin,
#                                       sura, shaman; _m and _w), the counts raised
#   gamedata/shiningtable.txt           gamedata pack, NEW - the glows (exe ENABLE_ITEM_SHINING_TABLE,
#                                       client-patches/exe; an older exe ignores the file)
#   locale/pl/itemdesc.txt              dbdata pack - name and description
# Without an out dir the files are rewritten in place; with one, every file goes there (same
# relative paths). Idempotent: a second run changes nothing (a row / group that is there is
# rewritten only when it differs; a msm group of the same index is left as it is).
# Plain Python 3; cp1250 text, each file keeps its own line ends.
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RACES = ('warrior_m', 'assassin_m', 'sura_m', 'shaman_m', 'warrior_w', 'assassin_w', 'sura_w', 'shaman_w')
JOBS = (('JOB_WARRIOR', 'warrior'), ('JOB_ASSASSIN', 'assassin'), ('JOB_SURA', 'sura'), ('JOB_SHAMAN', 'shaman'))
FLAG_APPLICABLE = 1 << 14
SPECULAR = 100
CLASS_TEXT = {0: u'wojownik, ninja, sura', 1: u'ninja', 2: u'ninja', 3: u'wojownik', 4: u'szaman', 5: u'szaman'}


def load():
    with open(os.path.join(HERE, 'azcostume_items.json'), encoding='utf-8') as f:
        return json.load(f)


def set_word(item, sets):
    return dict((s['key'], s['name'].replace('_', ' ')) for s in sets)[item['set']]


def table_row(it):
    """24 columns: vnum, name, subtype, size, anti, flags, 2 limits, 3 applies, 6 values, specular, vnum."""
    if it['kind'] == 'SashSkin':
        limit, flags, spec = (0, 0), FLAG_APPLICABLE, 0
    else:
        limit, flags, spec = (7, 2592000), 0, SPECULAR
    cols = [it['vnum'], it['name'], it['sub'], it['size'], it['anti'], flags, limit[0], limit[1], 0, 0,
            0, 0, 0, 0, 0, 0] + list(it['values']) + [spec, it['vnum']]
    assert len(cols) == 24
    return u'\t'.join(u'%s' % c for c in cols)


def description(it, sets):
    s = set_word(it, sets)
    if it['kind'] == 'ShapeData':
        return u'Kostium z zestawu Arezzo (%s). Działa 30 dni od założenia.' % s
    if it['kind'] == 'HairData':
        return u'Nakrycie głowy z zestawu Arezzo (%s). Działa 30 dni od założenia.' % s
    if it['kind'] == 'Weapon':
        return u'Nakładka na broń z zestawu Arezzo (%s): %s. Działa 30 dni od założenia.' % (
            s, CLASS_TEXT[it['values'][3]])
    return (u'Nakładka na szarfę z zestawu Arezzo (%s). Przeciągnij ją na szarfę w ekwipunku: szarfa '
            u'wygląda jak ta nakładka, jej stopień, pochłanianie i bonusy zostają. Poprzednia nakładka '
            u'wraca do ekwipunku.' % s)


def text_of(b):
    t = b.decode('cp1250')
    return t, ('\r\n' if '\r\n' in t else '\n')


def set_rows(b, rows):
    """Every line whose first column is a row's key becomes that row, or the row is appended."""
    text, nl = text_of(b)
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    pos = {}
    for i, l in enumerate(lines):
        pos.setdefault(l.split('\t')[0].strip(), []).append(i)
    changed = 0
    for row in rows:
        key = row.split('\t')[0]
        if key in pos:
            for i in pos[key]:
                if lines[i] != row:
                    lines[i] = row
                    changed += 1
        else:
            pos[key] = [len(lines)]
            lines.append(row)
            changed += 1
    if tail:
        lines.append('')
    return nl.join(lines).encode('cp1250'), changed


def set_scale_rows(b, vnums):
    """item_scale.txt: vnum, job, sex, x, y, z (percent). One row per class and sex for each skin;
    the rows of a vnum are replaced as a whole (the loader applies a row to vnum..vnum+4 too, so the
    skins' rows stay in ascending order at the end of the file)."""
    text, nl = text_of(b)
    lines = [l for l in text.split(nl) if l != '']
    want = []
    for v in vnums:
        for job, _ in JOBS:
            for sex in ('M', 'F'):
                want.append(u'%d\t%s\t%s\t100\t100\t100' % (v, job, sex))
    keep = [l for l in lines if not (l.split('\t')[0].strip().isdigit() and int(l.split('\t')[0]) in vnums)]
    new = keep + want
    out = (nl.join(new) + nl).encode('cp1250')
    return out, 0 if out == b else len(want)


def msm_groups(b, kind, groups):
    """Appends groups ([(index, {SpecialPath, Model, SourceSkin, TargetSkin})]) to the msm's
    ShapeData / HairData block; their names go on from the count (the loader reads ShapeData%02d
    0..count-1). A group whose index is there already is kept as it is."""
    text = b.decode('cp1250')
    lines = text.splitlines(True)
    nl = '\r\n' if lines and lines[0].endswith('\r\n') else '\n'
    start = next(i for i, l in enumerate(lines) if l.strip() == 'Group %s' % kind)
    depth, end = 0, None
    for i in range(start + 1, len(lines)):
        s = lines[i].strip()
        if s == '{':
            depth += 1
        elif s == '}':
            depth -= 1
            if depth == 0:
                end = i
                break
    cnt_key = '%sCount' % kind
    cnt_i = next(i for i in range(start, end) if lines[i].strip().startswith(cnt_key))
    cnt = int(lines[cnt_i].split()[1])
    idx_key = 'ShapeIndex' if kind == 'ShapeData' else 'HairIndex'
    have = set()
    for i in range(start, end):
        p = lines[i].split()
        if len(p) >= 2 and p[0] == idx_key and p[1].isdigit():
            have.add(int(p[1]))
    add = []
    n = cnt
    for index, g in groups:
        if index in have:
            continue
        body = [u'\tGroup %s%02d' % (kind, n), u'\t{', u'\t\t%s\t\t\t%d' % (idx_key, index),
                u'\t\tSpecialPath\t\t\t"%s"' % g['SpecialPath'], u'\t\tModel\t\t\t\t"%s"' % g['Model']]
        if g.get('SourceSkin'):
            body += [u'\t\tSourceSkin\t\t\t"%s"' % g['SourceSkin'], u'\t\tTargetSkin\t\t\t"%s"' % g['TargetSkin']]
        body.append(u'\t}')
        add.append(nl + nl.join(body) + nl)
        n += 1
    if not add:
        return b, 0
    lines[cnt_i] = lines[cnt_i].replace(str(cnt), str(n), 1)
    lines[end:end] = add
    return ''.join(lines).encode('cp1250'), len(add)


def shining_rows(b, items):
    rows = [u'%d\t%s' % (it['vnum'], u'\t'.join(u'"%s"' % f for f in it['shining'])) for it in items if it['shining']]
    if not b:
        b = (u'# MT2009_PLUS_AREZZO_COSTUME_SETS_V1: item glows by vnum (exe ENABLE_ITEM_SHINING_TABLE).\n'
             u'# vnum<TAB>"effect.mse"[<TAB>"effect.mse"...] - weapons on the weapon bone(s), the rest on Bip01.\n').encode('cp1250')
    return set_rows(b, rows)


def patch(data_dir, out_dir=None):
    d = load()
    items, sets = d['items'], d['sets']
    costume = [it for it in items if it['kind'] != 'SashSkin']
    skins = [it for it in items if it['kind'] == 'SashSkin']
    jobs = []

    def item_list_row(it):
        if it['kind'] == 'Weapon':
            return u'%d\tWEAPON\t%s\t%s' % (it['vnum'], it['icon'], it['model'])
        if it['kind'] == 'SashSkin':
            return u'%d\tWING\t%s\t%s' % (it['vnum'], it['icon'], it['model'])
        return u'%d\t%s\t%s' % (it['vnum'], 'ARMOR' if it['kind'] == 'ShapeData' else 'ETC', it['icon'])

    jobs.append(('gamedata/gf_official_costumes.txt', lambda b: set_rows(b, [table_row(it) for it in costume])))
    jobs.append(('gamedata/costume_attr_items.txt', lambda b: set_rows(b, [table_row(it) for it in skins])))
    jobs.append(('gamedata/item_list.txt', lambda b: set_rows(b, [item_list_row(it) for it in items])))
    jobs.append(('gamedata/item_scale.txt', lambda b: set_scale_rows(b, [it['vnum'] for it in skins])))
    jobs.append(('locale/pl/itemdesc.txt', lambda b: set_rows(b, [u'%d\t%s\t%s' % (it['vnum'], it['name'], description(it, sets))
                                                                  for it in items])))
    for race in RACES:
        def msm_job(b, race=race):
            total = 0
            for kind in ('ShapeData', 'HairData'):
                groups = [(it['vnum'], it['msm'][race]) for it in items if it['kind'] == kind and race in it['msm']]
                b, n = msm_groups(b, kind, groups)
                total += n
            return b, total
        jobs.append(('gamedata/%s.msm' % race, msm_job))
    jobs.append(('gamedata/shiningtable.txt', lambda b: shining_rows(b, items)))
    for rel, fn in jobs:
        src = os.path.join(data_dir, rel)
        b = open(src, 'rb').read() if os.path.exists(src) else b''
        nb, changed = fn(b)
        dst = os.path.join(out_dir or data_dir, rel)
        if out_dir or nb != b:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, 'wb') as f:
                f.write(nb)
        print('%s: %d change(s)%s' % (rel, changed, '' if dst == src else ' -> ' + dst))


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit('usage: patch_azcostume_client.py <data dir> [<out dir>]')
    patch(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)


if __name__ == '__main__':
    main()
