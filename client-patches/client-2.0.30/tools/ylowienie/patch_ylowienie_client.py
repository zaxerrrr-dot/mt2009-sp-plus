# -*- coding: utf-8 -*-
# MT2009_PLUS_FISHING_GLOBAL_V1 (client data) - fishing as on the global server, the method of
# ../yeliksiry/patch_yeliksiry_client.py:
#
#   gamedata/item_proto (dbdata)
#       * the new items of tools/yohara_lowienie/yohara_lowienie.json (= the server's yohara_lowienie.sql,
#         tools/yohara_lowienie/gen_ylowienie.py): Wedka Weglowa 27591, its parts 27621-27624, Skrzynia Nimfy Wodnej
#         27625, Zloty Tunczyk 27797, the fish 27824-27827 / 27854-27857 / 27884-27887, Ksiega Dzikiego / Dzielnego
#         Zwierza 55004 / 55005, Wino Kwiatu Brzoskwini+ 76033 - a full record each over a record of the same kind
#         (yitem_record);
#       * the rods 27400-27590: Wedka+1 ... Wedka+20, the global numbers (value0-5, the chain to +20, no refine set);
#       * the grilled fish of the wiki (27869, 27871, 27872, 27875, 27879, 27882): type, subtype, value0/1, apply;
#       * Kula Rybaka (27610, was Marmur Rybaka) and the Rybak's prices (27400 5 000, 27600 20 000, 27610 2 000).
#   gamedata/item_list.txt - the new items' lines (the GF 26.1.11 icons in client-2.0.30/root/icon/item; Wedka Weglowa
#       the rod's model; 27625 the GF chest 83032's icon; 76033 the official 71108.tga of the icon pack);
#   locale/pl/itemdesc.txt (dbdata) - the new items' lines, the fixed grilled fish, Kula Rybaka.
# Idempotent: a second run changes nothing. build_ylowienie_packs.py calls these functions on the packs; by hand, on
# plain copies, in the m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/ylowienie/patch_ylowienie_client.py <file> ... [--check]   (by its name)
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
ITEMS_JSON = os.path.join(REPO, 'tools', 'yohara_lowienie', 'yohara_lowienie.json')
ITEMS = 22
# a record of the same kind the client has, by (type, subtype)
TEMPLATES = {(13, 0): 27400, (12, 0): 27823, (12, 1): 27853, (36, 0): 27883, (3, 11): 27878, (5, 0): 55003,
             (20, 0): 50006, (18, 0): 50120}


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


def rod_record(old, r):
    n = bytearray(old)
    n[8:41] = base.fixed(r['locale_name'], 33)
    n[41:74] = base.fixed(r['locale_name'], 33)
    struct.pack_into('<6i', n, 139, *r['value'])
    struct.pack_into('<IH', n, 175, r['refined_vnum'], 0)
    return bytes(n)


def grilled_record(old, g):
    n = bytearray(old)
    struct.pack_into('<BB', n, 74, g['type'], g['subtype'])
    struct.pack_into('<BiBiBi', n, 124, g['applytype0'], g['applyvalue0'], 0, 0, 0, 0)
    struct.pack_into('<6i', n, 139, g['value0'], g['value1'], 0, 0, 0, 0)
    return bytes(n)


def priced_record(old, vnum, d):
    n = bytearray(old)
    pl = d['renamed'].get(str(vnum))
    if pl:
        n[41:74] = base.fixed(pl, 33)
    price = d['shop_gold'].get(str(vnum))
    if price is not None:
        struct.pack_into('<qq', n, 98, price, price)
    return bytes(n)


def want_records(recs):
    d = items_json()
    out = {}
    for w in d['items']:
        out[w['vnum']] = py.yitem_record(recs[TEMPLATES.get((w['type'], w['subtype']), 50120)], w)
    for r in d['rods']:
        out[r['vnum']] = rod_record(recs[r['vnum']], r)
    for k, g in d['grilled'].items():
        out[int(k)] = grilled_record(recs[int(k)], g)
    for k in set(d['renamed']) | set(d['shop_gold']):
        v = int(k)
        out[v] = priced_record(out.get(v, recs[v]), v, d)
    return out


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


def item_list(b):
    d = items_json()
    return base.set_rows(b, [d['item_list'][k] for k in sorted(d['item_list'], key=int)])


def desc_rows():
    d = items_json()
    rows = [d['itemdesc'][k] for k in sorted(d['itemdesc'], key=int)]
    rows += [d['grilled'][k]['desc'] for k in sorted(d['grilled'], key=int)]
    rows += [d['renamed_desc'][k] for k in sorted(d['renamed_desc'], key=int)]
    return rows


def itemdesc(b):
    return base.set_rows(b, desc_rows())


# in-pack name -> function
JOBS = {'gamedata/item_list.txt': item_list, 'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_ylowienie_client.py <item_list.txt|item_proto|itemdesc.txt> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
