# -*- coding: utf-8 -*-
# MT2009_PLUS_BALATHOR_V1 (client data; Autor: dracaryS) - Krypta Balathora (420) in the client's data (the method of
# ../ymeley/patch_ymeley_client.py), from balathor_client.json and the server's SQL
# (linux-port/docker/mariadb/playerbot/balathor.sql):
#
#   gamedata/atlasinfo.txt   the lair's row metin2_map_balathor 1152000 921600 2 2 (its own folder, stage_balathor.py;
#                            = the server's Setting.txt of metin2_map_guild_whitedragon_boss). No row of ours covers
#                            that square (checked: a row overlapping it stops the run).
#   gamedata/npclist.txt     nothing new today - the client has every row of the 20 vnums (guild_whitedragon_*,
#                            metinstone_*whitedragon*, whitedragon_guard / _misa); a missing one is appended
#   gamedata/mob_proto       the SQL's rows of the vnums the client lacks (6896-6900, 20491-20499, 20507, 20868,
#                            20869) on the record of 101 (monsters, stones) or 9012 (NPC); 8635/8636/20815 are the
#                            Yohara line's already (yohara_maps3.sql, the same monsters) and stay
#   gamedata/item_list.txt, gamedata/item_proto (dbdata), locale/pl/itemdesc.txt (dbdata)
#                            Ognista Strzala 30395 (the package's 30345 is Ezoteryczne Drewno here; icon
#                            root/icon/item/30395.tga), the chests Mrozna Skrz. Balathora 83075 / Balathora+ 83076
#                            (GIFTBOX; icons root/icon/item/83075.tga / 83076.tga = GF 26.1.11 icon/item/70413.tga /
#                            70414.tga, GF's own Balathor chests - silver-blue and golden frozen chest, as the pl-wiki;
#                            ground model boss_box.gr2): the SQL's records over ../yohara/patch_yohara_client.py's template,
#                            their item_list lines and Polish descriptions
#   locale/pl/locale_game.txt (locale)
#                            the 41 GUILD_WHITE_DRAGON_LAIR_* strings, in Polish (uiguildwhitedragon.py)
# APPEND ONLY for atlasinfo/npclist/mob_proto/locale_game: a key already there with other content stops the run.
# Idempotent: a second run changes nothing. build_balathor_packs.py calls these on the packs; by hand, on plain copies,
# in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/balathor/patch_balathor_client.py <file> ... [--check]   (by its name)
# BALATHOR_SQL=<file> reads another SQL file than the repo's (tests).
import io
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, os.path.join(HERE, '..', 'shipdefense'))
sys.path.insert(0, os.path.join(HERE, '..', 'yohara'))
sys.path.insert(0, os.path.join(HERE, '..', 'monstercard'))
import patch_shipdefense_client as sd  # noqa: E402
import patch_monstercard_client as base  # noqa: E402
import patch_yohara_client as py  # noqa: E402

REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
SQL = os.environ.get('BALATHOR_SQL') or os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'balathor.sql')
CELL = 25600
Collision = sd.Collision


def data():
    with io.open(os.path.join(HERE, 'balathor_client.json'), encoding='utf-8') as f:
        return json.load(f)


def _sql_rows(table):
    """the rows of every INSERT ... INTO world.<table> (...) VALUES list of the SQL, as dicts"""
    if not os.path.exists(SQL):
        raise SystemExit('balathor: %s is missing (the server SQL the client rows are taken from)' % SQL)
    t = open(SQL, encoding='utf-8').read()
    # _cp1250 X'..' literals (the Polish names) as plain quoted strings
    t = re.sub(r"_cp1250\s+X'([0-9A-Fa-f]*)'",
               lambda m: "'" + bytes.fromhex(m.group(1)).decode('cp1250').replace('\\', '\\\\').replace("'", "\\'") + "'", t)
    rows = []
    for m in re.finditer(r'INSERT\s+(?:IGNORE\s+)?INTO\s+`?world`?\.`?%s`?\s*\(([^)]*)\)\s*VALUES' % table, t, re.I):
        cols = [c.strip().strip('`') for c in m.group(1).split(',')]
        for r in sd._values(t[m.end():]):
            assert len(r) == len(cols), (table, r[:3])
            rows.append(dict(zip(cols, r)))
    return rows


def _flags(s, names):
    """the flag names our client knows (an unknown one is left out of the client record only)"""
    return ','.join(x.strip() for x in str(s or '').split(',') if x.strip() in names)


def sql_mobs():
    want = set(data()['vnums'])
    out = {}
    for r in _sql_rows('mob_proto'):
        if int(r['vnum']) in want:
            r = dict(r)
            r['vnum'] = int(r['vnum'])
            r['ai_flag'] = _flags(r.get('ai_flag'), sd.AI)
            r['setRaceFlag'] = _flags(r.get('setRaceFlag'), sd.RACE)
            r['setImmuneFlag'] = _flags(r.get('setImmuneFlag'), sd.IMMUNE)
            r['folder'] = r.get('folder') or ''
            out[r['vnum']] = r
    return out


def sql_item(vnum):
    for r in _sql_rows('item_proto'):
        if int(r['vnum']) == vnum:
            for k in ('type', 'subtype', 'stack', 'antiflag', 'flag'):
                assert isinstance(r.get(k), int), ('item_proto %d: %s must be a number in the SQL' % (vnum, k), r.get(k))
            w = dict((k, (v if isinstance(v, (int, float)) or k in ('name', 'locale_name') else
                          (int(v) if re.match(r'^-?\d+$', str(v).strip()) else 0))) for k, v in r.items())
            for k in ('weight', 'size', 'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set',
                      'magic_pct', 'specular', 'socket_pct'):
                w.setdefault(k, 0)
            for j in range(3):
                w.setdefault('applytype%d' % j, 0)
                w.setdefault('applyvalue%d' % j, 0)
            for j in range(2):
                w.setdefault('limittype%d' % j, 0)
                w.setdefault('limitvalue%d' % j, 0)
            for j in range(6):
                w.setdefault('value%d' % j, 0)
            return w
    raise SystemExit('balathor: item %d is not in %s' % (vnum, SQL))


def _append_rows(b, rows, key):
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    have = dict((key(l), l) for l in lines if l.strip() and not l.lstrip().startswith(('#', '//')))
    new = []
    for row in rows:
        k = key(row)
        if k in have:
            if have[k].split() != row.split():
                raise Collision('%r already there as %r' % (k, have[k]))
            continue
        new.append(row)
    if not new:
        return b, 0
    return (nl.join(lines + new + ([''] if tail else []))).encode('cp1250'), len(new)


def atlasinfo(b):
    rows = data()['atlasinfo']
    for row in rows:
        n, x, y, w, h = row.split('\t')
        x, y, w, h = int(x), int(y), int(w), int(h)
        for l in b.decode('cp1250').replace('\r\n', '\n').split('\n'):
            t = l.split()
            if len(t) < 5 or t[0].lower() == n.lower():
                continue
            try:
                ox, oy, ow, oh = [int(v) for v in t[1:5]]
            except ValueError:
                continue
            if ox < x + w * CELL and x < ox + ow * CELL and oy < y + h * CELL and y < oy + oh * CELL:
                raise Collision('atlasinfo.txt: %s overlaps %r' % (n, l))
    return _append_rows(b, rows, lambda l: l.split('\t')[0].strip().lower())


def npclist(b):
    rows = ['%s\t%s' % (k, v) for k, v in sorted(data()['npclist_expected'].items(), key=lambda kv: int(kv[0]))]
    return _append_rows(b, rows, lambda l: l.split()[0] if l.split() else '')


def mob_proto(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = m2pack.mcoz_decode(b[12:12 + esize], sd.MOB_KEY)
    assert len(raw) == cnt * sd.MOB_RECORD, (len(raw), cnt)
    R = sd.MOB_RECORD
    recs = dict((struct.unpack_from('<I', raw, i * R)[0], raw[i * R:(i + 1) * R]) for i in range(cnt))
    new = {}
    for v, w in sorted(sql_mobs().items()):
        if v in recs:
            continue            # the client's own row (8635/8636/20815 - the Yohara line's)
        new[v] = sd.mob_record(w, recs[101] if int(w['type']) in (0, 2) else recs[9012])
    if not new:
        return b, 0
    recs.update(new)
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, sd.MOB_KEY)
    return struct.pack('<4sII', b'MMPT', len(recs), len(blob)) + blob, len(new)


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                for i in range(cnt))
    changed = 0
    for vnum in data()['items']:
        w = sql_item(vnum)
        r = py.yitem_record(recs[py.YITEM_TEMPLATE.get(w['type'], py.TEMPLATE)], w)
        if recs.get(vnum) != r:
            recs[vnum] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def item_list(b):
    d = data()
    return base.set_rows(b, [d['item_list'][k] for k in sorted(d['item_list'], key=int)])


def itemdesc(b):
    d = data()
    return base.set_rows(b, [d['itemdesc'][k] for k in sorted(d['itemdesc'], key=int)])


def locale_game(b):
    return _append_rows(b, list(data()['locale_game'].values()), lambda l: l.split('\t')[0].strip())


# in-pack name -> function
JOBS = {'gamedata/atlasinfo.txt': atlasinfo, 'gamedata/npclist.txt': npclist, 'gamedata/mob_proto': mob_proto,
        'gamedata/item_list.txt': item_list, 'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc,
        'locale/pl/locale_game.txt': locale_game}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_balathor_client.py <atlasinfo.txt|npclist.txt|mob_proto|item_list.txt|item_proto|'
                         'itemdesc.txt|locale_game.txt> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
