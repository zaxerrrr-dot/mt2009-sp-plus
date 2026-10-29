# -*- coding: utf-8 -*-
# MT2009_PLUS_HORSE40_V1 (client data) - the horse past level 21 in the client's data (server-patches/konie/README.md),
# from tools/konie/konie_items.json (= the server's konie.sql, tools/konie/gen_konie.py):
#
#   gamedata/item_proto (dbdata)   83050 Zestaw Opieki nad Koniem (over the first ITEM_GIFTBOX record), 50046-50049 (Szlachetna Trawa, Czer. Zen-szen (premium), Pasza dla Konia, Zlota
#                                  Ksiega Konia): a full record each over Ksiega Wojskowego Konia 50053 (an ITEM_QUEST
#                                  record, ../yohara/patch_yohara_client.py yitem_record); the horse skill books
#                                  55050-55067: type ITEM_QUEST and the flag QUEST_USE on their own records
#   locale/pl/itemdesc.txt (dbdata) their descriptions; gamedata/item_list.txt their icons (root/icon/item)
#   gamedata/mob_proto (gamedata)  Potezny Kon Wojskowy 20149-20151: the military horse's record (20107) with the vnum
#                                  and the Polish name (the server's apply.sh copies 20107 the same way)
# Idempotent: a second run changes nothing. build_konie_packs.py calls these on the packs.
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
ITEMS_JSON = os.path.join(REPO, 'tools', 'konie', 'konie_items.json')
TEMPLATE = {18: 50053}           # an ITEM_QUEST record (Ksiega Wojskowego Konia)
MOB_KEY = (4813894, 18955, 552631, 6822045)
MOB_RECORD = 256
MOB_LOCALE = (29, 25)            # offset, size of the Polish name in a mob record


def items_json():
    with io.open(ITEMS_JSON, encoding='utf-8') as f:
        return json.load(f)


def records(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    return ver, dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                     for i in range(cnt))


def book_record(r, typ, flag_add):
    r = bytearray(r)
    r[74] = typ
    flag = struct.unpack_from('<I', r, 86)[0]
    struct.pack_into('<I', r, 86, flag | flag_add)
    return bytes(r)


def want_records(recs):
    d = items_json()
    want = {}
    for w in d['items']:
        t = recs.get(TEMPLATE.get(w['type'], -1))
        if t is None:      # the kit (ITEM_GIFTBOX): the first record of its type
            t = next(recs[v] for v in sorted(recs) if recs[v][74] == w['type'])
        assert t[74] == w['type'], (w['vnum'], t[74])
        want[w['vnum']] = py.yitem_record(t, w)
    for v in d['books']['vnums']:
        assert v in recs, 'the client has no record of the book %d (yohara_items2)' % v
        want[v] = book_record(recs[v], d['books']['type'], d['books']['flag_add'])
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


def mob_records(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = m2pack.mcoz_decode(b[12:12 + esize], MOB_KEY)
    assert len(raw) == cnt * MOB_RECORD, (len(raw), cnt)
    return [raw[i * MOB_RECORD:(i + 1) * MOB_RECORD] for i in range(cnt)]


def want_mobs(recs):
    d = items_json()['mobs']
    by = dict((struct.unpack_from('<I', r, 0)[0], r) for r in recs)
    t = by[d['template']]
    off, size = MOB_LOCALE
    name = d['locale_name'].encode('cp1250')
    assert len(name) < size
    want = {}
    for v in d['vnums']:
        r = bytearray(t)
        struct.pack_into('<I', r, 0, v)
        r[off:off + size] = name + b'\0' * (size - len(name))
        want[v] = bytes(r)
    return want


def mob_proto(b):
    import m2pack
    recs = mob_records(b)
    by = dict((struct.unpack_from('<I', r, 0)[0], r) for r in recs)
    changed = 0
    for v, r in want_mobs(recs).items():
        if by.get(v) != r:
            by[v] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(by[v] for v in sorted(by))
    blob = m2pack.mcoz_encode(out, MOB_KEY)
    return struct.pack('<4sII', b'MMPT', len(by), len(blob)) + blob, changed


# in-pack name -> function
JOBS = {'gamedata/item_list.txt': item_list, 'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc,
        'gamedata/mob_proto': mob_proto}
