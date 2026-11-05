# -*- coding: utf-8 -*-
# MT2009_PLUS_BRAKI_WIKI_V1 (client data) - the Yohara items of braki-yohara.md B9 as on the wiki in the client's data,
# the method of ../yhelm100/patch_yhelm100_client.py:
#
#   gamedata/item_proto (dbdata)   the 50 records of tools/brakiwiki/brakiwiki_items.json (= the server's braki_wiki.sql,
#                                  tools/brakiwiki/gen_brakiwiki.py): Tajemniczy Talizman+0..+9 (81560-81569, over the
#                                  record of 81560 - ../ymaps3 - so +0 gets its next item 81561) and Rekawice Weza
#                                  23050-23089 (over Rekawice Mocy+0 23000, ../ygloves) - ../yohara/patch_yohara_client.py
#                                  yitem_record;
#   gamedata/item_list.txt         their lines (GF icons: client-2.0.30/root/icon/item 23050/23060/23070/23080.tga;
#                                  81560.tga is there already);
#   locale/pl/itemdesc.txt (dbdata) their lines and the new texts of 31244 (Kamien Rekawic Pln. W.) and 50336 (Ksiega
#                                  Misji (W.Pln.W.)) - the old "Na razie bez zastosowania" note gone.
# Idempotent: a second run changes nothing. By hand, on plain copies, in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/brakiwiki/patch_brakiwiki_client.py <file> ... [--check]   (by its name)
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
ITEMS_JSON = os.path.join(REPO, 'tools', 'brakiwiki', 'brakiwiki_items.json')
ITEMS = 50
DESCS = 52
TEMPLATE = {7: 81560, 8: 23000}     # by subtype: a talisman (Tajemniczy Talizman+0), a glove (Rekawice Mocy+0)


def items_json():
    with io.open(ITEMS_JSON, encoding='utf-8') as f:
        d = json.load(f)
    assert len(d['items']) == ITEMS and len(d['itemdesc']) == DESCS, (len(d['items']), len(d['itemdesc']))
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
        t = recs[TEMPLATE[w['subtype']]]
        assert t[74] == w['type'] and t[75] == w['subtype'], (w['vnum'], t[74], t[75])
        want[w['vnum']] = py.yitem_record(t, w)
    return want


def item_proto(b):
    import m2pack
    ver, recs = records(b)
    changed = 0
    for v, r in sorted(want_records(recs).items()):
        if recs.get(v) != r:
            recs[v] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, base.RECORD, len(recs), len(blob)) + blob, changed


def list_rows():
    d = items_json()
    return [d['item_list'][k] for k in sorted(d['item_list'], key=int)]


def desc_rows():
    d = items_json()
    return [d['itemdesc'][k] for k in sorted(d['itemdesc'], key=int)]


def item_list(b):
    return base.set_rows(b, list_rows())


def itemdesc(b):
    return base.set_rows(b, desc_rows())


# in-pack name -> function
JOBS = {'gamedata/item_list.txt': item_list, 'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_brakiwiki_client.py <item_list.txt|item_proto|itemdesc.txt> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
