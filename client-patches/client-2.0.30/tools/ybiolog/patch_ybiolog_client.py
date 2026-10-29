# -*- coding: utf-8 -*-
# MT2009_PLUS_BIOLOGIST_YOHARA_V1 (client data) - the Biologist's specimens on the new continent in the client's data,
# the method of ../czepiec/patch_czepiec_client.py:
#
#   gamedata/item_list.txt, gamedata/item_proto (dbdata), locale/pl/itemdesc.txt (dbdata)
#       the 3 items of tools/ybiolog/ybiolog_items.json (= the server's yohara_biolog.sql, tools/ybiolog/
#       gen_ybiolog_items.py): Oczyszczony Rdzeń 31230, Kryształ Metin 31231, Mroczna Paproć 31232 - a full record
#       each over Czerwona Smocza Stal 30512 (a material record, ../yohara/patch_yohara_client.py yitem_record) -
#       their item_list lines (GF icons 31221 / 31229 / 31222.tga: client-2.0.30/root/icon/item) and itemdesc lines.
# A vnum the client has with another record is replaced. Idempotent: a second run changes nothing.
# build_ybiolog_packs.py calls these functions on the packs; by hand, on plain copies, in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/ybiolog/patch_ybiolog_client.py <file> ... [--check]   (by its name)
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
ITEMS_JSON = os.path.join(REPO, 'tools', 'ybiolog', 'ybiolog_items.json')
ITEMS = 3
TEMPLATE = {5: 30512}               # by type: a material (Czerwona Smocza Stal)


def items_json():
    with io.open(ITEMS_JSON, encoding='utf-8') as f:
        d = json.load(f)
    assert len(d['items']) == ITEMS, len(d['items'])
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
    want = {}
    for w in items_json()['items']:
        t = recs[TEMPLATE[w['type']]]
        assert t[74] == w['type'], (w['vnum'], t[74])      # the template is of the item's own type
        want[w['vnum']] = py.yitem_record(t, w)
    return want


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
        raise SystemExit('usage: patch_ybiolog_client.py <item_list.txt|item_proto|itemdesc.txt> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
