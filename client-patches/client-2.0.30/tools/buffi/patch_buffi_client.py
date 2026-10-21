# -*- coding: utf-8 -*-
# MT2009_PLUS_BUFFI_V1 (client data) - Buffi's items (61025/61026/61030/61031/61035-61038) in the client's data, the method
# of ../ygaya/patch_ygaya_client.py:
#
#   gamedata/item_list.txt, gamedata/item_proto (dbdata), locale/pl/itemdesc.txt (dbdata); MT2009_PLUS_BUFFI_V2:
#   locale/pl/skilldesc.txt and gamedata/skilltable.txt (dbdata) - the buffi skills 164-167
#       the items of tools/buffi/buffi.json (= the server's buffi.sql, tools/buffi/gen_buffi.py):
#       a full record each over Zelazna Szkatulka 50120 (../yohara/patch_yohara_client.py yitem_record), its item_list
#       line (Ameria's icons: client-2.0.30/root/icon/item/610xx.tga, buffi_book.tga) and its itemdesc line.
# A vnum the client has with another record is replaced (the records are ours). Idempotent: a second run changes
# nothing. build_buffi_packs.py calls these functions on the packs; by hand, on plain copies, in the m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/buffi/patch_buffi_client.py <file> ... [--check]   (by its name)
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
ITEMS_JSON = os.path.join(REPO, 'tools', 'buffi', 'buffi.json')
ITEMS = 8  # the seals, the name scroll, the soul stone, the four books


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
    d = items_json()
    return dict((w['vnum'], py.yitem_record(recs[py.TEMPLATE], w)) for w in d['items'])


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


# MT2009_PLUS_BUFFI_V2: the buffi skills 164-167 in the client's skill data (dbdata: locale/pl/skilldesc.txt,
# gamedata/skilltable.txt) - their names, the shaman's icons and the tooltip's polys (uibuffi.py's window)
def skilldesc(b):
    d = items_json()
    return base.set_rows(b, [d['skilldesc'][k] for k in sorted(d['skilldesc'], key=int)])


def skilltable(b):
    d = items_json()
    return base.set_rows(b, [d['skilltable'][k] for k in sorted(d['skilltable'], key=int)])


# in-pack name -> function
JOBS = {'gamedata/item_list.txt': item_list, 'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc,
        'locale/pl/skilldesc.txt': skilldesc, 'gamedata/skilltable.txt': skilltable}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_buffi_client.py <item_list.txt|item_proto|itemdesc.txt|skilldesc.txt|skilltable.txt> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
