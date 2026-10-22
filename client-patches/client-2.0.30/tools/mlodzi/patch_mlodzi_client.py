# -*- coding: utf-8 -*-
# MT2009_PLUS_MLODZI_BOHATEROWIE_V1 (client data) - Bronie dla Mlodych Bohaterow in the client's data, the method of
# ../yhelm100/patch_yhelm100_client.py:
#
#   gamedata/item_proto (dbdata)   the 48 weapons 21900-21975 of tools/mlodzi/mlodzi_items.json (= the server's
#                                  mlodzi_bohaterowie.sql, tools/mlodzi/gen_mlodzi.py): a full record each
#                                  (../yohara/patch_yohara_client.py yitem_record: type 1 ITEM_WEAPON, the json's
#                                  subtype / size / limits 15 days LIMIT_REAL_TIME / applies / values) over the record of
#                                  Miecz+0 (10, a weapon record);
#   gamedata/item_list.txt         their lines "<vnum> WEAPON icon/item/2190K.tga d:/ymir work/item/weapon/2190K.gr2" -
#                                  every tier uses the tier-1 icon and model of its kind (as the official client); the
#                                  6 icons travel in client-2.0.30/root/icon/item, the 6 models (and their textures)
#                                  in the pack "mlodzi" (build_mlodzi_packs.py);
#   locale/pl/itemdesc.txt (dbdata) their descriptions.
# Idempotent: a second run changes nothing. By hand, on plain copies, in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/mlodzi/patch_mlodzi_client.py <file> ... [--check]   (by its name)
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, os.path.join(HERE, '..', 'yohara'))
sys.path.insert(0, os.path.join(HERE, '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402
import patch_yohara_client as py  # noqa: E402

REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
ITEMS_JSON = os.path.join(REPO, 'tools', 'mlodzi', 'mlodzi_items.json')
ITEMS = 48
TEMPLATE = 10                       # Miecz+0: an ITEM_WEAPON record
ITEM_WEAPON = 1
FIRST, LAST = 21900, 21975


def items_json():
    with io.open(ITEMS_JSON, encoding='utf-8') as f:
        d = json.load(f)
    assert len(d['items']) == ITEMS, len(d['items'])
    for w in d['items']:
        assert FIRST <= w['vnum'] <= LAST and w['type'] == ITEM_WEAPON, (w['vnum'], w['type'])
        assert 1 <= w['size'] <= 3, (w['vnum'], w['size'])
    return d


def records(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    return ver, dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                     for i in range(cnt))


def want_records(recs):
    t = recs[TEMPLATE]
    assert t[74] == ITEM_WEAPON, ('template', TEMPLATE, t[74])
    return dict((w['vnum'], py.yitem_record(t, w)) for w in items_json()['items'])


def item_proto(b):
    import m2pack
    ver, recs = records(b)
    changed = 0
    for v, r in want_records(recs).items():
        if recs.get(v) != r:
            recs[v] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, base.RECORD, len(recs), len(blob)) + blob, changed


def item_list(b):
    d = items_json()
    return base.set_rows(b, [d['item_list'][k] for k in sorted(d['item_list'], key=int)])


def itemdesc(b):
    d = items_json()
    return base.set_rows(b, [d['itemdesc'][k] for k in sorted(d['itemdesc'], key=int)])


# in-pack name -> function
JOBS = {'gamedata/item_list.txt': item_list, 'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_mlodzi_client.py <item_list.txt|item_proto|itemdesc.txt> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
