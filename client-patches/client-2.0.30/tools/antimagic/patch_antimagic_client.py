# -*- coding: utf-8 -*-
# MT2009_PLUS_ANTI_RESIST_MAGIC_V1 (client data) - Kamien Duszy Antymagii (bron, 28044 + 100*N) and Bialy Kamien Antymagii
# (zbroja, 28045 + 100*N), +0..+9 (server-patches/antimagic), the method of ../kamienie/patch_kamienie_client.py:
#
#   gamedata/item_list.txt, gamedata/item_proto (dbdata), locale/pl/itemdesc.txt (dbdata)
#       the 20 items of tools/antimagic/antimagic.json (= the server's antymagia.sql, tools/antimagic/gen_antimagic.py):
#       a full record each over Kamien Duszy Przysp.+0 28043 (ITEM_METIN, the soul stones' record;
#       ../yohara/patch_yohara_client.py yitem_record) with applytype0 252 (POINT_ANTI_RESIST_MAGIC - the tooltip's
#       line is root/localeinfo_point.py's), its item_list line (the package's icons 28044.tga / 28045.tga in
#       client-2.0.30/root/icon/item) and its itemdesc line.
# A vnum the client has with another record is replaced. Idempotent: a second run changes nothing.
# build_antimagic_packs.py calls these functions on the packs; by hand, on plain copies, in the m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/antimagic/patch_antimagic_client.py <file> ... [--check]   (by its name)
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
ITEMS_JSON = os.path.join(REPO, 'tools', 'antimagic', 'antimagic.json')
ITEMS = 20
TEMPLATE = 28043    # Kamien Duszy Przysp.+0: ITEM_METIN, the soul stones' record


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
    return dict((w['vnum'], py.yitem_record(recs[TEMPLATE], w)) for w in d['items'])


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
        raise SystemExit('usage: patch_antimagic_client.py <item_list.txt|item_proto|itemdesc.txt> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
