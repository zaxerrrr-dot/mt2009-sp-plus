# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_CRACK_V1 (client data) - Zaklety Las (SZC) (404) in the client's data (the method of
# ../yiluzja/patch_yiluzja_client.py):
#
#   gamedata/mob_proto      the 19 rows of linux-port/docker/mariadb/playerbot/yohara_crack.sql (the SZC monsters,
#                           bosses, Metins and NPCs) on the record of 101 (monsters, stones) or 9012 (NPC), each with its
#                           element - race flag bits 11-16 (offset 83) from tools/yohara_crack/ycrack_client.json
#                           (= yohara_crack_zywioly.sql); Statua Szczeliny Czasu (20472) is ../yiluzja's row;
#   gamedata/atlasinfo.txt  the map's row (= the server's Setting.txt, the official base);
#   gamedata/npclist.txt    nothing new (client 2.0.61 has every race) - kept for the method;
#   gamedata/item_list.txt, gamedata/item_proto, locale/pl/itemdesc.txt
#                           the 6 items of tools/yohara_crack/ycrack_client.json (= yohara_items_crack.sql): a full
#                           record each over a template (../yohara/patch_yohara_client.py yitem_record), its item_list
#                           line (the GF icons: client-2.0.30/root/icon/item) and its itemdesc line.
# APPEND ONLY for mob_proto/atlasinfo/npclist: a vnum/map already there with other content (the element bits aside) is
# a collision and stops the run. Idempotent: a second run changes nothing.
# By hand, on plain copies, in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/ycrack/patch_ycrack_client.py <file> ...   (by its name)
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
SQL = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_crack.sql')
MOBS_JSON = os.path.join(REPO, 'tools', 'yohara_crack', 'ycrack_client.json')
ITEMS_JSON = MOBS_JSON
ATLAS = ['metin2_map_boss_crack_dawnmist\t332800\t1817600\t3\t4']   # = linux-port/docker/game/yohara_crack/map/*/Setting.txt
ROWS = 19
ITEMS = 6
RACE_FLAG = 83                 # the record's dwRaceFlag (= ../zywioly/patch_zywioly_client.py)
ELEMENT_MASK = 0x1F800         # bits 11-16
Collision = sd.Collision


def mobs_json():
    with io.open(MOBS_JSON, encoding='utf-8') as f:
        return json.load(f)


def items_json():
    with io.open(ITEMS_JSON, encoding='utf-8') as f:
        d = json.load(f)
    assert len(d['items']) == ITEMS, len(d['items'])
    return d


def sql_mobs(path=SQL):
    t = open(path, encoding='utf-8').read()
    m = re.search(r'INSERT IGNORE INTO world\.mob_proto \(([^)]*)\) VALUES', t)
    cols = [c.strip().strip('`') for c in m.group(1).split(',')]
    mobs = []
    for r in sd._values(t[m.end():]):
        assert len(r) == len(cols), r[:3]
        mobs.append(dict(zip(cols, r)))
    assert len(mobs) == ROWS, len(mobs)
    return mobs


def MOB_TYPE(r):
    # vnum(4) name(25) locale_name(25) type(1): ../shipdefense/patch_shipdefense_client.py mob_record's layout
    return r[54]


def with_element(r, element):
    r = bytearray(r)
    old = struct.unpack_from('<I', r, RACE_FLAG)[0]
    struct.pack_into('<I', r, RACE_FLAG, (old & ~ELEMENT_MASK) | (element & ELEMENT_MASK))
    return bytes(r)


def mob_proto(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = m2pack.mcoz_decode(b[12:12 + esize], sd.MOB_KEY)
    assert len(raw) == cnt * sd.MOB_RECORD, (len(raw), cnt)
    R = sd.MOB_RECORD
    recs = dict((struct.unpack_from('<I', raw, i * R)[0], raw[i * R:(i + 1) * R]) for i in range(cnt))
    elem = dict((int(k), v) for k, v in mobs_json()['elements'].items())
    want = dict((w['vnum'], with_element(sd.mob_record(w, recs[101] if w['type'] in (0, 2) else recs[9012]),
                                         elem.get(w['vnum'], 0))) for w in sql_mobs())
    clash = [v for v, r in sorted(want.items()) if v in recs and with_element(recs[v], 0) != with_element(r, 0)]
    if clash:
        raise Collision('mob_proto: %d vnum(s) already in the client with other content: %s' % (len(clash), clash))
    new = dict((v, r) for v, r in want.items() if recs.get(v) != r)
    if not new:
        return b, 0
    recs.update(new)
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, sd.MOB_KEY)
    return struct.pack('<4sII', b'MMPT', len(recs), len(blob)) + blob, len(new)


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
    return _append_rows(b, ATLAS, lambda l: l.split('\t')[0].strip().lower())


def npclist(b):
    rows = ['%s\t%s' % (k, v) for k, v in sorted(mobs_json().get('npclist_add', {}).items())]
    return _append_rows(b, rows, lambda l: l.split()[0] if l.split() else '')


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                for i in range(cnt))
    changed = 0
    for w in items_json()['items']:
        r = py.yitem_record(recs[py.YITEM_TEMPLATE.get(w['type'], py.TEMPLATE)], w)
        if recs.get(w['vnum']) != r:
            recs[w['vnum']] = r
            changed += 1
    # a second-batch item this batch gives its use (Pyl Wezowy 70428: a quest use, as the server's UPDATE)
    for k, t in sorted(items_json().get('retype', {}).items()):
        v = int(k)
        if v not in recs:
            continue
        r = bytearray(recs[v])
        struct.pack_into('<BB', r, 74, t['type'], t['subtype'])
        flag = struct.unpack_from('<I', r, 86)[0] | t['flag_or']
        struct.pack_into('<I', r, 86, flag)
        if recs[v] != bytes(r):
            recs[v] = bytes(r)
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def item_list(b):
    d = items_json()
    return base.set_rows(b, [d['item_list'][k] for k in sorted(d['item_list'], key=int)])


def itemdesc(b):
    d = items_json()
    rows = [d['itemdesc'][k] for k in sorted(d['itemdesc'], key=int)]
    rows += [d['itemdesc_replace'][k] for k in sorted(d.get('itemdesc_replace', {}), key=int)]
    return base.set_rows(b, rows)


# in-pack name -> function
JOBS = {'gamedata/mob_proto': mob_proto, 'gamedata/atlasinfo.txt': atlasinfo, 'gamedata/npclist.txt': npclist,
        'gamedata/item_list.txt': item_list, 'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_ycrack_client.py <mob_proto|atlasinfo.txt|npclist.txt|item_list.txt|item_proto|'
                         'itemdesc.txt> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
