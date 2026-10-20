# -*- coding: utf-8 -*-
# MT2009_PLUS_COSTUME_SET_V2 (client data) - the costume sets' items the client lacked or had as other items, the
# method of ../ygloves/patch_ygloves_client.py:
#
#   gamedata/item_list.txt, gamedata/item_proto (dbdata), locale/pl/itemdesc.txt (dbdata)
#       the 6 items of tools/zestawy/zestawy_items.json (= the server's zestawy_items.sql, tools/zestawy/gen_zestawy.py):
#       Amulet Nazara 71202, Lizak Magii 71188, Czekoladowy Amulet 71199, Mistrzowski Emblemat 70607,
#       Blogoslawienstwo Mocy 72713 - each the record of Lizak Potegi 71136 (ITEM_UNIQUE, the unique slot) under its
#       vnum, names and time limit (the old client had 71188/71199/72713 as other rings - written over); Szarfa Serca
#       (unikat.) 86064 - the same record made a grade 4 sash as the exe makes 85001-85104 (item JSON "client"), its model
#       d:/ymir work/item/wing/acce_valentine_2020_4.gr2 (pack gf_zestawy, build_zestawy_packs.py). The icons:
#       client-2.0.30/root/icon/item/<vnum>.tga (GF 26.1.11).
# Idempotent: a second run changes nothing. build_zestawy_packs.py calls these functions on the packs; by hand, on
# plain copies, in the m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/zestawy/patch_zestawy_client.py <file> ... [--check]   (by its name)
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, os.path.join(HERE, '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402

REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
ITEMS_JSON = os.path.join(REPO, 'tools', 'zestawy', 'zestawy_items.json')
ITEMS = 6


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


def record(template, w):
    r = bytearray(template)
    struct.pack_into('<II', r, 0, w['vnum'], 0)
    r[8:41] = base.fixed(w['name'], 33)
    r[41:74] = base.fixed(w['locale_name'], 33)
    if w['limit'] is not None:
        struct.pack_into('<Bi', r, 114, 7, w['limit'])     # LIMIT_REAL_TIME, seconds (0: the engine's 7 days)
    c = w.get('client')
    if c:                                                   # the sash: its own fields over the ring's record
        struct.pack_into('<BBBB', r, 74, c['type'], c['subtype'], 0, 1)
        struct.pack_into('<IIIII', r, 78, c['stack'], c['antiflag'], c['flag'], c['wearflag'], 0)
        struct.pack_into('<BiBi', r, 114, c['limit'][0], c['limit'][1], 0, 0)
        struct.pack_into('<BiBiBi', r, 124, *[x for a in c['applies'] for x in a])
        struct.pack_into('<6i', r, 139, *c['values'])
        struct.pack_into('<IHBBB', r, 175, 0, 0, 0, c['specular'], 0)
    return bytes(r)


def item_proto(b):
    import m2pack
    ver, recs = records(b)
    changed = 0
    for w in items_json()['items']:
        r = record(recs[w['template']], w)
        if recs.get(w['vnum']) != r:
            recs[w['vnum']] = r
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
        raise SystemExit('usage: patch_zestawy_client.py <item_list.txt|item_proto|itemdesc.txt> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
